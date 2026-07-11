import re


TRIGGERED_PATTERN = re.compile(
    r"\b(when|whenever|at)\b",
    flags=re.IGNORECASE,
)

BASIC_LAND_TYPES = (
    "plains",
    "island",
    "swamp",
    "mountain",
    "forest",
)


def build_oracle_rule_queries(
    oracle_text: str,
    focus: set[str] | None = None,
) -> list[str]:
    """
    Deriva consultas de reglas desde Oracle sin afirmar una respuesta.

    ``focus`` permite al contexto pedir solo las familias relevantes para la
    pregunta. Esto evita que una habilidad disparada incidental en una carta
    desplace, por ejemplo, las reglas de capas que realmente necesita una
    interacción de efectos continuos.
    """

    if not oracle_text:
        return []

    queries = []

    for line in oracle_text.splitlines():

        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        # Efectos continuos que modifican características. Se añaden antes que
        # habilidades disparadas o activadas porque suelen ser la evidencia
        # principal en interacciones de capas.
        if _wants(focus, "continuous"):

            if _looks_like_type_changing_effect(lower):
                _add_unique(queries, "613.1d")

            if _looks_like_ability_removing_effect(lower):
                _add_unique(queries, "613.1f")

            if _looks_like_ability_adding_effect(lower):
                _add_unique(queries, "613.1f")

            if _looks_like_power_toughness_setting_effect(lower):
                _add_unique(queries, "613.4b")

            if _sets_basic_land_type(lower):
                _add_unique(queries, "305.7")

            if _looks_like_multilayer_effect(lower):
                _add_unique(queries, "613.6")

        if _wants(focus, "activated") and _looks_like_activated_ability(line):

            _add_unique(
                queries,
                "activated ability",
            )

            if "add " in lower and _wants(focus, "mana"):

                _add_unique(
                    queries,
                    "mana ability",
                )

        if _wants(focus, "triggered") and _looks_like_triggered_ability(line):

            _add_unique(
                queries,
                "triggered ability",
            )

    return queries


def _wants(focus: set[str] | None, concept: str) -> bool:

    return focus is None or concept in focus


def _looks_like_activated_ability(line: str) -> bool:

    if ":" not in line:

        return False

    left, _, right = line.partition(":")

    return bool(
        left.strip()
        and right.strip()
    )


def _looks_like_triggered_ability(line: str) -> bool:

    return TRIGGERED_PATTERN.search(line) is not None


def _looks_like_type_changing_effect(lower: str) -> bool:

    if any(
        marker in lower
        for marker in [
            " in addition to its other types",
            "loses all other card types",
            "becomes a creature",
            "is a creature",
            "becomes an artifact",
            "is an artifact",
            "becomes an enchantment",
            "is an enchantment",
        ]
    ):
        return True

    return bool(
        re.search(r"\bis (?:a |an )?[^.]*\bland\b", lower)
        or re.search(r"\bbecomes (?:a |an )?[^.]*\bland\b", lower)
    )


def _looks_like_ability_removing_effect(lower: str) -> bool:

    return (
        "loses all abilities" in lower
        or (
            "loses all other" in lower
            and "abilities" in lower
        )
        or "can't have abilities" in lower
        or "cannot have abilities" in lower
    )


def _looks_like_ability_adding_effect(lower: str) -> bool:

    return (
        " has " in f" {lower} "
        and any(
            marker in lower
            for marker in [
                "indestructible",
                "haste",
                "flying",
                "trample",
                "vigilance",
                "lifelink",
                "deathtouch",
                "ward",
                '"whenever',
                '"when',
                '"at ',
            ]
        )
    )


def _looks_like_power_toughness_setting_effect(lower: str) -> bool:

    return bool(
        re.search(r"\bis (?:a |an )?\d+/\d+\b", lower)
        or "base power and toughness" in lower
        or "base power and base toughness" in lower
    )


def _sets_basic_land_type(lower: str) -> bool:

    if "land" not in lower:
        return False

    return any(
        re.search(rf"\b{land_type}\b", lower)
        for land_type in BASIC_LAND_TYPES
    )


def _looks_like_multilayer_effect(lower: str) -> bool:

    categories = 0

    if _looks_like_type_changing_effect(lower):
        categories += 1

    if _looks_like_ability_removing_effect(lower) or _looks_like_ability_adding_effect(lower):
        categories += 1

    if _looks_like_power_toughness_setting_effect(lower):
        categories += 1

    return categories >= 2


def _add_unique(items: list[str], item: str):

    if item and item not in items:

        items.append(item)
