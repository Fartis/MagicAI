from magicai.validation.rulings_renderer import render_rulings_answer


KNOWLEDGE = """QUESTION

¿Qué dicen los rulings oficiales de Prossh, Skyraider of Kher?

============================================================
CARDS

Prossh, Skyraider of Kher
Mana Cost: {3}{B}{R}{G}
Legendary Creature — Dragon

When you cast this spell, create X 0/1 red Kobold creature tokens named Kobolds of Kher Keep, where X is the amount of mana spent to cast it.
Flying
Sacrifice another creature: Prossh gets +1/+0 until end of turn.

============================================================
RULINGS

Card: Prossh, Skyraider of Kher
Published: 2020-11-10
Source: wotc
The first ability triggers when you cast Prossh, not when it enters the battlefield.

Card: Prossh, Skyraider of Kher
Published: 2020-11-10
Source: wotc
You can't choose to pay extra mana to cast a creature spell unless something instructs you to.
"""


def test_requested_rulings_are_rendered_literally():
    answer = render_rulings_answer(KNOWLEDGE)
    assert answer is not None
    assert "texto oficial" in answer
    assert "The first ability triggers when you cast Prossh" in answer
    assert "You can't choose to pay extra mana" in answer
    assert "vuelo" not in answer.lower()
    assert "+1/+0" not in answer


def test_renderer_does_not_intercept_normal_card_question():
    knowledge = KNOWLEDGE.replace(
        "¿Qué dicen los rulings oficiales de Prossh, Skyraider of Kher?",
        "¿Qué hace Prossh, Skyraider of Kher?",
    )
    assert render_rulings_answer(knowledge) is None


def main():
    tests = [
        test_requested_rulings_are_rendered_literally,
        test_renderer_does_not_intercept_normal_card_question,
    ]
    errors = 0
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors += 1
            print(f"ERROR: {test.__name__}: {exc}")

    print(f"Rulings renderer tests: {len(tests) - errors}/{len(tests)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
