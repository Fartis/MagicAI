from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from magicai.conversation.models import Conversation
from magicai.tactician.core import Tactician
from tests.quality.tactician_conversations.evaluator import evaluate_turn
from tests.quality.tactician_conversations.fixtures import (
    ConversationFixtureGateway,
    ConversationFixtureJudge,
)
from tests.quality.tactician_conversations.loader import load_scenarios
from tests.quality.tactician_conversations.report import write_reports


def run_gauntlet(
    cases: str | Path,
    *,
    mode: str = "fixture",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    scenarios = load_scenarios(cases)
    scenario_results: list[dict[str, Any]] = []
    turn_count = 0
    passed_turns = 0

    for scenario in scenarios:
        conversation = Conversation(language=scenario.get("language", "es"))
        tactician = _build_tactician(mode, behavior=scenario.get("judge_behavior", "normal"))
        turns: list[dict[str, Any]] = []
        for index, turn in enumerate(scenario["turns"], start=1):
            payload = tactician.ask_result(conversation, turn["question"]).to_dict()
            failures = evaluate_turn(payload, turn.get("expect", {}))
            passed = not failures
            turn_count += 1
            passed_turns += int(passed)
            turns.append({
                "turn": index,
                "question": turn["question"],
                "passed": passed,
                "failures": failures,
                "answer": payload.get("answer", ""),
                "strategy_intent": payload.get("strategy_intent", ""),
                "response_mode": payload.get("response_mode", ""),
                "combo_classification": payload.get("combo_classification", ""),
            })
        scenario_results.append({
            "id": scenario["id"],
            "title": scenario.get("title", ""),
            "passed": all(turn["passed"] for turn in turns),
            "turns": turns,
        })

    results = {
        "schema_version": "1.0",
        "mode": mode,
        "scenario_count": len(scenario_results),
        "turn_count": turn_count,
        "passed_turns": passed_turns,
        "failed_turns": turn_count - passed_turns,
        "passed_scenarios": sum(int(item["passed"]) for item in scenario_results),
        "failed_scenarios": sum(int(not item["passed"]) for item in scenario_results),
        "scenarios": scenario_results,
    }
    if output_dir is not None:
        write_reports(results, output_dir)
    return results


def _build_tactician(mode: str, *, behavior: str) -> Tactician:
    if mode == "fixture":
        return Tactician(
            judge=ConversationFixtureJudge(behavior=behavior),
            tool_gateway=ConversationFixtureGateway(),
        )
    if mode == "local":
        return Tactician()
    raise ValueError(f"unsupported gauntlet mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MagicAI Tactician conversational gauntlet.")
    parser.add_argument("--cases", default="tests/quality/cases/tactician_conversations")
    parser.add_argument("--mode", choices=("fixture", "local"), default="fixture")
    parser.add_argument("--output-dir", default="quality-results/tactician-conversations")
    args = parser.parse_args()

    results = run_gauntlet(args.cases, mode=args.mode, output_dir=args.output_dir)
    print(
        "Tactician conversation gauntlet: "
        f"{results['passed_scenarios']}/{results['scenario_count']} scenarios, "
        f"{results['passed_turns']}/{results['turn_count']} turns passed"
    )
    return 0 if results["failed_turns"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
