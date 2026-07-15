from __future__ import annotations

import re


_CONCEPT_RULES: dict[str, tuple[str, ...]] = {
    # Ward must never fall back merely because a keyword-dense card displaced
    # general trigger/stack/priority evidence from the bounded context.
    "ward": ("702.21a", "603.1", "405.1", "117.5"),
    # An activated or triggered ability on the stack is independent from its
    # source, but resolution can still need source information or the object.
    "source_independence": ("113.7a", "405.1", "608.2h", "609.3"),
}


def detected_evidence_concepts(question: str) -> tuple[str, ...]:
    q = _normalize(question)
    concepts: list[str] = []
    if re.search(r"\bward\b", q):
        concepts.append("ward")
    if _looks_like_source_independence(q):
        concepts.append("source_independence")
    return tuple(concepts)


def mandatory_rule_numbers(question: str) -> tuple[str, ...]:
    numbers: list[str] = []
    for concept in detected_evidence_concepts(question):
        for number in _CONCEPT_RULES[concept]:
            if number not in numbers:
                numbers.append(number)
    return tuple(numbers)


def _looks_like_source_independence(question: str) -> bool:
    has_ability = "habilidad" in question or "ability" in question
    has_stack_or_resolution = any(
        marker in question
        for marker in ("pila", "stack", "resolv", "contrarrest")
    )
    source_leaves = any(
        marker in question
        for marker in (
            "destruyen", "destruir", "retiran", "eliminan", "sacrific",
            "exilian", "fuente", "source leaves", "remove the source",
            "destroy the source",
        )
    )
    return has_ability and has_stack_or_resolution and source_leaves


def _normalize(text: str) -> str:
    return " ".join((text or "").casefold().split())
