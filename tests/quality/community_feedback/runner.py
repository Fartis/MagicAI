from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .campaign import (
    FeedbackCampaignError,
    FeedbackCampaignStore,
    execute_feedback_campaign,
)
from .execution import ACCEPTABLE_VALIDATED_OUTCOMES
from .loader import FeedbackCaseError, load_feedback_cases, write_template
from .models import FeedbackEvaluationMode, FeedbackOutcome


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run manually curated, paraphrased community rules scenarios through MagicAI "
            "as an evaluation-only, resumable campaign."
        )
    )
    parser.add_argument(
        "--input",
        default="community_feedback/inbox",
        help="JSON case file or directory. Defaults to community_feedback/inbox.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help=(
            "Campaign output directory. Defaults to "
            "resultado_community_feedback/<campaign-id>."
        ),
    )
    parser.add_argument(
        "--campaign-id",
        default="",
        help="Stable campaign identifier used for resume and result provenance.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue an existing campaign without rerunning completed cases.",
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="When resuming, rerun only cases stored under execution_errors/.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Refresh aggregate reports every N completed cases. Per-case JSON is always atomic.",
    )
    parser.add_argument(
        "--skip-source-hashes",
        action="store_true",
        help="Record source paths and sizes without hashing large local source files.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only one case id. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--create-template",
        default="",
        help="Create a safe exploratory JSON template and exit.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a validated case has a non-acceptable outcome.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.retry_errors and not args.resume:
        print("--retry-errors requires --resume.")
        return 2
    if args.resume and not (args.campaign_id or args.output_dir):
        print("--resume requires --campaign-id or --output-dir.")
        return 2

    if args.create_template:
        target = Path(args.create_template)
        if target.exists():
            print(f"Refusing to overwrite existing file: {target}")
            return 2
        write_template(target)
        print(f"Created feedback template: {target}")
        return 0

    input_path = Path(args.input)
    try:
        cases = load_feedback_cases(input_path)
    except FeedbackCaseError as error:
        print(f"Feedback case error: {error}")
        return 2

    selected = {case_id.upper() for case_id in args.case}
    if selected:
        cases = [case for case in cases if case.id.upper() in selected]
    if not cases:
        print("No community feedback cases selected.")
        return 2

    try:
        campaign_id = resolve_campaign_id(args)
        output_dir = Path(
            args.output_dir
            or Path("resultado_community_feedback") / campaign_id
        )
        store = FeedbackCampaignStore(
            campaign_id=campaign_id,
            output_dir=output_dir,
            input_path=input_path,
            project_root=Path.cwd(),
            command=sys.argv,
            include_source_hashes=not args.skip_source_hashes,
        )

        print("=" * 80)
        print("COMMUNITY FEEDBACK EVALUATION CAMPAIGN")
        print("=" * 80)
        print(f"Campaign         : {campaign_id}")
        print(f"Cases selected   : {len(cases)}")
        print(f"Resume           : {'yes' if args.resume else 'no'}")
        print(f"Retry errors     : {'yes' if args.retry_errors else 'no'}")
        print("Training         : disabled")
        print("Auto-promotion   : disabled")
        print()

        def show_case(result, index: int, total: int, resumed: bool) -> None:
            del resumed
            print(
                f"[{index}/{total}] {result.case.id} — "
                f"{result.outcome.value} ({result.elapsed:.2f}s)"
            )

        run = execute_feedback_campaign(
            cases,
            store=store,
            resume=args.resume,
            retry_errors=args.retry_errors,
            checkpoint_every=args.checkpoint_every,
            on_case_complete=show_case,
        )
    except (FeedbackCampaignError, json.JSONDecodeError, OSError) as error:
        print(f"Feedback campaign error: {error}")
        return 2

    turns = [turn for result in run.results for turn in result.turns]
    counts = run.manifest.get("counts", {})
    print()
    print("=" * 80)
    print("CAMPAIGN SUMMARY")
    print("=" * 80)
    print(f"Status           : {run.manifest.get('status', '')}")
    print(f"Processed cases  : {counts.get('processed_cases', len(run.results))}")
    print(f"Pending cases    : {counts.get('pending_cases', 0)}")
    print(f"Execution errors : {counts.get('execution_error_cases', 0)}")
    print(
        "Review required  : "
        + str(sum(turn.outcome is FeedbackOutcome.REVIEW_REQUIRED for turn in turns))
    )
    print(f"Reports          : {run.output_dir}")

    if run.interrupted:
        print("Campaign interrupted safely. Run the same command with --resume.")
        return 130

    if args.strict:
        invalid = [
            turn
            for result in run.results
            if result.case.mode is FeedbackEvaluationMode.VALIDATED
            for turn in result.turns
            if turn.outcome not in ACCEPTABLE_VALIDATED_OUTCOMES
        ]
        if invalid:
            return 1

    return 0


def resolve_campaign_id(args: argparse.Namespace) -> str:
    if args.campaign_id:
        return args.campaign_id

    if args.resume and args.output_dir:
        manifest_path = Path(args.output_dir) / "campaign_manifest.json"
        if manifest_path.is_file():
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            campaign_id = str(payload.get("campaign_id", "")).strip()
            if campaign_id:
                return campaign_id

    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


if __name__ == "__main__":
    sys.exit(main())
