from magicai.context import AssistantContext

from magicai.extractors.cards import extract_cards
from magicai.extractors.keywords import extract_keywords
from magicai.extractors.rules import extract_rules

from magicai.llm.intent_parser import parse_intent


def build_context(conversation, question: str):

    intent = parse_intent(question)

    context = AssistantContext(

        question=question,

        intent=intent["intent"],

        cards=extract_cards(question),

        keywords=extract_keywords(question),

        rules=extract_rules(question)

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