from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from magicai.conversation.models import Conversation
from magicai.conversation.repository import ConversationRepository


def test_strategy_context_round_trips_through_sqlite() -> None:
    with TemporaryDirectory() as directory:
        repository = ConversationRepository(Path(directory) / "conversations.sqlite3")
        conversation = Conversation(
            strategy_context={
                "last_intent": "interaction_hypothesis",
                "active_cards": ["Young Wolf", "The Ozolith"],
                "judge_verified": True,
            }
        )
        repository.save("session", conversation)
        loaded = repository.load("session")
        assert loaded is not None
        assert loaded.conversation.strategy_context == conversation.strategy_context


def main() -> int:
    test_strategy_context_round_trips_through_sqlite()
    print("OK: test_strategy_context_round_trips_through_sqlite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
