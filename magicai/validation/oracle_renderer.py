import re
from typing import Any


CardBlock = dict[str, Any]


def render_oracle_fallback(knowledge: str) -> str | None:
    """
    Renderiza una respuesta segura a partir del texto Oracle recuperado.

    Esta capa no conoce cartas concretas ni keywords concretas.
    Solo reconoce estructuras generales de Oracle, por ejemplo:
    - When/Whenever/At ..., efecto.
    - if it had no +/-N/+/-N counters on it.
    - return it to the battlefield ... with a counter.
    - put a counter on ... and draw a card.
    - deals N damage to any target.
    """

    cards_block = _extract_cards_block(
        knowledge
    )

    if not cards_block:

        return None

    question = _extract_question(
        knowledge
    )

    spanish = _is_spanish_question(
        question
    )

    action = _question_action(
        question
    )

    candidates: list[tuple[int, CardBlock, str]] = []

    for card in _parse_card_blocks(cards_block):

        for line in card["oracle_lines"]:

            score = _score_oracle_line(
                card=card,
                line=line,
                action=action,
                knowledge=knowledge,
            )

            if score <= 0:

                continue

            candidates.append(
                (
                    score,
                    card,
                    line,
                )
            )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    for _score, card, line in candidates:

        answer = _render_oracle_line(
            card=card,
            line=line,
            spanish=spanish,
            action=action,
            knowledge=knowledge,
        )

        if answer:

            return answer

    return None


def _extract_question(knowledge: str) -> str:

    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _extract_cards_block(knowledge: str) -> str:

    match = re.search(
        r"CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _parse_card_blocks(cards_block: str) -> list[CardBlock]:

    pattern = re.compile(
        r"(?P<name>[^\n]+)\n"
        r"Mana Cost:\s*(?P<mana_cost>[^\n]*)\n"
        r"(?P<type_line>[^\n]+)\n"
        r"(?P<oracle_text>.*?)(?=\n\n[^\n]+\nMana Cost:|\Z)",
        flags=re.DOTALL,
    )

    cards = []

    for match in pattern.finditer(cards_block.strip()):

        raw_oracle_text = match.group("oracle_text").strip()

        oracle_lines = [
            line.strip()
            for line in raw_oracle_text.splitlines()
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


def _question_action(question: str) -> str | None:

    lower = question.lower()

    if "sacrific" in lower:

        return "sacrifice"

    if (
        "muere" in lower
        or "morir" in lower
        or "dies" in lower
        or "die" in lower
    ):

        return "dies"

    if (
        "exilio" in lower
        or "exiliar" in lower
        or "exile" in lower
    ):

        return "exile"

    if (
        "entra" in lower
        or "entrar" in lower
        or "enters" in lower
    ):

        return "enters"

    if (
        "ataca" in lower
        or "atacar" in lower
        or "attacks" in lower
    ):

        return "attacks"

    return None


def _score_oracle_line(
    card: CardBlock,
    line: str,
    action: str | None,
    knowledge: str,
) -> int:

    lower = line.lower()
    condition = _extract_trigger_condition(line).lower()

    if action == "sacrifice":

        if "you sacrifice" in condition:

            return 100

        if (
            "dies" in condition
            and _is_creature(card)
            and _knowledge_supports_sacrifice_as_death(knowledge)
        ):

            return 90

        if "sacrifice" in lower:

            return 20

        return 0

    if action == "dies":

        if "dies" in condition:

            return 100

        if "graveyard from the battlefield" in lower:

            return 80

        return 0

    if action == "exile":

        if "exile" in condition or "exile" in lower:

            return 100

        return 0

    if action == "enters":

        if "enters" in condition:

            return 100

        return 0

    if action == "attacks":

        if "attacks" in condition:

            return 100

        return 0

    if _looks_like_keyword_parenthetical(line):

        return 70

    if _looks_like_triggered_ability(line):

        return 60

    if _looks_like_damage_any_target(line):

        return 60

    return 0


def _render_oracle_line(
    card: CardBlock,
    line: str,
    spanish: bool,
    action: str | None,
    knowledge: str,
) -> str | None:

    bridge = ""

    if (
        action == "sacrifice"
        and _is_creature(card)
        and "dies" in _extract_trigger_condition(line).lower()
        and _knowledge_supports_sacrifice_as_death(knowledge)
    ):

        if spanish:

            bridge = (
                "Según las reglas recuperadas, sacrificar una criatura la pone "
                "en el cementerio desde el campo de batalla, así que puede "
                "cumplir una condición de “muere”. "
            )

        else:

            bridge = (
                "According to the recovered rules, sacrificing a creature puts "
                "it into its owner's graveyard from the battlefield, so it can "
                "satisfy a dies condition. "
            )

    keyword_match = re.match(
        r"^(?P<label>[^()]+)\((?P<inner>(?:When|Whenever|At)\s+.+)\)$",
        line.strip(),
        flags=re.IGNORECASE,
    )

    if keyword_match:

        label = keyword_match.group("label").strip()
        inner = keyword_match.group("inner").strip()

        rendered = _render_triggered_sentence(
            sentence=inner,
            spanish=spanish,
            label=label,
        )

        if rendered:

            return bridge + rendered

    if _looks_like_triggered_ability(line):

        rendered = _render_triggered_sentence(
            sentence=line,
            spanish=spanish,
            label=None,
        )

        if rendered:

            return bridge + rendered

    rendered_damage = _render_damage_any_target(
        card=card,
        line=line,
        spanish=spanish,
    )

    if rendered_damage:

        return rendered_damage

    return None


def _render_triggered_sentence(
    sentence: str,
    spanish: bool,
    label: str | None,
) -> str | None:

    match = re.match(
        r"^(?:when|whenever|at)\s+"
        r"(?P<condition>.*?),\s*"
        r"(?:(?:if)\s+(?P<if_clause>.*?),\s*)?"
        r"(?P<effect>.+?)\.?$",
        sentence.strip(),
        flags=re.IGNORECASE,
    )

    if not match:

        return None

    condition = match.group("condition").strip()

    if_clause = (
        match.group("if_clause").strip()
        if match.group("if_clause")
        else ""
    )

    effect = match.group("effect").strip()

    if spanish:

        rendered_condition = _render_condition_spanish(
            condition
        )

        rendered_if = _render_if_clause_spanish(
            if_clause
        )

        rendered_effect = _render_effect_spanish(
            effect
        )

        if not rendered_effect:

            return None

        prefix = "El texto Oracle recuperado indica que"

        if label:

            prefix = f"{label} indica que"

        parts = [
            f"{prefix}, cuando {rendered_condition}",
        ]

        if rendered_if:

            parts.append(
                rendered_if
            )

        return (
            ", ".join(parts)
            + ", "
            + rendered_effect
            + "."
        )

    rendered_effect = _render_effect_english(
        effect
    )

    if not rendered_effect:

        return None

    prefix = "The recovered Oracle text says that"

    if label:

        prefix = f"{label} means that"

    return (
        f"{prefix}, when {condition}, "
        f"{rendered_effect}."
    )


def _render_condition_spanish(condition: str) -> str:

    lower = condition.lower()

    if lower == "this creature dies":

        return "esta criatura muere"

    if lower == "this permanent dies":

        return "este permanente muere"

    if lower == "you sacrifice a permanent":

        return "sacrificas un permanente"

    if lower == "you sacrifice a creature":

        return "sacrificas una criatura"

    match = re.match(
        r"(?P<name>.+?)\s+enters or attacks$",
        condition,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            match.group("name").strip()
            + " entra o ataca"
        )

    match = re.match(
        r"(?P<name>.+?)\s+enters$",
        condition,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            match.group("name").strip()
            + " entra al campo de batalla"
        )

    match = re.match(
        r"(?P<name>.+?)\s+attacks$",
        condition,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            match.group("name").strip()
            + " ataca"
        )

    return (
        "se cumple la condición indicada en Oracle: "
        f"«{condition}»"
    )


def _render_if_clause_spanish(if_clause: str) -> str:

    if not if_clause:

        return ""

    match = re.match(
        r"it had no (?P<counter>[+-]\d/[+-]\d) counters? on it",
        if_clause,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            "si no tenía contadores "
            + match.group("counter")
        )

    return f"si {if_clause}"


def _render_effect_spanish(effect: str) -> str:

    parts = _split_effect_parts(
        effect
    )

    rendered_parts = []

    for part in parts:

        rendered = _render_single_effect_spanish(
            part
        )

        if rendered:

            rendered_parts.append(
                rendered
            )

    if not rendered_parts:

        return ""

    if len(rendered_parts) == 1:

        return rendered_parts[0]

    return (
        ", ".join(rendered_parts[:-1])
        + " y "
        + rendered_parts[-1]
    )


def _render_single_effect_spanish(effect: str) -> str:

    clean = effect.strip().rstrip(".")
    lower = clean.lower()

    match = re.match(
        r"return (?:it|this permanent|this card|that card) "
        r"to the battlefield"
        r"(?: under its owner[’']s control)?"
        r"(?: with a (?P<counter>[+-]\d/[+-]\d) counter on it)?",
        clean,
        flags=re.IGNORECASE,
    )

    if match:

        counter = match.group("counter")

        result = (
            "vuelve al campo de batalla bajo el control de su dueño"
        )

        if counter:

            result += (
                f" con un contador {counter}"
            )

        return result

    match = re.match(
        r"put a (?P<counter>[+-]\d/[+-]\d) counter on (?P<target>.+)",
        clean,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            f"pones un contador {match.group('counter')} "
            f"en {match.group('target').strip()}"
        )

    if lower == "draw a card":

        return "robas una carta"

    match = re.match(
        r"sacrifice another (?P<object>permanent|creature)",
        clean,
        flags=re.IGNORECASE,
    )

    if match:

        object_name = match.group("object").lower()

        if object_name == "permanent":

            return "sacrificas otro permanente"

        if object_name == "creature":

            return "sacrificas otra criatura"

    match = re.match(
        r"(?P<source>.+?) deals (?P<amount>\d+|X) damage to any target",
        clean,
        flags=re.IGNORECASE,
    )

    if match:

        return (
            f"hace {match.group('amount')} puntos de daño "
            "a cualquier objetivo válido"
        )

    return ""


def _render_effect_english(effect: str) -> str:

    return effect.strip().rstrip(".")


def _render_damage_any_target(
    card: CardBlock,
    line: str,
    spanish: bool,
) -> str | None:

    match = re.search(
        r"\b(?P<source>.+?)\s+deals\s+(?P<amount>\d+|X)\s+"
        r"damage\s+to\s+any target\.?",
        line,
        flags=re.IGNORECASE,
    )

    if not match:

        return None

    name = str(card["name"])
    mana_cost = str(card["mana_cost"])
    type_line = str(card["type_line"])
    amount = match.group("amount")

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

        intro = name

        if description_parts:

            intro += (
                " "
                + " y ".join(description_parts)
            )

        return (
            f"{intro}. "
            f"Hace {amount} puntos de daño a cualquier objetivo válido."
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

    intro = name

    if description_parts:

        intro += (
            " "
            + " and ".join(description_parts)
        )

    return (
        f"{intro}. "
        f"It deals {amount} damage to any valid target."
    )


def _split_effect_parts(effect: str) -> list[str]:

    return [
        part.strip()
        for part in re.split(
            r"\s+and\s+",
            effect,
            flags=re.IGNORECASE,
        )
        if part.strip()
    ]


def _extract_trigger_condition(line: str) -> str:

    keyword_match = re.match(
        r"^[^()]+\((?P<inner>(?:When|Whenever|At)\s+.+)\)$",
        line.strip(),
        flags=re.IGNORECASE,
    )

    source = (
        keyword_match.group("inner")
        if keyword_match
        else line.strip()
    )

    match = re.match(
        r"^(?:when|whenever|at)\s+(?P<condition>.*?),",
        source,
        flags=re.IGNORECASE,
    )

    if not match:

        return ""

    return match.group("condition").strip()


def _looks_like_keyword_parenthetical(line: str) -> bool:

    return bool(
        re.match(
            r"^[^()]+\((?:When|Whenever|At)\s+.+\)$",
            line.strip(),
            flags=re.IGNORECASE,
        )
    )


def _looks_like_triggered_ability(line: str) -> bool:

    return bool(
        re.match(
            r"^(When|Whenever|At)\s+",
            line.strip(),
            flags=re.IGNORECASE,
        )
    )


def _looks_like_damage_any_target(line: str) -> bool:

    return bool(
        re.search(
            r"\bdeals\s+(\d+|X)\s+damage\s+to\s+any target",
            line,
            flags=re.IGNORECASE,
        )
    )


def _is_creature(card: CardBlock) -> bool:

    return "creature" in str(
        card.get("type_line", "")
    ).lower()


def _knowledge_supports_sacrifice_as_death(knowledge: str) -> bool:

    lower = knowledge.lower()

    has_sacrifice_rule = (
        "to sacrifice a permanent" in lower
        and "battlefield" in lower
        and "graveyard" in lower
    )

    has_death_definition = (
        "the term dies means" in lower
        and "graveyard from the battlefield" in lower
    )

    has_keyword_rule_equivalence = (
        "graveyard from the battlefield" in lower
        or (
            "put into a graveyard" in lower
            and "from the battlefield" in lower
        )
    )

    return (
        has_sacrifice_rule
        and (
            has_death_definition
            or has_keyword_rule_equivalence
        )
    )


def _is_spanish_question(question: str) -> bool:

    lower = question.lower()

    markers = [
        "¿",
        "qué",
        "que ",
        "si ",
        "sacrifico",
        "sacrificar",
        "muere",
        "morir",
        "exilio",
        "exiliar",
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
