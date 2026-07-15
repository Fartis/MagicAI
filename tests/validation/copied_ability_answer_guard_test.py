from magicai.validation.answer import validate_answer


KNOWLEDGE = """
QUESTION

Si copio la habilidad de Braids y sacrifico a Braids con la copia, ¿la habilidad original se resuelve normalmente?

============================================================
CARDS

Braids, Arisen Nightmare
Legendary Creature — Nightmare

At the beginning of your end step, you may sacrifice a permanent. If you do, each opponent may sacrifice a permanent that shares a card type with it.

============================================================
RULES

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

707.10
Choices that are normally made on resolution are not copied.
"""


def test_generic_priority_answer_is_rejected() -> None:
    answer = (
        "Después de que una habilidad resuelva, el jugador activo recibe "
        "prioridad. Los objetos de la pila se resuelven de arriba abajo."
    )
    violations = validate_answer(answer, KNOWLEDGE)

    assert any(
        "copied ability whose source leaves" in violation
        for violation in violations
    )


def test_source_independence_answer_is_accepted() -> None:
    answer = (
        "Sí. La habilidad original se resuelve normalmente y no desaparece "
        "aunque su fuente ya no esté en el campo de batalla."
    )
    violations = validate_answer(answer, KNOWLEDGE)

    assert not any(
        "copied ability whose source leaves" in violation
        for violation in violations
    )


def test_unrelated_stack_question_is_unaffected() -> None:
    knowledge = """
QUESTION

¿Cuándo recibe prioridad el jugador activo?

============================================================
RULES

117.3b
The active player receives priority after a spell or ability resolves.
"""
    violations = validate_answer(
        "El jugador activo recibe prioridad después de que se resuelve una habilidad.",
        knowledge,
    )

    assert not any(
        "copied ability whose source leaves" in violation
        for violation in violations
    )


def main() -> int:
    tests = [
        test_generic_priority_answer_is_rejected,
        test_source_independence_answer_is_accepted,
        test_unrelated_stack_question_is_unaffected,
    ]

    for test in tests:
        test()
        print(f"OK: {test.__name__}")

    print(f"Copied ability answer guard tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
