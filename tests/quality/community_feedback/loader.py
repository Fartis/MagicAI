from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.quality.open_judge.models import ForbiddenClaim, OpenJudgeOutcome, OpenJudgeTurn

from .models import (
    FeedbackCase,
    FeedbackEvaluationMode,
    FeedbackReview,
    FeedbackSource,
    FeedbackTurn,
)


SCHEMA_VERSION = "1.0"
ARTIFACT_PURPOSE = "evaluation"
FORBIDDEN_TRAINING_KEYS = {
    "training_target",
    "target_completion",
    "fine_tune_messages",
    "fine_tuning_messages",
    "assistant_target",
    "prompt_completion",
    "learned_examples",
    "training_examples",
}
ALLOWED_PLATFORMS = {"manual", "judgeapps", "reddit", "other"}
ALLOWED_REVIEW_STATUSES = {
    "unreviewed",
    "current_rules_validated",
    "historical_only",
    "out_of_scope",
}
FORBIDDEN_PRIVACY_KEYS = {
    "author",
    "username",
    "user_name",
    "display_name",
    "raw_post",
    "raw_comment",
    "post_text",
    "comment_text",
    "full_post",
    "full_comment",
}


class FeedbackCaseError(ValueError):
    pass


def discover_case_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(path for path in input_path.glob("*.json") if path.is_file())
    raise FeedbackCaseError(f"Input path does not exist: {input_path}")


def load_feedback_cases(input_path: Path) -> list[FeedbackCase]:
    files = discover_case_files(input_path)
    if not files:
        raise FeedbackCaseError(f"No JSON feedback cases found in: {input_path}")
    return [load_feedback_case(path) for path in files]


def load_feedback_case(path: Path) -> FeedbackCase:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FeedbackCaseError(f"Invalid JSON in {path}: {error}") from error

    if not isinstance(payload, dict):
        raise FeedbackCaseError(f"Feedback case must be a JSON object: {path}")

    _reject_privacy_keys(payload, path)
    _validate_evaluation_contract(payload, path)

    schema_version = _required_text(payload, "schema_version", path)
    if schema_version != SCHEMA_VERSION:
        raise FeedbackCaseError(
            f"Unsupported feedback schema {schema_version!r} in {path}; expected {SCHEMA_VERSION!r}."
        )

    case_id = _required_text(payload, "id", path)
    title = _required_text(payload, "title", path)

    try:
        mode = FeedbackEvaluationMode(str(payload.get("mode", "exploratory")))
    except ValueError as error:
        raise FeedbackCaseError(
            f"Invalid mode in {path}; use 'exploratory' or 'validated'."
        ) from error

    source = _load_source(payload.get("source", {}), path)
    review = _load_review(payload.get("review", {}), path)
    tags = _text_tuple(payload.get("tags", []), "tags", path)

    raw_turns = payload.get("turns")
    if not isinstance(raw_turns, list) or not raw_turns:
        raise FeedbackCaseError(f"Case {case_id!r} must contain at least one turn.")

    turns = tuple(
        _load_turn(item, case_id=case_id, mode=mode, index=index, path=path)
        for index, item in enumerate(raw_turns, start=1)
    )

    if mode is FeedbackEvaluationMode.VALIDATED:
        if review.status != "current_rules_validated":
            raise FeedbackCaseError(
                f"Validated case {case_id!r} requires review.status='current_rules_validated'."
            )
        if not review.expected_summary.strip():
            raise FeedbackCaseError(
                f"Validated case {case_id!r} requires review.expected_summary."
            )

    return FeedbackCase(
        schema_version=schema_version,
        id=case_id,
        title=title,
        mode=mode,
        source=source,
        review=review,
        tags=tags,
        turns=turns,
    )


def write_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "artifact_purpose": ARTIFACT_PURPOSE,
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "id": "CF-LOCAL-001",
        "title": "Describe the interaction briefly",
        "mode": "exploratory",
        "source": {
            "platform": "manual",
            "url": "",
            "topic_id": "",
            "published_at": "",
            "retrieved_at": "",
            "paraphrased": True,
            "contains_verbatim_quote": False,
            "contains_personal_data": False,
            "notes": "Optional minimal provenance. Do not paste usernames or full posts.",
        },
        "review": {
            "status": "unreviewed",
            "rules_version": "",
            "validated_at": "",
            "expected_summary": "",
            "notes": "Describe why the answer looks suspicious after running the case.",
        },
        "tags": ["manual-feedback"],
        "turns": [
            {
                "id": "CF-LOCAL-001-01",
                "question": "Write a paraphrased rules question here.",
                "notes": "Optional context for the reviewer.",
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_source(raw: Any, path: Path) -> FeedbackSource:
    if not isinstance(raw, dict):
        raise FeedbackCaseError(f"source must be an object in {path}.")

    platform = str(raw.get("platform", "manual")).strip().lower()
    if platform not in ALLOWED_PLATFORMS:
        raise FeedbackCaseError(
            f"Unsupported source.platform {platform!r} in {path}."
        )

    paraphrased = _bool_value(raw, "paraphrased", True, path)
    contains_verbatim_quote = _bool_value(
        raw, "contains_verbatim_quote", False, path
    )
    contains_personal_data = _bool_value(
        raw, "contains_personal_data", False, path
    )

    if not paraphrased or contains_verbatim_quote or contains_personal_data:
        raise FeedbackCaseError(
            "Manual feedback cases must be paraphrased and must not contain "
            "verbatim forum text or personal data."
        )

    return FeedbackSource(
        platform=platform,
        url=str(raw.get("url", "")).strip(),
        topic_id=str(raw.get("topic_id", "")).strip(),
        published_at=str(raw.get("published_at", "")).strip(),
        retrieved_at=str(raw.get("retrieved_at", "")).strip(),
        paraphrased=paraphrased,
        contains_verbatim_quote=contains_verbatim_quote,
        contains_personal_data=contains_personal_data,
        notes=str(raw.get("notes", "")).strip(),
    )


def _load_review(raw: Any, path: Path) -> FeedbackReview:
    if not isinstance(raw, dict):
        raise FeedbackCaseError(f"review must be an object in {path}.")

    status = str(raw.get("status", "unreviewed")).strip().lower()
    if status not in ALLOWED_REVIEW_STATUSES:
        raise FeedbackCaseError(f"Unsupported review.status {status!r} in {path}.")

    return FeedbackReview(
        status=status,
        rules_version=str(raw.get("rules_version", "")).strip(),
        validated_at=str(raw.get("validated_at", "")).strip(),
        expected_summary=str(raw.get("expected_summary", "")).strip(),
        notes=str(raw.get("notes", "")).strip(),
    )


def _load_turn(
    raw: Any,
    *,
    case_id: str,
    mode: FeedbackEvaluationMode,
    index: int,
    path: Path,
) -> FeedbackTurn:
    if not isinstance(raw, dict):
        raise FeedbackCaseError(f"Turn {index} in {path} must be an object.")

    turn_id = str(raw.get("id") or f"{case_id}-{index:02d}").strip()
    question = _required_text(raw, "question", path)
    notes = str(raw.get("notes", "")).strip()

    if mode is FeedbackEvaluationMode.EXPLORATORY:
        return FeedbackTurn(id=turn_id, question=question, notes=notes)

    forbidden = tuple(
        ForbiddenClaim(
            text=_required_text(item, "text", path),
            outcome=_outcome(item.get("outcome", "FACTUAL_CONTRADICTION"), path),
        )
        for item in _object_list(raw.get("forbidden", []), "forbidden", path)
    )

    contract = OpenJudgeTurn(
        id=turn_id,
        question=question,
        required_all=_text_tuple(raw.get("required_all", []), "required_all", path),
        required_any=_group_tuple(raw.get("required_any", []), "required_any", path),
        recommended_all=_text_tuple(
            raw.get("recommended_all", []), "recommended_all", path
        ),
        recommended_any=_group_tuple(
            raw.get("recommended_any", []), "recommended_any", path
        ),
        forbidden=forbidden,
        expected_cards=_text_tuple(
            raw.get("expected_cards", []), "expected_cards", path
        ),
        forbidden_cards=_text_tuple(
            raw.get("forbidden_cards", []), "forbidden_cards", path
        ),
        missing_outcome=_outcome(
            raw.get("missing_outcome", "RETRIEVAL_FAILURE"), path
        ),
        success_outcome=_outcome(raw.get("success_outcome", "PASS"), path),
        notes=notes,
    )
    if not _has_meaningful_contract(contract):
        raise FeedbackCaseError(
            f"Validated turn {turn_id!r} in {path} needs at least one semantic "
            "assertion or a non-PASS expected status."
        )
    return FeedbackTurn(id=turn_id, question=question, contract=contract, notes=notes)


def _has_meaningful_contract(contract: OpenJudgeTurn) -> bool:
    return bool(
        contract.required_all
        or contract.required_any
        or contract.recommended_all
        or contract.recommended_any
        or contract.forbidden
        or contract.expected_cards
        or contract.forbidden_cards
        or contract.success_outcome is not OpenJudgeOutcome.PASS
    )


def _required_text(raw: dict[str, Any], key: str, path: Path) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise FeedbackCaseError(f"Missing non-empty {key!r} in {path}.")
    return value


def _text_tuple(raw: Any, label: str, path: Path) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise FeedbackCaseError(f"{label} must be a list in {path}.")
    return tuple(str(item).strip() for item in raw if str(item).strip())


def _group_tuple(raw: Any, label: str, path: Path) -> tuple[tuple[str, ...], ...]:
    if not isinstance(raw, list):
        raise FeedbackCaseError(f"{label} must be a list of lists in {path}.")
    groups: list[tuple[str, ...]] = []
    for group in raw:
        if not isinstance(group, list):
            raise FeedbackCaseError(f"Every {label} entry must be a list in {path}.")
        values = tuple(str(item).strip() for item in group if str(item).strip())
        if values:
            groups.append(values)
    return tuple(groups)


def _object_list(raw: Any, label: str, path: Path) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise FeedbackCaseError(f"{label} must be a list of objects in {path}.")
    return raw


def _bool_value(raw: dict[str, Any], key: str, default: bool, path: Path) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise FeedbackCaseError(f"{key} must be a JSON boolean in {path}.")
    return value


def _outcome(raw: Any, path: Path) -> OpenJudgeOutcome:
    try:
        return OpenJudgeOutcome(str(raw))
    except ValueError as error:
        raise FeedbackCaseError(f"Invalid Open Judge outcome {raw!r} in {path}.") from error


def _reject_privacy_keys(value: Any, path: Path, prefix: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            current = f"{prefix}.{key}" if prefix else str(key)
            if normalized in FORBIDDEN_PRIVACY_KEYS:
                raise FeedbackCaseError(
                    f"Forbidden privacy/raw-content field {current!r} in {path}."
                )
            _reject_privacy_keys(child, path, current)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_privacy_keys(child, path, f"{prefix}[{index}]")

def _validate_evaluation_contract(payload: dict[str, Any], path: Path) -> None:
    purpose = str(payload.get("artifact_purpose", ARTIFACT_PURPOSE)).strip().lower()
    if purpose != ARTIFACT_PURPOSE:
        raise FeedbackCaseError(
            f"Feedback artifacts are evaluation-only in {path}; "
            f"artifact_purpose must be {ARTIFACT_PURPOSE!r}."
        )

    for key in ("training_allowed", "automatic_learning", "automatic_promotion"):
        if key not in payload:
            continue
        value = payload[key]
        if not isinstance(value, bool):
            raise FeedbackCaseError(f"{key} must be a JSON boolean in {path}.")
        if value:
            raise FeedbackCaseError(
                f"{key}=true is forbidden in evaluation-only feedback artifacts: {path}"
            )

    _reject_training_keys(payload, path)


def _reject_training_keys(value: Any, path: Path, prefix: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            current = f"{prefix}.{key}" if prefix else str(key)
            if normalized in FORBIDDEN_TRAINING_KEYS:
                raise FeedbackCaseError(
                    f"Forbidden training field {current!r} in evaluation artifact {path}."
                )
            _reject_training_keys(child, path, current)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_training_keys(child, path, f"{prefix}[{index}]")

