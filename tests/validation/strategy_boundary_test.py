from magicai.validation.strategy_boundary import render_strategy_boundary_answer


def assert_contains(text: str, expected: list[str], label: str) -> None:
    lower = text.lower()
    missing = [item for item in expected if item.lower() not in lower]
    if missing:
        raise AssertionError(f"{label}: missing {missing!r} in answer:\n{text}")


def test_sol_ring_strategy_boundary() -> None:
    knowledge = """
QUESTION

¿Y merece la pena jugarlo?

============================================================
CARDS

Sol Ring
Mana Cost: {1}
Artifact

{T}: Add {C}{C}.
"""

    answer = render_strategy_boundary_answer(knowledge)
    assert answer
    assert_contains(
        answer,
        ["Sol Ring", "{1}", "{C}{C}", "aceleración", "Estratega", "depende"],
        "Sol Ring strategy boundary",
    )


def test_two_card_strategy_boundary_uses_recovered_facts() -> None:
    knowledge = """
QUESTION

¿Es mejor Korvold que Prossh?

============================================================
CARDS

Korvold, Fae-Cursed King
Mana Cost: {2}{B}{R}{G}
Legendary Creature — Dragon Noble

Flying
Whenever you sacrifice a permanent, put a +1/+1 counter on Korvold and draw a card.

Prossh, Skyraider of Kher
Mana Cost: {3}{B}{R}{G}
Legendary Creature — Dragon

When you cast this spell, create X 0/1 red Kobold creature tokens named Kobolds of Kher Keep, where X is the amount of mana spent to cast it.
Flying
Sacrifice another creature: Prossh gets +1/+0 until end of turn.
"""

    answer = render_strategy_boundary_answer(knowledge)
    assert answer
    assert_contains(
        answer,
        ["Korvold", "Prossh", "depende", "Estratega", "roba", "Kobold"],
        "Two-card strategy boundary",
    )



def test_named_format_is_preserved() -> None:
    knowledge = """
QUESTION

¿Merece la pena jugar Sol Ring en Commander?

============================================================
CARDS

Sol Ring
Mana Cost: {1}
Artifact

{T}: Add {C}{C}.
"""

    answer = render_strategy_boundary_answer(knowledge)
    assert answer
    assert_contains(
        answer,
        ["Sol Ring", "Commander", "Estratega"],
        "Named format strategy boundary",
    )

def main() -> int:
    tests = [
        test_sol_ring_strategy_boundary,
        test_two_card_strategy_boundary_uses_recovered_facts,
        test_named_format_is_preserved,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Strategy boundary tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
