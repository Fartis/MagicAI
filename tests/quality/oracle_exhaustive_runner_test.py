from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.exhaustive.planner import build_exhaustive_plan, normalize_families
from tests.quality.exhaustive.runner import ExhaustiveAuditError, prepare_exhaustive_campaign


def _catalog(directory: Path) -> CardCatalog:
    path = directory / "oracle-cards.json"
    path.write_text(
        json.dumps([
            {
                "name": "Mana Rock",
                "oracle_text": "{T}: Add {C}.",
                "type_line": "Artifact",
                "keywords": [],
                "games": ["paper"],
                "set": "tst",
                "set_name": "Test",
                "set_type": "expansion",
                "legalities": {"commander": "legal"},
            }
        ]),
        encoding="utf-8",
    )
    return CardCatalog(path)


def test_prepare_is_reproducible_and_resume_safe():
    project_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as temp:
        temp_path = Path(temp)
        catalog = _catalog(temp_path)
        plan = build_exhaustive_plan(catalog, families=("mana_ability",))
        output = temp_path / "output"
        common = dict(
            project_root=project_root,
            output_root=output,
            oracle_file=catalog.oracle_file,
            scenarios=plan.scenarios,
            static_summary=plan.static_summary,
            static_findings=plan.static_findings,
            workers=1,
            shard_size=10,
            template_mode="one",
            families=normalize_families(("mana_ability",)),
            allow_llm=False,
            command=["test"],
        )
        prepare_exhaustive_campaign(**common, resume=False)
        assert (output / "campaign_manifest.json").is_file()
        assert (output / "scenarios.jsonl.gz").is_file()
        prepare_exhaustive_campaign(**common, resume=True)


def test_resume_rejects_changed_plan():
    project_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as temp:
        temp_path = Path(temp)
        catalog = _catalog(temp_path)
        plan = build_exhaustive_plan(catalog, families=("mana_ability",))
        output = temp_path / "output"
        common = dict(
            project_root=project_root,
            output_root=output,
            oracle_file=catalog.oracle_file,
            scenarios=plan.scenarios,
            static_summary=plan.static_summary,
            static_findings=plan.static_findings,
            workers=1,
            template_mode="one",
            families=normalize_families(("mana_ability",)),
            allow_llm=False,
            command=["test"],
        )
        prepare_exhaustive_campaign(**common, shard_size=10, resume=False)
        try:
            prepare_exhaustive_campaign(**common, shard_size=11, resume=True)
        except ExhaustiveAuditError as exc:
            assert "Cannot resume" in str(exc)
        else:
            raise AssertionError("Resume accepted a changed shard size")


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
