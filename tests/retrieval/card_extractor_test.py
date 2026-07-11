from magicai.extractors.cards import _is_mechanic_reference


def test_persist_in_rules_context_is_not_card_reference():
    assert _is_mechanic_reference(
        "Persist",
        "si una criatura 0/0 tiene persist y muere con un contador",
    )


def test_direct_persist_card_question_remains_card_reference():
    assert not _is_mechanic_reference(
        "Persist",
        "¿qué hace persist?",
    )


def test_undying_and_persist_are_mechanics_together():
    assert _is_mechanic_reference(
        "Undying",
        "si una criatura tiene persist y undying a la vez, ¿qué ocurre?",
    )


def main():
    tests = [
        test_persist_in_rules_context_is_not_card_reference,
        test_direct_persist_card_question_remains_card_reference,
        test_undying_and_persist_are_mechanics_together,
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
