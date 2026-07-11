from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OpenJudgeOutcome(str, Enum):
    """Semantic result of one conversational turn."""

    PASS = "PASS"
    CORRECT_BUT_INCOMPLETE = "CORRECT_BUT_INCOMPLETE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FALSE_PREMISE_HANDLED = "FALSE_PREMISE_HANDLED"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    CONTEXT_FAILURE = "CONTEXT_FAILURE"
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    HALLUCINATION = "HALLUCINATION"
    EXECUTION_ERROR = "EXECUTION_ERROR"


OUTCOME_SEVERITY: dict[OpenJudgeOutcome, int] = {
    OpenJudgeOutcome.PASS: 0,
    OpenJudgeOutcome.FALSE_PREMISE_HANDLED: 0,
    OpenJudgeOutcome.CORRECT_BUT_INCOMPLETE: 1,
    OpenJudgeOutcome.NEEDS_CLARIFICATION: 1,
    OpenJudgeOutcome.INSUFFICIENT_EVIDENCE: 2,
    OpenJudgeOutcome.RETRIEVAL_FAILURE: 3,
    OpenJudgeOutcome.CONTEXT_FAILURE: 4,
    OpenJudgeOutcome.FACTUAL_CONTRADICTION: 5,
    OpenJudgeOutcome.HALLUCINATION: 6,
    OpenJudgeOutcome.EXECUTION_ERROR: 7,
}


@dataclass(frozen=True)
class ForbiddenClaim:
    text: str
    outcome: OpenJudgeOutcome = OpenJudgeOutcome.FACTUAL_CONTRADICTION


@dataclass(frozen=True)
class OpenJudgeTurn:
    id: str
    question: str
    required_all: tuple[str, ...] = ()
    required_any: tuple[tuple[str, ...], ...] = ()
    recommended_all: tuple[str, ...] = ()
    recommended_any: tuple[tuple[str, ...], ...] = ()
    forbidden: tuple[ForbiddenClaim, ...] = ()
    expected_cards: tuple[str, ...] = ()
    forbidden_cards: tuple[str, ...] = ()
    missing_outcome: OpenJudgeOutcome = OpenJudgeOutcome.RETRIEVAL_FAILURE
    success_outcome: OpenJudgeOutcome = OpenJudgeOutcome.PASS
    notes: str = ""


@dataclass(frozen=True)
class OpenJudgeCase:
    id: str
    name: str
    tags: tuple[str, ...]
    turns: tuple[OpenJudgeTurn, ...]


@dataclass(frozen=True)
class ConversationSnapshot:
    cards: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    intent: str = ""
    history_size: int = 0


@dataclass(frozen=True)
class EvaluationFinding:
    outcome: OpenJudgeOutcome
    message: str


@dataclass
class OpenJudgeTurnResult:
    case_id: str
    case_name: str
    turn_id: str
    turn_index: int
    question: str
    answer: str
    outcome: OpenJudgeOutcome
    elapsed: float
    findings: list[EvaluationFinding] = field(default_factory=list)
    snapshot: ConversationSnapshot = field(default_factory=ConversationSnapshot)
    exception: str = ""
    internal_log: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["outcome"] = self.outcome.value
        payload["findings"] = [
            {
                "outcome": finding.outcome.value,
                "message": finding.message,
            }
            for finding in self.findings
        ]
        return payload


@dataclass
class OpenJudgeCaseResult:
    id: str
    name: str
    tags: tuple[str, ...]
    outcome: OpenJudgeOutcome
    elapsed: float
    turns: list[OpenJudgeTurnResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tags": list(self.tags),
            "outcome": self.outcome.value,
            "elapsed": self.elapsed,
            "turns": [turn.to_dict() for turn in self.turns],
        }
