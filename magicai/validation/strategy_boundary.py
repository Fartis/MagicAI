from __future__ import annotations

import re
import unicodedata
from typing import Any


CardBlock = dict[str, Any]


_STRATEGY_MARKERS = (
    "merece la pena",
    "vale la pena",
    "es mejor",
    "que es mejor",
    "cual es mejor",
    "en que mazos",
    "en que mazo",
    "que mazo",
    "deberia jugar",
    "debo jugar",
    "jugarias",
    "recomiendas",
    "recomendarías",
    "conviene jugar",
    "worth playing",
    "better than",
    "which is better",
    "what deck",
    "should i play",
    "would you play",
    "recommend",
    "combo",
    "sinergia",
    "synergy",
    "linea de juego",
    "línea de juego",
    "game line",
)


def render_strategy_boundary_answer(knowledge: str) -> str | None:
    """Return a factual Judge answer for questions that require strategy.

    The Judge keeps authority over recovered card facts, but it does not decide
    which card or line is strategically best. That recommendation belongs to
    the future Estratega. The response therefore exposes a compact factual
    summary and makes the domain boundary explicit.
    """

    question = _extract_question(knowledge)

    if not _looks_like_strategy_question(question):
        return None

    cards = _parse_card_blocks(_extract_cards_block(knowledge))
    spanish = _is_spanish_question(question)
    named_format = _detect_named_format(question)

    if _is_combo_question(question):
        return _render_combo_boundary(
            cards,
            spanish=spanish,
            named_format=named_format,
        )

    if spanish:
        return _render_spanish(cards, named_format=named_format)

    return _render_english(cards, named_format=named_format)



def _is_combo_question(question: str) -> bool:
    normalized = _normalize(question)
    return any(marker in normalized for marker in ("combo", "infinito", "infinite", "bucle", "loop"))


def _render_combo_boundary(
    cards: list[CardBlock],
    *,
    spanish: bool,
    named_format: str | None = None,
) -> str:
    names = ", ".join(card["name"] for card in cards)
    format_text = f" en {named_format}" if named_format else ""
    if spanish:
        if names:
            return (
                f"El Juez ha recuperado la base factual de {names}. Determinar si forman un combo{format_text}, "
                "reconstruir el ciclo y calcular su resultado neto corresponde al Estratega; esta respuesta "
                "de frontera está preparada para el handoff automático."
            )
        return (
            "Esta consulta requiere reconstruir y validar una posible línea de combo. El Juez aporta Oracle, "
            "reglas y legalidad, y el Estratega analiza el ciclo mediante el handoff automático."
        )
    if names:
        return (
            f"The Judge recovered the factual package for {names}. Determining whether they form a combo{format_text}, "
            "reconstructing the loop, and calculating its net result belongs to the Tactician; this boundary "
            "answer is ready for automatic handoff."
        )
    return (
        "This question requires reconstructing and validating a possible combo line. The Judge supplies Oracle, "
        "rules, and legality, while the Tactician analyzes the loop through automatic handoff."
    )

def _render_spanish(
    cards: list[CardBlock],
    named_format: str | None = None,
) -> str:
    format_context = (
        f" Has indicado {named_format} como formato."
        if named_format
        else ""
    )

    if not cards:
        return (
            "Esa consulta requiere una valoración estratégica. El Juez puede "
            "validar reglas, Oracle y legalidad, pero la recomendación sobre "
            "qué conviene jugar corresponde a Estratega y depende del "
            "formato, la lista y el plan de juego."
            + format_context
        )

    summaries = [_summarize_card_spanish(card) for card in cards[:3]]
    factual = "; ".join(summary for summary in summaries if summary)

    if len(cards) == 1:
        return (
            f"El Juez puede confirmar estos hechos: {factual}. "
            "Decidir si merece la pena jugar esa carta o en qué mazo encaja mejor es "
            "una recomendación estratégica: depende del formato, la lista, "
            "el plan de juego y el nivel de la mesa, y corresponde a Estratega."
            + format_context
        )

    names = " y ".join(card["name"] for card in cards[:2])
    return (
        f"No hay una respuesta universal sobre cuál es mejor entre {names}: "
        "depende del formato, la lista y el plan de juego, y esa recomendación "
        "estratégica corresponde a Estratega. El Juez sí puede confirmar los "
        f"hechos recuperados: {factual}."
        + format_context
    )


def _render_english(
    cards: list[CardBlock],
    named_format: str | None = None,
) -> str:
    format_context = (
        f" You specified {named_format} as the format."
        if named_format
        else ""
    )

    if not cards:
        return (
            "This requires a strategic evaluation. The Judge can validate rules, "
            "Oracle text, and legality, but the recommendation belongs to Deck "
            "Master and depends on the format, deck list, and game plan."
            + format_context
        )

    summaries = [_summarize_card_english(card) for card in cards[:3]]
    factual = "; ".join(summary for summary in summaries if summary)

    if len(cards) == 1:
        return (
            f"The Judge can confirm these facts: {factual}. Whether it is worth "
            "playing or where it fits best is a strategic recommendation for "
            "Estratega and depends on the format, list, and game plan."
            + format_context
        )

    names = " and ".join(card["name"] for card in cards[:2])
    return (
        f"There is no universal answer about which is better between {names}; "
        "that depends on the format, list, and game plan and belongs to Deck "
        f"Master. The Judge can confirm these recovered facts: {factual}."
        + format_context
    )


def _summarize_card_spanish(card: CardBlock) -> str:
    facts: list[str] = []
    name = card["name"]
    mana_cost = card.get("mana_cost", "")
    lines = card.get("oracle_lines", [])
    oracle_lower = card.get("oracle_text", "").lower()

    if mana_cost:
        facts.append(f"{name} cuesta {mana_cost}")
    else:
        facts.append(name)

    keywords = [_translate_keyword_spanish(item) for item in _keyword_lines(lines)]
    if keywords:
        facts.append("tiene " + " y ".join(keywords[:3]))

    produced_mana = _find_tap_mana_output(lines)
    if produced_mana:
        facts.append(
            f"puede girarse para añadir {produced_mana}, lo que proporciona "
            "aceleración de maná"
        )

    if "draw a card" in oracle_lower and "sacrifice a permanent" in oracle_lower:
        facts.append(
            "premia sacrificar permanentes: recibe un contador +1/+1 y roba una carta"
        )
    elif "draw a card" in oracle_lower:
        facts.append("puede hacerte robar una carta")

    if _has_variable_token_creation(lines):
        facts.append(
            "crea fichas Kobold al lanzarse en una cantidad igual al maná gastado"
            if "kobold" in oracle_lower
            else "crea una cantidad variable de fichas según su texto Oracle"
        )

    if "sacrifice another creature:" in oracle_lower:
        facts.append("puede sacrificar otra criatura para obtener su efecto")

    return ", ".join(facts)


def _summarize_card_english(card: CardBlock) -> str:
    facts: list[str] = []
    name = card["name"]
    mana_cost = card.get("mana_cost", "")
    lines = card.get("oracle_lines", [])
    oracle_lower = card.get("oracle_text", "").lower()

    facts.append(f"{name} costs {mana_cost}" if mana_cost else name)

    keywords = _keyword_lines(lines)
    if keywords:
        facts.append("has " + " and ".join(keywords[:3]))

    produced_mana = _find_tap_mana_output(lines)
    if produced_mana:
        facts.append(f"can tap to add {produced_mana}, providing mana acceleration")

    if "draw a card" in oracle_lower and "sacrifice a permanent" in oracle_lower:
        facts.append("rewards sacrifices with a +1/+1 counter and a card")
    elif "draw a card" in oracle_lower:
        facts.append("can draw a card")

    if _has_variable_token_creation(lines):
        facts.append("creates a variable number of tokens when cast")

    if "sacrifice another creature:" in oracle_lower:
        facts.append("can sacrifice another creature for its effect")

    return ", ".join(facts)


def _keyword_lines(lines: list[str]) -> list[str]:
    keywords: list[str] = []

    for line in lines:
        clean = line.strip()

        if re.fullmatch(r"[A-Za-z][A-Za-z '’-]*", clean):
            if clean not in keywords:
                keywords.append(clean)
            continue

        match = re.match(r"^(?P<keyword>[A-Za-z][A-Za-z '’-]*)\s*\(", clean)
        if match:
            keyword = match.group("keyword").strip()
            if keyword not in keywords:
                keywords.append(keyword)

    return keywords



def _translate_keyword_spanish(value: str) -> str:
    translations = {
        "flying": "vuelo",
        "haste": "prisa",
        "first strike": "dañar primero",
        "double strike": "dañar dos veces",
        "deathtouch": "toque mortal",
        "lifelink": "vínculo vital",
        "trample": "arrollar",
        "vigilance": "vigilancia",
        "reach": "alcance",
        "hexproof": "antimaleficio",
        "indestructible": "indestructible",
    }
    return translations.get(value.casefold(), value)

def _find_tap_mana_output(lines: list[str]) -> str | None:
    for line in lines:
        match = re.match(
            r"^\{T\}:\s*Add\s+(?P<mana>(?:\{[^}]+\})+)\.?$",
            line.strip(),
            flags=re.IGNORECASE,
        )
        if match:
            return match.group("mana")

    return None


def _has_variable_token_creation(lines: list[str]) -> bool:
    return any(
        re.search(r"\bcreate\s+X\b.+\btoken", line, flags=re.IGNORECASE)
        for line in lines
    )


_FORMAT_NAMES: tuple[tuple[str, str], ...] = (
    ("commander", "Commander"),
    ("cedh", "cEDH"),
    ("modern", "Modern"),
    ("pioneer", "Pioneer"),
    ("standard", "Standard"),
    ("legacy", "Legacy"),
    ("vintage", "Vintage"),
    ("pauper", "Pauper"),
    ("brawl", "Brawl"),
    ("historic", "Historic"),
    ("explorer", "Explorer"),
    ("alchemy", "Alchemy"),
)


def _detect_named_format(question: str) -> str | None:
    normalized = _normalize(question)

    for marker, display_name in _FORMAT_NAMES:
        if re.search(r"(?<!\w)" + re.escape(marker) + r"(?!\w)", normalized):
            return display_name

    return None


def _looks_like_strategy_question(question: str) -> bool:
    normalized = _normalize(question)
    return any(marker in normalized for marker in _STRATEGY_MARKERS)


def _extract_question(knowledge: str) -> str:
    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _extract_cards_block(knowledge: str) -> str:
    match = re.search(
        r"CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _parse_card_blocks(cards_block: str) -> list[CardBlock]:
    if not cards_block:
        return []

    pattern = re.compile(
        r"(?P<name>[^\n]+)\n"
        r"Mana Cost:\s*(?P<mana_cost>[^\n]*)\n"
        r"(?P<type_line>[^\n]+)\n"
        r"(?P<oracle_text>.*?)(?=\n\n[^\n]+\nMana Cost:|\Z)",
        flags=re.DOTALL,
    )

    cards: list[CardBlock] = []

    for match in pattern.finditer(cards_block.strip()):
        oracle_lines = [
            line.strip()
            for line in match.group("oracle_text").splitlines()
            if line.strip()
        ]
        cards.append(
            {
                "name": match.group("name").strip(),
                "mana_cost": match.group("mana_cost").strip(),
                "type_line": match.group("type_line").strip(),
                "oracle_text": " ".join(oracle_lines),
                "oracle_lines": oracle_lines,
            }
        )

    return cards


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", normalized.casefold()).strip()


def _is_spanish_question(question: str) -> bool:
    q = _normalize(question)
    return "¿" in question or any(
        marker in q
        for marker in (
            "que ",
            "cual ",
            "merece",
            "mejor",
            "mazo",
            "jugarias",
        )
    )
