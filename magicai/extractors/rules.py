import re


RULE_REF_PATTERN = re.compile(
    r"\b\d{3}(?:\.\d+[a-z]?)?\b"
)


def extract_rules(question: str):
    """
    Extrae únicamente referencias explícitas a reglas.

    Esta capa no traduce conceptos a números de regla. Si el usuario pregunta
    por "capas", "prioridad" o "mulligan", la recuperación conceptual se hace
    mediante búsqueda textual sobre las Comprehensive Rules, no mediante IDs
    codificados aquí.
    """

    refs = []

    for rule_ref in RULE_REF_PATTERN.findall(question.lower()):

        _add_unique(
            refs,
            rule_ref,
        )

    return refs


def _add_unique(items: list[str], item: str):

    if item not in items:

        items.append(item)
