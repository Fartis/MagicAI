from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


CARD_FIELDS = (
    "oracle_id",
    "id",
    "name",
    "mana_cost",
    "cmc",
    "type_line",
    "oracle_text",
    "power",
    "toughness",
    "loyalty",
    "defense",
    "colors",
    "color_identity",
    "keywords",
    "legalities",
    "rarity",
    "released_at",
    "scryfall_uri",
    "rulings_uri",
)


def card_to_evidence(card: Any) -> dict[str, Any]:
    if isinstance(card, dict):
        source = card
    elif is_dataclass(card):
        source = {item.name: getattr(card, item.name) for item in fields(card)}
    else:
        source = {
            key: getattr(card, key, None)
            for key in CARD_FIELDS
            if hasattr(card, key)
        }

    data = {
        key: source.get(key)
        for key in CARD_FIELDS
        if source.get(key) is not None
    }
    return {
        "kind": "card",
        "identifier": str(data.get("oracle_id") or data.get("name") or ""),
        "data": data,
    }


def rule_to_evidence(rule: dict[str, Any]) -> dict[str, Any]:
    data = {
        "number": str(rule.get("number", "")),
        "title": str(rule.get("title", "")),
        "rules": [
            {"number": str(number), "text": str(text)}
            for number, text in rule.get("rules", [])
        ],
    }
    return {
        "kind": "rule",
        "identifier": data["number"] or data["title"],
        "data": data,
    }


def clean_string_list(value: Any, *, field_name: str) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple)):
        values = list(value)
    elif value is None:
        values = []
    else:
        raise ValueError(f"{field_name} must be a string or a list of strings")

    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result
