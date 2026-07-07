from magicai.scryfall import (
    search_exact_card,
    search_cards_by_name,
)


def find_card(query: str):

    card = search_exact_card(query)

    if card:
        return {
            "type": "exact",
            "results": [card]
        }

    cards = search_cards_by_name(query)

    return {
        "type": "multiple",
        "results": cards
    }