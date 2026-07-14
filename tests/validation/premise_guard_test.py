from __future__ import annotations

from types import SimpleNamespace

from magicai.answer_generator import generate_judge_result
from magicai.validation.premise_guard import render_false_premise_answer
from magicai.judge_result import JudgeOrigin, JudgeStatus


def _card(name: str, oracle_text: str):
    return SimpleNamespace(
        name=name,
        oracle_id="oracle-test",
        mana_cost="{3}{B}{R}{G}",
        type_line="Legendary Creature — Dragon",
        oracle_text=oracle_text,
        scryfall_uri="https://example.invalid/card",
    )


def test_cast_trigger_false_premise_is_corrected() -> None:
    question = (
        "Como Prossh crea Kobolds cuando entra al campo de batalla, "
        "¿cuántos crea si lo reanimo?"
    )
    context = SimpleNamespace(
        question=question,
        intent="rules",
        cards=[
            _card(
                "Prossh, Skyraider of Kher",
                "When you cast this spell, create X 0/1 red Kobold creature tokens.",
            )
        ],
        rules=[],
        rulings=[],
        rule_queries=[],
    )
    knowledge = "QUESTION\n\n" + question + "\n"
    result = generate_judge_result(knowledge, context=context)

    assert result.status is JudgeStatus.FALSE_PREMISE
    assert result.origin is JudgeOrigin.PREMISE_GUARD
    assert result.confidence.value == "high"
    assert "premisa no es correcta" in result.answer.lower()
    assert "lanzas" in result.answer.lower()
    assert result.warnings


def test_question_without_asserted_premise_is_not_intercepted() -> None:
    question = "¿Qué ocurre si Prossh vuelve a entrar al campo de batalla?"
    context = SimpleNamespace(
        question=question,
        intent="rules",
        cards=[
            _card(
                "Prossh, Skyraider of Kher",
                "When you cast this spell, create X 0/1 red Kobold creature tokens.",
            )
        ],
        rules=[],
        rulings=[],
        rule_queries=[],
    )
    knowledge = "QUESTION\n\n" + question + "\n"
    correction = render_false_premise_answer(knowledge, context=context)

    assert correction is None



def test_exact_self_sacrifice_sequence_is_corrected() -> None:
    question = (
        "Activo en Tormod's Crypt la habilidad «{T}, Sacrifice Tormod's Crypt: "
        "Exile target player's graveyard.» y después destruyen ese permanente. "
        "¿La habilidad desaparece?"
    )
    context = SimpleNamespace(
        question=question,
        cards=[_card(
            "Tormod's Crypt",
            "{T}, Sacrifice Tormod's Crypt: Exile target player's graveyard.",
        )],
    )
    correction = render_false_premise_answer("QUESTION\n\n" + question, context=context)
    assert correction is not None
    assert "no es posible" in correction.answer.lower()
    assert "coste retira" in correction.answer.lower()


def test_exact_graveyard_source_sequence_is_corrected() -> None:
    question = (
        "Activo en Grave Test la habilidad «{2}: Draw a card. Activate only "
        "if this card is in your graveyard.» y después destruyen la fuente. "
        "¿Qué ocurre?"
    )
    context = SimpleNamespace(
        question=question,
        cards=[_card(
            "Grave Test",
            "{2}: Draw a card. Activate only if this card is in your graveyard.",
        )],
    )
    correction = render_false_premise_answer("QUESTION\n\n" + question, context=context)
    assert correction is not None
    assert "desde el cementerio" in correction.answer.lower()


def test_valid_exact_battlefield_source_is_not_intercepted() -> None:
    question = (
        "Activo en Safe Source la habilidad «{T}: Draw a card.» y después "
        "destruyen ese permanente. ¿La habilidad desaparece?"
    )
    context = SimpleNamespace(
        question=question,
        cards=[_card("Safe Source", "{T}: Draw a card.")],
    )
    correction = render_false_premise_answer("QUESTION\n\n" + question, context=context)
    assert correction is None

def main() -> int:
    tests = [
        test_cast_trigger_false_premise_is_corrected,
        test_question_without_asserted_premise_is_not_intercepted,
        test_exact_self_sacrifice_sequence_is_corrected,
        test_exact_graveyard_source_sequence_is_corrected,
        test_valid_exact_battlefield_source_is_not_intercepted,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Premise guard tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
