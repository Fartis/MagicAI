from magicai.language.policy import resolve_language_policy


def test_spanish_turn_ignores_english_mtg_terms() -> None:
    decision = resolve_language_policy(
        "Entonces, Undying es cuando muere la criatura, no cuando pisa cementerio?",
        session_language="es",
    )
    assert decision.input_language == "es"
    assert decision.response_language == "es"
    assert decision.confidence == "high"


def test_ambiguous_card_only_followup_inherits_session_language() -> None:
    decision = resolve_language_policy("¿Y The Ozolith?", session_language="es")
    assert decision.response_language == "es"
    assert decision.locked is True


def test_clear_english_turn_can_change_response_language() -> None:
    decision = resolve_language_policy(
        "Why does Undying not trigger when the creature dies with a counter?",
        session_language="es",
    )
    assert decision.input_language == "en"
    assert decision.response_language == "en"


def main() -> int:
    tests = [
        test_spanish_turn_ignores_english_mtg_terms,
        test_ambiguous_card_only_followup_inherits_session_language,
        test_clear_english_turn_can_change_response_language,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Language policy tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
