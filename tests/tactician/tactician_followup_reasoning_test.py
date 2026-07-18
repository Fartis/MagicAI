from __future__ import annotations

from types import SimpleNamespace

from magicai.tactician.core import Tactician


YOUNG_WOLF = {
    "name": "Young Wolf",
    "oracle_text": "Undying (When this creature dies, return it with a +1/+1 counter.)",
}
ALTAR = {
    "name": "Ashnod's Altar",
    "oracle_text": "Sacrifice a creature: Add {C}{C}.",
}
GHAVE = {
    "name": "Ghave, Guru of Spores",
    "oracle_text": (
        "{1}, Remove a +1/+1 counter from a creature you control: "
        "Create a 1/1 green Saproling creature token."
    ),
}


def _judge_result(cards=None):
    return SimpleNamespace(
        to_dict=lambda: {
            "question": "follow-up",
            "answer": "Generic Judge boundary.",
            "status": "strategy_required",
            "origin": "strategy_boundary",
            "confidence": "high",
            "authority": "judge",
            "cards": cards or [],
            "rules": [],
            "rulings": [],
            "retrieval_queries": [],
            "assumptions": [],
            "warnings": [],
            "source_versions": {},
            "source_health": {},
        }
    )


def test_play_sequence_inherits_active_combo_cards() -> None:
    result = Tactician().from_judge_result(
        question="¿En qué orden se juega?",
        judge_result=_judge_result(),
        prior_cards=[YOUNG_WOLF, ALTAR, GHAVE],
    )
    payload = result.to_dict()
    assert payload["strategy_intent"] == "play_sequence"
    assert payload["combo_classification"] == "infinite_combo"
    assert payload["inherited_cards"] == ["Young Wolf", "Ashnod's Altar", "Ghave, Guru of Spores"]
    assert "orden de despliegue" in payload["answer"]
    assert payload["combo_steps"]


def test_disruption_followup_identifies_interaction_windows() -> None:
    result = Tactician().from_judge_result(
        question="¿Dónde pueden cortarlo?",
        judge_result=_judge_result(),
        prior_cards=[YOUNG_WOLF, ALTAR, GHAVE],
    )
    payload = result.to_dict()
    assert payload["strategy_intent"] == "combo_disruption"
    assert "exiliar Young Wolf" in payload["answer"]
    assert "Ghave" in payload["answer"]
    assert payload["risks"]


def main() -> int:
    tests = [
        test_play_sequence_inherits_active_combo_cards,
        test_disruption_followup_identifies_interaction_windows,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician follow-up reasoning tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
