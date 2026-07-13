from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:

    history: list[Message] = field(default_factory=list)

    active_cards: list = field(default_factory=list)

    active_keywords: list[str] = field(default_factory=list)

    # Rule identifiers such as ``702.93``. The enriched rule dictionaries are
    # intentionally not stored in the session because they are source data and
    # can be recovered again from the local repository.
    active_rules: list[str] = field(default_factory=list)

    # Conceptual searches are retained for procedural topics that have no
    # stable keyword or numbered-rule reference, for example London Mulligan.
    active_rule_queries: list[str] = field(default_factory=list)

    pending_card_question: str | None = None

    pending_card_alias: str | None = None

    pending_card_candidates: list[str] = field(default_factory=list)

    last_intent: str = ""

    language: str = "es"

    mode: str = "assistant"

    def add_user_message(self, text: str):

        self.history.append(
            Message(
                role="user",
                content=text,
            )
        )

    def add_assistant_message(self, text: str):

        self.history.append(
            Message(
                role="assistant",
                content=text,
            )
        )
