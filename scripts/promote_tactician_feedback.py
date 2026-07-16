#!/usr/bin/env python3
"""Create a reviewable conversational-gauntlet candidate from an exported result.

This command never modifies the regression corpus automatically. It creates a
candidate with structural expectations inferred from the export and marks it as
requiring human review before promotion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


def build_candidate(payload: dict[str, Any], *, candidate_id: str) -> dict[str, Any]:
    question = str(payload.get("question", "")).strip()
    if not question:
        raise ValueError("the exported result does not contain a question")

    language = str(payload.get("response_language") or payload.get("input_analysis", {}).get("language") or "es")
    if language not in {"es", "en"}:
        language = "es"

    cards = [
        str(card.get("name", "")).strip()
        for card in payload.get("cards", [])
        if isinstance(card, dict) and card.get("name")
    ]
    rules = [
        str(rule.get("number", "")).strip()
        for rule in payload.get("rules", [])
        if isinstance(rule, dict) and rule.get("number")
    ]
    tools = [
        str(call.get("tool", "")).strip()
        for call in payload.get("judge_tool_calls", [])
        if isinstance(call, dict) and call.get("tool")
    ]

    expect: dict[str, Any] = {
        "response_language": language,
        "review_required": True,
    }
    for field in (
        "strategy_intent",
        "response_mode",
        "combo_classification",
    ):
        value = payload.get(field)
        if value not in (None, ""):
            expect[field] = value
    if cards:
        expect["required_cards"] = _deduplicate(cards)
    if rules:
        expect["required_rules"] = _deduplicate(rules)
    if tools:
        expect["required_tools"] = _deduplicate(tools)

    return {
        "schema_version": "1.0",
        "candidate": {
            "id": candidate_id,
            "title": f"Candidate promoted from {question[:80]}",
            "language": language,
            "review_required": True,
            "source": {
                "origin": payload.get("origin", ""),
                "schema_version": payload.get("schema_version", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "turns": [
                {
                    "question": question,
                    "expect": expect,
                    "observed_answer": str(payload.get("answer", "")),
                    "review_notes": [
                        "Replace observed_answer with semantic requirements before moving this candidate into the regression corpus.",
                        "Add forbidden concepts for the failure mode that motivated the promotion.",
                    ],
                }
            ],
        },
    }


def promote_file(source: str | Path, output_dir: str | Path, *, candidate_id: str | None = None) -> Path:
    source_path = Path(source)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    resolved_id = candidate_id or _candidate_id(source_path.stem)
    candidate = build_candidate(payload, candidate_id=resolved_id)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{resolved_id.casefold().replace('_', '-')}.candidate.json"
    target.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _candidate_id(stem: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").upper()
    return f"TACT-CANDIDATE-{clean or 'FEEDBACK'}"


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a reviewable Tactician gauntlet candidate from an exported JSON result.")
    parser.add_argument("source")
    parser.add_argument("--output-dir", default="tests/quality/cases/tactician_conversations/candidates")
    parser.add_argument("--id", dest="candidate_id")
    args = parser.parse_args()

    target = promote_file(args.source, args.output_dir, candidate_id=args.candidate_id)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
