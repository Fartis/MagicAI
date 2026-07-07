import json

from magicai.importer import parse_card

with open("sources/scryfall/oracle-cards.json", encoding="utf-8") as f:
    cards = json.load(f)

card = parse_card(cards[0])

print(card)
