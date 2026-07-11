import argparse
import sys
import time
from pathlib import Path

from magicai.assistant import MagicAI
from tests.quality.generalization_probe_cases import GENERALIZATION_CASES
from tests.quality.reddit_gauntlet_test import (
    run_case,
    write_txt_report,
    write_xml_report,
    write_html_report,
    count_steps_by_status,
    suite_status,
)


DEFAULT_TXT = "resultado_generalization_probe.txt"
DEFAULT_XML = "resultado_generalization_probe.xml"
DEFAULT_HTML = "resultado_generalization_probe.html"


def parse_args():

    parser = argparse.ArgumentParser(
        description="Run MagicAI generalization probe cases.",
    )

    parser.add_argument(
        "--txt",
        default=DEFAULT_TXT,
        help="TXT report output path.",
    )

    parser.add_argument(
        "--xml",
        default=DEFAULT_XML,
        help="XML report output path.",
    )

    parser.add_argument(
        "--html",
        default=DEFAULT_HTML,
        help="HTML report output path.",
    )

    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only a specific case id. Can be used multiple times.",
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failing case.",
    )

    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Return a non-zero exit code if there are warnings but no failures.",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    selected_ids = {
        item.upper()
        for item in args.case
    }

    cases = [
        case
        for case in GENERALIZATION_CASES
        if not selected_ids
        or case["id"].upper() in selected_ids
    ]

    if not cases:

        print("No cases selected.")
        return 1

    assistant = MagicAI()
    results = []
    suite_start = time.perf_counter()

    for case in cases:

        print(f"[{case['id']}] {case['name']}")

        result = run_case(
            assistant,
            case,
        )

        results.append(result)

        print(f"  {result['status']} ({result['elapsed']:.2f}s)")

        if args.fail_fast and result["status"] == "FAIL":

            break

    total_elapsed = time.perf_counter() - suite_start

    txt_file = Path(args.txt)
    xml_file = Path(args.xml)
    html_file = Path(args.html)

    write_txt_report(
        results=results,
        output_file=txt_file,
        total_elapsed=total_elapsed,
        suite_name="MagicAI Generalization Probe",
    )

    write_xml_report(
        results=results,
        output_file=xml_file,
        total_elapsed=total_elapsed,
        suite_name="MagicAI Generalization Probe",
    )

    write_html_report(
        results=results,
        output_file=html_file,
        total_elapsed=total_elapsed,
        suite_name="MagicAI Generalization Probe",
        suite_subtitle=(
            "Pruebas de generalización y regresión semántica del Juez."
        ),
    )

    failed_steps = count_steps_by_status(
        results,
        "FAIL",
    )

    warning_steps = count_steps_by_status(
        results,
        "WARN",
    )

    current_status = suite_status(results)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Cases   : {len(results)}")
    print(
        "Steps   : "
        + str(
            sum(
                len(result["steps"])
                for result in results
            )
        )
    )
    print(f"Failures: {failed_steps}")
    print(f"Warnings: {warning_steps}")
    print(f"Status  : {current_status}")
    print(f"TXT     : {txt_file}")
    print(f"XML     : {xml_file}")
    print(f"HTML    : {html_file}")

    if failed_steps:

        print("FAILED")
        return 1

    if warning_steps and args.fail_on_warn:

        print("WARNINGS")
        return 1

    if warning_steps:

        print("WARNINGS")
        return 0

    print("OK")
    return 0


if __name__ == "__main__":

    sys.exit(main())
