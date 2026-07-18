from __future__ import annotations

from magicai.api import routes
from magicai.api.schemas import JudgeToolExecuteRequest
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.versioning import JUDGE_TOOL_RESULT_SCHEMA_VERSION


class FakeGateway:
    def execute(self, request, *, conversation=None, budget=None):
        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS,
            authority="official_card_data",
            provider="local_scryfall_oracle",
            purpose=request.purpose,
            arguments=dict(request.arguments),
            evidence=[{"kind": "card", "identifier": "Young Wolf", "data": {"name": "Young Wolf"}}],
        )

    def cache_info(self):
        return {"size": 0, "max_size": 1}


def test_meta_exposes_executable_gateway_contract() -> None:
    payload = routes.meta()
    assert payload["judge_tool_result_schema_version"] == JUDGE_TOOL_RESULT_SCHEMA_VERSION
    assert payload["judge_tool_gateway"]["executable"] is True
    capabilities = {item["name"]: item for item in payload["judge_capabilities"]}
    assert capabilities["oracle_lookup"]["executable"] is True
    assert capabilities["legality_check"]["status"] == "available"
    assert capabilities["spellbook_search"]["executable"] is False


def test_execute_endpoint_returns_structured_tool_result() -> None:
    original = routes.judge_tool_gateway
    routes.judge_tool_gateway = FakeGateway()
    try:
        response = routes.execute_judge_tool(
            JudgeToolExecuteRequest(
                tool="oracle_lookup",
                arguments={"card_names": ["Young Wolf"]},
                purpose="api_test",
            )
        )
    finally:
        routes.judge_tool_gateway = original

    payload = response.model_dump()
    assert payload["schema_version"] == JUDGE_TOOL_RESULT_SCHEMA_VERSION
    assert payload["authority"] == "official_card_data"
    assert payload["evidence"][0]["data"]["name"] == "Young Wolf"


def main() -> int:
    tests = [
        test_meta_exposes_executable_gateway_contract,
        test_execute_endpoint_returns_structured_tool_result,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Judge tool API tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
