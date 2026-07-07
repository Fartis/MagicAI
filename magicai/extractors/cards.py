import re

from magicai.scryfall import load_cards

_cards = None


def _load():

    global _cards

    if _cards is not None:
        return

    cards = load_cards()

    #
    # Obtenemos todos los nombres únicos y los ordenamos
    # del más largo al más corto.
    #

    _cards = sorted(
        {card["name"] for card in cards},
        key=len,
        reverse=True
    )


def extract_cards(question: str):

    _load()

    question = question.lower()

    found = []

    for name in _cards:

        lower_name = name.lower()

        #
        # Coincidencia únicamente por palabra completa
        #

        pattern = r"\b" + re.escape(lower_name) + r"\b"

        if re.search(pattern, question):

            found.append(name)

            #
            # Eliminamos únicamente esa coincidencia
            #

            question = re.sub(
                pattern,
                " ",
                question,
            )

    return found