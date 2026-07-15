from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from magicai.oracle_abilities import (
    extract_activated_abilities,
    extract_quoted_activated_abilities,
)


@dataclass(frozen=True, slots=True)
class PremiseCorrection:
    answer: str
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def render_false_premise_answer(
    knowledge: str,
    *,
    context: Any | None = None,
) -> PremiseCorrection | None:
    """Correct only high-confidence false premises grounded in Oracle text."""

    raw_question = getattr(context, "question", "") or _question(knowledge)
    question = _normalize(raw_question)
    cards = list(getattr(context, "cards", []) or [])

    impossible_sequence = _exact_ability_source_removal_premise(
        raw_question,
        question,
        cards,
    )
    if impossible_sequence:
        return impossible_sequence

    if not _asserts_a_premise(question):
        return None

    cast_trigger = _cast_trigger_entering_premise(question, cards)
    if cast_trigger:
        return cast_trigger

    self_sacrifice = _another_cost_self_sacrifice_premise(question, cards)
    if self_sacrifice:
        return self_sacrifice

    return None



def _exact_ability_source_removal_premise(
    raw_question: str,
    question: str,
    cards: list[Any],
) -> PremiseCorrection | None:
    if not any(marker in question for marker in (
        "destruy", "elimin", "retir", "fuente", "source", "removed",
    )):
        return None
    quoted = extract_quoted_activated_abilities(raw_question)
    if not quoted:
        return None
    quoted_texts = {_normalize(ability.text) for ability in quoted}
    for card in cards:
        name = str(getattr(card, "name", "Esta carta") or "Esta carta")
        oracle = str(getattr(card, "oracle_text", "") or "")
        type_line = str(getattr(card, "type_line", "") or "")
        for ability in extract_activated_abilities(
            oracle,
            card_name=name,
            type_line=type_line,
        ):
            if _normalize(ability.text) not in quoted_texts:
                continue
            if ability.source_removed_as_cost:
                return PremiseCorrection(
                    answer=(
                        f"La secuencia planteada no es posible para esa habilidad de "
                        f"{name}: el coste retira la propia fuente antes de que la "
                        "habilidad quede activada en la pila. No puede destruirse "
                        "después como si todavía siguiera en el campo de batalla."
                    ),
                    warnings=[
                        "Se corrigió una premisa donde la propia fuente abandona su zona como coste de activación."
                    ],
                )
            if ability.source_zone != "battlefield":
                zone = {
                    "hand": "la mano",
                    "graveyard": "el cementerio",
                    "exile": "el exilio",
                    "library": "la biblioteca",
                }.get(ability.source_zone, ability.source_zone)
                return PremiseCorrection(
                    answer=(
                        f"La secuencia planteada no es posible para esa habilidad de "
                        f"{name}: se activa desde {zone}, no desde un permanente en "
                        "el campo de batalla que pueda ser destruido después."
                    ),
                    warnings=[
                        "Se corrigió una premisa que colocaba la fuente de una habilidad en una zona incorrecta."
                    ],
                )
    return None

def _cast_trigger_entering_premise(
    question: str,
    cards: list[Any],
) -> PremiseCorrection | None:
    if not any(
        marker in question
        for marker in (
            "cuando entra",
            "al entrar",
            "cuando vuelve a entrar",
            "al volver a entrar",
            "entra al campo",
            "entra en el campo",
        )
    ):
        return None

    for card in cards:
        oracle = _normalize(getattr(card, "oracle_text", "") or "")
        if "when you cast this spell" not in oracle:
            continue

        name = getattr(card, "name", "Esta carta")
        return PremiseCorrection(
            answer=(
                f"La premisa no es correcta: {name} no dispara esa habilidad "
                "simplemente por entrar al campo de batalla. Su texto Oracle "
                "dice que se dispara cuando lanzas el hechizo; entrar sin "
                "haber sido lanzado no cumple esa condición."
            ),
            warnings=[
                "Se corrigió una premisa que confundía lanzar un hechizo con poner un permanente en el campo de batalla."
            ],
        )

    return None


def _another_cost_self_sacrifice_premise(
    question: str,
    cards: list[Any],
) -> PremiseCorrection | None:
    if "sacrific" not in question or not any(
        marker in question
        for marker in ("su propia habilidad", "esa habilidad", "esta habilidad")
    ):
        return None

    for card in cards:
        oracle = getattr(card, "oracle_text", "") or ""
        if not re.search(r"(?im)^sacrifice another [^:]+:", oracle):
            continue

        name = getattr(card, "name", "Esta carta")
        return PremiseCorrection(
            answer=(
                f"La premisa no es correcta: {name} no puede sacrificarse "
                "para pagar esa habilidad, porque el coste exige sacrificar "
                "«otra» criatura o permanente."
            ),
            warnings=[
                "Se corrigió una premisa sobre el significado de «another» en un coste de sacrificio."
            ],
        )

    return None


def _asserts_a_premise(question: str) -> bool:
    return any(
        marker in question
        for marker in (
            "como ",
            "ya que ",
            "dado que ",
            "puesto que ",
            "entonces ",
            "por lo tanto ",
        )
    )


def _question(knowledge: str) -> str:
    if "QUESTION" not in knowledge:
        return ""
    remainder = knowledge.split("QUESTION", 1)[1]
    return remainder.split("=" * 10, 1)[0].strip()


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.lower()).strip()
