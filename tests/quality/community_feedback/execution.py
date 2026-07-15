from __future__ import annotations

import contextlib
import io
import time
import traceback
from collections.abc import Callable

from magicai.assistant import MagicAI
from magicai.conversation import Conversation
from tests.quality.open_judge.evaluator import evaluate_turn
from tests.quality.open_judge.execution import snapshot_conversation

from .diagnostics import classify_turn
from .models import (
    FeedbackCase,
    FeedbackCaseResult,
    FeedbackEvaluationMode,
    FeedbackFinding,
    FeedbackOutcome,
    FeedbackTurnResult,
)


OUTCOME_SEVERITY: dict[FeedbackOutcome, int] = {
    FeedbackOutcome.REVIEW_REQUIRED: 0,
    FeedbackOutcome.PASS: 0,
    FeedbackOutcome.FALSE_PREMISE_HANDLED: 0,
    FeedbackOutcome.CORRECT_BUT_INCOMPLETE: 1,
    FeedbackOutcome.NEEDS_CLARIFICATION: 1,
    FeedbackOutcome.STRATEGY_REQUIRED: 1,
    FeedbackOutcome.INSUFFICIENT_EVIDENCE: 2,
    FeedbackOutcome.RETRIEVAL_FAILURE: 3,
    FeedbackOutcome.CONTEXT_FAILURE: 4,
    FeedbackOutcome.FACTUAL_CONTRADICTION: 5,
    FeedbackOutcome.HALLUCINATION: 6,
    FeedbackOutcome.EXECUTION_ERROR: 7,
}

ACCEPTABLE_VALIDATED_OUTCOMES = {
    FeedbackOutcome.PASS,
    FeedbackOutcome.FALSE_PREMISE_HANDLED,
    FeedbackOutcome.NEEDS_CLARIFICATION,
    FeedbackOutcome.STRATEGY_REQUIRED,
}


def run_feedback_case(
    case: FeedbackCase,
    assistant_factory: Callable[[], MagicAI] = MagicAI,
) -> FeedbackCaseResult:
    assistant = assistant_factory()
    conversation = Conversation()
    results: list[FeedbackTurnResult] = []
    case_started = time.perf_counter()

    for index, turn in enumerate(case.turns, start=1):
        started = time.perf_counter()
        answer = ""
        result_payload: dict = {}
        exception = ""
        internal_output = io.StringIO()

        try:
            with contextlib.redirect_stdout(internal_output):
                judge_result = assistant.ask_result(conversation, turn.question)
                answer = judge_result.answer
                result_payload = judge_result.to_dict()
        except Exception:
            exception = traceback.format_exc()

        elapsed = time.perf_counter() - started
        snapshot = snapshot_conversation(conversation)

        if exception:
            outcome = FeedbackOutcome.EXECUTION_ERROR
            findings = [
                FeedbackFinding(
                    outcome=FeedbackOutcome.EXECUTION_ERROR.value,
                    message="Exception during answer generation.",
                )
            ]
        elif case.mode is FeedbackEvaluationMode.EXPLORATORY:
            outcome = FeedbackOutcome.REVIEW_REQUIRED
            findings = [
                FeedbackFinding(
                    outcome=FeedbackOutcome.REVIEW_REQUIRED.value,
                    message=(
                        "Exploratory case: inspect the answer and evidence, validate "
                        "against current sources, then add a semantic contract before promotion."
                    ),
                )
            ]
        else:
            assert turn.contract is not None
            evaluated, open_findings = evaluate_turn(
                contract=turn.contract,
                answer=answer,
                snapshot=snapshot,
                exception=exception,
                judge_status=str(result_payload.get("status", "")),
            )
            outcome = FeedbackOutcome(evaluated.value)
            findings = [
                FeedbackFinding(outcome=item.outcome.value, message=item.message)
                for item in open_findings
            ]

        turn_result = FeedbackTurnResult(
            case_id=case.id,
            case_title=case.title,
            turn_id=turn.id,
            turn_index=index,
            question=turn.question,
            answer=answer,
            outcome=outcome,
            elapsed=elapsed,
            judge_result=result_payload,
            conversation_snapshot={
                "cards": list(snapshot.cards),
                "keywords": list(snapshot.keywords),
                "rules": list(snapshot.rules),
                "intent": snapshot.intent,
                "history_size": snapshot.history_size,
            },
            findings=findings,
            exception=exception,
            internal_log=internal_output.getvalue().strip(),
        )
        turn_result.failure_family = classify_turn(turn_result)
        results.append(turn_result)

    aggregate = max(
        (turn.outcome for turn in results),
        key=lambda item: OUTCOME_SEVERITY[item],
        default=FeedbackOutcome.REVIEW_REQUIRED,
    )
    return FeedbackCaseResult(
        case=case,
        outcome=aggregate,
        elapsed=time.perf_counter() - case_started,
        turns=results,
    )
