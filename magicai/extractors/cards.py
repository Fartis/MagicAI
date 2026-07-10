import re
from dataclasses import dataclass

from magicai.retrieval.rule_intent import is_common_language_card_alias
from magicai.scryfall import load_cards


_exact_cards = None
_alias_cards = None
_ambiguous_aliases = None

_STOP_ALIASES = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "or",
    "the",
    "to",
    "with",
}

_REFERENCE_ALIAS_BLOCKLIST = {
    "magic",
    "mtg",
    "commander",
    "edh",
    "modern",
    "pioneer",
    "standard",
    "legacy",
    "vintage",
    "pauper",
    "brawl",
    "historic",
    "timeless",
    "alchemy",
    "draft",
    "sealed",

    "priority",
    "prioridad",
    "stack",
    "pila",
    "layers",
    "layer",
    "capas",
    "capa",
    "mulligan",
    "london",

    "undying",
    "persist",
    "flying",
    "trample",
    "haste",
    "vigilance",
    "lifelink",
    "deathtouch",
    "menace",
    "reach",
    "hexproof",
    "ward",
    "flash",
    "defender",
    "prowess",
    "cascade",
    "storm",
    "madness",
    "cycling",
    "kicker",
    "flashback",
    "escape",
    "convoke",
    "delve",

    # Palabras comunes en preguntas de reglas en español.
    # Si se permitieran como aliases ambiguos, preguntas como
    # "una carta en mesa" o "paso final" terminarían pidiendo
    # desambiguar cartas Mesa/Final en vez de contestar reglas.
    "mesa",
    "final",
    "paso",
    "inicio",
    "principio",
    "limpieza",
    "enderezar",
    "resolución",
    "resolucion",
    "respuesta",
    "orden",
}

@dataclass(frozen=True)
class CardNameAmbiguity:

    alias: str
    candidates: list[str]


def _load():

    global _exact_cards
    global _alias_cards
    global _ambiguous_aliases

    if (
        _exact_cards is not None
        and _alias_cards is not None
        and _ambiguous_aliases is not None
    ):
        return

    cards = load_cards()

    names = sorted(
        {
            _display_name(card["name"])
            for card in cards
        },
        key=len,
        reverse=True,
    )

    _exact_cards = []

    for name in names:

        pattern = _compile_name_pattern(
            name.lower()
        )

        _exact_cards.append(
            (
                name,
                pattern,
            )
        )

    auto_alias_map: dict[str, set[str]] = {}
    reference_alias_map: dict[str, set[str]] = {}

    for name in names:

        for alias in _auto_alias_candidates(name):

            alias_key = alias.lower()

            auto_alias_map.setdefault(
                alias_key,
                set(),
            ).add(name)

            reference_alias_map.setdefault(
                alias_key,
                set(),
            ).add(name)

        for alias in _reference_alias_candidates(name):

            alias_key = alias.lower()

            reference_alias_map.setdefault(
                alias_key,
                set(),
            ).add(name)

    unique_aliases = []

    for alias, alias_names in auto_alias_map.items():

        sorted_names = sorted(alias_names)

        if len(sorted_names) != 1:

            continue

        canonical_name = sorted_names[0]

        if alias == canonical_name.lower():

            continue

        unique_aliases.append(
            (
                alias,
                canonical_name,
            )
        )

    unique_aliases.sort(
        key=lambda item: len(item[0]),
        reverse=True,
    )

    _alias_cards = []

    for alias, canonical_name in unique_aliases:

        pattern = _compile_name_pattern(alias)

        _alias_cards.append(
            (
                canonical_name,
                pattern,
            )
        )

    ambiguous_aliases = []

    for alias, alias_names in reference_alias_map.items():

        sorted_names = sorted(alias_names)

        if len(sorted_names) <= 1:

            continue

        ambiguous_aliases.append(
            (
                alias,
                sorted_names,
            )
        )

    ambiguous_aliases.sort(
        key=lambda item: len(item[0]),
        reverse=True,
    )

    _ambiguous_aliases = []

    for alias, candidates in ambiguous_aliases:

        pattern = _compile_name_pattern(alias)

        _ambiguous_aliases.append(
            (
                alias,
                candidates,
                pattern,
            )
        )


def extract_cards(question: str):

    _load()

    question = question.lower()

    found = []

    for name, pattern in _exact_cards:

        if pattern.search(question):

            _add_unique(
                found,
                name,
            )

            question = pattern.sub(
                " ",
                question,
            )

    for name, pattern in _alias_cards:

        if pattern.search(question):

            _add_unique(
                found,
                name,
            )

            question = pattern.sub(
                " ",
                question,
            )

    return found


def find_ambiguous_card_references(
    question: str,
) -> CardNameAmbiguity | None:

    _load()

    question_lower = question.lower()

    for _name, pattern in _exact_cards:

        if pattern.search(question_lower):

            return None

    for alias, candidates, pattern in _ambiguous_aliases:

        if alias.lower() in _REFERENCE_ALIAS_BLOCKLIST:

            continue

        if is_common_language_card_alias(
            alias,
            question,
        ):

            continue

        if pattern.search(question_lower):

            return CardNameAmbiguity(
                alias=alias,
                candidates=candidates[:10],
            )

    return None


def _auto_alias_candidates(name: str) -> list[str]:
    """
    Aliases que MagicAI puede resolver automáticamente.

    Ejemplos:
    - Korvold, Fae-Cursed King -> Korvold
    - Prossh, Skyraider of Kher -> Prossh

    Solo usamos alias derivados de coma para evitar resolver palabras comunes
    demasiado agresivamente.
    """

    aliases = []

    for face in _faces(name):

        if "," in face:

            alias = face.split(",", 1)[0].strip()

            _add_candidate_alias(
                aliases,
                alias,
            )

    return aliases


def _reference_alias_candidates(name: str) -> list[str]:
    """
    Aliases usados para detectar ambigüedad.

    Ejemplos:
    - Olivia Voldaren -> Olivia
    - Olivia, Crimson Bride -> Olivia
    - Olivia's Attendants -> Olivia

    No debe generar ambigüedad para conceptos comunes como:
    Magic, Commander, Undying, Priority, Layers, etc.
    """

    aliases = []

    for face in _faces(name):

        if "," in face:

            alias = face.split(",", 1)[0].strip()

            _add_reference_alias(
                aliases,
                alias,
            )

        first_word = _first_word(face)

        if first_word:

            _add_reference_alias(
                aliases,
                first_word,
            )

            possessive = _strip_possessive(first_word)

            if possessive != first_word:

                _add_reference_alias(
                    aliases,
                    possessive,
                )

    return aliases


def _faces(name: str) -> list[str]:

    return [
        part.strip()
        for part in name.split("//")
        if part.strip()
    ]


def _first_word(text: str) -> str | None:

    parts = text.strip().split()

    if not parts:

        return None

    return parts[0].strip(
        " ,.:;!?\"“”‘’"
    )


def _strip_possessive(word: str) -> str:

    lower = word.lower()

    if lower.endswith("'s"):

        return word[:-2]

    if lower.endswith("’s"):

        return word[:-2]

    return word


def _add_candidate_alias(
    aliases: list[str],
    alias: str,
):

    alias = alias.strip()

    if not alias:

        return

    if len(alias) < 3:

        return

    if alias.lower() in _STOP_ALIASES:

        return

    if alias not in aliases:

        aliases.append(alias)


def _compile_name_pattern(text: str):

    return re.compile(
        r"(?<![\w'])" + re.escape(text) + r"(?![\w'])"
    )


def _add_unique(items: list[str], item: str):

    if item not in items:

        items.append(item)

def _display_name(name: str) -> str:

    if "//" not in name:

        return name

    parts = [
        part.strip()
        for part in name.split("//")
        if part.strip()
    ]

    if not parts:

        return name

    if len(set(parts)) == 1:

        return parts[0]

    return name

def _add_reference_alias(
    aliases: list[str],
    alias: str,
):

    alias = alias.strip()

    if alias.lower() in _REFERENCE_ALIAS_BLOCKLIST:

        return

    _add_candidate_alias(
        aliases,
        alias,
    )