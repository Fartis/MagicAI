from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from magicai.versioning import JUDGE_TOOL_RESULT_SCHEMA_VERSION


class JudgeToolStatus(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    INVALID_REQUEST = "invalid_request"
    UNAVAILABLE = "unavailable"
    BUDGET_EXCEEDED = "budget_exceeded"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class JudgeToolRequest:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    purpose: str = ""
    request_id: str = ""
    result_limit: int = 8

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": dict(self.arguments),
            "purpose": self.purpose,
            "request_id": self.request_id,
            "result_limit": self.result_limit,
        }


@dataclass(slots=True)
class JudgeToolPayload:
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: JudgeToolStatus = JudgeToolStatus.SUCCESS
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JudgeToolResult:
    tool: str
    status: JudgeToolStatus
    authority: str
    provider: str
    purpose: str = ""
    request_id: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    source_versions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""
    elapsed_ms: float = 0.0
    cache_hit: bool = False
    budget: dict[str, Any] = field(default_factory=dict)

    @property
    def successful(self) -> bool:
        return self.status in {JudgeToolStatus.SUCCESS, JudgeToolStatus.NOT_FOUND}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": JUDGE_TOOL_RESULT_SCHEMA_VERSION,
            "tool": self.tool,
            "status": self.status.value,
            "authority": self.authority,
            "provider": self.provider,
            "purpose": self.purpose,
            "request_id": self.request_id,
            "arguments": dict(self.arguments),
            "evidence": list(self.evidence),
            "source_versions": dict(self.source_versions),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "elapsed_ms": round(float(self.elapsed_ms), 3),
            "cache_hit": bool(self.cache_hit),
            "budget": dict(self.budget),
        }
