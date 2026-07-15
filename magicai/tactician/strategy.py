from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from magicai.tactician.intents import StrategyIntent, is_spanish


ROLE_LABELS_ES = {
    "mana_acceleration": "aceleración de maná",
    "sacrifice_outlet": "motor de sacrificio",
    "death_value": "valor al morir",
    "recursion": "recursión",
    "card_advantage": "ventaja de cartas",
    "removal": "interacción o removal",
    "token_generation": "generación de fichas",
    "protection": "protección",
    "counter_removal": "gestión de contadores",
}

ROLE_LABELS_EN = {
    "mana_acceleration": "mana acceleration",
    "sacrifice_outlet": "sacrifice outlet",
    "death_value": "death value",
    "recursion": "recursion",
    "card_advantage": "card advantage",
    "removal": "interaction or removal",
    "token_generation": "token generation",
    "protection": "protection",
    "counter_removal": "counter management",
}


@dataclass(slots=True)
class StrategyAnalysis:
    answer: str
    synergies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    combo_classification: str = "insufficient_information"
    combo_steps: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    evidence_cards: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CardCapabilities:
    name: str
    oracle_text: str
    roles: frozenset[str]
    undying: bool = False
    persist: bool = False
    sacrifice_mana: int = 0
    counter_to_token_cost: int | None = None
    removes_plus_counter_from_controlled_creature: bool = False


def analyze_strategy(
    question: str,
    judge_payload: dict[str, Any],
    *,
    intent: StrategyIntent = StrategyIntent.GENERAL_STRATEGY,
) -> StrategyAnalysis:
    cards = [card for card in judge_payload.get("cards", []) if card.get("name")]
    capabilities = [_capabilities(card) for card in cards]
    spanish = is_spanish(question)

    if intent is StrategyIntent.COMBO_DETECTION:
        combo = _analyze_repeatable_combo(capabilities, spanish=spanish)
        if combo is not None:
            return combo

    synergies: list[str] = []
    risks: list[str] = []

    for left_index, left in enumerate(capabilities):
        for right in capabilities[left_index + 1 :]:
            pair_synergies, pair_risks = _pair_analysis(left, right, spanish=spanish)
            synergies.extend(pair_synergies)
            risks.extend(pair_risks)

    labels = ROLE_LABELS_ES if spanish else ROLE_LABELS_EN
    role_sentences: list[str] = []
    for card in capabilities:
        if not card.roles:
            continue
        role_text = ", ".join(labels[role] for role in sorted(card.roles))
        if spanish:
            role_sentences.append(f"{card.name} aporta {role_text}")
        else:
            role_sentences.append(f"{card.name} provides {role_text}")

    if synergies:
        answer = " ".join(_deduplicate(synergies))
        if risks:
            answer += " " + " ".join(_deduplicate(risks))
        classification = "repeatable_synergy"
    elif role_sentences:
        if spanish:
            answer = (
                "Con los hechos validados por el Juez, "
                + "; ".join(role_sentences)
                + ". No hay evidencia suficiente para demostrar un bucle infinito con estas piezas por sí solas."
            )
        else:
            answer = (
                "Using the facts validated by the Judge, "
                + "; ".join(role_sentences)
                + ". There is not enough evidence to prove an infinite loop from these pieces alone."
            )
        classification = "non_combo"
    else:
        if spanish:
            answer = (
                "El Juez ha validado las cartas disponibles, pero todavía no hay suficiente "
                "información estratégica para demostrar una línea concreta."
            )
            risks.append("Falta información suficiente para reconstruir costes, estado inicial y resultado neto.")
        else:
            answer = (
                "The Judge validated the available cards, but there is not enough strategic "
                "information to prove a concrete line."
            )
            risks.append("There is not enough information to reconstruct costs, initial state, and net result.")
        classification = "insufficient_information"

    return StrategyAnalysis(
        answer=answer,
        synergies=_deduplicate(synergies),
        risks=_deduplicate(risks),
        combo_classification=classification,
        evidence_cards=[card.name for card in capabilities],
    )


def _analyze_repeatable_combo(
    cards: list[CardCapabilities],
    *,
    spanish: bool,
) -> StrategyAnalysis | None:
    undying_cards = [card for card in cards if card.undying]
    mana_outlets = [card for card in cards if card.sacrifice_mana > 0]
    counter_converters = [
        card
        for card in cards
        if card.removes_plus_counter_from_controlled_creature
        and card.counter_to_token_cost is not None
    ]

    if not undying_cards or not mana_outlets or not counter_converters:
        return None

    value = undying_cards[0]
    outlet = max(mana_outlets, key=lambda item: item.sacrifice_mana)
    converter = min(
        counter_converters,
        key=lambda item: item.counter_to_token_cost or 0,
    )
    cost = converter.counter_to_token_cost or 0
    net_mana = outlet.sacrifice_mana - cost

    if net_mana < 0:
        return None

    if spanish:
        steps = [
            f"Sacrifica {value.name} con {outlet.name}; la habilidad produce {outlet.sacrifice_mana} manás incoloros.",
            f"{value.name} muere y Undying se dispara; al resolverse vuelve con un contador +1/+1.",
            f"Paga {cost} maná con {converter.name}, retira ese contador de {value.name} y crea una ficha.",
            f"{value.name} vuelve a quedar sin contador +1/+1, por lo que el estado necesario para repetir el ciclo se recupera.",
        ]
        outcomes = [
            f"{net_mana} maná incoloro neto por iteración",
            "una ficha adicional por iteración",
            "un número arbitrariamente grande de iteraciones mientras nadie interrumpa la línea",
        ]
        answer = (
            f"Sí. {value.name}, {outlet.name} y {converter.name} forman un combo infinito. "
            f"Cada vuelta sacrifica y devuelve {value.name}, retira el contador que bloquearía Undying "
            f"y deja {net_mana} maná incoloro neto además de una ficha. "
            "La línea puede repetirse un número arbitrariamente grande de veces si no es interrumpida."
        )
        risks = [
            "El combo puede interrumpirse retirando la criatura antes de que se resuelva Undying, contrarrestando la habilidad disparada o anulando una de las habilidades activadas relevantes.",
            "La conclusión presupone que no hay un efecto de reemplazo que impida que la criatura llegue al cementerio.",
        ]
        synergy = (
            f"{outlet.name} convierte la muerte de {value.name} en maná, y {converter.name} elimina "
            "el contador +1/+1 de Undying para restaurar el estado inicial."
        )
    else:
        steps = [
            f"Sacrifice {value.name} to {outlet.name}; the mana ability produces {outlet.sacrifice_mana} colorless mana.",
            f"{value.name} dies and Undying triggers; when it resolves, it returns with a +1/+1 counter.",
            f"Pay {cost} mana with {converter.name}, remove that counter from {value.name}, and create a token.",
            f"{value.name} is again free of +1/+1 counters, restoring the state required to repeat the loop.",
        ]
        outcomes = [
            f"{net_mana} net colorless mana per iteration",
            "one additional token per iteration",
            "an arbitrarily large number of iterations while the line remains uninterrupted",
        ]
        answer = (
            f"Yes. {value.name}, {outlet.name}, and {converter.name} form an infinite combo. "
            f"Each iteration sacrifices and returns {value.name}, removes the counter that would stop Undying, "
            f"and produces {net_mana} net colorless mana plus one token."
        )
        risks = [
            "The combo can be interrupted by moving the creature before Undying resolves, countering the trigger, or disabling a relevant activated ability.",
            "This conclusion assumes no replacement effect prevents the creature from reaching the graveyard.",
        ]
        synergy = (
            f"{outlet.name} converts {value.name}'s death into mana, while {converter.name} removes "
            "the Undying counter and restores the initial state."
        )

    return StrategyAnalysis(
        answer=answer,
        synergies=[synergy],
        risks=risks,
        combo_classification="infinite_combo",
        combo_steps=steps,
        outcomes=outcomes,
        evidence_cards=[value.name, outlet.name, converter.name],
    )


def _capabilities(card: dict[str, Any]) -> CardCapabilities:
    name = str(card.get("name", "Card"))
    oracle = str(card.get("oracle_text", ""))
    text = " ".join(oracle.casefold().split())
    roles = _roles_for_oracle(oracle)

    sacrifice_mana = 0
    for match in re.finditer(
        r"sacrifice (?:a|another) creature:\s*add\s+(?P<mana>(?:\{[^}]+\})+)",
        oracle,
        flags=re.IGNORECASE,
    ):
        sacrifice_mana = max(sacrifice_mana, _mana_amount(match.group("mana")))

    counter_cost: int | None = None
    removes_counter = False
    for line in oracle.splitlines():
        if not re.search(
            r"remove a \+1/\+1 counter from a creature you control",
            line,
            flags=re.IGNORECASE,
        ):
            continue
        if not re.search(r"create (?:a|one|\d+|x).*token", line, flags=re.IGNORECASE):
            continue
        removes_counter = True
        cost_text = line.split(":", 1)[0]
        counter_cost = _generic_mana_cost(cost_text)
        break

    return CardCapabilities(
        name=name,
        oracle_text=oracle,
        roles=frozenset(roles),
        undying="undying" in text,
        persist="persist" in text,
        sacrifice_mana=sacrifice_mana,
        counter_to_token_cost=counter_cost,
        removes_plus_counter_from_controlled_creature=removes_counter,
    )


def _roles_for_oracle(oracle_text: str) -> set[str]:
    text = " ".join((oracle_text or "").casefold().split())
    roles: set[str] = set()

    if re.search(r"\badd \{", text) or "create a treasure" in text:
        roles.add("mana_acceleration")
    if re.search(
        r"(?:^|\n)[^:]*sacrifice (?:a|another|this) [^:]+:",
        oracle_text or "",
        flags=re.IGNORECASE,
    ):
        roles.add("sacrifice_outlet")
    if "undying" in text or "persist" in text or "when this creature dies" in text:
        roles.add("death_value")
    if "return" in text and "graveyard" in text:
        roles.add("recursion")
    if "draw a card" in text or "draw two cards" in text:
        roles.add("card_advantage")
    if "destroy target" in text or "exile target" in text or (
        "deals" in text and "damage to any target" in text
    ):
        roles.add("removal")
    if "create" in text and "token" in text:
        roles.add("token_generation")
    if any(keyword in text for keyword in ("hexproof", "indestructible", "ward ", "protection from")):
        roles.add("protection")
    if "remove a +1/+1 counter" in text:
        roles.add("counter_removal")

    return roles


def _pair_analysis(
    left: CardCapabilities,
    right: CardCapabilities,
    *,
    spanish: bool,
) -> tuple[list[str], list[str]]:
    synergies: list[str] = []
    risks: list[str] = []

    for outlet, value in ((left, right), (right, left)):
        if "sacrifice_outlet" not in outlet.roles or "death_value" not in value.roles:
            continue
        if spanish:
            synergies.append(
                f"{outlet.name} y {value.name} forman una sinergia de sacrificio: "
                f"{outlet.name} convierte la criatura en un recurso y {value.name} aporta valor al morir o regresar."
            )
            if value.undying:
                risks.append(
                    "No es un bucle infinito por sí solo: Undying devuelve la criatura con un contador +1/+1; "
                    "hace falta otra pieza que retire o neutralice ese contador."
                )
        else:
            synergies.append(
                f"{outlet.name} and {value.name} form a sacrifice synergy: "
                f"{outlet.name} converts the creature into a resource while {value.name} provides death or recursion value."
            )
            if value.undying:
                risks.append(
                    "This is not an infinite loop by itself: Undying returns the creature with a +1/+1 counter, "
                    "so another piece must remove or neutralize that counter."
                )
        break

    if "token_generation" in left.roles and "sacrifice_outlet" in right.roles:
        synergies.append(
            f"{left.name} provides tokens that {right.name} can convert through sacrifices."
            if not spanish
            else f"{left.name} proporciona fichas que {right.name} puede convertir en valor mediante sacrificios."
        )
    if "token_generation" in right.roles and "sacrifice_outlet" in left.roles:
        synergies.append(
            f"{right.name} provides tokens that {left.name} can convert through sacrifices."
            if not spanish
            else f"{right.name} proporciona fichas que {left.name} puede convertir en valor mediante sacrificios."
        )

    return synergies, risks


def _mana_amount(mana: str) -> int:
    amount = 0
    for symbol in re.findall(r"\{([^}]+)\}", mana):
        amount += int(symbol) if symbol.isdigit() else 1
    return amount


def _generic_mana_cost(cost_text: str) -> int:
    amount = 0
    for symbol in re.findall(r"\{([^}]+)\}", cost_text):
        if symbol.isdigit():
            amount += int(symbol)
        elif symbol.upper() not in {"T", "Q"}:
            amount += 1
    return amount


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
