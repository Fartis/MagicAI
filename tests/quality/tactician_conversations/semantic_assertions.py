from __future__ import annotations

import re
import unicodedata


_CONCEPT_MARKERS: dict[str, tuple[tuple[str, ...], ...]] = {
    "battlefield_to_graveyard": (
        ("campo de batalla", "cementerio"),
        ("battlefield", "graveyard"),
    ),
    "dies": (("muere",), ("morir",), ("dies",)),
    "undying_without_counter": (
        ("undying", "se dispara", "no tenia", "contador"),
        ("undying", "se dispara", "sin contador"),
        ("undying", "triggers", "no +1/+1 counter"),
        ("undying", "triggers", "had no +1/+1"),
    ),
    "returns_with_counter": (
        ("vuelve", "contador +1/+1"),
        ("regresa", "contador +1/+1"),
        ("returns", "+1/+1 counter"),
    ),
    "undying_blocked_by_counter": (
        ("contador +1/+1", "undying no se dispara"),
        ("undying", "contador", "no se dispara"),
        ("tenia", "contador", "no se dispara"),
        ("had a +1/+1 counter", "does not trigger"),
    ),
    "same_event": (
        ("mismo evento",),
        ("no son dos momentos",),
        ("same event",),
        ("not two separate moments",),
    ),
    "other_zone_not_dies": (
        ("otra zona", "no", "morir"),
        ("mano", "biblioteca", "no"),
        ("another zone", "not dying"),
        ("hand", "library", "did not die"),
    ),
    "ozolith_does_not_reset": (
        ("ozolith", "no reinicia undying"),
        ("ozolith", "no", "retira", "contador"),
        ("ozolith", "no retiro", "contador"),
        ("ozolith", "does not reset undying"),
        ("ozolith", "does not remove", "counter"),
    ),
    "non_infinite_loop": (
        ("no forman", "bucle infinito"),
        ("no es", "combo infinito"),
        ("do not form", "infinite loop"),
    ),
    "ghave_resets_counter": (
        ("ghave", "retira", "contador"),
        ("ghave", "remove", "counter"),
    ),
    "altar_produces_two": (
        ("ashnod", "dos manas"),
        ("ashnod", "dos manás"),
        ("ashnod", "two", "mana"),
    ),
    "net_mana_and_token": (
        ("mana", "neto", "saproling"),
        ("maná", "neto", "saproling"),
        ("mana", "neto", "ficha"),
        ("maná", "neto", "ficha"),
        ("net", "mana", "saproling"),
        ("net", "mana", "token"),
    ),
    "graveyard_interruption": (
        ("exiliar", "young wolf", "cementerio"),
        ("exile", "young wolf", "graveyard"),
    ),
    "ghave_removal_window": (
        ("eliminar", "ghave"),
        ("removal", "ghave"),
        ("remove", "ghave"),
    ),
    "requires_three_pieces": (
        ("necesitas", "young wolf", "ashnod", "ghave"),
        ("need", "young wolf", "ashnod", "ghave"),
    ),
    "no_starting_mana": (
        ("no necesitas mana inicial",),
        ("no necesitas maná inicial",),
        ("no starting mana",),
    ),
}


def has_concept(text: str, concept: str) -> bool:
    normalized = _normalize(text)
    groups = _CONCEPT_MARKERS.get(concept)
    if groups is None:
        raise KeyError(f"unknown semantic concept: {concept}")
    return any(all(_normalize(marker) in normalized for marker in group) for group in groups)


def known_concepts() -> set[str]:
    return set(_CONCEPT_MARKERS)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.casefold()).strip()
