from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tests.quality.dynamic.models import DynamicScenario


_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def write_manifest(
    output_file: str | Path,
    seed: int,
    scenarios: list[DynamicScenario],
) -> Path:
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "seed": seed,
        "cases": len(scenarios),
        "scenarios": [scenario.to_dict() for scenario in scenarios],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def save_failure(
    output_dir: str | Path,
    scenario: DynamicScenario,
    result: dict[str, Any],
) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_concept = _SAFE_NAME_RE.sub("-", scenario.concept_id).strip("-")
    filename = f"{scenario.seed}_{scenario.id}_{safe_concept}.json"
    path = directory / filename
    payload = {
        "schema_version": 1,
        "scenario": scenario.to_dict(),
        "last_result": result,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_replay(path: str | Path) -> DynamicScenario:
    replay_path = Path(path)
    payload = json.loads(replay_path.read_text(encoding="utf-8"))

    if "scenario" in payload:
        payload = payload["scenario"]
    elif "scenarios" in payload:
        scenarios = payload["scenarios"]

        if len(scenarios) != 1:
            raise ValueError(
                "A manifest can only be replayed directly when it contains "
                "exactly one scenario."
            )

        payload = scenarios[0]

    return DynamicScenario.from_dict(payload)
