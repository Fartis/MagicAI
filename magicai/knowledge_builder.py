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

            parts.append(rule["title"])
            parts.append("")

            for number, text in rule["rules"]:

                parts.append(number)
                parts.append(text)
                parts.append("")

    return "\n".join(parts)