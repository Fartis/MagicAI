from dataclasses import dataclass, field


@dataclass(slots=True)
class AssistantContext:

    question: str

    intent: str

    language: str = "es"

    cards: list = field(default_factory=list)

    keywords: list[str] = field(default_factory=list)

    rules: list[str] = field(default_factory=list)

    rule_queries: list[str] = field(default_factory=list)

    facts: list[str] = field(default_factory=list)

    symbols: list[dict] = field(default_factory=list)

    # Conversational provenance. These fields let the assistant distinguish
    # what the user named in the current turn from what was inherited from the
    # shared conversation state.
    explicit_cards: list[str] = field(default_factory=list)

    explicit_keywords: list[str] = field(default_factory=list)

    explicit_rules: list[str] = field(default_factory=list)

    follow_up: bool = False

    comparison: bool = False

    inherited_rule_queries: bool = False
