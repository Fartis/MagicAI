from magicai.context import AssistantContext

from magicai.extractors.cards import extract_cards
from magicai.extractors.keywords import extract_keywords
from magicai.extractors.rules import extract_rules

from magicai.llm.intent_parser import parse_intent

from magicai.reasoning import build_reasoning
from magicai.reasoning import extract_action_search_terms

from magicai.retrieval import build_rule_queries


def build_context(conversation, question: str):

    intent = parse_intent(question)

    language = "es"

    keywords = extract_keywords(question)

    action_terms = extract_action_search_terms(question)

    context = AssistantContext(

        question=question,

        intent=intent["intent"],

        language=language,

        cards=extract_cards(question),

        keywords=keywords,

        rules=extract_rules(question),

        rule_queries=build_rule_queries(
            question=question,
            keywords=keywords,
            action_terms=action_terms,
        ),

        facts=build_reasoning(
            question,
            language=language,
        ),

    )

    if not context.cards and conversation.active_cards:

        context.cards = [
            card.name
            for card in conversation.active_cards
        ]

    return context
