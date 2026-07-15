from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from magicai.api import routes
from magicai.api.schemas import AskRequest, AskResponse
from magicai.conversation.manager import ConversationManager
from magicai.conversation.repository import ConversationRepository
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_judge_result,
)


def _payload() -> dict:
    response = AskResponse(
        schema_version="1.0",
        answer="Respuesta validada.",
        session_id="session-test",
        question="¿Qué ocurre?",
        status="answered",
        origin="deterministic_rule",
        confidence="high",
        authority="judge",
        intent="rules",
        cards=[
            {
                "name": "Young Wolf",
                "mana_cost": "{G}",
                "type_line": "Creature — Wolf",
                "oracle_text": "Undying",
                "scryfall_uri": "https://scryfall.com/card/example/young-wolf",
            }
        ],
        rules=[{"number": "702.93a", "title": "Undying"}],
        rulings=[{
            "card_name": "Young Wolf",
            "oracle_id": "oracle-young-wolf",
            "source": "wotc",
            "published_at": "2024-01-01",
            "comment": "Example ruling.",
        }],
        retrieval_queries=["undying"],
        assumptions=[],
        warnings=[],
        source_versions={"comprehensive_rules": "2026-06-19"},
        source_health={"status": "ready", "ready": True, "sources": {}},
        validation_attempts=0,
    )
    return response.model_dump()


def test_schema_keeps_legacy_and_structured_fields() -> None:
    payload = _payload()

    assert payload["schema_version"] == "1.0"
    assert payload["answer"] == "Respuesta validada."
    assert payload["session_id"] == "session-test"
    assert payload["status"] == "answered"
    assert payload["cards"][0]["name"] == "Young Wolf"
    assert payload["rules"][0]["number"] == "702.93a"
    assert payload["rulings"][0]["source"] == "wotc"


def test_route_serializes_judge_result() -> None:
    class FakeAssistant:
        def ask_result(self, conversation, question):
            context = SimpleNamespace(
                question=question,
                intent="rules",
                cards=[],
                rules=[{"number": "117.2e", "title": "Priority"}],
                rulings=[],
                rule_queries=["priority"],
            )
            return build_judge_result(
                question=question,
                answer="No puedes responder durante la resolución.",
                status=JudgeStatus.ANSWERED,
                origin=JudgeOrigin.DETERMINISTIC_RULE,
                confidence=JudgeConfidence.HIGH,
                context=context,
            )

    original_assistant = routes.assistant
    original_manager = routes.conversation_manager

    with TemporaryDirectory() as directory:
        routes.assistant = FakeAssistant()
        routes.conversation_manager = ConversationManager(
            ConversationRepository(Path(directory) / "judge-result.sqlite3")
        )

        try:
            response = routes.ask(
                AskRequest(
                    question="¿Puedo responder durante la resolución?",
                )
            )
        finally:
            routes.assistant = original_assistant
            routes.conversation_manager = original_manager

    payload = response.model_dump()
    assert payload["answer"].startswith("No puedes responder")
    assert payload["session_id"]
    assert payload["status"] == "answered"
    assert payload["origin"] == "deterministic_rule"
    assert payload["schema_version"] == "1.0"
    assert payload["rules"][0]["number"] == "117.2e"


def main() -> int:
    tests = [
        test_schema_keeps_legacy_and_structured_fields,
        test_route_serializes_judge_result,
    ]

    for test in tests:
        test()
        print(f"OK: {test.__name__}")

    print(f"JudgeResult API tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
