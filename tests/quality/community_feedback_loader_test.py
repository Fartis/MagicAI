from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.community_feedback.loader import (
    FeedbackCaseError,
    load_feedback_case,
    write_template,
)
from tests.quality.community_feedback.models import FeedbackEvaluationMode


def test_template_loads_as_safe_exploratory_case() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "case.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        case = load_feedback_case(path)

    assert payload["artifact_purpose"] == "evaluation"
    assert payload["training_allowed"] is False
    assert payload["automatic_learning"] is False
    assert payload["automatic_promotion"] is False
    assert case.mode is FeedbackEvaluationMode.EXPLORATORY
    assert case.source.paraphrased is True
    assert case.source.contains_verbatim_quote is False
    assert case.source.contains_personal_data is False
    assert case.turns[0].contract is None


def test_loader_rejects_verbatim_or_personal_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "unsafe.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "id": "CF-UNSAFE",
                    "title": "Unsafe",
                    "mode": "exploratory",
                    "source": {
                        "platform": "reddit",
                        "paraphrased": False,
                        "contains_verbatim_quote": True,
                        "contains_personal_data": False,
                    },
                    "review": {"status": "unreviewed"},
                    "tags": [],
                    "turns": [{"question": "Paraphrase"}],
                }
            ),
            encoding="utf-8",
        )
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "paraphrased" in str(error)
        else:
            raise AssertionError("Unsafe verbatim case was accepted")


def test_loader_rejects_raw_content_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "raw.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["source"]["username"] = "someone"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "privacy/raw-content" in str(error)
        else:
            raise AssertionError("Raw identity field was accepted")



def test_loader_rejects_string_privacy_flags() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "flags.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["source"]["paraphrased"] = "true"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "JSON boolean" in str(error)
        else:
            raise AssertionError("String privacy flag was accepted")

def test_validated_case_requires_current_rules_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "validated.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["mode"] = "validated"
        payload["turns"][0]["required_all"] = ["stack"]
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "current_rules_validated" in str(error)
        else:
            raise AssertionError("Unreviewed validated case was accepted")



def test_validated_case_rejects_empty_semantic_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty-contract.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["mode"] = "validated"
        payload["review"] = {
            "status": "current_rules_validated",
            "rules_version": "2026-06-19",
            "validated_at": "2026-07-14",
            "expected_summary": "A reviewed answer.",
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "semantic assertion" in str(error)
        else:
            raise AssertionError("Validated turn without a contract was accepted")


def test_loader_rejects_training_fields_and_automatic_learning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "training.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["automatic_learning"] = True
        payload["turns"][0]["assistant_target"] = "A memorized answer"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "automatic_learning" in str(error) or "training field" in str(error)
        else:
            raise AssertionError("Training-oriented feedback artifact was accepted")


def test_loader_rejects_non_evaluation_purpose() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "purpose.json"
        write_template(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["artifact_purpose"] = "training"
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            load_feedback_case(path)
        except FeedbackCaseError as error:
            assert "evaluation-only" in str(error)
        else:
            raise AssertionError("Non-evaluation feedback artifact was accepted")

def main() -> int:
    tests = [
        test_template_loads_as_safe_exploratory_case,
        test_loader_rejects_verbatim_or_personal_data,
        test_loader_rejects_raw_content_keys,
        test_loader_rejects_string_privacy_flags,
        test_validated_case_requires_current_rules_review,
        test_validated_case_rejects_empty_semantic_contract,
        test_loader_rejects_training_fields_and_automatic_learning,
        test_loader_rejects_non_evaluation_purpose,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Community feedback loader tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
