from magicai.extractors.cards import extract_cards
from magicai.extractors.keywords import extract_keywords
from magicai.extractors.rules import extract_rules

while True:

    try:
        q = input("> ")
    except EOFError:
        break

    print()

    print("Cards    :", extract_cards(q))

    print("Keywords :", extract_keywords(q))

    print("Rules    :", extract_rules(q))

    print()