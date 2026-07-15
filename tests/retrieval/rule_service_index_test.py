from magicai.services.rule_service import (
    clear_rule_caches,
    find_rule,
    rule_search_cache_info,
    search_rules,
    warm_rule_index,
)


def test_index_builds_once_and_is_reused():
    clear_rule_caches(reset_index=True)
    first = warm_rule_index()
    second = warm_rule_index()
    assert first["sections"] > 0
    assert first["terms"] > 0
    assert first["builds"] == 1
    assert second["builds"] == 1


def test_repeated_search_uses_lru_cache_without_changing_results():
    clear_rule_caches(reset_index=False)
    first = search_rules("mana abilities do not use the stack", limit=3)
    before = rule_search_cache_info()["search_rules"]
    second = search_rules("mana abilities do not use the stack", limit=3)
    after = rule_search_cache_info()["search_rules"]
    assert first == second
    assert after["hits"] == before["hits"] + 1
    assert any(str(item.get("number", "")).startswith("605") for item in first)


def test_repeated_find_rule_uses_lru_cache():
    clear_rule_caches(reset_index=False)
    first = find_rule("113.7a")
    before = rule_search_cache_info()["find_rule"]
    second = find_rule("113.7a")
    after = rule_search_cache_info()["find_rule"]
    assert first == second
    assert first is not None
    assert after["hits"] == before["hits"] + 1


def test_priority_query_keeps_rule_117_near_the_top():
    results = search_rules("timing and priority player receives priority", limit=5)
    numbers = [str(item.get("number", "")) for item in results]
    assert any(number.startswith("117") for number in numbers[:3]), numbers


def main():
    tests = [
        test_index_builds_once_and_is_reused,
        test_repeated_search_uses_lru_cache_without_changing_results,
        test_repeated_find_rule_uses_lru_cache,
        test_priority_query_keeps_rule_117_near_the_top,
    ]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}\n{exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
