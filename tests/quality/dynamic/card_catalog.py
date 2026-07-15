from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from magicai.oracle_abilities import ActivatedAbility, extract_activated_abilities
from magicai.scryfall import SCRYFALL_FILE
from magicai.sources.card_scope import is_supported_judge_card, supported_legal_formats


@dataclass(frozen=True)
class CardCandidate:
    name: str
    oracle_text: str
    type_line: str
    keywords: tuple[str, ...]
    set_code: str = ""
    set_name: str = ""
    set_type: str = ""
    legal_formats: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "oracle_text": self.oracle_text,
            "type_line": self.type_line,
            "keywords": list(self.keywords),
            "set_code": self.set_code,
            "set_name": self.set_name,
            "set_type": self.set_type,
            "legal_formats": list(self.legal_formats),
        }


@dataclass(frozen=True)
class CardAbilityCandidate:
    card: CardCandidate
    ability: ActivatedAbility

    @property
    def name(self) -> str:
        return self.card.name


class CardCatalog:
    def __init__(self, oracle_file: str | Path | None = None):
        self.oracle_file = Path(oracle_file or SCRYFALL_FILE)
        self._cards: list[CardCandidate] | None = None
        self._selector_cache: dict[str, list[CardCandidate]] = {}
        self._ability_selector_cache: dict[str, list[CardAbilityCandidate]] = {}

    def load(self) -> list[CardCandidate]:
        if self._cards is not None:
            return self._cards
        if not self.oracle_file.is_file():
            raise FileNotFoundError(
                "Scryfall Oracle bulk data was not found at "
                f"{self.oracle_file}. Run scripts/download_sources.sh first, "
                "or pass --oracle-file PATH."
            )
        with self.oracle_file.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        cards: list[CardCandidate] = []
        for raw_card in payload:
            candidate = _to_candidate(raw_card)
            if candidate is not None:
                cards.append(candidate)
        cards.sort(key=lambda card: card.name.casefold())
        self._cards = cards
        return cards

    def select(self, selector: str) -> list[CardCandidate]:
        if selector in self._selector_cache:
            return self._selector_cache[selector]
        if selector in _ABILITY_SELECTORS:
            cards: list[CardCandidate] = []
            seen: set[str] = set()
            for candidate in self.select_abilities(selector):
                key = candidate.card.name.casefold()
                if key not in seen:
                    seen.add(key)
                    cards.append(candidate.card)
            self._selector_cache[selector] = cards
            return cards
        predicate = _CARD_SELECTORS.get(selector)
        if predicate is None:
            raise ValueError(f"Unknown card selector: {selector}")
        selected = [card for card in self.load() if predicate(card)]
        if not selected:
            raise ValueError(
                f"Card selector {selector!r} returned no candidates from "
                f"{self.oracle_file}."
            )
        self._selector_cache[selector] = selected
        return selected

    def select_abilities(self, selector: str) -> list[CardAbilityCandidate]:
        if selector in self._ability_selector_cache:
            return self._ability_selector_cache[selector]
        predicate = _ABILITY_SELECTORS.get(selector)
        if predicate is None:
            raise ValueError(f"Unknown ability selector: {selector}")
        selected: list[CardAbilityCandidate] = []
        for card in self.load():
            for ability in _abilities_for_card(card):
                if predicate(card, ability):
                    selected.append(CardAbilityCandidate(card=card, ability=ability))
        if not selected:
            raise ValueError(
                f"Ability selector {selector!r} returned no candidates from "
                f"{self.oracle_file}."
            )
        self._ability_selector_cache[selector] = selected
        return selected


def _to_candidate(raw_card: dict) -> CardCandidate | None:
    name = str(raw_card.get("name", "")).strip()
    oracle_text = str(raw_card.get("oracle_text", "")).strip()
    type_line = str(raw_card.get("type_line", "")).strip()
    if not name or not oracle_text or "//" in name:
        return None
    if not is_supported_judge_card(raw_card):
        return None
    legal_formats = supported_legal_formats(raw_card)
    if not legal_formats:
        return None
    if "sticker" in type_line.casefold():
        return None
    return CardCandidate(
        name=name,
        oracle_text=oracle_text,
        type_line=type_line,
        keywords=tuple(str(item) for item in raw_card.get("keywords", [])),
        set_code=str(raw_card.get("set", "")).strip(),
        set_name=str(raw_card.get("set_name", "")).strip(),
        set_type=str(raw_card.get("set_type", "")).strip(),
        legal_formats=legal_formats,
    )


@lru_cache(maxsize=32768)
def _parse_abilities(
    oracle_text: str,
    card_name: str,
    type_line: str,
) -> tuple[ActivatedAbility, ...]:
    return extract_activated_abilities(
        oracle_text,
        card_name=card_name,
        type_line=type_line,
    )


def _abilities_for_card(card: CardCandidate) -> tuple[ActivatedAbility, ...]:
    return _parse_abilities(card.oracle_text, card.name, card.type_line)


def _oracle_lines(card: CardCandidate) -> list[str]:
    return [line.strip() for line in card.oracle_text.splitlines() if line.strip()]


def _has_intrinsic_keyword_line(card: CardCandidate, keyword: str) -> bool:
    pattern = re.compile(
        rf"(?:^|,\s*){re.escape(keyword)}(?=\s*(?:$|[,(—-]|\{{))",
        flags=re.IGNORECASE,
    )
    return any(pattern.search(line) for line in _oracle_lines(card))


def _has_ward(card: CardCandidate) -> bool:
    return _has_intrinsic_keyword_line(card, "ward")


def _has_undying(card: CardCandidate) -> bool:
    return _has_intrinsic_keyword_line(card, "undying")


def _is_permanent_card(card: CardCandidate) -> bool:
    card_types = card.type_line.split("—", 1)[0].casefold()
    return any(
        permanent_type in card_types
        for permanent_type in (
            "artifact", "battle", "creature", "enchantment", "land", "planeswalker"
        )
    )


def _is_mana_candidate(card: CardCandidate, ability: ActivatedAbility) -> bool:
    return ability.is_mana and ability.source_zone == "battlefield"


def _is_activated_nonmana(card: CardCandidate, ability: ActivatedAbility) -> bool:
    return _is_permanent_card(card) and not ability.is_mana


def _is_source_independence_candidate(
    card: CardCandidate,
    ability: ActivatedAbility,
) -> bool:
    return (
        _is_permanent_card(card)
        and not ability.is_mana
        and ability.source_zone == "battlefield"
        and not ability.source_removed_as_cost
    )


_CARD_SELECTORS = {
    "ward": _has_ward,
    "undying": _has_undying,
}

_ABILITY_SELECTORS = {
    "mana_ability": _is_mana_candidate,
    "activated_nonmana": _is_activated_nonmana,
    "source_independence_ability": _is_source_independence_candidate,
}
