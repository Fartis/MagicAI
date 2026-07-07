import re
from magicai.nlp.normalize import normalize

CARD_PATTERNS = [

    r"^qué hace (.+)$",
    r"^que hace (.+)$",
    r"^what does (.+) do\??$",

]


RULE_PATTERNS = [

    r"^qué significa (.+)$",
    r"^que significa (.+)$",
    r"^how does (.+) work\??$",

]


def parse_question(question: str):
    question = normalize(question)
    question = question.strip()

    #
    # Buscar preguntas sobre cartas
    #

    for pattern in CARD_PATTERNS:

        m = re.match(pattern, question, re.IGNORECASE)

        if m:

            return {
                "intent": "card",
                "query": m.group(1)
            }

    #
    # Buscar preguntas sobre reglas
    #

    for pattern in RULE_PATTERNS:

        m = re.match(pattern, question, re.IGNORECASE)

        if m:

            return {
                "intent": "rule",
                "query": m.group(1)
            }

    #
    # Si no sabemos...
    #

    return {
        "intent": "unknown",
        "query": question
    }