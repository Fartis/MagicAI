from pathlib import Path

from tests.quality.tactician_conversations import load_scenarios
from tests.quality.tactician_conversations.semantic_assertions import known_concepts


CASES = Path(__file__).parent / "cases" / "tactician_conversations"


def test_conversation_case_contract_is_loadable() -> None:
    scenarios = load_scenarios(CASES)
    assert len(scenarios) == 40
    assert len({scenario["id"] for scenario in scenarios}) == 40
    assert sum(len(scenario["turns"]) for scenario in scenarios) == 58
    allowed_concepts = known_concepts()
    for scenario in scenarios:
        assert scenario["language"] in {"es", "en"}
        for turn in scenario["turns"]:
            assert turn["question"].strip()
            expected = turn["expect"]
            assert isinstance(expected, dict)
            assert set(expected.get("required_concepts", [])) <= allowed_concepts
            assert set(expected.get("forbidden_concepts", [])) <= allowed_concepts


def main() -> int:
    test_conversation_case_contract_is_loadable()
    print("OK: test_conversation_case_contract_is_loadable")
    print("Tactician conversation contract tests: 40 scenarios / 58 turns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
