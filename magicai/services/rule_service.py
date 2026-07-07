from magicai.rules_parser import parse_rules

_rules = None


def load():

    global _rules

    if _rules is None:
        _rules = parse_rules()

    return _rules


def find_rule(query: str):

    query = query.strip().lower()

    rules = load()

    #
    # Buscar por número
    #

    if query in rules:
        return rules[query]

    #
    # Buscar por nombre
    #

    for number, section in rules.items():

        if query == section["title"].lower():

            return section

    #
    # Buscar por texto
    #

    for number, section in rules.items():

        for rule_number, text in section["rules"]:

            if query in text.lower():

                return section

    return None