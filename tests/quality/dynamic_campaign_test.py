from __future__ import annotations

import argparse
import secrets
import sys
import time
from pathlib import Path

from magicai.assistant import MagicAI
from tests.quality.dynamic.campaign import (
    build_campaign_payload,
    resolve_campaign_seeds,
    write_campaign_summary,
)
from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.dynamic.concepts import CONCEPTS, get_concepts
from tests.quality.dynamic.execution import (
    run_dynamic_scenarios,
    summarize_results,
    write_dynamic_reports,
)
from tests.quality.dynamic.failure_store import write_manifest
from tests.quality.dynamic.scenario_generator import ScenarioGenerator

DEFAULT_OUTPUT_DIR = "resultado_dynamic_campaign"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run a reproducible multi-seed MagicAI Dynamic Gauntlet campaign "
            "and aggregate concept/template coverage."
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


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def main():
    args = parse_args()

    if args.list_concepts:
        _print_concepts()
        return 0

    if args.cases <= 0:
        print("ERROR: --cases must be greater than zero.", file=sys.stderr)
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
        catalog = CardCatalog(args.oracle_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    assistant = MagicAI()
    run_summaries = []
    all_scenarios = []
    campaign_start = time.perf_counter()

    print(f"Base seed : {base_seed}")
    print(f"Seeds     : {', '.join(str(seed) for seed in seeds)}")
    print(f"Runs      : {len(seeds)}")
    print(f"Cases/run : {args.cases}")
    print(f"Output    : {output_root}")

    for run_index, seed in enumerate(seeds, start=1):
        run_dir = output_root / f"run_{run_index:02d}_seed_{seed}"
        failure_dir = run_dir / "failures"
        generator = ScenarioGenerator(
            seed=seed,
            catalog=catalog,
            concepts=concepts,
        )
        scenarios = generator.generate(args.cases)
        manifest = write_manifest(run_dir / "manifest.json", seed, scenarios)

        print()
        print("=" * 80)
        print(f"RUN {run_index}/{len(seeds)} · seed {seed}")
        print("=" * 80)

        def _progress(scenario, result):
            source_label = scenario.card_name or "rules-only"
            print(
                f"[{scenario.id}] {scenario.concept_id} · "
                f"{source_label} · {scenario.template_id}"
            )
            print(f"  {result['status']} ({result['elapsed']:.2f}s)")

            if result.get("dynamic_failure_file"):
                print(f"  Saved failure: {result['dynamic_failure_file']}")

        results, saved_failures, elapsed = run_dynamic_scenarios(
            assistant,
            scenarios,
            failure_dir=failure_dir,
            fail_fast=args.fail_fast,
            progress_callback=_progress,
        )
        metadata = {
            "Campaign base seed": str(base_seed),
            "Campaign run": f"{run_index}/{len(seeds)}",
            "Seed": str(seed),
            "Generated cases": str(len(scenarios)),
            "Executed cases": str(len(results)),
            "Mode": "campaign",
        }
        txt_path = run_dir / "report.txt"
        xml_path = run_dir / "report.xml"
        html_path = run_dir / "report.html"
        write_dynamic_reports(
            results=results,
            txt_file=txt_path,
            xml_file=xml_path,
            html_file=html_path,
            total_elapsed=elapsed,
            metadata=metadata,
            suite_name="MagicAI Dynamic Campaign Run",
            suite_subtitle=(
                "Ejecución individual dentro de una campaña multisemilla "
                "reproducible."
            ),
        )
        summary = summarize_results(results)
        all_scenarios.extend(scenarios[: summary["cases"]])
        run_summaries.append(
            {
                "index": run_index,
                "seed": seed,
                "cases": summary["cases"],
                "failures": summary["failures"],
                "warnings": summary["warnings"],
                "status": summary["status"],
                "elapsed_seconds": round(elapsed, 6),
                "manifest": _relative(manifest, output_root),
                "txt": _relative(txt_path, output_root),
                "xml": _relative(xml_path, output_root),
                "html": _relative(html_path, output_root),
                "failure_files": [
                    _relative(path, output_root)
                    for path in saved_failures
                ],
            }
        )

        if summary["failures"] and args.fail_fast:
            break

    total_elapsed = time.perf_counter() - campaign_start
    payload = build_campaign_payload(
        base_seed=base_seed,
        seeds=seeds,
        cases_per_seed=args.cases,
        run_summaries=run_summaries,
        scenarios=all_scenarios,
        concepts=concepts,
        total_elapsed=total_elapsed,
    )
    summary_paths = write_campaign_summary(output_root, payload)

    print()
    print("=" * 80)
    print("CAMPAIGN RESULT")
    print("=" * 80)
    print(f"Runs     : {payload['runs_executed']}/{payload['runs_requested']}")
    print(f"Cases    : {payload['cases_executed']}")
    print(f"Failures : {payload['failures']}")
    print(f"Warnings : {payload['warnings']}")
    print(f"Templates: {payload['coverage']['templates_seen']}/"
          f"{payload['coverage']['templates_expected']}")
    print(f"Status   : {payload['status']}")
    print(f"TXT      : {summary_paths['txt']}")
    print(f"JSON     : {summary_paths['json']}")
    print(f"HTML     : {summary_paths['html']}")

    if payload["failures"]:
        return 1

    if args.require_full_coverage and not payload["coverage"]["complete"]:
        return 1

    if payload["warnings"] and args.fail_on_warn:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
