from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.exhaustive.planner import build_exhaustive_plan


def _card(name: str, oracle: str, type_line: str, keywords=()):
    return {
        "name": name,
        "oracle_text": oracle,
        "type_line": type_line,
        "keywords": list(keywords),
        "games": ["paper"],
        "set": "tst",
        "set_name": "Test",
        "set_type": "expansion",
        "legalities": {"commander": "legal"},
    }


def _catalog(directory: Path) -> CardCatalog:
    cards = [
        _card("Mana Rock", "{T}: Add {C}.", "Artifact"),
        _card("Ward Beast", "Ward {2}", "Creature — Beast", ("Ward",)),
        _card("Undying Beast", "Undying", "Creature — Beast", ("Undying",)),
        _card("Source Mage", "{T}: Draw a card.", "Creature — Wizard"),
    ]
    path = directory / "oracle-cards.json"
    path.write_text(json.dumps(cards), encoding="utf-8")
    return CardCatalog(path)


def test_one_template_builds_one_scenario_per_candidate():
    with tempfile.TemporaryDirectory() as temp:
        plan = build_exhaustive_plan(_catalog(Path(temp)), template_mode="one")
        assert plan.static_summary["candidate_total"] == 4
        assert len(plan.scenarios) == 4
        assert len({scenario.id for scenario in plan.scenarios}) == 4
        assert all("exhaustive" in scenario.tags for scenario in plan.scenarios)


def test_all_templates_triples_dynamic_scenarios():
    with tempfile.TemporaryDirectory() as temp:
        plan = build_exhaustive_plan(_catalog(Path(temp)), template_mode="all")
        assert plan.static_summary["candidate_total"] == 4
        assert len(plan.scenarios) == 12


def test_source_pronoun_is_not_hidden_as_independent():
    with tempfile.TemporaryDirectory() as temp:
        cards = [_card("Weather", "{T}: It deals 1 damage to any target.", "Creature — Wizard")]
        path = Path(temp) / "oracle-cards.json"
        path.write_text(json.dumps(cards), encoding="utf-8")
        plan = build_exhaustive_plan(
            CardCatalog(path),
            families=("source_independence",),
            template_mode="one",
        )
        assert plan.scenarios[0].source_dependency == "information"
        assert plan.static_findings == ()


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
