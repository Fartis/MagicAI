from pathlib import Path
from tempfile import TemporaryDirectory

from magicai.conversation.manager import ConversationManager
from magicai.conversation.models import Conversation
from magicai.conversation.repository import ConversationRepository


def test_conversation_survives_manager_restart() -> None:
    with TemporaryDirectory() as directory:
        database = Path(directory) / "conversations.sqlite3"
        first_manager = ConversationManager(ConversationRepository(database))
        session_id, conversation = first_manager.get_or_create(None)
        conversation.add_user_message("¿Qué hace Young Wolf?")
        conversation.active_keywords = ["Undying"]
        conversation.add_assistant_message("Young Wolf tiene Undying.")
        first_manager.save(
            session_id,
            conversation,
            last_result={"answer": "Young Wolf tiene Undying.", "status": "answered"},
        )

        second_manager = ConversationManager(ConversationRepository(database))
        loaded_id, loaded = second_manager.get_or_create(session_id)
        record = second_manager.load(session_id)

        assert loaded_id == session_id
        assert [message.content for message in loaded.history] == [
            "¿Qué hace Young Wolf?",
            "Young Wolf tiene Undying.",
        ]
        assert loaded.active_keywords == ["Undying"]
        assert record is not None
        assert record.last_result["status"] == "answered"
        assert record.summary.title == "¿Qué hace Young Wolf?"
        assert record.summary.message_count == 2


def test_history_can_be_listed_renamed_and_deleted() -> None:
    with TemporaryDirectory() as directory:
        repository = ConversationRepository(Path(directory) / "history.sqlite3")
        conversation = Conversation()
        conversation.add_user_message("Una pregunta con un título inicial")
        repository.save("session-a", conversation)

        summaries = repository.list()
        assert [summary.session_id for summary in summaries] == ["session-a"]
        assert summaries[0].title == "Una pregunta con un título inicial"

        renamed = repository.rename("session-a", "Young Wolf y Undying")
        assert renamed is not None
        assert renamed.title == "Young Wolf y Undying"

        conversation.add_assistant_message("Respuesta posterior")
        repository.save("session-a", conversation)
        assert repository.list()[0].title == "Young Wolf y Undying"

        assert repository.delete("session-a") is True
        assert repository.load("session-a") is None
        assert repository.delete("session-a") is False


def main() -> int:
    tests = [
        test_conversation_survives_manager_restart,
        test_history_can_be_listed_renamed_and_deleted,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Conversation repository tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
