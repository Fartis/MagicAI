from __future__ import annotations

from types import SimpleNamespace

from magicai.judge_tools.models import JudgeToolResult, JudgeToolStatus


YOUNG_WOLF = {
    "name": "Young Wolf",
    "oracle_id": "wolf",
    "oracle_text": (
        "Undying (When this creature dies, if it had no +1/+1 counters on it, "
        "return it to the battlefield under its owner's control with a +1/+1 counter on it.)"
    ),
}
CARRION_FEEDER = {
    "name": "Carrion Feeder",
    "oracle_id": "feeder",
    "oracle_text": "Sacrifice a creature: Put a +1/+1 counter on this creature.",
}
OZOLITH = {
    "name": "The Ozolith",
    "oracle_id": "ozolith",
    "oracle_text": (
        "Whenever a creature you control leaves the battlefield, if it had counters on it, "
        "put those counters on The Ozolith."
    ),
}
ALTAR = {
    "name": "Ashnod's Altar",
    "oracle_id": "altar",
    "oracle_text": "Sacrifice a creature: Add {C}{C}.",
}
GHAVE = {
    "name": "Ghave, Guru of Spores",
    "oracle_id": "ghave",
    "oracle_text": (
        "Ghave enters with five +1/+1 counters on it.\n"
        "{1}, Remove a +1/+1 counter from a creature you control: Create a 1/1 green Saproling creature token.\n"
        "{1}, Sacrifice a creature: Put a +1/+1 counter on target creature."
    ),
}

ALL_CARDS = {
    card["name"].casefold(): card
    for card in (YOUNG_WOLF, CARRION_FEEDER, OZOLITH, ALTAR, GHAVE)
}


class ConversationFixtureJudge:
    def __init__(self, *, behavior: str = "normal") -> None:
        self.behavior = behavior

    def ask_result(self, conversation, question):
        cards = self._cards_for_turn(conversation, question)
        normalized = question.casefold()
        is_strategy = any(marker in normalized for marker in (
            "combo", "bucle", "infinito", "orden", "cort", "interrump", "necesito", "requisitos",
            "loop", "sequence", "disrupt", "what do i need",
        ))

        if self.behavior == "drift" and any(marker in normalized for marker in ("pisa cementerio", "mismo evento", "muere", "morir", "no simplemente")):
            answer = "Cuando un jugador pierde el juego, se comprueban habilidades disparadas por perder la partida."
            status = "answered"
            origin = "llm_validated"
        elif is_strategy and len(cards) >= 2:
            answer = "The Judge recovered the factual package and hands strategic synthesis to the Tactician."
            status = "strategy_required"
            origin = "strategy_boundary"
        else:
            asks_with_counter = any(marker in normalized for marker in (
                "con un contador", "ya tenía contador", "ya tenia contador", "with a +1/+1 counter",
            ))
            if asks_with_counter:
                answer = (
                    "Al sacrificar Young Wolf, pasa del campo de batalla al cementerio y muere. "
                    "Como ya tenía un contador +1/+1, Undying no se dispara y permanece en el cementerio."
                )
            else:
                answer = (
                    "Al sacrificar Young Wolf, pasa del campo de batalla al cementerio y muere. "
                    "Si no tenía contadores +1/+1, Undying se dispara y, cuando se resuelve, "
                    "vuelve al campo de batalla bajo el control de su propietario con un contador +1/+1."
                )
            if getattr(conversation, "language", "") == "en":
                if asks_with_counter:
                    answer = (
                        "When Young Wolf is sacrificed, it moves from the battlefield to the graveyard and dies. "
                        "Because it already had a +1/+1 counter, Undying does not trigger and it remains in the graveyard."
                    )
                else:
                    answer = (
                        "When Young Wolf is sacrificed, it moves from the battlefield to the graveyard and dies. "
                        "If it had no +1/+1 counters, Undying triggers and returns it with a +1/+1 counter when it resolves."
                    )
            status = "answered"
            origin = "deterministic_rule"

        return SimpleNamespace(to_dict=lambda: {
            "schema_version": "1.0",
            "question": question,
            "answer": answer,
            "status": status,
            "origin": origin,
            "confidence": "high",
            "authority": "judge",
            "cards": cards,
            "rules": [],
            "rulings": [],
            "retrieval_queries": [],
            "assumptions": [],
            "warnings": [],
            "source_versions": {},
            "source_health": {},
            "validation_attempts": 0,
            "reviewed_by": [],
            "review_challenges": [],
            "llm_called": origin == "llm_validated",
            "timings": {},
        })

    def _cards_for_turn(self, conversation, question: str) -> list[dict]:
        normalized = question.casefold()
        explicit = [card for name, card in ALL_CARDS.items() if name in normalized]
        if explicit:
            names = {card["name"] for card in explicit}
            if "Ghave, Guru of Spores" in names or "Ashnod's Altar" in names:
                return [YOUNG_WOLF, ALTAR, GHAVE]
            if "Carrion Feeder" in names or "The Ozolith" in names:
                return [YOUNG_WOLF, CARRION_FEEDER, OZOLITH]
            return explicit
        if conversation.active_cards:
            return list(conversation.active_cards)
        return [YOUNG_WOLF]

    @staticmethod
    def _english(question: str) -> bool:
        normalized = question.casefold()
        return any(marker in normalized for marker in ("what happens", "if i", "does undying", "why does"))


class ConversationFixtureGateway:
    def execute(self, request, *, conversation=None, budget=None):
        if request.tool == "oracle_lookup":
            evidence = [
                {"kind": "card", "identifier": ALL_CARDS[name.casefold()]["oracle_id"], "data": ALL_CARDS[name.casefold()]}
                for name in request.arguments.get("card_names", [])
                if name.casefold() in ALL_CARDS
            ]
            authority = "official_card_data"
        elif request.tool == "rules_lookup":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": identifier,
                    "data": {"number": identifier, "title": f"Rule {identifier}", "rules": []},
                }
                for identifier in request.arguments.get("identifiers", [])
            ]
            authority = "official_rules"
        elif request.tool == "rulings_lookup":
            evidence = [{
                "kind": "ruling",
                "identifier": "ozolith:2020-04-17",
                "data": {
                    "oracle_id": "ozolith",
                    "card_name": "The Ozolith",
                    "published_at": "2020-04-17",
                    "source": "wotc",
                    "comment": "The Ozolith does not move counters off the creature that left the battlefield.",
                },
            }]
            authority = "official_rulings"
        else:
            raise AssertionError(f"unexpected fixture tool: {request.tool}")

        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS,
            authority=authority,
            provider="conversation_fixture",
            purpose=request.purpose,
            arguments=request.arguments,
            evidence=evidence,
            budget=budget.snapshot() if budget else {},
        )
