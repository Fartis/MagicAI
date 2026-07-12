from typing import Any

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    session_id: str | None = Field(default=None, max_length=128)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question must not be empty")
        return normalized


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
    schema_version: str
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
    source_health: dict[str, Any] = Field(default_factory=dict)
    validation_attempts: int = 0


class MetaResponse(BaseModel):
    project: str
    project_version: str
    api_contract_version: str
    judge_result_schema_version: str
    authority: str
    judge_statuses: list[str]
    judge_origins: list[str]
    confidence_levels: list[str]


class HealthResponse(BaseModel):
    status: str
    ready: bool
    full_service: bool
    project_version: str
    api_contract_version: str
    judge_result_schema_version: str
    sources: dict[str, Any]
    services: dict[str, Any]


class ErrorDetailResponse(BaseModel):
    location: list[str] = Field(default_factory=list)
    message: str = ""
    type: str = ""


class ErrorBodyResponse(BaseModel):
    code: str
    message: str
    retryable: bool
    details: list[ErrorDetailResponse] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    schema_version: str
    error: ErrorBodyResponse
