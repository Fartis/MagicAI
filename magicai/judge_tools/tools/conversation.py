from __future__ import annotations

from typing import Any

from magicai.judge_tools.models import JudgeToolPayload, JudgeToolStatus
from magicai.judge_tools.tools.common import card_to_evidence


class ConversationContextTool:
    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        if conversation is None:
            return JudgeToolPayload(
                status=JudgeToolStatus.NOT_FOUND,
                warnings=["No conversation was supplied to conversation_context."],
            )

        include_history = bool(arguments.get("include_history", False))
        history_limit = max(0, min(int(arguments.get("history_limit", 6)), 20))
        active_cards = [card_to_evidence(card)["data"] for card in conversation.active_cards]
        data: dict[str, Any] = {
            "active_cards": active_cards,
            "active_keywords": list(conversation.active_keywords),
            "active_rules": list(conversation.active_rules),
            "active_rule_queries": list(conversation.active_rule_queries),
            "last_intent": conversation.last_intent,
            "language": conversation.language,
            "mode": conversation.mode,
        }
        if include_history:
            data["recent_history"] = [
                {"role": message.role, "content": message.content}
                for message in conversation.history[-history_limit:]
            ]

        return JudgeToolPayload(
            evidence=[
                {
                    "kind": "conversation_context",
                    "identifier": "active_session",
                    "data": data,
                }
            ],
            metadata={"history_included": include_history},
        )
