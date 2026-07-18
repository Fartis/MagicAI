from __future__ import annotations

from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.tactician.core import Tactician
from magicai.tactician.input_analysis import analyze_user_input
from magicai.tactician.planner import plan_investigation
from magicai.retrieval.concept_evidence import mandatory_rule_numbers
from magicai.validation.rule_renderer import render_rule_answer


QUESTION = """Estoy jugando Commander. Mi oponente controla Blood Moon. Yo controlo
Urborg, Tomb of Yawgmoth y después lanzo Dryad of the Ilysian Grove.

¿Qué tipos de tierra, habilidades de maná y colores pueden producir mis tierras
básicas, mis tierras no básicas y las tierras no básicas del oponente?

¿Cambiaría el resultado si Dryad hubiera entrado antes que Blood Moon?
Explica las capas, dependencias y timestamp aplicables."""


CARDS = [
    {
        "name": "Dryad of the Ilysian Grove",
        "type_line": "Enchantment Creature — Nymph Dryad",
        "oracle_text": "Lands you control are every basic land type in addition to their other types.",
    },
    {
        "name": "Urborg, Tomb of Yawgmoth",
        "type_line": "Legendary Land",
        "oracle_text": "Each land is a Swamp in addition to its other land types.",
    },
    {
        "name": "Blood Moon",
        "type_line": "Enchantment",
        "oracle_text": "Nonbasic lands are Mountains.",
    },
]


RULES = (
    "305.6",
    "305.7",
    "305.8",
    "611.3",
    "613.1d",
    "613.7",
    "613.8a",
    "613.8b",
)


class InsufficientJudge:
    def ask_result(self, conversation, question):
        return SimpleNamespace(
            to_dict=lambda: {
                "schema_version": "1.0",
                "question": question,
                "answer": "No he podido generar una explicación completa con suficiente seguridad.",
                "status": "insufficient_evidence",
                "origin": "safe_fallback",
                "confidence": "low",
                "authority": "judge",
                "cards": CARDS,
                "rules": [],
                "rulings": [],
                "retrieval_queries": [],
                "assumptions": [],
                "warnings": ["The answer looks incomplete."],
                "source_versions": {},
                "source_health": {},
                "validation_attempts": 2,
            }
        )




def _deterministic_answer() -> str:
    cards_block = "\n\n".join(
        f"{card['name']}\n{card['type_line']}\n\n{card['oracle_text']}"
        for card in CARDS
    )
    rules_block = "\n\n".join(
        f"{number}\nRule {number}"
        for number in RULES
    )
    knowledge = (
        f"QUESTION\n\n{QUESTION}\n\n"
        "============================================================\n"
        f"CARDS\n\n{cards_block}\n\n"
        "============================================================\n"
        f"RULES\n\n{rules_block}\n"
    )
    answer = render_rule_answer(knowledge)
    assert answer is not None
    return answer


class AnsweredJudge:
    def ask_result(self, conversation, question):
        answer = _deterministic_answer()
        return SimpleNamespace(
            to_dict=lambda: {
                "schema_version": "1.0",
                "question": question,
                "answer": answer,
                "status": "answered",
                "origin": "deterministic_rule",
                "confidence": "high",
                "authority": "judge",
                "cards": CARDS,
                "rules": [
                    {"number": number, "title": f"Rule {number}"}
                    for number in RULES
                ],
                "rulings": [],
                "retrieval_queries": list(RULES),
                "assumptions": [],
                "warnings": [],
                "source_versions": {},
                "source_health": {},
                "validation_attempts": 0,
            }
        )


class CompleteEvidenceGateway:
    def execute(self, request, *, conversation=None, budget=None):
        if request.tool == "oracle_lookup":
            evidence = [
                {"kind": "card", "identifier": card["name"], "data": card}
                for card in CARDS
            ]
            authority = "official_card_data"
        elif request.tool == "rules_lookup":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": identifier,
                    "data": {"number": identifier, "title": f"Rule {identifier}"},
                }
                for identifier in request.arguments.get("identifiers", [])
            ]
            authority = "comprehensive_rules"
        elif request.tool == "rules_search":
            evidence = []
            authority = "comprehensive_rules"
        else:
            raise AssertionError(f"unexpected tool: {request.tool}")
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


def test_question_is_classified_as_rules_clarification() -> None:
    analysis = analyze_user_input(QUESTION)

    assert analysis.strategy_intent.value == "rules_clarification"
    assert {
        "layers",
        "dependency",
        "timestamp",
        "land_types",
        "basic_lands",
        "nonbasic_lands",
        "mana_abilities",
    }.issubset(set(analysis.concepts))


def test_judge_context_reserves_complete_land_layer_evidence() -> None:
    assert mandatory_rule_numbers(QUESTION) == RULES


def test_plan_requires_complete_land_layer_evidence() -> None:
    analysis = analyze_user_input(QUESTION)
    plan = plan_investigation(analysis, cards=CARDS)
    rule_requests = [
        request for request in plan.requests
        if request.tool == "rules_lookup"
    ]

    assert len(rule_requests) == 1
    assert set(RULES).issubset(set(rule_requests[0].arguments["identifiers"]))
    required = {
        token
        for hypothesis in plan.hypotheses
        for token in hypothesis.required_evidence
    }
    assert {f"rule:{number}" for number in RULES}.issubset(required)


def test_insufficient_judge_cannot_be_reported_as_verified_or_complete() -> None:
    result = Tactician(
        judge=InsufficientJudge(),
        tool_gateway=CompleteEvidenceGateway(),
    ).ask_result(Conversation(), QUESTION)
    payload = result.to_dict()

    assert payload["investigation_trace"]["sufficient"] is True
    assert payload["judge_result"]["status"] == "insufficient_evidence"
    assert payload["response_mode"] == "judge_led"
    assert payload["judge_verified"] is False
    assert payload["answer_complete"] is False
    assert payload["answer_contract"]["answer_complete"] is False
    assert payload["factual_core_coverage"]["required"] == 0
    assert "judge:evidence_incomplete" in payload["authority_trace"]



def test_answered_deterministic_judge_has_consistent_metadata() -> None:
    result = Tactician(
        judge=AnsweredJudge(),
        tool_gateway=CompleteEvidenceGateway(),
    ).ask_result(Conversation(), QUESTION)
    payload = result.to_dict()

    assert payload["judge_result"]["status"] == "answered"
    assert payload["judge_result"]["origin"] == "deterministic_rule"
    assert payload["investigation_trace"]["sufficient"] is True
    assert all(payload["answer_contract"]["checks"].values())
    assert payload["answer_contract"]["answer_complete"] is True
    assert payload["answer_complete"] is True
    assert payload["judge_verified"] is True
    assert payload["confidence"] == "high"
    assert "judge:evidence_verification" in payload["authority_trace"]
    assert "judge:evidence_incomplete" not in payload["authority_trace"]

def main() -> int:
    test_question_is_classified_as_rules_clarification()
    test_judge_context_reserves_complete_land_layer_evidence()
    test_plan_requires_complete_land_layer_evidence()
    test_insufficient_judge_cannot_be_reported_as_verified_or_complete()
    test_answered_deterministic_judge_has_consistent_metadata()
    print("OK: land type investigation regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
