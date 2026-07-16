from magicai.conversation.normalization import normalize_user_question


def test_graveyard_colloquialism_is_normalized_without_answering() -> None:
    normalized = normalize_user_question(
        "Entonces, Undying es cuando muere la criatura, no cuando pisa cementerio?",
        session_language="es",
    )
    assert normalized.language == "es"
    assert normalized.register == "casual"
    assert "es puesta en un cementerio" in normalized.canonical
    assert "graveyard_colloquial" in normalized.transformations
    assert "undying" in normalized.concepts
    assert "graveyard" in normalized.concepts


def test_casual_battlefield_wording_becomes_retrieval_friendly() -> None:
    normalized = normalize_user_question(
        "¿Pisa mesa con los contadores?",
        session_language="es",
    )
    assert "entra al campo de batalla" in normalized.canonical
    assert normalized.register == "casual"


def main() -> int:
    tests = [
        test_graveyard_colloquialism_is_normalized_without_answering,
        test_casual_battlefield_wording_becomes_retrieval_friendly,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Casual normalization tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
