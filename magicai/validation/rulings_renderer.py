from __future__ import annotations

import re


_RULINGS_MARKERS = (
    "ruling",
    "rulings",
    "dictamen",
    "aclaración oficial",
    "aclaracion oficial",
    "fallo oficial",
    "qué dice scryfall",
    "que dice scryfall",
    "qué dice wizards",
    "que dice wizards",
)


def render_rulings_answer(knowledge: str) -> str | None:
    """Render requested rulings literally from recovered local evidence.

    Rulings are quoted rather than paraphrased so the Judge cannot introduce
    facts that are absent from the official comments. Translation can be a
    separate UI concern later; the factual answer remains auditable here.
    """

    question = _extract_question(knowledge).lower()
    if not any(marker in question for marker in _RULINGS_MARKERS):
        return None

    rulings = _extract_rulings(knowledge)
    if not rulings:
        return None

    card_names = []
    for ruling in rulings:
        name = ruling.get("card_name", "")
        if name and name not in card_names:
            card_names.append(name)

    if len(card_names) == 1:
        heading = (
            f"Los rulings oficiales recuperados para **{card_names[0]}** "
            "son (texto oficial):"
        )
    else:
        heading = "Los rulings oficiales recuperados son (texto oficial):"

    lines = [heading]
    for index, ruling in enumerate(rulings, start=1):
        metadata = ", ".join(
            value
            for value in (
                ruling.get("published_at", ""),
                _source_label(ruling.get("source", "")),
            )
            if value
        )
        prefix = f"{index}."
        if metadata:
            prefix += f" [{metadata}]"
        lines.append(f"{prefix} {ruling['comment']}")

    lines.append(
        "Se muestran literalmente para no alterar el contenido factual de la fuente."
    )
    return "\n".join(lines)


def _extract_question(knowledge: str) -> str:
    match = re.search(
        r"(?:^|\n)QUESTION\s*\n+(.*?)(?=\n={10,}|\Z)",
        knowledge,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _extract_rulings(knowledge: str) -> list[dict[str, str]]:
    match = re.search(
        r"(?:^|\n)RULINGS\s*\n+(.*?)(?=\n={10,}|\Z)",
        knowledge,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []

    block = match.group(1).strip()
    chunks = re.split(r"\n\s*\n", block)
    rulings: list[dict[str, str]] = []

    for chunk in chunks:
        payload = {
            "card_name": "",
            "published_at": "",
            "source": "",
            "comment": "",
        }
        comment_lines: list[str] = []

        for line in chunk.splitlines():
            stripped = line.strip()
            if stripped.startswith("Card:"):
                payload["card_name"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Published:"):
                payload["published_at"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Source:"):
                payload["source"] = stripped.split(":", 1)[1].strip()
            elif stripped:
                comment_lines.append(stripped)

        payload["comment"] = " ".join(comment_lines).strip()
        if payload["comment"]:
            rulings.append(payload)

    return rulings


def _source_label(source: str) -> str:
    normalized = source.strip().lower()
    if normalized == "wotc":
        return "WotC"
    if normalized == "scryfall":
        return "Scryfall"
    return source.strip()
