from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from magicai.versioning import TACTICIAN_RESULT_SCHEMA_VERSION


class TacticianReviewStatus(str, Enum):
    ACCEPTED = "accepted"
    CHALLENGED = "challenged"
    REPAIRED = "repaired"


@dataclass(frozen=True, slots=True)
class JudgeChallenge:
    code: str
    message: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "evidence": list(self.evidence),
        }


@dataclass(slots=True)
class TacticianReview:
    status: TacticianReviewStatus
    challenges: list[JudgeChallenge] = field(default_factory=list)
    repaired_answer: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status in {
            TacticianReviewStatus.ACCEPTED,
            TacticianReviewStatus.REPAIRED,
        }

    def violation_messages(self) -> list[str]:
        return [challenge.message for challenge in self.challenges]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "challenges": [challenge.to_dict() for challenge in self.challenges],
            "repaired_answer": self.repaired_answer,
        }


@dataclass(slots=True)
class TacticianResult:
    question: str
    answer: str
    status: str = "answered"
    origin: str = "tactician_strategy"
    confidence: str = "medium"
    authority: str = "tactician"
    cards: list[dict[str, Any]] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)
    rulings: list[dict[str, Any]] = field(default_factory=list)
    retrieval_queries: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    synergies: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    authority_trace: list[str] = field(default_factory=list)
    judge_result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": TACTICIAN_RESULT_SCHEMA_VERSION,
            "question": self.question,
            "answer": self.answer,
            "status": self.status,
            "origin": self.origin,
            "confidence": self.confidence,
            "authority": self.authority,
            "intent": "strategy",
            "cards": list(self.cards),
            "rules": list(self.rules),
            "rulings": list(self.rulings),
            "retrieval_queries": list(self.retrieval_queries),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "source_versions": dict(self.judge_result.get("source_versions", {})),
            "source_health": dict(self.judge_result.get("source_health", {})),
            "validation_attempts": int(self.judge_result.get("validation_attempts", 0)),
            "llm_called": False,
            "timings": {},
            "synergies": list(self.synergies),
            "risks": list(self.risks),
            "authority_trace": list(self.authority_trace),
            "judge_result": dict(self.judge_result),
        }
