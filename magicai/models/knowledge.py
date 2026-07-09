from dataclasses import dataclass, field

@dataclass
class Knowledge:

    question: str

    cards: list[str] = field(default_factory=list)

    rules: list[str] = field(default_factory=list)

    facts: list[str] = field(default_factory=list)