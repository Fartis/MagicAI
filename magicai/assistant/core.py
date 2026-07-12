import time

from magicai.context_builder import build_context
from magicai.context_enricher import enrich
from magicai.knowledge_builder import build_knowledge
from magicai.answer_generator import generate_answer
from magicai.conversation.disambiguation import handle_card_disambiguation


class MagicAI:

    def ask(self, conversation, question: str) -> str:

        total = time.perf_counter()

        disambiguation_answer, resolved_question = handle_card_disambiguation(
            conversation,
            question,
        )

        if disambiguation_answer:

            conversation.add_user_message(question)
            conversation.add_assistant_message(disambiguation_answer)

            return disambiguation_answer

        if resolved_question:

            question = resolved_question

        #
        # Guardar pregunta
        #

        conversation.add_user_message(question)

        #
        # Context Builder
        #

        t = time.perf_counter()

        context = build_context(
            conversation,
            question,
        )

        print(
            f"Context Builder : {time.perf_counter()-t:.3f}s"
        )

        #
        # Enricher
        #

        t = time.perf_counter()

        context = enrich(context)

        print(
            f"Context Enricher: {time.perf_counter()-t:.3f}s"
        )

        #
        # Conversación
        #

        _update_conversation_state(
            conversation,
            context,
        )

        #
        # Knowledge Builder
        #

        t = time.perf_counter()

        knowledge = build_knowledge(context)

        print(
            f"Knowledge Builder: {time.perf_counter()-t:.3f}s"
        )

        #
        # LLM
        #

        t = time.perf_counter()

        answer = generate_answer(knowledge)

        print(
            f"LLM              : {time.perf_counter()-t:.3f}s"
        )

        #
        # Historial
        #

        conversation.add_assistant_message(answer)

        print(
            f"TOTAL            : {time.perf_counter()-total:.3f}s"
        )

        print()

        return answer

def _update_conversation_state(conversation, context) -> None:
    """Persist only source identifiers and resolved entities in the session."""

    conversation.active_cards = context.cards.copy()
    conversation.active_keywords = list(context.keywords)
    conversation.active_rules = _rule_identifiers(context.rules)
    conversation.active_rule_queries = list(context.rule_queries)
    conversation.last_intent = context.intent


def _rule_identifiers(rules: list) -> list[str]:
    identifiers: list[str] = []

    for rule in rules:
        if isinstance(rule, str):
            identifier = rule
        else:
            identifier = rule.get("number") or rule.get("title")

        if identifier and identifier not in identifiers:
            identifiers.append(str(identifier))

    return identifiers
