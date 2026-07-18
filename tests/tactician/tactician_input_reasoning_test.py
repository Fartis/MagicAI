from __future__ import annotations

from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.tactician.core import Tactician
from magicai.tactician.input_analysis import SpeechAct, analyze_user_input


CARDS = [
    {
        "name": "Carrion Feeder",
        "oracle_id": "carrion",
        "type_line": "Creature — Zombie",
        "oracle_text": "This creature can't block.\nSacrifice a creature: Put a +1/+1 counter on this creature.",
    },
    {
        "name": "The Ozolith",
        "oracle_id": "ozolith",
        "type_line": "Legendary Artifact",
        "oracle_text": (
            "Whenever a creature you control leaves the battlefield, if it had counters on it, "
            "put those counters on The Ozolith.\nAt the beginning of combat on your turn, "
            "if The Ozolith has counters on it, you may move all counters from The Ozolith onto target creature."
        ),
    },
    {
        "name": "Young Wolf",
        "oracle_id": "wolf",
        "type_line": "Creature — Wolf",
        "oracle_text": (
            "Undying (When this creature dies, if it had no +1/+1 counters on it, "
            "return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
        ),
    },
]


class FakeJudge:
    def __init__(self, *, status: str = "strategy_required") -> None:
        self.status = status

    def ask_result(self, conversation, question):
        return SimpleNamespace(
            to_dict=lambda: {
                "schema_version": "1.0",
                "question": question,
                "answer": "Generic Judge answer about Young Wolf.",
                "status": self.status,
                "origin": "strategy_boundary" if self.status == "strategy_required" else "deterministic_rule",
                "confidence": "high",
                "authority": "judge",
                "cards": CARDS,
                "rules": [],
                "rulings": [],
                "retrieval_queries": [],
                "assumptions": [],
                "warnings": [],
                "source_versions": {},
                "source_health": {},
                "validation_attempts": 0,
                "reviewed_by": [],
                "review_challenges": [],
                "llm_called": False,
                "timings": {},
            }
        )


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
            authority = "comprehensive_rules"
        elif request.tool == "rulings_lookup":
            evidence = []
            authority = "official_rulings"
        else:
            raise AssertionError(f"unexpected tool: {request.tool}")
        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS if evidence or request.tool == "rulings_lookup" else JudgeToolStatus.NOT_FOUND,
            authority=authority,
            provider="fake",
            purpose=request.purpose,
            arguments=request.arguments,
            evidence=evidence,
            budget=budget.snapshot() if budget else {},
        )


def test_input_analysis_recognizes_user_hypothesis() -> None:
    analysis = analyze_user_input(
        "Pero el contador +1/+1 va a The Ozolith, por lo que Undying se activa otra vez."
    )
    assert analysis.speech_act is SpeechAct.CHALLENGE
    assert analysis.strategy_intent.value == "interaction_hypothesis"
    assert any(claim.kind.value == "timing_hypothesis" for claim in analysis.claims)
    assert any(claim.kind.value == "derived_conclusion" for claim in analysis.claims)


def test_three_card_question_explains_why_ozolith_is_not_a_reset() -> None:
    conversation = Conversation(active_cards=CARDS)
    result = Tactician(judge=FakeJudge(), tool_gateway=FakeGateway()).ask_result(
        conversation,
        "¿Cómo funciona Young Wolf, Carrion Feeder y The Ozolith? ¿Hace combo?",
    )
    payload = result.to_dict()

    assert payload["combo_classification"] == "non_combo"
    assert payload["response_mode"] == "tactician_led"
    assert payload["tactician_synthesized"] is True
    assert payload["judge_verified"] is True
    assert payload["queries_completed"] >= 3
    assert "no reinicia Undying" in payload["answer"]
    assert "no forman un bucle infinito" in payload["answer"]
    assert payload["combo_steps"]
    assert payload["reasoning_summary"]
    assert "tactician:input_analysis" in payload["authority_trace"]


def test_challenge_is_evaluated_instead_of_relaying_judge_answer() -> None:
    conversation = Conversation(active_cards=CARDS)
    result = Tactician(judge=FakeJudge(status="answered"), tool_gateway=FakeGateway()).ask_result(
        conversation,
        (
            "Pero Carrion Feeder vuelve a sacrificar Young Wolf y su contador +1/+1 va a "
            "The Ozolith, por lo que al entrar en el cementerio no tiene contador y se activa Undying."
        ),
    )
    payload = result.to_dict()

    assert payload["origin"] == "tactician_hybrid"
    assert payload["response_mode"] == "hybrid"
    assert payload["tactician_synthesized"] is True
    assert payload["input_analysis"]["speech_act"] == "challenge"
    assert payload["strategy_intent"] == "interaction_hypothesis"
    assert any(item["verdict"] == "contradicted" for item in payload["claim_verdicts"])
    assert "Entiendo por qué lo interpretas así" in payload["answer"]
    assert "Undying no se dispara" in " ".join(payload["combo_steps"])
    assert payload["answer"] != "Generic Judge answer about Young Wolf."
    assert conversation.strategy_context["judge_verified"] is True


def main() -> int:
    tests = [
        test_input_analysis_recognizes_user_hypothesis,
        test_three_card_question_explains_why_ozolith_is_not_a_reset,
        test_challenge_is_evaluated_instead_of_relaying_judge_answer,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician input reasoning tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
