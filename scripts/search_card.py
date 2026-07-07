#!/usr/bin/env python3

import sys

from magicai.services.card_service import find_card


def print_card(card):

    print("=" * 50)
    print(card["name"])
    print("=" * 50)
    print()

    print("Mana Cost :", card.get("mana_cost"))
    print("Type      :", card.get("type_line"))

    if card.get("power"):
        print("Power     :", card["power"])

    if card.get("toughness"):
        print("Toughness :", card["toughness"])

    print()

    print("Oracle")
    print()

    print(card.get("oracle_text"))

    print()

    print("Commander :", card["legalities"]["commander"])


def main():

    if len(sys.argv) < 2:
        print("Uso:")
        print('python scripts/search_card.py "Young Wolf"')
        return

    search = find_card(sys.argv[1])

    results = search["results"]

    if not results:
        print("Carta no encontrada.")
        return

    if search["type"] == "multiple":

        print(f"{len(results)} cartas encontradas:\n")

        for i, card in enumerate(results[:20], start=1):
            print(f"{i:2d}. {card['name']}")

        if len(results) > 20:
            print("...")

        return

    print_card(results[0])


if __name__ == "__main__":
    main()