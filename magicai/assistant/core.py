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

        if context.cards:

            conversation.active_cards = context.cards.copy()

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