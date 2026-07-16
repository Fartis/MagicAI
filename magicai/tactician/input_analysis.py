from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
import unicodedata

from magicai.conversation.normalization import normalize_user_question
from magicai.language.policy import resolve_language_policy
from magicai.tactician.intents import StrategyIntent, classify_strategy_intent


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
    MECHANIC_EQUIVALENCE = "mechanic_equivalence"
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
    canonical_text: str
    language: str
    language_policy: dict[str, object]
    register: str
    speech_act: SpeechAct
    strategy_intent: StrategyIntent
    claims: list[InputClaim] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    causal_markers: list[str] = field(default_factory=list)
    asks_for_validation: bool = False
    question_target: str = ""
    answer_focus: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "language_policy": dict(self.language_policy),
            "register": self.register,
            "canonical_question": self.canonical_text,
            "speech_act": self.speech_act.value,
            "strategy_intent": self.strategy_intent.value,
            "question_target": self.question_target,
            "answer_focus": list(self.answer_focus),
            "claims_detected": len(self.claims),
            "claims": [claim.to_dict() for claim in self.claims],
            "concepts": list(self.concepts),
            "causal_markers": list(self.causal_markers),
            "asks_for_validation": bool(self.asks_for_validation),
        }


_CAUSAL_MARKERS = (
    "por lo que", "asi que", "de modo que", "entonces", "therefore", "so that", "which means",
)
_VALIDATION_MARKERS = (
    "hace combo", "es correcto", "tengo razon", "tengo razón", "funciona asi", "funciona así",
    "seria asi", "sería así", "is that correct", "does that work",
)


def analyze_user_input(text: str, *, session_language: str | None = None) -> InputAnalysis:
    raw = (text or "").strip()
    policy = resolve_language_policy(raw, session_language=session_language)
    normalized_question = normalize_user_question(raw, session_language=policy.response_language)
    canonical = normalized_question.canonical or raw
    normalized = _normalize(canonical)
    causal_markers = [marker for marker in _CAUSAL_MARKERS if marker in normalized]
    asks_for_validation = any(marker in normalized for marker in _VALIDATION_MARKERS)

    if re.match(r"^(pero|but)\b", normalized):
        speech_act = SpeechAct.CHALLENGE
    elif re.match(r"^(y|and)\b", normalized):
        speech_act = SpeechAct.FOLLOW_UP
    elif _looks_like_question(raw, normalized):
        speech_act = SpeechAct.QUESTION
    elif causal_markers:
        speech_act = SpeechAct.HYPOTHESIS
    else:
        speech_act = SpeechAct.REQUEST

    intent = classify_strategy_intent(canonical)
    concepts = _detect_concepts(normalized)
    claims = _extract_claims(raw, normalized, concepts, speech_act, intent)

    if speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS} and intent not in {
        StrategyIntent.COMBO_FAILURE_EXPLANATION,
        StrategyIntent.MECHANIC_EQUIVALENCE,
        StrategyIntent.INTERACTION_TIMING,
    }:
        intent = StrategyIntent.INTERACTION_HYPOTHESIS

    return InputAnalysis(
        raw_text=raw,
        normalized_text=normalized,
        canonical_text=canonical,
        language=policy.response_language,
        language_policy=policy.to_dict(),
        register=normalized_question.register,
        speech_act=speech_act,
        strategy_intent=intent,
        claims=claims,
        concepts=concepts,
        causal_markers=causal_markers,
        asks_for_validation=asks_for_validation,
        question_target=intent.value,
        answer_focus=_answer_focus(intent, concepts),
    )


def _extract_claims(
    raw: str,
    normalized: str,
    concepts: list[str],
    speech_act: SpeechAct,
    intent: StrategyIntent,
) -> list[InputClaim]:
    claims: list[InputClaim] = []

    def add(text: str, kind: ClaimKind, claim_concepts: tuple[str, ...]) -> None:
        cleaned = re.sub(r"\s+", " ", text).strip(" ,.;:¿?¡!")
        if not cleaned:
            return
        if any(existing.text.casefold() == cleaned.casefold() for existing in claims):
            return
        claims.append(InputClaim(f"claim-{len(claims) + 1}", cleaned, kind, claim_concepts))

    if intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        add(raw, ClaimKind.MECHANIC_EQUIVALENCE, ("dies", "graveyard", "undying"))

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
        # Do not turn a pure definition/equivalence question into a false claim
        # that Undying necessarily triggers.
        if intent is not StrategyIntent.MECHANIC_EQUIVALENCE:
            add(
                "Undying triggers again after Young Wolf leaves the battlefield",
                ClaimKind.DERIVED_CONCLUSION,
                ("undying", "intervening_if", "last_known_information"),
            )

    if "combo" in normalized and speech_act in {SpeechAct.HYPOTHESIS, SpeechAct.CHALLENGE, SpeechAct.REQUEST}:
        add(raw, ClaimKind.STRATEGIC, tuple(concepts))

    # Only assertion-like turns receive generic claim extraction. Open questions
    # such as "¿Qué necesito?" are question targets, not factual claims.
    if not claims and speech_act in {SpeechAct.CHALLENGE, SpeechAct.HYPOTHESIS}:
        fragments = re.split(r"[;.]|\b(?:por lo que|asi que|así que|therefore)\b", raw, flags=re.IGNORECASE)
        for fragment in fragments[:4]:
            fragment_normalized = _normalize(fragment)
            if len(fragment_normalized.split()) < 3:
                continue
            add(fragment, ClaimKind.FACTUAL, tuple(_detect_concepts(fragment_normalized)))

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
        ("battlefield", ("campo de batalla", "battlefield")),
        ("last_known_information", ("antes de dejar", "justo antes", "last known", "cuando deja")),
        ("ozolith", ("ozolith",)),
        ("combo", ("combo", "bucle", "loop", "infinito", "infinite")),
        ("play_sequence", ("orden", "sequence")),
        ("disruption", ("cortar", "interrump", "disrupt", "stop")),
        ("definition", ("que es", "como funciona", "define", "what is", "how does")),
        ("equivalence", ("es lo mismo", "equivale", "no cuando", "mismo evento", "same event")),
    )
    for concept, markers in mappings:
        if any(marker in normalized for marker in markers):
            concepts.append(concept)
    return concepts


def _answer_focus(intent: StrategyIntent, concepts: list[str]) -> list[str]:
    if intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        return ["define_dies", "compare_events", "exclude_other_zone_changes", "apply_current_interaction"]
    if intent is StrategyIntent.COMBO_FAILURE_EXPLANATION:
        return ["identify_failed_transition", "explain_rule", "apply_current_interaction"]
    if intent is StrategyIntent.INTERACTION_TIMING:
        return ["identify_timing_window", "explain_state_check", "apply_current_interaction"]
    if intent is StrategyIntent.COMBO_REQUIREMENTS:
        return ["list_required_permanents", "list_initial_state", "list_disruptive_assumptions"]
    return list(concepts)


def _looks_like_question(raw: str, normalized: str) -> bool:
    if "?" in raw or "¿" in raw:
        return True
    return bool(re.match(
        r"^(que|qué|como|cómo|cual|cuál|cuando|cuándo|donde|dónde|por que|por qué|puedo|tiene|hace|is|does|how|what|when|where|why|can|entonces)\b",
        normalized,
    ))


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
