from magicai.context_enricher import _merge_unique_queries


def test_oracle_queries_are_prioritized_without_duplicates():
    merged = _merge_unique_queries(
        preferred=[
            "activated ability",
            "mana ability",
        ],
        existing=[
            "117",
            "mana ability",
            "in response priority stack resolves",
        ],
    )

    expected = [
        "activated ability",
        "mana ability",
        "117",
        "in response priority stack resolves",
    ]

    if merged != expected:
        raise AssertionError(
            f"unexpected query priority:\nexpected={expected!r}\nactual={merged!r}"
        )


def main():
    tests = [
        test_oracle_queries_are_prioritized_without_duplicates,
    ]

    errors = []

    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")

        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}")
            print(exc)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Tests : {len(tests)}")
    print(f"Errors: {len(errors)}")

    if errors:
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
