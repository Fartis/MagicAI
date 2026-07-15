from __future__ import annotations

import argparse
import secrets
import sys
import time
from pathlib import Path

from tests.quality.dynamic.campaign import (
    build_campaign_payload,
    resolve_campaign_seeds,
    write_campaign_summary,
)
from tests.quality.dynamic.campaign_runner import (
    DynamicCampaignError,
    execute_campaign_runs,
    finalize_campaign_manifest,
    prepare_campaign,
)
from tests.quality.dynamic.concepts import CONCEPTS, get_concepts

DEFAULT_OUTPUT_DIR = "resultado_dynamic_campaign"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run a reproducible, resumable multi-seed MagicAI Dynamic "
            "Gauntlet campaign. Runs can be distributed across independent "
            "worker processes."
        ),
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        help="Seed used to derive the campaign seeds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        action="append",
        default=[],
        help=(
            "Use an explicit campaign seed. Can be repeated. When present, "
            "--base-seed and --runs do not derive additional seeds."
        ),
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of derived seeds. Default: 3.",
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=42,
        help="Scenarios generated per seed. Default: 42.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "Independent worker processes used for campaign runs. "
            "Default: 1. For deterministic campaigns on a Ryzen 5 5600, "
            "start with 4."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume the same campaign from completed run markers. Stable "
            "inputs, sources, model metadata and code fingerprints must match."
        ),
    )
    parser.add_argument(
        "--concept",
        action="append",
        default=[],
        help="Restrict the campaign to a concept id. Can be repeated.",
    )
    parser.add_argument(
        "--list-concepts",
        action="store_true",
        help="List available concept ids and exit.",
    )
    parser.add_argument(
        "--oracle-file",
        help="Override sources/scryfall/oracle-cards.json.",
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument(
        "--require-full-coverage",
        action="store_true",
        help=(
            "Return a failure status unless every selected concept and "
            "question template was executed at least once."
        ),
    )
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def _print_concepts():
    print("Available dynamic concepts:")
    for concept in CONCEPTS:
        print(f"- {concept.id}: {concept.name}")


def main():
    args = parse_args()

    if args.list_concepts:
        _print_concepts()
        return 0

    if args.cases <= 0:
        print("ERROR: --cases must be greater than zero.", file=sys.stderr)
        return 2
    if args.workers <= 0:
        print("ERROR: --workers must be greater than zero.", file=sys.stderr)
        return 2
    if args.fail_fast and args.workers > 1:
        print(
            "ERROR: --fail-fast is only supported with --workers 1.",
            file=sys.stderr,
        )
        return 2

    base_seed = (
        args.base_seed
        if args.base_seed is not None
        else (args.seed[0] if args.seed else secrets.randbits(32))
    )

    try:
        seeds = resolve_campaign_seeds(
            explicit_seeds=args.seed,
            base_seed=base_seed,
            runs=args.runs,
        )
        concepts = get_concepts(args.concept)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    concept_ids = [concept.id for concept in concepts]
    requires_oracle = any(concept.selector is not None for concept in concepts)
    project_root = Path.cwd().resolve()
    output_root = Path(args.output_dir).resolve()
    command = [sys.executable, "-m", "tests.quality.dynamic_campaign_test", *sys.argv[1:]]

    try:
        prepare_campaign(
            project_root=project_root,
            output_root=output_root,
            base_seed=base_seed,
            seeds=seeds,
            cases_per_seed=args.cases,
            concept_ids=concept_ids,
            oracle_file=args.oracle_file,
            workers=args.workers,
            requires_oracle=requires_oracle,
            resume=args.resume,
            command=command,
        )
    except (DynamicCampaignError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Base seed : {base_seed}")
    print(f"Seeds     : {', '.join(str(seed) for seed in seeds)}")
    print(f"Runs      : {len(seeds)}")
    print(f"Cases/run : {args.cases}")
    print(f"Workers   : {args.workers} process(es)")
    print(f"Resume    : {'yes' if args.resume else 'no'}")
    print(f"Output    : {output_root}")
    print("Purpose   : evaluation only; no training or automatic learning")

    campaign_start = time.perf_counter()
    run_summaries = []
    scenarios = []
    run_errors = []
    payload = None

    try:
        run_summaries, scenarios, run_errors = execute_campaign_runs(
            project_root=project_root,
            output_root=output_root,
            base_seed=base_seed,
            seeds=seeds,
            cases_per_seed=args.cases,
            concept_ids=concept_ids,
            oracle_file=args.oracle_file,
            workers=args.workers,
            requires_oracle=requires_oracle,
            fail_fast=args.fail_fast,
            resume=args.resume,
        )
        total_elapsed = time.perf_counter() - campaign_start
        payload = build_campaign_payload(
            base_seed=base_seed,
            seeds=seeds,
            cases_per_seed=args.cases,
            run_summaries=run_summaries,
            scenarios=scenarios,
            concepts=concepts,
            total_elapsed=total_elapsed,
        )
        payload.update(
            {
                "artifact_purpose": "evaluation",
                "training_allowed": False,
                "automatic_learning": False,
                "automatic_promotion": False,
                "workers": args.workers,
                "resume": args.resume,
                "run_errors": run_errors,
            }
        )
        if run_errors:
            payload["status"] = "FAIL"
        summary_paths = write_campaign_summary(output_root, payload)
        final_status = "failed" if payload["status"] == "FAIL" else "completed"
        finalize_campaign_manifest(
            output_root,
            status=final_status,
            run_summaries=run_summaries,
            run_errors=run_errors,
            elapsed_seconds=total_elapsed,
        )
    except (DynamicCampaignError, FileNotFoundError, ValueError) as exc:
        total_elapsed = time.perf_counter() - campaign_start
        with_exception = [*run_errors, {"error": str(exc)}]
        try:
            finalize_campaign_manifest(
                output_root,
                status="failed",
                run_summaries=run_summaries,
                run_errors=with_exception,
                elapsed_seconds=total_elapsed,
            )
        except Exception:
            pass
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print()
    print("=" * 80)
    print("CAMPAIGN RESULT")
    print("=" * 80)
    print(f"Runs     : {payload['runs_executed']}/{payload['runs_requested']}")
    print(f"Cases    : {payload['cases_executed']}")
    print(f"Failures : {payload['failures']}")
    print(f"Warnings : {payload['warnings']}")
    print(f"Errors   : {len(run_errors)}")
    print(
        f"Templates: {payload['coverage']['templates_seen']}/"
        f"{payload['coverage']['templates_expected']}"
    )
    print(f"Origins  : {payload.get('origin_counts', {})}")
    print(f"LLM calls: {payload.get('llm_calls', 0)}")
    print(f"Timings  : {payload.get('timing_means', {})}")
    print(f"Status   : {payload['status']}")
    print(f"TXT      : {summary_paths['txt']}")
    print(f"JSON     : {summary_paths['json']}")
    print(f"HTML     : {summary_paths['html']}")

    if run_errors or payload["failures"]:
        return 1
    if args.require_full_coverage and not payload["coverage"]["complete"]:
        return 1
    if payload["warnings"] and args.fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
