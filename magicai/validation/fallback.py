import re

from magicai.validation.oracle_renderer import render_oracle_fallback


def build_fallback_answer(knowledge: str, violations: list[str]) -> str:
    """
    Fallback seguro.

    Esta capa no interpreta reglas, no conoce cartas concretas y no intenta
    responder por el modelo. Si el LLM falla dos veces, devolvemos una respuesta
    honesta basada en las fuentes recuperadas y pedimos más contexto si hace
    falta.
    """
    rendered_oracle_answer = render_oracle_fallback(
        knowledge
    )

    if rendered_oracle_answer:

        return rendered_oracle_answer

    literal_oracle_answer = _build_literal_oracle_fallback(
        knowledge
    )

    if literal_oracle_answer:

        return literal_oracle_answer

    oracle_lines = _oracle_lines_matching_question(knowledge)

    if oracle_lines:

        return (
            "Con el texto Oracle recuperado, la línea relevante es: "
            + " ".join(oracle_lines)
    )
    
    if _has_cards(knowledge):

        return (
            "No he podido generar una explicación completa con suficiente "
            "seguridad. Con las fuentes recuperadas, puedo afirmar solo lo que "
            "aparece en el texto Oracle de la carta: "
            + _compact_card_text(knowledge)
        )
    
    question = _extract_question(knowledge)

    if _is_spanish_question(question):

        return _build_spanish_safe_fallback(
            knowledge=knowledge,
            violations=violations,
        )

    return _build_english_safe_fallback(
        knowledge=knowledge,
        violations=violations,
    )


def _build_spanish_safe_fallback(
    knowledge: str,
    violations: list[str],
) -> str:

    sources = _summarize_sources(knowledge)

    if sources:

        return (
            "No he podido generar una respuesta suficientemente fiable con el "
            "contexto recuperado. Para no inventar una interacción, revisa las "
            "fuentes que MagicAI sí ha encontrado: "
            + sources
            + "."
        )

    return (
        "No he podido generar una respuesta suficientemente fiable con el "
        "contexto disponible. Necesito recuperar más texto Oracle, reglas o "
        "rulings antes de responder con seguridad."
    )


def _build_english_safe_fallback(
    knowledge: str,
    violations: list[str],
) -> str:

    sources = _summarize_sources(knowledge)

    if sources:

        return (
            "I could not generate a reliable answer from the recovered context. "
            "To avoid inventing an interaction, check the sources MagicAI found: "
            + sources
            + "."
        )

    return (
        "I could not generate a reliable answer from the available context. "
        "More Oracle text, rules, or rulings are needed before answering safely."
    )


def _summarize_sources(knowledge: str) -> str:

    cards = _extract_card_names(knowledge)
    rules = _extract_rule_numbers(knowledge)

    parts = []

    if cards:

        parts.append(
            "cartas: " + ", ".join(cards[:3])
        )

    if rules:

        parts.append(
            "reglas: " + ", ".join(rules[:6])
        )

    return "; ".join(parts)


def _extract_question(knowledge: str) -> str:

    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _extract_card_names(knowledge: str) -> list[str]:

    match = re.search(
        r"CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return []

    names = []

    for block in match.group(1).strip().split("\n\n"):

        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if lines:

            names.append(lines[0])

    return names


def _extract_rule_numbers(knowledge: str) -> list[str]:

    numbers = re.findall(
        r"^\d{3}(?:\.\d+[a-z]?)?",
        knowledge,
        flags=re.MULTILINE,
    )

    result = []

    for number in numbers:

        if number not in result:

            result.append(number)

    return result


def _is_spanish_question(question: str) -> bool:

    lower = question.lower()

    markers = [
        "¿",
        "qué",
        "que ",
        "si ",
        "sacrifico",
        "muere",
        "exilio",
        "lanzar",
        "campo de batalla",
        "prioridad",
        "capas",
        "explícame",
        "merece la pena",
    ]

    return any(
        marker in lower
        for marker in markers
    )

def _extract_cards_block(knowledge: str) -> str:

    match = re.search(
        r"CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _has_cards(knowledge: str) -> bool:

    return bool(
        _extract_cards_block(knowledge)
    )

def _compact_card_text(knowledge: str) -> str:

    block = _extract_cards_block(knowledge)

    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip()
    ]

    useful = []

    for line in lines:

        if line.startswith("Mana Cost:"):

            continue

        if "—" in line:

            continue

        useful.append(line)

    return " ".join(useful[:8])

def _oracle_lines_matching_question(knowledge: str) -> list[str]:

    question = _extract_question(knowledge).lower()
    cards_block = _extract_cards_block(knowledge)

    if not cards_block:

        return []

    triggers = []

    if "sacrific" in question:

        triggers.append("sacrifice")

    if "muere" in question or "morir" in question or "dies" in question:

        triggers.append("dies")

    if "exilio" in question or "exiliar" in question or "exile" in question:

        triggers.append("exile")

    if "entra" in question or "ata" in question or "enters" in question or "attacks" in question:

        triggers.extend(
            [
                "enters",
                "attacks",
            ]
        )

    if not triggers:

        return []

    lines = []

    for line in cards_block.splitlines():

        clean = line.strip()

        if not clean:

            continue

        lower = clean.lower()

        if any(trigger in lower for trigger in triggers):

            lines.append(clean)

    return lines

def _build_literal_oracle_fallback(knowledge: str) -> str | None:

    cards_block = _extract_cards_block(knowledge)

    if not cards_block:

        return None

    question = _extract_question(knowledge)
    spanish = _is_spanish_question(question)

    for card in _parse_card_blocks(cards_block):

        answer = _render_sacrifice_permanent_trigger(
            card,
            spanish=spanish,
        )

        if answer:

            return answer

        answer = _render_damage_any_target(
            card,
            spanish=spanish,
        )

        if answer:

            return answer

    return None


def _parse_card_blocks(cards_block: str) -> list[dict[str, str]]:

    pattern = re.compile(
        r"(?P<name>[^\n]+)\n"
        r"Mana Cost:\s*(?P<mana_cost>[^\n]*)\n"
        r"(?P<type_line>[^\n]+)\n"
        r"(?P<oracle_text>.*?)(?=\n\n[^\n]+\nMana Cost:|\Z)",
        flags=re.DOTALL,
    )

    cards = []

    for match in pattern.finditer(cards_block.strip()):

        oracle_text = " ".join(
            line.strip()
            for line in match.group("oracle_text").splitlines()
            if line.strip()
        )

        cards.append(
            {
                "name": match.group("name").strip(),
                "mana_cost": match.group("mana_cost").strip(),
                "type_line": match.group("type_line").strip(),
                "oracle_text": oracle_text,
            }
        )

    return cards

def _render_sacrifice_permanent_trigger(
    card: dict[str, str],
    spanish: bool,
) -> str | None:

    oracle_text = card["oracle_text"]

    if "sacrifice" not in oracle_text.lower():

        return None

    match = re.search(
        r"whenever you sacrifice a permanent,\s*"
        r"put a \+1/\+1 counter on (?P<target>.+?)\s+"
        r"and draw a card\.?",
        oracle_text,
        flags=re.IGNORECASE,
    )

    if not match:

        return None

    target = match.group("target").strip()

    if spanish:

        return (
            "El texto Oracle recuperado indica que, cuando sacrificas "
            f"un permanente, pones un contador +1/+1 en {target} "
            "y robas una carta."
        )

    return (
        "The recovered Oracle text says that whenever you sacrifice "
        f"a permanent, you put a +1/+1 counter on {target} "
        "and draw a card."
    )


def _render_damage_any_target(
    card: dict[str, str],
    spanish: bool,
) -> str | None:

    oracle_text = card["oracle_text"]

    match = re.search(
        r"\b(.+?)\s+deals\s+(\d+|X)\s+damage\s+to\s+any target\.?",
        oracle_text,
        flags=re.IGNORECASE,
    )

    if not match:

        return None

    name = card["name"]
    mana_cost = card["mana_cost"]
    type_line = card["type_line"]
    damage = match.group(2)

    if spanish:

        description_parts = []

        if mana_cost:

            description_parts.append(
                f"cuesta {mana_cost}"
            )

        if "instant" in type_line.lower():

            description_parts.append(
                "es un instantáneo"
            )

        if description_parts:

            intro = (
                name
                + " "
                + " y ".join(description_parts)
            )

        else:

            intro = name

        return (
            f"{intro}. "
            f"Hace {damage} puntos de daño a cualquier objetivo válido."
        )

    description_parts = []

    if mana_cost:

        description_parts.append(
            f"costs {mana_cost}"
        )

    if "instant" in type_line.lower():

        description_parts.append(
            "is an instant"
        )

    if description_parts:

        intro = (
            name
            + " "
            + " and ".join(description_parts)
        )

    else:

        intro = name

    return (
        f"{intro}. "
        f"It deals {damage} damage to any valid target."
    )