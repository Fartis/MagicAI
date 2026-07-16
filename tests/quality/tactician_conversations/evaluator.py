from __future__ import annotations

from tests.quality.tactician_conversations.semantic_assertions import has_concept


def evaluate_turn(payload: dict, expected: dict) -> list[str]:
    failures: list[str] = []
    for field in (
        "strategy_intent",
        "combo_classification",
        "response_language",
        "response_mode",
        "judge_verified",
        "answer_complete",
        "factual_core_preserved",
        "tactician_synthesized",
        "origin",
    ):
        if field in expected and payload.get(field) != expected[field]:
            failures.append(f"{field}: expected {expected[field]!r}, got {payload.get(field)!r}")

    answer = str(payload.get("answer", ""))
    for phrase in expected.get("required_phrases", []):
        if phrase.casefold() not in answer.casefold():
            failures.append(f"missing required phrase: {phrase}")
    for phrase in expected.get("forbidden_phrases", []):
        if phrase.casefold() in answer.casefold():
            failures.append(f"forbidden phrase present: {phrase}")

    for concept in expected.get("required_concepts", []):
        if not has_concept(answer, concept):
            failures.append(f"missing required concept: {concept}")
    for concept in expected.get("forbidden_concepts", []):
        if has_concept(answer, concept):
            failures.append(f"forbidden concept present: {concept}")

    rule_numbers = {str(item.get("number", "")) for item in payload.get("rules", [])}
    for number in expected.get("required_rules", []):
        if number not in rule_numbers:
            failures.append(f"missing required rule: {number}")

    card_names = {str(item.get("name", "")).casefold() for item in payload.get("cards", [])}
    for name in expected.get("required_cards", []):
        if name.casefold() not in card_names:
            failures.append(f"missing required card: {name}")

    tools = {str(item.get("tool", "")) for item in payload.get("judge_tool_calls", [])}
    for tool in expected.get("required_tools", []):
        if tool not in tools:
            failures.append(f"missing required tool: {tool}")

    minimum_coverage = expected.get("minimum_factual_core_coverage")
    if minimum_coverage is not None:
        coverage = payload.get("factual_core_coverage", {})
        required = int(coverage.get("required", 0))
        covered = int(coverage.get("covered", 0))
        ratio = 1.0 if required == 0 else covered / required
        if ratio < float(minimum_coverage):
            failures.append(
                f"factual core coverage: expected >= {minimum_coverage}, got {covered}/{required}"
            )

    forbidden_trace = expected.get("forbidden_authority_trace", [])
    trace = set(payload.get("authority_trace", []))
    for item in forbidden_trace:
        if item in trace:
            failures.append(f"forbidden authority trace present: {item}")

    return failures
