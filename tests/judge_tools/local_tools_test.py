from __future__ import annotations

from types import SimpleNamespace

from magicai.conversation.models import Conversation, Message
from magicai.judge_tools.models import JudgeToolStatus
from magicai.judge_tools.tools import (
    ConversationContextTool,
    LegalityCheckTool,
    OracleLookupTool,
    RulesLookupTool,
    RulesSearchTool,
    RulingsLookupTool,
)


YOUNG_WOLF = SimpleNamespace(
    oracle_id="oracle-young-wolf",
    id="printing-young-wolf",
    name="Young Wolf",
    mana_cost="{G}",
    cmc=1.0,
    type_line="Creature — Wolf",
    oracle_text="Undying",
    power="1",
    toughness="1",
    loyalty=None,
    defense=None,
    colors=["G"],
    color_identity=["G"],
    keywords=["Undying"],
    legalities={"commander": "legal", "modern": "legal"},
    rarity="common",
    released_at="2026-01-01",
    scryfall_uri="https://example.invalid/young-wolf",
    rulings_uri="https://example.invalid/rulings",
)


class FakeCardRepository:
    def find_by_name(self, name):
        return YOUNG_WOLF if name.casefold() == "young wolf" else None


class FakeRuleRepository:
    def find_by_keyword(self, identifier):
        if identifier.casefold() in {"702.93", "undying"}:
            return {
                "number": "702.93",
                "title": "Undying",
                "rules": [("702.93a", "Undying is a triggered ability.")],
            }
        return None

    def search(self, query, limit=5):
        return [self.find_by_keyword("702.93")] if "undying" in query.casefold() else []


class FakeRulingRepository:
    def find_by_oracle_id(self, oracle_id, *, limit=8):
        if oracle_id != "oracle-young-wolf":
            return []
        return [
            {
                "oracle_id": oracle_id,
                "source": "scryfall",
                "published_at": "2026-01-01",
                "comment": "Test ruling.",
            }
        ][:limit]


def test_oracle_and_legality_tools_return_structured_evidence() -> None:
    oracle = OracleLookupTool(FakeCardRepository())(
        {"card_names": ["Young Wolf", "Missing Card"]},
        result_limit=8,
    )
    legality = LegalityCheckTool(FakeCardRepository())(
        {"card_names": ["Young Wolf"], "formats": ["commander"]},
        result_limit=8,
    )

    assert oracle.status is JudgeToolStatus.SUCCESS
    assert oracle.evidence[0]["data"]["oracle_text"] == "Undying"
    assert oracle.warnings
    assert legality.evidence[0]["data"]["legalities"] == {"commander": "legal"}


def test_rules_and_rulings_tools_preserve_source_identifiers() -> None:
    rules_lookup = RulesLookupTool(FakeRuleRepository())(
        {"identifiers": ["702.93"]},
        result_limit=8,
    )
    rules_search = RulesSearchTool(FakeRuleRepository())(
        {"query": "undying trigger", "limit": 3},
        result_limit=8,
    )
    rulings = RulingsLookupTool(
        FakeCardRepository(),
        FakeRulingRepository(),
    )(
        {"card_names": ["Young Wolf"]},
        result_limit=8,
    )

    assert rules_lookup.evidence[0]["identifier"] == "702.93"
    assert rules_search.evidence[0]["data"]["rules"][0]["number"] == "702.93a"
    assert rulings.evidence[0]["data"]["card_name"] == "Young Wolf"


def test_conversation_context_is_bounded_and_structured() -> None:
    conversation = Conversation(
        history=[
            Message(role="user", content="First"),
            Message(role="assistant", content="Second"),
            Message(role="user", content="Third"),
        ],
        active_cards=[YOUNG_WOLF],
        active_rules=["702.93"],
        last_intent="combo_detection",
    )
    result = ConversationContextTool()(
        {"include_history": True, "history_limit": 2},
        conversation=conversation,
        result_limit=1,
    )
    data = result.evidence[0]["data"]
    assert data["active_cards"][0]["name"] == "Young Wolf"
    assert data["active_rules"] == ["702.93"]
    assert [item["content"] for item in data["recent_history"]] == ["Second", "Third"]


def main() -> int:
    tests = [
        test_oracle_and_legality_tools_return_structured_evidence,
        test_rules_and_rulings_tools_preserve_source_identifiers,
        test_conversation_context_is_bounded_and_structured,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Local Judge tool tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
