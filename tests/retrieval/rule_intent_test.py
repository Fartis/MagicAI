from magicai.retrieval.rule_intent import (
    is_common_language_card_alias,
    looks_like_general_rule_question,
)


def test_general_rule_question_detects_resolution():

    assert looks_like_general_rule_question(
        "Si una habilidad está resolviéndose y pone una carta en mesa, ¿puedo activar esa carta?"
    )


def test_general_rule_question_detects_end_step():

    assert looks_like_general_rule_question(
        "Si dos jugadores tienen habilidades al comienzo del paso final, ¿en qué orden van a la pila?"
    )


def test_common_language_alias_blocks_mesa():

    assert is_common_language_card_alias(
        "mesa",
        "Si una habilidad pone una carta en mesa, ¿puedo responder?",
    )


def test_common_language_alias_blocks_final():

    assert is_common_language_card_alias(
        "final",
        "Si dos jugadores tienen habilidades al comienzo del paso final, ¿en qué orden van a la pila?",
    )



def test_common_language_alias_blocks_sin():

    assert is_common_language_card_alias(
        "sin",
        "Si hay dos objetos en la pila, ¿se resuelven sin dar prioridad?",
    )

def main():

    tests = [
        test_general_rule_question_detects_resolution,
        test_general_rule_question_detects_end_step,
        test_common_language_alias_blocks_mesa,
        test_common_language_alias_blocks_final,
        test_common_language_alias_blocks_sin,
    ]

    errors = []

    for test in tests:

        try:

            test()

            print(f"OK: {test.__name__}")

        except Exception as exc:

            errors.append(
                (
                    test.__name__,
                    exc,
                )
            )

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
