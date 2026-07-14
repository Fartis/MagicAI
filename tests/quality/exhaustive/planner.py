from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from tests.quality.dynamic.card_catalog import CardAbilityCandidate, CardCandidate, CardCatalog
from tests.quality.dynamic.concepts import get_concepts
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.scenario_generator import build_bound_scenario

FAMILY_ORDER = ("mana_ability", "ward", "undying_exile", "source_independence")
FAMILY_SELECTORS = {
    "mana_ability": ("ability", "mana_ability"),
    "ward": ("card", "ward"),
    "undying_exile": ("card", "undying"),
    "source_independence": ("ability", "source_independence_ability"),
}
_LEADING_SOURCE_PRONOUN_RE = re.compile(
    r"^(?:then\s+)?(?:it|he|she|they)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ExhaustivePlan:
    scenarios: tuple[DynamicScenario, ...]
    static_summary: dict[str, object]
    static_findings: tuple[dict[str, object], ...]


def normalize_families(families: Iterable[str]) -> tuple[str, ...]:
    requested = tuple(dict.fromkeys(item.strip() for item in families if item.strip()))
    if not requested:
        return FAMILY_ORDER
    unknown = sorted(set(requested) - set(FAMILY_ORDER))
    if unknown:
        raise ValueError("Unknown exhaustive family/families: " + ", ".join(unknown))
    return tuple(item for item in FAMILY_ORDER if item in requested)


def build_exhaustive_plan(
    catalog: CardCatalog,
    *,
    families: Iterable[str] = (),
    template_mode: str = "one",
    max_cases: int | None = None,
) -> ExhaustivePlan:
    selected_families = normalize_families(families)
    if template_mode not in {"one", "all"}:
        raise ValueError("template_mode must be 'one' or 'all'")
    if max_cases is not None and max_cases <= 0:
        raise ValueError("max_cases must be greater than zero")

    cards = catalog.load()
    scenarios: list[DynamicScenario] = []
    findings: list[dict[str, object]] = []
    candidate_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()

    concepts = {concept.id: concept for concept in get_concepts(selected_families)}
    global_ordinal = 0

    for family in selected_families:
        concept = concepts[family]
        kind, selector = FAMILY_SELECTORS[family]
        candidates: list[CardCandidate | CardAbilityCandidate]
        if kind == "ability":
            candidates = list(catalog.select_abilities(selector))
        else:
            candidates = list(catalog.select(selector))
        candidate_counts[family] = len(candidates)

        for family_ordinal, candidate in enumerate(candidates, start=1):
            if isinstance(candidate, CardAbilityCandidate):
                card = candidate.card
                ability = candidate.ability
                dependency_counts[ability.source_dependency] += 1
                findings.extend(_static_ability_findings(family, candidate))
            else:
                card = candidate
                ability = None

            templates = (
                concept.templates
                if template_mode == "all"
                else (concept.templates[(family_ordinal - 1) % len(concept.templates)],)
            )
            for template in templates:
                global_ordinal += 1
                prefix = {
                    "mana_ability": "MA",
                    "ward": "WA",
                    "undying_exile": "UN",
                    "source_independence": "SI",
                }[family]
                scenario = build_bound_scenario(
                    scenario_id=f"EX-{prefix}-{global_ordinal:06d}",
                    seed=0,
                    concept=concept,
                    template=template,
                    card=card,
                    ability=ability,
                    extra_tags=(
                        "exhaustive",
                        f"candidate-family:{family}",
                        f"candidate-ordinal:{family_ordinal}",
                    ),
                )
                scenarios.append(scenario)
                template_counts[f"{family}:{template.id}"] += 1
                if max_cases is not None and len(scenarios) >= max_cases:
                    return _finish_plan(
                        scenarios,
                        findings,
                        cards=cards,
                        families=selected_families,
                        candidate_counts=candidate_counts,
                        dependency_counts=dependency_counts,
                        template_counts=template_counts,
                        template_mode=template_mode,
                        truncated=True,
                    )

    return _finish_plan(
        scenarios,
        findings,
        cards=cards,
        families=selected_families,
        candidate_counts=candidate_counts,
        dependency_counts=dependency_counts,
        template_counts=template_counts,
        template_mode=template_mode,
        truncated=False,
    )


def _finish_plan(
    scenarios: list[DynamicScenario],
    findings: list[dict[str, object]],
    *,
    cards: list[CardCandidate],
    families: tuple[str, ...],
    candidate_counts: Counter[str],
    dependency_counts: Counter[str],
    template_counts: Counter[str],
    template_mode: str,
    truncated: bool,
) -> ExhaustivePlan:
    summary = {
        "artifact_purpose": "evaluation",
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "supported_cards": len(cards),
        "families": list(families),
        "candidate_counts": dict(sorted(candidate_counts.items())),
        "candidate_total": sum(candidate_counts.values()),
        "scenario_total": len(scenarios),
        "template_mode": template_mode,
        "template_counts": dict(sorted(template_counts.items())),
        "source_dependency_counts": dict(sorted(dependency_counts.items())),
        "static_findings": len(findings),
        "truncated": truncated,
    }
    return ExhaustivePlan(
        scenarios=tuple(scenarios),
        static_summary=summary,
        static_findings=tuple(findings),
    )


def _static_ability_findings(
    family: str,
    candidate: CardAbilityCandidate,
) -> list[dict[str, object]]:
    ability = candidate.ability
    card = candidate.card
    findings: list[dict[str, object]] = []
    if (
        family == "source_independence"
        and ability.source_dependency == "independent"
        and _LEADING_SOURCE_PRONOUN_RE.search(_strip_nonsemantic_text(ability.effect))
    ):
        findings.append(
            {
                "kind": "source_pronoun_classified_independent",
                "family": family,
                "card_name": card.name,
                "type_line": card.type_line,
                "ability_index": ability.index,
                "ability_text": ability.text,
                "effect": ability.effect,
                "source_dependency": ability.source_dependency,
            }
        )
    if family == "source_independence" and ability.source_removed_as_cost:
        findings.append(
            {
                "kind": "invalid_source_candidate_removes_itself_as_cost",
                "family": family,
                "card_name": card.name,
                "ability_index": ability.index,
                "ability_text": ability.text,
            }
        )
    return findings


def _strip_nonsemantic_text(text: str) -> str:
    result: list[str] = []
    parentheses = 0
    quote_closer = ""
    pairs = {'"': '"', '“': '”', '«': '»'}
    for char in text or "":
        if quote_closer:
            if char == quote_closer:
                quote_closer = ""
            continue
        if char in pairs:
            quote_closer = pairs[char]
            continue
        if char == "(":
            parentheses += 1
            continue
        if char == ")" and parentheses:
            parentheses -= 1
            continue
        if parentheses == 0:
            result.append(char)
    return " ".join("".join(result).split())
