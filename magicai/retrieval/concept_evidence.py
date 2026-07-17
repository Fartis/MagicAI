from __future__ import annotations

import re


_CONCEPT_RULES: dict[str, tuple[str, ...]] = {
    # Ward must never fall back merely because a keyword-dense card displaced
    # general trigger/stack/priority evidence from the bounded context.
    "ward": ("702.21a", "603.1", "405.1", "117.5"),
    # An activated or triggered ability on the stack is independent from its
    # source, but resolution can still need source information or the object.
    "source_independence": ("113.7a", "405.1", "608.2h", "609.3"),
    # Land-type-setting interactions need a complete, reserved layer package.
    # This prevents incidental Oracle keywords from displacing timestamp,
    # dependency, basic-supertype, and intrinsic-mana evidence.
    "basic_land_layer_interaction": (
        "305.6",
        "305.7",
        "305.8",
        "611.3",
        "613.1d",
        "613.7",
        "613.8a",
        "613.8b",
    ),
}


def detected_evidence_concepts(question: str) -> tuple[str, ...]:
    q = _normalize(question)
    concepts: list[str] = []
    if re.search(r"\bward\b", q):
        concepts.append("ward")
    if _looks_like_source_independence(q):
        concepts.append("source_independence")
    if _looks_like_basic_land_layer_interaction(q):
        concepts.append("basic_land_layer_interaction")
    return tuple(concepts)


def mandatory_rule_numbers(question: str) -> tuple[str, ...]:
    numbers: list[str] = []
    for concept in detected_evidence_concepts(question):
        for number in _CONCEPT_RULES[concept]:
            if number not in numbers:
                numbers.append(number)
    return tuple(numbers)



def _looks_like_basic_land_layer_interaction(question: str) -> bool:
    has_land_types = any(
        marker in question
        for marker in (
            "tipo de tierra",
            "tipos de tierra",
            "tierra basica",
            "tierra básica",
            "tierras basicas",
            "tierras básicas",
            "tierra no basica",
            "tierra no básica",
            "tierras no basicas",
            "tierras no básicas",
            "land type",
            "land types",
            "basic land",
            "nonbasic land",
        )
    )
    has_ordering = any(
        marker in question
        for marker in (
            "capa",
            "capas",
            "layer",
            "layers",
            "dependencia",
            "dependency",
            "timestamp",
            "marca de tiempo",
            "orden de entrada",
            "antes que",
            "despues que",
            "después que",
        )
    )
    has_mana_or_effect = any(
        marker in question
        for marker in (
            "habilidad de mana",
            "habilidad de maná",
            "habilidades de mana",
            "habilidades de maná",
            "pueden producir",
            "produce mana",
            "produce maná",
            "mana ability",
            "mana abilities",
            "in addition to their other types",
            "ademas de sus otros tipos",
            "además de sus otros tipos",
        )
    )
    return has_land_types and has_ordering and has_mana_or_effect


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
