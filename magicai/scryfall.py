import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCRYFALL_FILE = (
    PROJECT_ROOT /
    "sources" /
    "scryfall" /
    "oracle-cards.json"
)

_cards = None
_card_index = None


def load_cards():
    """Carga Oracle una única vez."""

    global _cards
    global _card_index

    if _cards is not None:
        return _cards

    with open(SCRYFALL_FILE, encoding="utf-8") as f:
        _cards = json.load(f)

    #
    # Creamos un índice por nombre.
    #

    _card_index = {
        card["name"].lower(): card
        for card in _cards
    }

    print(f"[MagicAI] Indexed {len(_card_index)} cards.")

    return _cards


def search_exact_card(name: str):

    load_cards()

    return _card_index.get(
        name.lower()
    )


def search_cards_by_name(text: str):

    load_cards()

    text = text.lower()

    return [

        card

        for name, card in _card_index.items()

        if text in name

    ]