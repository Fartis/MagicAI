from magicai.tactician.intents import StrategyIntent
from magicai.tactician.strategy import analyze_strategy


def _young_wolf() -> dict:
    return {
        "name": "Young Wolf",
        "oracle_text": (
            "Undying (When this creature dies, if it had no +1/+1 counters "
            "on it, return it to the battlefield under its owner's control "
            "with a +1/+1 counter on it.)"
        ),
    }


def test_sacrifice_synergy_is_not_misclassified_as_infinite() -> None:
    payload = {
        "cards": [
            _young_wolf(),
            {
                "name": "Carrion Feeder",
                "oracle_text": (
                    "Carrion Feeder can't block.\n"
                    "Sacrifice a creature: Put a +1/+1 counter on Carrion Feeder."
                ),
            },
        ]
    }
    analysis = analyze_strategy(
        "¿Es un combo?",
        payload,
        intent=StrategyIntent.COMBO_DETECTION,
    )
    assert analysis.synergies
    assert "sinergia de sacrificio" in analysis.answer
    assert "No es un bucle infinito" in analysis.answer
    assert analysis.combo_classification == "repeatable_synergy"
    assert analysis.risks


def test_generic_three_piece_undying_loop_is_detected() -> None:
    payload = {
        "cards": [
            _young_wolf(),
            {
                "name": "Ashnod's Altar",
                "oracle_text": "Sacrifice a creature: Add {C}{C}.",
            },
            {
                "name": "Ghave, Guru of Spores",
                "oracle_text": (
                    "Ghave enters with five +1/+1 counters on it.\n"
                    "{1}, Remove a +1/+1 counter from a creature you control: "
                    "Create a 1/1 green Saproling creature token.\n"
                    "{1}, Sacrifice a creature: Put a +1/+1 counter on target creature."
                ),
            },
        ]
    }
    analysis = analyze_strategy(
        "¿Tienen combo infinito?",
        payload,
        intent=StrategyIntent.COMBO_DETECTION,
    )
    assert analysis.combo_classification == "infinite_combo"
    assert len(analysis.combo_steps) == 4
    assert any("maná incoloro neto" in outcome for outcome in analysis.outcomes)
    assert any("ficha adicional" in outcome for outcome in analysis.outcomes)
    assert "forman un combo infinito" in analysis.answer


def main() -> int:
    tests = [
        test_sacrifice_synergy_is_not_misclassified_as_infinite,
        test_generic_three_piece_undying_loop_is_detected,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician strategy tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
