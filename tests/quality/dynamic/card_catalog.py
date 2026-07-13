from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from magicai.scryfall import SCRYFALL_FILE
from magicai.sources.card_scope import (
    is_supported_judge_card,
    supported_legal_formats,
)


_MANA_SYMBOL_RE = re.compile(
    r"\{(?:[WUBRGC]|[0-9]+|[XYZS]|[WUBRG]/[WUBRGP]|C/P)\}",
    flags=re.IGNORECASE,
)
_LOYALTY_PREFIX_RE = re.compile(r"^[+−-]?\d+\s*:")

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


class CardCatalog:
    def __init__(self, oracle_file: str | Path | None = None):
        self.oracle_file = Path(oracle_file or SCRYFALL_FILE)
        self._cards: list[CardCandidate] | None = None
        self._selector_cache: dict[str, list[CardCandidate]] = {}

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

        cards = []

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

        predicate = _SELECTORS.get(selector)

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


def _supported_legal_formats(raw_card: dict) -> tuple[str, ...]:
    legalities = raw_card.get("legalities") or {}

    return tuple(
        format_name
        for format_name in _SUPPORTED_PAPER_FORMATS
        if str(legalities.get(format_name, "")).casefold()
        in _SUPPORTED_LEGALITY_STATUSES
    )


def _is_funny_or_playtest_card(raw_card: dict) -> bool:
    set_type = str(raw_card.get("set_type", "")).casefold()
    border_color = str(raw_card.get("border_color", "")).casefold()
    security_stamp = str(raw_card.get("security_stamp", "")).casefold()
    set_name = str(raw_card.get("set_name", "")).casefold()
    promo_types = {
        str(item).casefold()
        for item in (raw_card.get("promo_types") or [])
    }

    return (
        set_type == "funny"
        or border_color == "silver"
        or security_stamp == "acorn"
        or "playtest" in promo_types
        or "playtest" in set_name
    )


def _to_candidate(raw_card: dict) -> CardCandidate | None:
    name = str(raw_card.get("name", "")).strip()
    oracle_text = str(raw_card.get("oracle_text", "")).strip()
    type_line = str(raw_card.get("type_line", "")).strip()

    if not name or not oracle_text:
        return None

    if "//" in name:
        return None

    if not is_supported_judge_card(raw_card):
        return None

    legal_formats = supported_legal_formats(raw_card)

    if not legal_formats:
        return None

    if _is_funny_or_playtest_card(raw_card):
        return None

    legal_formats = _supported_legal_formats(raw_card)

    if not legal_formats:
        return None

    # Scryfall bulk data also contains supplemental game objects such as
    # sticker sheets. They are not cards/permanents and must never be used to
    # build premises such as "this card has Ward/Undying".
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


def _oracle_lines(card: CardCandidate) -> list[str]:
    return [line.strip() for line in card.oracle_text.splitlines() if line.strip()]


def _top_level_colon_index(line: str) -> int | None:
    """Return the first ability colon outside quotes and reminder text.

    Oracle text frequently embeds activated abilities inside quoted granted text
    or reminder parentheses. Those colons describe another object or explain a
    keyword; they must not be treated as an activated ability of this card.
    """

    in_quotes = False
    parenthesis_depth = 0
    escaped = False

    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue

        if character == "\\":
            escaped = True
            continue

        if character == '"':
            in_quotes = not in_quotes
            continue

        if in_quotes:
            continue

        if character == "(":
            parenthesis_depth += 1
            continue

        if character == ")" and parenthesis_depth:
            parenthesis_depth -= 1
            continue

        if character == ":" and parenthesis_depth == 0:
            return index

    return None


def _split_activated_line(line: str) -> tuple[str, str] | None:
    colon_index = _top_level_colon_index(line)

    if colon_index is None:
        return None

    prefix = line[:colon_index].strip()
    effect = line[colon_index + 1 :].strip()

    if not prefix or not effect:
        return None

    return prefix, effect


def _activated_lines(card: CardCandidate) -> list[str]:
    return [
        line
        for line in _oracle_lines(card)
        if _split_activated_line(line) is not None
    ]


def _is_mana_line(line: str) -> bool:
    split = _split_activated_line(line)

    if split is None:
        return False

    prefix, effect = split
    normalized_effect = effect.casefold()

    if _LOYALTY_PREFIX_RE.match(line.strip()):
        return False

    if "target" in normalized_effect:
        return False

    if "add" not in normalized_effect:
        return False

    if "mana" not in normalized_effect and not _MANA_SYMBOL_RE.search(effect):
        return False

    # Saga chapter notation and similar text can contain a colon but is not an
    # activated ability. Requiring a plausible cost before the colon removes
    # most of those false positives without encoding specific card names.
    normalized_prefix = prefix.casefold()
    return any(
        marker in normalized_prefix
        for marker in ("{t}", "{q}", "pay", "sacrifice", "discard", "remove", "{")
    )


def _has_mana_ability(card: CardCandidate) -> bool:
    return any(_is_mana_line(line) for line in _activated_lines(card))


def _has_intrinsic_keyword_line(card: CardCandidate, keyword: str) -> bool:
    """Return True only when the card itself visibly has the keyword.

    Scryfall's ``keywords`` list and a broad Oracle substring search are too
    permissive for premise generation: they also match reminder text, cards
    that grant the keyword to another object, and text that merely mentions
    the keyword. Dynamic scenarios must only assert a keyword when it appears
    as an intrinsic keyword line on the selected card.
    """

    pattern = re.compile(
        rf"(?:^|,\s*){re.escape(keyword)}"
        rf"(?=\s*(?:$|[,(—-]|\{{))",
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
            "artifact",
            "battle",
            "creature",
            "enchantment",
            "land",
            "planeswalker",
        )
    )


def _has_activated_nonmana_ability(card: CardCandidate) -> bool:
    if not _is_permanent_card(card):
        return False

    for line in _activated_lines(card):
        if _LOYALTY_PREFIX_RE.match(line.strip()):
            continue

        if _is_mana_line(line):
            continue

        split = _split_activated_line(line)

        if split is None:
            continue

        return True

    return False


_SELECTORS = {
    "mana_ability": _has_mana_ability,
    "ward": _has_ward,
    "activated_nonmana": _has_activated_nonmana_ability,
    "undying": _has_undying,
}
