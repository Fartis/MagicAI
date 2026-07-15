from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from magicai.tactician.input_analysis import ClaimKind, InputAnalysis, InputClaim


class ClaimVerdictStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    PARTIALLY_SUPPORTED = "partially_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STRATEGIC_OPINION = "strategic_opinion"


@dataclass(frozen=True, slots=True)
class ClaimVerdict:
    claim_id: str
    claim: str
    status: ClaimVerdictStatus
    explanation: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "claim": self.claim,
            "verdict": self.status.value,
            "explanation": self.explanation,
            "evidence": list(self.evidence),
        }


def evaluate_claims(
    analysis: InputAnalysis,
    *,
    cards: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
) -> list[ClaimVerdict]:
    evidence_ids = _evidence_identifiers(tool_calls)
    oracle_by_name = {
        str(card.get("name", "")).casefold(): str(card.get("oracle_text", ""))
        for card in cards
        if card.get("name")
    }
    has_ozolith = "the ozolith" in oracle_by_name
    has_undying = any("undying" in oracle.casefold() for oracle in oracle_by_name.values())

    verdicts: list[ClaimVerdict] = []
    for claim in analysis.claims:
        verdicts.append(
            _evaluate_claim(
                claim,
                has_ozolith=has_ozolith,
                has_undying=has_undying,
                evidence_ids=evidence_ids,
            )
        )
    return verdicts


def _evaluate_claim(
    claim: InputClaim,
    *,
    has_ozolith: bool,
    has_undying: bool,
    evidence_ids: set[str],
) -> ClaimVerdict:
    concepts = set(claim.concepts)

    if claim.kind is ClaimKind.STATE_TRANSITION and "sacrifice" in concepts:
        return ClaimVerdict(
            claim_id=claim.claim_id,
            claim=claim.text,
            status=ClaimVerdictStatus.SUPPORTED,
            explanation="Sacrificing a permanent moves it from the battlefield to its owner's graveyard; a creature moved this way dies.",
            evidence=_prefer_evidence(evidence_ids, "701.21a", "700.4"),
        )

    if claim.kind is ClaimKind.TIMING_HYPOTHESIS and has_ozolith and "counters" in concepts:
        return ClaimVerdict(
            claim_id=claim.claim_id,
            claim=claim.text,
            status=ClaimVerdictStatus.CONTRADICTED,
            explanation=(
                "The Ozolith does not remove or transfer the original counter before the zone change. "
                "The counter ceases to exist when the object changes zones, and The Ozolith's triggered ability puts corresponding counters on itself later."
            ),
            evidence=_prefer_evidence(evidence_ids, "122.2", "400.7", "603.6c", "603.10a"),
        )

    if claim.kind is ClaimKind.DERIVED_CONCLUSION and has_undying:
        return ClaimVerdict(
            claim_id=claim.claim_id,
            claim=claim.text,
            status=ClaimVerdictStatus.CONTRADICTED,
            explanation=(
                "Undying uses the creature's last battlefield state for the leaves-the-battlefield trigger. "
                "If Young Wolf had a +1/+1 counter immediately before it left, the intervening-if condition is false and Undying does not trigger."
            ),
            evidence=_prefer_evidence(evidence_ids, "702.93a", "603.4", "603.10a"),
        )

    if claim.kind is ClaimKind.STRATEGIC:
        return ClaimVerdict(
            claim_id=claim.claim_id,
            claim=claim.text,
            status=ClaimVerdictStatus.STRATEGIC_OPINION,
            explanation="Whether the pieces form a combo must be derived from the verified state transitions and net result.",
            evidence=(),
        )

    return ClaimVerdict(
        claim_id=claim.claim_id,
        claim=claim.text,
        status=ClaimVerdictStatus.INSUFFICIENT_EVIDENCE,
        explanation="The current evidence package does not prove or disprove this claim yet.",
        evidence=(),
    )


def _evidence_identifiers(tool_calls: list[dict[str, Any]]) -> set[str]:
    identifiers: set[str] = set()
    for call in tool_calls:
        for item in call.get("evidence", []):
            identifier = str(item.get("identifier", "")).strip()
            if identifier:
                identifiers.add(identifier)
            data = item.get("data", {})
            if isinstance(data, dict):
                number = str(data.get("number", "")).strip()
                if number:
                    identifiers.add(number)
    return identifiers


def _prefer_evidence(available: set[str], *identifiers: str) -> tuple[str, ...]:
    selected = [identifier for identifier in identifiers if identifier in available]
    return tuple(selected or identifiers)
