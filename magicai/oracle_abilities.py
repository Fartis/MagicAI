from __future__ import annotations

import re
from dataclasses import dataclass


_MANA_SYMBOL_RE = re.compile(
    r"\{(?:[WUBRGC]|[0-9]+|[XYZS]|[WUBRG]/[WUBRGP]|C/P)\}",
    flags=re.IGNORECASE,
)
_LOYALTY_COST_RE = re.compile(r"^[+−-]\d+\s*$")
_WORD_ADD_RE = re.compile(r"\badds?\b", flags=re.IGNORECASE)
_QUOTED_TEXT_RE = re.compile(r'["“”«](.*?)["“”»]', flags=re.DOTALL)
_ROMAN_SUFFIX_RE = re.compile(r"\s+[IVXLCDM]+$", flags=re.IGNORECASE)
_SOURCE_DEPENDENCIES = {"independent", "source_object", "information", "partial"}


@dataclass(frozen=True, slots=True)
class ActivatedAbility:
    index: int
    text: str
    cost: str
    effect: str
    is_mana: bool
    source_zone: str
    source_removed_as_cost: bool
    source_may_be_removed_as_cost: bool
    source_dependency: str
    source_may_be_target: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "text": self.text,
            "cost": self.cost,
            "effect": self.effect,
            "is_mana": self.is_mana,
            "source_zone": self.source_zone,
            "source_removed_as_cost": self.source_removed_as_cost,
            "source_may_be_removed_as_cost": self.source_may_be_removed_as_cost,
            "source_dependency": self.source_dependency,
            "source_may_be_target": self.source_may_be_target,
        }


def extract_activated_abilities(
    oracle_text: str,
    *,
    card_name: str = "",
    type_line: str = "",
) -> tuple[ActivatedAbility, ...]:
    """Extract top-level activated abilities from Oracle text.

    Oracle modal abilities can span several bullet lines.  Those bullets belong
    to the activated ability that introduced them and must not be discarded,
    otherwise the source-dependency analysis can classify an empty "Choose one"
    shell instead of the real effect.
    """

    abilities: list[ActivatedAbility] = []
    for block in _oracle_ability_blocks(oracle_text):
        split = split_top_level_activated_ability(block)
        if split is None:
            continue
        cost, effect = split
        source_removed = _source_removed_as_cost(
            cost,
            card_name=card_name,
            type_line=type_line,
        )
        abilities.append(
            ActivatedAbility(
                index=len(abilities),
                text=block,
                cost=cost,
                effect=effect,
                is_mana=_is_mana_ability(cost, effect),
                source_zone=_infer_source_zone(cost, effect, card_name),
                source_removed_as_cost=source_removed,
                source_may_be_removed_as_cost=(
                    source_removed
                    or _source_may_be_removed_as_cost(
                        cost,
                        card_name=card_name,
                        type_line=type_line,
                    )
                ),
                source_dependency=_source_dependency(
                    effect,
                    card_name=card_name,
                    type_line=type_line,
                ),
                source_may_be_target=_source_may_be_target(
                    effect,
                    type_line=type_line,
                ),
            )
        )
    return tuple(abilities)


def split_top_level_activated_ability(line: str) -> tuple[str, str] | None:
    colon = _top_level_colon_index(line)
    if colon is None:
        return None
    cost = line[:colon].strip()
    effect = line[colon + 1 :].strip()
    if not cost or not effect:
        return None
    return cost, effect


def extract_quoted_activated_abilities(
    text: str,
    *,
    card_name: str = "",
    type_line: str = "",
) -> tuple[ActivatedAbility, ...]:
    results: list[ActivatedAbility] = []
    for match in _QUOTED_TEXT_RE.finditer(text or ""):
        quoted = match.group(1).strip()
        for ability in extract_activated_abilities(
            quoted,
            card_name=card_name,
            type_line=type_line,
        ):
            results.append(ability)
    return tuple(results)


def contains_quoted_mana_ability(text: str) -> bool:
    return any(ability.is_mana for ability in extract_quoted_activated_abilities(text))


def _oracle_lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _oracle_ability_blocks(text: str) -> list[str]:
    """Return activated-ability lines with their modal bullet continuations."""

    blocks: list[str] = []
    active: str | None = None
    for line in _oracle_lines(text):
        if line.startswith("•") and active is not None:
            active += "\n" + line
            continue

        if active is not None:
            blocks.append(active)
            active = None

        if split_top_level_activated_ability(line) is not None:
            active = line

    if active is not None:
        blocks.append(active)
    return blocks


def _top_level_colon_index(line: str) -> int | None:
    quote_closer = ""
    parentheses = 0
    braces = 0
    escaped = False
    pairs = {'"': '"', '“': '”', '«': '»'}

    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote_closer:
            if char == quote_closer:
                quote_closer = ""
            continue
        if char in pairs:
            quote_closer = pairs[char]
            continue
        if char == "(":
            parentheses += 1
            continue
        if char == ")" and parentheses:
            parentheses -= 1
            continue
        if char == "{":
            braces += 1
            continue
        if char == "}" and braces:
            braces -= 1
            continue
        if char == ":" and parentheses == 0 and braces == 0:
            return index
    return None


def _is_mana_ability(cost: str, effect: str) -> bool:
    cleaned_effect = _strip_parenthetical_and_quoted(effect)
    normalized_effect = cleaned_effect.casefold()
    if _LOYALTY_COST_RE.match(cost.strip()):
        return False
    if re.search(r"\btarget\b", normalized_effect):
        return False
    if not _WORD_ADD_RE.search(cleaned_effect):
        return False
    return bool(
        re.search(r"\bmana\b", normalized_effect)
        or _MANA_SYMBOL_RE.search(cleaned_effect)
        or re.search(r"\bone mana of any\b", normalized_effect)
    )


def _strip_parenthetical_and_quoted(text: str) -> str:
    result: list[str] = []
    parentheses = 0
    quote_closer = ""
    pairs = {'"': '"', '“': '”', '«': '»'}
    for char in text:
        if quote_closer:
            if char == quote_closer:
                quote_closer = ""
            continue
        if char in pairs:
            quote_closer = pairs[char]
            continue
        if char == "(":
            parentheses += 1
            continue
        if char == ")" and parentheses:
            parentheses -= 1
            continue
        if parentheses == 0:
            result.append(char)
    return "".join(result)


def _infer_source_zone(cost: str, effect: str, card_name: str) -> str:
    combined = f"{cost} {effect}".casefold()
    aliases = _card_name_aliases(card_name)
    name_pattern = "(?:" + "|".join(re.escape(item) for item in aliases) + ")" if aliases else "this card"
    if re.search(rf"(?:discard|reveal)\s+(?:{name_pattern}|this card)\b", combined):
        return "hand"
    if "from your hand" in combined or "in your hand" in combined:
        return "hand"
    if "from your graveyard" in combined or "in your graveyard" in combined:
        return "graveyard"
    if "from exile" in combined or "in exile" in combined:
        return "exile"
    if "from your library" in combined or "in your library" in combined:
        return "library"
    return "battlefield"


def _card_name_aliases(card_name: str) -> tuple[str, ...]:
    normalized = (card_name or "").strip().casefold()
    if not normalized:
        return ()
    aliases: list[str] = [normalized]
    if "," in normalized:
        aliases.append(normalized.split(",", 1)[0].strip())
    without_roman = _ROMAN_SUFFIX_RE.sub("", normalized).strip()
    if without_roman:
        aliases.append(without_roman)
    if "," in without_roman:
        aliases.append(without_roman.split(",", 1)[0].strip())
    return tuple(sorted(set(filter(None, aliases)), key=len, reverse=True))


def _source_reference_pattern(card_name: str, type_line: str) -> str:
    refs = [
        r"this\s+(?:card|permanent|creature|artifact|enchantment|land|planeswalker|battle|vehicle|token|aura|case|class)"
    ]
    refs.extend(re.escape(alias) for alias in _card_name_aliases(card_name))

    card_types, _, subtypes = (type_line or "").partition("—")
    combined_types = f"{card_types} {subtypes}".casefold()
    for card_type in (
        "artifact", "aura", "battle", "case", "class", "creature",
        "enchantment", "land", "planeswalker", "vehicle",
    ):
        if re.search(rf"\b{re.escape(card_type)}\b", combined_types):
            refs.append(rf"this\s+{re.escape(card_type)}")
    return "(?:" + "|".join(dict.fromkeys(refs)) + ")"


def _source_removed_as_cost(cost: str, *, card_name: str, type_line: str) -> bool:
    normalized = _strip_parenthetical_and_quoted(cost).casefold()
    source = _source_reference_pattern(card_name, type_line)
    patterns = (
        rf"\bsacrifice\s+{source}\b",
        rf"\bdiscard\s+{source}\b",
        rf"\bexile\s+{source}\b",
        rf"\breturn\s+{source}\b.*\bto (?:its|your) owner's hand\b",
        rf"\bput\s+{source}\b.*\b(?:graveyard|library|hand|exile)\b",
        rf"\bdestroy\s+{source}\b",
        rf"\bshuffle\s+{source}\b.*\blibrary\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _source_may_be_removed_as_cost(
    cost: str,
    *,
    card_name: str,
    type_line: str,
) -> bool:
    """Detect costs where the source is one legal payment, but not mandatory.

    Examples include "Sacrifice a creature" on a creature or "Sacrifice an
    Elf" on an Elf.  The generated scenario remains valid only if it states
    that other objects were used to pay that cost.
    """

    normalized = _strip_parenthetical_and_quoted(cost).casefold()
    if "sacrifice" not in normalized:
        return False
    if _source_removed_as_cost(cost, card_name=card_name, type_line=type_line):
        return True

    sacrifice_tail = normalized.split("sacrifice", 1)[1]

    card_types, _, subtype_text = (type_line or "").partition("—")
    types = set(re.findall(r"[a-z]+", card_types.casefold()))
    subtypes = set(re.findall(r"[a-z]+", subtype_text.casefold()))
    permanent_types = {
        "artifact", "battle", "creature", "enchantment", "land", "planeswalker",
    }

    def allows_source_word(word: str) -> bool:
        match = re.search(rf"(?:\banother\s+)?\b{re.escape(word)}s?\b", sacrifice_tail)
        return bool(match and not match.group(0).lstrip().startswith("another "))

    if allows_source_word("permanent") and types & permanent_types:
        return True
    for card_type in permanent_types:
        if card_type in types and allows_source_word(card_type):
            return True
    return any(allows_source_word(subtype) for subtype in subtypes)


def _source_dependency(effect: str, *, card_name: str, type_line: str) -> str:
    normalized = _resolution_effect(effect)
    if not normalized:
        return "independent"

    source = _source_reference_pattern(card_name, type_line)
    kinds: set[str] = set()
    source_seen = False

    for clause in _effect_clauses(normalized):
        explicit = bool(re.search(source, clause))
        keyword_self = _keyword_effect_uses_source(clause)
        pronoun_continuation = source_seen and bool(
            re.search(r"^(?:then\s+)?(?:return|exile|sacrifice|destroy|put|tap|untap)\s+it\b", clause)
        )
        dependent = explicit or keyword_self or pronoun_continuation
        source_seen = source_seen or explicit or keyword_self

        if not dependent:
            kinds.add("independent")
            continue

        modifies = (
            _clause_modifies_source(clause, source)
            or _clause_creates_source_bound_effect(clause, source)
            or keyword_self
            or pronoun_continuation
        )
        if modifies:
            kinds.add("source_object")
            if _clause_also_affects_other_objects(clause, source):
                kinds.add("independent")
        else:
            kinds.add("information")

    if not kinds or kinds == {"independent"}:
        return "independent"
    if len(kinds) > 1:
        return "partial"
    dependency = next(iter(kinds))
    return dependency if dependency in _SOURCE_DEPENDENCIES else "independent"


def _resolution_effect(effect: str) -> str:
    """Remove activation instructions that do not happen on resolution."""

    text = _strip_parenthetical_and_quoted(effect).casefold()
    # Bullet separators are semantic clause boundaries.
    text = text.replace("\n•", ". ").replace("•", ". ")
    sentences = [piece.strip(" ,") for piece in re.split(r"(?<=[.])\s+", text) if piece.strip(" ,")]
    kept: list[str] = []
    for sentence in sentences:
        normalized = sentence.lstrip(". ")
        if re.match(r"^(?:activate|you may activate|this ability can be activated)\b", normalized):
            continue
        if re.match(r"^this ability costs?\b.*\bto activate\b", normalized):
            continue
        if re.fullmatch(r"choose (?:one|two|one or both|one or more)[—-]?", normalized.rstrip(".")):
            continue
        kept.append(normalized)
    return " ".join(kept).strip()


def _effect_clauses(text: str) -> list[str]:
    pieces = re.split(r"(?:[.;]|\bthen\b)", text)
    return [piece.strip(" ,") for piece in pieces if piece.strip(" ,")]


def _keyword_effect_uses_source(clause: str) -> bool:
    return bool(
        re.search(r"^(?:adapt|level|monstrosity)\b", clause)
        or re.search(r"\b(?:adapt|level|monstrosity)\s+\d+\b", clause)
    )


def _clause_modifies_source(clause: str, source: str) -> bool:
    return bool(
        re.search(
            rf"{source}\s+(?:gets?|gains?|loses?|becomes?|has|is|can(?:'t| not)?|doesn't|does not)\b",
            clause,
        )
        or re.search(
            rf"(?:put|remove)\b[^.]*\b(?:counter|counters)\b[^.]*\b(?:on|from)\s+{source}",
            clause,
        )
        or re.search(
            rf"{source}\s+and\s+[^.]*\b(?:gets?|gains?|loses?|becomes?|has|is)\b",
            clause,
        )
        or re.search(
            rf"\b(?:tap|untap|transform|regenerate|sacrifice|exile|destroy|return|put|shuffle)\s+{source}\b",
            clause,
        )
        or re.search(r"^(?:return|exile|sacrifice|destroy|put|tap|untap)\s+it\b", clause)
    )


def _clause_creates_source_bound_effect(clause: str, source: str) -> bool:
    return bool(
        re.search(rf"damage\s+that\s+would\s+be\s+dealt\s+to\s+{source}", clause)
        or re.search(rf"prevent\b[^.]*\b(?:to|by)\s+{source}", clause)
        or re.search(rf"the next\b[^.]*\b{source}\b", clause)
    )


def _clause_also_affects_other_objects(clause: str, source: str) -> bool:
    without_source = re.sub(source, "<source>", clause)
    return bool(
        re.search(r"\b(?:another|other|up to one other)\s+target\b", without_source)
        or re.search(r"<source>\s+and\s+[^.]*\btarget\b", without_source)
        or re.search(r"\btarget\b[^.]*\band\s+<source>", without_source)
        or re.search(r"\b(?:draw|create|gain life|lose life|destroy target|exile target)\b", without_source)
    )


def _source_may_be_target(effect: str, *, type_line: str) -> bool:
    normalized = _resolution_effect(effect)
    if "target" not in normalized:
        return False
    if re.search(r"\banother\s+target\b|\bup to one other target\b", normalized):
        # There may still be a separate unrestricted target, so only return
        # early when every target phrase is explicitly another.
        target_phrases = re.findall(r"(?:another\s+|up to one other\s+)?target\b", normalized)
        if target_phrases and all("other" in phrase for phrase in target_phrases):
            return False

    card_types, _, subtype_text = (type_line or "").partition("—")
    types = set(re.findall(r"[a-z]+", card_types.casefold()))
    subtypes = set(re.findall(r"[a-z]+", subtype_text.casefold()))
    permanent_types = {"artifact", "battle", "creature", "enchantment", "land", "planeswalker"}

    if re.search(r"\btarget\s+(?:card|spell|ability|player|opponent)\b", normalized):
        object_target = re.search(
            r"\btarget\s+(?:nonland\s+)?(?:permanent|artifact|battle|creature|enchantment|land|planeswalker)\b|\bany target\b",
            normalized,
        )
        if not object_target:
            return False
    if "target face-down creature" in normalized:
        return False
    if "target nonland permanent" in normalized:
        return bool(types & (permanent_types - {"land"})) and "land" not in types
    if "target permanent" in normalized:
        return bool(types & permanent_types)
    if re.search(r"target\s+[^.]{0,40}\bartifact\b", normalized) and "artifact" in types:
        return True
    if re.search(r"target\s+[^.]{0,40}\bcreature\b", normalized) and "creature" in types:
        return True
    if re.search(r"target\s+[^.]{0,40}\bland\b", normalized) and "land" in types:
        return True
    if re.search(r"target\s+[^.]{0,40}\bplaneswalker\b", normalized):
        if "planeswalker" in types:
            named = re.search(r"target\s+([a-z-]+)\s+planeswalker", normalized)
            return not named or named.group(1) in subtypes
    if "any target" in normalized:
        return bool(types & {"battle", "creature", "planeswalker"})
    return False
