from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ACCEPTABLE = {
    "PASS",
    "FALSE_PREMISE_HANDLED",
    "NEEDS_CLARIFICATION",
    "STRATEGY_REQUIRED",
}


def validate_reports(paths: list[Path]) -> Counter[str]:
    if len(paths) < 3:
        raise ValueError("At least three Open Judge reports are required.")

    aggregate: Counter[str] = Counter()
    expected_shape: tuple[int, int] | None = None

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        shape = (
            int(summary.get("cases", 0)),
            int(summary.get("turns", 0)),
        )

        if expected_shape is None:
            expected_shape = shape
        elif shape != expected_shape:
            raise AssertionError(
                f"Open Judge report shape changed: {shape} != {expected_shape}"
            )

        outcomes = {
            str(name): int(count)
            for name, count in summary.get("outcomes", {}).items()
        }
        unexpected = {
            name: count
            for name, count in outcomes.items()
            if count and name not in ACCEPTABLE
        }
        if unexpected:
            raise AssertionError(
                f"{path}: non-acceptable outcomes found: {unexpected}"
            )

        aggregate.update(outcomes)

    return aggregate


def _summary_path(value: str) -> Path:
    path = Path(value)
    if path.is_dir():
        path = path / "open_judge_summary.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate three or more stable Open Judge baselines.",
    )
    parser.add_argument(
        "reports",
        nargs="+",
        help="Run directories or open_judge_summary.json files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = [_summary_path(value) for value in args.reports]

    try:
        aggregate = validate_reports(paths)
    except (AssertionError, FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1

    print(f"Stable Open Judge reports: {len(paths)}")
    for name in sorted(aggregate):
        print(f"{name:<26}: {aggregate[name]}")
    print("Open Judge stability gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
