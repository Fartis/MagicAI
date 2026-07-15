from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from magicai.api import routes
from magicai.api.schemas import AskRequest
from magicai.conversation.manager import ConversationManager
from magicai.conversation.models import Conversation
from magicai.conversation.repository import ConversationRepository
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_judge_result,
)


YOUNG_WOLF = {
    "name": "Young Wolf",
    "mana_cost": "{G}",
    "type_line": "Creature — Wolf",
    "oracle_text": (
        "Undying (When this creature dies, if it had no +1/+1 counters on it, "
        "return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
    ),
}

ASHNODS_ALTAR = {
    "name": "Ashnod's Altar",
    "mana_cost": "{3}",
    "type_line": "Artifact",
    "oracle_text": "Sacrifice a creature: Add {C}{C}.",
}

GHAVE = {
    "name": "Ghave, Guru of Spores",
    "mana_cost": "{2}{W}{B}{G}",
    "type_line": "Legendary Creature — Fungus Shaman",
    "oracle_text": (
        "Ghave enters with five +1/+1 counters on it.\n"
        "{1}, Remove a +1/+1 counter from a creature you control: "
        "Create a 1/1 green Saproling creature token.\n"
        "{1}, Sacrifice a creature: Put a +1/+1 counter on target creature."
    ),
}


class StrategyBoundaryAssistant:
    def ask_result(self, conversation, question):
        conversation.add_user_message(question)
        boundary = (
            "This is a strategic combo question. The Judge has recovered the requested "
            "card facts and is handing them to the Tactician."
        )
        conversation.add_assistant_message(boundary)
        conversation.active_cards = [ASHNODS_ALTAR, GHAVE]
        context = SimpleNamespace(
            question=question,
            intent="unknown",
            cards=[ASHNODS_ALTAR, GHAVE],
            rules=[{"number": "702.93", "title": "Undying"}],
            rulings=[],
            rule_queries=["undying", "sacrifice"],
        )
        return build_judge_result(
            question=question,
            answer=boundary,
            status=JudgeStatus.STRATEGY_REQUIRED,
            origin=JudgeOrigin.STRATEGY_BOUNDARY,
            confidence=JudgeConfidence.HIGH,
            context=context,
        )


def _seed_conversation(manager: ConversationManager, session_id: str) -> None:
    conversation = Conversation(active_cards=[YOUNG_WOLF])
    conversation.add_user_message("¿Qué ocurre si sacrifico Young Wolf?")
    conversation.add_assistant_message(
        "Young Wolf dies and Undying returns it with a +1/+1 counter."
    )
    manager.save(session_id, conversation)


def test_ask_automatically_hands_strategy_to_tactician() -> None:
    with TemporaryDirectory() as directory:
        manager = ConversationManager(
            ConversationRepository(Path(directory) / "handoff.sqlite3")
        )
        session_id = "handoff-session"
        _seed_conversation(manager, session_id)

        original_manager = routes.conversation_manager
        original_assistant = routes.assistant
        routes.conversation_manager = manager
        routes.assistant = StrategyBoundaryAssistant()

        try:
            response = routes.ask(
                AskRequest(
                    session_id=session_id,
                    question="¿Y tiene combo con Ghave y Ashnod's Altar?",
                )
            )
            detail = routes.get_conversation(session_id)
        finally:
            routes.conversation_manager = original_manager
            routes.assistant = original_assistant

        assert response.authority == "tactician"
        assert response.status == "answered"
        assert response.origin == "tactician_strategy"
        assert response.strategy_intent == "combo_detection"
        assert response.combo_classification == "infinite_combo"
        assert response.inherited_cards == ["Young Wolf"]
        assert [card.name for card in response.cards] == [
            "Young Wolf",
            "Ashnod's Altar",
            "Ghave, Guru of Spores",
        ]
        assert "which is better" not in response.answer.casefold()
        assert "infinite" in response.answer.casefold() or "infinito" in response.answer.casefold()

        # The Judge boundary assistant turn is replaced, not duplicated.
        assert len(detail.messages) == 4
        assert detail.messages[-2].role == "user"
        assert detail.messages[-1].role == "assistant"
        assert detail.messages[-1].content == response.answer
        assert detail.last_result["authority"] == "tactician"


def test_ask_can_expose_raw_strategy_boundary_for_diagnostics() -> None:
    with TemporaryDirectory() as directory:
        manager = ConversationManager(
            ConversationRepository(Path(directory) / "boundary.sqlite3")
        )
        session_id = "boundary-session"
        _seed_conversation(manager, session_id)

        original_manager = routes.conversation_manager
        original_assistant = routes.assistant
        routes.conversation_manager = manager
        routes.assistant = StrategyBoundaryAssistant()

        try:
            response = routes.ask(
                AskRequest(
                    session_id=session_id,
                    question="¿Y tiene combo con Ghave y Ashnod's Altar?",
                    auto_handoff=False,
                )
            )
        finally:
            routes.conversation_manager = original_manager
            routes.assistant = original_assistant

        assert response.authority == "judge"
        assert response.status == "strategy_required"
        assert response.origin == "strategy_boundary"
        assert response.combo_classification == ""


def main() -> int:
    tests = [
        test_ask_automatically_hands_strategy_to_tactician,
        test_ask_can_expose_raw_strategy_boundary_for_diagnostics,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Automatic Tactician handoff API tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
