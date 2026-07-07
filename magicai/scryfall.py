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


def load_cards():
    """Carga las cartas una única vez."""

    global _cards

    if _cards is None:
        with open(SCRYFALL_FILE, encoding="utf-8") as f:
            _cards = json.load(f)

    return _cards


def search_exact_card(name: str):

    name = name.lower()

    for card in load_cards():

        if card["name"].lower() == name:
            return card

    return None


def search_cards_by_name(text: str):

    text = text.lower()

    results = []

    for card in load_cards():

        if text in card["name"].lower():
            results.append(card)

    return results