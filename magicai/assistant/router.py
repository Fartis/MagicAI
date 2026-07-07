from magicai.services.card_service import find_card
from magicai.services.rule_service import find_rule
from magicai.nlp.parser import parse_question

def answer_question(question: str):

    parsed = parse_question(question)

    #
    # Buscar cartas
    #

    if parsed["intent"] == "card":

        return {
            "kind": "card",
            "data": find_card(parsed["query"])
        }

    #
    # Buscar reglas
    #

    if parsed["intent"] == "rule":

        return {
            "kind": "rule",
            "data": find_rule(parsed["query"])
        }

    #
    # Fallback:
    # primero carta, luego regla
    #

    card = find_card(question)

    if card["results"]:

        return {
            "kind": "card",
            "data": card
        }

    rule = find_rule(question)

    if rule:

        return {
            "kind": "rule",
            "data": rule
        }

    return {
        "kind": "unknown",
        "data": None
    }