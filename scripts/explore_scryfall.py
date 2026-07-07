import json
from pprint import pprint

with open("sources/scryfall/oracle-cards.json", encoding="utf-8") as f:
    cards = json.load(f)

print(f"Total cartas: {len(cards)}")

print()

pprint(cards[0])
