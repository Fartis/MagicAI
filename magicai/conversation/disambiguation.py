import re

from magicai.extractors.cards import find_ambiguous_card_references


def handle_card_disambiguation(
    conversation,
    question: str,
) -> tuple[str | None, str | None]:
    """
    Devuelve:
    - (answer, None) si debe responder pidiendo aclaración.
    - (None, resolved_question) si ha resuelto una aclaración pendiente.
    - (None, None) si no hay nada que hacer.
    """

    if conversation.pending_card_question:

        resolved = _resolve_pending_selection(
            conversation,
            question,
        )

        if resolved:

            return (
                None,
                resolved,
            )

        return (
            _format_pending_clarification(conversation),
            None,
        )

    ambiguity = find_ambiguous_card_references(question)

    if not ambiguity:

        return (
            None,
            None,
        )
    
    active_card_name = _resolve_from_active_cards(
        conversation,
        ambiguity.alias,
    )

    if active_card_name:

        return (
            None,
            _replace_alias_in_question(
                question=question,
                alias=ambiguity.alias,
                replacement=active_card_name,
            ),
        )

    conversation.pending_card_question = question
    conversation.pending_card_alias = ambiguity.alias
    conversation.pending_card_candidates = ambiguity.candidates

    return (
        _format_new_clarification(
            alias=ambiguity.alias,
            candidates=ambiguity.candidates,
            question=question,
        ),
        None,
    )


def _resolve_pending_selection(
    conversation,
    answer: str,
) -> str | None:

    candidates = conversation.pending_card_candidates
    text = answer.strip()
    lower = text.lower()

    selected = None

    if lower.isdigit():

        index = int(lower) - 1

        if 0 <= index < len(candidates):

            selected = candidates[index]

    if not selected:

        for candidate in candidates:

            if candidate.lower() in lower:

                selected = candidate

                break

    if not selected:

        return None

    original_question = conversation.pending_card_question
    alias = conversation.pending_card_alias

    _clear_pending(conversation)

    if not original_question:

        return selected

    if alias:

        pattern = re.compile(
            r"(?<!\w)" + re.escape(alias) + r"(?!\w)",
            flags=re.IGNORECASE,
        )

        resolved = pattern.sub(
            selected,
            original_question,
            count=1,
        )

        if resolved != original_question:

            return resolved

    return original_question + f" ({selected})"


def _clear_pending(conversation):

    conversation.pending_card_question = None
    conversation.pending_card_alias = None
    conversation.pending_card_candidates = []


def _format_new_clarification(
    alias: str,
    candidates: list[str],
    question: str,
) -> str:

    lines = [
        f'He encontrado varias cartas que pueden encajar con "{alias}".',
        "¿A cuál te refieres?",
        "",
    ]

    for index, candidate in enumerate(candidates, start=1):

        lines.append(
            f"{index}. {candidate}"
        )

    lines.extend(
        [
            "",
            "Respóndeme con el número o el nombre de la carta y continúo con la pregunta original.",
        ]
    )

    return "\n".join(lines)


def _format_pending_clarification(conversation) -> str:

    lines = [
        "No he podido identificar cuál de las cartas querías.",
        "Elige una de estas opciones:",
        "",
    ]

    for index, candidate in enumerate(
        conversation.pending_card_candidates,
        start=1,
    ):

        lines.append(
            f"{index}. {candidate}"
        )

    return "\n".join(lines)

def _resolve_from_active_cards(
    conversation,
    alias: str,
) -> str | None:

    active_cards = getattr(
        conversation,
        "active_cards",
        [],
    )

    matches = []

    for card in active_cards:

        name = _card_name(card)

        if not name:

            continue

        if _alias_matches_card_name(
            alias,
            name,
        ):

            if name not in matches:

                matches.append(name)

    if len(matches) == 1:

        return matches[0]

    return None


def _card_name(card) -> str | None:

    if isinstance(card, dict):

        return card.get("name")

    return getattr(
        card,
        "name",
        None,
    )


def _alias_matches_card_name(
    alias: str,
    name: str,
) -> bool:

    alias = alias.lower().strip()
    name_lower = name.lower().strip()

    if alias == name_lower:

        return True

    if "," in name_lower:

        short_name = name_lower.split(",", 1)[0].strip()

        if alias == short_name:

            return True

    first_word = name_lower.split()[0].strip(
        " ,.:;!?\"“”‘’"
    )

    if alias == first_word:

        return True

    return False


def _replace_alias_in_question(
    question: str,
    alias: str,
    replacement: str,
) -> str:

    pattern = re.compile(
        r"(?<!\w)" + re.escape(alias) + r"(?!\w)",
        flags=re.IGNORECASE,
    )

    return pattern.sub(
        replacement,
        question,
        count=1,
    )