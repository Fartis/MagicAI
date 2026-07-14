import magicai.answer_generator as answer_generator


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


def test_tactician_repairs_llm_candidate_when_deterministic_route_is_unavailable() -> None:
    original_renderer = answer_generator.render_rule_answer
    original_generate = answer_generator.generate
    try:
        answer_generator.render_rule_answer = lambda knowledge: None
        answer_generator.generate = lambda system, prompt: (
            "Si sacrificas Young Wolf, va al cementerio sin pasar por el campo de "
            "batalla. Undying no se activa y no regresa."
        )
        result = answer_generator.generate_judge_result(KNOWLEDGE)
    finally:
        answer_generator.render_rule_answer = original_renderer
        answer_generator.generate = original_generate

    payload = result.to_dict()
    assert payload["origin"] == "tactician_repair"
    assert payload["reviewed_by"] == ["tactician"]
    assert payload["review_challenges"]
    assert "Undying se dispara" in payload["answer"]
    assert "sin pasar por el campo de batalla" not in payload["answer"]


def main() -> int:
    test_tactician_repairs_llm_candidate_when_deterministic_route_is_unavailable()
    print("OK: test_tactician_repairs_llm_candidate_when_deterministic_route_is_unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
