from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:

    history: list[Message] = field(default_factory=list)

    active_cards: list = field(default_factory=list)

    active_keywords: list = field(default_factory=list)

    active_rules: list = field(default_factory=list)

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