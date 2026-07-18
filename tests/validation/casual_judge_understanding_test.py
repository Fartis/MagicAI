from magicai.context import AssistantContext
from magicai.knowledge_builder import build_knowledge
from magicai.validation.rule_renderer import render_rule_answer


def test_judge_answers_casual_undying_equivalence_professionally() -> None:
    context = AssistantContext(
        question="Entonces, Undying es cuando muere la criatura, no cuando pisa cementerio?",
        canonical_question="Entonces, Undying es cuando muere la criatura, no cuando es puesta en un cementerio?",
        intent="judge",
        language="es",
        input_register="casual",
        rules=[
            {"number": "700.4", "title": "The term dies means is put into a graveyard from the battlefield.", "rules": []},
            {"number": "702.93a", "title": "Undying is a triggered ability.", "rules": []},
        ],
    )
    answer = render_rule_answer(build_knowledge(context))
    assert answer is not None
    assert "no son dos eventos distintos" in answer
    assert "desde otra zona" in answer
    assert "Undying" in answer
    assert "pisa cementerio" not in answer
    assert "jugador pierde el juego" not in answer


def main() -> int:
    test_judge_answers_casual_undying_equivalence_professionally()
    print("OK: test_judge_answers_casual_undying_equivalence_professionally")
    print("Casual Judge understanding tests: 1/1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
