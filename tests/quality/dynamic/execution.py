from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Iterable

from tests.quality.dynamic.failure_store import save_failure
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.reddit_gauntlet_test import (
    count_steps_by_status,
    run_case,
    suite_status,
    write_html_report,
    write_txt_report,
    write_xml_report,
)

ProgressCallback = Callable[[DynamicScenario, dict[str, Any]], None]


def run_dynamic_scenarios(
    assistant,
    scenarios: Iterable[DynamicScenario],
    *,
    failure_dir: str | Path,
    fail_fast: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[dict[str, Any]], list[Path], float]:
    results: list[dict[str, Any]] = []
    saved_failures: list[Path] = []
    suite_start = time.perf_counter()

    for scenario in scenarios:
        result = run_case(assistant, scenario.to_case())
        result["dynamic"] = scenario.to_dict()
        results.append(result)

        if result["status"] == "FAIL":
            failure_file = save_failure(failure_dir, scenario, result)
            saved_failures.append(failure_file)
            result["dynamic_failure_file"] = str(failure_file)

        if progress_callback is not None:
            progress_callback(scenario, result)

        if result["status"] == "FAIL" and fail_fast:
            break

    total_elapsed = time.perf_counter() - suite_start
    return results, saved_failures, total_elapsed


def write_dynamic_reports(
    *,
    results: list[dict[str, Any]],
    txt_file: str | Path,
    xml_file: str | Path,
    html_file: str | Path,
    total_elapsed: float,
    metadata: dict[str, str],
    suite_name: str = "MagicAI Dynamic Gauntlet",
    suite_subtitle: str = (
        "Escenarios reproducibles generados desde Oracle y contratos "
        "deterministas de reglas."
    ),
) -> None:
    write_txt_report(
        results=results,
        output_file=Path(txt_file),
        total_elapsed=total_elapsed,
        suite_name=suite_name,
        metadata=metadata,
    )
    write_xml_report(
        results=results,
        output_file=Path(xml_file),
        total_elapsed=total_elapsed,
        suite_name=suite_name,
        metadata=metadata,
    )
    write_html_report(
        results=results,
        output_file=Path(html_file),
        total_elapsed=total_elapsed,
        suite_name=suite_name,
        suite_subtitle=suite_subtitle,
        metadata=metadata,
    )


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    failures = count_steps_by_status(results, "FAIL")
    warnings = count_steps_by_status(results, "WARN")
    return {
        "cases": len(results),
        "failures": failures,
        "warnings": warnings,
        "status": suite_status(results),
    }
