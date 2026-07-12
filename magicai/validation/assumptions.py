from __future__ import annotations

import re
from typing import Any


def derive_assumptions(
    *,
    question: str,
    answer: str,
    context: Any | None,
) -> list[str]:
    """Derive only assumptions explicitly implied by the produced answer.

    This intentionally stays conservative: it does not invent a game state or
    pretend that missing information was supplied by the user.
    """

    assumptions: list[str] = []
    normalized_answer = _normalize(answer)

    if "coste impreso" in normalized_answer and re.search(
        r"\b(?:si|cuando)\s+pagas\b",
        normalized_answer,
    ):
        assumptions.append(
            "El ejemplo numérico asume que solo se paga el coste impreso, "
            "sin costes adicionales, aumentos, reducciones ni otros efectos "
            "que cambien el maná realmente gastado."
        )

    if "london mulligan" in normalized_answer and any(
        marker in normalized_answer
        for marker in ("normalmente siete", "normalmente 7")
    ):
        assumptions.append(
            "Se asume un tamaño inicial de mano de siete cartas; formatos o "
            "efectos específicos pueden modificarlo."
        )

    return assumptions


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()
