from threading import Lock
from uuid import uuid4

from magicai.conversation.models import Conversation


class ConversationManager:

    def __init__(self):

        self._lock = Lock()
        self._conversations: dict[str, Conversation] = {}

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

            new_session_id = session_id or uuid4().hex

            conversation = Conversation()

            self._conversations[new_session_id] = conversation

            return (
                new_session_id,
                conversation,
            )
