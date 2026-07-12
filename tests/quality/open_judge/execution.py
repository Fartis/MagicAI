from __future__ import annotations

import contextlib
import io
import time
import traceback
from collections.abc import Callable

from magicai.assistant import MagicAI
from magicai.conversation import Conversation

from .evaluator import evaluate_turn
from .models import (
    OUTCOME_SEVERITY,
    ConversationSnapshot,
    OpenJudgeCase,
    OpenJudgeCaseResult,
    OpenJudgeOutcome,
    OpenJudgeTurnResult,
)


def snapshot_conversation(conversation: Conversation) -> ConversationSnapshot:
    cards = tuple(
        getattr(card, "name", str(card))
        for card in getattr(conversation, "active_cards", [])
    )
    keywords = tuple(str(item) for item in getattr(conversation, "active_keywords", []))
    rules = tuple(str(item) for item in getattr(conversation, "active_rules", []))

    return ConversationSnapshot(
        cards=cards,
        keywords=keywords,
        rules=rules,
        intent=str(getattr(conversation, "last_intent", "")),
        history_size=len(getattr(conversation, "history", [])),
    )


def aggregate_outcome(outcomes: list[OpenJudgeOutcome]) -> OpenJudgeOutcome:
    if not outcomes:
        return OpenJudgeOutcome.PASS

    return max(outcomes, key=lambda outcome: OUTCOME_SEVERITY[outcome])


def run_open_judge_case(
    case: OpenJudgeCase,
    assistant_factory: Callable[[], MagicAI] = MagicAI,
) -> OpenJudgeCaseResult:
    assistant = assistant_factory()
    conversation = Conversation()
    turn_results: list[OpenJudgeTurnResult] = []
    case_start = time.perf_counter()

    for turn_index, contract in enumerate(case.turns, start=1):
        start = time.perf_counter()
        answer = ""
        judge_status = ""
        judge_origin = ""
        judge_confidence = ""
        judge_authority = ""
        exception = ""
        internal_output = io.StringIO()

        try:
            with contextlib.redirect_stdout(internal_output):
                if hasattr(assistant, "ask_result"):
                    judge_result = assistant.ask_result(
                        conversation,
                        contract.question,
                    )
                    answer = judge_result.answer
                    judge_status = judge_result.status.value
                    judge_origin = judge_result.origin.value
                    judge_confidence = judge_result.confidence.value
                    judge_authority = judge_result.authority
                else:
                    answer = assistant.ask(conversation, contract.question)
        except Exception:
            exception = traceback.format_exc()

        elapsed = time.perf_counter() - start
        snapshot = snapshot_conversation(conversation)
        outcome, findings = evaluate_turn(
            contract=contract,
            answer=answer,
            snapshot=snapshot,
            exception=exception,
            judge_status=judge_status,
        )

        turn_results.append(
            OpenJudgeTurnResult(
                case_id=case.id,
                case_name=case.name,
                turn_id=contract.id,
                turn_index=turn_index,
                question=contract.question,
                answer=answer,
                outcome=outcome,
                elapsed=elapsed,
                findings=findings,
                snapshot=snapshot,
                judge_status=judge_status,
                judge_origin=judge_origin,
                judge_confidence=judge_confidence,
                judge_authority=judge_authority,
                exception=exception,
                internal_log=internal_output.getvalue().strip(),
            )
        )

    return OpenJudgeCaseResult(
        id=case.id,
        name=case.name,
        tags=case.tags,
        outcome=aggregate_outcome([turn.outcome for turn in turn_results]),
        elapsed=time.perf_counter() - case_start,
        turns=turn_results,
    )
