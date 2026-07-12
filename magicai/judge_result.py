from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from magicai.sources.versions import get_source_versions
from magicai.validation.assumptions import derive_assumptions


class JudgeStatus(str, Enum):
    ANSWERED = "answered"
    NEEDS_CLARIFICATION = "needs_clarification"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STRATEGY_REQUIRED = "strategy_required"
    FALSE_PREMISE = "false_premise"


class JudgeOrigin(str, Enum):
    DISAMBIGUATION = "disambiguation"
    DETERMINISTIC_RULE = "deterministic_rule"
    DETERMINISTIC_ORACLE = "deterministic_oracle"
    DETERMINISTIC_RULINGS = "deterministic_rulings"
    STRATEGY_BOUNDARY = "strategy_boundary"
    LLM_VALIDATED = "llm_validated"
    SAFE_FALLBACK = "safe_fallback"
    PREMISE_GUARD = "premise_guard"


class JudgeConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class CardEvidence:
    name: str
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    scryfall_uri: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mana_cost": self.mana_cost,
            "type_line": self.type_line,
            "oracle_text": self.oracle_text,
            "scryfall_uri": self.scryfall_uri,
        }


@dataclass(frozen=True, slots=True)
class RuleEvidence:
    number: str | None = None
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class RulingEvidence:
    card_name: str | None = None
    oracle_id: str | None = None
    source: str | None = None
    published_at: str | None = None
    comment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_name": self.card_name,
            "oracle_id": self.oracle_id,
            "source": self.source,
            "published_at": self.published_at,
            "comment": self.comment,
        }


@dataclass(slots=True)
class JudgeResult:
    question: str
    answer: str
    status: JudgeStatus
    origin: JudgeOrigin
    confidence: JudgeConfidence
    authority: str = "judge"
    intent: str = ""
    cards: list[CardEvidence] = field(default_factory=list)
    rules: list[RuleEvidence] = field(default_factory=list)
    rulings: list[RulingEvidence] = field(default_factory=list)
    retrieval_queries: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_versions: dict[str, str] = field(default_factory=dict)
    validation_attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "status": self.status.value,
            "origin": self.origin.value,
            "confidence": self.confidence.value,
            "authority": self.authority,
            "intent": self.intent,
            "cards": [card.to_dict() for card in self.cards],
            "rules": [rule.to_dict() for rule in self.rules],
            "rulings": [ruling.to_dict() for ruling in self.rulings],
            "retrieval_queries": list(self.retrieval_queries),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "source_versions": dict(self.source_versions),
            "validation_attempts": self.validation_attempts,
        }


def build_judge_result(
    *,
    question: str,
    answer: str,
    status: JudgeStatus,
    origin: JudgeOrigin,
    confidence: JudgeConfidence,
    context: Any | None = None,
    assumptions: list[str] | None = None,
    warnings: list[str] | None = None,
    validation_attempts: int = 0,
) -> JudgeResult:
    return JudgeResult(
        question=question,
        answer=answer,
        status=status,
        origin=origin,
        confidence=confidence,
        intent=str(getattr(context, "intent", "") or ""),
        cards=_card_evidence(getattr(context, "cards", [])),
        rules=_rule_evidence(getattr(context, "rules", [])),
        rulings=_ruling_evidence(getattr(context, "rulings", [])),
        retrieval_queries=[
            str(query)
            for query in getattr(context, "rule_queries", [])
            if query
        ],
        assumptions=_merge_unique(
            list(assumptions or []),
            derive_assumptions(
                question=question,
                answer=answer,
                context=context,
            ),
        ),
        warnings=list(warnings or []),
        source_versions=get_source_versions(),
        validation_attempts=validation_attempts,
    )


def build_clarification_result(
    *,
    question: str,
    answer: str,
    candidates: list[str],
) -> JudgeResult:
    return JudgeResult(
        question=question,
        answer=answer,
        status=JudgeStatus.NEEDS_CLARIFICATION,
        origin=JudgeOrigin.DISAMBIGUATION,
        confidence=JudgeConfidence.HIGH,
        cards=[CardEvidence(name=name) for name in candidates],
        warnings=["Multiple supported cards match the current reference."],
        source_versions=get_source_versions(),
    )


def _card_evidence(cards: list[Any]) -> list[CardEvidence]:
    evidence: list[CardEvidence] = []

    for card in cards:
        if isinstance(card, dict):
            getter = card.get
        else:
            getter = lambda name, default=None, item=card: getattr(item, name, default)

        name = getter("name")
        if not name:
            continue

        evidence.append(
            CardEvidence(
                name=str(name),
                mana_cost=_optional_string(getter("mana_cost")),
                type_line=_optional_string(getter("type_line")),
                oracle_text=_optional_string(getter("oracle_text")),
                scryfall_uri=_optional_string(getter("scryfall_uri")),
            )
        )

    return evidence


def _rule_evidence(rules: list[Any]) -> list[RuleEvidence]:
    evidence: list[RuleEvidence] = []
    seen: set[tuple[str | None, str | None]] = set()

    for rule in rules:
        if isinstance(rule, str):
            number = rule
            title = None
        elif isinstance(rule, dict):
            number = _optional_string(rule.get("number"))
            title = _optional_string(rule.get("title"))
        else:
            number = _optional_string(getattr(rule, "number", None))
            title = _optional_string(getattr(rule, "title", None))

        key = (number, title)
        if key == (None, None) or key in seen:
            continue

        seen.add(key)
        evidence.append(RuleEvidence(number=number, title=title))

    return evidence


def _ruling_evidence(rulings: list[Any]) -> list[RulingEvidence]:
    evidence: list[RulingEvidence] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()

    for ruling in rulings:
        if isinstance(ruling, dict):
            getter = ruling.get
        else:
            getter = lambda name, default=None, item=ruling: getattr(item, name, default)

        oracle_id = _optional_string(getter("oracle_id"))
        published_at = _optional_string(getter("published_at"))
        comment = _optional_string(getter("comment"))
        key = (oracle_id, published_at, comment)

        if comment is None or key in seen:
            continue

        seen.add(key)
        evidence.append(
            RulingEvidence(
                card_name=_optional_string(getter("card_name")),
                oracle_id=oracle_id,
                source=_optional_string(getter("source")),
                published_at=published_at,
                comment=comment,
            )
        )

    return evidence


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    for item in primary + secondary:
        if item and item not in merged:
            merged.append(item)
    return merged


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None
