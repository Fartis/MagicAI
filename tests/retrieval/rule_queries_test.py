from magicai.retrieval.rule_queries import build_rule_queries


def assert_contains(
    items: list[str],
    expected: list[str],
    label: str,
):

    joined = "\n".join(items).lower()

    missing = [
        item
        for item in expected
        if item.lower() not in joined
    ]

    if missing:

        raise AssertionError(
            f"{label}: missing {missing!r} in queries:\n{joined}"
        )


def assert_not_contains_exact(
    items: list[str],
    forbidden: list[str],
    label: str,
):

    lower_items = [
        item.lower()
        for item in items
    ]

    present = [
        item
        for item in forbidden
        if item.lower() in lower_items
    ]

    if present:

        raise AssertionError(
            f"{label}: unexpected exact queries {present!r} in:\n{items}"
        )


def test_sacrifice_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si lo sacrifico?",
        keywords=[],
        action_terms=[
            "sacrifice",
            "permanent",
            "battlefield",
            "graveyard",
        ],
    )

    assert_contains(
        queries,
        [
            "sacrifice a permanent",
            "battlefield",
            "graveyard",
        ],
        "sacrifice queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "sacrifice",
            "permanent",
            "graveyard",
            "battlefield",
        ],
        "sacrifice queries",
    )


def test_dies_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si muere?",
        keywords=[],
        action_terms=[
            "dies",
            "graveyard",
            "battlefield",
        ],
    )

    assert_contains(
        queries,
        [
            "graveyard from the battlefield",
        ],
        "dies queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "dies",
            "graveyard",
            "battlefield",
        ],
        "dies queries",
    )


def test_exile_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si lo exilio?",
        keywords=[],
        action_terms=[
            "exile",
            "exile zone",
        ],
    )

    assert_contains(
        queries,
        [
            "exile",
            "exile zone",
        ],
        "exile queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "exile",
            "exile zone",
        ],
        "exile queries",
    )


def test_resolution_queries_include_no_priority_during_resolution():

    queries = build_rule_queries(
        question="Si una habilidad está resolviéndose, ¿puedo activar otra habilidad?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "no player has priority",
            "resolving",
        ],
        "resolution priority queries",
    )


def test_end_step_queries_include_apnap_stack():

    queries = build_rule_queries(
        question="Si dos jugadores tienen habilidades al comienzo del paso final, ¿en qué orden van a la pila?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "end step",
            "APNAP",
            "stack",
        ],
        "end step APNAP queries",
    )


def test_mana_ability_queries_include_stack_exception():

    queries = build_rule_queries(
        question="¿Puedo responder a la habilidad de Sol Ring?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "mana abilities",
            "do not use the stack",
            "resolve immediately",
        ],
        "mana ability queries",
    )


def main():

    tests = [
        test_sacrifice_queries_are_specific,
        test_dies_queries_are_specific,
        test_exile_queries_are_specific,
        test_resolution_queries_include_no_priority_during_resolution,
        test_end_step_queries_include_apnap_stack,
        test_mana_ability_queries_include_stack_exception,
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
