import json
from pathlib import Path

from magicai.sources.card_scope import (
    SUPPORTED_PAPER_FORMATS,
    SUPPORTED_LEGALITY_STATUSES,
    is_supported_judge_card,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCRYFALL_FILE = (
    PROJECT_ROOT /
    "sources" /
    "scryfall" /
    "oracle-cards.json"
)

_cards = None
_card_index = None
_loaded_source = None


def _supported_legality_count(card: dict) -> int:
    legalities = card.get("legalities") or {}

    return sum(
        1
        for format_name in SUPPORTED_PAPER_FORMATS
        if str(legalities.get(format_name, "")).casefold()
        in SUPPORTED_LEGALITY_STATUSES
    )


def _preferred_card(candidates: list[dict]) -> dict:
    """Choose the strongest ordinary representative for an exact name.

    Multiple Oracle identities can share a printed name. Supplemental objects
    are filtered before this point; among remaining cards, prefer the object
    supported by the most paper formats and then the most recently released
    representative. This prevents input order from deciding name resolution.
    """

    return max(
        candidates,
        key=lambda card: (
            _supported_legality_count(card),
            str(card.get("released_at", "")),
            str(card.get("oracle_id", "")),
        ),
    )


def configure_card_source(path: str | Path) -> Path:
    """Select the Oracle bulk file used by runtime card lookup.

    Dynamic campaigns may override the generator corpus.  Runtime lookup must
    use that exact same file, especially in forked workers, or a scenario can be
    generated from one Oracle snapshot and answered from another.
    """

    global SCRYFALL_FILE, _cards, _card_index, _loaded_source
    resolved = Path(path).resolve()
    if Path(SCRYFALL_FILE).resolve() != resolved:
        SCRYFALL_FILE = resolved
        _cards = None
        _card_index = None
        _loaded_source = None
    return resolved


def load_cards(source_file: str | Path | None = None):
    """Load the supported ordinary-paper Oracle corpus once per source file."""

    global _cards
    global _card_index
    global _loaded_source

    if source_file is not None:
        configure_card_source(source_file)
    resolved_source = Path(SCRYFALL_FILE).resolve()
    if _cards is not None and _loaded_source == resolved_source:
        return _cards

    _cards = None
    _card_index = None
    with resolved_source.open(encoding="utf-8") as f:
        raw_cards = json.load(f)

    _cards = [
        card
        for card in raw_cards
        if is_supported_judge_card(card)
    ]

    candidates_by_name: dict[str, list[dict]] = {}

    for card in _cards:
        name = str(card.get("name", "")).casefold().strip()

        if not name:
            continue

        candidates_by_name.setdefault(name, []).append(card)

    _card_index = {
        name: _preferred_card(candidates)
        for name, candidates in candidates_by_name.items()
    }
    _loaded_source = resolved_source

    excluded_count = len(raw_cards) - len(_cards)

    print(
        f"[MagicAI] Indexed {len(_card_index)} card names "
        f"from {len(_cards)} supported cards "
        f"({excluded_count} supplemental/out-of-scope objects excluded) "
        f"from {resolved_source}."
    )

    return _cards


def search_exact_card(name: str):

    load_cards()

    return _card_index.get(
        name.casefold().strip()
    )


def search_cards_by_name(text: str):

    load_cards()

    text = text.casefold().strip()

    return [
        card
        for name, card in _card_index.items()
        if text in name
    ]
