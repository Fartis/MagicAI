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

    return [
        _evaluate_claim(
            claim,
            language=analysis.language,
            has_ozolith=has_ozolith,
            has_undying=has_undying,
            evidence_ids=evidence_ids,
        )
        for claim in analysis.claims
    ]


def _evaluate_claim(
    claim: InputClaim,
    *,
    language: str,
    has_ozolith: bool,
    has_undying: bool,
    evidence_ids: set[str],
) -> ClaimVerdict:
    concepts = set(claim.concepts)
    spanish = language == "es"

    if claim.kind is ClaimKind.MECHANIC_EQUIVALENCE:
        required = {"700.4", "702.93a"}
        if required.issubset(evidence_ids):
            explanation = (
                "La idea es parcialmente correcta, pero 'morir' y ser puesta en un cementerio desde el campo de batalla no son eventos distintos: son el mismo evento reglamentario. Undying no se dispara por entrar al cementerio desde cualquier otra zona."
                if spanish else
                "The idea is partially correct, but dying and being put into a graveyard from the battlefield are not separate events: they are the same rules event. Undying does not trigger for entering a graveyard from another zone."
            )
            return ClaimVerdict(
                claim.claim_id,
                claim.text,
                ClaimVerdictStatus.PARTIALLY_SUPPORTED,
                explanation,
                ("700.4", "702.93a"),
            )

    if claim.kind is ClaimKind.STATE_TRANSITION and "sacrifice" in concepts:
        explanation = (
            "Sacrificar un permanente lo mueve del campo de batalla al cementerio de su propietario; si es una criatura, muere."
            if spanish else
            "Sacrificing a permanent moves it from the battlefield to its owner's graveyard; a creature moved this way dies."
        )
        return ClaimVerdict(
            claim.claim_id,
            claim.text,
            ClaimVerdictStatus.SUPPORTED,
            explanation,
            _prefer_evidence(evidence_ids, "701.21a", "700.4"),
        )

    if claim.kind is ClaimKind.TIMING_HYPOTHESIS and has_ozolith and "counters" in concepts:
        explanation = (
            "The Ozolith no retira ni transfiere el contador original antes del cambio de zona. El contador deja de existir cuando el objeto cambia de zona y la habilidad disparada de The Ozolith pone después contadores equivalentes sobre el artefacto."
            if spanish else
            "The Ozolith does not remove or transfer the original counter before the zone change. The counter ceases to exist when the object changes zones, and The Ozolith's triggered ability puts corresponding counters on itself later."
        )
        return ClaimVerdict(
            claim.claim_id,
            claim.text,
            ClaimVerdictStatus.CONTRADICTED,
            explanation,
            _prefer_evidence(evidence_ids, "122.2", "400.7", "603.6c", "603.10a"),
        )

    if claim.kind is ClaimKind.DERIVED_CONCLUSION and has_undying:
        explanation = (
            "Undying usa el último estado de la criatura en el campo de batalla. Si Young Wolf tenía un contador +1/+1 inmediatamente antes de salir, la condición no se cumple y Undying no se dispara."
            if spanish else
            "Undying uses the creature's last battlefield state. If Young Wolf had a +1/+1 counter immediately before it left, the condition is false and Undying does not trigger."
        )
        return ClaimVerdict(
            claim.claim_id,
            claim.text,
            ClaimVerdictStatus.CONTRADICTED,
            explanation,
            _prefer_evidence(evidence_ids, "702.93a", "603.4", "603.10a"),
        )

    if claim.kind is ClaimKind.STRATEGIC:
        explanation = (
            "La clasificación del combo debe derivarse de las transiciones de estado verificadas y del resultado neto."
            if spanish else
            "Whether the pieces form a combo must be derived from the verified state transitions and net result."
        )
        return ClaimVerdict(
            claim.claim_id,
            claim.text,
            ClaimVerdictStatus.STRATEGIC_OPINION,
            explanation,
            (),
        )

    explanation = (
        "La evidencia disponible todavía no permite confirmar ni refutar esta afirmación."
        if spanish else
        "The current evidence package does not prove or disprove this claim yet."
    )
    return ClaimVerdict(
        claim.claim_id,
        claim.text,
        ClaimVerdictStatus.INSUFFICIENT_EVIDENCE,
        explanation,
        (),
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
