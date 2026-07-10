from magicai.extractors.keywords import extract_keywords

from magicai.repositories.card_repository import CardRepository
from magicai.repositories.rule_repository import RuleRepository
from magicai.sources.symbology import extract_symbols_from_card
from magicai.retrieval import build_oracle_rule_queries


MAX_RULES = 8


def enrich(context):

    card_repo = CardRepository()
    rule_repo = RuleRepository()

    enriched_cards = []

    for name in context.cards:

        card = card_repo.find_by_name(name)

        if card is not None:
            enriched_cards.append(card)

    context.cards = enriched_cards

    symbols = []

    for card in context.cards:

        for symbol in extract_symbols_from_card(card):

            _add_unique_symbol(
                symbols,
                symbol,
            )

    context.symbols = symbols

    if _needs_oracle_rule_queries(context):

        oracle_rule_queries = []

        for card in context.cards:

            for query in build_oracle_rule_queries(card.oracle_text or ""):

                _add_unique_query(
                    oracle_rule_queries,
                    query,
                )

        # Los conceptos derivados del Oracle recuperado son evidencia más
        # específica que las expansiones léxicas de la pregunta. Se priorizan
        # para que el límite MAX_RULES no los deje fuera por ruido anterior.
        context.rule_queries = _merge_unique_queries(
            oracle_rule_queries,
            context.rule_queries,
        )

    enriched_rules = []

    #
    # Reglas explícitas pedidas por el usuario.
    #

    for number in context.rules:

        rule = rule_repo.find_by_keyword(number)

        if rule is not None:
            _add_unique_rule(enriched_rules, rule)

    #
    # Keywords detectadas en la pregunta.
    #

    for keyword in context.keywords:

        rule = rule_repo.find_by_keyword(keyword)

        if rule is not None:
            _add_unique_rule(enriched_rules, rule)

    #
    # Keywords detectadas en el Oracle text de las cartas recuperadas.
    #
    # Esto es clave: si el texto oficial de una carta contiene Undying,
    # Flying, Haste, etc., podemos traer la regla correspondiente sin que
    # el usuario tenga que nombrarla explícitamente.
    #

    if not _is_basic_card_question(context):

        for card in context.cards:

            for keyword in extract_keywords(card.oracle_text or ""):

                rule = rule_repo.find_by_keyword(keyword)

                if rule is not None:
                    _add_unique_rule(enriched_rules, rule)

    #
    # Búsqueda conceptual en Comprehensive Rules.
    #
    # Limitamos a 3 por query y a MAX_RULES total para evitar ruido.
    #

    for query in context.rule_queries:

        for rule in rule_repo.search(query, limit=1):

            _add_unique_rule(enriched_rules, rule)

            if len(enriched_rules) >= MAX_RULES:

                break

        if len(enriched_rules) >= MAX_RULES:

            break

    context.rules = enriched_rules

    return context


def _add_unique_rule(items: list, rule):

    number = rule.get("number")

    for item in items:

        if item.get("number") == number:

            return

    items.append(rule)


def _add_unique_symbol(items: list[dict], symbol: dict):

    code = symbol.get("symbol")

    for item in items:

        if item.get("symbol") == code:

            return

    items.append(symbol)


def _is_basic_card_question(context) -> bool:

    q = context.question.lower()

    if not context.cards:

        return False

    basic_markers = [
        "qué hace",
        "que hace",
        "explícame qué hace",
        "explicame que hace",
        "what does",
    ]

    return any(
        marker in q
        for marker in basic_markers
    )

def _add_unique_query(items: list[str], query: str):

    if query and query not in items:

        items.append(query)

def _needs_oracle_rule_queries(context) -> bool:

    q = context.question.lower()

    markers = [
        "habilidad",
        "habilidades",
        "ability",
        "abilities",
        "habilidad activada",
        "habilidades activadas",
        "habilidad disparada",
        "habilidad desencadenada",
        "habilidades disparadas",
        "activar",
        "activa",
        "se dispara",
        "disparada",
        "desencadenada",
        "responder",
        "respuesta",
        "activated ability",
        "activated abilities",
        "triggered ability",
        "triggered abilities",
        "mana ability",
        "habilidad de maná",
        "habilidad de mana",
    ]

    return any(
        marker in q
        for marker in markers
    )

def _merge_unique_queries(
    preferred: list[str],
    existing: list[str],
) -> list[str]:

    merged = []

    for query in preferred + existing:

        _add_unique_query(
            merged,
            query,
        )

    return merged
