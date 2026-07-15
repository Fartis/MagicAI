from __future__ import annotations

import json
import tempfile
from pathlib import Path

from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeResult,
    JudgeStatus,
)
from tests.quality.community_feedback.campaign import (
    FeedbackCampaignError,
    FeedbackCampaignStore,
    execute_feedback_campaign,
)
from tests.quality.community_feedback.models import (
    FeedbackCase,
    FeedbackEvaluationMode,
    FeedbackReview,
    FeedbackSource,
    FeedbackTurn,
)


def _case(case_id: str, question: str | None = None) -> FeedbackCase:
    question = question or f"Question for {case_id}?"
    return FeedbackCase(
        schema_version="1.0",
        id=case_id,
        title=f"Case {case_id}",
        mode=FeedbackEvaluationMode.EXPLORATORY,
        source=FeedbackSource(platform="manual"),
        review=FeedbackReview(status="unreviewed"),
        tags=("campaign-test",),
        turns=(
            FeedbackTurn(
                id=f"{case_id}-01",
                question=question,
            ),
        ),
    )


class RecordingAssistant:
    def __init__(
        self,
        calls: list[str],
        *,
        fail_questions: set[str] | None = None,
        interrupt_questions: set[str] | None = None,
    ) -> None:
        self.calls = calls
        self.fail_questions = fail_questions or set()
        self.interrupt_questions = interrupt_questions or set()

    def ask_result(self, conversation, question: str) -> JudgeResult:
        self.calls.append(question)
        if question in self.interrupt_questions:
            raise KeyboardInterrupt()
        if question in self.fail_questions:
            raise RuntimeError("simulated failure")
        conversation.add_user_message(question)
        answer = "Evaluation answer grounded by the fake test assistant."
        conversation.add_assistant_message(answer)
        return JudgeResult(
            question=question,
            answer=answer,
            status=JudgeStatus.ANSWERED,
            origin=JudgeOrigin.DETERMINISTIC_RULE,
            confidence=JudgeConfidence.HIGH,
        )


def _store(root: Path, campaign_id: str = "campaign-test") -> FeedbackCampaignStore:
    return FeedbackCampaignStore(
        campaign_id=campaign_id,
        output_dir=root / campaign_id,
        input_path=Path("community_feedback/inbox"),
        project_root=root,
        command=["python", "-m", "tests.quality.community_feedback_test"],
        include_source_hashes=False,
    )


def test_campaign_writes_evaluation_manifest_and_case_checkpoint() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = execute_feedback_campaign(
            [_case("CF-A")],
            store=_store(root),
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        manifest = json.loads(
            (run.output_dir / "campaign_manifest.json").read_text(encoding="utf-8")
        )
        progress = json.loads(
            (run.output_dir / "campaign_progress.json").read_text(encoding="utf-8")
        )
        persisted = list((run.output_dir / "completed").glob("*.json"))

    assert calls == ["Question for CF-A?"]
    assert manifest["artifact_purpose"] == "evaluation"
    assert manifest["training_allowed"] is False
    assert manifest["automatic_learning"] is False
    assert manifest["automatic_promotion"] is False
    assert manifest["status"] == "completed"
    assert progress["counts"]["pending_cases"] == 0
    assert len(persisted) == 1


def test_resume_skips_completed_cases() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = [_case("CF-A"), _case("CF-B")]
        store = _store(root, "resume-test")
        execute_feedback_campaign(
            cases,
            store=store,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        execute_feedback_campaign(
            cases,
            store=store,
            resume=True,
            assistant_factory=lambda: RecordingAssistant(calls),
        )

    assert calls == ["Question for CF-A?", "Question for CF-B?"]


def test_retry_errors_reruns_only_failed_cases() -> None:
    calls: list[str] = []
    failed_question = "Question for CF-B?"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = [_case("CF-A"), _case("CF-B")]
        store = _store(root, "retry-test")
        first = execute_feedback_campaign(
            cases,
            store=store,
            assistant_factory=lambda: RecordingAssistant(
                calls,
                fail_questions={failed_question},
            ),
        )
        assert first.manifest["counts"]["execution_error_cases"] == 1
        assert len(list((store.output_dir / "execution_errors").glob("*.json"))) == 1

        second = execute_feedback_campaign(
            cases,
            store=store,
            resume=True,
            retry_errors=True,
            assistant_factory=lambda: RecordingAssistant(calls),
        )

        assert second.manifest["counts"]["execution_error_cases"] == 0
        assert not list((store.output_dir / "execution_errors").glob("*.json"))
        assert len(list((store.output_dir / "completed").glob("*.json"))) == 2

    assert calls == [
        "Question for CF-A?",
        failed_question,
        failed_question,
    ]


def test_interruption_checkpoints_and_resume_continues() -> None:
    calls: list[str] = []
    interrupted_question = "Question for CF-B?"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = [_case("CF-A"), _case("CF-B"), _case("CF-C")]
        store = _store(root, "interrupt-test")
        first = execute_feedback_campaign(
            cases,
            store=store,
            assistant_factory=lambda: RecordingAssistant(
                calls,
                interrupt_questions={interrupted_question},
            ),
        )
        assert first.interrupted is True
        assert first.manifest["status"] == "interrupted"
        assert first.manifest["counts"]["processed_cases"] == 1

        second = execute_feedback_campaign(
            cases,
            store=store,
            resume=True,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        assert second.interrupted is False
        assert second.manifest["counts"]["processed_cases"] == 3

    assert calls == [
        "Question for CF-A?",
        interrupted_question,
        interrupted_question,
        "Question for CF-C?",
    ]


def test_resume_rejects_changed_case_definition() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = _store(root, "fingerprint-test")
        execute_feedback_campaign(
            [_case("CF-A", "Original question")],
            store=store,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        try:
            execute_feedback_campaign(
                [_case("CF-A", "Changed question")],
                store=store,
                resume=True,
                assistant_factory=lambda: RecordingAssistant(calls),
            )
        except FeedbackCampaignError as error:
            assert "changed" in str(error).lower()
        else:
            raise AssertionError("Changed case definition was mixed into an existing campaign")


def test_source_snapshot_can_hash_local_authority_files() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rule_path = root / "sources/rules/MagicCompRules.txt"
        rule_path.parent.mkdir(parents=True)
        rule_path.write_text("100.1 Test rule", encoding="utf-8")
        store = FeedbackCampaignStore(
            campaign_id="hash-test",
            output_dir=root / "hash-test",
            input_path=Path("case.json"),
            project_root=root,
            include_source_hashes=True,
        )
        run = execute_feedback_campaign(
            [_case("CF-HASH")],
            store=store,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        snapshot = run.manifest["sources"]["sources/rules/MagicCompRules.txt"]

    assert snapshot["exists"] is True
    assert snapshot["size_bytes"] > 0
    assert len(snapshot["sha256"]) == 64



def test_resume_rejects_changed_authority_source_snapshot() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rule_path = root / "sources/rules/MagicCompRules.txt"
        rule_path.parent.mkdir(parents=True)
        rule_path.write_text("100.1 First snapshot", encoding="utf-8")
        store = FeedbackCampaignStore(
            campaign_id="source-change-test",
            output_dir=root / "source-change-test",
            input_path=Path("case.json"),
            project_root=root,
            include_source_hashes=True,
        )
        cases = [_case("CF-SOURCE")]
        execute_feedback_campaign(
            cases,
            store=store,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        rule_path.write_text("100.1 Changed snapshot", encoding="utf-8")
        try:
            execute_feedback_campaign(
                cases,
                store=store,
                resume=True,
                assistant_factory=lambda: RecordingAssistant(calls),
            )
        except FeedbackCampaignError as error:
            assert "source snapshots changed" in str(error).lower()
        else:
            raise AssertionError("Changed authority sources were mixed into one campaign")


def test_resume_rejects_changed_judge_code_snapshot() -> None:
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code_path = root / "magicai/example.py"
        code_path.parent.mkdir(parents=True)
        code_path.write_text("VALUE = 1\n", encoding="utf-8")
        store = _store(root, "code-change-test")
        cases = [_case("CF-CODE")]
        execute_feedback_campaign(
            cases,
            store=store,
            assistant_factory=lambda: RecordingAssistant(calls),
        )
        code_path.write_text("VALUE = 2\n", encoding="utf-8")
        try:
            execute_feedback_campaign(
                cases,
                store=store,
                resume=True,
                assistant_factory=lambda: RecordingAssistant(calls),
            )
        except FeedbackCampaignError as error:
            assert "code changed" in str(error).lower()
        else:
            raise AssertionError("Changed Judge code was mixed into one campaign")

def main() -> int:
    tests = [
        test_campaign_writes_evaluation_manifest_and_case_checkpoint,
        test_resume_skips_completed_cases,
        test_retry_errors_reruns_only_failed_cases,
        test_interruption_checkpoints_and_resume_continues,
        test_resume_rejects_changed_case_definition,
        test_source_snapshot_can_hash_local_authority_files,
        test_resume_rejects_changed_authority_source_snapshot,
        test_resume_rejects_changed_judge_code_snapshot,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Community feedback campaign tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
