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
from magicai.tactician.claims import (
    ClaimVerdictStatus,
    evaluate_claims,
)
from magicai.tactician.input_analysis import analyze_user_input
from magicai.tactician.intents import looks_like_referential_follow_up
from magicai.tactician.models import TacticianResult
from magicai.tactician.planner import plan_investigation
from magicai.tactician.synthesis import synthesize_strategy


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
        _apply_result_state(conversation, result)
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
        """Investigate the user's input and synthesize a strategic answer.

        The Tactician can issue multiple bounded requests through the Judge Tool
        Gateway. It never opens Oracle, rules, rulings, or strategic providers
        directly, and it never treats the Judge's prose as a ready-made
        strategic response.
        """

        input_analysis = analyze_user_input(question)
        judge_payload = judge_result.to_dict()
        merged_cards, inherited_names = _merge_context_cards(
            current=judge_payload.get("cards", []),
            previous=prior_cards or [],
            inherit=(
                looks_like_referential_follow_up(question)
                or input_analysis.speech_act.value in {"challenge", "follow_up"}
                or input_analysis.strategy_intent.value in {"play_sequence", "combo_disruption", "combo_requirements"}
            ),
        )

        budget = JudgeToolBudget(
            max_calls=8,
            max_calls_per_tool=3,
            max_repeated_request=1,
            max_elapsed_seconds=30.0,
        )
        tool_calls: list[dict[str, Any]] = []
        if conversation is not None and merged_cards:
            merged_cards, oracle_calls = self._refresh_oracle_evidence(
                cards=merged_cards,
                conversation=conversation,
                budget=budget,
            )
            tool_calls.extend(oracle_calls)

        plan = plan_investigation(
            input_analysis,
            cards=merged_cards,
            oracle_already_refreshed=bool(tool_calls),
        )
        if conversation is not None and plan.requests:
            for request in plan.requests:
                result = self.execute_judge_tool(
                    request,
                    conversation=conversation,
                    budget=budget,
                )
                tool_calls.append(result.to_dict())

        judge_payload = _merge_tool_evidence(
            {**judge_payload, "cards": merged_cards},
            tool_calls,
        )
        claim_verdicts = evaluate_claims(
            input_analysis,
            cards=merged_cards,
            tool_calls=tool_calls,
        )

        synthesis = synthesize_strategy(
            question=question,
            judge_payload=judge_payload,
            input_analysis=input_analysis,
            claim_verdicts=claim_verdicts,
        )

        judge_status = str(judge_payload.get("status", ""))
        if judge_status not in {"strategy_required", "answered"}:
            status = judge_status or "insufficient_evidence"
            warnings = [
                *list(judge_payload.get("warnings", [])),
                "The Judge could not close the factual package; the Strategist's conclusion is limited to the evidence recovered so far.",
            ]
        else:
            status = "answered"
            warnings = list(judge_payload.get("warnings", []))

        judge_verified = _judge_verified(
            claim_verdicts=claim_verdicts,
            combo_classification=synthesis.combo_classification,
            tool_calls=tool_calls,
        )
        confidence = _strategy_confidence(
            synthesis.combo_classification,
            judge_payload,
            judge_verified=judge_verified,
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

        authority_trace = ["judge:factual_evidence"]
        if tool_calls:
            authority_trace.append("judge:tool_gateway")
        authority_trace.extend(
            [
                "tactician:input_analysis",
                "tactician:claim_evaluation",
                "tactician:strategic_synthesis",
                "judge:evidence_verification" if judge_verified else "judge:evidence_incomplete",
            ]
        )

        result = TacticianResult(
            question=question,
            answer=synthesis.answer,
            status=status,
            origin="tactician_reasoned_strategy",
            confidence=confidence,
            strategy_intent=input_analysis.strategy_intent.value,
            cards=merged_cards,
            rules=list(judge_payload.get("rules", [])),
            rulings=list(judge_payload.get("rulings", [])),
            retrieval_queries=list(judge_payload.get("retrieval_queries", [])),
            assumptions=list(judge_payload.get("assumptions", [])),
            warnings=warnings,
            synergies=synthesis.synergies,
            risks=synthesis.risks,
            combo_classification=synthesis.combo_classification,
            combo_steps=synthesis.combo_steps,
            outcomes=synthesis.outcomes,
            inherited_cards=inherited_names,
            judge_queries=judge_queries,
            judge_tool_calls=tool_calls,
            tactician_synthesized=True,
            authority_trace=authority_trace,
            judge_result=judge_payload,
            input_analysis=input_analysis.to_dict(),
            claim_verdicts=[verdict.to_dict() for verdict in claim_verdicts],
            reasoning_summary=synthesis.reasoning_summary,
            queries_planned=len(plan.requests) + (1 if merged_cards else 0),
            queries_completed=len(tool_calls),
            judge_verified=judge_verified,
            investigation_plan=plan.to_dict(),
        )
        return result

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
        budget: JudgeToolBudget,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        names = [str(card.get("name", "")).strip() for card in cards]
        names = [name for name in names if name]
        if not names:
            return cards, []

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
    _apply_result_state(conversation, result)


def _apply_result_state(conversation, result: TacticianResult) -> None:
    conversation.active_cards = deepcopy(result.cards)
    conversation.last_intent = result.strategy_intent
    conversation.mode = "tactician"
    conversation.strategy_context = {
        "last_intent": result.strategy_intent,
        "active_cards": [card.get("name", "") for card in result.cards],
        "combo_classification": result.combo_classification,
        "reasoning_summary": list(result.reasoning_summary),
        "claim_verdicts": deepcopy(result.claim_verdicts),
        "judge_verified": bool(result.judge_verified),
    }


def _strategy_confidence(
    classification: str,
    judge_payload: dict[str, Any],
    *,
    judge_verified: bool,
) -> str:
    if judge_verified and classification in {"infinite_combo", "non_combo"}:
        return "high"
    if classification in {"non_combo", "repeatable_synergy"}:
        return "medium"
    if judge_payload.get("confidence") == "high" and judge_verified:
        return "high"
    return "low"


def _judge_verified(
    *,
    claim_verdicts,
    combo_classification: str,
    tool_calls: list[dict[str, Any]],
) -> bool:
    unresolved = [
        verdict
        for verdict in claim_verdicts
        if verdict.status is ClaimVerdictStatus.INSUFFICIENT_EVIDENCE
    ]
    successful_evidence = any(
        call.get("status") == "success" and call.get("evidence")
        for call in tool_calls
    )
    if unresolved:
        return False
    if claim_verdicts:
        return successful_evidence
    return combo_classification in {"infinite_combo", "non_combo", "repeatable_synergy"} and successful_evidence


def _merge_tool_evidence(
    payload: dict[str, Any],
    tool_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    rules = list(payload.get("rules", []))
    rulings = list(payload.get("rulings", []))
    rule_keys = {str(rule.get("number", "")) for rule in rules}
    ruling_keys = {
        (str(item.get("oracle_id", "")), str(item.get("published_at", "")))
        for item in rulings
    }

    for call in tool_calls:
        for item in call.get("evidence", []):
            kind = item.get("kind")
            data = item.get("data", {})
            if not isinstance(data, dict):
                continue
            if kind == "rule":
                number = str(data.get("number", item.get("identifier", "")))
                if number and number not in rule_keys:
                    rules.append({"number": number, "title": str(data.get("title", data.get("text", "")))})
                    rule_keys.add(number)
            elif kind == "ruling":
                key = (str(data.get("oracle_id", "")), str(data.get("published_at", "")))
                if key not in ruling_keys:
                    rulings.append(data)
                    ruling_keys.add(key)

    return {**payload, "rules": rules, "rulings": rulings}


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
    target.strategy_context = deepcopy(getattr(source, "strategy_context", {}))
