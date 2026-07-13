import re
import unicodedata

from magicai.context import AssistantContext

from magicai.extractors.cards import extract_cards
from magicai.extractors.keywords import extract_keywords
from magicai.extractors.rules import extract_rules

from magicai.llm.intent_parser import parse_intent

from magicai.reasoning import build_reasoning
from magicai.reasoning import extract_action_search_terms

from magicai.retrieval import build_rule_queries
from magicai.retrieval.rule_intent import looks_like_general_rule_question


_COMPARISON_MARKERS = (
    "mejor que",
    "peor que",
    "compar",
    "diferenc",
    "cada uno",
    "cada una",
    "ambos",
    "ambas",
    "entre ellos",
    "entre ellas",
    "versus",
    " vs ",
)

_FOLLOW_UP_MARKERS = (
    " y ",
    "y si",
    "y persist",
    "ademas",
    "tambien",
    "despues",
    "entonces",
    "esa ",
    "ese ",
    "esta ",
    "este ",
    "aquella",
    "aquello",
    "explicarla",
    "explicarlo",
    "explicarlas",
    "explicarlos",
    "cada uno",
    "cada una",
    "ambos",
    "ambas",
    "diferenc",
    "mejor que",
    "merece la pena jugarlo",
    "merece la pena jugarla",
)

_RULE_FOLLOW_UP_MARKERS = (
    "explicarla",
    "explicarlo",
    "explicame esa",
    "explicame ese",
    "con un ejemplo",
    "por ejemplo",
    "que significa",
    "como funciona eso",
)

_PROCEDURAL_FOLLOW_UP_MARKERS = (
    "cuantas cartas",
    "cuantos",
    "cuantas",
    "despues",
    "entonces",
    "a continuacion",
    "siguiente",
)


def build_context(conversation, question: str):

    intent = parse_intent(question)

    language = "es"

    explicit_cards = extract_cards(question)
    explicit_keywords = extract_keywords(question)
    explicit_rules = extract_rules(question)

    follow_up = _looks_like_follow_up(
        question,
        has_history=len(conversation.history) > 1,
    )
    comparison = _looks_like_comparison(question)

    # A word can be both a card name and a keyword. In an established rules
    # conversation, the keyword interpretation wins unless the user explicitly
    # asks for the card or its Oracle text.
    explicit_cards = _prefer_mechanics_in_rule_context(
        question=question,
        cards=explicit_cards,
        keywords=explicit_keywords,
        active_keywords=conversation.active_keywords,
        follow_up=follow_up,
        comparison=comparison,
    )

    cards = _resolve_cards(
        question=question,
        explicit_cards=explicit_cards,
        active_cards=conversation.active_cards,
        follow_up=follow_up,
        comparison=comparison,
        rule_topic=bool(
            explicit_keywords
            or explicit_rules
            or looks_like_general_rule_question(question)
            or _looks_like_procedural_rule_topic(question)
        ),
    )

    keywords = _resolve_keywords(
        explicit_keywords=explicit_keywords,
        active_keywords=conversation.active_keywords,
        follow_up=follow_up,
        comparison=comparison,
        question=question,
    )

    rules = _resolve_rules(
        explicit_rules=explicit_rules,
        active_rules=conversation.active_rules,
        follow_up=follow_up,
        question=question,
    )

    action_terms = extract_action_search_terms(question)

    direct_rule_queries = build_rule_queries(
        question=question,
        keywords=keywords,
        action_terms=action_terms,
    )

    # A referential request to explain a numbered rule should keep that exact
    # rule as the sole retrieval anchor. Generic words such as "ejemplo" or
    # "explicarla" otherwise retrieve unrelated rules and dilute the source.
    if rules and not explicit_rules and _looks_like_rule_follow_up(question):
        direct_rule_queries = []

    rule_queries, inherited_rule_queries = _resolve_rule_queries(
        question=question,
        direct_queries=direct_rule_queries,
        active_queries=conversation.active_rule_queries,
        explicit_cards=explicit_cards,
        explicit_keywords=explicit_keywords,
        explicit_rules=explicit_rules,
        follow_up=follow_up,
    )

    context = AssistantContext(

        question=question,

        intent=intent["intent"],

        language=language,

        cards=cards,

        keywords=keywords,

        rules=rules,

        rule_queries=rule_queries,

        facts=build_reasoning(
            question,
            language=language,
        ),

        explicit_cards=explicit_cards,

        explicit_keywords=explicit_keywords,

        explicit_rules=explicit_rules,

        follow_up=follow_up,

        comparison=comparison,

        inherited_rule_queries=inherited_rule_queries,

    )

    return context


def _resolve_cards(
    question: str,
    explicit_cards: list[str],
    active_cards: list,
    follow_up: bool,
    comparison: bool,
    rule_topic: bool,
) -> list[str]:

    active_names = _card_names(active_cards)

    if explicit_cards:
        if active_names and comparison:
            return _merge_unique(active_names, explicit_cards)

        return explicit_cards

    if active_names and not rule_topic:
        return active_names

    return []


def _resolve_keywords(
    explicit_keywords: list[str],
    active_keywords: list[str],
    follow_up: bool,
    comparison: bool,
    question: str,
) -> list[str]:

    if explicit_keywords:
        if active_keywords and (follow_up or comparison):
            return _merge_unique(active_keywords, explicit_keywords)

        return explicit_keywords

    if active_keywords and (
        follow_up
        or comparison
        or _looks_like_rule_follow_up(question)
    ):
        return list(active_keywords)

    return []


def _resolve_rules(
    explicit_rules: list[str],
    active_rules: list[str],
    follow_up: bool,
    question: str,
) -> list[str]:

    if explicit_rules:
        return explicit_rules

    if active_rules and (
        _looks_like_rule_follow_up(question)
        or (follow_up and not _has_explicit_topic_words(question))
    ):
        return list(active_rules)

    return []


def _resolve_rule_queries(
    question: str,
    direct_queries: list[str],
    active_queries: list[str],
    explicit_cards: list[str],
    explicit_keywords: list[str],
    explicit_rules: list[str],
    follow_up: bool,
) -> tuple[list[str], bool]:

    has_explicit_topic = bool(
        explicit_cards
        or explicit_keywords
        or explicit_rules
    )

    should_inherit = bool(
        active_queries
        and follow_up
        and not has_explicit_topic
        and (
            not direct_queries
            or _looks_like_procedural_follow_up(question)
            or _looks_like_rule_follow_up(question)
        )
    )

    if not should_inherit:
        return direct_queries, False

    return _merge_unique(active_queries, direct_queries), True


def _prefer_mechanics_in_rule_context(
    question: str,
    cards: list[str],
    keywords: list[str],
    active_keywords: list[str],
    follow_up: bool,
    comparison: bool,
) -> list[str]:

    if not cards or not keywords:
        return cards

    if _looks_like_explicit_card_request(question):
        return cards

    direct_mechanic_question = any(
        marker in _normalize(question)
        for marker in [
            "como funciona",
            "que es",
            "define",
        ]
    )

    if not (
        active_keywords
        or follow_up
        or comparison
        or direct_mechanic_question
        or looks_like_general_rule_question(question)
    ):
        return cards

    keyword_names = {
        _normalize(keyword)
        for keyword in keywords
    }

    return [
        card
        for card in cards
        if _normalize(card) not in keyword_names
    ]


def _looks_like_comparison(question: str) -> bool:
    q = _normalize(question)
    return any(marker in q for marker in _COMPARISON_MARKERS)


def _looks_like_follow_up(question: str, has_history: bool) -> bool:
    if not has_history:
        return False

    q = " " + _normalize(question) + " "

    if any(marker in q for marker in _FOLLOW_UP_MARKERS):
        return True

    # Short questions with an object pronoun are normally continuations of the
    # active topic: "¿Y si lo sacrifico?", "¿Puedo explicarla?", etc.
    if len(q.split()) <= 10 and re.search(
        r"\b(?:lo|la|los|las|le|les|ello|ellos|ellas)\b",
        q,
    ):
        return True

    return False


def _looks_like_rule_follow_up(question: str) -> bool:
    q = _normalize(question)
    return any(marker in q for marker in _RULE_FOLLOW_UP_MARKERS)



def _looks_like_procedural_rule_topic(question: str) -> bool:
    q = _normalize(question)
    return any(
        marker in q
        for marker in [
            "mulligan",
            "mano inicial",
            "opening hand",
            "starting hand",
        ]
    )

def _looks_like_procedural_follow_up(question: str) -> bool:
    q = _normalize(question)
    return any(marker in q for marker in _PROCEDURAL_FOLLOW_UP_MARKERS)


def _looks_like_explicit_card_request(question: str) -> bool:
    q = _normalize(question)
    return any(
        marker in q
        for marker in [
            "carta ",
            "oracle de",
            "texto oracle",
            "que hace",
        ]
    )


def _has_explicit_topic_words(question: str) -> bool:
    q = _normalize(question)
    return any(
        marker in q
        for marker in [
            "regla ",
            "carta ",
            "oracle",
            "mulligan",
            "priority",
            "prioridad",
            "pila",
            "stack",
        ]
    )


def _card_names(cards: list) -> list[str]:
    names = []

    for card in cards:
        name = (
            card.get("name")
            if isinstance(card, dict)
            else getattr(card, "name", None)
        )

        if name and name not in names:
            names.append(name)

    return names


def _merge_unique(first: list[str], second: list[str]) -> list[str]:
    merged = []

    for item in first + second:
        if item and item not in merged:
            merged.append(item)

    return merged


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text
