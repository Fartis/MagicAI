from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any

from magicai.tactician.input_analysis import InputAnalysis
from magicai.tactician.intents import StrategyIntent
from magicai.tactician.orchestration import ResponseMode


@dataclass(frozen=True, slots=True)
class FactualCoreItem:
    """A factual proposition that must survive final-response orchestration."""

    code: str
    statement: str
    markers: tuple[tuple[str, ...], ...]
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "statement": self.statement,
            "evidence": list(self.evidence),
        }


@dataclass(slots=True)
class FactualCoreCoverage:
    required: int = 0
    covered: int = 0
    covered_codes: list[str] = field(default_factory=list)
    missing_codes: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.required == self.covered

    def to_dict(self) -> dict[str, object]:
        return {
            "required": self.required,
            "covered": self.covered,
            "covered_codes": list(self.covered_codes),
            "missing": list(self.missing_codes),
            "complete": self.complete,
        }


def extract_factual_core(
    analysis: InputAnalysis,
    *,
    judge_payload: dict[str, Any],
    cards: list[dict[str, Any]],
    response_mode: ResponseMode | None = None,
) -> list[FactualCoreItem]:
    """Extract the Judge-owned factual core without card-specific production rules.

    Judge-led turns preserve the Judge's direct, validated answer sentence by
    sentence. Strategic and hybrid turns remain governed by their answer
    obligations and semantic gauntlet assertions instead of hard-coded card
    combinations.
    """

    del cards  # The preservation policy is deliberately card-agnostic.
    if response_mode is not ResponseMode.JUDGE_LED:
        return []
    if not _judge_answer_is_directly_usable(judge_payload, analysis):
        return []

    answer = str(judge_payload.get("answer", "")).strip()
    rules = tuple(_rule_numbers(judge_payload))
    sentences = _sentences(answer) or [answer]
    return [
        FactualCoreItem(
            code=f"judge_fact_{index}",
            statement=sentence,
            markers=((_normalize(sentence),),),
            evidence=rules,
        )
        for index, sentence in enumerate(sentences, start=1)
        if sentence.strip()
    ]


def evaluate_factual_core(answer: str, core: list[FactualCoreItem]) -> FactualCoreCoverage:
    normalized = _normalize(answer)
    covered_codes: list[str] = []
    missing_codes: list[str] = []
    for item in core:
        if _item_covered(normalized, item):
            covered_codes.append(item.code)
        else:
            missing_codes.append(item.code)
    return FactualCoreCoverage(
        required=len(core),
        covered=len(covered_codes),
        covered_codes=covered_codes,
        missing_codes=missing_codes,
    )


def preserve_factual_core(
    answer: str,
    *,
    judge_answer: str,
    core: list[FactualCoreItem],
    response_mode: ResponseMode,
    judge_answer_usable: bool,
) -> tuple[str, FactualCoreCoverage, bool]:
    coverage = evaluate_factual_core(answer, core)
    if coverage.complete:
        return answer, coverage, True

    # A Judge-led response may never discard a validated Judge answer. Hybrid
    # and Tactician-led responses are not repaired by blindly prepending prose;
    # their own semantic contracts decide whether they are complete.
    if (
        response_mode is ResponseMode.JUDGE_LED
        and judge_answer_usable
        and judge_answer.strip()
    ):
        repaired = judge_answer.strip()
        repaired_coverage = evaluate_factual_core(repaired, core)
        return repaired, repaired_coverage, repaired_coverage.complete

    return answer, coverage, not core


def judge_answer_is_directly_usable(judge_payload: dict[str, Any], analysis: InputAnalysis) -> bool:
    return _judge_answer_is_directly_usable(judge_payload, analysis)


def _judge_answer_is_directly_usable(judge_payload: dict[str, Any], analysis: InputAnalysis) -> bool:
    answer = _normalize(str(judge_payload.get("answer", "")))
    if not answer or str(judge_payload.get("status", "")) != "answered":
        return False

    if analysis.language == "es" and any(
        marker in answer
        for marker in ("player loses the game", "the interaction creates value")
    ):
        return False

    if analysis.strategy_intent in {
        StrategyIntent.MECHANIC_EQUIVALENCE,
        StrategyIntent.MECHANIC_RESOLUTION,
        StrategyIntent.RULES_CLARIFICATION,
        StrategyIntent.MECHANIC_DEFINITION,
    }:
        drift = any(
            marker in answer
            for marker in (
                "jugador pierde el juego",
                "abdica por empate",
                "player loses the game",
                "concedes the game",
                "no hay evidencia suficiente para demostrar un bucle",
                "insufficient evidence to prove an infinite loop",
            )
        )
        if drift:
            return False
    return True


def _item_covered(answer: str, item: FactualCoreItem) -> bool:
    for marker_group in item.markers:
        if all(_normalize(marker) in answer for marker in marker_group):
            return True
    return False


def _sentences(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text.strip())
        if part.strip()
    ]


def _rule_numbers(payload: dict[str, Any]) -> list[str]:
    return [
        str(item.get("number", ""))
        for item in payload.get("rules", [])
        if item.get("number")
    ]


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
