from types import SimpleNamespace

import magicai.context_builder as context_builder
from magicai.assistant.core import _update_conversation_state
from magicai.context import AssistantContext
from magicai.conversation import Conversation


def _conversation_with_history() -> Conversation:
    conversation = Conversation()
    conversation.add_user_message("Pregunta anterior")
    conversation.add_assistant_message("Respuesta anterior")
    return conversation


def _run_builder(
    conversation: Conversation,
    question: str,
    *,
    cards: list[str] | None = None,
    keywords: list[str] | None = None,
    rules: list[str] | None = None,
    queries: list[str] | None = None,
):
    originals = {
        "extract_cards": context_builder.extract_cards,
        "extract_keywords": context_builder.extract_keywords,
        "extract_rules": context_builder.extract_rules,
        "parse_intent": context_builder.parse_intent,
        "extract_action_search_terms": context_builder.extract_action_search_terms,
        "build_rule_queries": context_builder.build_rule_queries,
        "build_reasoning": context_builder.build_reasoning,
    }

    context_builder.extract_cards = lambda _question: list(cards or [])
    context_builder.extract_keywords = lambda _question: list(keywords or [])
    context_builder.extract_rules = lambda _question: list(rules or [])
    context_builder.parse_intent = lambda _question: {"intent": "judge"}
    context_builder.extract_action_search_terms = lambda _question: []
    context_builder.build_rule_queries = (
        lambda question, keywords, action_terms: list(queries or [])
    )
    context_builder.build_reasoning = lambda _question, language="es": []

    try:
        return context_builder.build_context(conversation, question)
    finally:
        for name, value in originals.items():
            setattr(context_builder, name, value)


def test_comparison_merges_new_card_with_active_card():
    conversation = _conversation_with_history()
    conversation.active_cards = [
        SimpleNamespace(name="Korvold, Fae-Cursed King"),
    ]

    context = _run_builder(
        conversation,
        "¿Es mejor que Prossh?",
        cards=["Prossh, Skyraider of Kher"],
    )

    expected = [
        "Korvold, Fae-Cursed King",
        "Prossh, Skyraider of Kher",
    ]

    if context.cards != expected:
        raise AssertionError(f"comparison cards: {context.cards!r}")


def test_explicit_topic_switch_replaces_active_card():
    conversation = _conversation_with_history()
    conversation.active_cards = [SimpleNamespace(name="Young Wolf")]

    context = _run_builder(
        conversation,
        "¿Qué hace Sol Ring?",
        cards=["Sol Ring"],
    )

    if context.cards != ["Sol Ring"]:
        raise AssertionError(f"topic switch cards: {context.cards!r}")



def test_implicit_card_followup_keeps_active_card():
    conversation = _conversation_with_history()
    conversation.active_cards = [
        SimpleNamespace(name="Prossh, Skyraider of Kher"),
    ]

    context = _run_builder(
        conversation,
        "¿Cuántos kobolds crea?",
    )

    if context.cards != ["Prossh, Skyraider of Kher"]:
        raise AssertionError(f"implicit card follow-up: {context.cards!r}")


def test_explicit_procedural_topic_clears_stale_card():
    conversation = _conversation_with_history()
    conversation.active_cards = [SimpleNamespace(name="Sol Ring")]

    context = _run_builder(
        conversation,
        "Explícame el London Mulligan.",
        queries=["mulligan", "starting hand size"],
    )

    if context.cards:
        raise AssertionError(f"procedural topic kept stale card: {context.cards!r}")


def test_direct_mechanic_question_beats_homonymous_card():
    conversation = Conversation()
    conversation.add_user_message("¿Cómo funciona Persist?")

    context = _run_builder(
        conversation,
        "¿Cómo funciona Persist?",
        cards=["Persist"],
        keywords=["persist"],
    )

    if context.cards:
        raise AssertionError(f"direct mechanic resolved as card: {context.cards!r}")

    if context.keywords != ["persist"]:
        raise AssertionError(f"direct mechanic keyword: {context.keywords!r}")

def test_keyword_followup_beats_homonymous_card():
    conversation = _conversation_with_history()
    conversation.active_keywords = ["undying"]

    context = _run_builder(
        conversation,
        "¿Y Persist?",
        cards=["Persist"],
        keywords=["persist"],
    )

    if context.cards:
        raise AssertionError(f"Persist card should be filtered: {context.cards!r}")

    if context.keywords != ["undying", "persist"]:
        raise AssertionError(f"keyword continuity: {context.keywords!r}")


def test_numbered_rule_is_inherited_by_referential_followup():
    conversation = _conversation_with_history()
    conversation.active_rules = ["702.93"]

    context = _run_builder(
        conversation,
        "¿Puedes explicarla con un ejemplo?",
    )

    if context.rules != ["702.93"]:
        raise AssertionError(f"rule continuity: {context.rules!r}")


def test_procedural_rule_queries_are_inherited():
    conversation = _conversation_with_history()
    conversation.active_rule_queries = [
        "mulligan",
        "starting hand size",
    ]

    context = _run_builder(
        conversation,
        "¿Cuántas cartas robo después?",
    )

    if context.rule_queries != ["mulligan", "starting hand size"]:
        raise AssertionError(f"procedural continuity: {context.rule_queries!r}")

    if not context.inherited_rule_queries:
        raise AssertionError("inherited_rule_queries should be true")


def test_enriched_context_updates_shared_conversation_state():
    conversation = Conversation()
    context = AssistantContext(
        question="¿Qué diferencias tienen?",
        intent="judge",
        cards=[SimpleNamespace(name="Young Wolf")],
        keywords=["undying", "persist"],
        rules=[
            {"number": "702.93", "title": "Undying"},
            {"number": "702.79", "title": "Persist"},
        ],
        rule_queries=["undying", "persist"],
    )

    _update_conversation_state(conversation, context)

    if [card.name for card in conversation.active_cards] != ["Young Wolf"]:
        raise AssertionError("active cards were not persisted")

    if conversation.active_keywords != ["undying", "persist"]:
        raise AssertionError("active keywords were not persisted")

    if conversation.active_rules != ["702.93", "702.79"]:
        raise AssertionError(f"active rules: {conversation.active_rules!r}")

    if conversation.active_rule_queries != ["undying", "persist"]:
        raise AssertionError("active rule queries were not persisted")


def main():
    tests = [
        test_comparison_merges_new_card_with_active_card,
        test_explicit_topic_switch_replaces_active_card,
        test_implicit_card_followup_keeps_active_card,
        test_explicit_procedural_topic_clears_stale_card,
        test_direct_mechanic_question_beats_homonymous_card,
        test_keyword_followup_beats_homonymous_card,
        test_numbered_rule_is_inherited_by_referential_followup,
        test_procedural_rule_queries_are_inherited,
        test_enriched_context_updates_shared_conversation_state,
    ]

    errors = []

    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}")
            print(exc)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Tests : {len(tests)}")
    print(f"Errors: {len(errors)}")

    if errors:
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
