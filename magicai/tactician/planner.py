from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from magicai.judge_tools import JudgeToolRequest
from magicai.tactician.input_analysis import InputAnalysis


@dataclass(slots=True)
class InvestigationPlan:
    requests: list[JudgeToolRequest] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "queries_planned": len(self.requests),
            "goals": list(self.goals),
            "requests": [request.to_dict() for request in self.requests],
        }


def plan_investigation(
    analysis: InputAnalysis,
    *,
    cards: list[dict[str, Any]],
    oracle_already_refreshed: bool = False,
) -> InvestigationPlan:
    requests: list[JudgeToolRequest] = []
    goals: list[str] = []
    names = [str(card.get("name", "")).strip() for card in cards if card.get("name")]

    if names and not oracle_already_refreshed:
        requests.append(
            JudgeToolRequest(
                tool="oracle_lookup",
                arguments={"card_names": names},
                purpose="verify_input_cards",
                result_limit=min(max(len(names), 1), 20),
            )
        )
        goals.append("Verify the current Oracle text for every referenced card.")

    rules: list[str] = []
    concepts = set(analysis.concepts)
    if "sacrifice" in concepts or "dies" in concepts:
        rules.extend(["701.21a", "700.4"])
        goals.append("Verify the sacrifice-to-dies transition.")
    if "undying" in concepts or any("Undying" in str(card.get("oracle_text", "")) for card in cards):
        rules.extend(["702.93a", "603.4"])
        goals.append("Verify the Undying trigger condition.")
    if {"counters", "ozolith", "leaves_battlefield", "last_known_information"} & concepts:
        rules.extend(["122.2", "400.7", "603.6c", "603.10a"])
        goals.append("Verify counter persistence and leaves-the-battlefield timing.")

    rules = _deduplicate(rules)
    if rules:
        requests.append(
            JudgeToolRequest(
                tool="rules_lookup",
                arguments={"identifiers": rules},
                purpose="verify_claim_timing_and_state",
                result_limit=min(len(rules), 20),
            )
        )

    if any(name.casefold() == "the ozolith" for name in names):
        requests.append(
            JudgeToolRequest(
                tool="rulings_lookup",
                arguments={"card_names": ["The Ozolith"]},
                purpose="check_ozolith_rulings",
                result_limit=8,
            )
        )
        goals.append("Check official rulings for The Ozolith when available.")

    return InvestigationPlan(requests=requests, goals=_deduplicate(goals))


def _deduplicate(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
