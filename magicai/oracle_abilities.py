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


@dataclass(frozen=True, slots=True)
class ActivatedAbility:
    index: int
    text: str
    cost: str
    effect: str
    is_mana: bool
    source_zone: str
    source_removed_as_cost: bool
    source_dependency: str

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "text": self.text,
            "cost": self.cost,
            "effect": self.effect,
            "is_mana": self.is_mana,
            "source_zone": self.source_zone,
            "source_removed_as_cost": self.source_removed_as_cost,
            "source_dependency": self.source_dependency,
        }


def extract_activated_abilities(
    oracle_text: str,
    *,
    card_name: str = "",
    type_line: str = "",
) -> tuple[ActivatedAbility, ...]:
    abilities: list[ActivatedAbility] = []
    for line in _oracle_lines(oracle_text):
        split = split_top_level_activated_ability(line)
        if split is None:
            continue
        cost, effect = split
        abilities.append(
            ActivatedAbility(
                index=len(abilities),
                text=line,
                cost=cost,
                effect=effect,
                is_mana=_is_mana_ability(cost, effect),
                source_zone=_infer_source_zone(cost, effect, card_name),
                source_removed_as_cost=_source_removed_as_cost(
                    cost,
                    card_name=card_name,
                    type_line=type_line,
                ),
                source_dependency=_source_dependency(
                    effect,
                    card_name=card_name,
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
    # Longest first prevents a shortened alias from consuming only part of a name.
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


def _source_dependency(effect: str, *, card_name: str, type_line: str) -> str:
    normalized = _strip_parenthetical_and_quoted(effect).casefold().strip()
    if not normalized:
        return "independent"

    source = _source_reference_pattern(card_name, type_line)
    clauses = _effect_clauses(normalized)
    dependent_flags: list[bool] = []
    source_seen = False

    for clause in clauses:
        explicit = bool(re.search(source, clause))
        keyword_self = _keyword_effect_uses_source(clause)
        pronoun_continuation = source_seen and bool(
            re.search(r"^(?:then\s+)?(?:return|exile|sacrifice|destroy|put|tap|untap)\s+it\b", clause)
        )
        dependent = explicit or keyword_self or pronoun_continuation
        dependent_flags.append(dependent)
        source_seen = source_seen or explicit or keyword_self

    if not any(dependent_flags):
        return "independent"

    if any(not item for item in dependent_flags):
        return "partial"

    # A source reference that is only read for information can still use LKI.
    if not any(
        _clause_modifies_source(clause, source) or _keyword_effect_uses_source(clause)
        for clause in clauses
    ):
        return "information"
    return "source_object"


def _effect_clauses(text: str) -> list[str]:
    # "then" is a sequencing boundary for effects such as Sensei's Divining Top.
    pieces = re.split(r"(?:[.;]|\bthen\b)", text)
    return [piece.strip(" ,") for piece in pieces if piece.strip(" ,")]


def _keyword_effect_uses_source(clause: str) -> bool:
    return bool(
        re.search(r"^(?:adapt|amass|level)\b", clause)
        or re.search(r"\b(?:adapt|level)\s+\d+\b", clause)
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
            rf"\b(?:tap|untap|transform|regenerate|sacrifice|exile|destroy|return|put|shuffle)\s+{source}\b",
            clause,
        )
        or re.search(r"^(?:return|exile|sacrifice|destroy|put|tap|untap)\s+it\b", clause)
    )
