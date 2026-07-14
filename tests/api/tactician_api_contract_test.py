from magicai.api import routes
from magicai.api.schemas import TacticianAskResponse
from magicai.versioning import TACTICIAN_RESULT_SCHEMA_VERSION


def test_meta_exposes_tactician_profile() -> None:
    payload = routes.meta()
    assert "tactician" in payload["profiles"]
    assert payload["tactician_result_schema_version"] == TACTICIAN_RESULT_SCHEMA_VERSION


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
        authority_trace=["judge:factual_evidence", "tactician:strategic_interpretation"],
        judge_result={"authority": "judge"},
    )
    payload = response.model_dump()
    assert payload["authority"] == "tactician"
    assert payload["judge_result"]["authority"] == "judge"
    assert payload["authority_trace"][0].startswith("judge:")


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
