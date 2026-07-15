from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.exhaustive.planner import FAMILY_ORDER, build_exhaustive_plan, normalize_families
from tests.quality.exhaustive.runner import (
    ExhaustiveAuditError,
    execute_exhaustive_campaign,
    finalize_exhaustive_campaign,
    prepare_exhaustive_campaign,
)

DEFAULT_OUTPUT_DIR = "resultado_oracle_exhaustive"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Audit every supported Oracle candidate for mana abilities, Ward, "
            "Undying, and activated-ability source independence. Output is "
            "compact, resumable, and evaluation-only."
        )
    )
    parser.add_argument("--oracle-file", help="Override sources/scryfall/oracle-cards.json")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--shard-size", type=int, default=250)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--allow-llm",
        action="store_true",
        help=(
            "Permit fallback to Ollama. By default the exhaustive sweep is "
            "deterministic-only and records every fallback as a coverage failure."
        ),
    )
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help=(
            "Restrict to a family: mana_ability, ward, undying_exile, or "
            "source_independence. Can be repeated."
        ),
    )
    parser.add_argument(
        "--template-mode",
        choices=("one", "all"),
        default="one",
        help="Use one rotating template per candidate (default) or all three.",
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Build the exhaustive Oracle plan/findings without asking the Judge.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        help="Development smoke limit; omit for the full exhaustive sweep.",
    )
    parser.add_argument("--list-families", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_families:
        print("Available exhaustive families:")
        for family in FAMILY_ORDER:
            print(f"- {family}")
        return 0
    if args.workers <= 0 or args.shard_size <= 0:
        print("ERROR: --workers and --shard-size must be greater than zero", file=sys.stderr)
        return 2

    project_root = Path.cwd().resolve()
    output_root = Path(args.output_dir).resolve()
    catalog = CardCatalog(args.oracle_file)
    oracle_file = catalog.oracle_file.resolve()
    try:
        families = normalize_families(args.family)
        plan = build_exhaustive_plan(
            catalog,
            families=families,
            template_mode=args.template_mode,
            max_cases=args.max_cases,
        )
        prepare_exhaustive_campaign(
            project_root=project_root,
            output_root=output_root,
            oracle_file=oracle_file,
            scenarios=plan.scenarios,
            static_summary=plan.static_summary,
            static_findings=plan.static_findings,
            workers=args.workers,
            shard_size=args.shard_size,
            template_mode=args.template_mode,
            families=families,
            resume=args.resume,
            allow_llm=args.allow_llm,
            command=[sys.executable, "-m", "tests.quality.oracle_exhaustive_test", *sys.argv[1:]],
        )
    except (ExhaustiveAuditError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Oracle       : {oracle_file}")
    print(f"Cards scanned: {plan.static_summary['supported_cards']}")
    print(f"Candidates   : {plan.static_summary['candidate_total']}")
    print(f"Scenarios    : {plan.static_summary['scenario_total']}")
    print(f"Families     : {', '.join(families)}")
    print(f"Templates    : {args.template_mode}")
    print(f"Workers      : {args.workers}")
    print(f"Shard size   : {args.shard_size}")
    print(f"Static flags : {plan.static_summary['static_findings']}")
    print(f"LLM fallback : {'allowed' if args.allow_llm else 'blocked (coverage audit)'}")
    print(f"Output       : {output_root}")
    print("Purpose      : evaluation only; no training or automatic learning")

    if args.static_only:
        print("Static-only plan completed.")
        return 1 if plan.static_findings else 0

    started = time.perf_counter()
    summaries, errors = execute_exhaustive_campaign(
        project_root=project_root,
        output_root=output_root,
        oracle_file=oracle_file,
        scenarios=plan.scenarios,
        workers=args.workers,
        shard_size=args.shard_size,
        resume=args.resume,
        allow_llm=args.allow_llm,
    )
    payload = finalize_exhaustive_campaign(
        output_root,
        shard_summaries=summaries,
        errors=errors,
        wall_seconds=time.perf_counter() - started,
        static_summary=plan.static_summary,
    )
    print()
    print("=" * 80)
    print("EXHAUSTIVE RESULT")
    print("=" * 80)
    print(f"Cases    : {payload['cases']}")
    print(f"Failures : {payload['failures']}")
    print(f"Warnings : {payload['warnings']}")
    print(f"Errors   : {len(errors)}")
    print(f"LLM calls: {payload['llm_calls']}")
    print(f"Origins  : {payload['origin_counts']}")
    print(f"Status   : {payload['status']}")
    print(f"Summary  : {output_root / 'exhaustive_summary.md'}")
    return 1 if payload["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
