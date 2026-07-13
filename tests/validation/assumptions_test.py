from __future__ import annotations

from types import SimpleNamespace

from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_judge_result,
)


def test_printed_cost_example_emits_explicit_assumption() -> None:
    answer = (
        "Prossh crea X fichas. Si pagas únicamente su coste impreso, "
        "gastas 6 manás y crea 6."
    )
    result = build_judge_result(
        question="¿Cuántos Kobolds crea?",
        answer=answer,
        status=JudgeStatus.ANSWERED,
        origin=JudgeOrigin.DETERMINISTIC_ORACLE,
        confidence=JudgeConfidence.HIGH,
        context=SimpleNamespace(
            intent="rules",
            cards=[],
            rules=[],
            rulings=[],
            rule_queries=[],
        ),
    )

    assert len(result.assumptions) == 1
    assert "costes adicionales" in result.assumptions[0]
    assert "reducciones" in result.assumptions[0]


def test_unconditional_answer_does_not_invent_assumptions() -> None:
    result = build_judge_result(
        question="¿Qué hace Young Wolf?",
        answer="Young Wolf tiene Undying.",
        status=JudgeStatus.ANSWERED,
        origin=JudgeOrigin.DETERMINISTIC_ORACLE,
        confidence=JudgeConfidence.HIGH,
        context=SimpleNamespace(
            intent="rules",
            cards=[],
            rules=[],
            rulings=[],
            rule_queries=[],
        ),
    )
    assert result.assumptions == []


def main() -> int:
    tests = [
        test_printed_cost_example_emits_explicit_assumption,
        test_unconditional_answer_does_not_invent_assumptions,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Assumptions tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
