import re


GENERAL_RULE_MARKERS = [
    "habilidad",
    "habilidades",
    "priority",
    "prioridad",
    "stack",
    "pila",
    "resuelve",
    "resolver",
    "resolviendo",
    "resolverse",
    "resolución",
    "resolucion",
    "responder",
    "respuesta",
    "paso final",
    "end step",
    "paso de enderezar",
    "untap step",
    "paso de limpieza",
    "cleanup step",
    "jugador activo",
    "jugador no activo",
    "apnap",
    "efecto de reemplazo",
    "efectos de reemplazo",
    "replacement effect",
    "replacement effects",
    "acciones basadas en estado",
    "state-based",
    "zona de mando",
    "command zone",
]


COMMON_LANGUAGE_CARD_ALIASES = {
    "mesa",
    "final",
    "paso",
    "inicio",
    "principio",
    "limpieza",
    "enderezar",
    "resolucion",
    "resolución",
    "respuesta",
    "orden",
}


def looks_like_general_rule_question(question: str) -> bool:
    """
    Heurística conservadora para detectar preguntas de reglas generales.

    No decide la respuesta. Solo ayuda al routing para evitar que palabras
    comunes del español como "mesa" o "final" se interpreten como aliases de
    cartas cuando la pregunta claramente trata de timing, pila, prioridad,
    pasos, zonas o conceptos de reglas.
    """

    q = _normalize(question)

    if not q:
        return False

    return any(
        marker in q
        for marker in GENERAL_RULE_MARKERS
    )


def is_common_language_card_alias(
    alias: str,
    question: str,
) -> bool:

    normalized_alias = _normalize(alias)

    if normalized_alias in COMMON_LANGUAGE_CARD_ALIASES:
        return True

    if looks_like_general_rule_question(question):

        if normalized_alias in COMMON_LANGUAGE_CARD_ALIASES:
            return True

    return False


def _normalize(text: str) -> str:

    text = text.lower().strip()

    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text
