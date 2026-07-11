from magicai.validation.fallback import build_fallback_answer


def assert_contains(
    text: str,
    expected: list[str],
    label: str,
):

    lower = text.lower()

    missing = [
        item
        for item in expected
        if item.lower() not in lower
    ]

    if missing:

        raise AssertionError(
            f"{label}: missing {missing!r} in answer:\n{text}"
        )


def assert_not_contains(
    text: str,
    forbidden: list[str],
    label: str,
):

    lower = text.lower()

    present = [
        item
        for item in forbidden
        if item.lower() in lower
    ]

    if present:

        raise AssertionError(
            f"{label}: unexpected {present!r} in answer:\n{text}"
        )


def test_undying_sacrifice():

    knowledge = """
QUESTION

¿Y si lo sacrifico?

============================================================
CARDS

Young Wolf
Mana Cost: {G}
Creature — Wolf

Undying (When this creature dies, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.)

============================================================
RULES

702.93a
Undying is a triggered ability. “Undying” means “When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield under its owner’s control with a +1/+1 counter on it.”

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner’s graveyard.

700.4
The term dies means “is put into a graveyard from the battlefield.”
"""

    answer = build_fallback_answer(
        knowledge,
        ["test"],
    )

    assert_contains(
        answer,
        [
            "sacrificar una criatura",
            "cementerio desde el campo de batalla",
            "muere",
            "+1/+1",
            "vuelve al campo de batalla",
        ],
        "Undying sacrifice fallback",
    )

    assert_not_contains(
        answer,
        [
            "No he podido generar",
            "Food",
            "forage",
            "no se activa",
        ],
        "Undying sacrifice fallback",
    )


def test_persist_dies():

    knowledge = """
QUESTION

¿Y si una criatura con Persist muere?

============================================================
CARDS

Safehold Elite
Mana Cost: {1}{G/W}
Creature — Elf Scout

Persist (When this creature dies, if it had no -1/-1 counters on it, return it to the battlefield under its owner's control with a -1/-1 counter on it.)
"""

    answer = build_fallback_answer(
        knowledge,
        ["test"],
    )

    assert_contains(
        answer,
        [
            "Persist",
            "cuando esta criatura muere",
            "si no tenía contadores -1/-1",
            "vuelve al campo de batalla",
            "contador -1/-1",
        ],
        "Persist dies fallback",
    )

    assert_not_contains(
        answer,
        [
            "+1/+1",
            "Undying",
            "No he podido generar",
        ],
        "Persist dies fallback",
    )


def test_sacrifice_permanent_counter_draw():

    knowledge = """
QUESTION

¿Qué ocurre si sacrifico un permanente con Korvold, Fae-Cursed King en mesa?

============================================================
CARDS

Korvold, Fae-Cursed King
Mana Cost: {2}{B}{R}{G}
Legendary Creature — Dragon Noble

Flying
Whenever you sacrifice a permanent, put a +1/+1 counter on Korvold and draw a card.
"""

    answer = build_fallback_answer(
        knowledge,
        ["test"],
    )

    assert_contains(
        answer,
        [
            "sacrificas un permanente",
            "contador +1/+1",
            "Korvold",
            "robas una carta",
        ],
        "Sacrifice permanent counter draw fallback",
    )

    assert_not_contains(
        answer,
        [
            "Food",
            "no se activa",
            "si el permanente sacrificado es Korvold",
            "aún así activa",
            "aun así activa",
        ],
        "Sacrifice permanent counter draw fallback",
    )


def test_damage_any_target():

    knowledge = """
QUESTION

Ahora explícame qué hace Lightning Bolt.

============================================================
CARDS

Lightning Bolt
Mana Cost: {R}
Instant

Lightning Bolt deals 3 damage to any target.
"""

    answer = build_fallback_answer(
        knowledge,
        ["test"],
    )

    assert_contains(
        answer,
        [
            "Lightning Bolt",
            "cuesta {R}",
            "instantáneo",
            "3 puntos de daño",
            "cualquier objetivo válido",
        ],
        "Damage any target fallback",
    )

    assert_not_contains(
        answer,
        [
            "objeto",
            "no requiere objetivo",
            "ataca",
            "cementerio",
        ],
        "Damage any target fallback",
    )


def main():

    tests = [
        test_undying_sacrifice,
        test_persist_dies,
        test_sacrifice_permanent_counter_draw,
        test_damage_any_target,
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
