from __future__ import annotations

from magicai.judge_tools import (
    JudgeToolBudget,
    JudgeToolGateway,
    JudgeToolPayload,
    JudgeToolRequest,
    JudgeToolStatus,
)


class CountingHandler:
    def __init__(self):
        self.calls = 0

    def __call__(self, arguments, *, conversation=None, result_limit=8):
        self.calls += 1
        return JudgeToolPayload(
            evidence=[
                {
                    "kind": "card",
                    "identifier": "Young Wolf",
                    "data": {"name": "Young Wolf"},
                }
            ],
            metadata={"received_limit": result_limit},
        )


def test_gateway_executes_and_caches_read_only_tool() -> None:
    handler = CountingHandler()
    gateway = JudgeToolGateway(handlers={"oracle_lookup": handler}, cache_size=4)
    request = JudgeToolRequest(
        tool="oracle_lookup",
        arguments={"card_names": ["Young Wolf"]},
        purpose="test",
    )

    first = gateway.execute(request)
    second = gateway.execute(request)

    assert first.status is JudgeToolStatus.SUCCESS
    assert first.authority == "official_card_data"
    assert first.provider == "local_scryfall_oracle"
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert handler.calls == 1
    assert second.evidence[0]["data"]["name"] == "Young Wolf"


def test_gateway_rejects_unknown_and_planned_tools() -> None:
    gateway = JudgeToolGateway(handlers={})
    unknown = gateway.execute(JudgeToolRequest(tool="not_a_tool"))
    planned = gateway.execute(JudgeToolRequest(tool="spellbook_search"))

    assert unknown.status is JudgeToolStatus.INVALID_REQUEST
    assert unknown.error_code == "unknown_tool"
    assert planned.status is JudgeToolStatus.UNAVAILABLE
    assert planned.error_code == "capability_not_available"


def test_budget_blocks_repeated_identical_request() -> None:
    handler = CountingHandler()
    gateway = JudgeToolGateway(handlers={"oracle_lookup": handler}, cache_size=0)
    budget = JudgeToolBudget(max_calls=3, max_repeated_request=1)
    request = JudgeToolRequest(
        tool="oracle_lookup",
        arguments={"card_names": ["Young Wolf"]},
    )

    first = gateway.execute(request, budget=budget)
    second = gateway.execute(request, budget=budget)

    assert first.status is JudgeToolStatus.SUCCESS
    assert second.status is JudgeToolStatus.BUDGET_EXCEEDED
    assert second.error_code == "repeated_tool_request_blocked"
    assert handler.calls == 1


def main() -> int:
    tests = [
        test_gateway_executes_and_caches_read_only_tool,
        test_gateway_rejects_unknown_and_planned_tools,
        test_budget_blocks_repeated_identical_request,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Judge Tool Gateway tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
