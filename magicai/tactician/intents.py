from __future__ import annotations

import re
import unicodedata
from enum import Enum


class StrategyIntent(str, Enum):
    COMBO_DETECTION = "combo_detection"
    SYNERGY_ANALYSIS = "synergy_analysis"
    CARD_COMPARISON = "card_comparison"
    PLAY_RECOMMENDATION = "play_recommendation"
    DECKBUILDING = "deckbuilding"
    GENERAL_STRATEGY = "general_strategy"


_COMBO_MARKERS = (
    "combo",
    "infinito",
    "infinite",
    "loop",
    "bucle",
)

_SYNERGY_MARKERS = (
    "sinergia",
    "synergy",
    "funcionan juntas",
    "funcionan juntos",
    "interactuan",
    "interactúan",
)

_COMPARISON_MARKERS = (
    "cual es mejor",
    "cuál es mejor",
    "mejor que",
    "compar",
    "versus",
    " vs ",
    "which is better",
    "better than",
)

_PLAY_MARKERS = (
    "que juego",
    "qué juego",
    "que jugada",
    "qué jugada",
    "linea de juego",
    "línea de juego",
    "deberia hacer",
    "debería hacer",
    "conviene",
    "play line",
    "what should i do",
)

_DECK_MARKERS = (
    "mi mazo",
    "decklist",
    "deck list",
    "construir mazo",
    "mejorar mazo",
    "deckbuilding",
    "upgrade",
)


def classify_strategy_intent(question: str) -> StrategyIntent:
    normalized = _normalize(question)

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
    return StrategyIntent.GENERAL_STRATEGY


def looks_like_referential_follow_up(question: str) -> bool:
    normalized = " " + _normalize(question) + " "
    if re.match(r"^\s*[¿?¡!]*(?:y|and)\b", normalized):
        return True
    if re.search(
        r"\b(?:lo|la|los|las|ello|ellos|ellas|it|them|that|those)\b",
        normalized,
    ):
        return True
    return any(
        marker in normalized
        for marker in (
            " tambien ",
            " también ",
            " ademas ",
            " además ",
            " with them ",
            " con ellos ",
            " con ellas ",
        )
    )


def is_spanish(question: str) -> bool:
    if "¿" in (question or "") or "¡" in (question or ""):
        return True
    normalized = _normalize(question)
    spanish_markers = (
        "que ",
        "qué ",
        "como ",
        "cómo ",
        "con ",
        "tiene ",
        "mazo",
        "jugada",
        "sinergia",
        "puedo",
    )
    return any(marker in normalized for marker in spanish_markers)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"\s+", " ", value.casefold()).strip()
    return value
