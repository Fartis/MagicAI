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


def main() -> int:
    tests = [
        test_cast_trigger_false_premise_is_corrected,
        test_question_without_asserted_premise_is_not_intercepted,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Premise guard tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
