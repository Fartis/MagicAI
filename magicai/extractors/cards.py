import re

from magicai.scryfall import load_cards

_cards = None


def _load():

    global _cards

    if _cards is not None:
        return

    cards = load_cards()

    #
    # Preparamos todos los patrones una única vez.
    #

    _cards = []

    names = sorted(
        {card["name"] for card in cards},
        key=len,
        reverse=True,
    )

    for name in names:

        lower = name.lower()

        pattern = re.compile(
            r"\b" + re.escape(lower) + r"\b"
        )

        _cards.append(
            (
                name,
                pattern,
            )
        )


def extract_cards(question: str):

    _load()

    question = question.lower()

    found = []

    for name, pattern in _cards:

        if pattern.search(question):

            found.append(name)

            #
            # Eliminamos únicamente esa coincidencia.
            #

            question = pattern.sub(
                " ",
                question,
            )

    return found