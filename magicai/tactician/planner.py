from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from magicai.judge_tools import JudgeToolRequest
from magicai.tactician.input_analysis import InputAnalysis
from magicai.tactician.investigation import InvestigationHypothesis, build_hypotheses
from magicai.tactician.intents import StrategyIntent


@dataclass(slots=True)
class InvestigationPlan:
    requests: list[JudgeToolRequest] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    hypotheses: list[InvestigationHypothesis] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "queries_planned": len(self.requests),
            "goals": list(self.goals),
            "requests": [request.to_dict() for request in self.requests],
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
        }


def plan_investigation(
    analysis: InputAnalysis,
    *,
    cards: list[dict[str, Any]],
    oracle_already_refreshed: bool = False,
) -> InvestigationPlan:
    requests: list[JudgeToolRequest] = []
    goals: list[str] = []
    names = [str(card.get("name", "")).strip() for card in cards if card.get("name")]
    spanish = analysis.language == "es"

    if names and not oracle_already_refreshed:
        requests.append(JudgeToolRequest(
            tool="oracle_lookup",
            arguments={"card_names": names},
            purpose="verify_input_cards",
            result_limit=min(max(len(names), 1), 20),
        ))
        goals.append(
            "Verificar el texto Oracle actual de cada carta implicada."
            if spanish else
            "Verify the current Oracle text for every referenced card."
        )

    rules: list[str] = []
    concepts = set(analysis.concepts)
    intent = analysis.strategy_intent

    if intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        rules.extend(["700.4", "702.93a", "603.4"])
        goals.extend([
            "Definir reglamentariamente qué significa que una criatura muera." if spanish else "Define the rules meaning of a creature dying.",
            "Relacionar el evento de morir con Undying y excluir entradas al cementerio desde otras zonas." if spanish else "Relate dying to Undying and exclude graveyard entry from other zones.",
        ])
    else:
        derive_card_mechanics = intent in {
            StrategyIntent.COMBO_DETECTION,
            StrategyIntent.SYNERGY_ANALYSIS,
            StrategyIntent.INTERACTION_HYPOTHESIS,
            StrategyIntent.COMBO_FAILURE_EXPLANATION,
            StrategyIntent.INTERACTION_TIMING,
            StrategyIntent.PLAY_SEQUENCE,
            StrategyIntent.COMBO_DISRUPTION,
            StrategyIntent.COMBO_REQUIREMENTS,
        }
        has_sacrifice_text = any(
            "sacrifice" in str(card.get("oracle_text", "")).casefold()
            for card in cards
        )
        if "sacrifice" in concepts or (derive_card_mechanics and has_sacrifice_text):
            rules.extend(["701.21a", "700.4"])
            goals.append(
                "Verificar la transición de sacrificar a morir."
                if spanish else
                "Verify the sacrifice-to-dies transition."
            )
        elif "dies" in concepts or {"battlefield", "graveyard"}.issubset(concepts):
            rules.append("700.4")
            goals.append(
                "Verificar cuándo un cambio de zona cuenta como morir."
                if spanish else
                "Verify when a zone change counts as dying."
            )
        if "undying" in concepts or any("Undying" in str(card.get("oracle_text", "")) for card in cards):
            rules.extend(["702.93a", "603.4"])
            goals.append(
                "Verificar la condición de disparo de Undying."
                if spanish else
                "Verify the Undying trigger condition."
            )

    land_layer_concepts = {
        "land_types",
        "basic_lands",
        "nonbasic_lands",
        "mana_abilities",
    } & concepts
    ordering_concepts = {"layers", "dependency", "timestamp"} & concepts
    if land_layer_concepts and ordering_concepts:
        rules.extend([
            "305.6",
            "305.7",
            "305.8",
            "611.3",
            "613.1d",
            "613.7",
            "613.8a",
            "613.8b",
        ])
        goals.extend([
            (
                "Distinguir entre fijar un tipo de tierra y añadir tipos en la capa 4."
                if spanish else
                "Distinguish setting a land type from adding land types in layer 4."
            ),
            (
                "Aplicar dependencias antes de marcas de tiempo y derivar las habilidades de maná resultantes."
                if spanish else
                "Apply dependencies before timestamps and derive the resulting mana abilities."
            ),
        ])

    if intent in {StrategyIntent.INTERACTION_TIMING, StrategyIntent.COMBO_FAILURE_EXPLANATION}:
        rules.extend(["603.4", "603.6c", "603.10a", "400.7"])
        goals.append(
            "Identificar el momento exacto en que se comprueba el estado anterior del permanente."
            if spanish else
            "Identify the exact point at which the permanent's previous state is checked."
        )

    if {"counters", "ozolith", "leaves_battlefield", "last_known_information"} & concepts:
        rules.extend(["122.2", "400.7", "603.6c", "603.10a"])
        goals.append(
            "Verificar la persistencia de contadores y el momento de las habilidades de salida del campo."
            if spanish else
            "Verify counter persistence and leaves-the-battlefield timing."
        )

    rules = _deduplicate(rules)
    if rules:
        requests.append(JudgeToolRequest(
            tool="rules_lookup",
            arguments={"identifiers": rules},
            purpose="verify_claim_timing_and_state",
            result_limit=min(len(rules), 20),
        ))

    # Rulings are useful when The Ozolith itself is part of the current claim,
    # but not for a generic definition question that merely inherits the card.
    needs_ozolith_ruling = (
        any(name.casefold() == "the ozolith" for name in names)
        and (
            "ozolith" in concepts
            or intent in {
                StrategyIntent.INTERACTION_HYPOTHESIS,
                StrategyIntent.COMBO_FAILURE_EXPLANATION,
                StrategyIntent.INTERACTION_TIMING,
                StrategyIntent.COMBO_DETECTION,
            }
        )
    )
    if needs_ozolith_ruling:
        requests.append(JudgeToolRequest(
            tool="rulings_lookup",
            arguments={"card_names": ["The Ozolith"]},
            purpose="check_ozolith_rulings",
            result_limit=8,
        ))
        goals.append(
            "Comprobar las aclaraciones oficiales de The Ozolith."
            if spanish else
            "Check official rulings for The Ozolith."
        )

    hypotheses = build_hypotheses(analysis, cards=cards)
    return InvestigationPlan(
        requests=requested_unique(requests),
        goals=_deduplicate(goals),
        hypotheses=hypotheses,
    )


def requested_unique(requests: list[JudgeToolRequest]) -> list[JudgeToolRequest]:
    result: list[JudgeToolRequest] = []
    seen: set[tuple[str, str]] = set()
    for request in requests:
        key = (request.tool, repr(sorted(request.arguments.items())))
        if key in seen:
            continue
        seen.add(key)
        result.append(request)
    return result


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
