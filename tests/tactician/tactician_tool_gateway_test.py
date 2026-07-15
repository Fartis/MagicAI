from __future__ import annotations

from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.tactician.core import Tactician


class FakeJudge:
    def ask_result(self, conversation, question):
        return SimpleNamespace(
            to_dict=lambda: {
                "question": question,
                "answer": "Strategy boundary.",
                "status": "strategy_required",
                "origin": "strategy_boundary",
                "confidence": "high",
                "authority": "judge",
                "cards": [
                    {
                        "name": "Young Wolf",
                        "type_line": "Creature — Wolf",
                        "oracle_text": "Undying",
                    }
                ],
                "rules": [],
                "rulings": [],
                "retrieval_queries": [],
                "assumptions": [],
                "warnings": [],
                "source_versions": {},
                "source_health": {},
            }
        )


class FakeGateway:
    def execute(self, request, *, conversation=None, budget=None):
        assert request.tool == "oracle_lookup"
        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS,
            authority="official_card_data",
            provider="local_scryfall_oracle",
            purpose=request.purpose,
            arguments=request.arguments,
            evidence=[
                {
                    "kind": "card",
                    "identifier": "oracle-young-wolf",
                    "data": {
                        "oracle_id": "oracle-young-wolf",
                        "name": "Young Wolf",
                        "type_line": "Creature — Wolf",
                        "oracle_text": "Undying (When this creature dies, return it with a +1/+1 counter.)",
                    },
                }
            ],
        )


def test_tactician_refreshes_evidence_through_judge_gateway() -> None:
    conversation = Conversation()
    result = Tactician(judge=FakeJudge(), tool_gateway=FakeGateway()).ask_result(
        conversation,
        "¿Tiene alguna sinergia Young Wolf?",
    )
    payload = result.to_dict()

    assert payload["judge_tool_calls"][0]["tool"] == "oracle_lookup"
    assert payload["judge_tool_calls"][0]["status"] == "success"
    assert payload["cards"][0]["oracle_id"] == "oracle-young-wolf"
    assert "judge:tool_gateway" in payload["authority_trace"]
    assert payload["tactician_synthesized"] is True


def main() -> int:
    test_tactician_refreshes_evidence_through_judge_gateway()
    print("OK: test_tactician_refreshes_evidence_through_judge_gateway")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
