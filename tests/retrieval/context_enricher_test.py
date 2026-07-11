from magicai.context_enricher import _looks_like_continuous_effect_question
from magicai.context_enricher import _merge_unique_queries


def test_oracle_queries_are_prioritized_without_duplicates():
    merged = _merge_unique_queries(
        preferred=[
            "activated ability",
            "mana ability",
        ],
        existing=[
            "117",
            "mana ability",
            "in response priority stack resolves",
        ],
    )

    expected = [
        "activated ability",
        "mana ability",
        "117",
        "in response priority stack resolves",
    ]

    if merged != expected:
        raise AssertionError(
            f"unexpected query priority:\nexpected={expected!r}\nactual={merged!r}"
        )




def test_bare_power_toughness_is_not_enough_for_continuous_focus():
    question = (
        "Una criatura base 0/0 con Persist vuelve del cementerio con su "
        "contador. ¿Qué comprueba el juego después?"
    )

    if _looks_like_continuous_effect_question(question.lower()):
        raise AssertionError(
            "bare 0/0 Persist question must not request continuous-effect Oracle queries"
        )


def test_characteristic_change_with_power_toughness_keeps_continuous_focus():
    question = (
        "Bello convierte un encantamiento en una criatura 4/4 y después "
        "pierde sus habilidades. ¿Sigue siendo criatura?"
    )

    if not _looks_like_continuous_effect_question(question.lower()):
        raise AssertionError(
            "type-changing 4/4 question must keep continuous-effect focus"
        )

def main():
    tests = [
        test_oracle_queries_are_prioritized_without_duplicates,
        test_bare_power_toughness_is_not_enough_for_continuous_focus,
        test_characteristic_change_with_power_toughness_keeps_continuous_focus,
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
