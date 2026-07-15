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
        judge_result={"authority": "judge"},
    )
    payload = response.model_dump()
    assert payload["authority"] == "tactician"
    assert payload["judge_result"]["authority"] == "judge"
    assert payload["authority_trace"][0].startswith("judge:")
    assert payload["strategy_intent"] == "combo_detection"
    assert payload["combo_classification"] == "infinite_combo"
    assert payload["inherited_cards"] == ["Young Wolf"]


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
