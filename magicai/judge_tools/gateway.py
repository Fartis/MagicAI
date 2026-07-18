from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import json
import time
from typing import Any, Callable

from magicai.judge_tools.budget import JudgeToolBudget
from magicai.judge_tools.models import (
    JudgeToolPayload,
    JudgeToolRequest,
    JudgeToolResult,
    JudgeToolStatus,
)
from magicai.judge_tools.registry import (
    CapabilityStatus,
    JudgeCapability,
    get_capability,
    get_capability_registry,
)
from magicai.judge_tools.tools import (
    ConversationContextTool,
    LegalityCheckTool,
    OracleLookupTool,
    OracleSearchTool,
    RulesLookupTool,
    RulesSearchTool,
    RulingsLookupTool,
)
from magicai.sources.versions import get_source_versions


ToolHandler = Callable[..., JudgeToolPayload]


class JudgeToolGateway:
    """Execute read-only source tools while preserving Judge authority."""

    def __init__(
        self,
        *,
        handlers: dict[str, ToolHandler] | None = None,
        cache_size: int = 256,
    ):
        self.handlers = handlers or _default_handlers()
        self.cache_size = max(0, int(cache_size))
        self._cache: OrderedDict[str, JudgeToolResult] = OrderedDict()

    def capabilities(self) -> tuple[JudgeCapability, ...]:
        return get_capability_registry()

    def execute(
        self,
        request: JudgeToolRequest,
        *,
        conversation=None,
        budget: JudgeToolBudget | None = None,
    ) -> JudgeToolResult:
        started = time.perf_counter()
        capability = get_capability(request.tool)
        if capability is None:
            return self._error_result(
                request,
                status=JudgeToolStatus.INVALID_REQUEST,
                error_code="unknown_tool",
                message=f"Unknown Judge tool: {request.tool}",
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )

        if capability.status not in {CapabilityStatus.AVAILABLE, CapabilityStatus.PARTIAL}:
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.UNAVAILABLE,
                error_code="capability_not_available",
                message=(
                    f"{request.tool} is {capability.status.value}; provider "
                    f"{capability.provider} is not executable in this build."
                ),
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )

        handler = self.handlers.get(request.tool)
        if handler is None or not capability.executable:
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.UNAVAILABLE,
                error_code="tool_handler_missing",
                message=f"No executable handler is registered for {request.tool}.",
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )

        if request.result_limit <= 0:
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.INVALID_REQUEST,
                error_code="invalid_result_limit",
                message="result_limit must be greater than zero.",
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )

        if budget is not None:
            accepted, reason = budget.consume(request)
            if not accepted:
                return self._error_result(
                    request,
                    capability=capability,
                    status=JudgeToolStatus.BUDGET_EXCEEDED,
                    error_code=reason,
                    message="The bounded Judge-tool investigation budget rejected this request.",
                    elapsed_ms=_elapsed_ms(started),
                    budget=budget,
                )

        result_limit = min(int(request.result_limit), capability.max_results)
        source_versions = get_source_versions()
        cache_key = self._cache_key(request, source_versions)
        if request.tool != "conversation_context":
            cached = self._cache_get(cache_key)
            if cached is not None:
                cached.elapsed_ms = _elapsed_ms(started)
                cached.cache_hit = True
                cached.budget = budget.snapshot() if budget else {}
                return cached

        try:
            payload = handler(
                dict(request.arguments),
                conversation=conversation,
                result_limit=result_limit,
            )
        except (TypeError, ValueError) as error:
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.INVALID_REQUEST,
                error_code="invalid_arguments",
                message=str(error),
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )
        except (FileNotFoundError, OSError) as error:
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.UNAVAILABLE,
                error_code="local_source_unavailable",
                message=str(error),
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )
        except Exception as error:  # pragma: no cover - production safety boundary
            return self._error_result(
                request,
                capability=capability,
                status=JudgeToolStatus.ERROR,
                error_code="tool_execution_failed",
                message=f"{type(error).__name__}: {error}",
                elapsed_ms=_elapsed_ms(started),
                budget=budget,
            )

        result = JudgeToolResult(
            tool=request.tool,
            status=payload.status,
            authority=capability.authority,
            provider=capability.provider,
            purpose=request.purpose,
            request_id=request.request_id,
            arguments=dict(request.arguments),
            evidence=payload.evidence[:result_limit],
            source_versions=source_versions,
            warnings=list(payload.warnings),
            metadata={
                **payload.metadata,
                "result_limit": result_limit,
                "read_only": capability.read_only,
            },
            elapsed_ms=_elapsed_ms(started),
            budget=budget.snapshot() if budget else {},
        )
        if request.tool != "conversation_context" and result.successful:
            self._cache_put(cache_key, result)
        return result

    def execute_many(
        self,
        requests: list[JudgeToolRequest],
        *,
        conversation=None,
        budget: JudgeToolBudget | None = None,
    ) -> list[JudgeToolResult]:
        active_budget = budget or JudgeToolBudget()
        return [
            self.execute(request, conversation=conversation, budget=active_budget)
            for request in requests
        ]

    def clear_cache(self) -> None:
        self._cache.clear()

    def cache_info(self) -> dict[str, int]:
        return {"size": len(self._cache), "max_size": self.cache_size}

    def _cache_key(
        self,
        request: JudgeToolRequest,
        source_versions: dict[str, str],
    ) -> str:
        return json.dumps(
            {
                "tool": request.tool,
                "arguments": request.arguments,
                "result_limit": request.result_limit,
                "source_versions": source_versions,
            },
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )

    def _cache_get(self, key: str) -> JudgeToolResult | None:
        if self.cache_size <= 0 or key not in self._cache:
            return None
        result = self._cache.pop(key)
        self._cache[key] = result
        return deepcopy(result)

    def _cache_put(self, key: str, result: JudgeToolResult) -> None:
        if self.cache_size <= 0:
            return
        self._cache.pop(key, None)
        self._cache[key] = deepcopy(result)
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)

    def _error_result(
        self,
        request: JudgeToolRequest,
        *,
        status: JudgeToolStatus,
        error_code: str,
        message: str,
        elapsed_ms: float,
        capability: JudgeCapability | None = None,
        budget: JudgeToolBudget | None = None,
    ) -> JudgeToolResult:
        return JudgeToolResult(
            tool=request.tool,
            status=status,
            authority=capability.authority if capability else "judge_gateway",
            provider=capability.provider if capability else "judge_tool_registry",
            purpose=request.purpose,
            request_id=request.request_id,
            arguments=dict(request.arguments),
            source_versions=get_source_versions(),
            error_code=error_code,
            error_message=message,
            elapsed_ms=elapsed_ms,
            budget=budget.snapshot() if budget else {},
        )


def _default_handlers() -> dict[str, ToolHandler]:
    return {
        "oracle_lookup": OracleLookupTool(),
        "oracle_search": OracleSearchTool(),
        "rules_lookup": RulesLookupTool(),
        "rules_search": RulesSearchTool(),
        "rulings_lookup": RulingsLookupTool(),
        "conversation_context": ConversationContextTool(),
        "legality_check": LegalityCheckTool(),
    }


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0
