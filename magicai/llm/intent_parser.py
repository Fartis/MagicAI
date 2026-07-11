import re


def parse_intent(question: str):

    q = question.lower().strip()

    #
    # Judge / reglas aplicadas.
    #
    # Se evalúa antes que deckbuilding. Mencionar que una carta es el
    # comandante no convierte una pregunta de interacción en una consulta de
    # construcción de mazo.
    #

    if _looks_like_judge_question(q):

        return {
            "intent": "judge"
        }

    #
    # Consulta explícita de una regla numerada.
    #

    if re.search(r"\b\d+\.\d+\b", q):

        return {
            "intent": "rule"
        }

    #
    # Carta.
    #

    if any(phrase in q for phrase in [

        "qué hace",
        "que hace",
        "explícame",
        "explicame",
        "cómo funciona",
        "como funciona",
        "texto oracle",
        "oracle de",

    ]):

        return {
            "intent": "card"
        }

    #
    # Deckbuilding / estrategia.
    #

    if _looks_like_deck_question(q):

        return {
            "intent": "deck"
        }

    return {

        "intent": "unknown"

    }


def _looks_like_judge_question(q: str) -> bool:

    phrases = [
        "puedo",
        "puede atacar",
        "sigue siendo",
        "deja de ser",
        "vuelve a ser",
        "qué ocurre",
        "que ocurre",
        "qué pasa",
        "que pasa",
        "interacción",
        "interaccion",
        "cuando",
        "muere",
        "sacrifico",
        "exilio",
        "pierde todas las habilidades",
        "pierde habilidades",
        "gana habilidades",
    ]

    if any(phrase in q for phrase in phrases):
        return True

    # "si" debe tratarse como palabra, no como subcadena de "sigue",
    # "sirve", "sin", etc.
    return re.search(r"\bsi\b", q) is not None


def _looks_like_deck_question(q: str) -> bool:

    phrases = [
        "construir un mazo",
        "crear un mazo",
        "mejorar mi mazo",
        "mejorar el mazo",
        "qué carta añadir",
        "que carta añadir",
        "qué carta quitar",
        "que carta quitar",
        "lista de mazo",
        "decklist",
        "curva de maná",
        "curva de mana",
        "sideboard",
        "banquillo",
        "qué comandante elegir",
        "que comandante elegir",
        "qué comandante usar",
        "que comandante usar",
    ]

    if any(phrase in q for phrase in phrases):
        return True

    # Términos de formato por sí solos no bastan; deben aparecer junto a una
    # intención de construir, valorar o modificar una lista.
    format_markers = [
        "commander",
        "edh",
        "modern",
        "pioneer",
        "legacy",
        "standard",
    ]

    deck_actions = [
        "mazo",
        "deck",
        "lista",
        "añadir",
        "quitar",
        "cambiar",
        "mejorar",
        "construir",
        "crear",
        "sideboard",
        "banquillo",
    ]

    return (
        any(marker in q for marker in format_markers)
        and any(action in q for action in deck_actions)
    )
