from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.community_feedback.execution import run_feedback_case
from tests.quality.community_feedback.models import (
    FeedbackCase,
    FeedbackEvaluationMode,
    FeedbackReview,
    FeedbackSource,
    FeedbackTurn,
)
from tests.quality.community_feedback.reports import write_feedback_reports
from tests.quality.community_feedback_execution_test import FakeAssistant


def _case() -> FeedbackCase:
    return FeedbackCase(
        schema_version="1.0",
        id="CF-REPORT",
        title="Report safety",
        mode=FeedbackEvaluationMode.EXPLORATORY,
        source=FeedbackSource(
            platform="reddit",
            url="https://www.reddit.com/r/mtgrules/comments/example/",
            topic_id="example",
            paraphrased=True,
            contains_verbatim_quote=False,
            contains_personal_data=False,
        ),
        review=FeedbackReview(status="unreviewed"),
        tags=("manual-feedback",),
        turns=(
            FeedbackTurn(
                id="CF-REPORT-01",
                question="Paraphrased question about a copied ability.",
            ),
        ),
    )


def test_reports_include_review_packet_and_structured_evidence() -> None:
    result = run_feedback_case(_case(), FakeAssistant)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        write_feedback_reports(
            [result],
            output,
            {"created_at": "2026-07-14T00:00:00"},
        )
        summary = json.loads(
            (output / "community_feedback_summary.json").read_text(encoding="utf-8")
        )
        packet = json.loads(
            (output / "review_packets" / "CF-REPORT_review.json").read_text(
                encoding="utf-8"
            )
        )
        html = (output / "community_feedback_summary.html").read_text(
            encoding="utf-8"
        )

    assert summary["summary"]["review_required"] == 1
    assert packet["review_decision"]["promote_to_regression"] is False
    assert packet["turns"][0]["judge_result"]["rules"][0]["number"] == "113.7a"
    assert "MagicAI Community Feedback Gauntlet" in html
    assert "Paraphrased question" in html


def test_reports_do_not_create_identity_fields() -> None:
    result = run_feedback_case(_case(), FakeAssistant)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        write_feedback_reports([result], output, {})
        text = (output / "community_feedback_summary.json").read_text(
            encoding="utf-8"
        )

    assert '"username"' not in text
    assert '"author"' not in text
    assert '"raw_post"' not in text



def test_reports_preserve_manual_review_decision_on_checkpoint() -> None:
    result = run_feedback_case(_case(), FakeAssistant)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        write_feedback_reports([result], output, {"created_at": "first"})
        packet_path = output / "review_packets" / "CF-REPORT_review.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        packet["review_decision"]["current_sources_checked"] = True
        packet["review_decision"]["generic_fix"] = "Improve generic retrieval."
        packet_path.write_text(json.dumps(packet), encoding="utf-8")

        write_feedback_reports([result], output, {"created_at": "second"})
        preserved = json.loads(packet_path.read_text(encoding="utf-8"))

    assert preserved["review_decision"]["current_sources_checked"] is True
    assert preserved["review_decision"]["generic_fix"] == "Improve generic retrieval."


def test_reports_publish_evaluation_contract_and_failure_families() -> None:
    result = run_feedback_case(_case(), FakeAssistant)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        write_feedback_reports([result], output, {})
        summary = json.loads(
            (output / "community_feedback_summary.json").read_text(encoding="utf-8")
        )
        families = json.loads(
            (output / "findings_by_family.json").read_text(encoding="utf-8")
        )
        names = {path.name for path in output.rglob("*") if path.is_file()}

    assert summary["artifact_purpose"] == "evaluation"
    assert summary["training_allowed"] is False
    assert families["counts"]["REVIEW_REQUIRED"] == 1
    assert not {
        "training.jsonl",
        "fine_tuning_dataset.json",
        "learned_examples.json",
    } & names

def main() -> int:
    tests = [
        test_reports_include_review_packet_and_structured_evidence,
        test_reports_do_not_create_identity_fields,
        test_reports_preserve_manual_review_decision_on_checkpoint,
        test_reports_publish_evaluation_contract_and_failure_families,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Community feedback report tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
