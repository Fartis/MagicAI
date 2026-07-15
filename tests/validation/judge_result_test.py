from __future__ import annotations

from types import SimpleNamespace

import magicai.answer_generator as answer_generator
from magicai.answer_generator import generate_judge_result
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_clarification_result,
)


def _context(question: str):
    return SimpleNamespace(
        question=question,
        intent="rules",
        cards=[
            SimpleNamespace(
                name="Young Wolf",
                mana_cost="{G}",
                type_line="Creature — Wolf",
                oracle_text=(
                    "Undying (When this creature dies, if it had no +1/+1 "
                    "counters on it, return it to the battlefield under its "
                    "owner's control with a +1/+1 counter on it.)"
                ),
                scryfall_uri="https://scryfall.com/card/example/young-wolf",
            )
        ],
        rulings=[
            {
                "card_name": "Young Wolf",
                "oracle_id": "oracle-young-wolf",
                "source": "wotc",
                "published_at": "2024-01-01",
                "comment": "Example ruling.",
            }
        ],
        rules=[
            {
                "number": "117.2e",
                "title": "No player has priority while a spell or ability is resolving.",
            }
        ],
        rule_queries=["priority during resolution"],
    )


def test_deterministic_result_contains_evidence() -> None:
    knowledge = """
QUESTION

Si una habilidad está resolviéndose, ¿puedo responder antes de que termine?

============================================================
RULES

117.2e
No player has priority while a spell or ability is resolving.
"""
    context = _context("Si una habilidad está resolviéndose, ¿puedo responder?")
    result = generate_judge_result(knowledge, context=context)

    assert result.status is JudgeStatus.ANSWERED
    assert result.origin is JudgeOrigin.DETERMINISTIC_RULE
    assert result.confidence is JudgeConfidence.HIGH
    assert result.schema_version == "1.0"
    assert result.authority == "judge"
    assert result.cards[0].name == "Young Wolf"
    assert result.rules[0].number == "117.2e"
    assert result.rulings[0].card_name == "Young Wolf"
    assert result.rulings[0].source == "wotc"
    assert result.rulings[0].comment == "Example ruling."
    assert result.retrieval_queries == ["priority during resolution"]
    assert result.source_versions.get("comprehensive_rules") == "2026-06-19"
    assert "sources" in result.source_health



def test_copied_ability_interaction_uses_deterministic_judge_route() -> None:
    question = (
        "Si copio la habilidad de Braids y sacrifico a Braids con la copia, "
        "¿la habilidad original se resuelve normalmente?"
    )
    knowledge = """
QUESTION

Si copio la habilidad de Braids y sacrifico a Braids con la copia, ¿la habilidad original se resuelve normalmente?

============================================================
CARDS

Braids, Arisen Nightmare
Mana Cost: {1}{B}{B}
Legendary Creature — Nightmare

At the beginning of your end step, you may sacrifice an artifact, creature, enchantment, land, or planeswalker. If you do, each opponent may sacrifice a permanent that shares a card type with it. For each opponent who doesn't, that player loses 2 life and you draw a card.

============================================================
RULES

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

405.5
The top object on the stack resolves first.

608.2d
Choices made while applying an effect are announced during resolution.

707.10
To copy an ability means to put a copy of it onto the stack. Choices that are normally made on resolution are not copied.
"""
    context = SimpleNamespace(
        question=question,
        intent="rules",
        cards=[
            SimpleNamespace(
                name="Braids, Arisen Nightmare",
                mana_cost="{1}{B}{B}",
                type_line="Legendary Creature — Nightmare",
                oracle_text=(
                    "At the beginning of your end step, you may sacrifice an "
                    "artifact, creature, enchantment, land, or planeswalker. "
                    "If you do, each opponent may sacrifice a permanent that "
                    "shares a card type with it. For each opponent who doesn't, "
                    "that player loses 2 life and you draw a card."
                ),
                scryfall_uri="https://scryfall.com/card/example/braids",
            )
        ],
        rules=[
            {"number": "113.7a", "title": "Ability source independence"},
            {"number": "405.5", "title": "Top object resolves first"},
            {"number": "608.2d", "title": "Choices on resolution"},
            {"number": "707.10", "title": "Copying spells and abilities"},
        ],
        rulings=[],
        rule_queries=["707.10", "113.7a", "608.2d", "405.5"],
    )

    result = generate_judge_result(knowledge, context=context)

    assert result.status is JudgeStatus.ANSWERED
    assert result.origin is JudgeOrigin.DETERMINISTIC_RULE
    assert result.confidence is JudgeConfidence.HIGH
    assert "original se resuelve normalmente" in result.answer
    assert "otro permanente válido" in result.answer

def test_strategy_result_is_explicit() -> None:
    knowledge = """
QUESTION

¿Merece la pena jugar Sol Ring?

============================================================
CARDS

Sol Ring
Mana Cost: {1}
Artifact

{T}: Add {C}{C}.
"""
    context = SimpleNamespace(
        question="¿Merece la pena jugar Sol Ring?",
        intent="strategy",
        cards=[
            SimpleNamespace(
                name="Sol Ring",
                mana_cost="{1}",
                type_line="Artifact",
                oracle_text="{T}: Add {C}{C}.",
                scryfall_uri="https://scryfall.com/card/example/sol-ring",
            )
        ],
        rules=[],
        rulings=[],
        rule_queries=[],
    )
    result = generate_judge_result(knowledge, context=context)

    assert result.status is JudgeStatus.STRATEGY_REQUIRED
    assert result.origin is JudgeOrigin.STRATEGY_BOUNDARY
    assert result.confidence is JudgeConfidence.HIGH
    assert result.warnings


def test_safe_fallback_reports_insufficient_evidence() -> None:
    original_generate = answer_generator.generate
    answer_generator.generate = lambda *_args, **_kwargs: ""

    try:
        result = generate_judge_result(
            "QUESTION\n\n¿Qué ocurre aquí?\n",
            context=SimpleNamespace(
                question="¿Qué ocurre aquí?",
                intent="rules",
                cards=[],
                rules=[],
                rulings=[],
                rule_queries=[],
            ),
        )
    finally:
        answer_generator.generate = original_generate

    assert result.status is JudgeStatus.INSUFFICIENT_EVIDENCE
    assert result.origin is JudgeOrigin.SAFE_FALLBACK
    assert result.confidence is JudgeConfidence.LOW
    assert result.validation_attempts == 2


def test_clarification_result_serializes_legacy_and_structured_fields() -> None:
    result = build_clarification_result(
        question="¿Qué hace Squee?",
        answer="¿A cuál te refieres?",
        candidates=["Squee, Goblin Nabob", "Squee, the Immortal"],
    )
    payload = result.to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["answer"] == "¿A cuál te refieres?"
    assert payload["status"] == "needs_clarification"
    assert payload["origin"] == "disambiguation"
    assert [card["name"] for card in payload["cards"]] == [
        "Squee, Goblin Nabob",
        "Squee, the Immortal",
    ]


def main() -> int:
    tests = [
        test_deterministic_result_contains_evidence,
        test_copied_ability_interaction_uses_deterministic_judge_route,
        test_strategy_result_is_explicit,
        test_safe_fallback_reports_insufficient_evidence,
        test_clarification_result_serializes_legacy_and_structured_fields,
    ]

    for test in tests:
        test()
        print(f"OK: {test.__name__}")

    print(f"JudgeResult tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
