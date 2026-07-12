from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from html import escape
from pathlib import Path
from typing import Iterable

from .models import ACCEPTABLE_OUTCOMES, OpenJudgeCaseResult, OpenJudgeOutcome


def collect_turns(results: Iterable[OpenJudgeCaseResult]):
    return [turn for result in results for turn in result.turns]


def outcome_counts(results: list[OpenJudgeCaseResult]) -> Counter[str]:
    return Counter(turn.outcome.value for turn in collect_turns(results))


def write_json_report(
    results: list[OpenJudgeCaseResult],
    output_file: Path,
    metadata: dict[str, object],
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    turns = collect_turns(results)
    payload = {
        "suite": "MagicAI Open Judge Gauntlet",
        "metadata": metadata,
        "summary": {
            "cases": len(results),
            "turns": len(turns),
            "outcomes": dict(sorted(outcome_counts(results).items())),
        },
        "results": [result.to_dict() for result in results],
    }
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_txt_report(
    results: list[OpenJudgeCaseResult],
    output_file: Path,
    metadata: dict[str, object],
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    turns = collect_turns(results)
    counts = outcome_counts(results)
    lines = [
        "=" * 80,
        "MagicAI Open Judge Gauntlet",
        "=" * 80,
        "",
    ]

    for key, value in metadata.items():
        lines.append(f"{key:<14}: {value}")

    lines.extend(
        [
            "",
            f"Cases         : {len(results)}",
            f"Turns         : {len(turns)}",
            "",
            "Outcomes",
            "--------",
        ]
    )

    for outcome in OpenJudgeOutcome:
        lines.append(f"{outcome.value:<26}: {counts.get(outcome.value, 0)}")

    lines.append("")

    for result in results:
        lines.extend(
            [
                "=" * 80,
                f"{result.id} - {result.name} [{result.outcome.value}]",
                f"Tags: {', '.join(result.tags)}",
                "=" * 80,
                "",
            ]
        )

        for turn in result.turns:
            lines.extend(
                [
                    f"{turn.turn_id} [{turn.outcome.value}] ({turn.elapsed:.2f}s)",
                    f"USER: {turn.question}",
                    f"ASSISTANT: {turn.answer}",
                    "STATE:",
                    f"  cards={list(turn.snapshot.cards)}",
                    f"  keywords={list(turn.snapshot.keywords)}",
                    f"  rules={list(turn.snapshot.rules)}",
                    f"  intent={turn.snapshot.intent!r}",
                    f"  history={turn.snapshot.history_size}",
                    "JUDGE RESULT:",
                    f"  status={turn.judge_status!r}",
                    f"  origin={turn.judge_origin!r}",
                    f"  confidence={turn.judge_confidence!r}",
                    f"  authority={turn.judge_authority!r}",
                ]
            )

            if turn.findings:
                lines.append("FINDINGS:")
                lines.extend(
                    f"  - {finding.outcome.value}: {finding.message}"
                    for finding in turn.findings
                )

            if turn.exception:
                lines.extend(["EXCEPTION:", turn.exception])

            if turn.internal_log:
                lines.extend(["INTERNAL LOG:", turn.internal_log])

            lines.extend(["", "-" * 80, ""])

    output_file.write_text("\n".join(lines), encoding="utf-8")


def write_xml_report(
    results: list[OpenJudgeCaseResult],
    output_file: Path,
    metadata: dict[str, object],
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    turns = collect_turns(results)
    root = ET.Element(
        "testsuite",
        {
            "name": "MagicAI Open Judge Gauntlet",
            "tests": str(len(turns)),
            "failures": str(
                sum(
                    turn.outcome not in ACCEPTABLE_OUTCOMES
                    for turn in turns
                )
            ),
        },
    )

    properties = ET.SubElement(root, "properties")
    for key, value in metadata.items():
        ET.SubElement(
            properties,
            "property",
            {"name": str(key), "value": str(value)},
        )

    for result in results:
        for turn in result.turns:
            testcase = ET.SubElement(
                root,
                "testcase",
                {
                    "classname": result.id,
                    "name": turn.turn_id,
                    "time": f"{turn.elapsed:.6f}",
                },
            )
            ET.SubElement(testcase, "system-out").text = (
                turn.answer
                + "\n\nJudgeResult: "
                + f"status={turn.judge_status}; origin={turn.judge_origin}; "
                + f"confidence={turn.judge_confidence}; authority={turn.judge_authority}"
            )

            if turn.outcome not in ACCEPTABLE_OUTCOMES:
                failure = ET.SubElement(
                    testcase,
                    "failure",
                    {
                        "type": turn.outcome.value,
                        "message": "; ".join(
                            finding.message for finding in turn.findings
                        ),
                    },
                )
                failure.text = "\n".join(
                    f"{finding.outcome.value}: {finding.message}"
                    for finding in turn.findings
                )

    ET.ElementTree(root).write(
        output_file,
        encoding="utf-8",
        xml_declaration=True,
    )



def write_failure_artifacts(
    results: list[OpenJudgeCaseResult],
    output_dir: Path,
) -> int:
    failures_dir = output_dir / "open_judge_failures"
    written = 0

    for result in results:
        for turn in result.turns:
            if turn.outcome in ACCEPTABLE_OUTCOMES:
                continue

            failures_dir.mkdir(parents=True, exist_ok=True)
            target = failures_dir / f"{turn.turn_id}_{turn.outcome.value}.json"
            target.write_text(
                json.dumps(turn.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            written += 1

    return written


def write_html_report(
    results: list[OpenJudgeCaseResult],
    output_file: Path,
    metadata: dict[str, object],
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    counts = outcome_counts(results)
    turns = collect_turns(results)

    summary_rows = "".join(
        "<tr><td>"
        + escape(outcome.value)
        + "</td><td>"
        + str(counts.get(outcome.value, 0))
        + "</td></tr>"
        for outcome in OpenJudgeOutcome
    )

    metadata_rows = "".join(
        f"<tr><td>{escape(str(key))}</td><td>{escape(str(value))}</td></tr>"
        for key, value in metadata.items()
    )

    case_sections: list[str] = []
    for result in results:
        turns_html: list[str] = []
        for turn in result.turns:
            findings = "".join(
                "<li><strong>"
                + escape(finding.outcome.value)
                + ":</strong> "
                + escape(finding.message)
                + "</li>"
                for finding in turn.findings
            ) or "<li>None</li>"

            turns_html.append(
                f"""
                <article class="turn">
                  <h3>{escape(turn.turn_id)} · {escape(turn.outcome.value)}</h3>
                  <p><strong>User:</strong> {escape(turn.question)}</p>
                  <p><strong>Assistant:</strong> {escape(turn.answer)}</p>
                  <p><strong>Cards:</strong> {escape(', '.join(turn.snapshot.cards))}</p>
                  <p><strong>JudgeResult:</strong> status={escape(turn.judge_status)}, origin={escape(turn.judge_origin)}, confidence={escape(turn.judge_confidence)}, authority={escape(turn.judge_authority)}</p>
                  <p><strong>Elapsed:</strong> {turn.elapsed:.2f}s</p>
                  <details><summary>Findings</summary><ul>{findings}</ul></details>
                </article>
                """
            )

        case_sections.append(
            f"""
            <section>
              <h2>{escape(result.id)} · {escape(result.name)} · {escape(result.outcome.value)}</h2>
              <p>{escape(', '.join(result.tags))}</p>
              {''.join(turns_html)}
            </section>
            """
        )

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MagicAI Open Judge Gauntlet</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
th, td {{ border: 1px solid #bbb; padding: .5rem; text-align: left; }}
section {{ border-top: 3px solid #333; margin-top: 2rem; padding-top: 1rem; }}
.turn {{ border: 1px solid #bbb; border-radius: .5rem; margin: 1rem 0; padding: 1rem; }}
code, pre {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>MagicAI Open Judge Gauntlet</h1>
<p>{len(results)} cases · {len(turns)} conversational turns</p>
<h2>Run metadata</h2>
<table><tbody>{metadata_rows}</tbody></table>
<h2>Semantic outcomes</h2>
<table><thead><tr><th>Outcome</th><th>Turns</th></tr></thead><tbody>{summary_rows}</tbody></table>
{''.join(case_sections)}
</body>
</html>
"""
    output_file.write_text(html, encoding="utf-8")
