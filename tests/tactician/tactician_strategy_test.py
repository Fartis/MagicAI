from magicai.tactician.strategy import analyze_strategy


def test_sacrifice_synergy_is_not_misclassified_as_infinite() -> None:
    payload = {
        "cards": [
            {
                "name": "Young Wolf",
                "oracle_text": (
                    "Undying (When this creature dies, if it had no +1/+1 counters "
                    "on it, return it to the battlefield under its owner's control "
                    "with a +1/+1 counter on it.)"
                ),
            },
            {
                "name": "Carrion Feeder",
                "oracle_text": (
                    "Carrion Feeder can't block.\n"
                    "Sacrifice a creature: Put a +1/+1 counter on Carrion Feeder."
                ),
            },
        ]
    }
    answer, synergies, risks = analyze_strategy("¿Es un combo?", payload)
    assert synergies
    assert "sinergia de sacrificio" in answer
    assert "No es un bucle infinito" in answer
    assert risks


def main() -> int:
    test_sacrifice_synergy_is_not_misclassified_as_infinite()
    print("OK: test_sacrifice_synergy_is_not_misclassified_as_infinite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
