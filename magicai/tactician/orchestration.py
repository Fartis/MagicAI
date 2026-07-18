from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from magicai.tactician.input_analysis import InputAnalysis
from magicai.tactician.intents import StrategyIntent


class ResponseMode(str, Enum):
    """Profile that owns the wording of the final response."""

    JUDGE_LED = "judge_led"
    TACTICIAN_LED = "tactician_led"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class ResponseDecision:
    mode: ResponseMode
    reason: str
    factual_core_required: bool
    strategic_extension_required: bool
    combo_analysis_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "reason": self.reason,
            "factual_core_required": self.factual_core_required,
            "strategic_extension_required": self.strategic_extension_required,
            "combo_analysis_required": self.combo_analysis_required,
        }


_JUDGE_LED_INTENTS = {
    StrategyIntent.MECHANIC_RESOLUTION,
    StrategyIntent.RULES_CLARIFICATION,
    StrategyIntent.MECHANIC_DEFINITION,
    StrategyIntent.MECHANIC_EQUIVALENCE,
}

_TACTICIAN_LED_INTENTS = {
    StrategyIntent.COMBO_DETECTION,
    StrategyIntent.SYNERGY_ANALYSIS,
    StrategyIntent.CARD_COMPARISON,
    StrategyIntent.PLAY_RECOMMENDATION,
    StrategyIntent.DECKBUILDING,
    StrategyIntent.PLAY_SEQUENCE,
    StrategyIntent.COMBO_DISRUPTION,
    StrategyIntent.COMBO_REQUIREMENTS,
}

_COMBO_INTENTS = {
    StrategyIntent.COMBO_DETECTION,
    StrategyIntent.COMBO_FAILURE_EXPLANATION,
    StrategyIntent.PLAY_SEQUENCE,
    StrategyIntent.COMBO_DISRUPTION,
    StrategyIntent.COMBO_REQUIREMENTS,
}


def choose_response_mode(
    analysis: InputAnalysis,
    *,
    judge_payload: dict[str, Any],
    cards: list[dict[str, Any]],
    strategy_context: dict[str, Any] | None = None,
) -> ResponseDecision:
    """Choose whether the Judge or Tactician should lead the final answer.

    The decision is semantic rather than profile-based: a user may be talking to
    the Tactician while asking a pure rules question. In that case, the Judge's
    professional factual answer remains the core of the response.
    """

    intent = analysis.strategy_intent
    context = strategy_context or {}

    if intent is StrategyIntent.INTERACTION_TIMING:
        if len(cards) >= 2:
            return ResponseDecision(
                mode=ResponseMode.HYBRID,
                reason="The timing question applies a rules window to an active multi-card interaction.",
                factual_core_required=True,
                strategic_extension_required=True,
                combo_analysis_required=True,
            )
        return ResponseDecision(
            mode=ResponseMode.JUDGE_LED,
            reason="The turn asks for the timing of a single rules event.",
            factual_core_required=True,
            strategic_extension_required=False,
            combo_analysis_required=False,
        )

    if intent in _JUDGE_LED_INTENTS:
        return ResponseDecision(
            mode=ResponseMode.JUDGE_LED,
            reason="The current turn asks for a rules or mechanic resolution.",
            factual_core_required=True,
            strategic_extension_required=False,
            combo_analysis_required=False,
        )

    if intent in {StrategyIntent.COMBO_FAILURE_EXPLANATION, StrategyIntent.INTERACTION_HYPOTHESIS}:
        return ResponseDecision(
            mode=ResponseMode.HYBRID,
            reason="The turn combines a factual interaction with a strategic conclusion.",
            factual_core_required=True,
            strategic_extension_required=True,
            combo_analysis_required=True,
        )

    if intent in _TACTICIAN_LED_INTENTS:
        return ResponseDecision(
            mode=ResponseMode.TACTICIAN_LED,
            reason="The current turn asks for strategic analysis or sequencing.",
            factual_core_required=True,
            strategic_extension_required=True,
            combo_analysis_required=intent in _COMBO_INTENTS,
        )

    judge_is_direct = (
        str(judge_payload.get("status", "")) == "answered"
        and str(judge_payload.get("confidence", "")) == "high"
        and str(judge_payload.get("origin", "")) in {
            "deterministic_rule",
            "oracle_renderer",
            "rulings_renderer",
            "llm_validated",
        }
    )
    active_combo = str(context.get("combo_classification", "")) in {
        "infinite_combo",
        "non_combo",
        "repeatable_synergy",
    }

    if judge_is_direct and len(cards) <= 1 and not active_combo:
        return ResponseDecision(
            mode=ResponseMode.JUDGE_LED,
            reason="The Judge already has a direct high-confidence factual answer.",
            factual_core_required=True,
            strategic_extension_required=False,
            combo_analysis_required=False,
        )

    return ResponseDecision(
        mode=ResponseMode.TACTICIAN_LED,
        reason="The turn is strategic or depends on the active strategic context.",
        factual_core_required=bool(cards),
        strategic_extension_required=True,
        combo_analysis_required=active_combo,
    )


def combo_classification_for_turn(
    *,
    analysis: InputAnalysis,
    decision: ResponseDecision,
    synthesized_classification: str,
    strategy_context: dict[str, Any] | None = None,
) -> str:
    """Return a combo label only when combo analysis is relevant to this turn."""

    if decision.combo_analysis_required:
        return synthesized_classification

    context = strategy_context or {}
    if analysis.strategy_intent is StrategyIntent.MECHANIC_EQUIVALENCE:
        inherited = str(context.get("combo_classification", ""))
        if inherited in {"infinite_combo", "non_combo", "repeatable_synergy"}:
            return inherited

    return "not_applicable"
