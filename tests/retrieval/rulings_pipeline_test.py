from __future__ import annotations

from types import SimpleNamespace

import magicai.context_enricher as context_enricher
from magicai.context import AssistantContext
from magicai.knowledge_builder import build_knowledge


class FakeCardRepository:
    def find_by_name(self, name: str):
        return SimpleNamespace(
            name=name,
            oracle_id="oracle-test",
            mana_cost="{1}",
            type_line="Artifact",
            oracle_text="Test Oracle text.",
        )


class FakeRuleRepository:
    def find_by_keyword(self, _keyword: str):
        return None

    def search(self, _query: str, limit: int = 1):
        return []


class FakeRulingRepository:
    def find_by_oracle_id(self, oracle_id: str, *, limit: int = 8):
        assert oracle_id == "oracle-test"
        assert limit == 8
        return [
            {
                "oracle_id": oracle_id,
                "source": "wotc",
                "published_at": "2024-01-01",
                "comment": "Official clarification.",
            }
        ]


def test_explicit_rulings_request_reaches_knowledge_and_result_context() -> None:
    original_card_repo = context_enricher.CardRepository
    original_rule_repo = context_enricher.RuleRepository
    original_ruling_repo = context_enricher.RulingRepository
    original_symbols = context_enricher.extract_symbols_from_card

    context_enricher.CardRepository = FakeCardRepository
    context_enricher.RuleRepository = FakeRuleRepository
    context_enricher.RulingRepository = FakeRulingRepository
    context_enricher.extract_symbols_from_card = lambda _card: []

    try:
        context = AssistantContext(
            question="¿Qué dicen los rulings oficiales de Test Card?",
            intent="rules",
            cards=["Test Card"],
        )
        enriched = context_enricher.enrich(context)
        knowledge = build_knowledge(enriched)
    finally:
        context_enricher.CardRepository = original_card_repo
        context_enricher.RuleRepository = original_rule_repo
        context_enricher.RulingRepository = original_ruling_repo
        context_enricher.extract_symbols_from_card = original_symbols

    assert enriched.rulings == [
        {
            "oracle_id": "oracle-test",
            "source": "wotc",
            "published_at": "2024-01-01",
            "comment": "Official clarification.",
            "card_name": "Test Card",
        }
    ]
    assert "RULINGS" in knowledge
    assert "Card: Test Card" in knowledge
    assert "Official clarification." in knowledge


def main() -> int:
    tests = [test_explicit_rulings_request_reaches_knowledge_and_result_context]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Rulings pipeline tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
