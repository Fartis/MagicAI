from __future__ import annotations

from copy import deepcopy
from typing import Any

from magicai.assistant import MagicAI
from magicai.tactician.intents import (
    classify_strategy_intent,
    looks_like_referential_follow_up,
)
from magicai.tactician.models import TacticianResult
from magicai.tactician.strategy import analyze_strategy


class Tactician:
    """Strategic profile that investigates through Judge-owned evidence."""

    def __init__(self, judge: MagicAI | None = None):
        self.judge = judge or MagicAI()

    def ask_result(self, conversation, question: str) -> TacticianResult:
        """Direct Tactician entry point without duplicating conversation turns."""

        prior_conversation = deepcopy(conversation)
        judge_conversation = deepcopy(conversation)
        judge_result = self.judge.ask_result(judge_conversation, question)

        result = self.from_judge_result(
            question=question,
            judge_result=judge_result,
            prior_cards=prior_conversation.active_cards,
        )

        _copy_state(judge_conversation, conversation)
        conversation.active_cards = deepcopy(result.cards)
        conversation.add_user_message(question)
        conversation.add_assistant_message(result.answer)
        conversation.mode = "tactician"
        return result

    def from_judge_result(
        self,
        *,
        question: str,
        judge_result,
        prior_cards: list[Any] | None = None,
    ) -> TacticianResult:
        """Build a strategic result from an already executed Judge query.

        This is used by the automatic handoff in ``POST /ask``. The Tactician
        receives the Judge package and optional active cards from the previous
        turn, but it never opens Oracle, rules, or external sources directly.
        """

        judge_payload = judge_result.to_dict()
        intent = classify_strategy_intent(question)
        merged_cards, inherited_names = _merge_context_cards(
            current=judge_payload.get("cards", []),
            previous=prior_cards or [],
            inherit=looks_like_referential_follow_up(question),
        )
        judge_payload = {**judge_payload, "cards": merged_cards}

        judge_status = str(judge_payload.get("status", ""))
        if judge_status == "strategy_required":
            analysis = analyze_strategy(
                question,
                judge_payload,
                intent=intent,
            )
            answer = analysis.answer
            status = "answered"
            origin = "tactician_strategy"
            confidence = _strategy_confidence(
                analysis.combo_classification,
                judge_payload,
            )
            synergies = analysis.synergies
            risks = analysis.risks
            combo_classification = analysis.combo_classification
            combo_steps = analysis.combo_steps
            outcomes = analysis.outcomes
        else:
            answer = str(judge_payload.get("answer", ""))
            synergies = []
            risks = []
            combo_classification = "not_applicable"
            combo_steps = []
            outcomes = []
            status = judge_status or "insufficient_evidence"
            origin = "tactician_judge_gate"
            confidence = str(judge_payload.get("confidence", "low"))

        warnings = list(judge_payload.get("warnings", []))
        if judge_status not in {"strategy_required", "answered"}:
            warnings.append(
                "The Judge could not close the factual package, so the Tactician did not add a strategic recommendation."
            )

        return TacticianResult(
            question=question,
            answer=answer,
            status=status,
            origin=origin,
            confidence=confidence,
            strategy_intent=intent.value,
            cards=merged_cards,
            rules=list(judge_payload.get("rules", [])),
            rulings=list(judge_payload.get("rulings", [])),
            retrieval_queries=list(judge_payload.get("retrieval_queries", [])),
            assumptions=list(judge_payload.get("assumptions", [])),
            warnings=warnings,
            synergies=synergies,
            risks=risks,
            combo_classification=combo_classification,
            combo_steps=combo_steps,
            outcomes=outcomes,
            inherited_cards=inherited_names,
            judge_queries=[
                {
                    "sequence": 1,
                    "purpose": "factual_evidence",
                    "question": question,
                    "status": judge_status,
                    "origin": str(judge_payload.get("origin", "")),
                }
            ],
            authority_trace=(
                [
                    "judge:factual_evidence",
                    "tactician:strategic_interpretation",
                    "judge:source_gateway",
                ]
                if origin == "tactician_strategy"
                else ["judge:factual_answer", "tactician:relay"]
            ),
            judge_result=judge_payload,
        )


def replace_boundary_answer(conversation, result: TacticianResult) -> None:
    """Replace the Judge boundary message after an automatic handoff."""

    if conversation.history and conversation.history[-1].role == "assistant":
        conversation.history[-1].content = result.answer
    else:
        conversation.add_assistant_message(result.answer)
    conversation.active_cards = deepcopy(result.cards)
    conversation.last_intent = result.strategy_intent
    conversation.mode = "tactician"


def _strategy_confidence(classification: str, judge_payload: dict[str, Any]) -> str:
    if classification == "infinite_combo" and judge_payload.get("confidence") == "high":
        return "high"
    if classification in {"non_combo", "repeatable_synergy"}:
        return "medium"
    return "low"


def _merge_context_cards(
    *,
    current: list[Any],
    previous: list[Any],
    inherit: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    current_cards = [_card_to_dict(card) for card in current]
    if not inherit:
        return _deduplicate_cards(current_cards), []

    previous_cards = [_card_to_dict(card) for card in previous]
    current_names = {card.get("name") for card in current_cards}
    inherited_names = [
        str(card.get("name"))
        for card in previous_cards
        if card.get("name") and card.get("name") not in current_names
    ]
    return _deduplicate_cards(previous_cards + current_cards), inherited_names


def _card_to_dict(card: Any) -> dict[str, Any]:
    if isinstance(card, dict):
        return deepcopy(card)
    return {
        key: getattr(card, key, None)
        for key in (
            "name",
            "mana_cost",
            "type_line",
            "oracle_text",
            "scryfall_uri",
        )
        if getattr(card, key, None) is not None
    }


def _deduplicate_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card in cards:
        name = str(card.get("name", "")).strip()
        key = name.casefold()
        if not name or key in seen:
            continue
        seen.add(key)
        result.append(card)
    return result


def _copy_state(source, target) -> None:
    target.active_cards = deepcopy(source.active_cards)
    target.active_keywords = list(source.active_keywords)
    target.active_rules = list(source.active_rules)
    target.active_rule_queries = list(source.active_rule_queries)
    target.pending_card_question = source.pending_card_question
    target.pending_card_alias = source.pending_card_alias
    target.pending_card_candidates = list(source.pending_card_candidates)
    target.last_intent = source.last_intent
    target.language = source.language
    target.mode = "tactician"
