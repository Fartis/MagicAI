from dataclasses import dataclass, field


@dataclass(slots=True)
class AssistantContext:

    question: str

    intent: str

    language: str = "es"

    cards: list = field(default_factory=list)

    keywords: list[str] = field(default_factory=list)

    rules: list[str] = field(default_factory=list)

    facts: list[str] = field(default_factory=list)