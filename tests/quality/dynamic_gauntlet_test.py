from __future__ import annotations

import argparse
import secrets
import sys
import time
from pathlib import Path

from magicai.assistant import MagicAI
from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.dynamic.concepts import CONCEPTS, get_concepts
from tests.quality.dynamic.failure_store import (
    load_replay,
    save_failure,
    write_manifest,
)
from tests.quality.dynamic.scenario_generator import ScenarioGenerator
from tests.quality.reddit_gauntlet_test import (
    count_steps_by_status,
    run_case,
    suite_status,
    write_html_report,
    write_txt_report,
    write_xml_report,
)


DEFAULT_TXT = "resultado_dynamic_gauntlet.txt"
DEFAULT_XML = "resultado_dynamic_gauntlet.xml"
DEFAULT_HTML = "resultado_dynamic_gauntlet.html"
DEFAULT_MANIFEST = "resultado_dynamic_gauntlet_manifest.json"
DEFAULT_FAILURE_DIR = "resultado_dynamic_gauntlet_failures"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run a seeded, reproducible MagicAI Dynamic Gauntlet using "
            "controlled question templates and local Scryfall Oracle data."
        ),
    )
    parser.add_argument("--seed", type=int, help="Reproducible random seed.")
    parser.add_argument(
        "--cases",
        type=int,
        default=30,
        help="Number of dynamic scenarios to generate. Default: 30.",
    )
    parser.add_argument(
        "--concept",
        action="append",
        default=[],
        help="Restrict generation to a concept id. Can be repeated.",
    )
    parser.add_argument(
        "--list-concepts",
        action="store_true",
        help="List available concept ids and exit.",
    )
    parser.add_argument(
        "--replay",
        help="Replay one previously saved scenario or failure JSON.",
    )
    parser.add_argument(
        "--oracle-file",
        help="Override sources/scryfall/oracle-cards.json.",
    )
    parser.add_argument("--txt", default=DEFAULT_TXT)
    parser.add_argument("--xml", default=DEFAULT_XML)
    parser.add_argument("--html", default=DEFAULT_HTML)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--failure-dir", default=DEFAULT_FAILURE_DIR)
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true")
    return parser.parse_args()


def _print_concepts():
    print("Available dynamic concepts:")

    for concept in CONCEPTS:
        print(f"- {concept.id}: {concept.name}")


def _generate_scenarios(args):
    if args.replay:
        scenario = load_replay(args.replay)
        return scenario.seed, [scenario], None

    seed = args.seed if args.seed is not None else secrets.randbits(32)
    concepts = get_concepts(args.concept)
    catalog = CardCatalog(args.oracle_file)
    generator = ScenarioGenerator(
        seed=seed,
        catalog=catalog,
        concepts=concepts,
    )
    scenarios = generator.generate(args.cases)
    manifest = write_manifest(args.manifest, seed, scenarios)
    return seed, scenarios, manifest


def main():
    args = parse_args()

    if args.list_concepts:
        _print_concepts()
        return 0

    try:
        seed, scenarios, manifest = _generate_scenarios(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Seed     : {seed}")
    print(f"Cases    : {len(scenarios)}")

    if args.replay:
        print(f"Replay   : {args.replay}")
    elif manifest is not None:
        print(f"Manifest : {manifest}")

    assistant = MagicAI()
    results = []
    saved_failures = []
    suite_start = time.perf_counter()

    for scenario in scenarios:
        print(
            f"[{scenario.id}] {scenario.concept_id} · "
            f"{scenario.card_name} · {scenario.template_id}"
        )
        result = run_case(assistant, scenario.to_case())
        result["dynamic"] = scenario.to_dict()
        results.append(result)
        print(f"  {result['status']} ({result['elapsed']:.2f}s)")

        if result["status"] == "FAIL":
            failure_file = save_failure(args.failure_dir, scenario, result)
            saved_failures.append(failure_file)
            print(f"  Saved failure: {failure_file}")

            if args.fail_fast:
                break

    total_elapsed = time.perf_counter() - suite_start
    metadata = {
        "Seed": str(seed),
        "Generated cases": str(len(scenarios)),
        "Executed cases": str(len(results)),
        "Mode": "replay" if args.replay else "generated",
    }

    write_txt_report(
        results=results,
        output_file=Path(args.txt),
        total_elapsed=total_elapsed,
        suite_name="MagicAI Dynamic Gauntlet",
        metadata=metadata,
    )
    write_xml_report(
        results=results,
        output_file=Path(args.xml),
        total_elapsed=total_elapsed,
        suite_name="MagicAI Dynamic Gauntlet",
        metadata=metadata,
    )
    write_html_report(
        results=results,
        output_file=Path(args.html),
        total_elapsed=total_elapsed,
        suite_name="MagicAI Dynamic Gauntlet",
        suite_subtitle=(
            "Escenarios reproducibles generados desde Oracle y contratos "
            "deterministas de reglas."
        ),
        metadata=metadata,
    )

    failed_steps = count_steps_by_status(results, "FAIL")
    warning_steps = count_steps_by_status(results, "WARN")
    current_status = suite_status(results)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Seed    : {seed}")
    print(f"Cases   : {len(results)}")
    print(f"Failures: {failed_steps}")
    print(f"Warnings: {warning_steps}")
    print(f"Status  : {current_status}")
    print(f"TXT     : {args.txt}")
    print(f"XML     : {args.xml}")
    print(f"HTML    : {args.html}")

    if manifest is not None:
        print(f"Manifest: {manifest}")

    if saved_failures:
        print(f"Replays : {len(saved_failures)} file(s) in {args.failure_dir}")

    if failed_steps:
        return 1

    if warning_steps and args.fail_on_warn:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
