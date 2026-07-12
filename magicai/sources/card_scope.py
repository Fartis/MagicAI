"""Shared scope rules for Scryfall card objects used by MagicAI.

The normal Judge corpus intentionally contains ordinary paper cards. Scryfall
bulk data also contains supplemental game objects such as Vanguard cards,
tokens, emblems and planar cards. Those objects are useful in their own modes,
but they must not win ordinary card-name resolution.
"""

from __future__ import annotations


SUPPORTED_PAPER_FORMATS = (
    "standard",
    "pioneer",
    "modern",
    "legacy",
    "pauper",
    "vintage",
    "commander",
    "standardbrawl",
    "brawl",
)

SUPPORTED_LEGALITY_STATUSES = {"legal", "restricted"}

# These Scryfall layouts represent supplemental objects rather than ordinary
# cards that belong in a player's deck. Legitimate card layouts such as
# transform, modal_dfc, adventure, split, battle or prototype remain allowed.
EXCLUDED_STANDARD_LAYOUTS = {
    "art_series",
    "double_faced_token",
    "emblem",
    "planar",
    "scheme",
    "token",
    "vanguard",
}

EXCLUDED_STANDARD_SET_TYPES = {
    "funny",
    "token",
    "vanguard",
}


def supported_legal_formats(raw_card: dict) -> tuple[str, ...]:
    """Return supported paper formats where the card is legal/restricted."""

    legalities = raw_card.get("legalities") or {}

    return tuple(
        format_name
        for format_name in SUPPORTED_PAPER_FORMATS
        if str(legalities.get(format_name, "")).casefold()
        in SUPPORTED_LEGALITY_STATUSES
    )


def is_funny_or_playtest_card(raw_card: dict) -> bool:
    set_type = str(raw_card.get("set_type", "")).casefold()
    border_color = str(raw_card.get("border_color", "")).casefold()
    security_stamp = str(raw_card.get("security_stamp", "")).casefold()
    set_name = str(raw_card.get("set_name", "")).casefold()
    promo_types = {
        str(item).casefold()
        for item in (raw_card.get("promo_types") or [])
    }

    return (
        set_type == "funny"
        or border_color == "silver"
        or security_stamp == "acorn"
        or "playtest" in promo_types
        or "playtest" in set_name
    )


def is_supplemental_game_object(raw_card: dict) -> bool:
    """Return True for non-deck objects excluded from ordinary Judge lookup."""

    layout = str(raw_card.get("layout", "")).casefold()
    set_type = str(raw_card.get("set_type", "")).casefold()
    type_line = str(raw_card.get("type_line", "")).casefold().strip()

    if layout in EXCLUDED_STANDARD_LAYOUTS:
        return True

    if set_type in EXCLUDED_STANDARD_SET_TYPES:
        return True

    # Defensive fallback for old or incomplete bulk objects. Compare complete
    # type words rather than prefixes so an ordinary type such as
    # "Planeswalker" can never be mistaken for "Plane".
    type_words = {
        word.strip(" ,")
        for word in type_line.replace("—", " ").split()
    }
    supplemental_type_words = {
        "conspiracy",
        "dungeon",
        "emblem",
        "phenomenon",
        "plane",
        "scheme",
        "sticker",
        "token",
        "vanguard",
    }

    return bool(type_words & supplemental_type_words)


def is_supported_judge_card(raw_card: dict) -> bool:
    """Return whether a Scryfall object belongs in ordinary Judge lookup.

    This deliberately does not require current format legality. A genuine paper
    card may be banned everywhere and still be a valid subject for a rules
    question. Legality remains available as evidence; it is not used to erase
    ordinary cards from the Judge corpus.
    """

    name = str(raw_card.get("name", "")).strip()

    if not name:
        return False

    games = raw_card.get("games") or []

    if games and "paper" not in games:
        return False

    if raw_card.get("digital") is True:
        return False

    if is_funny_or_playtest_card(raw_card):
        return False

    if is_supplemental_game_object(raw_card):
        return False

    return True
