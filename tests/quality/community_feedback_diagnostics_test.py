from __future__ import annotations

from tests.quality.community_feedback.diagnostics import classify_turn
from tests.quality.community_feedback.models import (
    FeedbackFailureFamily,
    FeedbackFinding,
    FeedbackOutcome,
    FeedbackTurnResult,
)


def _turn(
    outcome: FeedbackOutcome,
    *,
    findings: list[FeedbackFinding] | None = None,
    judge_result: dict | None = None,
    exception: str = "",
) -> FeedbackTurnResult:
    return FeedbackTurnResult(
        case_id="CF-DIAG",
        case_title="Diagnostics",
        turn_id="CF-DIAG-01",
        turn_index=1,
        question="Question",
        answer="Answer",
        outcome=outcome,
        elapsed=0.1,
        findings=findings or [],
        judge_result=judge_result or {},
        exception=exception,
    )


def test_exploratory_and_execution_results_have_explicit_families() -> None:
    assert (
        classify_turn(_turn(FeedbackOutcome.REVIEW_REQUIRED))
        is FeedbackFailureFamily.REVIEW_REQUIRED
    )
    assert (
        classify_turn(
            _turn(FeedbackOutcome.EXECUTION_ERROR, exception="traceback")
        )
        is FeedbackFailureFamily.EXECUTION_ERROR
    )


def test_missing_active_card_is_classified_as_extraction_failure() -> None:
    turn = _turn(
        FeedbackOutcome.CONTEXT_FAILURE,
        findings=[
            FeedbackFinding(
                outcome="CONTEXT_FAILURE",
                message="Expected active card missing from conversation state: Young Wolf",
            )
        ],
    )
    assert classify_turn(turn) is FeedbackFailureFamily.CARD_EXTRACTION_FAILURE


def test_retrieval_failure_without_rules_is_grouped_as_rule_retrieval() -> None:
    turn = _turn(
        FeedbackOutcome.RETRIEVAL_FAILURE,
        findings=[
            FeedbackFinding(
                outcome="RETRIEVAL_FAILURE",
                message="Missing required rule explanation.",
            )
        ],
        judge_result={"cards": [{"name": "Young Wolf"}], "rules": []},
    )
    assert classify_turn(turn) is FeedbackFailureFamily.RULE_RETRIEVAL_FAILURE


def test_deterministic_incomplete_answer_points_to_renderer() -> None:
    turn = _turn(
        FeedbackOutcome.CORRECT_BUT_INCOMPLETE,
        judge_result={"origin": "deterministic_rule"},
    )
    assert classify_turn(turn) is FeedbackFailureFamily.RENDERER_FAILURE



def test_status_mismatch_for_clarification_is_grouped_as_rule_intent() -> None:
    turn = _turn(
        FeedbackOutcome.CONTEXT_FAILURE,
        findings=[
            FeedbackFinding(
                outcome="CONTEXT_FAILURE",
                message=(
                    "JudgeResult status mismatch: expected 'needs_clarification', "
                    "got 'answered'."
                ),
            )
        ],
        judge_result={"status": "answered"},
    )
    assert classify_turn(turn) is FeedbackFailureFamily.RULE_INTENT_FAILURE

def main() -> int:
    tests = [
        test_exploratory_and_execution_results_have_explicit_families,
        test_missing_active_card_is_classified_as_extraction_failure,
        test_retrieval_failure_without_rules_is_grouped_as_rule_retrieval,
        test_deterministic_incomplete_answer_points_to_renderer,
        test_status_mismatch_for_clarification_is_grouped_as_rule_intent,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Community feedback diagnostics tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
