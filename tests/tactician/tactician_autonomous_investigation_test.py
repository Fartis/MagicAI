from __future__ import annotations

from magicai.judge_tools import JudgeToolBudget, JudgeToolResult, JudgeToolStatus
from magicai.tactician.input_analysis import analyze_user_input
from magicai.tactician.investigation import run_investigation
from magicai.tactician.planner import plan_investigation


CARDS = [
    {
        "name": "Young Wolf",
        "oracle_text": "Undying",
        "type_line": "Creature — Wolf",
    }
]


class RecoveringGateway:
    def execute(self, request, *, conversation=None, budget=None):
        accepted, reason = budget.consume(request)
        if not accepted:
            return JudgeToolResult(
                tool=request.tool,
                status=JudgeToolStatus.BUDGET_EXCEEDED,
                authority="judge_gateway",
                provider="fake",
                purpose=request.purpose,
                arguments=request.arguments,
                error_code=reason,
                budget=budget.snapshot(),
            )

        if request.tool == "oracle_lookup":
            evidence = [
                {
                    "kind": "card",
                    "identifier": "young-wolf-oracle",
                    "data": dict(CARDS[0]),
                }
            ]
        elif request.tool == "rules_lookup":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": identifier,
                    "data": {"number": identifier, "title": f"Rule {identifier}"},
                }
                for identifier in request.arguments.get("identifiers", [])
                if identifier != "702.93a"
            ]
        elif request.tool == "rules_search":
            evidence = [
                {
                    "kind": "rule",
                    "identifier": "702.93a",
                    "data": {"number": "702.93a", "title": "Undying"},
                }
            ]
        else:
            raise AssertionError(f"unexpected tool: {request.tool}")

        return JudgeToolResult(
            tool=request.tool,
            status=JudgeToolStatus.SUCCESS,
            authority="official_rules",
            provider="fake",
            purpose=request.purpose,
            request_id=request.request_id,
            arguments=request.arguments,
            evidence=evidence,
            budget=budget.snapshot(),
        )


def _mechanic_plan():
    analysis = analyze_user_input(
        "Morir y entrar al cementerio es lo mismo para Undying, ¿verdad?"
    )
    return analysis, plan_investigation(analysis, cards=CARDS)


def test_plan_decomposes_claims_into_evidence_hypotheses() -> None:
    _, plan = _mechanic_plan()

    assert [item.kind for item in plan.hypotheses] == [
        "oracle_foundation",
        "mechanic_equivalence",
        "answer_basis",
    ]
    assert plan.hypotheses[1].required_evidence == (
        "rule:700.4",
        "rule:702.93a",
    )
    assert plan.hypotheses[1].search_queries


def test_investigation_recovers_missing_evidence_with_counterexample_search() -> None:
    analysis, plan = _mechanic_plan()
    gateway = RecoveringGateway()

    outcome = run_investigation(
        analysis=analysis,
        requests=plan.requests,
        hypotheses=plan.hypotheses,
        execute=gateway.execute,
        conversation=object(),
        budget=JudgeToolBudget(max_calls=4, max_calls_per_tool=2),
    )

    assert outcome.sufficient is True
    assert outcome.sufficiency_score == 1.0
    assert outcome.follow_up_queries == 1
    assert outcome.stopped_reason == "evidence_sufficient"
    assert [step.phase for step in outcome.steps] == [
        "initial_evidence",
        "initial_evidence",
        "counterexample_search",
    ]
    assert outcome.steps[-1].request.tool == "rules_search"
    assert outcome.hypotheses[1].resolved_evidence == (
        "rule:700.4",
        "rule:702.93a",
    )


def test_investigation_stops_when_follow_up_exceeds_budget() -> None:
    analysis, plan = _mechanic_plan()
    gateway = RecoveringGateway()

    outcome = run_investigation(
        analysis=analysis,
        requests=plan.requests,
        hypotheses=plan.hypotheses,
        execute=gateway.execute,
        conversation=object(),
        budget=JudgeToolBudget(max_calls=2, max_calls_per_tool=2),
    )

    assert outcome.sufficient is False
    assert outcome.stopped_reason == "budget_exceeded"
    assert outcome.follow_up_queries == 1
    assert outcome.steps[-1].status == "budget_exceeded"
    assert outcome.steps[-1].error_code == "maximum_tool_calls_reached"


def main() -> int:
    test_plan_decomposes_claims_into_evidence_hypotheses()
    test_investigation_recovers_missing_evidence_with_counterexample_search()
    test_investigation_stops_when_follow_up_exceeds_budget()
    print("OK: autonomous investigation planner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
