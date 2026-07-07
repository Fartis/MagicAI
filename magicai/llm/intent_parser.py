import re


def parse_intent(question: str):

    q = question.lower().strip()

    #
    # Deckbuilding
    #

    if any(word in q for word in [

        "mazo",
        "deck",
        "commander",
        "edh",
        "sideboard",
        "banquillo",
        "modern",
        "pioneer",
        "legacy",
        "standard",

    ]):

        return {
            "intent": "deck"
        }

    #
    # Reglas
    #

    if re.search(r"\b\d+\.\d+\b", q):

        return {
            "intent": "rule"
        }

    #
    # Judge
    #

    if any(word in q for word in [

        "puedo",
        "ocurre",
        "cuando",
        "qué pasa",
        "que pasa",
        "interacción",
        "interaccion",
        "si",
        "muere",
        "sacrifico",
        "exilio",

    ]):

        return {
            "intent": "judge"
        }

    #
    # Carta
    #

    if any(word in q for word in [

        "qué hace",
        "que hace",
        "explícame",
        "explicame",
        "cómo funciona",
        "como funciona",

    ]):

        return {
            "intent": "card"
        }

    return {

        "intent": "unknown"

    }