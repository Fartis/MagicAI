from types import SimpleNamespace

from magicai.conversation.models import Conversation
from magicai.tactician.core import Tactician


class FakeJudge:
    def ask_result(self, conversation, question):
        conversation.active_cards = [SimpleNamespace(name="Young Wolf"), SimpleNamespace(name="Carrion Feeder")]
        conversation.active_keywords = ["undying"]
        conversation.last_intent = "strategy"
        return SimpleNamespace(
            to_dict=lambda: {
                "schema_version": "1.0",
                "question": question,
                "answer": "La recomendación corresponde al Estratega.",
                "status": "strategy_required",
                "origin": "strategy_boundary",
                "confidence": "high",
                "authority": "judge",
                "intent": "strategy",
                "cards": [
                    {
                        "name": "Young Wolf",
                        "mana_cost": "{G}",
                        "type_line": "Creature — Wolf",
                        "oracle_text": "Undying (When this creature dies, return it with a +1/+1 counter.)",
                    },
                    {
                        "name": "Carrion Feeder",
                        "mana_cost": "{B}",
                        "type_line": "Creature — Zombie",
                        "oracle_text": "Sacrifice a creature: Put a +1/+1 counter on Carrion Feeder.",
                    },
                ],
                "rules": [],
                "rulings": [],
                "retrieval_queries": [],
                "assumptions": [],
                "warnings": [],
                "source_versions": {},
                "source_health": {},
                "validation_attempts": 0,
            }
        )


def test_tactician_consumes_judge_package_without_direct_sources() -> None:
    conversation = Conversation()
    result = Tactician(judge=FakeJudge()).ask_result(
        conversation,
        "¿Young Wolf y Carrion Feeder son un combo?",
    )
    payload = result.to_dict()
    assert payload["authority"] == "tactician"
    assert payload["judge_result"]["authority"] == "judge"
    assert payload["authority_trace"] == [
        "judge:factual_evidence",
        "tactician:strategic_interpretation",
    ]
    assert "sinergia de sacrificio" in payload["answer"]
    assert "No es un bucle infinito" in payload["answer"]
    assert conversation.mode == "tactician"
    assert [message.role for message in conversation.history] == ["user", "assistant"]


def main() -> int:
    test_tactician_consumes_judge_package_without_direct_sources()
    print("OK: test_tactician_consumes_judge_package_without_direct_sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
