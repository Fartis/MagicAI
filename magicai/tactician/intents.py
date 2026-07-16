from __future__ import annotations

import re
import unicodedata
from enum import Enum

from magicai.language.detection import detect_language


class StrategyIntent(str, Enum):
    COMBO_DETECTION = "combo_detection"
    SYNERGY_ANALYSIS = "synergy_analysis"
    CARD_COMPARISON = "card_comparison"
    PLAY_RECOMMENDATION = "play_recommendation"
    DECKBUILDING = "deckbuilding"
    PLAY_SEQUENCE = "play_sequence"
    COMBO_DISRUPTION = "combo_disruption"
    COMBO_REQUIREMENTS = "combo_requirements"
    INTERACTION_HYPOTHESIS = "interaction_hypothesis"
    RULES_CLARIFICATION = "rules_clarification"
    MECHANIC_DEFINITION = "mechanic_definition"
    MECHANIC_EQUIVALENCE = "mechanic_equivalence"
    COMBO_FAILURE_EXPLANATION = "combo_failure_explanation"
    INTERACTION_TIMING = "interaction_timing"
    GENERAL_STRATEGY = "general_strategy"


_COMBO_MARKERS = (
    "combo", "infinito", "infinite", "loop", "bucle",
)
_SYNERGY_MARKERS = (
    "sinergia", "synergy", "funcionan juntas", "funcionan juntos", "interactuan", "interactúan",
)
_COMPARISON_MARKERS = (
    "cual es mejor", "cuál es mejor", "mejor que", "compar", "versus", " vs ", "which is better", "better than",
)
_PLAY_MARKERS = (
    "que juego", "qué juego", "que jugada", "qué jugada", "linea de juego", "línea de juego",
    "deberia hacer", "debería hacer", "conviene", "play line", "what should i do",
)
_SEQUENCE_MARKERS = (
    "en que orden", "en qué orden", "orden se juega", "orden del combo", "play sequence", "what order",
)
_DISRUPTION_MARKERS = (
    "donde se corta", "dónde se corta", "como se corta", "cómo se corta", "cortar", "cortarlo", "interrump", "disrupt", "stop the combo",
)
_REQUIREMENT_MARKERS = (
    "que necesito", "qué necesito", "requisitos", "required pieces", "what do i need",
)
_HYPOTHESIS_MARKERS = (
    "por lo que", "asi que", "así que", "entonces se", "therefore", "which means",
)
_DECK_MARKERS = (
    "mi mazo", "decklist", "deck list", "construir mazo", "mejorar mazo", "deckbuilding", "upgrade",
)
_FAILURE_MARKERS = (
    "por que no", "por qué no", "porque no", "que impide", "qué impide", "donde falla", "dónde falla",
    "por que se rompe", "por qué se rompe", "why does not", "why doesn't", "why does the combo fail",
)
_TIMING_MARKERS = (
    "en que momento", "en qué momento", "cuando comprueba", "cuándo comprueba", "antes o despues", "antes o después",
    "when does", "at what point", "timing",
)
_EQUIVALENCE_MARKERS = (
    "es cuando muere", "no cuando", "es lo mismo", "mismo evento", "equivale", "significa lo mismo",
    "same event", "is the same as", "rather than",
)
_DEFINITION_MARKERS = (
    "que es", "qué es", "define", "como funciona", "cómo funciona", "what is", "define", "how does",
)
_RULES_CLARIFICATION_MARKERS = (
    "regla", "rules", "se dispara", "se activa", "trigger", "cementerio", "graveyard", "muere", "dies",
    "prioridad", "priority", "pila", "stack",
)


def classify_strategy_intent(question: str) -> StrategyIntent:
    normalized = _normalize(question)

    if _looks_like_mechanic_equivalence(normalized):
        return StrategyIntent.MECHANIC_EQUIVALENCE
    if any(marker in normalized for marker in _FAILURE_MARKERS):
        return StrategyIntent.COMBO_FAILURE_EXPLANATION
    if any(marker in normalized for marker in _TIMING_MARKERS):
        return StrategyIntent.INTERACTION_TIMING
    if re.match(r"^(pero|but)\b", normalized) or any(marker in normalized for marker in _HYPOTHESIS_MARKERS):
        return StrategyIntent.INTERACTION_HYPOTHESIS
    if any(marker in normalized for marker in _SEQUENCE_MARKERS):
        return StrategyIntent.PLAY_SEQUENCE
    if any(marker in normalized for marker in _DISRUPTION_MARKERS):
        return StrategyIntent.COMBO_DISRUPTION
    if any(marker in normalized for marker in _REQUIREMENT_MARKERS):
        return StrategyIntent.COMBO_REQUIREMENTS
    if any(marker in normalized for marker in _COMBO_MARKERS):
        return StrategyIntent.COMBO_DETECTION
    if any(marker in normalized for marker in _SYNERGY_MARKERS):
        return StrategyIntent.SYNERGY_ANALYSIS
    if any(marker in normalized for marker in _COMPARISON_MARKERS):
        return StrategyIntent.CARD_COMPARISON
    if any(marker in normalized for marker in _PLAY_MARKERS):
        return StrategyIntent.PLAY_RECOMMENDATION
    if any(marker in normalized for marker in _DECK_MARKERS):
        return StrategyIntent.DECKBUILDING
    if any(marker in normalized for marker in _DEFINITION_MARKERS) and any(
        keyword in normalized for keyword in ("undying", "persist", "ward", "habilidad", "ability")
    ):
        return StrategyIntent.MECHANIC_DEFINITION
    if any(marker in normalized for marker in _RULES_CLARIFICATION_MARKERS):
        return StrategyIntent.RULES_CLARIFICATION
    return StrategyIntent.GENERAL_STRATEGY


def looks_like_referential_follow_up(question: str) -> bool:
    normalized = " " + _normalize(question) + " "
    if re.match(r"^\s*[¿?¡!]*(?:y|and|entonces|so)\b", normalized):
        return True
    if re.search(r"\b(?:lo|la|los|las|ello|ellos|ellas|it|them|that|those|eso|esto)\b", normalized):
        return True
    return any(
        marker in normalized
        for marker in (" tambien ", " también ", " ademas ", " además ", " with them ", " con ellos ", " con ellas ")
    )


def is_spanish(question: str) -> bool:
    language, _, _, _ = detect_language(question, default="es")
    return language == "es"


def _looks_like_mechanic_equivalence(normalized: str) -> bool:
    has_mechanic = any(keyword in normalized for keyword in ("undying", "persist", "ward", "habilidad", "ability"))
    has_event_pair = (
        any(marker in normalized for marker in ("muere", "morir", "dies"))
        and any(marker in normalized for marker in ("cementerio", "graveyard"))
    )
    return has_mechanic and has_event_pair and any(marker in normalized for marker in _EQUIVALENCE_MARKERS)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
