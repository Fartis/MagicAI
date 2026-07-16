from __future__ import annotations


def evaluate_turn(payload: dict, expected: dict) -> list[str]:
    failures: list[str] = []
    for field in (
        "strategy_intent",
        "combo_classification",
        "response_language",
        "judge_verified",
        "answer_complete",
    ):
        if field in expected and payload.get(field) != expected[field]:
            failures.append(f"{field}: expected {expected[field]!r}, got {payload.get(field)!r}")

    answer = str(payload.get("answer", ""))
    for phrase in expected.get("required_phrases", []):
        if phrase not in answer:
            failures.append(f"missing required phrase: {phrase}")
    for phrase in expected.get("forbidden_phrases", []):
        if phrase.casefold() in answer.casefold():
            failures.append(f"forbidden phrase present: {phrase}")

    rule_numbers = {str(item.get("number", "")) for item in payload.get("rules", [])}
    for number in expected.get("required_rules", []):
        if number not in rule_numbers:
            failures.append(f"missing required rule: {number}")
    return failures
