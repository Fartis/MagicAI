from magicai.api import routes
from magicai.api.health import ServiceProbe, build_health_payload
from magicai.sources.health import SourceHealth, SourceProbe
from magicai.versioning import (
    API_CONTRACT_VERSION,
    JUDGE_RESULT_SCHEMA_VERSION,
    PUBLIC_VERSION,
    RELEASE_CODENAME,
    RELEASE_TAG,
)


def _source_health() -> SourceHealth:
    probes = {
        "scryfall_oracle": SourceProbe(
            name="scryfall_oracle",
            status="available",
            required=True,
        ),
        "comprehensive_rules": SourceProbe(
            name="comprehensive_rules",
            status="available",
            required=True,
        ),
        "scryfall_symbology": SourceProbe(
            name="scryfall_symbology",
            status="available",
            required=False,
        ),
        "scryfall_rulings": SourceProbe(
            name="scryfall_rulings",
            status="available",
            required=False,
        ),
    }
    return SourceHealth(
        status="ready",
        ready=True,
        complete=True,
        sources=probes,
    )


def test_meta_exposes_stable_contract_values() -> None:
    payload = routes.meta()

    assert payload["project_version"] == PUBLIC_VERSION
    assert payload["release_codename"] == RELEASE_CODENAME
    assert payload["release_tag"] == RELEASE_TAG
    assert payload["api_contract_version"] == API_CONTRACT_VERSION
    assert payload["judge_result_schema_version"] == JUDGE_RESULT_SCHEMA_VERSION
    assert "answered" in payload["judge_statuses"]
    assert "deterministic_rulings" in payload["judge_origins"]
    assert payload["authority"] == "judge"


def test_health_payload_distinguishes_ready_and_full_service() -> None:
    payload = build_health_payload(
        source_health=_source_health(),
        ollama_probe=ServiceProbe(
            status="unavailable",
            available=False,
            detail="test",
            model="qwen3:8b",
        ),
    )

    assert payload["project_version"] == PUBLIC_VERSION
    assert payload["release_codename"] == RELEASE_CODENAME
    assert payload["release_tag"] == RELEASE_TAG
    assert payload["status"] == "degraded"
    assert payload["ready"] is True
    assert payload["full_service"] is False
    assert payload["sources"]["ready"] is True


def main() -> int:
    tests = [
        test_meta_exposes_stable_contract_values,
        test_health_payload_distinguishes_ready_and_full_service,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"API metadata tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
