from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from magicai.judge_tools import (
    JudgeToolBudget,
    JudgeToolRequest,
    JudgeToolResult,
    JudgeToolStatus,
)
from magicai.tactician.input_analysis import ClaimKind, InputAnalysis, SpeechAct
from magicai.tactician.intents import StrategyIntent


class HypothesisStatus(str, Enum):
    OPEN = "open"
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"


@dataclass(slots=True)
class InvestigationHypothesis:
    hypothesis_id: str
    statement: str
    kind: str
    concepts: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    search_queries: tuple[str, ...] = ()
    status: HypothesisStatus = HypothesisStatus.OPEN
    sufficiency_score: float = 0.0
    resolved_evidence: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    follow_up_attempted: bool = False

    def evaluate(self, available_evidence: set[str]) -> None:
        required = tuple(_normalize_token(item) for item in self.required_evidence if item)
        if not required:
            self.sufficiency_score = 1.0
            self.status = HypothesisStatus.SUFFICIENT
            self.resolved_evidence = ()
            self.missing_evidence = ()
            return

        resolved = tuple(item for item in required if item in available_evidence)
        missing = tuple(item for item in required if item not in available_evidence)
        self.resolved_evidence = resolved
        self.missing_evidence = missing
        self.sufficiency_score = round(len(resolved) / len(required), 3)
        self.status = (
            HypothesisStatus.SUFFICIENT
            if not missing
            else HypothesisStatus.INSUFFICIENT
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.hypothesis_id,
            "statement": self.statement,
            "kind": self.kind,
            "concepts": list(self.concepts),
            "required_evidence": list(self.required_evidence),
            "search_queries": list(self.search_queries),
            "status": self.status.value,
            "sufficiency_score": self.sufficiency_score,
            "resolved_evidence": list(self.resolved_evidence),
            "missing_evidence": list(self.missing_evidence),
            "follow_up_attempted": self.follow_up_attempted,
        }


@dataclass(slots=True)
class InvestigationStep:
    sequence: int
    phase: str
    request: JudgeToolRequest
    status: str
    evidence_count: int
    hypothesis_ids: tuple[str, ...] = ()
    sufficiency_before: float = 0.0
    sufficiency_after: float = 0.0
    cache_hit: bool = False
    error_code: str = ""
    budget: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "phase": self.phase,
            "hypothesis_ids": list(self.hypothesis_ids),
            "request": self.request.to_dict(),
            "status": self.status,
            "evidence_count": self.evidence_count,
            "sufficiency_before": self.sufficiency_before,
            "sufficiency_after": self.sufficiency_after,
            "cache_hit": self.cache_hit,
            "error_code": self.error_code,
            "budget": dict(self.budget),
        }


@dataclass(slots=True)
class InvestigationOutcome:
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[InvestigationHypothesis] = field(default_factory=list)
    steps: list[InvestigationStep] = field(default_factory=list)
    sufficiency_score: float = 0.0
    sufficient: bool = False
    stopped_reason: str = "not_started"
    initial_queries: int = 0
    follow_up_queries: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "sufficient": self.sufficient,
            "sufficiency_score": self.sufficiency_score,
            "stopped_reason": self.stopped_reason,
            "initial_queries": self.initial_queries,
            "follow_up_queries": self.follow_up_queries,
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "steps": [item.to_dict() for item in self.steps],
        }


JudgeToolExecutor = Callable[..., JudgeToolResult]


def build_hypotheses(
    analysis: InputAnalysis,
    *,
    cards: list[dict[str, Any]],
) -> list[InvestigationHypothesis]:
    hypotheses: list[InvestigationHypothesis] = []
    card_names = [str(card.get("name", "")).strip() for card in cards if card.get("name")]

    for claim in analysis.claims:
        required, queries = _claim_requirements(claim.kind, claim.concepts, card_names)
        hypotheses.append(
            InvestigationHypothesis(
                hypothesis_id=f"hypothesis-{len(hypotheses) + 1}",
                statement=claim.text,
                kind=claim.kind.value,
                concepts=claim.concepts,
                required_evidence=required,
                search_queries=queries,
            )
        )

    if card_names and not any(
        any(token.startswith("card:") for token in item.required_evidence)
        for item in hypotheses
    ):
        hypotheses.insert(
            0,
            InvestigationHypothesis(
                hypothesis_id="hypothesis-1",
                statement=(
                    "El análisis usa el texto Oracle actual de todas las cartas implicadas."
                    if analysis.language == "es"
                    else "The analysis uses current Oracle text for every referenced card."
                ),
                kind="oracle_foundation",
                concepts=("oracle",),
                required_evidence=tuple(f"card:{name}" for name in card_names),
                search_queries=tuple(card_names),
            ),
        )
        _renumber_hypotheses(hypotheses)

    intent_required, intent_queries = _intent_requirements(analysis, cards)
    covered = {
        _normalize_token(token)
        for hypothesis in hypotheses
        for token in hypothesis.required_evidence
    }
    uncovered = tuple(
        token for token in intent_required
        if _normalize_token(token) not in covered
    )
    if uncovered or not hypotheses:
        hypotheses.append(
            InvestigationHypothesis(
                hypothesis_id=f"hypothesis-{len(hypotheses) + 1}",
                statement=(
                    "La base factual necesaria para responder está respaldada por evidencia del Juez."
                    if analysis.language == "es"
                    else "The factual basis needed for the answer is backed by Judge-owned evidence."
                ),
                kind="answer_basis",
                concepts=tuple(analysis.concepts),
                required_evidence=uncovered or intent_required,
                search_queries=intent_queries,
            )
        )

    return hypotheses


def run_investigation(
    *,
    analysis: InputAnalysis,
    requests: list[JudgeToolRequest],
    hypotheses: list[InvestigationHypothesis],
    execute: JudgeToolExecutor,
    conversation,
    budget: JudgeToolBudget,
) -> InvestigationOutcome:
    outcome = InvestigationOutcome(
        hypotheses=hypotheses,
        initial_queries=len(requests),
    )
    available_evidence: set[str] = set()
    _evaluate_hypotheses(outcome.hypotheses, available_evidence)

    for request in requests:
        if not _execute_step(
            outcome,
            request=request,
            phase="initial_evidence",
            hypothesis_ids=_related_hypotheses(request, outcome.hypotheses),
            execute=execute,
            conversation=conversation,
            budget=budget,
            available_evidence=available_evidence,
        ):
            outcome.stopped_reason = "budget_exceeded"
            _finalize_outcome(outcome)
            return outcome

    while True:
        _finalize_outcome(outcome)
        if outcome.sufficient:
            outcome.stopped_reason = "evidence_sufficient"
            return outcome

        candidate = _next_follow_up(analysis, outcome.hypotheses)
        if candidate is None:
            outcome.stopped_reason = "no_follow_up_available"
            return outcome

        hypothesis, request, phase = candidate
        hypothesis.follow_up_attempted = True
        outcome.follow_up_queries += 1
        if not _execute_step(
            outcome,
            request=request,
            phase=phase,
            hypothesis_ids=(hypothesis.hypothesis_id,),
            execute=execute,
            conversation=conversation,
            budget=budget,
            available_evidence=available_evidence,
        ):
            outcome.stopped_reason = "budget_exceeded"
            _finalize_outcome(outcome)
            return outcome


def evidence_tokens_from_calls(tool_calls: list[dict[str, Any]]) -> set[str]:
    tokens: set[str] = set()
    for call in tool_calls:
        for item in call.get("evidence", []):
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind", "")).strip().casefold()
            data = item.get("data", {})
            if not isinstance(data, dict):
                data = {}
            identifier = str(item.get("identifier", "")).strip()
            if kind == "rule":
                number = str(data.get("number", identifier)).strip()
                if number:
                    tokens.add(_normalize_token(f"rule:{number}"))
            elif kind == "card":
                name = str(data.get("name", identifier)).strip()
                if name:
                    tokens.add(_normalize_token(f"card:{name}"))
            elif kind == "ruling":
                card_name = str(data.get("card_name", "")).strip()
                oracle_id = str(data.get("oracle_id", "")).strip()
                if card_name:
                    tokens.add(_normalize_token(f"ruling:{card_name}"))
                if oracle_id:
                    tokens.add(_normalize_token(f"ruling_oracle:{oracle_id}"))
            if kind in {"rule", "card", "ruling"}:
                tokens.add("evidence:authoritative")
    return tokens


def _execute_step(
    outcome: InvestigationOutcome,
    *,
    request: JudgeToolRequest,
    phase: str,
    hypothesis_ids: tuple[str, ...],
    execute: JudgeToolExecutor,
    conversation,
    budget: JudgeToolBudget,
    available_evidence: set[str],
) -> bool:
    before = _overall_score(outcome.hypotheses)
    result = execute(request, conversation=conversation, budget=budget)
    payload = result.to_dict()
    outcome.tool_calls.append(payload)
    available_evidence.update(evidence_tokens_from_calls([payload]))
    _evaluate_hypotheses(outcome.hypotheses, available_evidence)
    after = _overall_score(outcome.hypotheses)
    outcome.steps.append(
        InvestigationStep(
            sequence=len(outcome.steps) + 1,
            phase=phase,
            request=request,
            status=str(payload.get("status", "")),
            evidence_count=len(payload.get("evidence", [])),
            hypothesis_ids=hypothesis_ids,
            sufficiency_before=before,
            sufficiency_after=after,
            cache_hit=bool(payload.get("cache_hit", False)),
            error_code=str(payload.get("error_code", "")),
            budget=dict(payload.get("budget", {})),
        )
    )
    return result.status is not JudgeToolStatus.BUDGET_EXCEEDED


def _next_follow_up(
    analysis: InputAnalysis,
    hypotheses: list[InvestigationHypothesis],
) -> tuple[InvestigationHypothesis, JudgeToolRequest, str] | None:
    phase = (
        "counterexample_search"
        if analysis.asks_for_validation
        or analysis.speech_act in {SpeechAct.HYPOTHESIS, SpeechAct.CHALLENGE}
        else "alternative_search"
    )
    for hypothesis in hypotheses:
        if hypothesis.status is HypothesisStatus.SUFFICIENT or hypothesis.follow_up_attempted:
            continue
        if not hypothesis.search_queries:
            continue

        missing_rules = [
            token.split(":", 1)[1]
            for token in hypothesis.missing_evidence
            if token.startswith("rule:")
        ]
        if missing_rules:
            return (
                hypothesis,
                JudgeToolRequest(
                    tool="rules_search",
                    arguments={"query": hypothesis.search_queries[0], "limit": 8},
                    purpose=f"resolve_{hypothesis.hypothesis_id}",
                    request_id=f"{hypothesis.hypothesis_id}-rules-search",
                    result_limit=8,
                ),
                phase,
            )

        missing_cards = [
            token.split(":", 1)[1]
            for token in hypothesis.missing_evidence
            if token.startswith("card:")
        ]
        if missing_cards:
            return (
                hypothesis,
                JudgeToolRequest(
                    tool="oracle_search",
                    arguments={"query": missing_cards[0], "limit": 8},
                    purpose=f"resolve_{hypothesis.hypothesis_id}",
                    request_id=f"{hypothesis.hypothesis_id}-oracle-search",
                    result_limit=8,
                ),
                phase,
            )
    return None


def _related_hypotheses(
    request: JudgeToolRequest,
    hypotheses: list[InvestigationHypothesis],
) -> tuple[str, ...]:
    if request.tool == "oracle_lookup":
        prefix = "card:"
    elif request.tool in {"rules_lookup", "rules_search"}:
        prefix = "rule:"
    elif request.tool == "rulings_lookup":
        related = [
            item.hypothesis_id
            for item in hypotheses
            if "ozolith" in item.concepts or item.kind == ClaimKind.TIMING_HYPOTHESIS.value
        ]
        return tuple(related)
    else:
        return tuple(item.hypothesis_id for item in hypotheses)
    related = [
        item.hypothesis_id
        for item in hypotheses
        if any(token.startswith(prefix) for token in item.required_evidence)
    ]
    return tuple(related)


def _claim_requirements(
    kind: ClaimKind,
    concepts: tuple[str, ...],
    card_names: list[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    concept_set = set(concepts)
    if kind is ClaimKind.MECHANIC_EQUIVALENCE:
        return (
            ("rule:700.4", "rule:702.93a"),
            ("dies put into a graveyard from the battlefield undying",),
        )
    if kind is ClaimKind.STATE_TRANSITION:
        return (
            ("rule:701.21a", "rule:700.4"),
            ("sacrifice permanent creature dies graveyard",),
        )
    if kind is ClaimKind.TIMING_HYPOTHESIS:
        required = ["rule:122.2", "rule:400.7", "rule:603.6c", "rule:603.10a"]
        if any(name.casefold() == "the ozolith" for name in card_names):
            required.append("card:The Ozolith")
        return (
            tuple(required),
            ("counters cease to exist zone change leaves battlefield triggered ability",),
        )
    if kind is ClaimKind.DERIVED_CONCLUSION:
        return (
            ("rule:702.93a", "rule:603.4"),
            ("undying intervening if last known information",),
        )
    if kind is ClaimKind.STRATEGIC:
        required = tuple(f"card:{name}" for name in card_names)
        return (
            required or ("context:active_interaction",),
            tuple(card_names),
        )

    required: list[str] = []
    if "sacrifice" in concept_set:
        required.extend(["rule:701.21a", "rule:700.4"])
    if "undying" in concept_set:
        required.extend(["rule:702.93a", "rule:603.4"])
    if "counters" in concept_set:
        required.extend(["rule:122.2", "rule:400.7"])
    resolved_requirements = tuple(_deduplicate(required))
    return (
        resolved_requirements or ("evidence:authoritative",),
        (" ".join(concepts),) if concepts else (),
    )


def _intent_requirements(
    analysis: InputAnalysis,
    cards: list[dict[str, Any]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    card_names = [str(card.get("name", "")).strip() for card in cards if card.get("name")]
    oracle_text = " ".join(str(card.get("oracle_text", "")) for card in cards).casefold()
    required = [f"card:{name}" for name in card_names]
    concepts = set(analysis.concepts)
    derive_card_mechanics = analysis.strategy_intent in {
        StrategyIntent.COMBO_DETECTION,
        StrategyIntent.SYNERGY_ANALYSIS,
        StrategyIntent.INTERACTION_HYPOTHESIS,
        StrategyIntent.COMBO_FAILURE_EXPLANATION,
        StrategyIntent.INTERACTION_TIMING,
        StrategyIntent.PLAY_SEQUENCE,
        StrategyIntent.COMBO_DISRUPTION,
        StrategyIntent.COMBO_REQUIREMENTS,
    }
    if "sacrifice" in concepts or (derive_card_mechanics and "sacrifice" in oracle_text):
        required.extend(["rule:701.21a", "rule:700.4"])
    if "undying" in concepts or (derive_card_mechanics and "undying" in oracle_text):
        required.extend(["rule:702.93a", "rule:603.4"])
    if "ozolith" in concepts or "counters" in concepts:
        required.extend(["rule:122.2", "rule:400.7", "rule:603.6c", "rule:603.10a"])
    if (
        {"land_types", "basic_lands", "nonbasic_lands", "mana_abilities"} & concepts
        and {"layers", "dependency", "timestamp"} & concepts
    ):
        required.extend([
            "rule:305.6",
            "rule:305.7",
            "rule:305.8",
            "rule:611.3",
            "rule:613.1d",
            "rule:613.7",
            "rule:613.8a",
            "rule:613.8b",
        ])
    query_parts = list(analysis.concepts)
    if derive_card_mechanics and "sacrifice" in oracle_text and "sacrifice" not in query_parts:
        query_parts.append("sacrifice")
    if derive_card_mechanics and "undying" in oracle_text and "undying" not in query_parts:
        query_parts.append("undying")
    if (
        {"land_types", "basic_lands", "nonbasic_lands", "mana_abilities"} & concepts
        and {"layers", "dependency", "timestamp"} & concepts
    ):
        query_parts.extend([
            "basic land types",
            "intrinsic mana abilities",
            "timestamp dependency layer 4",
        ])
    query = " ".join(_deduplicate(query_parts)) or analysis.canonical_text
    return tuple(_deduplicate(required)), ((query,) if query else ())


def _evaluate_hypotheses(
    hypotheses: list[InvestigationHypothesis],
    available_evidence: set[str],
) -> None:
    for hypothesis in hypotheses:
        hypothesis.evaluate(available_evidence)


def _finalize_outcome(outcome: InvestigationOutcome) -> None:
    outcome.sufficiency_score = _overall_score(outcome.hypotheses)
    outcome.sufficient = bool(outcome.hypotheses) and all(
        item.status is HypothesisStatus.SUFFICIENT
        for item in outcome.hypotheses
    )


def _overall_score(hypotheses: list[InvestigationHypothesis]) -> float:
    if not hypotheses:
        return 0.0
    return round(sum(item.sufficiency_score for item in hypotheses) / len(hypotheses), 3)


def _normalize_token(token: str) -> str:
    prefix, separator, value = str(token).partition(":")
    if not separator:
        return str(token).strip().casefold()
    return f"{prefix.strip().casefold()}:{value.strip().casefold()}"


def _renumber_hypotheses(hypotheses: list[InvestigationHypothesis]) -> None:
    for index, hypothesis in enumerate(hypotheses, start=1):
        hypothesis.hypothesis_id = f"hypothesis-{index}"


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = str(item).casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
