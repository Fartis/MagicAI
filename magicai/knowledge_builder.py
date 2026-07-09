def build_knowledge(context):

    parts = []

    parts.append("QUESTION")
    parts.append("")
    parts.append(context.question)
    parts.append("")

    if context.cards:

        parts.append("=" * 60)
        parts.append("CARDS")
        parts.append("")

        for card in context.cards:

            parts.append(card.name)

            if card.mana_cost:
                parts.append(f"Mana Cost: {card.mana_cost}")

            parts.append(card.type_line)
            parts.append("")

            if card.oracle_text:
                parts.append(card.oracle_text)

            parts.append("")

    if context.rules:

        parts.append("=" * 60)
        parts.append("RULES")
        parts.append("")

        for rule in context.rules:

            _append_rule(parts, rule)

    if context.facts:

        parts.append("=" * 60)
        parts.append("REASONING HINTS")
        parts.append("")

        for fact in context.facts:

            parts.append(f"- {fact}")

        parts.append("")

    return "\n".join(parts)


def _append_rule(parts, rule):

    number = rule.get("number")
    title = rule.get("title")
    subrules = rule.get("rules", [])

    #
    # Caso 1:
    # Regla con subreglas.
    #
    # Ejemplo:
    #
    # 701.21. Sacrifice
    # 701.21a To sacrifice...
    #
    # Aquí mantenemos el comportamiento actual:
    #
    # Sacrifice
    # 701.21a
    # To sacrifice...
    #

    if subrules:

        parts.append(title)
        parts.append("")

        for rule_number, text in subrules:

            parts.append(rule_number)
            parts.append(text)
            parts.append("")

        return

    #
    # Caso 2:
    # Regla directa sin subreglas.
    #
    # Ejemplo:
    #
    # 700.4. The term dies means...
    #
    # Antes se imprimía solo el texto.
    # Ahora imprimimos también el número.
    #

    if number:

        parts.append(number)

    if title:

        parts.append(title)

    parts.append("")