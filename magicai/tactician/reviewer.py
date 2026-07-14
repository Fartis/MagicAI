from __future__ import annotations

import re
import unicodedata

from magicai.tactician.models import (
    JudgeChallenge,
    TacticianReview,
    TacticianReviewStatus,
)
from magicai.validation.fallback import _extract_cards_block, _parse_card_blocks


def review_judge_candidate(
    answer: str,
    knowledge: str,
    *,
    context=None,
) -> TacticianReview:
    """Review a factual candidate without consulting factual sources directly.

    The reviewer consumes only the evidence package already assembled by the
    Judge. It is deliberately independent from the answer validator so that a
    shared blind spot does not automatically become an accepted answer.
    """

    question = _extract_question(knowledge)
    cards = _parse_card_blocks(_extract_cards_block(knowledge))
    normalized_answer = _normalize(answer)
    normalized_question = _normalize(question)

    challenges: list[JudgeChallenge] = []
    repaired_answer: str | None = None

    sacrifice_contract = _derive_sacrifice_contract(
        normalized_question,
        cards,
        knowledge,
    )
    if sacrifice_contract:
        challenges.extend(
            _review_sacrifice_contract(
                normalized_answer,
                sacrifice_contract,
            )
        )
        if challenges and sacrifice_contract["has_undying"]:
            repaired_answer = _render_undying_sacrifice_answer(
                sacrifice_contract,
                spanish=_is_spanish(question),
            )

    if not challenges:
        return TacticianReview(status=TacticianReviewStatus.ACCEPTED)

    return TacticianReview(
        status=(
            TacticianReviewStatus.REPAIRED
            if repaired_answer
            else TacticianReviewStatus.CHALLENGED
        ),
        challenges=challenges,
        repaired_answer=repaired_answer,
    )


def _derive_sacrifice_contract(
    question: str,
    cards: list[dict[str, str]],
    knowledge: str,
) -> dict[str, object] | None:
    if "sacrific" not in question and "sacrifice" not in question:
        return None
    if not cards:
        return None

    primary = _select_sacrificed_card(question, cards)
    if primary is None:
        return None
    type_line = _normalize(primary.get("type_line", ""))
    oracle = _normalize(primary.get("oracle_text", ""))
    rules = _normalize(_extract_rules_block(knowledge))

    is_creature = "creature" in type_line or "criatura" in type_line
    has_undying = "undying" in oracle and (
        "702.93" in rules or "undying" in rules
    )
    explicit_plus_counter = bool(
        re.search(
            r"(?:con|tiene|tenia|had|with)\s+(?:un|a|one)?\s*contador\s*\+1/\+1|"
            r"with\s+(?:a|one)\s*\+1/\+1\s+counter",
            question,
        )
    )
    replacement_to_exile = any(
        marker in question
        for marker in (
            "rest in peace",
            "descanso eterno",
            "en vez de ir al cementerio",
            "en lugar de ir al cementerio",
            "instead of going to the graveyard",
        )
    )

    return {
        "card_name": primary.get("name", "el permanente"),
        "is_creature": is_creature,
        "has_undying": has_undying,
        "explicit_plus_counter": explicit_plus_counter,
        "replacement_to_exile": replacement_to_exile,
        "has_sacrifice_rule": "701.21" in rules,
        "has_dies_rule": "700.4" in rules,
    }



def _select_sacrificed_card(
    question: str,
    cards: list[dict[str, str]],
) -> dict[str, str] | None:
    named = [
        card
        for card in cards
        if _normalize(card.get("name", "")) in question
    ]
    if len(named) == 1:
        return named[0]

    sacrifice_tail = re.split(
        r"sacrific(?:o|as|a|ar|e|ed|ing)?",
        question,
        maxsplit=1,
    )[-1]
    for card in named or cards:
        if _normalize(card.get("name", "")) in sacrifice_tail[:120]:
            return card

    return cards[0] if len(cards) == 1 else None

def _review_sacrifice_contract(
    answer: str,
    contract: dict[str, object],
) -> list[JudgeChallenge]:
    challenges: list[JudgeChallenge] = []

    if contract["has_sacrifice_rule"] and any(
        marker in answer
        for marker in (
            "sin pasar por el campo de batalla",
            "without passing through the battlefield",
            "no estaba en el campo de batalla",
            "was not on the battlefield",
        )
    ):
        challenges.append(
            JudgeChallenge(
                code="sacrifice_requires_battlefield",
                message=(
                    "The candidate contradicts the recovered sacrifice rule: a "
                    "permanent is sacrificed from the battlefield."
                ),
                evidence=("CR 701.21a",),
            )
        )

    if (
        contract["is_creature"]
        and contract["has_dies_rule"]
        and not contract["replacement_to_exile"]
        and any(
            marker in answer
            for marker in (
                "no muere",
                "does not die",
                "no cuenta como morir",
                "does not count as dying",
            )
        )
    ):
        challenges.append(
            JudgeChallenge(
                code="sacrificed_creature_dies",
                message=(
                    "The candidate contradicts the recovered definition of dies: "
                    "a sacrificed creature moved from the battlefield to a graveyard dies."
                ),
                evidence=("CR 701.21a", "CR 700.4"),
            )
        )

    expects_undying = (
        contract["has_undying"]
        and contract["is_creature"]
        and not contract["explicit_plus_counter"]
        and not contract["replacement_to_exile"]
    )
    if expects_undying:
        if any(
            marker in answer
            for marker in (
                "undying no se activa",
                "undying no se dispara",
                "undying does not trigger",
                "no regresa al campo de batalla",
                "does not return to the battlefield",
            )
        ):
            challenges.append(
                JudgeChallenge(
                    code="undying_should_trigger",
                    message=(
                        "The candidate contradicts the recovered Undying rule: absent "
                        "a +1/+1 counter or a graveyard replacement, Undying triggers."
                    ),
                    evidence=("CR 702.93a", "CR 701.21a", "CR 700.4"),
                )
            )

        required_semantics = (
            any(marker in answer for marker in ("muere", "dies")),
            any(marker in answer for marker in ("se dispara", "triggers")),
            any(marker in answer for marker in ("vuelve", "regresa", "returns")),
            "+1/+1" in answer,
        )
        if not all(required_semantics):
            challenges.append(
                JudgeChallenge(
                    code="undying_answer_incomplete",
                    message=(
                        "The candidate does not state the complete recovered causal chain: "
                        "sacrifice, dies, Undying triggers, and return with a +1/+1 counter."
                    ),
                    evidence=("CR 702.93a", "CR 701.21a", "CR 700.4"),
                )
            )

    return challenges


def _render_undying_sacrifice_answer(
    contract: dict[str, object],
    *,
    spanish: bool,
) -> str:
    name = str(contract["card_name"])
    if contract["explicit_plus_counter"]:
        if spanish:
            return (
                f"Al sacrificar {name}, pasa del campo de batalla al cementerio y muere. "
                "Como ya tenía un contador +1/+1, Undying no se dispara y no vuelve por esa habilidad."
            )
        return (
            f"When you sacrifice {name}, it moves from the battlefield to the graveyard and dies. "
            "Because it already had a +1/+1 counter, Undying does not trigger."
        )

    if spanish:
        return (
            f"Al sacrificar {name}, pasa del campo de batalla al cementerio y muere. "
            "Si no tenía contadores +1/+1, Undying se dispara y, cuando la habilidad "
            "se resuelve, vuelve al campo de batalla bajo el control de su propietario "
            "con un contador +1/+1."
        )
    return (
        f"When you sacrifice {name}, it moves from the battlefield to the graveyard and dies. "
        "If it had no +1/+1 counters, Undying triggers and returns it under its owner's "
        "control with a +1/+1 counter when the ability resolves."
    )


def _extract_question(knowledge: str) -> str:
    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _extract_rules_block(knowledge: str) -> str:
    match = re.search(
        r"RULES\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.casefold().split())


def _is_spanish(question: str) -> bool:
    normalized = _normalize(question)
    return "¿" in question or any(
        marker in normalized
        for marker in (
            "que ",
            "sacrific",
            "campo de batalla",
            "cementerio",
        )
    )
