from threading import Lock
from typing import Any
from uuid import uuid4

from magicai.conversation.models import Conversation
from magicai.conversation.repository import (
    ConversationRecord,
    ConversationRepository,
    ConversationSummary,
)


class ConversationManager:

    def __init__(
        self,
        repository: ConversationRepository | None = None,
    ):
        self._lock = Lock()
        self._conversations: dict[str, Conversation] = {}
        self._repository = repository or ConversationRepository()

    def get_or_create(
        self,
        session_id: str | None,
    ) -> tuple[str, Conversation]:
        with self._lock:
            if session_id and session_id in self._conversations:
                return (
                    session_id,
                    self._conversations[session_id],
                )

            if session_id:
                stored = self._repository.load(session_id)
                if stored:
                    self._conversations[session_id] = stored.conversation
                    return session_id, stored.conversation

            new_session_id = session_id or uuid4().hex
            conversation = Conversation()
            self._conversations[new_session_id] = conversation
            return new_session_id, conversation

    def save(
        self,
        session_id: str,
        conversation: Conversation,
        *,
        last_result: dict[str, Any] | None = None,
    ) -> ConversationSummary:
        return self._repository.save(
            session_id,
            conversation,
            last_result=last_result,
        )

    def list(self, limit: int = 50) -> list[ConversationSummary]:
        return self._repository.list(limit=limit)

    def load(self, session_id: str) -> ConversationRecord | None:
        record = self._repository.load(session_id)
        if record:
            with self._lock:
                self._conversations[session_id] = record.conversation
        return record

    def rename(
        self,
        session_id: str,
        title: str,
    ) -> ConversationSummary | None:
        return self._repository.rename(session_id, title)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            self._conversations.pop(session_id, None)
        return self._repository.delete(session_id)
