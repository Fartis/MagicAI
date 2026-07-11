from tests.quality.reddit_gauntlet_test import validate_answer


def assert_no_failures(answer: str, forbidden: list[str], label: str):
    failures, _ = validate_answer(
        answer=answer,
        required_all=[],
        required_any=[],
        forbidden=forbidden,
    )

    if failures:
        raise AssertionError(f"{label}: unexpected failures {failures!r}")


def assert_has_failure(answer: str, forbidden: list[str], label: str):
    failures, _ = validate_answer(
        answer=answer,
        required_all=[],
        required_any=[],
        forbidden=forbidden,
    )

    if not failures:
        raise AssertionError(f"{label}: expected a forbidden-term failure")


def test_negated_forbidden_proposition_is_allowed():
    assert_no_failures(
        "No son lo mismo: son categorías distintas.",
        ["son lo mismo"],
        "negated proposition",
    )


def test_affirmed_forbidden_proposition_is_rejected():
    assert_has_failure(
        "Sí, son lo mismo.",
        ["son lo mismo"],
        "affirmed proposition",
    )


def test_negated_counter_claim_is_allowed():
    assert_no_failures(
        "La habilidad no se contrarresta automáticamente.",
        ["se contrarresta automáticamente"],
        "negated counter claim",
    )


def test_forbidden_term_that_starts_with_negation_remains_literal():
    assert_has_failure(
        "No hay diferencia entre ambas habilidades.",
        ["no hay diferencia"],
        "literal negated forbidden term",
    )



def test_negated_singular_does_not_match_plural_verb():
    assert_no_failures(
        "No se activan efectos que reemplacen la destrucción.",
        ["no se activa"],
        "singular forbidden phrase boundary",
    )


def test_literal_singular_forbidden_phrase_still_matches():
    assert_has_failure(
        "Undying no se activa.",
        ["no se activa"],
        "literal singular forbidden phrase",
    )


def main():
    tests = [
        test_negated_forbidden_proposition_is_allowed,
        test_affirmed_forbidden_proposition_is_rejected,
        test_negated_counter_claim_is_allowed,
        test_forbidden_term_that_starts_with_negation_remains_literal,
        test_negated_singular_does_not_match_plural_verb,
        test_literal_singular_forbidden_phrase_still_matches,
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
