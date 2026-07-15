from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
import time
from typing import Any

from magicai.judge_tools.models import JudgeToolRequest


@dataclass(slots=True)
class JudgeToolBudget:
    """Bound one strategic investigation without limiting normal Judge use."""

    max_calls: int = 8
    max_calls_per_tool: int = 4
    max_repeated_request: int = 1
    max_elapsed_seconds: float = 30.0
    started_at: float = field(default_factory=time.perf_counter)
    calls: int = 0
    per_tool: Counter[str] = field(default_factory=Counter)
    request_signatures: Counter[str] = field(default_factory=Counter)

    def consume(self, request: JudgeToolRequest) -> tuple[bool, str]:
        if self.calls >= self.max_calls:
            return False, "maximum_tool_calls_reached"
        if self.per_tool[request.tool] >= self.max_calls_per_tool:
            return False, "maximum_calls_for_tool_reached"
        if self.elapsed_seconds >= self.max_elapsed_seconds:
            return False, "maximum_investigation_time_reached"

        signature = _request_signature(request)
        if self.request_signatures[signature] >= self.max_repeated_request:
            return False, "repeated_tool_request_blocked"

        self.calls += 1
        self.per_tool[request.tool] += 1
        self.request_signatures[signature] += 1
        return True, ""

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, time.perf_counter() - self.started_at)

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "max_calls": self.max_calls,
            "per_tool": dict(self.per_tool),
            "max_calls_per_tool": self.max_calls_per_tool,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "max_elapsed_seconds": self.max_elapsed_seconds,
        }


def _request_signature(request: JudgeToolRequest) -> str:
    return json.dumps(
        {
            "tool": request.tool,
            "arguments": request.arguments,
        },
        sort_keys=True,
        ensure_ascii=True,
        default=str,
        separators=(",", ":"),
    )
