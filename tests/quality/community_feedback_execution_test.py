from __future__ import annotations

from types import SimpleNamespace

from magicai.judge_result import (
    CardEvidence,
    JudgeConfidence,
    JudgeOrigin,
    JudgeResult,
    JudgeStatus,
    RuleEvidence,
)
from tests.quality.community_feedback.execution import run_feedback_case
from tests.quality.community_feedback.models import (
    FeedbackCase,
    FeedbackEvaluationMode,
    FeedbackOutcome,
    FeedbackReview,
    FeedbackSource,
    FeedbackTurn,
)
from tests.quality.open_judge.models import OpenJudgeTurn


class FakeAssistant:
    def ask_result(self, conversation, question: str) -> JudgeResult:
        conversation.add_user_message(question)
        answer = (
            "The original ability remains on the stack and exists independently "
            "of its source."
        )
        conversation.active_cards = [SimpleNamespace(name="Braids, Arisen Nightmare")]
        conversation.active_rules = ["113.7a"]
        conversation.add_assistant_message(answer)
        return JudgeResult(
            question=question,
            answer=answer,
            status=JudgeStatus.ANSWERED,
            origin=JudgeOrigin.DETERMINISTIC_RULE,
            confidence=JudgeConfidence.HIGH,
            cards=[CardEvidence(name="Braids, Arisen Nightmare")],
            rules=[RuleEvidence(number="113.7a", title="Source independence")],
        )


def _case(mode: FeedbackEvaluationMode) -> FeedbackCase:
    contract = None
    review = FeedbackReview(status="unreviewed")
    if mode is FeedbackEvaluationMode.VALIDATED:
        contract = OpenJudgeTurn(
            id="CF-BRAIDS-01",
            question="Does the original ability resolve after Braids is sacrificed?",
            required_any=(("remains on the stack", "independently of its source"),),
            expected_cards=("Braids, Arisen Nightmare",),
        )
        review = FeedbackReview(
            status="current_rules_validated",
            rules_version="2026-06-19",
            validated_at="2026-07-14",
            expected_summary="The original ability remains independent of its source.",
        )
    return FeedbackCase(
        schema_version="1.0",
        id="CF-BRAIDS",
        title="Copied ability removes its source",
        mode=mode,
        source=FeedbackSource(platform="manual"),
        review=review,
        tags=("copies", "source-independence"),
        turns=(
            FeedbackTurn(
                id="CF-BRAIDS-01",
                question="Does the original ability resolve after Braids is sacrificed?",
                contract=contract,
            ),
        ),
    )


def test_exploratory_case_never_becomes_false_pass() -> None:
    result = run_feedback_case(_case(FeedbackEvaluationMode.EXPLORATORY), FakeAssistant)
    assert result.outcome is FeedbackOutcome.REVIEW_REQUIRED
    assert result.turns[0].judge_result["origin"] == "deterministic_rule"
    assert result.turns[0].judge_result["rules"][0]["number"] == "113.7a"


def test_validated_case_reuses_open_judge_semantic_contract() -> None:
    result = run_feedback_case(_case(FeedbackEvaluationMode.VALIDATED), FakeAssistant)
    assert result.outcome is FeedbackOutcome.PASS
    assert not result.turns[0].findings


def main() -> int:
    tests = [
        test_exploratory_case_never_becomes_false_pass,
        test_validated_case_reuses_open_judge_semantic_contract,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Community feedback execution tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
