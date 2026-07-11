from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.dynamic.concepts import get_concepts
from tests.quality.dynamic.failure_store import (
    load_replay,
    save_failure,
    write_manifest,
)
from tests.quality.dynamic.scenario_generator import ScenarioGenerator


_FIXTURE_CARDS = [
    {
        "name": "Alpha Mana Druid",
        "oracle_text": "{T}: Add one mana of any color.",
        "type_line": "Creature — Elf Druid",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Beta Mana Stone",
        "oracle_text": "{T}: Add {C}{C}.",
        "type_line": "Artifact",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Guardian Alpha",
        "oracle_text": "Ward {2}",
        "type_line": "Creature — Spirit",
        "keywords": ["Ward"],
        "games": ["paper"],
    },
    {
        "name": "Guardian Beta",
        "oracle_text": "Flying\nWard—Pay 2 life.",
        "type_line": "Creature — Bird",
        "keywords": ["Flying", "Ward"],
        "games": ["paper"],
    },
    {
        "name": "Source Alpha",
        "oracle_text": "{T}: Draw a card, then discard a card.",
        "type_line": "Creature — Wizard",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Source Beta",
        "oracle_text": "Sacrifice Source Beta: You gain 3 life.",
        "type_line": "Artifact",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Undying Alpha",
        "oracle_text": "Undying",
        "type_line": "Creature — Wolf",
        "keywords": ["Undying"],
        "games": ["paper"],
    },
    {
        "name": "Undying Beta",
        "oracle_text": "Haste\nUndying",
        "type_line": "Creature — Devil",
        "keywords": ["Haste", "Undying"],
        "games": ["paper"],
    },
    {
        "name": "Mana Granted Elsewhere",
        "oracle_text": (
            "When this creature enters, target artifact becomes a Treasure "
            "with \"{T}, Sacrifice this artifact: Add one mana of any color.\""
        ),
        "type_line": "Creature — Pirate",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Nonpermanent Activated Source",
        "oracle_text": "{2}, Discard this card: Draw a card.",
        "type_line": "Instant",
        "keywords": [],
        "games": ["paper"],
    },
    {
        "name": "Reminder Activated Text",
        "oracle_text": (
            "Cycling {2} ({2}, Discard this card: Draw a card.)"
        ),
        "type_line": "Instant",
        "keywords": ["Cycling"],
        "games": ["paper"],
    },
    {
        "name": "Ward Mention Only",
        "oracle_text": (
            "This spell can't be countered. "
            "(This includes by the ward ability.)"
        ),
        "type_line": "Sorcery",
        "keywords": ["Ward"],
        "games": ["paper"],
    },
    {
        "name": "Ward Granted Elsewhere",
        "oracle_text": (
            "Cloak a card from your hand. It is a 2/2 creature with ward {2}."
        ),
        "type_line": "Creature — Wizard",
        "keywords": ["Ward"],
        "games": ["paper"],
    },
    {
        "name": "Intrinsic Comma Ward",
        "oracle_text": "Flying, ward {2}",
        "type_line": "Creature — Bird",
        "keywords": ["Flying", "Ward"],
        "games": ["paper"],
    },
    {
        "name": "Undying Granted Elsewhere",
        "oracle_text": "Other creatures you control have undying.",
        "type_line": "Creature — Cleric",
        "keywords": ["Undying"],
        "games": ["paper"],
    },
    {
        "name": "Undying Sticker Sheet",
        "oracle_text": "{TK}{TK}{TK} — Undying",
        "type_line": "Sticker",
        "keywords": ["Undying"],
        "games": ["paper"],
    },
    {
        "name": "Digital Only Card",
        "oracle_text": "{T}: Add {U}.",
        "type_line": "Creature",
        "keywords": [],
        "games": ["arena"],
        "digital": True,
    },
]


def _fixture_catalog(directory: Path) -> CardCatalog:
    oracle_file = directory / "oracle-cards.json"
    oracle_file.write_text(
        json.dumps(_FIXTURE_CARDS),
        encoding="utf-8",
    )
    return CardCatalog(oracle_file)


def test_same_seed_generates_identical_scenarios():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        concepts = get_concepts()
        first = ScenarioGenerator(184729, _fixture_catalog(root), concepts).generate(16)
        second = ScenarioGenerator(184729, _fixture_catalog(root), concepts).generate(16)

        assert [scenario.to_dict() for scenario in first] == [
            scenario.to_dict()
            for scenario in second
        ]


def test_different_seed_changes_generated_manifest():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        concepts = get_concepts()
        first = ScenarioGenerator(1, _fixture_catalog(root), concepts).generate(16)
        second = ScenarioGenerator(2, _fixture_catalog(root), concepts).generate(16)

        assert [scenario.to_dict() for scenario in first] != [
            scenario.to_dict()
            for scenario in second
        ]


def test_each_selector_returns_only_matching_fixture_cards():
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog = _fixture_catalog(Path(temp_dir))

        assert {card.name for card in catalog.select("mana_ability")} == {
            "Alpha Mana Druid",
            "Beta Mana Stone",
        }
        assert {card.name for card in catalog.select("ward")} == {
            "Guardian Alpha",
            "Guardian Beta",
            "Intrinsic Comma Ward",
        }
        assert {card.name for card in catalog.select("activated_nonmana")} == {
            "Source Alpha",
            "Source Beta",
        }
        assert {card.name for card in catalog.select("undying")} == {
            "Undying Alpha",
            "Undying Beta",
        }


def test_concept_cycle_covers_every_selected_concept():
    with tempfile.TemporaryDirectory() as temp_dir:
        concepts = get_concepts()
        scenarios = ScenarioGenerator(
            99,
            _fixture_catalog(Path(temp_dir)),
            concepts,
        ).generate(len(concepts))

        assert {scenario.concept_id for scenario in scenarios} == {
            concept.id
            for concept in concepts
        }


def test_manifest_and_failure_replay_round_trip():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        scenario = ScenarioGenerator(
            123,
            _fixture_catalog(root),
            get_concepts(["undying_exile"]),
        ).generate(1)[0]
        manifest = write_manifest(root / "manifest.json", 123, [scenario])
        replay_from_manifest = load_replay(manifest)

        assert replay_from_manifest == scenario

        result = {
            "id": scenario.id,
            "status": "FAIL",
            "steps": [{"status": "FAIL", "failures": ["synthetic"]}],
        }
        failure = save_failure(root / "failures", scenario, result)
        replay_from_failure = load_replay(failure)

        assert replay_from_failure == scenario


def test_generated_manifest_keeps_card_audit_metadata():
    with tempfile.TemporaryDirectory() as temp_dir:
        scenario = ScenarioGenerator(
            777,
            _fixture_catalog(Path(temp_dir)),
            get_concepts(["ward"]),
        ).generate(1)[0]
        payload = scenario.to_dict()

        assert payload["card_type_line"]
        assert isinstance(payload["card_keywords"], list)



def main():
    tests = [
        test_same_seed_generates_identical_scenarios,
        test_different_seed_changes_generated_manifest,
        test_each_selector_returns_only_matching_fixture_cards,
        test_concept_cycle_covers_every_selected_concept,
        test_manifest_and_failure_replay_round_trip,
        test_generated_manifest_keeps_card_audit_metadata,
    ]
    errors = []

    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}")
            print(exc)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Tests : {len(tests)}")
    print(f"Errors: {len(errors)}")

    if errors:
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
