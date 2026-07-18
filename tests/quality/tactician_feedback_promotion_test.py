from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.promote_tactician_feedback import build_candidate, promote_file


EXPORT = {
    "schema_version": "0.5",
    "question": "¿Qué ocurre si sacrifico Young Wolf?",
    "answer": "Observed answer.",
    "origin": "tactician_judge_led",
    "strategy_intent": "mechanic_resolution",
    "response_mode": "judge_led",
    "combo_classification": "not_applicable",
    "response_language": "es",
    "cards": [{"name": "Young Wolf"}],
    "rules": [{"number": "701.21a"}, {"number": "700.4"}],
    "judge_tool_calls": [{"tool": "oracle_lookup"}, {"tool": "rules_lookup"}],
}


def test_candidate_requires_human_review() -> None:
    candidate = build_candidate(EXPORT, candidate_id="TACT-CANDIDATE-001")
    item = candidate["candidate"]
    assert item["review_required"] is True
    turn = item["turns"][0]
    assert turn["expect"]["review_required"] is True
    assert turn["expect"]["strategy_intent"] == "mechanic_resolution"
    assert turn["expect"]["required_cards"] == ["Young Wolf"]
    assert "semantic requirements" in turn["review_notes"][0]


def test_promotion_writes_candidate_outside_active_corpus() -> None:
    with TemporaryDirectory() as directory:
        source = Path(directory) / "export.json"
        source.write_text(json.dumps(EXPORT), encoding="utf-8")
        target = promote_file(source, Path(directory) / "candidates", candidate_id="TACT-CANDIDATE-002")
        payload = json.loads(target.read_text(encoding="utf-8"))
        assert target.name.endswith(".candidate.json")
        assert payload["candidate"]["id"] == "TACT-CANDIDATE-002"
        assert payload["candidate"]["review_required"] is True


def main() -> int:
    tests = [test_candidate_requires_human_review, test_promotion_writes_candidate_outside_active_corpus]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Tactician feedback promotion tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
