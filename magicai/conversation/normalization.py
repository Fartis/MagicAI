from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata

from magicai.language.policy import resolve_language_policy


@dataclass(frozen=True, slots=True)
class NormalizedUserQuestion:
    original: str
    canonical: str
    language: str
    register: str
    concepts: tuple[str, ...] = ()
    transformations: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "original": self.original,
            "canonical_question": self.canonical,
            "language": self.language,
            "register": self.register,
            "concepts": list(self.concepts),
            "transformations": list(self.transformations),
            "ambiguities": list(self.ambiguities),
        }


# The normalizer maps colloquial wording to retrieval-friendly wording. It does
# not answer the question and it does not silently correct a factual premise.
_SPANISH_REWRITES = (
    (r"\bpisa(?:r)?\s+(?:el\s+)?cementerio\b", "es puesta en un cementerio" , "graveyard_colloquial"),
    (r"\bva\s+al\s+hoyo\b", "va al cementerio", "graveyard_colloquial"),
    (r"\bmanda(?:r)?\s+al\s+hoyo\b", "pone en el cementerio", "graveyard_colloquial"),
    (r"\bse\s+va\s+al\s+hoyo\b", "es puesta en el cementerio", "graveyard_colloquial"),
    (r"\bpisa(?:r)?\s+mesa\b", "entra al campo de batalla", "battlefield_colloquial"),
    (r"\bbaja(?:r)?\s+a\s+mesa\b", "entra al campo de batalla", "battlefield_colloquial"),
    (r"\bse\s+lleva\s+puesto\s+el\s+contador\b", "conserva el contador al cambiar de zona", "counter_colloquial"),
    (r"\bse\s+puede\s+cortar\b", "se puede responder o interrumpir", "interaction_colloquial"),
    (r"\bme\s+pueden\s+reventar\s+el\s+combo\b", "pueden interrumpir el combo", "interaction_colloquial"),
    (r"\bhacer\s+la\s+pirula\b", "repetir la interacción", "strategy_colloquial"),
)

_ENGLISH_REWRITES = (
    (r"\bhits?\s+the\s+graveyard\b", "is put into a graveyard", "graveyard_colloquial"),
    (r"\bhits?\s+the\s+board\b", "enters the battlefield", "battlefield_colloquial"),
)


def normalize_user_question(
    text: str,
    *,
    session_language: str | None = None,
) -> NormalizedUserQuestion:
    original = " ".join((text or "").strip().split())
    policy = resolve_language_policy(original, session_language=session_language)
    canonical = original
    transformations: list[str] = []

    rewrites = _SPANISH_REWRITES if policy.response_language == "es" else _ENGLISH_REWRITES
    for pattern, replacement, code in rewrites:
        updated, count = re.subn(pattern, replacement, canonical, flags=re.IGNORECASE)
        if count:
            canonical = updated
            transformations.append(code)

    canonical = " ".join(canonical.split())
    concepts = _detect_concepts(canonical)
    register = "casual" if transformations or _looks_casual(original) else "standard"

    return NormalizedUserQuestion(
        original=original,
        canonical=canonical,
        language=policy.response_language,
        register=register,
        concepts=tuple(concepts),
        transformations=tuple(_deduplicate(transformations)),
        ambiguities=(),
    )


def _detect_concepts(text: str) -> list[str]:
    normalized = _normalize(text)
    mappings = (
        ("graveyard", ("cementerio", "graveyard")),
        ("battlefield", ("campo de batalla", "battlefield")),
        ("dies", ("muere", "morir", "dies", "put into a graveyard from the battlefield")),
        ("undying", ("undying",)),
        ("counter", ("contador", "counter")),
        ("trigger", ("dispara", "activa", "trigger")),
        ("combo", ("combo", "bucle", "loop", "infinito", "infinite")),
        ("interaction", ("interrump", "responder", "interaction", "cortar")),
    )
    result: list[str] = []
    for concept, markers in mappings:
        if any(marker in normalized for marker in markers):
            result.append(concept)
    return result


def _looks_casual(text: str) -> bool:
    normalized = _normalize(text)
    markers = (
        "hoyo",
        "pisa mesa",
        "pisa cementerio",
        "pirula",
        "reventar el combo",
        "se lleva puesto",
    )
    return any(marker in normalized for marker in markers)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
