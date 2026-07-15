from __future__ import annotations

from copy import deepcopy
from typing import Any

from magicai.assistant import MagicAI
from magicai.judge_tools import (
    JudgeToolBudget,
    JudgeToolGateway,
    JudgeToolRequest,
    JudgeToolStatus,
)
from magicai.tactician.intents import (
    classify_strategy_intent,
    looks_like_referential_follow_up,
)
from magicai.tactician.models import TacticianResult
from magicai.tactician.strategy import analyze_strategy


class Tactician:
    """Strategic profile that investigates through Judge-owned evidence."""

    def __init__(
        self,
        judge: MagicAI | None = None,
        tool_gateway: JudgeToolGateway | None = None,
    ):
        self.judge = judge or MagicAI()
        self.tool_gateway = tool_gateway or JudgeToolGateway()

    def ask_result(self, conversation, question: str) -> TacticianResult:
        """Direct Tactician entry point without duplicating conversation turns."""

        prior_conversation = deepcopy(conversation)
        judge_conversation = deepcopy(conversation)
        judge_result = self.judge.ask_result(judge_conversation, question)

        result = self.from_judge_result(
            question=question,
            judge_result=judge_result,
            prior_cards=prior_conversation.active_cards,
            conversation=prior_conversation,
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
        conversation=None,
    ) -> TacticianResult:
        """Build a strategic result from a Judge package.

        The Tactician may request bounded, read-only evidence through the
        Judge Tool Gateway. It never opens Oracle, rules, rulings, or future
        strategic providers directly.
        """

        judge_payload = judge_result.to_dict()
        intent = classify_strategy_intent(question)
        merged_cards, inherited_names = _merge_context_cards(
            current=judge_payload.get("cards", []),
            previous=prior_cards or [],
            inherit=looks_like_referential_follow_up(question),
        )

        tool_calls: list[dict[str, Any]] = []
        if conversation is not None and merged_cards:
            merged_cards, tool_calls = self._refresh_oracle_evidence(
                cards=merged_cards,
                conversation=conversation,
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
            tactician_synthesized = True
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
            tactician_synthesized = False

        warnings = list(judge_payload.get("warnings", []))
        if judge_status not in {"strategy_required", "answered"}:
            warnings.append(
                "The Judge could not close the factual package, so the Tactician did not add a strategic recommendation."
            )

        judge_queries = [
            {
                "sequence": 1,
                "purpose": "factual_evidence",
                "question": question,
                "status": judge_status,
                "origin": str(judge_payload.get("origin", "")),
            }
        ]
        for sequence, tool_call in enumerate(tool_calls, start=2):
            judge_queries.append(
                {
                    "sequence": sequence,
                    "purpose": tool_call.get("purpose", "judge_tool_evidence"),
                    "tool": tool_call.get("tool", ""),
                    "status": tool_call.get("status", ""),
                    "evidence_count": len(tool_call.get("evidence", [])),
                    "cache_hit": bool(tool_call.get("cache_hit", False)),
                }
            )

        if origin == "tactician_strategy":
            authority_trace = ["judge:factual_evidence"]
            if tool_calls:
                authority_trace.append("judge:tool_gateway")
            authority_trace.extend(
                [
                    "tactician:strategic_interpretation",
                    "judge:source_gateway",
                ]
            )
        else:
            authority_trace = ["judge:factual_answer", "tactician:relay"]

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
            judge_queries=judge_queries,
            judge_tool_calls=tool_calls,
            tactician_synthesized=tactician_synthesized,
            authority_trace=authority_trace,
            judge_result=judge_payload,
        )

    def execute_judge_tool(
        self,
        request: JudgeToolRequest,
        *,
        conversation=None,
        budget: JudgeToolBudget | None = None,
    ):
        """Public strategic-side entry point to the Judge-owned gateway."""

        return self.tool_gateway.execute(
            request,
            conversation=conversation,
            budget=budget,
        )

    def _refresh_oracle_evidence(
        self,
        *,
        cards: list[dict[str, Any]],
        conversation,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        names = [str(card.get("name", "")).strip() for card in cards]
        names = [name for name in names if name]
        if not names:
            return cards, []

        budget = JudgeToolBudget(
            max_calls=3,
            max_calls_per_tool=2,
            max_repeated_request=1,
            max_elapsed_seconds=10.0,
        )
        result = self.execute_judge_tool(
            JudgeToolRequest(
                tool="oracle_lookup",
                arguments={"card_names": names},
                purpose="refresh_strategic_oracle_evidence",
                result_limit=max(1, min(len(names), 20)),
            ),
            conversation=conversation,
            budget=budget,
        )
        payload = result.to_dict()
        if result.status is not JudgeToolStatus.SUCCESS:
            return cards, [payload]

        refreshed = [
            dict(item.get("data", {}))
            for item in result.evidence
            if item.get("kind") == "card" and item.get("data")
        ]
        if not refreshed:
            return cards, [payload]

        return _merge_refreshed_cards(cards, refreshed), [payload]


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
            "oracle_id",
            "id",
            "name",
            "mana_cost",
            "cmc",
            "type_line",
            "oracle_text",
            "power",
            "toughness",
            "loyalty",
            "defense",
            "colors",
            "color_identity",
            "keywords",
            "legalities",
            "rarity",
            "released_at",
            "scryfall_uri",
            "rulings_uri",
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


def _merge_refreshed_cards(
    original: list[dict[str, Any]],
    refreshed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_name = {
        str(card.get("name", "")).casefold(): card
        for card in refreshed
        if card.get("name")
    }
    result = []
    for card in original:
        replacement = by_name.get(str(card.get("name", "")).casefold())
        result.append(deepcopy(replacement or card))
    return _deduplicate_cards(result)


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
