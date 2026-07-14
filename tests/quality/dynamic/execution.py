from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Iterable

from tests.quality.dynamic.failure_store import save_failure
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.premise_validation import validate_dynamic_premise
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
        premise_failures = validate_dynamic_premise(scenario)
        if premise_failures:
            result = _premise_failure_result(scenario, premise_failures)
        else:
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
    origin_counts: dict[str, int] = {}
    timing_sums: dict[str, float] = {}
    timing_counts: dict[str, int] = {}
    llm_calls = 0
    for result in results:
        for step in result.get("steps", []):
            judge_result = step.get("judge_result") or {}
            origin = str(judge_result.get("origin", "") or "")
            if origin:
                origin_counts[origin] = origin_counts.get(origin, 0) + 1
            if judge_result.get("llm_called"):
                llm_calls += 1
            for name, value in (judge_result.get("timings") or {}).items():
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                timing_sums[name] = timing_sums.get(name, 0.0) + numeric
                timing_counts[name] = timing_counts.get(name, 0) + 1
    timing_means = {
        name: round(timing_sums[name] / timing_counts[name], 6)
        for name in sorted(timing_sums)
        if timing_counts.get(name)
    }
    return {
        "cases": len(results),
        "failures": failures,
        "warnings": warnings,
        "status": suite_status(results),
        "origin_counts": dict(sorted(origin_counts.items())),
        "llm_calls": llm_calls,
        "timing_means": timing_means,
        "timing_sums": {name: round(value, 6) for name, value in sorted(timing_sums.items())},
        "timing_counts": dict(sorted(timing_counts.items())),
    }


def _premise_failure_result(
    scenario: DynamicScenario,
    failures: list[str],
) -> dict[str, Any]:
    step = scenario.contract.to_step(scenario.question)
    return {
        "id": scenario.id,
        "name": scenario.concept_name + (f" · {scenario.card_name}" if scenario.card_name else ""),
        "tags": list(scenario.tags),
        "status": "FAIL",
        "elapsed": 0.0,
        "failures": [f"Step 1: Invalid generated premise: {item}" for item in failures],
        "warnings": [],
        "steps": [
            {
                "index": 1,
                "question": scenario.question,
                "answer": "",
                "elapsed": 0.0,
                "status": "FAIL",
                "failures": [f"Invalid generated premise: {item}" for item in failures],
                "warnings": [],
                "exception": "",
                "judge_result": {},
                "required_all": step.get("required_all", []),
                "required_any": step.get("required_any", []),
                "recommended_all": step.get("recommended_all", []),
                "recommended_any": step.get("recommended_any", []),
                "forbidden": step.get("forbidden", []),
                "soft_forbidden": step.get("soft_forbidden", []),
            }
        ],
    }
