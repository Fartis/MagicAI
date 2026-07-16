from __future__ import annotations

import json
from pathlib import Path


def load_scenarios(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "1.0"
    scenarios = payload.get("scenarios")
    assert isinstance(scenarios, list) and scenarios
    return scenarios
