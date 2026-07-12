from tests.quality.open_judge.evaluator import evaluate_turn
from tests.quality.open_judge.models import (
    ConversationSnapshot,
    ForbiddenClaim,
    OpenJudgeOutcome,
    OpenJudgeTurn,
)


def assert_outcome(
    expected,
    contract,
    answer,
    snapshot=None,
    exception="",
    judge_status="",
):
    outcome, findings = evaluate_turn(
        contract=contract,
        answer=answer,
        snapshot=snapshot,
        exception=exception,
        judge_status=judge_status,
    )
    assert outcome == expected, (outcome, findings)


def main() -> int:
    base = OpenJudgeTurn(
        id="TEST-01",
        question="¿Qué ocurre?",
        required_all=("Undying",),
        required_any=(("vuelve", "regresa"),),
        recommended_all=("cementerio",),
        expected_cards=("Young Wolf",),
    )
    snapshot = ConversationSnapshot(cards=("Young Wolf",))

    assert_outcome(
        OpenJudgeOutcome.PASS,
        base,
        "Undying hace que vuelve desde el cementerio.",
        snapshot,
    )
    assert_outcome(
        OpenJudgeOutcome.CORRECT_BUT_INCOMPLETE,
        base,
        "Undying hace que vuelve.",
        snapshot,
    )
    assert_outcome(
        OpenJudgeOutcome.INSUFFICIENT_EVIDENCE,
        base,
        "No hay suficiente información para responder.",
        snapshot,
    )
    assert_outcome(
        OpenJudgeOutcome.CONTEXT_FAILURE,
        base,
        "Undying hace que vuelve desde el cementerio.",
        ConversationSnapshot(cards=()),
    )

    contradiction = OpenJudgeTurn(
        id="TEST-02",
        question="¿Tiene prisa?",
        required_all=("Young Wolf",),
        forbidden=(ForbiddenClaim("Young Wolf tiene prisa"),),
    )
    assert_outcome(
        OpenJudgeOutcome.FACTUAL_CONTRADICTION,
        contradiction,
        "Young Wolf tiene prisa.",
    )

    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-NEGATION",
            question="¿Vuelve?",
            required_all=("no vuelve",),
            forbidden=(ForbiddenClaim("vuelve al campo"),),
        ),
        "No vuelve al campo.",
    )

    hallucination = OpenJudgeTurn(
        id="TEST-03",
        question="¿Y Persist?",
        required_all=("Persist",),
        forbidden=(
            ForbiddenClaim(
                "es un conjuro",
                OpenJudgeOutcome.HALLUCINATION,
            ),
        ),
    )
    assert_outcome(
        OpenJudgeOutcome.HALLUCINATION,
        hallucination,
        "Persist es un conjuro.",
    )


    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-VARIANTS-TRIGGER",
            question="¿Se dispara?",
            required_all=("no activa",),
        ),
        "La habilidad no se activa.",
    )

    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-VARIANTS-HASTE",
            question="¿Tiene prisa?",
            required_all=("prisa",),
        ),
        "Strangleroot Geist tiene Haste.",
    )

    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-VARIANTS-DRAW",
            question="¿Cuántas roba?",
            required_all=("roba",),
        ),
        "El jugador dibuja siete cartas.",
    )

    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-VARIANTS-COUNTER",
            question="¿Qué comprueba?",
            required_all=("no tenía",),
        ),
        "Comprueba que no tiene contadores +1/+1.",
    )

    assert_outcome(
        OpenJudgeOutcome.PASS,
        OpenJudgeTurn(
            id="TEST-VARIANTS-SUBJUNCTIVE",
            question="¿Qué comprueba?",
            required_all=("no tenía",),
        ),
        "Se dispara siempre que no tuviera contadores +1/+1.",
    )


    clarification = OpenJudgeTurn(
        id="TEST-CLARIFICATION",
        question="¿Qué hace Squee?",
        required_all=("Squee, Goblin Nabob",),
        success_outcome=OpenJudgeOutcome.NEEDS_CLARIFICATION,
    )
    assert_outcome(
        OpenJudgeOutcome.NEEDS_CLARIFICATION,
        clarification,
        "¿Te refieres a Squee, Goblin Nabob?",
    )

    strategy = OpenJudgeTurn(
        id="TEST-STRATEGY",
        question="¿Merece la pena jugarla?",
        required_all=("Deck Master",),
        success_outcome=OpenJudgeOutcome.STRATEGY_REQUIRED,
    )
    assert_outcome(
        OpenJudgeOutcome.STRATEGY_REQUIRED,
        strategy,
        "La recomendación estratégica corresponde a Deck Master.",
    )


    assert_outcome(
        OpenJudgeOutcome.STRATEGY_REQUIRED,
        strategy,
        "La recomendación estratégica corresponde a Deck Master.",
        judge_status="strategy_required",
    )

    assert_outcome(
        OpenJudgeOutcome.CONTEXT_FAILURE,
        strategy,
        "La recomendación estratégica corresponde a Deck Master.",
        judge_status="answered",
    )

    assert_outcome(
        OpenJudgeOutcome.INSUFFICIENT_EVIDENCE,
        base,
        "Undying hace que vuelve desde el cementerio.",
        snapshot,
        judge_status="insufficient_evidence",
    )
    assert_outcome(
        OpenJudgeOutcome.EXECUTION_ERROR,
        base,
        "",
        snapshot,
        exception="traceback",
    )

    print("Open Judge evaluator test: all semantic classifications passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
