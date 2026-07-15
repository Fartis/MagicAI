from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from tests.quality.open_judge.models import OpenJudgeTurn


class FeedbackEvaluationMode(str, Enum):
    EXPLORATORY = "exploratory"
    VALIDATED = "validated"


class FeedbackOutcome(str, Enum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PASS = "PASS"
    CORRECT_BUT_INCOMPLETE = "CORRECT_BUT_INCOMPLETE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    STRATEGY_REQUIRED = "STRATEGY_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FALSE_PREMISE_HANDLED = "FALSE_PREMISE_HANDLED"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    CONTEXT_FAILURE = "CONTEXT_FAILURE"
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    HALLUCINATION = "HALLUCINATION"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class FeedbackFailureFamily(str, Enum):
    NO_FAILURE = "NO_FAILURE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CARD_EXTRACTION_FAILURE = "CARD_EXTRACTION_FAILURE"
    RULE_INTENT_FAILURE = "RULE_INTENT_FAILURE"
    ORACLE_RETRIEVAL_FAILURE = "ORACLE_RETRIEVAL_FAILURE"
    RULE_RETRIEVAL_FAILURE = "RULE_RETRIEVAL_FAILURE"
    CONTEXT_FAILURE = "CONTEXT_FAILURE"
    RENDERER_FAILURE = "RENDERER_FAILURE"
    VALIDATOR_FAILURE = "VALIDATOR_FAILURE"
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    HALLUCINATION = "HALLUCINATION"
    UNSUPPORTED_SCENARIO = "UNSUPPORTED_SCENARIO"
    EXECUTION_ERROR = "EXECUTION_ERROR"


@dataclass(frozen=True, slots=True)
class FeedbackSource:
    platform: str = "manual"
    url: str = ""
    topic_id: str = ""
    published_at: str = ""
    retrieved_at: str = ""
    paraphrased: bool = True
    contains_verbatim_quote: bool = False
    contains_personal_data: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FeedbackReview:
    status: str = "unreviewed"
    rules_version: str = ""
    validated_at: str = ""
    expected_summary: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FeedbackTurn:
    id: str
    question: str
    contract: OpenJudgeTurn | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FeedbackCase:
    schema_version: str
    id: str
    title: str
    mode: FeedbackEvaluationMode
    source: FeedbackSource
    review: FeedbackReview
    tags: tuple[str, ...]
    turns: tuple[FeedbackTurn, ...]


@dataclass(frozen=True, slots=True)
class FeedbackFinding:
    outcome: str
    message: str


@dataclass(slots=True)
class FeedbackTurnResult:
    case_id: str
    case_title: str
    turn_id: str
    turn_index: int
    question: str
    answer: str
    outcome: FeedbackOutcome
    elapsed: float
    judge_result: dict[str, Any] = field(default_factory=dict)
    conversation_snapshot: dict[str, Any] = field(default_factory=dict)
    findings: list[FeedbackFinding] = field(default_factory=list)
    exception: str = ""
    internal_log: str = ""
    failure_family: FeedbackFailureFamily = FeedbackFailureFamily.REVIEW_REQUIRED

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["outcome"] = self.outcome.value
        payload["failure_family"] = self.failure_family.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FeedbackTurnResult:
        raw_family = payload.get("failure_family")
        if raw_family is None:
            raw_family = (
                FeedbackFailureFamily.EXECUTION_ERROR.value
                if payload.get("exception")
                else FeedbackFailureFamily.REVIEW_REQUIRED.value
            )
        return cls(
            case_id=str(payload.get("case_id", "")),
            case_title=str(payload.get("case_title", "")),
            turn_id=str(payload.get("turn_id", "")),
            turn_index=int(payload.get("turn_index", 0)),
            question=str(payload.get("question", "")),
            answer=str(payload.get("answer", "")),
            outcome=FeedbackOutcome(str(payload.get("outcome", "REVIEW_REQUIRED"))),
            elapsed=float(payload.get("elapsed", 0.0)),
            judge_result=dict(payload.get("judge_result") or {}),
            conversation_snapshot=dict(payload.get("conversation_snapshot") or {}),
            findings=[
                FeedbackFinding(
                    outcome=str(item.get("outcome", "")),
                    message=str(item.get("message", "")),
                )
                for item in payload.get("findings", [])
                if isinstance(item, dict)
            ],
            exception=str(payload.get("exception", "")),
            internal_log=str(payload.get("internal_log", "")),
            failure_family=FeedbackFailureFamily(str(raw_family)),
        )


@dataclass(slots=True)
class FeedbackCaseResult:
    case: FeedbackCase
    outcome: FeedbackOutcome
    elapsed: float
    turns: list[FeedbackTurnResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": {
                "schema_version": self.case.schema_version,
                "id": self.case.id,
                "title": self.case.title,
                "mode": self.case.mode.value,
                "source": asdict(self.case.source),
                "review": asdict(self.case.review),
                "tags": list(self.case.tags),
            },
            "outcome": self.outcome.value,
            "elapsed": self.elapsed,
            "turns": [turn.to_dict() for turn in self.turns],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FeedbackCaseResult:
        raw_case = dict(payload.get("case") or {})
        raw_source = dict(raw_case.get("source") or {})
        raw_review = dict(raw_case.get("review") or {})
        turn_results = [
            FeedbackTurnResult.from_dict(item)
            for item in payload.get("turns", [])
            if isinstance(item, dict)
        ]
        case = FeedbackCase(
            schema_version=str(raw_case.get("schema_version", "1.0")),
            id=str(raw_case.get("id", "")),
            title=str(raw_case.get("title", "")),
            mode=FeedbackEvaluationMode(str(raw_case.get("mode", "exploratory"))),
            source=FeedbackSource(
                platform=str(raw_source.get("platform", "manual")),
                url=str(raw_source.get("url", "")),
                topic_id=str(raw_source.get("topic_id", "")),
                published_at=str(raw_source.get("published_at", "")),
                retrieved_at=str(raw_source.get("retrieved_at", "")),
                paraphrased=bool(raw_source.get("paraphrased", True)),
                contains_verbatim_quote=bool(
                    raw_source.get("contains_verbatim_quote", False)
                ),
                contains_personal_data=bool(
                    raw_source.get("contains_personal_data", False)
                ),
                notes=str(raw_source.get("notes", "")),
            ),
            review=FeedbackReview(
                status=str(raw_review.get("status", "unreviewed")),
                rules_version=str(raw_review.get("rules_version", "")),
                validated_at=str(raw_review.get("validated_at", "")),
                expected_summary=str(raw_review.get("expected_summary", "")),
                notes=str(raw_review.get("notes", "")),
            ),
            tags=tuple(str(item) for item in raw_case.get("tags", [])),
            turns=tuple(
                FeedbackTurn(
                    id=turn.turn_id,
                    question=turn.question,
                )
                for turn in turn_results
            ),
        )
        return cls(
            case=case,
            outcome=FeedbackOutcome(str(payload.get("outcome", "REVIEW_REQUIRED"))),
            elapsed=float(payload.get("elapsed", 0.0)),
            turns=turn_results,
        )
