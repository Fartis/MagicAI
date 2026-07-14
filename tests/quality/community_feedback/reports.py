from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from .diagnostics import build_findings_by_family
from .models import FeedbackCaseResult, FeedbackOutcome


EVALUATION_CONTRACT = {
    "artifact_purpose": "evaluation",
    "training_allowed": False,
    "automatic_learning": False,
    "automatic_promotion": False,
}


def write_feedback_reports(
    results: list[FeedbackCaseResult],
    output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(results, output_dir / "community_feedback_summary.json", metadata)
    write_markdown(results, output_dir / "community_feedback_summary.md", metadata)
    write_html(results, output_dir / "community_feedback_summary.html", metadata)
    write_review_packets(results, output_dir / "review_packets", metadata)
    _atomic_write_json(
        output_dir / "findings_by_family.json",
        build_findings_by_family(results),
    )


def write_json(
    results: list[FeedbackCaseResult],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    payload = {
        "suite": "MagicAI Community Feedback Gauntlet",
        **EVALUATION_CONTRACT,
        "metadata": metadata,
        "summary": _summary(results),
        "results": [result.to_dict() for result in results],
    }
    _atomic_write_json(path, payload)


def write_markdown(
    results: list[FeedbackCaseResult],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    lines = [
        "# MagicAI Community Feedback Gauntlet",
        "",
        "> Manual, paraphrased cases. Community material is scenario input, not factual authority.",
        "> Evaluation only: no training, automatic learning or automatic promotion.",
        "",
    ]
    for key, value in metadata.items():
        lines.append(f"- **{key}:** {value}")
    lines.append("")

    for result in results:
        source = result.case.source
        lines.extend(
            [
                f"## {result.case.id} — {result.case.title}",
                "",
                f"- **Mode:** {result.case.mode.value}",
                f"- **Outcome:** {result.outcome.value}",
                f"- **Source platform:** {source.platform}",
                f"- **Source topic:** {source.topic_id or 'not provided'}",
                f"- **Current-rules review:** {result.case.review.status}",
                f"- **Tags:** {', '.join(result.case.tags) or 'none'}",
                "",
            ]
        )
        if source.url:
            lines.append(f"- **Source URL:** {source.url}")
            lines.append("")
        if result.case.review.expected_summary:
            lines.extend(
                [
                    "### Expected summary after validation",
                    "",
                    result.case.review.expected_summary,
                    "",
                ]
            )

        for turn in result.turns:
            lines.extend(
                [
                    f"### {turn.turn_id} — {turn.outcome.value}",
                    "",
                    f"- **Diagnostic family:** {turn.failure_family.value}",
                    "",
                    f"**Question:** {turn.question}",
                    "",
                    f"**MagicAI:** {turn.answer}",
                    "",
                    "**JudgeResult:**",
                    "",
                    "```json",
                    json.dumps(turn.judge_result, ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
            if turn.findings:
                lines.append("**Findings:**")
                lines.append("")
                for finding in turn.findings:
                    lines.append(f"- `{finding.outcome}` — {finding.message}")
                lines.append("")

    _atomic_write_text(path, "\n".join(lines).rstrip() + "\n")


def write_html(
    results: list[FeedbackCaseResult],
    path: Path,
    metadata: dict[str, Any],
) -> None:
    cards: list[str] = []
    for result in results:
        turns: list[str] = []
        for turn in result.turns:
            findings = "".join(
                f"<li><strong>{escape(item.outcome)}</strong>: {escape(item.message)}</li>"
                for item in turn.findings
            )
            turns.append(
                "<section class='turn'>"
                f"<h3>{escape(turn.turn_id)} <span>{escape(turn.outcome.value)}</span></h3>"
                f"<p class='family'><strong>Diagnostic family:</strong> {escape(turn.failure_family.value)}</p>"
                f"<p><strong>Question:</strong> {escape(turn.question)}</p>"
                f"<p><strong>MagicAI:</strong> {escape(turn.answer)}</p>"
                f"<details><summary>JudgeResult</summary><pre>{escape(json.dumps(turn.judge_result, ensure_ascii=False, indent=2))}</pre></details>"
                f"<ul>{findings}</ul>"
                "</section>"
            )
        source = result.case.source
        source_line = f"{source.platform} · {source.topic_id or 'no topic id'}"
        if source.url:
            source_line += f" · {source.url}"
        cards.append(
            "<article class='case'>"
            f"<h2>{escape(result.case.id)} — {escape(result.case.title)}</h2>"
            f"<p class='meta'>{escape(result.case.mode.value)} · {escape(result.outcome.value)} · {escape(source_line)}</p>"
            + "".join(turns)
            + "</article>"
        )

    summary = _summary(results)
    html = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>MagicAI Community Feedback Gauntlet</title>
<style>
:root{{--bg:#111827;--panel:#1f2937;--border:#374151;--text:#f3f4f6;--muted:#9ca3af;--accent:#60a5fa;}}
body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,sans-serif;}}
main{{max-width:1180px;margin:auto;padding:32px 20px 64px;}}
h1,h2,h3{{margin-top:0}} .meta{{color:var(--muted)}} .family{{color:var(--accent)}}
.summary,.case,.turn{{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:18px;margin:16px 0;}}
.turn{{background:#172033}} h3 span{{color:var(--accent);font-size:.8em}} pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
a{{color:var(--accent)}}
</style>
</head>
<body><main>
<h1>MagicAI Community Feedback Gauntlet</h1>
<p>Manual paraphrased cases. Current official sources remain the factual authority.</p>
<p><strong>Evaluation only:</strong> no model training, automatic learning or automatic promotion.</p>
<section class='summary'><strong>Cases:</strong> {summary['cases']} · <strong>Turns:</strong> {summary['turns']} · <strong>Generated:</strong> {escape(str(metadata.get('created_at', '')))}</section>
{''.join(cards)}
</main></body></html>"""
    _atomic_write_text(path, html)


def write_review_packets(
    results: list[FeedbackCaseResult],
    output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        payload = result.to_dict()
        payload.update(EVALUATION_CONTRACT)
        payload["packet_metadata"] = metadata
        target = output_dir / f"{_safe_name(result.case.id)}_review.json"
        existing_decision = _read_existing_review_decision(target)
        default_family = next(
            (
                turn.failure_family.value
                for turn in result.turns
                if turn.failure_family.value != "NO_FAILURE"
            ),
            "NO_FAILURE",
        )
        payload["review_decision"] = existing_decision or {
            "current_sources_checked": False,
            "decision": "",
            "failure_family": default_family,
            "required_facts": [],
            "forbidden_claims": [],
            "generic_fix": "",
            "promote_to_regression": False,
            "review_notes": "",
        }
        _atomic_write_json(target, payload)


def _read_existing_review_decision(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    decision = payload.get("review_decision") if isinstance(payload, dict) else None
    return dict(decision) if isinstance(decision, dict) else None


def _summary(results: list[FeedbackCaseResult]) -> dict[str, Any]:
    turns = [turn for result in results for turn in result.turns]
    counts = Counter(turn.outcome.value for turn in turns)
    families = Counter(turn.failure_family.value for turn in turns)
    return {
        "cases": len(results),
        "turns": len(turns),
        "outcomes": dict(sorted(counts.items())),
        "failure_families": dict(sorted(families.items())),
        "review_required": counts.get(FeedbackOutcome.REVIEW_REQUIRED.value, 0),
    }


def _safe_name(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in value
    )
    return cleaned.strip("_") or datetime.now().strftime("feedback_%Y%m%d_%H%M%S")


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
