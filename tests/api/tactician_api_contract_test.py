from magicai.api import routes
from magicai.api.schemas import TacticianAskResponse
from magicai.versioning import (
    NEXT_BETA_CODENAME,
    NEXT_BETA_VERSION,
    PUBLIC_VERSION,
    RELEASE_CHANNEL,
    RELEASE_CODENAME,
    RELEASE_TAG,
    TACTICIAN_RESULT_SCHEMA_VERSION,
    V1_CODENAME,
)


def test_meta_exposes_tactician_profile() -> None:
    payload = routes.meta()
    assert "tactician" in payload["profiles"]
    assert payload["project_version"] == PUBLIC_VERSION
    assert payload["release_channel"] == RELEASE_CHANNEL
    assert payload["release_codename"] == RELEASE_CODENAME
    assert payload["release_tag"] == RELEASE_TAG
    assert payload["tactician_result_schema_version"] == TACTICIAN_RESULT_SCHEMA_VERSION
    assert payload["next_beta_version"] == NEXT_BETA_VERSION
    assert payload["next_beta_codename"] == NEXT_BETA_CODENAME
    assert payload["v1_codename"] == V1_CODENAME
    capabilities = {item["name"]: item for item in payload["judge_capabilities"]}
    assert capabilities["oracle_lookup"]["status"] == "available"
    assert capabilities["spellbook_search"]["status"] == "planned"
    assert capabilities["strategic_statistics"]["status"] == "permission_required"


def test_tactician_response_remains_judge_evidence_compatible() -> None:
    response = TacticianAskResponse(
        schema_version=TACTICIAN_RESULT_SCHEMA_VERSION,
        answer="Sinergia validada.",
        session_id="session",
        question="¿Hay sinergia?",
        status="answered",
        origin="tactician_strategy",
        confidence="medium",
        authority="tactician",
        cards=[],
        rules=[],
        authority_trace=[
            "judge:factual_evidence",
            "tactician:strategic_interpretation",
            "judge:source_gateway",
        ],
        strategy_intent="combo_detection",
        combo_classification="infinite_combo",
        combo_steps=["Repeat the loop."],
        outcomes=["Arbitrarily large mana."],
        inherited_cards=["Young Wolf"],
        judge_queries=[{"sequence": 1, "purpose": "factual_evidence"}],
        input_analysis={"speech_act": "question", "claims_detected": 1},
        claim_verdicts=[{"claim_id": "claim-1", "verdict": "supported"}],
        reasoning_summary=["The loop restores its initial state."],
        queries_planned=2,
        queries_completed=2,
        judge_verified=True,
        investigation_plan={"queries_planned": 2},
        investigation_trace={
            "sufficient": True,
            "sufficiency_score": 1.0,
            "stopped_reason": "evidence_sufficient",
        },
        response_language="es",
        language_policy={"response_language": "es", "language_locked": True},
        answer_obligations=[{"code": "direct_user_question", "required": True}],
        answer_contract={"answer_complete": True},
        answer_complete=True,
        response_mode="tactician_led",
        response_orchestration={"mode": "tactician_led"},
        factual_core=[{"code": "combo_loop", "statement": "The loop restores its state."}],
        factual_core_coverage={"required": 1, "covered": 1, "complete": True},
        factual_core_preserved=True,
        strategic_extension_required=True,
        judge_result={"authority": "judge"},
    )
    payload = response.model_dump()
    assert payload["authority"] == "tactician"
    assert payload["judge_result"]["authority"] == "judge"
    assert payload["authority_trace"][0].startswith("judge:")
    assert payload["strategy_intent"] == "combo_detection"
    assert payload["combo_classification"] == "infinite_combo"
    assert payload["inherited_cards"] == ["Young Wolf"]
    assert payload["input_analysis"]["speech_act"] == "question"
    assert payload["claim_verdicts"][0]["verdict"] == "supported"
    assert payload["judge_verified"] is True
    assert payload["investigation_trace"]["sufficiency_score"] == 1.0
    assert payload["response_language"] == "es"
    assert payload["answer_complete"] is True
    assert payload["answer_obligations"][0]["code"] == "direct_user_question"
    assert payload["response_mode"] == "tactician_led"
    assert payload["factual_core_preserved"] is True
    assert payload["factual_core_coverage"]["complete"] is True


def main() -> int:
    tests = [
        test_meta_exposes_tactician_profile,
        test_tactician_response_remains_judge_evidence_compatible,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician API tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
