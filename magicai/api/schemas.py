from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


class CardEvidenceResponse(BaseModel):
    name: str
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    scryfall_uri: str | None = None


class RuleEvidenceResponse(BaseModel):
    number: str | None = None
    title: str | None = None


class RulingEvidenceResponse(BaseModel):
    card_name: str | None = None
    oracle_id: str | None = None
    source: str | None = None
    published_at: str | None = None
    comment: str | None = None


class AskResponse(BaseModel):
    answer: str
    session_id: str
    question: str
    status: str
    origin: str
    confidence: str
    authority: str = "judge"
    intent: str = ""
    cards: list[CardEvidenceResponse] = Field(default_factory=list)
    rules: list[RuleEvidenceResponse] = Field(default_factory=list)
    rulings: list[RulingEvidenceResponse] = Field(default_factory=list)
    retrieval_queries: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_versions: dict[str, str] = Field(default_factory=dict)
    validation_attempts: int = 0
