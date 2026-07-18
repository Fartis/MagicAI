from __future__ import annotations

from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus
from magicai.tactician.core import Tactician


YOUNG_WOLF = {
    "name": "Young Wolf",
    "oracle_id": "wolf",
    "oracle_text": (
        "Undying (When this creature dies, if it had no +1/+1 counters on it, "
        "return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
    ),
}
CARRION_FEEDER = {
    "name": "Carrion Feeder",
    "oracle_id": "feeder",
    "oracle_text": "Sacrifice a creature: Put a +1/+1 counter on this creature.",
}
GENERIC_CARD = {
    "name": "Example Adept",
    "oracle_id": "example",
    "oracle_text": "Whenever this creature attacks, draw a card.",
}
OZOLITH = {
    "name": "The Ozolith",
    "oracle_id": "ozolith",
    "oracle_text": (
        "Whenever a creature you control leaves the battlefield, if it had counters on it, "
        "put those counters on The Ozolith."
    ),
}


class FixtureJudge:
    def __init__(self, *, drift: bool = False) -> None:
        self.drift = drift

    def ask_result(self, conversation, question):
        if "Carrion" in question or "Ozolith" in question or conversation.active_cards:
            cards = list(conversation.active_cards or [YOUNG_WOLF, CARRION_FEEDER, OZOLITH])
        else:
            cards = [YOUNG_WOLF]
        answer = (
            "Cuando un jugador pierde el juego, se comprueban habilidades disparadas."
            if self.drift
            else (
                "Al sacrificar Young Wolf, pasa del campo de batalla al cementerio y muere. "
                "Si no tenía contadores +1/+1, Undying se dispara y vuelve con un contador +1/+1."
            )
        )
        return SimpleNamespace(to_dict=lambda: {
            "schema_version": "1.0",
            "question": question,
            "answer": answer,
            "status": "answered",
            "origin": "llm_validated" if self.drift else "deterministic_rule",
            "confidence": "high",
            "authority": "judge",
            "cards": cards,
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
            "llm_called": self.drift,
            "timings": {},
        })


class FixtureGateway:
    def execute(self, request, *, conversation=None, budget=None):
        if request.tool == "oracle_lookup":
            lookup = {
                "young wolf": YOUNG_WOLF,
                "carrion feeder": CARRION_FEEDER,
                "the ozolith": OZOLITH,
                "example adept": GENERIC_CARD,
            }
            evidence = [
                {"kind": "card", "identifier": lookup[name.casefold()]["oracle_id"], "data": lookup[name.casefold()]}
                for name in request.arguments.get("card_names", [])
                if name.casefold() in lookup
            ]
            authority = "official_card_data"
        elif request.tool == "rules_lookup":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": identifier,
                    "data": {"number": identifier, "title": f"Rule {identifier}", "rules": []},
                }
                for identifier in request.arguments.get("identifiers", [])
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
            provider="fixture",
            purpose=request.purpose,
            arguments=request.arguments,
            evidence=evidence,
            budget=budget.snapshot() if budget else {},
        )


def test_rules_turn_is_judge_led_and_preserves_factual_core() -> None:
    conversation = Conversation(language="es")
    result = Tactician(judge=FixtureJudge(), tool_gateway=FixtureGateway()).ask_result(
        conversation,
        "¿Qué ocurre si sacrifico Young Wolf?",
    )
    payload = result.to_dict()

    assert payload["strategy_intent"] == "mechanic_resolution"
    assert payload["response_mode"] == "judge_led"
    assert payload["combo_classification"] == "not_applicable"
    assert payload["factual_core_preserved"] is True
    assert payload["factual_core_coverage"]["complete"] is True
    assert payload["factual_core_coverage"]["covered"] >= 1
    assert payload["answer_complete"] is True
    assert payload["judge_verified"] is True
    assert "pasa del campo de batalla al cementerio" in payload["answer"]
    assert "bucle infinito" not in payload["answer"]




class GenericRuleJudge:
    def ask_result(self, conversation, question):
        return SimpleNamespace(to_dict=lambda: {
            "schema_version": "1.0",
            "question": question,
            "answer": "Sí. Una habilidad disparada usa la pila y los jugadores pueden responder antes de que se resuelva.",
            "status": "answered",
            "origin": "deterministic_rule",
            "confidence": "high",
            "authority": "judge",
            "cards": [GENERIC_CARD],
            "rules": [{"number": "603", "title": "Handling Triggered Abilities"}],
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
        })


def test_judge_led_preservation_is_card_agnostic() -> None:
    conversation = Conversation(language="es")
    result = Tactician(judge=GenericRuleJudge(), tool_gateway=FixtureGateway()).ask_result(
        conversation,
        "¿Se puede responder a la habilidad disparada de Example Adept?",
    )
    payload = result.to_dict()

    assert payload["response_mode"] == "judge_led"
    assert payload["combo_classification"] == "not_applicable"
    assert payload["factual_core_preserved"] is True
    assert payload["answer"] == payload["judge_result"]["answer"]
    assert payload["factual_core_coverage"]["complete"] is True

def test_drifted_judge_answer_is_not_relayed() -> None:
    conversation = Conversation(
        language="es",
        active_cards=[YOUNG_WOLF, CARRION_FEEDER, OZOLITH],
        strategy_context={"combo_classification": "non_combo"},
    )
    result = Tactician(judge=FixtureJudge(drift=True), tool_gateway=FixtureGateway()).ask_result(
        conversation,
        "Entonces, ¿Undying es cuando muere la criatura, no cuando pisa cementerio?",
    )
    payload = result.to_dict()

    assert payload["response_mode"] == "judge_led"
    assert payload["strategy_intent"] == "mechanic_equivalence"
    assert payload["combo_classification"] == "non_combo"
    assert payload["factual_core_preserved"] is True
    assert payload["answer_complete"] is True
    assert "mismo evento" in payload["answer"]
    assert "jugador pierde el juego" not in payload["answer"]


def test_combo_question_remains_tactician_led() -> None:
    conversation = Conversation(language="es", active_cards=[YOUNG_WOLF, CARRION_FEEDER, OZOLITH])
    result = Tactician(judge=FixtureJudge(), tool_gateway=FixtureGateway()).ask_result(
        conversation,
        "¿Young Wolf, Carrion Feeder y The Ozolith hacen combo?",
    )
    payload = result.to_dict()

    assert payload["response_mode"] == "tactician_led"
    assert payload["strategy_intent"] == "combo_detection"
    assert payload["combo_classification"] == "non_combo"
    assert payload["tactician_synthesized"] is True


def test_incorrect_combo_hypothesis_is_hybrid() -> None:
    conversation = Conversation(language="es", active_cards=[YOUNG_WOLF, CARRION_FEEDER, OZOLITH])
    result = Tactician(judge=FixtureJudge(), tool_gateway=FixtureGateway()).ask_result(
        conversation,
        "Pero The Ozolith se lleva el contador antes, por lo que Undying se dispara otra vez.",
    )
    payload = result.to_dict()

    assert payload["response_mode"] == "hybrid"
    assert payload["strategy_intent"] == "interaction_hypothesis"
    assert payload["combo_classification"] == "non_combo"
    assert any(item["verdict"] == "contradicted" for item in payload["claim_verdicts"])
    assert "Undying no se dispara" in " ".join(payload["combo_steps"])


def main() -> int:
    tests = [
        test_rules_turn_is_judge_led_and_preserves_factual_core,
        test_judge_led_preservation_is_card_agnostic,
        test_drifted_judge_answer_is_not_relayed,
        test_combo_question_remains_tactician_led,
        test_incorrect_combo_hypothesis_is_hybrid,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician response orchestration tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
