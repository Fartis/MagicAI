from __future__ import annotations

import re
import unicodedata

from .models import (
    OUTCOME_SEVERITY,
    ConversationSnapshot,
    EvaluationFinding,
    OpenJudgeOutcome,
    OpenJudgeTurn,
)


INSUFFICIENT_EVIDENCE_MARKERS: tuple[str, ...] = (
    "no hay suficiente información",
    "no hay suficiente informacion",
    "información insuficiente",
    "informacion insuficiente",
    "no es suficiente para responder",
    "no puedo responder con seguridad",
    "no he podido generar",
    "no es posible determinar",
    "no se puede determinar",
    "no hay suficiente contexto",
    "no hay suficiente evidencia",
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    text = text.replace("*", "").replace("_", "").replace("`", "")
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return _canonicalize_semantic_variants(text)


def _canonicalize_semantic_variants(text: str) -> str:
    """Collapse harmless wording variants without trying to judge new facts."""

    replacements = (
        # Official Spanish uses "robar", but archived model runs may use the
        # literal translation "dibujar" while expressing the same fact.
        (r"\b(?:roba|robar|robas|robo|dibuja|dibujar|dibujas|dibujo)\b", "roba"),
        (r"\b(?:haste|prisa)\b", "prisa"),
        (r"\b(?:vuelve|volver|regresa|regresar|retorna|retornar)\b", "vuelve"),
        (
            r"\b(?:tiene|tenia|tenga|teniendo|tuviera|tuviese|tuvo)\b",
            "tiene",
        ),
        (
            r"\b(?:se\s+)?(?:activa|activar|activan|activara|activaras|"
            r"dispara|disparar|disparan|disparara|dispararas)\b",
            "activa",
        ),
    )

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return re.sub(r"\s+", " ", text).strip()


def contains_term(text: str, term: str) -> bool:
    normalized_text = normalize(text)
    normalized_term = normalize(term)

    if not normalized_term:
        return False

    return normalized_term in normalized_text


def contains_claim(text: str, claim: str) -> bool:
    normalized_text = normalize(text)
    normalized_claim = normalize(claim)

    if not normalized_claim:
        return False

    pattern = re.compile(
        r"(?<!\w)" + re.escape(normalized_claim) + r"(?!\w)"
    )
    matches = list(pattern.finditer(normalized_text))

    if not matches:
        return False

    # A proposition such as "vuelve al campo" is not present when the answer
    # explicitly says "no vuelve al campo". Claims that already begin with a
    # negation keep their literal meaning.
    if re.match(r"^(?:no|nunca|jamas)\b", normalized_claim):
        return True

    for match in matches:
        prefix = normalized_text[max(0, match.start() - 16):match.start()]
        if not re.search(r"\b(?:no|nunca|jamas)\s+$", prefix):
            return True

    return False


def _snapshot_has_card(snapshot: ConversationSnapshot, expected: str) -> bool:
    normalized_expected = normalize(expected)
    return any(
        normalize(card) == normalized_expected
        for card in snapshot.cards
    )


def _is_insufficient_answer(answer: str) -> bool:
    return any(
        contains_term(answer, marker)
        for marker in INSUFFICIENT_EVIDENCE_MARKERS
    )


def _highest_outcome(findings: list[EvaluationFinding]) -> OpenJudgeOutcome:
    if not findings:
        return OpenJudgeOutcome.PASS

    return max(
        (finding.outcome for finding in findings),
        key=lambda outcome: OUTCOME_SEVERITY[outcome],
    )


def evaluate_turn(
    contract: OpenJudgeTurn,
    answer: str,
    snapshot: ConversationSnapshot | None = None,
    exception: str = "",
) -> tuple[OpenJudgeOutcome, list[EvaluationFinding]]:
    """Evaluate one answer against its semantic and conversational contract."""

    snapshot = snapshot or ConversationSnapshot()
    findings: list[EvaluationFinding] = []

    if exception:
        findings.append(
            EvaluationFinding(
                outcome=OpenJudgeOutcome.EXECUTION_ERROR,
                message="Exception during answer generation.",
            )
        )
        return OpenJudgeOutcome.EXECUTION_ERROR, findings

    for claim in contract.forbidden:
        if contains_claim(answer, claim.text):
            findings.append(
                EvaluationFinding(
                    outcome=claim.outcome,
                    message=f"Forbidden claim present: {claim.text}",
                )
            )

    for expected_card in contract.expected_cards:
        if not _snapshot_has_card(snapshot, expected_card):
            findings.append(
                EvaluationFinding(
                    outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
                    message=(
                        "Expected active card missing from conversation state: "
                        f"{expected_card}"
                    ),
                )
            )

    for forbidden_card in contract.forbidden_cards:
        if _snapshot_has_card(snapshot, forbidden_card):
            findings.append(
                EvaluationFinding(
                    outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
                    message=(
                        "Stale card remained active after topic change: "
                        f"{forbidden_card}"
                    ),
                )
            )

    missing_required: list[str] = []

    for term in contract.required_all:
        if not contains_term(answer, term):
            missing_required.append(f"Missing required term: {term}")

    for group in contract.required_any:
        if not any(contains_term(answer, term) for term in group):
            missing_required.append(
                "Missing one required alternative: " + ", ".join(group)
            )

    if missing_required:
        missing_outcome = (
            OpenJudgeOutcome.INSUFFICIENT_EVIDENCE
            if _is_insufficient_answer(answer)
            else contract.missing_outcome
        )
        findings.extend(
            EvaluationFinding(
                outcome=missing_outcome,
                message=message,
            )
            for message in missing_required
        )

    missing_recommended: list[str] = []

    for term in contract.recommended_all:
        if not contains_term(answer, term):
            missing_recommended.append(f"Missing recommended term: {term}")

    for group in contract.recommended_any:
        if not any(contains_term(answer, term) for term in group):
            missing_recommended.append(
                "Missing one recommended alternative: " + ", ".join(group)
            )

    findings.extend(
        EvaluationFinding(
            outcome=OpenJudgeOutcome.CORRECT_BUT_INCOMPLETE,
            message=message,
        )
        for message in missing_recommended
    )

    if findings:
        return _highest_outcome(findings), findings

    return contract.success_outcome, findings
