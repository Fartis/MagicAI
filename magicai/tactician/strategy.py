from __future__ import annotations

import re
from typing import Any


ROLE_LABELS = {
    "mana_acceleration": "aceleración de maná",
    "sacrifice_outlet": "motor de sacrificio",
    "death_value": "valor al morir",
    "recursion": "recursión",
    "card_advantage": "ventaja de cartas",
    "removal": "interacción o removal",
    "token_generation": "generación de fichas",
    "protection": "protección",
}


def analyze_strategy(question: str, judge_payload: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    cards = judge_payload.get("cards", [])
    roles_by_card = {
        card.get("name", "Carta"): _roles_for_oracle(card.get("oracle_text", ""))
        for card in cards
    }

    synergies: list[str] = []
    risks: list[str] = []

    names = list(roles_by_card)
    if len(names) >= 2:
        for left_index, left in enumerate(names):
            for right in names[left_index + 1 :]:
                pair_synergies, pair_risks = _pair_analysis(
                    left,
                    roles_by_card[left],
                    cards[names.index(left)].get("oracle_text", ""),
                    right,
                    roles_by_card[right],
                    cards[names.index(right)].get("oracle_text", ""),
                )
                synergies.extend(pair_synergies)
                risks.extend(pair_risks)

    role_sentences = []
    for name, roles in roles_by_card.items():
        if roles:
            labels = ", ".join(ROLE_LABELS[role] for role in sorted(roles))
            role_sentences.append(f"{name} aporta {labels}")

    if synergies:
        answer = " ".join(synergies)
        if risks:
            answer += " " + " ".join(risks)
    elif role_sentences:
        answer = (
            "Con los hechos validados por el Juez, "
            + "; ".join(role_sentences)
            + ". Para recomendar una línea exacta todavía necesito el formato, la lista y el estado de la partida."
        )
    else:
        answer = (
            "El Juez ha validado la información factual disponible, pero todavía no hay "
            "suficiente contexto estratégico para recomendar una línea concreta. Indica formato, "
            "cartas disponibles, recursos y objetivo de la jugada."
        )
        risks.append("Falta contexto estratégico de formato, lista o estado de partida.")

    return answer, _deduplicate(synergies), _deduplicate(risks)


def _roles_for_oracle(oracle_text: str) -> set[str]:
    text = " ".join((oracle_text or "").casefold().split())
    roles: set[str] = set()

    if re.search(r"\badd \{", text) or "create a treasure" in text:
        roles.add("mana_acceleration")
    if re.search(r"^[^.]*sacrifice (?:a|another|this) [^:]+:", text) or re.search(
        r"(?:^|\n)[^:]*sacrifice [^:]+:",
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
    if "destroy target" in text or "exile target" in text or "deals" in text and "damage to any target" in text:
        roles.add("removal")
    if "create" in text and "token" in text:
        roles.add("token_generation")
    if any(keyword in text for keyword in ("hexproof", "indestructible", "ward ", "protection from")):
        roles.add("protection")

    return roles


def _pair_analysis(
    left_name: str,
    left_roles: set[str],
    left_oracle: str,
    right_name: str,
    right_roles: set[str],
    right_oracle: str,
) -> tuple[list[str], list[str]]:
    synergies: list[str] = []
    risks: list[str] = []

    combinations = (
        (left_name, left_roles, left_oracle, right_name, right_roles, right_oracle),
        (right_name, right_roles, right_oracle, left_name, left_roles, left_oracle),
    )
    for outlet_name, outlet_roles, outlet_oracle, value_name, value_roles, value_oracle in combinations:
        if "sacrifice_outlet" in outlet_roles and "death_value" in value_roles:
            synergies.append(
                f"{outlet_name} y {value_name} forman una sinergia de sacrificio: "
                f"{outlet_name} convierte la criatura en un recurso y {value_name} aporta valor al morir o regresar."
            )
            if "undying" in value_oracle.casefold():
                risks.append(
                    "No es un bucle infinito por sí solo: Undying devuelve la criatura con un contador +1/+1, "
                    "así que necesitas una forma independiente de retirar o neutralizar ese contador para repetirlo."
                )
            break

    if "token_generation" in left_roles and "sacrifice_outlet" in right_roles:
        synergies.append(f"{left_name} proporciona fichas que {right_name} puede convertir en valor mediante sacrificios.")
    if "token_generation" in right_roles and "sacrifice_outlet" in left_roles:
        synergies.append(f"{right_name} proporciona fichas que {left_name} puede convertir en valor mediante sacrificios.")

    return synergies, risks


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
