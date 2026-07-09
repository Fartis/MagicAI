from magicai.context import AssistantContext

from magicai.extractors.cards import extract_cards
from magicai.extractors.keywords import extract_keywords
from magicai.extractors.rules import extract_rules

from magicai.llm.intent_parser import parse_intent

from magicai.reasoning import build_reasoning
from magicai.reasoning import extract_action_rule_refs


def build_context(conversation, question: str):

    intent = parse_intent(question)

    language = "es"

    rules = _merge_unique(
        extract_rules(question),
        extract_action_rule_refs(question),
    )

    context = AssistantContext(

        question=question,

        intent=intent["intent"],

        language=language,

        cards=extract_cards(question),

        keywords=extract_keywords(question),

        rules=rules,

        facts=build_reasoning(
            question,
            language=language,
        ),

    )

    #
    # Si no se ha encontrado ninguna carta,
    # reutilizamos la última de la conversación.
    #

    if not context.cards and conversation.active_cards:

        context.cards = [

            card.name

            for card in conversation.active_cards

        ]

    return context


def _merge_unique(*lists):

    result = []

    for items in lists:

        for item in items:

            if item not in result:

                result.append(item)

    return result