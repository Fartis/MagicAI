from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.tactician.core import Tactician
from tests.quality.tactician_conversations import evaluate_turn, load_scenarios


CASES = Path(__file__).parent / "cases" / "tactician_conversations" / "sprint12_2c.json"

CARDS = [
    {
        "name": "Carrion Feeder",
        "oracle_id": "carrion",
        "oracle_text": "Sacrifice a creature: Put a +1/+1 counter on this creature.",
    },
    {
        "name": "The Ozolith",
        "oracle_id": "ozolith",
        "oracle_text": "Whenever a creature you control leaves the battlefield, if it had counters on it, put those counters on The Ozolith.",
    },
    {
        "name": "Young Wolf",
        "oracle_id": "wolf",
        "oracle_text": "Undying (When this creature dies, if it had no +1/+1 counters on it, return it with a +1/+1 counter.)",
    },
]


class FakeJudge:
    def ask_result(self, conversation, question):
        # The second answer deliberately reproduces the drift found in the
        # manual JSON. The Tactician must not relay it.
        wrong_answer = (
            "Cuando un jugador pierde el juego, las habilidades disparadas por ello se activan."
            if "pisa cementerio" in question
            else "Generic Judge strategy boundary."
        )
        return SimpleNamespace(to_dict=lambda: {
            "schema_version": "1.0",
            "question": question,
            "answer": wrong_answer,
            "status": "answered" if "pisa cementerio" in question else "strategy_required",
            "origin": "llm_validated" if "pisa cementerio" in question else "strategy_boundary",
            "confidence": "medium",
            "authority": "judge",
            "cards": CARDS,
            "rules": [],
            "rulings": [],
            "retrieval_queries": [],
            "assumptions": [],
            "warnings": [],
            "source_versions": {},
            "source_health": {},
            "validation_attempts": 1,
            "reviewed_by": ["tactician"],
            "review_challenges": [],
            "llm_called": True,
            "timings": {},
        })


class FakeGateway:
    def execute(self, request, *, conversation=None, budget=None):
        if request.tool == "oracle_lookup":
            evidence = [
                {"kind": "card", "identifier": card["oracle_id"], "data": card}
                for card in CARDS
            ]
            authority = "official_card_data"
        elif request.tool == "rules_lookup":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": identifier,
                    "data": {"number": identifier, "title": f"Rule {identifier}", "rules": []},
                }
                for identifier in request.arguments["identifiers"]
            ]
            authority = "official_rules"
        elif request.tool == "rulings_lookup":
            evidence = [{
                "kind": "ruling",
                "identifier": "ozolith:2020-04-17",
                "data": {
                    "oracle_id": "ozolith",
                    "card_name": "The Ozolith",
                    "published_at": "2020-04-17",
                    "source": "wotc",
                    "comment": "The Ozolith does not move counters off the creature that left the battlefield.",
                },
            }]
            authority = "official_rulings"
        else:
            raise AssertionError(request.tool)
        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS,
            authority=authority,
            provider="fake",
            purpose=request.purpose,
            arguments=request.arguments,
            evidence=evidence,
            budget=budget.snapshot() if budget else {},
        )


def test_ozolith_conversation_regression() -> None:
    scenario = load_scenarios(CASES)[0]
    conversation = Conversation(language=scenario["language"])
    tactician = Tactician(judge=FakeJudge(), tool_gateway=FakeGateway())

    for turn in scenario["turns"]:
        payload = tactician.ask_result(conversation, turn["question"]).to_dict()
        failures = evaluate_turn(payload, turn["expect"])
        assert not failures, "; ".join(failures)

    assert conversation.language == "es"
    assert conversation.strategy_context["answer_complete"] is True
    assert conversation.strategy_context["judge_verified"] is True


def main() -> int:
    test_ozolith_conversation_regression()
    print("OK: test_ozolith_conversation_regression")
    print("Tactician conversation regression tests: 1/1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
