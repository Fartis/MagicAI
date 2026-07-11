from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.dynamic import execution
from tests.quality.dynamic.campaign import (
    aggregate_coverage,
    build_campaign_payload,
    derive_campaign_seeds,
    resolve_campaign_seeds,
    write_campaign_summary,
)
from tests.quality.dynamic.concepts import get_concepts
from tests.quality.dynamic.models import DynamicScenario, EvaluationContract


def _scenario(
    *,
    scenario_id: str,
    seed: int,
    concept_id: str,
    template_id: str,
    source_kind: str = "rules",
    card_name: str = "",
    card_set_name: str = "",
    card_legal_formats: tuple[str, ...] = (),
) -> DynamicScenario:
    return DynamicScenario(
        id=scenario_id,
        seed=seed,
        concept_id=concept_id,
        concept_name=concept_id,
        card_name=card_name,
        template_id=template_id,
        question="Synthetic question",
        tags=("dynamic",),
        contract=EvaluationContract(required_all=("ok",)),
        card_set_name=card_set_name,
        card_legal_formats=card_legal_formats,
        source_kind=source_kind,
    )


def test_derived_campaign_seeds_are_reproducible_and_unique():
    first = derive_campaign_seeds(184729, 6)
    second = derive_campaign_seeds(184729, 6)

    assert first == second
    assert first[0] == 184729
    assert len(first) == len(set(first)) == 6


def test_explicit_campaign_seeds_are_preserved():
    seeds = resolve_campaign_seeds(
        explicit_seeds=[1, 2, 3],
        base_seed=999,
        runs=20,
    )

    assert seeds == [1, 2, 3]


def test_duplicate_explicit_seeds_are_rejected():
    try:
        resolve_campaign_seeds(
            explicit_seeds=[7, 7],
            base_seed=7,
            runs=2,
        )
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("Duplicate explicit seeds were accepted.")


def test_campaign_coverage_tracks_concepts_templates_sources_and_cards():
    concepts = get_concepts(["ward", "cleanup_priority"])
    scenarios = [
        _scenario(
            scenario_id="DG-001",
            seed=1,
            concept_id="ward",
            template_id="ward-stack",
            source_kind="card",
            card_name="Guardian One",
            card_set_name="Legal Set",
            card_legal_formats=("commander", "legacy"),
        ),
        _scenario(
            scenario_id="DG-002",
            seed=1,
            concept_id="cleanup_priority",
            template_id="cleanup-exception",
        ),
        _scenario(
            scenario_id="DG-003",
            seed=2,
            concept_id="ward",
            template_id="ward-priority",
            source_kind="card",
            card_name="Guardian Two",
            card_set_name="Legal Set",
            card_legal_formats=("commander",),
        ),
    ]

    coverage = aggregate_coverage(scenarios, concepts=concepts)

    assert coverage["concept_counts"] == {
        "cleanup_priority": 1,
        "ward": 2,
    }
    assert coverage["source_kind_counts"] == {"card": 2, "rules": 1}
    assert coverage["unique_cards"] == 2
    assert coverage["legal_format_counts"] == {
        "commander": 2,
        "legacy": 1,
    }
    assert coverage["set_counts"] == {"Legal Set": 2}
    assert coverage["templates_seen"] == 3
    assert coverage["templates_expected"] == 6
    assert len(coverage["missing_templates"]) == 3
    assert coverage["complete"] is False


def test_campaign_payload_and_summary_files_round_trip():
    concepts = get_concepts(["cleanup_priority"])
    scenarios = [
        _scenario(
            scenario_id="DG-001",
            seed=11,
            concept_id="cleanup_priority",
            template_id="cleanup-exception",
        )
    ]
    runs = [
        {
            "index": 1,
            "seed": 11,
            "cases": 1,
            "failures": 0,
            "warnings": 0,
            "status": "PASS",
            "elapsed_seconds": 1.25,
            "manifest": "run_01/manifest.json",
            "txt": "run_01/report.txt",
            "xml": "run_01/report.xml",
            "html": "run_01/report.html",
            "failure_files": [],
        }
    ]
    payload = build_campaign_payload(
        base_seed=11,
        seeds=[11],
        cases_per_seed=1,
        run_summaries=runs,
        scenarios=scenarios,
        concepts=concepts,
        total_elapsed=1.5,
    )

    assert payload["status"] == "PASS"
    assert payload["cases_executed"] == 1

    with tempfile.TemporaryDirectory() as temp_dir:
        paths = write_campaign_summary(temp_dir, payload)

        assert all(path.exists() for path in paths.values())
        loaded = json.loads(paths["json"].read_text(encoding="utf-8"))
        assert loaded == payload
        assert loaded["coverage"]["complete"] is False
        assert "MagicAI Dynamic Campaign" in paths["txt"].read_text(
            encoding="utf-8"
        )
        assert "run_01/report.html" in paths["html"].read_text(
            encoding="utf-8"
        )


def test_shared_execution_engine_saves_failure_and_honors_fail_fast():
    scenarios = [
        _scenario(
            scenario_id="DG-001",
            seed=5,
            concept_id="cleanup_priority",
            template_id="cleanup-exception",
        ),
        _scenario(
            scenario_id="DG-002",
            seed=5,
            concept_id="cleanup_priority",
            template_id="cleanup-can-act",
        ),
    ]
    original_run_case = execution.run_case

    def fake_run_case(_assistant, case):
        return {
            "id": case["id"],
            "name": case["name"],
            "tags": case["tags"],
            "status": "FAIL",
            "elapsed": 0.01,
            "steps": [
                {
                    "status": "FAIL",
                    "failures": ["synthetic"],
                    "warnings": [],
                }
            ],
        }

    execution.run_case = fake_run_case

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            results, failures, _elapsed = execution.run_dynamic_scenarios(
                object(),
                scenarios,
                failure_dir=Path(temp_dir) / "failures",
                fail_fast=True,
            )

            assert len(results) == 1
            assert len(failures) == 1
            assert failures[0].exists()
            assert results[0]["dynamic"]["id"] == "DG-001"
    finally:
        execution.run_case = original_run_case


def main():
    tests = [
        test_derived_campaign_seeds_are_reproducible_and_unique,
        test_explicit_campaign_seeds_are_preserved,
        test_duplicate_explicit_seeds_are_rejected,
        test_campaign_coverage_tracks_concepts_templates_sources_and_cards,
        test_campaign_payload_and_summary_files_round_trip,
        test_shared_execution_engine_saves_failure_and_honors_fail_fast,
    ]
    errors = []

    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}")
            print(exc)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Tests : {len(tests)}")
    print(f"Errors: {len(errors)}")

    if errors:
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
