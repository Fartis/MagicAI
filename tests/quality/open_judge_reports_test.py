from pathlib import Path
from tempfile import TemporaryDirectory

from tests.quality.open_judge.models import (
    ConversationSnapshot,
    EvaluationFinding,
    OpenJudgeCaseResult,
    OpenJudgeOutcome,
    OpenJudgeTurnResult,
)
from tests.quality.open_judge.reports import (
    write_failure_artifacts,
    write_html_report,
    write_json_report,
    write_txt_report,
    write_xml_report,
)


def main() -> int:
    passing_turn = OpenJudgeTurnResult(
        case_id="OJ-TEST",
        case_name="Report test",
        turn_id="OJ-TEST-01",
        turn_index=1,
        question="Pregunta",
        answer="Respuesta",
        outcome=OpenJudgeOutcome.PASS,
        elapsed=0.1,
        snapshot=ConversationSnapshot(cards=("Young Wolf",), history_size=2),
    )
    clarification_turn = OpenJudgeTurnResult(
        case_id="OJ-TEST",
        case_name="Report test",
        turn_id="OJ-TEST-CLARIFICATION",
        turn_index=2,
        question="¿Qué hace Squee?",
        answer="¿A cuál Squee te refieres?",
        outcome=OpenJudgeOutcome.NEEDS_CLARIFICATION,
        elapsed=0.12,
        snapshot=ConversationSnapshot(history_size=4),
    )
    strategy_turn = OpenJudgeTurnResult(
        case_id="OJ-TEST",
        case_name="Report test",
        turn_id="OJ-TEST-STRATEGY",
        turn_index=3,
        question="¿Es mejor?",
        answer="La recomendación corresponde a Deck Master.",
        outcome=OpenJudgeOutcome.STRATEGY_REQUIRED,
        elapsed=0.15,
        snapshot=ConversationSnapshot(history_size=4),
    )
    failing_turn = OpenJudgeTurnResult(
        case_id="OJ-TEST",
        case_name="Report test",
        turn_id="OJ-TEST-02",
        turn_index=4,
        question="Seguimiento",
        answer="No lo sé",
        outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
        elapsed=0.2,
        findings=[
            EvaluationFinding(
                outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
                message="Expected active card missing.",
            )
        ],
        snapshot=ConversationSnapshot(history_size=4),
    )
    result = OpenJudgeCaseResult(
        id="OJ-TEST",
        name="Report test",
        tags=("test",),
        outcome=OpenJudgeOutcome.CONTEXT_FAILURE,
        elapsed=0.3,
        turns=[passing_turn, clarification_turn, strategy_turn, failing_turn],
    )

    with TemporaryDirectory() as directory:
        output = Path(directory)
        metadata = {"run_id": "test"}
        write_txt_report([result], output / "summary.txt", metadata)
        write_json_report([result], output / "summary.json", metadata)
        write_xml_report([result], output / "summary.xml", metadata)
        write_html_report([result], output / "summary.html", metadata)
        failures = write_failure_artifacts([result], output)

        assert failures == 1
        assert (output / "summary.txt").is_file()
        assert (output / "summary.json").is_file()
        assert (output / "summary.xml").is_file()
        assert (output / "summary.html").is_file()
        assert len(list((output / "open_judge_failures").glob("*.json"))) == 1

    print("Open Judge reports test: TXT, JSON, XML, HTML and failures OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
