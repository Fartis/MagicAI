from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True, slots=True)
class LanguageDecision:
    input_language: str
    session_language: str
    response_language: str
    confidence: str
    locked: bool
    spanish_score: int
    english_score: int

    def to_dict(self) -> dict[str, object]:
        return {
            "input_language": self.input_language,
            "session_language": self.session_language,
            "response_language": self.response_language,
            "confidence": self.confidence,
            "language_locked": self.locked,
            "spanish_score": self.spanish_score,
            "english_score": self.english_score,
        }


# Card names, rules keywords, mana symbols, and format names are deliberately
# ignored. They are normally English even inside an otherwise Spanish turn.
_NEUTRAL_MTG_TERMS = {
    "undying",
    "persist",
    "ward",
    "commander",
    "modern",
    "pioneer",
    "legacy",
    "standard",
    "oracle",
    "trigger",
    "stack",
    "the",
    "ozolith",
    "young",
    "wolf",
    "carrion",
    "feeder",
    "ashnod",
    "altar",
    "ghave",
    "guru",
    "of",
    "spores",
}

_SPANISH_STRONG = {
    "entonces",
    "cuando",
    "muere",
    "morir",
    "criatura",
    "cementerio",
    "campo",
    "batalla",
    "contador",
    "contadores",
    "porque",
    "porqué",
    "aunque",
    "pero",
    "tiene",
    "hace",
    "puedo",
    "puede",
    "vuelve",
    "entra",
    "sale",
    "sacrifica",
    "sacrifico",
    "necesito",
    "antes",
    "después",
    "despues",
    "mismo",
    "misma",
    "no",
    "sí",
    "si",
    "qué",
    "que",
    "cómo",
    "como",
    "cuándo",
    "dónde",
    "donde",
}

_ENGLISH_STRONG = {
    "then",
    "when",
    "dies",
    "creature",
    "graveyard",
    "battlefield",
    "counter",
    "counters",
    "because",
    "although",
    "but",
    "does",
    "returns",
    "enters",
    "leaves",
    "sacrifice",
    "need",
    "before",
    "after",
    "same",
    "what",
    "how",
    "why",
    "where",
}

_SPANISH_FUNCTION = {
    "el", "la", "los", "las", "un", "una", "de", "del", "al", "en",
    "por", "para", "con", "sin", "y", "o", "es", "son", "se", "lo",
    "le", "su", "sus", "mi", "tu", "ya", "más", "mas", "eso", "esto",
}

_ENGLISH_FUNCTION = {
    "a", "an", "and", "or", "is", "are", "to", "from", "in", "on",
    "with", "without", "it", "its", "this", "that", "the", "my", "your",
}


def detect_language(text: str, *, default: str = "es") -> tuple[str, str, int, int]:
    raw = text or ""
    normalized = _normalize(raw)
    tokens = [token for token in re.findall(r"[a-z0-9+/'-]+", normalized) if token]
    semantic_tokens = [token for token in tokens if token not in _NEUTRAL_MTG_TERMS]

    spanish_score = 0
    english_score = 0

    if "¿" in raw or "¡" in raw:
        spanish_score += 4
    if re.search(r"[áéíóúüñ]", raw.casefold()):
        spanish_score += 3

    for token in semantic_tokens:
        if token in _SPANISH_STRONG:
            spanish_score += 2
        if token in _ENGLISH_STRONG:
            english_score += 2
        if token in _SPANISH_FUNCTION:
            spanish_score += 1
        if token in _ENGLISH_FUNCTION:
            english_score += 1

    if spanish_score >= english_score + 2:
        return "es", "high" if spanish_score >= 5 else "medium", spanish_score, english_score
    if english_score >= spanish_score + 2:
        return "en", "high" if english_score >= 5 else "medium", spanish_score, english_score

    normalized_default = default if default in {"es", "en"} else "es"
    return normalized_default, "low", spanish_score, english_score


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
