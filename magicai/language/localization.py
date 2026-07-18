from __future__ import annotations


_KNOWN_MESSAGES_ES = {
    "A strategic recommendation requires Estratega; the Judge only validates recovered facts.": (
        "Una recomendación estratégica requiere al Estratega; el Juez solo valida los hechos recuperados."
    ),
    "The Judge could not close the factual package; the Strategist's conclusion is limited to the evidence recovered so far.": (
        "El Juez no pudo cerrar el paquete factual; la conclusión del Estratega queda limitada a la evidencia recuperada."
    ),
    "The current evidence package does not prove or disprove this claim yet.": (
        "La evidencia disponible todavía no permite confirmar ni refutar esta afirmación."
    ),
}


def localize_messages(messages: list[str], language: str) -> list[str]:
    if language != "es":
        return list(messages)
    return [_KNOWN_MESSAGES_ES.get(message, message) for message in messages]
