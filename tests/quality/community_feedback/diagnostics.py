from __future__ import annotations

from collections import Counter
from typing import Any

from .models import (
    FeedbackCaseResult,
    FeedbackFailureFamily,
    FeedbackOutcome,
    FeedbackTurnResult,
)


NO_FAILURE_OUTCOMES = {
    FeedbackOutcome.PASS,
    FeedbackOutcome.FALSE_PREMISE_HANDLED,
    FeedbackOutcome.NEEDS_CLARIFICATION,
    FeedbackOutcome.STRATEGY_REQUIRED,
}


def classify_turn(turn: FeedbackTurnResult) -> FeedbackFailureFamily:
    if turn.exception or turn.outcome is FeedbackOutcome.EXECUTION_ERROR:
        return FeedbackFailureFamily.EXECUTION_ERROR

    if turn.outcome is FeedbackOutcome.REVIEW_REQUIRED:
        return FeedbackFailureFamily.REVIEW_REQUIRED

    if turn.outcome in NO_FAILURE_OUTCOMES:
        return FeedbackFailureFamily.NO_FAILURE

    messages = " ".join(item.message.lower() for item in turn.findings)
    origin = str(turn.judge_result.get("origin", "")).lower()

    if "expected active card missing" in messages or "stale card remained active" in messages:
        return FeedbackFailureFamily.CARD_EXTRACTION_FAILURE

    if "status mismatch" in messages and any(
        expected in messages
        for expected in (
            "needs_clarification",
            "false_premise",
            "strategy_required",
        )
    ):
        return FeedbackFailureFamily.RULE_INTENT_FAILURE

    if turn.outcome is FeedbackOutcome.CONTEXT_FAILURE:
        return FeedbackFailureFamily.CONTEXT_FAILURE

    if turn.outcome is FeedbackOutcome.FACTUAL_CONTRADICTION:
        return FeedbackFailureFamily.FACTUAL_CONTRADICTION

    if turn.outcome is FeedbackOutcome.HALLUCINATION:
        return FeedbackFailureFamily.HALLUCINATION

    if turn.outcome is FeedbackOutcome.INSUFFICIENT_EVIDENCE:
        return FeedbackFailureFamily.UNSUPPORTED_SCENARIO

    if turn.outcome is FeedbackOutcome.CORRECT_BUT_INCOMPLETE:
        if origin.startswith("deterministic_"):
            return FeedbackFailureFamily.RENDERER_FAILURE
        return FeedbackFailureFamily.VALIDATOR_FAILURE

    if turn.outcome is FeedbackOutcome.RETRIEVAL_FAILURE:
        rules = turn.judge_result.get("rules") or []
        if "card" in messages:
            return FeedbackFailureFamily.CARD_EXTRACTION_FAILURE
        if "oracle" in messages:
            return FeedbackFailureFamily.ORACLE_RETRIEVAL_FAILURE
        if "rule" in messages or not rules:
            return FeedbackFailureFamily.RULE_RETRIEVAL_FAILURE
        return FeedbackFailureFamily.VALIDATOR_FAILURE

    return FeedbackFailureFamily.VALIDATOR_FAILURE


def apply_failure_families(results: list[FeedbackCaseResult]) -> None:
    for result in results:
        for turn in result.turns:
            turn.failure_family = classify_turn(turn)


def build_findings_by_family(results: list[FeedbackCaseResult]) -> dict[str, Any]:
    apply_failure_families(results)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        for turn in result.turns:
            family = turn.failure_family.value
            grouped.setdefault(family, []).append(
                {
                    "case_id": result.case.id,
                    "case_title": result.case.title,
                    "turn_id": turn.turn_id,
                    "outcome": turn.outcome.value,
                    "question": turn.question,
                    "answer": turn.answer,
                    "judge_status": turn.judge_result.get("status", ""),
                    "judge_origin": turn.judge_result.get("origin", ""),
                    "findings": [
                        {"outcome": item.outcome, "message": item.message}
                        for item in turn.findings
                    ],
                    "exception": turn.exception,
                }
            )

    counts = Counter(
        turn.failure_family.value
        for result in results
        for turn in result.turns
    )
    return {
        "schema_version": "1.0",
        "artifact_purpose": "evaluation",
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "counts": dict(sorted(counts.items())),
        "families": {key: grouped[key] for key in sorted(grouped)},
    }
