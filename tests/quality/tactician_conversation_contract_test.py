from pathlib import Path

from tests.quality.tactician_conversations import load_scenarios


CASES = Path(__file__).parent / "cases" / "tactician_conversations" / "sprint12_2c.json"


def test_conversation_case_contract_is_loadable() -> None:
    scenarios = load_scenarios(CASES)
    assert scenarios[0]["id"] == "TACT-CONV-OZOLITH-001"
    assert len(scenarios[0]["turns"]) == 2
    for turn in scenarios[0]["turns"]:
        assert turn["question"].strip()
        assert isinstance(turn["expect"], dict)


def main() -> int:
    test_conversation_case_contract_is_loadable()
    print("OK: test_conversation_case_contract_is_loadable")
    print("Tactician conversation contract tests: 1/1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
