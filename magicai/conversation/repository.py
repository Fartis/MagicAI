from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

from magicai.conversation.models import Conversation, Message


DEFAULT_HISTORY_LIMIT = 50
MAX_HISTORY_LIMIT = 200
DEFAULT_TITLE = "Nueva conversación"
MAX_TITLE_LENGTH = 120


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    summary: ConversationSummary
    conversation: Conversation
    last_result: dict[str, Any] | None


def default_conversation_database_path() -> Path:
    configured = os.environ.get("MAGICAI_CONVERSATION_DB")
    if configured:
        return Path(configured).expanduser().resolve()

    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MagicAI"
    else:
        root = Path(
            os.environ.get(
                "XDG_DATA_HOME",
                Path.home() / ".local" / "share",
            )
        ) / "magicai"

    return root / "conversations.sqlite3"


class ConversationRepository:
    """Persist local Judge conversations in a standalone SQLite database."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(
            database_path or default_conversation_database_path()
        ).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(
        self,
        session_id: str,
        conversation: Conversation,
        *,
        last_result: dict[str, Any] | None = None,
    ) -> ConversationSummary:
        now = _utc_now()
        state_json = json.dumps(
            _conversation_to_dict(conversation),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result_json = (
            json.dumps(last_result, ensure_ascii=False, separators=(",", ":"))
            if last_result is not None
            else None
        )
        message_count = len(conversation.history)
        generated_title = _title_from_conversation(conversation)

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT title, title_is_custom, created_at, last_result_json
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

            if existing:
                title = (
                    existing["title"]
                    if existing["title_is_custom"]
                    else generated_title
                )
                created_at = existing["created_at"]
                stored_result_json = (
                    result_json
                    if result_json is not None
                    else existing["last_result_json"]
                )
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?, message_count = ?,
                        state_json = ?, last_result_json = ?
                    WHERE session_id = ?
                    """,
                    (
                        title,
                        now,
                        message_count,
                        state_json,
                        stored_result_json,
                        session_id,
                    ),
                )
            else:
                title = generated_title
                created_at = now
                connection.execute(
                    """
                    INSERT INTO conversations (
                        session_id, title, title_is_custom, created_at,
                        updated_at, message_count, state_json, last_result_json
                    ) VALUES (?, ?, 0, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        title,
                        created_at,
                        now,
                        message_count,
                        state_json,
                        result_json,
                    ),
                )

            connection.commit()

        return ConversationSummary(
            session_id=session_id,
            title=title,
            created_at=created_at,
            updated_at=now,
            message_count=message_count,
        )

    def load(self, session_id: str) -> ConversationRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT session_id, title, created_at, updated_at,
                       message_count, state_json, last_result_json
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()

        if not row:
            return None

        state = _load_json_object(row["state_json"])
        last_result = _load_json_object(row["last_result_json"])
        return ConversationRecord(
            summary=_summary_from_row(row),
            conversation=_conversation_from_dict(state),
            last_result=last_result or None,
        )

    def list(self, limit: int = DEFAULT_HISTORY_LIMIT) -> list[ConversationSummary]:
        normalized_limit = min(max(int(limit), 1), MAX_HISTORY_LIMIT)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT session_id, title, created_at, updated_at, message_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (normalized_limit,),
            ).fetchall()
        return [_summary_from_row(row) for row in rows]

    def rename(self, session_id: str, title: str) -> ConversationSummary | None:
        normalized_title = _normalize_title(title)
        now = _utc_now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE conversations
                SET title = ?, title_is_custom = 1, updated_at = ?
                WHERE session_id = ?
                """,
                (normalized_title, now, session_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                """
                SELECT session_id, title, created_at, updated_at, message_count
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            connection.commit()
        return _summary_from_row(row)

    def delete(self, session_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    title_is_custom INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    state_json TEXT NOT NULL,
                    last_result_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                ON conversations(updated_at DESC);
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        return connection


def _summary_from_row(row: sqlite3.Row) -> ConversationSummary:
    return ConversationSummary(
        session_id=str(row["session_id"]),
        title=str(row["title"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        message_count=int(row["message_count"]),
    )


def _conversation_to_dict(conversation: Conversation) -> dict[str, Any]:
    return {
        "history": [asdict(message) for message in conversation.history],
        "active_cards": _json_safe(conversation.active_cards),
        "active_keywords": _string_list(conversation.active_keywords),
        "active_rules": _string_list(conversation.active_rules),
        "active_rule_queries": _string_list(conversation.active_rule_queries),
        "pending_card_question": _optional_string(conversation.pending_card_question),
        "pending_card_alias": _optional_string(conversation.pending_card_alias),
        "pending_card_candidates": _string_list(conversation.pending_card_candidates),
        "last_intent": str(conversation.last_intent or ""),
        "language": str(conversation.language or "es"),
        "mode": str(conversation.mode or "assistant"),
    }


def _conversation_from_dict(value: dict[str, Any]) -> Conversation:
    history: list[Message] = []
    raw_history = value.get("history", [])
    if isinstance(raw_history, list):
        for item in raw_history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                history.append(Message(role=role, content=content))

    active_cards = value.get("active_cards", [])
    if not isinstance(active_cards, list):
        active_cards = []

    return Conversation(
        history=history,
        active_cards=active_cards,
        active_keywords=_string_list(value.get("active_keywords")),
        active_rules=_string_list(value.get("active_rules")),
        active_rule_queries=_string_list(value.get("active_rule_queries")),
        pending_card_question=_optional_string(value.get("pending_card_question")),
        pending_card_alias=_optional_string(value.get("pending_card_alias")),
        pending_card_candidates=_string_list(value.get("pending_card_candidates")),
        last_intent=str(value.get("last_intent") or ""),
        language=str(value.get("language") or "es"),
        mode=str(value.get("mode") or "assistant"),
    )


def _title_from_conversation(conversation: Conversation) -> str:
    for message in conversation.history:
        if message.role == "user" and message.content.strip():
            return _normalize_title(message.content)
    return DEFAULT_TITLE


def _normalize_title(value: str) -> str:
    compact = " ".join(str(value).strip().split())
    if not compact:
        return DEFAULT_TITLE
    if len(compact) <= MAX_TITLE_LENGTH:
        return compact
    return compact[: MAX_TITLE_LENGTH - 1].rstrip() + "…"


def _load_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return str(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item not in result:
            result.append(item)
    return result


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
