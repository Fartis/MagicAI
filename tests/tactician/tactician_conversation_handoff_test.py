from types import SimpleNamespace

from magicai.conversation.models import Conversation, Message
from magicai.tactician.core import Tactician, replace_boundary_answer


YOUNG_WOLF = {
    "name": "Young Wolf",
    "mana_cost": "{G}",
    "type_line": "Creature — Wolf",
    "oracle_text": (
        "Undying (When this creature dies, if it had no +1/+1 counters on it, "
        "return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
    ),
}


def _judge_result():
    return SimpleNamespace(
        to_dict=lambda: {
            "schema_version": "1.0",
            "question": "¿Y tiene combo con Ghave y Ashnod's Altar?",
            "answer": "The Judge recovered a strategic factual package.",
            "status": "strategy_required",
            "origin": "strategy_boundary",
            "confidence": "high",
            "authority": "judge",
            "intent": "unknown",
            "cards": [
                {
                    "name": "Ashnod's Altar",
                    "mana_cost": "{3}",
                    "type_line": "Artifact",
                    "oracle_text": "Sacrifice a creature: Add {C}{C}.",
                },
                {
                    "name": "Ghave, Guru of Spores",
                    "mana_cost": "{2}{W}{B}{G}",
                    "type_line": "Legendary Creature — Fungus Shaman",
                    "oracle_text": (
                        "Ghave enters with five +1/+1 counters on it.\n"
                        "{1}, Remove a +1/+1 counter from a creature you control: "
                        "Create a 1/1 green Saproling creature token.\n"
                        "{1}, Sacrifice a creature: Put a +1/+1 counter on target creature."
                    ),
                },
            ],
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


def test_follow_up_inherits_prior_judge_card_and_detects_combo() -> None:
    result = Tactician().from_judge_result(
        question="¿Y tiene combo con Ghave y Ashnod's Altar?",
        judge_result=_judge_result(),
        prior_cards=[YOUNG_WOLF],
    )
    payload = result.to_dict()
    assert [card["name"] for card in payload["cards"]] == [
        "Young Wolf",
        "Ashnod's Altar",
        "Ghave, Guru of Spores",
    ]
    assert payload["inherited_cards"] == ["Young Wolf"]
    assert payload["strategy_intent"] == "combo_detection"
    assert payload["combo_classification"] == "infinite_combo"
    assert payload["authority"] == "tactician"
    assert "which is better" not in payload["answer"].casefold()


def test_automatic_handoff_replaces_boundary_without_duplicate_turns() -> None:
    conversation = Conversation(
        history=[
            Message(role="user", content="¿Qué ocurre si sacrifico Young Wolf?"),
            Message(role="assistant", content="Young Wolf vuelve con Undying."),
            Message(role="user", content="¿Y tiene combo con Ghave y Ashnod's Altar?"),
            Message(role="assistant", content="Boundary answer"),
        ],
        active_cards=[YOUNG_WOLF],
    )
    result = Tactician().from_judge_result(
        question="¿Y tiene combo con Ghave y Ashnod's Altar?",
        judge_result=_judge_result(),
        prior_cards=[YOUNG_WOLF],
    )
    replace_boundary_answer(conversation, result)
    assert len(conversation.history) == 4
    assert conversation.history[-1].content == result.answer
    assert conversation.mode == "tactician"
    assert [card["name"] for card in conversation.active_cards] == [
        "Young Wolf",
        "Ashnod's Altar",
        "Ghave, Guru of Spores",
    ]


def main() -> int:
    tests = [
        test_follow_up_inherits_prior_judge_card_and_detects_combo,
        test_automatic_handoff_replaces_boundary_without_duplicate_turns,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician handoff tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
