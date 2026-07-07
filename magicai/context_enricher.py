from magicai.repositories.card_repository import CardRepository
from magicai.repositories.rule_repository import RuleRepository


def enrich(context):

    card_repo = CardRepository()
    rule_repo = RuleRepository()

    #
    # Cartas
    #

    enriched_cards = []

    for name in context.cards:

        card = card_repo.find_by_name(name)

        if card is not None:
            enriched_cards.append(card)

    context.cards = enriched_cards

    #
    # Reglas
    #

    enriched_rules = []

    # Reglas detectadas por número
    for number in context.rules:

        rule = rule_repo.find_by_keyword(number)

        if rule is not None:
            enriched_rules.append(rule)

    # Reglas detectadas por keyword
    for keyword in context.keywords:

        rule = rule_repo.find_by_keyword(keyword)

        if rule is not None and rule not in enriched_rules:
            enriched_rules.append(rule)

    context.rules = enriched_rules

    return context