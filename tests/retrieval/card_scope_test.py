from __future__ import annotations

import json
import tempfile
from pathlib import Path

import magicai.extractors.cards as card_extractor
import magicai.scryfall as scryfall
from magicai.conversation import Conversation
from magicai.conversation.disambiguation import handle_card_disambiguation
from magicai.sources.card_scope import is_supported_judge_card


def _card(
    name: str,
    *,
    oracle_id: str,
    type_line: str = "Legendary Creature — Goblin",
    layout: str = "normal",
    set_type: str = "expansion",
    legal: bool = True,
    oversized: bool = False,
) -> dict:
    status = "legal" if legal else "not_legal"

    return {
        "id": oracle_id + "-print",
        "oracle_id": oracle_id,
        "name": name,
        "mana_cost": "{2}{R}",
        "cmc": 3,
        "type_line": type_line,
        "oracle_text": "Sample Oracle text.",
        "colors": ["R"],
        "color_identity": ["R"],
        "keywords": [],
        "legalities": {
            "commander": status,
            "modern": status,
            "legacy": status,
            "vintage": status,
        },
        "rarity": "rare",
        "released_at": "2020-01-01",
        "scryfall_uri": "https://example.invalid/card",
        "rulings_uri": "https://example.invalid/rulings",
        "games": ["paper"],
        "digital": False,
        "layout": layout,
        "set_type": set_type,
        "set_name": "Sample Set",
        "set": "tst",
        "border_color": "black",
        "oversized": oversized,
    }


def _reset_scryfall() -> None:
    scryfall._cards = None
    scryfall._card_index = None
    scryfall._loaded_source = None


def _reset_extractor() -> None:
    card_extractor._exact_cards = None
    card_extractor._alias_cards = None
    card_extractor._ambiguous_aliases = None
    card_extractor._card_data_by_name = None


def test_vanguard_is_outside_normal_judge_scope():
    vanguard = _card(
        "Squee",
        oracle_id="vanguard-squee",
        type_line="Vanguard",
        layout="vanguard",
        set_type="vanguard",
        legal=False,
        oversized=True,
    )

    assert not is_supported_judge_card(vanguard)


def test_banned_ordinary_paper_card_remains_queryable():
    ordinary = _card(
        "Ordinary Banned Card",
        oracle_id="ordinary-banned",
        legal=False,
    )

    assert is_supported_judge_card(ordinary)


def test_squee_vanguard_cannot_override_playable_squee_cards():
    payload = [
        _card(
            "Squee",
            oracle_id="vanguard-squee",
            type_line="Vanguard",
            layout="vanguard",
            set_type="vanguard",
            legal=False,
            oversized=True,
        ),
        _card("Squee, Goblin Nabob", oracle_id="squee-nabob"),
        _card("Squee, the Immortal", oracle_id="squee-immortal"),
        _card("Squee, Dubious Monarch", oracle_id="squee-monarch"),
    ]

    old_file = scryfall.SCRYFALL_FILE

    with tempfile.TemporaryDirectory() as temp_dir:
        oracle_file = Path(temp_dir) / "oracle-cards.json"
        oracle_file.write_text(json.dumps(payload), encoding="utf-8")

        try:
            scryfall.SCRYFALL_FILE = oracle_file
            _reset_scryfall()

            loaded = scryfall.load_cards()

            assert len(loaded) == 3
            assert scryfall.search_exact_card("Squee") is None
            assert (
                scryfall.search_exact_card("Squee, Goblin Nabob")["name"]
                == "Squee, Goblin Nabob"
            )
            assert {
                card["name"]
                for card in scryfall.search_cards_by_name("Squee")
            } == {
                "Squee, Goblin Nabob",
                "Squee, the Immortal",
                "Squee, Dubious Monarch",
            }

            old_loader = card_extractor.load_cards

            try:
                card_extractor.load_cards = scryfall.load_cards
                _reset_extractor()

                ambiguity = card_extractor.find_ambiguous_card_references(
                    "¿Qué hace Squee?"
                )

                assert ambiguity is not None
                assert ambiguity.alias.casefold() == "squee"
                assert set(ambiguity.candidates) == {
                    "Squee, Goblin Nabob",
                    "Squee, the Immortal",
                    "Squee, Dubious Monarch",
                }

                creature_ambiguity = (
                    card_extractor.find_ambiguous_card_references(
                        "¿Qué hace la criatura goblin Squee?"
                    )
                )

                assert creature_ambiguity is not None
                assert set(creature_ambiguity.candidates) == {
                    "Squee, Goblin Nabob",
                    "Squee, the Immortal",
                    "Squee, Dubious Monarch",
                }

                conversation = Conversation()
                clarification, resolved = handle_card_disambiguation(
                    conversation,
                    "¿Qué hace la criatura goblin Squee?",
                )

                assert resolved is None
                assert clarification is not None
                assert "Vanguard" not in clarification
                assert "Squee, Goblin Nabob" in clarification
                assert "Squee, the Immortal" in clarification
                assert "Squee, Dubious Monarch" in clarification
            finally:
                card_extractor.load_cards = old_loader
                _reset_extractor()
        finally:
            scryfall.SCRYFALL_FILE = old_file
            _reset_scryfall()



def test_configure_card_source_switches_runtime_index():
    first = _card("First Snapshot Card", oracle_id="first-snapshot")
    second = _card("Second Snapshot Card", oracle_id="second-snapshot")
    old_file = Path(scryfall.SCRYFALL_FILE)

    with tempfile.TemporaryDirectory() as temp_dir:
        first_file = Path(temp_dir) / "first.json"
        second_file = Path(temp_dir) / "second.json"
        first_file.write_text(json.dumps([first]), encoding="utf-8")
        second_file.write_text(json.dumps([second]), encoding="utf-8")

        try:
            scryfall.configure_card_source(first_file)
            assert scryfall.search_exact_card("First Snapshot Card") is not None
            assert scryfall.search_exact_card("Second Snapshot Card") is None

            scryfall.configure_card_source(second_file)
            assert scryfall.search_exact_card("First Snapshot Card") is None
            assert scryfall.search_exact_card("Second Snapshot Card") is not None
        finally:
            scryfall.configure_card_source(old_file)


def main():
    tests = [
        test_vanguard_is_outside_normal_judge_scope,
        test_banned_ordinary_paper_card_remains_queryable,
        test_squee_vanguard_cannot_override_playable_squee_cards,
        test_configure_card_source_switches_runtime_index,
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
