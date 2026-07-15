from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from tests.quality.dynamic.campaign_runner import (
    DynamicCampaignError,
    execute_campaign_runs,
    prepare_campaign,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_parallel_runs_are_isolated_and_resume_skips_completed_runs():
    project_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "campaign"
        seeds = [111, 222]
        common = dict(
            project_root=project_root,
            output_root=output,
            base_seed=111,
            seeds=seeds,
            cases_per_seed=1,
            concept_ids=["cleanup_priority"],
            oracle_file=None,
            requires_oracle=False,
        )
        prepare_campaign(
            **common,
            workers=2,
            resume=False,
            command=["test", "--workers", "2"],
        )
        summaries, scenarios, errors = execute_campaign_runs(
            **common,
            workers=2,
            fail_fast=False,
            resume=False,
        )
        assert not errors
        assert len(summaries) == 2
        assert len(scenarios) == 2
        markers = sorted(output.glob("run_*/run_complete.json"))
        assert len(markers) == 2
        before = {str(path): _digest(path) for path in markers}
        for path in markers:
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["artifact_purpose"] == "evaluation"
            assert payload["training_allowed"] is False

        prepare_campaign(
            **common,
            workers=1,
            resume=True,
            command=["test", "--workers", "1", "--resume"],
        )
        summaries2, scenarios2, errors2 = execute_campaign_runs(
            **common,
            workers=1,
            fail_fast=False,
            resume=True,
        )
        after = {str(path): _digest(path) for path in markers}
        assert before == after
        assert not errors2
        assert len(summaries2) == 2
        assert len(scenarios2) == 2


def test_resume_rejects_changed_reproducibility_inputs():
    project_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "campaign"
        common = dict(
            project_root=project_root,
            output_root=output,
            base_seed=123,
            seeds=[123],
            cases_per_seed=1,
            concept_ids=["cleanup_priority"],
            oracle_file=None,
            workers=1,
            requires_oracle=False,
            command=["test"],
        )
        prepare_campaign(**common, resume=False)
        manifest_path = output / "campaign_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["code_fingerprint"]["sha256"] = "changed"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        try:
            prepare_campaign(**common, resume=True)
        except DynamicCampaignError as exc:
            assert "reproducibility inputs changed" in str(exc)
        else:
            raise AssertionError("Resume accepted a changed code fingerprint")


def main():
    tests = [
        test_parallel_runs_are_isolated_and_resume_skips_completed_runs,
        test_resume_rejects_changed_reproducibility_inputs,
    ]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}\n{exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
