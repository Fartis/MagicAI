import argparse
import re
import sys
import time
import traceback
import unicodedata
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

from magicai.assistant import MagicAI
from magicai.conversation.models import Conversation

try:

    from tests.quality.reddit_gauntlet_cases import QUALITY_CASES

except ModuleNotFoundError:

    from reddit_gauntlet_cases import QUALITY_CASES


DEFAULT_TXT = "resultado_reddit_gauntlet.txt"
DEFAULT_XML = "resultado_reddit_gauntlet.xml"
DEFAULT_HTML = "resultado_reddit_gauntlet.html"


STATUS_ORDER = {
    "PASS": 0,
    "WARN": 1,
    "FAIL": 2,
}


def normalize(text: str) -> str:

    text = text or ""

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return text.lower()


def contains_term(text: str, term: str) -> bool:

    return normalize(term) in normalize(text)


def _missing_required_all(
    answer: str,
    terms: list[str],
    label: str,
) -> list[str]:

    return [
        f"Missing {label} term: {term}"
        for term in terms
        if not contains_term(
            answer,
            term,
        )
    ]


def _missing_required_any(
    answer: str,
    groups: list[list[str]],
    label: str,
) -> list[str]:

    failures = []

    for group in groups:

        if not any(
            contains_term(
                answer,
                term,
            )
            for term in group
        ):

            failures.append(
                f"Missing one of {label} alternatives: "
                + ", ".join(group)
            )

    return failures


def contains_forbidden_term(text: str, term: str) -> bool:
    normalized_text = normalize(text)
    normalized_term = normalize(term)

    if not normalized_term:
        return False

    pattern = re.compile(
        r"(?<!\w)" + re.escape(normalized_term) + r"(?!\w)"
    )
    matches = list(pattern.finditer(normalized_text))

    if not matches:
        return False

    # A forbidden proposition must not be reported when the answer explicitly
    # negates it, e.g. "No son lo mismo" or "no se contrarresta". Terms that
    # already begin with a negation keep their literal meaning. Exact token
    # boundaries also prevent "no se activa" from matching "no se activan".
    if re.match(r"^(?:no|nunca|jamas)\b", normalized_term):
        return True

    for match in matches:
        prefix = normalized_text[max(0, match.start() - 12):match.start()]

        if not re.search(r"\b(?:no|nunca|jamas)\s+$", prefix):
            return True

    return False


def _present_forbidden(
    answer: str,
    terms: list[str],
    label: str,
) -> list[str]:

    return [
        f"{label} term present: {term}"
        for term in terms
        if contains_forbidden_term(
            answer,
            term,
        )
    ]


def validate_answer(
    answer: str,
    required_all: list[str],
    required_any: list[list[str]],
    forbidden: list[str],
    recommended_all: list[str] | None = None,
    recommended_any: list[list[str]] | None = None,
    soft_forbidden: list[str] | None = None,
) -> tuple[list[str], list[str]]:

    failures = []
    warnings = []

    failures.extend(
        _missing_required_all(
            answer=answer,
            terms=required_all,
            label="required",
        )
    )

    failures.extend(
        _missing_required_any(
            answer=answer,
            groups=required_any,
            label="required",
        )
    )

    failures.extend(
        _present_forbidden(
            answer=answer,
            terms=forbidden,
            label="Forbidden",
        )
    )

    warnings.extend(
        _missing_required_all(
            answer=answer,
            terms=recommended_all or [],
            label="recommended",
        )
    )

    warnings.extend(
        _missing_required_any(
            answer=answer,
            groups=recommended_any or [],
            label="recommended",
        )
    )

    warnings.extend(
        _present_forbidden(
            answer=answer,
            terms=soft_forbidden or [],
            label="Soft-forbidden",
        )
    )

    return failures, warnings


def status_from_findings(
    failures: list[str],
    warnings: list[str],
) -> str:

    if failures:

        return "FAIL"

    if warnings:

        return "WARN"

    return "PASS"


def aggregate_status(
    statuses: list[str],
) -> str:

    if not statuses:

        return "PASS"

    return max(
        statuses,
        key=lambda status: STATUS_ORDER[status],
    )


def run_case(
    assistant: MagicAI,
    case: dict,
) -> dict:

    conversation = Conversation()

    case_start = time.perf_counter()

    steps = []
    case_failures = []
    case_warnings = []

    for index, step in enumerate(
        case["steps"],
        start=1,
    ):

        question = step["question"]

        step_start = time.perf_counter()

        answer = ""
        exception_text = ""

        try:

            answer = assistant.ask(
                conversation,
                question,
            )

        except Exception:

            exception_text = traceback.format_exc()

        elapsed = time.perf_counter() - step_start

        failures = []
        warnings = []

        if exception_text:

            failures.append(
                "Exception during answer generation."
            )

        else:

            step_failures, step_warnings = validate_answer(
                answer=answer,
                required_all=step.get(
                    "required_all",
                    [],
                ),
                required_any=step.get(
                    "required_any",
                    [],
                ),
                forbidden=step.get(
                    "forbidden",
                    [],
                ),
                recommended_all=step.get(
                    "recommended_all",
                    [],
                ),
                recommended_any=step.get(
                    "recommended_any",
                    [],
                ),
                soft_forbidden=step.get(
                    "soft_forbidden",
                    [],
                ),
            )

            failures.extend(step_failures)
            warnings.extend(step_warnings)

        status = status_from_findings(
            failures=failures,
            warnings=warnings,
        )

        if failures:

            case_failures.extend(
                [
                    f"Step {index}: {failure}"
                    for failure in failures
                ]
            )

        if warnings:

            case_warnings.extend(
                [
                    f"Step {index}: {warning}"
                    for warning in warnings
                ]
            )

        steps.append(
            {
                "index": index,
                "question": question,
                "answer": answer,
                "elapsed": elapsed,
                "status": status,
                "failures": failures,
                "warnings": warnings,
                "exception": exception_text,
                "required_all": step.get(
                    "required_all",
                    [],
                ),
                "required_any": step.get(
                    "required_any",
                    [],
                ),
                "recommended_all": step.get(
                    "recommended_all",
                    [],
                ),
                "recommended_any": step.get(
                    "recommended_any",
                    [],
                ),
                "forbidden": step.get(
                    "forbidden",
                    [],
                ),
                "soft_forbidden": step.get(
                    "soft_forbidden",
                    [],
                ),
            }
        )

    case_elapsed = time.perf_counter() - case_start

    return {
        "id": case["id"],
        "name": case["name"],
        "tags": case.get(
            "tags",
            [],
        ),
        "status": aggregate_status(
            [
                step["status"]
                for step in steps
            ]
        ),
        "elapsed": case_elapsed,
        "failures": case_failures,
        "warnings": case_warnings,
        "steps": steps,
    }


def collect_steps(
    results: list[dict],
) -> list[dict]:

    return [
        step
        for result in results
        for step in result["steps"]
    ]


def count_steps_by_status(
    results: list[dict],
    status: str,
) -> int:

    return sum(
        1
        for step in collect_steps(results)
        if step["status"] == status
    )


def count_cases_by_status(
    results: list[dict],
    status: str,
) -> int:

    return sum(
        1
        for result in results
        if result["status"] == status
    )


def suite_status(
    results: list[dict],
) -> str:

    return aggregate_status(
        [
            result["status"]
            for result in results
        ]
    )


def write_txt_report(
    results: list[dict],
    output_file: Path,
    total_elapsed: float,
    suite_name: str = "MagicAI Reddit Gauntlet Quality Test",
    metadata: dict[str, str] | None = None,
):

    lines = []

    total_steps = sum(
        len(result["steps"])
        for result in results
    )

    failed_cases = [
        result
        for result in results
        if result["status"] == "FAIL"
    ]

    warning_cases = [
        result
        for result in results
        if result["status"] == "WARN"
    ]

    failed_steps = [
        step
        for step in collect_steps(results)
        if step["status"] == "FAIL"
    ]

    warning_steps = [
        step
        for step in collect_steps(results)
        if step["status"] == "WARN"
    ]

    current_suite_status = suite_status(results)

    lines.append("=" * 80)
    lines.append(suite_name)
    lines.append("=" * 80)
    lines.append("")

    for key, value in (metadata or {}).items():
        lines.append(f"{key:<11}: {value}")

    if metadata:
        lines.append("")

    lines.append(f"Cases      : {len(results)}")
    lines.append(f"Steps      : {total_steps}")
    lines.append(f"Failures   : {len(failed_steps)}")
    lines.append(f"Warnings   : {len(warning_steps)}")
    lines.append(f"Time       : {total_elapsed:.2f}s")
    lines.append(f"Status     : {current_suite_status}")
    lines.append("")

    for result in results:

        lines.append("=" * 80)
        lines.append(
            f"{result['id']} - {result['name']} [{result['status']}] "
            f"({result['elapsed']:.2f}s)"
        )
        lines.append("=" * 80)
        lines.append(
            "Tags: "
            + ", ".join(result["tags"])
        )
        lines.append("")

        for step in result["steps"]:

            lines.append(
                f"Step {step['index']} [{step['status']}] "
                f"({step['elapsed']:.2f}s)"
            )
            lines.append("-" * 80)
            lines.append("QUESTION:")
            lines.append(step["question"])
            lines.append("")
            lines.append("ANSWER:")
            lines.append(step["answer"])
            lines.append("")

            if step["failures"]:

                lines.append("FAILURES:")

                for failure in step["failures"]:

                    lines.append(f"- {failure}")

                lines.append("")

            if step["warnings"]:

                lines.append("WARNINGS:")

                for warning in step["warnings"]:

                    lines.append(f"- {warning}")

                lines.append("")

            if step["exception"]:

                lines.append("EXCEPTION:")
                lines.append(step["exception"])
                lines.append("")

        lines.append("")

    lines.append("=" * 80)
    lines.append("RESULT")
    lines.append("=" * 80)
    lines.append(f"Cases   : {len(results)}")
    lines.append(f"Steps   : {total_steps}")
    lines.append(f"Failures: {len(failed_steps)}")
    lines.append(f"Warnings: {len(warning_steps)}")
    lines.append(f"Status  : {current_suite_status}")
    lines.append("")

    if failed_cases:

        lines.append("FAILED CASES:")

        for result in failed_cases:

            lines.append(
                f"- {result['id']} - {result['name']}"
            )

        lines.append("")

    if warning_cases:

        lines.append("WARNING CASES:")

        for result in warning_cases:

            lines.append(
                f"- {result['id']} - {result['name']}"
            )

        lines.append("")

    output_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _append_terms(
    parent: ET.Element,
    terms: list[str],
):

    for term in terms:

        term_node = ET.SubElement(
            parent,
            "term",
        )
        term_node.text = term


def _append_term_groups(
    parent: ET.Element,
    groups: list[list[str]],
):

    for group in groups:

        group_node = ET.SubElement(
            parent,
            "group",
        )

        _append_terms(
            group_node,
            group,
        )


def write_xml_report(
    results: list[dict],
    output_file: Path,
    total_elapsed: float,
    suite_name: str = "MagicAI Reddit Gauntlet",
    metadata: dict[str, str] | None = None,
):

    total_steps = sum(
        len(result["steps"])
        for result in results
    )

    failed_steps = [
        step
        for step in collect_steps(results)
        if step["status"] == "FAIL"
    ]

    warning_steps = [
        step
        for step in collect_steps(results)
        if step["status"] == "WARN"
    ]

    current_suite_status = suite_status(results)

    root = ET.Element(
        "qualitySuite",
        {
            "name": suite_name,
            "cases": str(len(results)),
            "steps": str(total_steps),
            "failures": str(len(failed_steps)),
            "warnings": str(len(warning_steps)),
            "time": f"{total_elapsed:.3f}",
            "status": current_suite_status,
        },
    )

    if metadata:
        metadata_node = ET.SubElement(root, "metadata")

        for key, value in metadata.items():
            item_node = ET.SubElement(metadata_node, "item", {"key": key})
            item_node.text = value

    for result in results:

        case_node = ET.SubElement(
            root,
            "case",
            {
                "id": result["id"],
                "name": result["name"],
                "status": result["status"],
                "time": f"{result['elapsed']:.3f}",
                "tags": ",".join(result["tags"]),
            },
        )

        for step in result["steps"]:

            step_node = ET.SubElement(
                case_node,
                "step",
                {
                    "index": str(step["index"]),
                    "status": step["status"],
                    "time": f"{step['elapsed']:.3f}",
                },
            )

            question_node = ET.SubElement(
                step_node,
                "question",
            )
            question_node.text = step["question"]

            answer_node = ET.SubElement(
                step_node,
                "answer",
            )
            answer_node.text = step["answer"]

            expectations_node = ET.SubElement(
                step_node,
                "expectations",
            )

            required_all_node = ET.SubElement(
                expectations_node,
                "requiredAll",
            )
            _append_terms(
                required_all_node,
                step["required_all"],
            )

            required_any_node = ET.SubElement(
                expectations_node,
                "requiredAny",
            )
            _append_term_groups(
                required_any_node,
                step["required_any"],
            )

            recommended_all_node = ET.SubElement(
                expectations_node,
                "recommendedAll",
            )
            _append_terms(
                recommended_all_node,
                step["recommended_all"],
            )

            recommended_any_node = ET.SubElement(
                expectations_node,
                "recommendedAny",
            )
            _append_term_groups(
                recommended_any_node,
                step["recommended_any"],
            )

            forbidden_node = ET.SubElement(
                expectations_node,
                "forbidden",
            )
            _append_terms(
                forbidden_node,
                step["forbidden"],
            )

            soft_forbidden_node = ET.SubElement(
                expectations_node,
                "softForbidden",
            )
            _append_terms(
                soft_forbidden_node,
                step["soft_forbidden"],
            )

            failures_node = ET.SubElement(
                step_node,
                "failures",
            )
            _append_terms(
                failures_node,
                step["failures"],
            )

            warnings_node = ET.SubElement(
                step_node,
                "warnings",
            )
            _append_terms(
                warnings_node,
                step["warnings"],
            )

            if step["exception"]:

                exception_node = ET.SubElement(
                    step_node,
                    "exception",
                )
                exception_node.text = step["exception"]

    tree = ET.ElementTree(
        root,
    )

    ET.indent(
        tree,
        space="  ",
    )

    tree.write(
        output_file,
        encoding="utf-8",
        xml_declaration=True,
    )


def _format_tags(
    tags: list[str],
) -> str:

    if not tags:

        return ""

    return "".join(
        f'<span class="tag">{escape(tag)}</span>'
        for tag in tags
    )


def _format_terms(
    terms: list[str],
) -> str:

    if not terms:

        return '<span class="muted">—</span>'

    return "".join(
        f'<span class="term">{escape(term)}</span>'
        for term in terms
    )


def _format_term_groups(
    groups: list[list[str]],
) -> str:

    if not groups:

        return '<span class="muted">—</span>'

    group_html = []

    for group in groups:

        group_html.append(
            '<div class="term-group">'
            + _format_terms(group)
            + "</div>"
        )

    return "".join(group_html)


def _format_findings(
    title: str,
    items: list[str],
    css_class: str,
) -> str:

    if not items:

        return ""

    return (
        f'<div class="{css_class}"><h4>{escape(title)}</h4><ul>'
        + "".join(
            f"<li>{escape(item)}</li>"
            for item in items
        )
        + "</ul></div>"
    )


def write_html_report(
    results: list[dict],
    output_file: Path,
    total_elapsed: float,
    suite_name: str = "MagicAI Reddit Gauntlet",
    suite_subtitle: str = (
        "Suite de calidad semántica para preguntas reales de reglas y Commander."
    ),
    metadata: dict[str, str] | None = None,
):

    total_steps = sum(
        len(result["steps"])
        for result in results
    )

    passed_steps = count_steps_by_status(
        results,
        "PASS",
    )
    warning_steps = count_steps_by_status(
        results,
        "WARN",
    )
    failed_steps = count_steps_by_status(
        results,
        "FAIL",
    )

    passed_cases = count_cases_by_status(
        results,
        "PASS",
    )
    warning_cases = count_cases_by_status(
        results,
        "WARN",
    )
    failed_cases = count_cases_by_status(
        results,
        "FAIL",
    )

    pass_percent = (
        0
        if total_steps == 0
        else round(
            passed_steps * 100 / total_steps,
            1,
        )
    )

    warn_percent = (
        0
        if total_steps == 0
        else round(
            warning_steps * 100 / total_steps,
            1,
        )
    )

    current_suite_status = suite_status(results)
    status_class = current_suite_status.lower()
    status_label = current_suite_status

    rows = []

    for result in results:

        rows.append(
            "<tr>"
            f"<td>{escape(result['id'])}</td>"
            f"<td>{escape(result['name'])}</td>"
            f"<td><span class=\"badge {result['status'].lower()}\">{escape(result['status'])}</span></td>"
            f"<td>{len(result['steps'])}</td>"
            f"<td>{result['elapsed']:.2f}s</td>"
            f"<td>{_format_tags(result['tags'])}</td>"
            "</tr>"
        )

    case_sections = []

    for result in results:

        open_attr = (
            " open"
            if result["status"] != "PASS"
            else ""
        )

        step_sections = []

        for step in result["steps"]:

            failures_html = _format_findings(
                title="Fallos",
                items=step["failures"],
                css_class="failures",
            )

            warnings_html = _format_findings(
                title="Avisos",
                items=step["warnings"],
                css_class="warnings",
            )

            exception_html = ""

            if step["exception"]:

                exception_html = (
                    '<div class="exception"><h4>Excepción</h4>'
                    f"<pre>{escape(step['exception'])}</pre></div>"
                )

            step_sections.append(
                '<section class="step">'
                '<div class="step-header">'
                f"<span>Step {step['index']}</span>"
                f"<span class=\"badge {step['status'].lower()}\">{escape(step['status'])}</span>"
                f"<span>{step['elapsed']:.2f}s</span>"
                "</div>"
                '<div class="qa-grid">'
                "<div>"
                "<h4>Pregunta</h4>"
                f"<p>{escape(step['question'])}</p>"
                "</div>"
                "<div>"
                "<h4>Respuesta</h4>"
                f"<p>{escape(step['answer'])}</p>"
                "</div>"
                "</div>"
                '<div class="expectations-grid">'
                "<div>"
                "<h4>Requeridos</h4>"
                f"{_format_terms(step['required_all'])}"
                "</div>"
                "<div>"
                "<h4>Alternativas requeridas</h4>"
                f"{_format_term_groups(step['required_any'])}"
                "</div>"
                "<div>"
                "<h4>Prohibidos</h4>"
                f"{_format_terms(step['forbidden'])}"
                "</div>"
                "</div>"
                '<div class="expectations-grid soft">'
                "<div>"
                "<h4>Recomendados</h4>"
                f"{_format_terms(step['recommended_all'])}"
                "</div>"
                "<div>"
                "<h4>Alternativas recomendadas</h4>"
                f"{_format_term_groups(step['recommended_any'])}"
                "</div>"
                "<div>"
                "<h4>Soft-forbidden</h4>"
                f"{_format_terms(step['soft_forbidden'])}"
                "</div>"
                "</div>"
                f"{failures_html}"
                f"{warnings_html}"
                f"{exception_html}"
                "</section>"
            )

        case_sections.append(
            f"<details class=\"case-card {result['status'].lower()}\"{open_attr}>"
            "<summary>"
            f"<span>{escape(result['id'])} — {escape(result['name'])}</span>"
            f"<span class=\"badge {result['status'].lower()}\">{escape(result['status'])}</span>"
            f"<span>{result['elapsed']:.2f}s</span>"
            "</summary>"
            f"<div class=\"case-tags\">{_format_tags(result['tags'])}</div>"
            + "".join(step_sections)
            + "</details>"
        )

    metadata_html = "".join(
        '<div class="metric">'
        f'<strong>{escape(value)}</strong>'
        f'<span>{escape(key)}</span>'
        '</div>'
        for key, value in (metadata or {}).items()
    )

    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(suite_name)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #111827;
      --panel: #1f2937;
      --panel-2: #273449;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --border: #374151;
      --pass: #22c55e;
      --pass-bg: rgba(34, 197, 94, .14);
      --warn: #f59e0b;
      --warn-bg: rgba(245, 158, 11, .16);
      --fail: #ef4444;
      --fail-bg: rgba(239, 68, 68, .14);
      --accent: #60a5fa;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(96, 165, 250, .16), transparent 28rem),
        var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{
      width: min(1200px, calc(100% - 32px));
      margin: 32px auto 64px;
    }}
    header {{
      display: flex;
      gap: 18px;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(1.8rem, 4vw, 3rem);
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
    }}
    .suite-status {{
      padding: 10px 14px;
      border-radius: 999px;
      font-weight: 800;
      letter-spacing: .08em;
      border: 1px solid var(--border);
    }}
    .suite-status.pass {{
      color: var(--pass);
      background: var(--pass-bg);
    }}
    .suite-status.warn {{
      color: var(--warn);
      background: var(--warn-bg);
    }}
    .suite-status.fail {{
      color: var(--fail);
      background: var(--fail-bg);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 12px;
      margin: 20px 0;
    }}
    .metric {{
      background: linear-gradient(180deg, var(--panel), rgba(31, 41, 55, .78));
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
    }}
    .metric strong {{
      display: block;
      font-size: 1.65rem;
    }}
    .metric span {{
      color: var(--muted);
      font-size: .9rem;
    }}
    .progress {{
      display: flex;
      height: 16px;
      border-radius: 999px;
      overflow: hidden;
      background: var(--panel);
      border: 1px solid var(--border);
      margin: 18px 0 26px;
    }}
    .progress-pass {{
      height: 100%;
      width: {pass_percent}%;
      background: linear-gradient(90deg, var(--pass), var(--accent));
    }}
    .progress-warn {{
      height: 100%;
      width: {warn_percent}%;
      background: var(--warn);
    }}
    .summary-table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
      margin-bottom: 24px;
    }}
    .summary-table th,
    .summary-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    .summary-table th {{
      color: var(--muted);
      font-size: .82rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      background: rgba(255, 255, 255, .03);
    }}
    .summary-table tr:last-child td {{
      border-bottom: 0;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: .78rem;
      font-weight: 800;
      letter-spacing: .04em;
      border: 1px solid var(--border);
    }}
    .badge.pass {{
      color: var(--pass);
      background: var(--pass-bg);
    }}
    .badge.warn {{
      color: var(--warn);
      background: var(--warn-bg);
    }}
    .badge.fail {{
      color: var(--fail);
      background: var(--fail-bg);
    }}
    .tag,
    .term {{
      display: inline-block;
      margin: 3px 5px 3px 0;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(96, 165, 250, .12);
      border: 1px solid rgba(96, 165, 250, .25);
      color: #bfdbfe;
      font-size: .82rem;
    }}
    .term {{
      background: rgba(255, 255, 255, .06);
      border-color: var(--border);
      color: var(--text);
    }}
    .muted {{
      color: var(--muted);
    }}
    .case-card {{
      margin: 14px 0;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
    }}
    .case-card.warn {{
      border-color: rgba(245, 158, 11, .55);
    }}
    .case-card.fail {{
      border-color: rgba(239, 68, 68, .45);
    }}
    .case-card > summary {{
      cursor: pointer;
      padding: 16px;
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 12px;
      align-items: center;
      background: rgba(255, 255, 255, .03);
      font-weight: 750;
    }}
    .case-tags {{
      padding: 12px 16px 0;
    }}
    .step {{
      margin: 16px;
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: var(--panel-2);
    }}
    .step-header {{
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 14px;
      color: var(--muted);
    }}
    .step-header span:first-child {{
      color: var(--text);
      font-weight: 700;
    }}
    .qa-grid,
    .expectations-grid {{
      display: grid;
      grid-template-columns: 1fr 1.4fr;
      gap: 14px;
    }}
    .expectations-grid {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 14px;
    }}
    .expectations-grid.soft {{
      opacity: .92;
    }}
    h4 {{
      margin: 0 0 8px;
      color: var(--muted);
      text-transform: uppercase;
      font-size: .78rem;
      letter-spacing: .08em;
    }}
    p {{
      margin: 0;
      white-space: pre-wrap;
    }}
    .failures,
    .warnings,
    .exception {{
      margin-top: 14px;
      padding: 12px;
      border-radius: 12px;
    }}
    .failures,
    .exception {{
      border: 1px solid rgba(239, 68, 68, .45);
      background: var(--fail-bg);
    }}
    .warnings {{
      border: 1px solid rgba(245, 158, 11, .55);
      background: var(--warn-bg);
    }}
    pre {{
      white-space: pre-wrap;
      overflow: auto;
      margin: 0;
    }}
    @media (max-width: 850px) {{
      header,
      .qa-grid,
      .expectations-grid {{
        grid-template-columns: 1fr;
        display: grid;
      }}
      header {{
        display: grid;
      }}
      .case-card > summary {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>{escape(suite_name)}</h1>
        <p class="subtitle">{escape(suite_subtitle)}</p>
      </div>
      <div class="suite-status {status_class}">{status_label}</div>
    </header>

    <section class="metrics">
      {metadata_html}
      <div class="metric"><strong>{len(results)}</strong><span>Casos</span></div>
      <div class="metric"><strong>{total_steps}</strong><span>Preguntas</span></div>
      <div class="metric"><strong>{passed_cases}</strong><span>Casos OK</span></div>
      <div class="metric"><strong>{warning_cases}</strong><span>Casos WARN</span></div>
      <div class="metric"><strong>{failed_cases}</strong><span>Casos KO</span></div>
      <div class="metric"><strong>{passed_steps}</strong><span>Steps OK</span></div>
      <div class="metric"><strong>{warning_steps}</strong><span>Steps WARN</span></div>
      <div class="metric"><strong>{failed_steps}</strong><span>Steps KO</span></div>
      <div class="metric"><strong>{total_elapsed:.1f}s</strong><span>Tiempo</span></div>
    </section>

    <div class="progress" title="{pass_percent}% pass · {warn_percent}% warn">
      <div class="progress-pass"></div>
      <div class="progress-warn"></div>
    </div>

    <table class="summary-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Caso</th>
          <th>Estado</th>
          <th>Steps</th>
          <th>Tiempo</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>

    <section>
      {''.join(case_sections)}
    </section>
  </main>
</body>
</html>
"""

    output_file.write_text(
        html,
        encoding="utf-8",
    )


def parse_args():

    parser = argparse.ArgumentParser(
        description="Run the MagicAI Reddit Gauntlet quality suite.",
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
        "--fail-fast",
        action="store_true",
        help="Stop on first failing case.",
    )

    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Return a non-zero exit code if there are warnings but no failures.",
    )

    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only a specific case id. Can be used multiple times.",
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
        for case in QUALITY_CASES
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

        print(
            f"[{case['id']}] {case['name']}"
        )

        result = run_case(
            assistant,
            case,
        )

        results.append(
            result,
        )

        print(
            f"  {result['status']} ({result['elapsed']:.2f}s)"
        )

        if (
            args.fail_fast
            and result["status"] == "FAIL"
        ):

            break

    total_elapsed = time.perf_counter() - suite_start

    txt_file = Path(
        args.txt,
    )

    xml_file = Path(
        args.xml,
    )

    html_file = Path(
        args.html,
    )

    write_txt_report(
        results=results,
        output_file=txt_file,
        total_elapsed=total_elapsed,
    )

    write_xml_report(
        results=results,
        output_file=xml_file,
        total_elapsed=total_elapsed,
    )

    write_html_report(
        results=results,
        output_file=html_file,
        total_elapsed=total_elapsed,
    )

    failed_steps = count_steps_by_status(
        results,
        "FAIL",
    )

    warning_steps = count_steps_by_status(
        results,
        "WARN",
    )

    current_suite_status = suite_status(results)

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
    print(f"Status  : {current_suite_status}")
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

    sys.exit(
        main()
    )