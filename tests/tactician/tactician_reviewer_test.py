from magicai.tactician.reviewer import review_judge_candidate


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
Undying is a triggered ability. When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it with a +1/+1 counter.

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard.

700.4
The term dies means is put into a graveyard from the battlefield.
"""


def test_tactician_challenges_persistent_young_wolf_error() -> None:
    bad = (
        "Si sacrificas Young Wolf, se mueve al cementerio sin pasar por el campo "
        "de batalla. Undying no se activa y no regresa al campo de batalla."
    )
    review = review_judge_candidate(bad, KNOWLEDGE)
    codes = {challenge.code for challenge in review.challenges}
    assert "sacrifice_requires_battlefield" in codes
    assert "undying_should_trigger" in codes
    assert review.repaired_answer
    assert "Undying se dispara" in review.repaired_answer


def test_tactician_accepts_source_grounded_young_wolf_answer() -> None:
    good = (
        "Al sacrificar Young Wolf, pasa del campo de batalla al cementerio y "
        "muere. Si no tenía contadores +1/+1, Undying se dispara y vuelve con "
        "un contador +1/+1 cuando la habilidad se resuelve."
    )
    review = review_judge_candidate(good, KNOWLEDGE)
    assert review.accepted
    assert review.challenges == []


def main() -> int:
    tests = [
        test_tactician_challenges_persistent_young_wolf_error,
        test_tactician_accepts_source_grounded_young_wolf_answer,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician reviewer tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
