from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from magicai.api import routes
from magicai.api.schemas import AskRequest, ConversationRenameRequest
from magicai.conversation.manager import ConversationManager
from magicai.conversation.repository import ConversationRepository
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_judge_result,
)


class FakeAssistant:
    def ask_result(self, conversation, question):
        conversation.add_user_message(question)
        answer = f"Respuesta persistida para: {question}"
        conversation.add_assistant_message(answer)
        context = SimpleNamespace(
            question=question,
            intent="rules",
            cards=[],
            rules=[{"number": "117.1", "title": "Priority"}],
            rulings=[],
            rule_queries=["priority"],
        )
        return build_judge_result(
            question=question,
            answer=answer,
            status=JudgeStatus.ANSWERED,
            origin=JudgeOrigin.DETERMINISTIC_RULE,
            confidence=JudgeConfidence.HIGH,
            context=context,
        )


def test_conversation_history_routes_use_persistent_manager() -> None:
    with TemporaryDirectory() as directory:
        manager = ConversationManager(
            ConversationRepository(Path(directory) / "api-history.sqlite3")
        )
        original_manager = routes.conversation_manager
        original_assistant = routes.assistant
        routes.conversation_manager = manager
        routes.assistant = FakeAssistant()

        try:
            response = routes.ask(AskRequest(question="¿Cuándo recibo prioridad?"))
            session_id = response.session_id

            summaries = routes.list_conversations(limit=50)
            detail = routes.get_conversation(session_id)
            renamed = routes.rename_conversation(
                session_id,
                ConversationRenameRequest(title="Prioridad y pila"),
            )
            deleted = routes.delete_conversation(session_id)
        finally:
            routes.conversation_manager = original_manager
            routes.assistant = original_assistant

        assert len(summaries) == 1
        assert summaries[0].session_id == session_id
        assert detail.messages[0].role == "user"
        assert detail.messages[-1].role == "assistant"
        assert detail.last_result["status"] == "answered"
        assert renamed.title == "Prioridad y pila"
        assert deleted.deleted is True
        assert manager.load(session_id) is None



def test_persistence_failure_does_not_hide_the_judge_answer() -> None:
    class FailingManager(ConversationManager):
        def save(self, session_id, conversation, *, last_result=None):
            raise sqlite3.OperationalError("read only database")

    with TemporaryDirectory() as directory:
        manager = FailingManager(
            ConversationRepository(Path(directory) / "failing-history.sqlite3")
        )
        original_manager = routes.conversation_manager
        original_assistant = routes.assistant
        routes.conversation_manager = manager
        routes.assistant = FakeAssistant()

        try:
            response = routes.ask(AskRequest(question="¿Qué hace Ward?"))
        finally:
            routes.conversation_manager = original_manager
            routes.assistant = original_assistant

        assert response.status == "answered"
        assert response.answer.startswith("Respuesta persistida")
        assert any("no se pudo guardar" in warning for warning in response.warnings)

def main() -> int:
    tests = [
        test_conversation_history_routes_use_persistent_manager,
        test_persistence_failure_does_not_hide_the_judge_answer,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Conversation history API tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
