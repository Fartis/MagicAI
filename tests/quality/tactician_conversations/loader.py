from __future__ import annotations

import json
from pathlib import Path


def load_scenarios(path: str | Path) -> list[dict]:
    target = Path(path)
    if target.is_dir():
        scenarios: list[dict] = []
        for file_path in sorted(target.glob("*.json")):
            scenarios.extend(_load_file(file_path))
        assert scenarios, f"no Tactician conversation cases found in {target}"
        return scenarios
    return _load_file(target)


def _load_file(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "1.0"
    scenarios = payload.get("scenarios")
    assert isinstance(scenarios, list) and scenarios
    for scenario in scenarios:
        assert str(scenario.get("id", "")).strip()
        assert scenario.get("language") in {"es", "en"}
        turns = scenario.get("turns")
        assert isinstance(turns, list) and turns
        for turn in turns:
            assert str(turn.get("question", "")).strip()
            assert isinstance(turn.get("expect", {}), dict)
    return scenarios
