import re


RULE_REF_PATTERN = re.compile(
    r"\b\d{3}(?:\.\d+[a-z]?)?\b"
)


def extract_rules(question: str):

    q = question.lower()

    refs = []

    explicit_refs = RULE_REF_PATTERN.findall(q)

    for rule_ref in explicit_refs:

        _add_unique(
            refs,
            rule_ref,
        )

    #
    # Si el usuario ya ha pedido una regla explícita,
    # no añadimos reglas conceptuales adicionales.
    #
    # Ejemplo:
    #
    # "¿Qué dice la regla 613 sobre las capas?"
    #
    # Ya contiene 613, así que no añadimos además:
    # 613.1, 613.2, 613.3, 613.4, 613.5
    #

    if not explicit_refs:

        _add_concept_rules(
            q,
            refs,
        )

    return _prune_child_refs(refs)


def _add_concept_rules(question: str, refs: list[str]):

    #
    # Capas / Continuous effects
    #

    if _contains_any(
        question,
        [
            "capa",
            "capas",
            "layers",
            "layer",
            "efectos continuos",
            "continuous effects",
        ],
    ):

        _add_unique(refs, "613.1")
        _add_unique(refs, "613.2")
        _add_unique(refs, "613.3")
        _add_unique(refs, "613.4")
        _add_unique(refs, "613.5")

    #
    # Fuerza / resistencia dentro del sistema de capas.
    #
    # Solo añadimos 613.4 porque esa regla ya contiene
    # las subreglas 613.4a, 613.4b, 613.4c y 613.4d.
    #

    if (
        _contains_any(
            question,
            [
                "fuerza",
                "resistencia",
                "power",
                "toughness",
            ],
        )
        and _contains_any(
            question,
            [
                "fija",
                "fijar",
                "base",
                "+1/+1",
                "contador",
                "contadores",
                "set",
                "modify",
                "modifier",
            ],
        )
    ):

        _add_unique(refs, "613.4")

    #
    # Prioridad.
    #

    if _contains_any(
        question,
        [
            "prioridad",
            "priority",
        ],
    ):

        _add_unique(refs, "117")

    #
    # Responder a hechizos / habilidades.
    #

    if _contains_any(
        question,
        [
            "responder",
            "responde",
            "respuesta",
            "en respuesta",
            "antes de que se resuelva",
            "before it resolves",
            "in response",
        ],
    ):

        _add_unique(refs, "117.3c")
        _add_unique(refs, "117.4")
        _add_unique(refs, "117.7")

    #
    # Mulligan.
    #

    if _contains_any(
        question,
        [
            "mulligan",
            "london mulligan",
        ],
    ):

        _add_unique(refs, "103.5")


def _prune_child_refs(refs: list[str]) -> list[str]:

    result = []

    for ref in refs:

        if _has_parent_ref(
            ref,
            refs,
        ):

            continue

        result.append(ref)

    return result


def _has_parent_ref(ref: str, refs: list[str]) -> bool:

    for candidate in refs:

        if candidate == ref:

            continue

        if _is_parent_ref(
            parent=candidate,
            child=ref,
        ):

            return True

    return False


def _is_parent_ref(parent: str, child: str) -> bool:

    #
    # 613 es padre de 613.1, 613.4, etc.
    #

    if "." not in parent:

        return child.startswith(
            parent + "."
        )

    #
    # 613.4 es padre de 613.4a, 613.4b, etc.
    #

    return child.startswith(parent)


def _contains_any(text: str, patterns: list[str]) -> bool:

    return any(
        pattern in text
        for pattern in patterns
    )


def _add_unique(items: list[str], item: str):

    if item not in items:

        items.append(item)