from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
import unicodedata

from magicai.tactician.intents import StrategyIntent, classify_strategy_intent, is_spanish


class SpeechAct(str, Enum):
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    CHALLENGE = "challenge"
    FOLLOW_UP = "follow_up"
    REQUEST = "request"


class ClaimKind(str, Enum):
    FACTUAL = "factual"
    STATE_TRANSITION = "state_transition"
    TIMING_HYPOTHESIS = "timing_hypothesis"
    DERIVED_CONCLUSION = "derived_conclusion"
    STRATEGIC = "strategic"


@dataclass(frozen=True, slots=True)
class InputClaim:
    claim_id: str
    text: str
    kind: ClaimKind
    concepts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.claim_id,
            "text": self.text,
            "kind": self.kind.value,
            "concepts": list(self.concepts),
        }


@dataclass(slots=True)
class InputAnalysis:
    raw_text: str
    normalized_text: str
    language: str
    speech_act: SpeechAct
    strategy_intent: StrategyIntent
    claims: list[InputClaim] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    causal_markers: list[str] = field(default_factory=list)
    asks_for_validation: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "speech_act": self.speech_act.value,
            "strategy_intent": self.strategy_intent.value,
            "claims_detected": len(self.claims),
            "claims": [claim.to_dict() for claim in self.claims],
            "concepts": list(self.concepts),
            "causal_markers": list(self.causal_markers),
            "asks_for_validation": bool(self.asks_for_validation),
        }


_CAUSAL_MARKERS = (
    "por lo que",
    "asi que",
    "de modo que",
    "entonces",
    "therefore",
    "so that",
    "which means",
)

_VALIDATION_MARKERS = (
    "hace combo",
    "es correcto",
    "tengo razon",
    "tengo razón",
    "funciona asi",
    "funciona así",
    "seria asi",
    "sería así",
    "is that correct",
    "does that work",
)


def analyze_user_input(text: str) -> InputAnalysis:
    raw = (text or "").strip()
    normalized = _normalize(raw)
    causal_markers = [marker for marker in _CAUSAL_MARKERS if marker in normalized]
    asks_for_validation = any(marker in normalized for marker in _VALIDATION_MARKERS)

    if re.match(r"^(pero|but)\b", normalized):
        speech_act = SpeechAct.CHALLENGE
    elif causal_markers and not _looks_like_simple_question(raw, normalized):
        speech_act = SpeechAct.HYPOTHESIS
    elif re.match(r"^(y|and)\b", normalized):
        speech_act = SpeechAct.FOLLOW_UP
    elif _looks_like_simple_question(raw, normalized):
        speech_act = SpeechAct.QUESTION
    else:
        speech_act = SpeechAct.REQUEST

    intent = classify_strategy_intent(raw)
    concepts = _detect_concepts(normalized)
    claims = _extract_claims(raw, normalized, concepts)

    if speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS}:
        intent = StrategyIntent.INTERACTION_HYPOTHESIS
    elif "orden" in normalized or "sequence" in normalized:
        intent = StrategyIntent.PLAY_SEQUENCE
    elif any(marker in normalized for marker in ("cortar", "interrump", "disrupt", "stop the combo")):
        intent = StrategyIntent.COMBO_DISRUPTION

    return InputAnalysis(
        raw_text=raw,
        normalized_text=normalized,
        language="es" if is_spanish(raw) else "en",
        speech_act=speech_act,
        strategy_intent=intent,
        claims=claims,
        concepts=concepts,
        causal_markers=causal_markers,
        asks_for_validation=asks_for_validation,
    )


def _extract_claims(raw: str, normalized: str, concepts: list[str]) -> list[InputClaim]:
    claims: list[InputClaim] = []

    def add(text: str, kind: ClaimKind, claim_concepts: tuple[str, ...]) -> None:
        cleaned = re.sub(r"\s+", " ", text).strip(" ,.;:¿?¡!")
        if not cleaned:
            return
        if any(existing.text.casefold() == cleaned.casefold() for existing in claims):
            return
        claims.append(
            InputClaim(
                claim_id=f"claim-{len(claims) + 1}",
                text=cleaned,
                kind=kind,
                concepts=claim_concepts,
            )
        )

    if "sacrific" in normalized and any(name in normalized for name in ("young wolf", "criatura", "creature")):
        add(
            "Carrion Feeder sacrifices Young Wolf" if "carrion feeder" in normalized else "Young Wolf is sacrificed",
            ClaimKind.STATE_TRANSITION,
            ("sacrifice", "dies"),
        )

    counter_to_ozolith = (
        "ozolith" in normalized
        and "contador" in normalized
        and any(marker in normalized for marker in ("va a", "pasa a", "mueve", "se lleva", "goes to", "moves to"))
    )
    if counter_to_ozolith:
        add(
            "The +1/+1 counter moves from Young Wolf to The Ozolith before Undying checks",
            ClaimKind.TIMING_HYPOTHESIS,
            ("counters", "leaves_battlefield", "last_known_information", "ozolith"),
        )

    if "undying" in normalized and any(marker in normalized for marker in ("activa", "dispara", "vuelve", "triggers", "returns")):
        add(
            "Undying triggers again after Young Wolf leaves the battlefield",
            ClaimKind.DERIVED_CONCLUSION,
            ("undying", "intervening_if", "last_known_information"),
        )

    if "combo" in normalized:
        add(
            raw,
            ClaimKind.STRATEGIC,
            tuple(concepts),
        )

    if not claims and raw:
        fragments = re.split(r"[;.]|\b(?:por lo que|asi que|así que|therefore)\b", raw, flags=re.IGNORECASE)
        for fragment in fragments[:4]:
            fragment_normalized = _normalize(fragment)
            if len(fragment_normalized.split()) < 3:
                continue
            kind = ClaimKind.DERIVED_CONCLUSION if any(marker in fragment_normalized for marker in ("por lo que", "asi que", "therefore")) else ClaimKind.FACTUAL
            add(fragment, kind, tuple(_detect_concepts(fragment_normalized)))

    return claims


def _detect_concepts(normalized: str) -> list[str]:
    concepts: list[str] = []
    mappings = (
        ("sacrifice", ("sacrific",)),
        ("dies", ("muere", "morir", "dies")),
        ("undying", ("undying",)),
        ("counters", ("contador", "counter")),
        ("leaves_battlefield", ("deja el campo", "abandona el campo", "leaves the battlefield")),
        ("graveyard", ("cementerio", "graveyard")),
        ("last_known_information", ("antes de dejar", "justo antes", "last known", "cuando deja")),
        ("ozolith", ("ozolith",)),
        ("combo", ("combo", "bucle", "loop", "infinito", "infinite")),
        ("play_sequence", ("orden", "sequence")),
        ("disruption", ("cortar", "interrump", "disrupt", "stop")),
    )
    for concept, markers in mappings:
        if any(marker in normalized for marker in markers):
            concepts.append(concept)
    return concepts


def _looks_like_simple_question(raw: str, normalized: str) -> bool:
    if "?" in raw or "¿" in raw:
        return True
    return bool(
        re.match(
            r"^(que|qué|como|cómo|cual|cuál|cuando|cuándo|donde|dónde|por que|por qué|puedo|tiene|hace|is|does|how|what|when|where|why|can)\b",
            normalized,
        )
    )


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
