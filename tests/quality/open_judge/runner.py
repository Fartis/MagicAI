from __future__ import annotations

import argparse
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

from .cases import OPEN_JUDGE_CASES
from .execution import run_open_judge_case
from .models import ACCEPTABLE_OUTCOMES, OpenJudgeOutcome
from .reports import (
    collect_turns,
    outcome_counts,
    write_failure_artifacts,
    write_html_report,
    write_json_report,
    write_txt_report,
    write_xml_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run conversational Open Judge contracts and classify semantic failures."
        ),
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only one case id. Can be used multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory. Defaults to resultado_open_judge/<run-id>.",
    )
    parser.add_argument(
        "--list-cases",
        action="store_true",
        help="List available cases and exit.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first case with a non-passing turn.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero unless every turn has an acceptable outcome.",
    )
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help=(
            "Return non-zero on factual contradiction, hallucination or execution error."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_cases:
        for case in OPEN_JUDGE_CASES:
            print(f"{case.id}: {case.name} ({len(case.turns)} turns)")
        return 0

    selected_ids = {case_id.upper() for case_id in args.case}
    cases = [
        case
        for case in OPEN_JUDGE_CASES
        if not selected_ids or case.id.upper() in selected_ids
    ]

    if not cases:
        print("No Open Judge cases selected.")
        return 2

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path(args.output_dir or Path("resultado_open_judge") / run_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    results = []

    for case in cases:
        print(f"[{case.id}] {case.name}")
        result = run_open_judge_case(case)
        results.append(result)
        print(f"  {result.outcome.value} ({result.elapsed:.2f}s)")

        if args.fail_fast and any(
            turn.outcome not in ACCEPTABLE_OUTCOMES
            for turn in result.turns
        ):
            break

    elapsed = time.perf_counter() - started
    metadata = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "elapsed_seconds": round(elapsed, 6),
    }

    write_txt_report(results, output_dir / "open_judge_summary.txt", metadata)
    write_json_report(results, output_dir / "open_judge_summary.json", metadata)
    write_xml_report(results, output_dir / "open_judge_summary.xml", metadata)
    write_html_report(results, output_dir / "open_judge_summary.html", metadata)
    failure_artifacts = write_failure_artifacts(results, output_dir)

    turns = collect_turns(results)
    counts = outcome_counts(results)

    print()
    print("=" * 80)
    print("OPEN JUDGE BASELINE")
    print("=" * 80)
    print(f"Cases   : {len(results)}")
    print(f"Turns   : {len(turns)}")
    for outcome in OpenJudgeOutcome:
        print(f"{outcome.value:<26}: {counts.get(outcome.value, 0)}")
    print(f"Failures: {failure_artifacts} artifacts")
    print(f"Reports : {output_dir}")

    passing = ACCEPTABLE_OUTCOMES
    critical = {
        OpenJudgeOutcome.FACTUAL_CONTRADICTION,
        OpenJudgeOutcome.HALLUCINATION,
        OpenJudgeOutcome.EXECUTION_ERROR,
    }

    if args.strict and any(turn.outcome not in passing for turn in turns):
        return 1

    if args.fail_on_critical and any(turn.outcome in critical for turn in turns):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
