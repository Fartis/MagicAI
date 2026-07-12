import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.quality.open_judge_stability_test import validate_reports


def _report(path: Path, outcomes: dict[str, int], turns: int = 27) -> Path:
    path.write_text(
        json.dumps(
            {
                "summary": {
                    "cases": 11,
                    "turns": turns,
                    "outcomes": outcomes,
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_three_acceptable_reports_pass() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        paths = [
            _report(
                root / f"run_{index}.json",
                {
                    "PASS": 21,
                    "STRATEGY_REQUIRED": 4,
                    "NEEDS_CLARIFICATION": 1,
                    "FALSE_PREMISE_HANDLED": 1,
                },
            )
            for index in range(3)
        ]

        aggregate = validate_reports(paths)

        assert aggregate["PASS"] == 63


def test_critical_outcome_fails() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        paths = [
            _report(root / "run_1.json", {"PASS": 27}),
            _report(root / "run_2.json", {"PASS": 26, "HALLUCINATION": 1}),
            _report(root / "run_3.json", {"PASS": 27}),
        ]

        try:
            validate_reports(paths)
        except AssertionError:
            return
        raise AssertionError("Critical Open Judge outcome was accepted.")


def main() -> int:
    tests = [
        test_three_acceptable_reports_pass,
        test_critical_outcome_fails,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Open Judge stability contract tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
