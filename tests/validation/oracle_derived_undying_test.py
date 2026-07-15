from magicai.validation.rule_renderer import render_rule_answer


KNOWLEDGE = """
QUESTION

¿Qué ocurre si sacrifico Young Wolf?

============================================================
CARDS

Young Wolf
Mana Cost: {G}
Creature — Wolf

Undying (When this creature dies, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.)

============================================================
RULES

702.93a
Undying is a triggered ability.

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard.

700.4
The term dies means is put into a graveyard from the battlefield.
"""


def test_oracle_derived_undying_does_not_require_user_to_name_keyword() -> None:
    answer = render_rule_answer(KNOWLEDGE)
    assert answer is not None
    assert "Young Wolf" in answer
    assert "muere" in answer
    assert "Undying se dispara" in answer
    assert "+1/+1" in answer
    assert "no se activa" not in answer



def test_oracle_derived_route_binds_the_sacrificed_card() -> None:
    knowledge = KNOWLEDGE.replace(
        "Young Wolf\nMana Cost: {G}\nCreature — Wolf\n\nUndying",
        "Carrion Feeder\nMana Cost: {B}\nCreature — Zombie\n\n"
        "Sacrifice a creature: Put a +1/+1 counter on Carrion Feeder.\n\n"
        "Young Wolf\nMana Cost: {G}\nCreature — Wolf\n\nUndying",
    ).replace(
        "¿Qué ocurre si sacrifico Young Wolf?",
        "¿Qué ocurre si sacrifico Carrion Feeder?",
    )
    assert render_rule_answer(knowledge) is None


def main() -> int:
    tests = [
        test_oracle_derived_undying_does_not_require_user_to_name_keyword,
        test_oracle_derived_route_binds_the_sacrificed_card,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
