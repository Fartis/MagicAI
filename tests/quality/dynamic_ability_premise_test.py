from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path

from magicai.oracle_abilities import extract_activated_abilities
from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.dynamic.concepts import get_concepts
from tests.quality.dynamic.execution import run_dynamic_scenarios
from tests.quality.dynamic.premise_validation import validate_dynamic_premise
from tests.quality.dynamic.scenario_generator import ScenarioGenerator


def _card(name: str, oracle_text: str, type_line: str = "Artifact") -> dict:
    return {
        "name": name,
        "oracle_text": oracle_text,
        "type_line": type_line,
        "keywords": [],
        "games": ["paper"],
        "set": "tst",
        "set_name": "Test Set",
        "set_type": "expansion",
        "border_color": "black",
        "legalities": {"commander": "legal"},
    }


def _catalog(root: Path) -> CardCatalog:
    payload = [
        _card("Real Mana Rock", "{T}: Add {C}."),
        _card(
            "Creates Treasure",
            "{1}, {T}: Draw a card, then create a Treasure token. "
            "(It has \"{T}, Sacrifice this artifact: Add one mana of any color.\")",
        ),
        _card(
            "Creates Manalith",
            "{2}, {T}: Create a token named Manalith. It has "
            "\"{T}: Add one mana of any color.\"",
            "Legendary Creature — Artificer",
        ),
        _card("Safe Source", "{T}: Draw a card.", "Creature — Wizard"),
        _card("Sacrifice Source", "{T}, Sacrifice this artifact: Draw a card."),
        _card(
            "Hand Source",
            "{2}, Discard this card: Draw a card.",
            "Artifact Creature — Construct",
        ),
        _card(
            "Grave Source",
            "{2}, Exile this card from your graveyard: Draw a card.",
            "Creature — Spirit",
        ),
        _card("Self Pump", "{B}: Self Pump gets +1/+1 until end of turn.", "Creature — Shade"),
    ]
    path = root / "oracle-cards.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return CardCatalog(path)


def test_mana_selector_ignores_reminder_and_quoted_granted_abilities():
    with tempfile.TemporaryDirectory() as temp:
        catalog = _catalog(Path(temp))
        selected = catalog.select_abilities("mana_ability")
        assert {(item.card.name, item.ability.text) for item in selected} == {
            ("Real Mana Rock", "{T}: Add {C}.")
        }


def test_source_selector_rejects_impossible_later_removal_sequences():
    with tempfile.TemporaryDirectory() as temp:
        catalog = _catalog(Path(temp))
        names = {item.card.name for item in catalog.select_abilities("source_independence_ability")}
        assert "Safe Source" in names
        assert "Self Pump" in names
        assert "Sacrifice Source" not in names
        assert "Hand Source" not in names
        assert "Grave Source" not in names


def test_generated_scenario_is_bound_to_exact_oracle_ability():
    with tempfile.TemporaryDirectory() as temp:
        scenario = ScenarioGenerator(
            123,
            _catalog(Path(temp)),
            get_concepts(["source_independence"]),
        ).generate(1)[0]
        assert scenario.ability_text
        assert f"«{scenario.ability_text}»" in scenario.question
        assert scenario.ability_source_zone == "battlefield"
        assert scenario.source_removed_as_cost is False
        assert validate_dynamic_premise(scenario) == []


def test_preflight_blocks_invalid_generator_premise_before_judge_call():
    class NeverCalledAssistant:
        def ask_result(self, question):
            raise AssertionError(f"Judge should not be called: {question}")

    with tempfile.TemporaryDirectory() as temp:
        valid = ScenarioGenerator(
            123,
            _catalog(Path(temp)),
            get_concepts(["source_independence"]),
        ).generate(1)[0]
        invalid = replace(
            valid,
            source_removed_as_cost=True,
            ability_cost="{T}, Sacrifice this artifact",
        )
        results, failures, _ = run_dynamic_scenarios(
            NeverCalledAssistant(),
            [invalid],
            failure_dir=Path(temp) / "failures",
        )
        assert results[0]["status"] == "FAIL"
        assert "Invalid generated premise" in results[0]["failures"][0]
        assert len(failures) == 1


def test_parser_uses_word_boundary_and_source_dependency():
    abilities = extract_activated_abilities(
        "{1}: Add an additional counter to target creature.\n"
        "{B}: This creature gets +1/+1 until end of turn.",
        card_name="Boundary Test",
        type_line="Creature — Shade",
    )
    assert len(abilities) == 2
    assert abilities[0].is_mana is False
    assert abilities[1].is_mana is False
    assert abilities[1].source_dependency == "source_object"


def test_parser_detects_hand_and_graveyard_source_zones():
    hand = extract_activated_abilities(
        "{2}, Discard this card: Draw a card.",
        card_name="Hand Test",
        type_line="Creature",
    )[0]
    grave = extract_activated_abilities(
        "{2}, Exile this card from your graveyard: Draw a card.",
        card_name="Grave Test",
        type_line="Creature",
    )[0]
    assert hand.source_zone == "hand"
    assert grave.source_zone == "graveyard"


def main():
    tests = [
        test_mana_selector_ignores_reminder_and_quoted_granted_abilities,
        test_source_selector_rejects_impossible_later_removal_sequences,
        test_generated_scenario_is_bound_to_exact_oracle_ability,
        test_preflight_blocks_invalid_generator_premise_before_judge_call,
        test_parser_uses_word_boundary_and_source_dependency,
        test_parser_detects_hand_and_graveyard_source_zones,
    ]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}\n{exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
