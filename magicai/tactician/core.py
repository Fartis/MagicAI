from __future__ import annotations

from copy import deepcopy

from magicai.assistant import MagicAI
from magicai.tactician.models import TacticianResult
from magicai.tactician.strategy import analyze_strategy


class Tactician:
    """Strategic profile subordinated to the Judge's factual package."""

    def __init__(self, judge: MagicAI | None = None):
        self.judge = judge or MagicAI()

    def ask_result(self, conversation, question: str) -> TacticianResult:
        judge_conversation = deepcopy(conversation)
        judge_result = self.judge.ask_result(judge_conversation, question)
        judge_payload = judge_result.to_dict()

        judge_status = str(judge_payload.get("status", ""))
        if judge_status == "strategy_required":
            answer, synergies, risks = analyze_strategy(question, judge_payload)
            status = "answered"
            origin = "tactician_strategy"
            confidence = (
                "high"
                if synergies and judge_payload.get("confidence") == "high"
                else "medium"
            )
        else:
            answer = str(judge_payload.get("answer", ""))
            synergies = []
            risks = []
            status = judge_status or "insufficient_evidence"
            origin = "tactician_judge_gate"
            confidence = str(judge_payload.get("confidence", "low"))

        conversation.add_user_message(question)
        conversation.add_assistant_message(answer)
        _copy_state(judge_conversation, conversation)

        warnings = list(judge_payload.get("warnings", []))
        if judge_status not in {"strategy_required", "answered"}:
            warnings.append(
                "El Juez no pudo cerrar completamente la base factual; el Estratega no añadió una recomendación."
            )

        return TacticianResult(
            question=question,
            answer=answer,
            status=status,
            origin=origin,
            confidence=confidence,
            cards=list(judge_payload.get("cards", [])),
            rules=list(judge_payload.get("rules", [])),
            rulings=list(judge_payload.get("rulings", [])),
            retrieval_queries=list(judge_payload.get("retrieval_queries", [])),
            assumptions=list(judge_payload.get("assumptions", [])),
            warnings=warnings,
            synergies=synergies,
            risks=risks,
            authority_trace=(
                ["judge:factual_evidence", "tactician:strategic_interpretation"]
                if origin == "tactician_strategy"
                else ["judge:factual_answer", "tactician:relay"]
            ),
            judge_result=judge_payload,
        )


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
