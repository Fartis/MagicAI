import re

from magicai.validation.fallback import _extract_cards_block


_BAD_SPANISH_TERMS = [
    "tumba",
    "gravedad",
    "tumba de batalla",
    "enterrada",
    "enterrado",
    "enterradas",
    "enterrados",
    "enterrar",
    "dibuja una carta",
    "dibujas una carta",
    "dibujar una carta",
    "te harías dibujar",
    "mueres",
    "permanente mueres",
    "el permanente mueres",
    "la permanente mueres",
    "al ser tocado",
    "cuando lo tapas",
    "cuando se tapea",
    "tapeado",
    "tapear","costa {",
    "costa un",
    "costa una",
]

_MIXED_ENGLISH_TERMS = [
    "mana colorless",
    "maná colorless",
]


def validate_answer(answer: str, knowledge: str) -> list[str]:

    violations = []

    if not answer:

        violations.append(
            "The answer is empty."
        )

        return violations

    if _is_rule_lookup(knowledge):
        return [
            violation
            for violation in violations
            if "contradicts" in violation.lower()
        ]
    
    if _looks_incomplete(answer):

        violations.append(
            "The answer looks incomplete."
        )

    if _is_spanish_question(knowledge):

        if _looks_like_wrong_language(answer):

            violations.append(
                "The answer appears to be in the wrong language."
            )

        if _contains_bad_spanish_terms(answer):

            violations.append(
                "The answer contains bad Spanish MTG wording."
            )

        if _contains_mixed_english_terms(answer):

            violations.append(
                "The answer mixes English terms in a Spanish answer."
            )

    if _mentions_unavailable_named_example(answer, knowledge):

        violations.append(
            "The answer appears to use a named example that is not present in the provided knowledge."
        )

    if _contradicts_recovered_symbols(answer, knowledge):

        violations.append(
            "The answer contradicts recovered symbol definitions."
        )

    if _mentions_zone_not_in_sources(answer, knowledge):

        violations.append(
            "The answer mentions a game zone that does not appear in the recovered sources."
        )

    if _contradicts_triggered_ability(answer, knowledge):

        violations.append(
            "The answer describes a triggered ability as an activated ability."
        )

    if _mentions_triggered_without_source(answer, knowledge):

        violations.append(
            "The answer describes an ability as triggered without recovered support."
        )
    if _is_rule_only_context(knowledge):

        violations = [
            violation
            for violation in violations
            if _is_hard_violation(violation)
        ]

    if _mentions_extra_target_categories(answer, knowledge):

        violations.append(
            "The answer introduces target categories not present in the recovered Oracle text."
        )

    if _mentions_immediate_resolution_without_support(answer, knowledge):

        violations.append(
            "The answer claims immediate resolution without recovered timing support."
        )

    if _has_card_and_rule_support(knowledge):

        violations = [
            violation
            for violation in violations
            if _is_hard_violation(violation)
        ]

    if _mentions_dies_in_graveyard(answer):

        violations.append(
            "The answer says a creature dies in the graveyard, which is incorrect."
        )

    if _mentions_response_during_resolution(answer, knowledge):

        violations.append(
            "The answer incorrectly says a player responds during resolution."
        )

    if _incorrectly_denies_response_before_resolution(answer, knowledge):

        violations.append(
            "The answer incorrectly denies that an opponent can respond before resolution."
        )

    if _contradicts_sacrifice_trigger_oracle(answer, knowledge):

        violations.append(
            "The answer contradicts recovered Oracle text about a sacrifice trigger."
        )

    if _adds_unasked_self_sacrifice_edge_case(answer, knowledge):

        violations.append(
            "The answer adds an unasked self-sacrifice edge case."
        )

    if _fails_to_answer_copied_ability_source_removal(answer, knowledge):

        violations.append(
            "The answer is incomplete for a copied ability whose source leaves the battlefield."
        )


    if _has_card_support(knowledge):

        violations = [
            violation
            for violation in violations
            if _is_hard_violation(violation)
        ]

    # Concept-specific factual guards run after generic evidence filters. A
    # well-sourced answer can still contradict Ward's actual procedure.
    violations.extend(_ward_semantic_violations(answer, knowledge))
    violations.extend(_source_independence_semantic_violations(answer, knowledge))

    return list(dict.fromkeys(violations))


def _ward_semantic_violations(answer: str, knowledge: str) -> list[str]:
    question = _normalize_match_text(_extract_question(knowledge))
    if not re.search(r"\bward\b", question):
        return []

    text = _normalize_match_text(answer)
    violations: list[str] = []
    if re.search(r"\bward\s+se\s+activa\b|\bse\s+activa\s+ward\b", text):
        violations.append("The answer incorrectly describes Ward as an activated ability.")
    if any(marker in text for marker in (
        "responder durante su resolucion",
        "responder durante la resolucion de ward",
        "respond during its resolution",
    )):
        violations.append("The answer incorrectly allows responses during Ward resolution.")
    if any(marker in text for marker in (
        "pagar para evitar que el hechizo se resuelva",
        "paga para evitar que el hechizo se resuelva",
        "pay to stop the spell from resolving",
    )):
        violations.append("The answer misstates what paying the Ward cost prevents.")

    if not any(marker in text for marker in (
        "habilidad disparada",
        "habilidad desencadenada",
        "triggered ability",
    )):
        violations.append("The answer does not identify Ward as a triggered ability.")
    if "pila" not in text and "stack" not in text:
        violations.append("The answer does not place Ward on the stack.")
    if "contrarrest" not in text and "counter" not in text:
        violations.append("The answer does not explain Ward's countering effect.")
    if not (
        any(marker in text for marker in (
            "si no paga",
            "si no se paga",
            "a menos que pague",
            "unless that player pays",
            "unless its controller pays",
        ))
        or re.search(r"\bsi\b[^.]{0,100}\bno\s+paga\b", text)
    ):
        violations.append("The answer does not link Ward's countering effect to nonpayment.")
    return violations



def _source_independence_semantic_violations(answer: str, knowledge: str) -> list[str]:
    question = _normalize_match_text(_extract_question(knowledge))
    if not (
        "fuente" in question
        and ("pila" in question or "destruy" in question or "elimin" in question)
    ):
        return []

    text = _normalize_match_text(answer)
    violations: list[str] = []
    if "no fue uno de los objetos sacrificados" in question and not any(marker in text for marker in (
        "no fue uno de los objetos sacrificados",
        "no fue sacrificada para pagar",
        "si se hubiera sacrificado la fuente",
        "si hubieras sacrificado la propia fuente",
    )):
        violations.append(
            "The answer omits that the source was not used to pay an optional sacrifice cost."
        )
    if "ninguno de los objetivos" in question and not any(marker in text for marker in (
        "ninguno de los objetivos era la fuente",
        "si la fuente hubiera sido objetivo",
        "si la fuente hubiera sido también el único objetivo",
        "si la fuente hubiera sido tambien el unico objetivo",
        "si la fuente fuese objetivo",
        "objetivo ilegal",
        "todos sus objetivos",
    )):
        violations.append(
            "The answer omits the separate target-legality consequence if the source were a target."
        )
    return violations

def _normalize_match_text(text: str) -> str:
    value = (text or "").casefold()
    replacements = str.maketrans({
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
    })
    return " ".join(value.translate(replacements).split())


def _looks_incomplete(answer: str) -> bool:

    text = answer.strip()

    if not text:

        return True

    unfinished_endings = (
        " con",
        " de",
        " que",
        " si",
        " porque",
        " cuando",
        " with",
        " of",
        " that",
        " because",
        " when",
    )

    lower = text.lower()

    if lower.endswith(unfinished_endings):

        return True

    if text[-1] not in ".!?…":

        return True

    return False


def _is_spanish_question(knowledge: str) -> bool:

    question = _extract_question(knowledge)

    lower = question.lower()

    spanish_markers = [
        "¿",
        "qué",
        "que ",
        "si ",
        "sacrifico",
        "muere",
        "exilio",
        "lanzar",
        "campo de batalla",
        "prioridad",
        "capas",
        "explícame",
        "merece la pena",
    ]

    return any(
        marker in lower
        for marker in spanish_markers
    )


def _extract_question(knowledge: str) -> str:

    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _looks_like_wrong_language(answer: str) -> bool:

    lower = answer.strip().lower()

    english_starts = (
        "if ",
        "when ",
        "exiling ",
        "sacrificing ",
        "you ",
    )

    if lower.startswith(english_starts):

        return True

    english_phrases = (
        "does not trigger",
        "if you exile",
        "when it dies",
    )

    return any(
        phrase in lower
        for phrase in english_phrases
    )


def _contains_bad_spanish_terms(answer: str) -> bool:

    lower = answer.lower()

    return any(
        term in lower
        for term in _BAD_SPANISH_TERMS
    )


def _contains_mixed_english_terms(answer: str) -> bool:

    lower = answer.lower()

    return any(
        term in lower
        for term in _MIXED_ENGLISH_TERMS
    )


def _mentions_unavailable_named_example(answer: str, knowledge: str) -> bool:
    """
    Heurística genérica: si no hay cartas en el contexto y la respuesta introduce
    un ejemplo con un nombre propio compuesto, probablemente está inventando una
    carta o entidad. No contiene nombres de cartas concretas.
    """

    lower = answer.lower()

    if "ejemplo" not in lower and "example" not in lower:

        return False

    if _extract_card_names(knowledge):

        return False

    proper_name = re.search(
        r"\b[A-Z][a-zA-Z'’]+(?:,?\s+[A-Z][a-zA-Z'’]+)+\b",
        answer,
    )

    if not proper_name:

        return False

    name = proper_name.group(0)

    ignored = {
        "Magic The",
        "Magic: The",
        "The Gathering",
    }

    return name not in ignored


def _extract_card_names(knowledge: str) -> list[str]:

    match = re.search(
        r"CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:

        return []

    names = []

    for block in match.group(1).split("\n\n"):

        line = block.strip().splitlines()[0] if block.strip() else ""

        if line:

            names.append(line.strip())

    return names

def _is_rule_lookup(knowledge: str) -> bool:

    question = _extract_question(knowledge).lower()

    return (
        "qué dice la regla" in question
        or "que dice la regla" in question
        or "what does rule" in question
    )

def _contradicts_recovered_symbols(answer: str, knowledge: str) -> bool:

    lower = answer.lower()

    if (
        "{C}" in knowledge
        and "one colorless mana" in knowledge
    ):

        bad_patterns = [
            "maná blanco",
            "mana blanco",
            "maná colorido",
            "mana colorido",
            "manás coloridos",
            "manas coloridas",
            "maná de color",
            "mana de color",
            "colored mana",
            "colourless color",
        ]

        return any(
            pattern in lower
            for pattern in bad_patterns
        )

    return False

def _mentions_zone_not_in_sources(answer: str, knowledge: str) -> bool:

    answer_lower = answer.lower()
    knowledge_lower = knowledge.lower()

    zones = [
        ("cementerio", "graveyard"),
        ("exilio", "exile"),
        ("mano", "hand"),
        ("biblioteca", "library"),
    ]

    for spanish, english in zones:

        if spanish in answer_lower and english not in knowledge_lower and spanish not in knowledge_lower:

            return True

    return False

def _contradicts_triggered_ability(answer: str, knowledge: str) -> bool:

    lower = answer.lower()

    if "triggered ability" not in knowledge.lower():

        return False

    bad_patterns = [
        "habilidad activada",
        "activated ability",
    ]

    return any(
        pattern in lower
        for pattern in bad_patterns
    )

def _mentions_triggered_without_source(answer: str, knowledge: str) -> bool:

    lower = answer.lower()
    source = knowledge.lower()

    mentions_triggered = (
        "habilidad disparada" in lower
        or "habilidad desencadenada" in lower
        or "se dispara" in lower
        or "triggered ability" in lower
    )

    if not mentions_triggered:

        return False

    if "triggered ability" in source:

        return False

    if re.search(
        r"\b(when|whenever|at)\b",
        knowledge,
        flags=re.IGNORECASE,
    ):

        return False

    return True

def _is_rule_only_context(knowledge: str) -> bool:

    return (
        "RULES" in knowledge
        and "CARDS" not in knowledge
    )

def _mentions_extra_target_categories(answer: str, knowledge: str) -> bool:

    source = knowledge.lower()
    lower = answer.lower()

    if "any target" not in source:

        return False

    bad_patterns = [
        "otra carta",
        "carta en el campo de batalla",
        "carta en campo de batalla",
        "objeto en el campo de batalla",
        "otro objeto",
        "otros objetos",
        " o objeto",
        " u objeto",
        "jugador o objeto",
        "criatura, jugador o objeto",
        "no requiere target",
        "no requiere objetivo",
        "no requiere target específico",
        "no requiere objetivo específico",
        "puede atacar",
        "puede atacar a",
        "ataca a una criatura",
        "atacar a una criatura",
    ]

    return any(
        pattern in lower
        for pattern in bad_patterns
    )

def _mentions_immediate_resolution_without_support(answer: str, knowledge: str) -> bool:

    lower = answer.lower()
    source = knowledge.lower()

    mentions = [
        "resuelve inmediatamente",
        "se resuelve inmediatamente",
        "efecto inmediato",
    ]

    if not any(pattern in lower for pattern in mentions):

        return False

    support = [
        "resolves",
        "resolution",
        "resolving",
    ]

    return not any(
        item in source
        for item in support
    )

def _has_card_and_rule_support(knowledge: str) -> bool:

    return (
        "CARDS" in knowledge
        and "RULES" in knowledge
    )

def _mentions_dies_in_graveyard(answer: str) -> bool:

    lower = answer.lower()

    bad_patterns = [
        "muere en el cementerio",
        "morir en el cementerio",
        "dies in the graveyard",
    ]

    return any(
        pattern in lower
        for pattern in bad_patterns
    )

def _has_card_support(knowledge: str) -> bool:

    return "CARDS" in knowledge

def _mentions_response_during_resolution(answer: str, knowledge: str) -> bool:

    lower = answer.lower()

    bad_patterns = [
        "durante la resolución del hechizo original",
        "durante la resolución",
        "durante su resolución",
        "during the resolution",
        "during its resolution",
    ]

    if not any(pattern in lower for pattern in bad_patterns):

        return False

    return (
        "117.7" in knowledge
        or "117.4" in knowledge
        or "608.1" in knowledge
    )

def _incorrectly_denies_response_before_resolution(
    answer: str,
    knowledge: str,
) -> bool:

    lower = answer.lower()

    asks_response_context = (
        "117.7" in knowledge
        and (
            "117.4" in knowledge
            or "608.1" in knowledge
            or "117.3c" in knowledge
        )
    )

    if not asks_response_context:

        return False

    bad_patterns = [
        "no, tu oponente no puede responder",
        "no puede responder antes de que se resuelva",
        "opponent cannot respond before",
    ]

    return any(
        pattern in lower
        for pattern in bad_patterns
    )

def _fails_to_answer_copied_ability_source_removal(
    answer: str,
    knowledge: str,
) -> bool:
    question = _normalize_for_contract(_extract_question(knowledge))

    mentions_copy = any(
        marker in question
        for marker in [
            "copiar la habilidad",
            "copio la habilidad",
            "copia la habilidad",
            "copia de la habilidad",
            "habilidad copiada",
            "copy the ability",
            "copy of the ability",
            "copied ability",
        ]
    )
    mentions_original = any(
        marker in question
        for marker in [
            "habilidad original",
            "la original",
            "suya propia",
            "las dos",
            "ambas",
            "original ability",
        ]
    )
    source_leaves = any(
        marker in question
        for marker in [
            "sacrific",
            "destruy",
            "muere",
            "exili",
            "deja el campo",
            "ya no esta",
            "no estar",
            "retir",
            "elimin",
        ]
    )

    if not (mentions_copy and mentions_original and source_leaves):
        return False

    lower = _normalize_for_contract(answer)
    addresses_original = any(
        marker in lower
        for marker in [
            "habilidad original se resuelve",
            "original se resuelve",
            "original permanece",
            "original no desaparece",
            "las dos se resuelven",
            "ambas se resuelven",
        ]
    )
    addresses_source = any(
        marker in lower
        for marker in [
            "independientemente de su fuente",
            "retirar su fuente no",
            "eliminar su fuente no",
            "sacrificar su fuente no",
            "aunque la fuente ya no",
            "aunque ya no este",
            "no se contrarresta",
            "no desaparece",
        ]
    )

    return not (addresses_original and addresses_source)


def _normalize_for_contract(text: str) -> str:
    text = text.lower()
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
    return re.sub(r"\s+", " ", text).strip()


def _is_hard_violation(violation: str) -> bool:

    lower = violation.lower()

    hard_markers = [
        "contradicts",
        "game zone",
        "without recovered support",
        "invented",
        "target categories",
        "responds during resolution",
        "opponent can respond before resolution",
        "dies in the graveyard",
        "incomplete",
        "bad spanish mtg wording",
        "unasked self-sacrifice edge case",
    ]

    return any(
        marker in lower
        for marker in hard_markers
    )

def _contradicts_sacrifice_trigger_oracle(
    answer: str,
    knowledge: str,
) -> bool:

    source = knowledge.lower()
    lower = answer.lower()

    if "whenever you sacrifice a permanent" not in source:

        return False

    direct_bad_patterns = [
        "no se activa",
        "no activa",
        "no se dispara",
        "no dispara",
        "no desencadena",
        "no se desencadena",
        "no obtiene beneficio",
        "no obtiene ningún beneficio",
        "no obtiene ningun beneficio",
        "no obtiene ningún efecto",
        "no obtiene ningun efecto",
        "no hay otros efectos",
        "no hay otro efecto",
        "no afecta este proceso",
        "no afecta al proceso",
        "acción es independiente de otros efectos",
        "accion es independiente de otros efectos",
        "sacrificar otro tipo de permanente no desencadena",
        "sacrificar otro tipo de permanente no activa",
        "sacrificar otro tipo de permanente no dispara",
        "sacrificar un permanente no desencadena",
        "sacrificar un permanente no activa",
        "sacrificar un permanente no dispara",
        "solo el permanente muere",
    ]

    if any(pattern in lower for pattern in direct_bad_patterns):

        return True

    if "food" in lower and (
        "requiere sacrificar" in lower
        or "requiere que sacrifiques" in lower
        or "requires sacrificing" in lower
        or "requires sacrifice" in lower
    ):

        return True

    if "korvold no" in lower and (
        "activa" in lower
        or "dispara" in lower
        or "desencadena" in lower
        or "afecta" in lower
        or "obtiene" in lower
    ):

        return True

    return False

def _adds_unasked_self_sacrifice_edge_case(
    answer: str,
    knowledge: str,
) -> bool:

    question = _extract_question(knowledge).lower()
    lower = answer.lower()

    if (
        "mismo" in question
        or "sí mismo" in question
        or "si mismo" in question
        or "itself" in question
        or "la propia" in question
        or "el propio" in question
        or "sacrifico a" in question
        or "sacrificar a" in question
    ):

        return False

    if "sacrif" not in question:

        return False

    if "sacrif" not in lower:

        return False

    card_names = _extract_card_names_from_knowledge(
        knowledge
    )

    for card_name in card_names:

        names_to_check = _card_reference_variants(
            card_name
        )

        for name in names_to_check:

            escaped = re.escape(
                name.lower()
            )

            bad_patterns = [
                rf"si el permanente sacrificado es {escaped}",
                rf"si la criatura sacrificada es {escaped}",
                rf"si sacrificas a {escaped}",
                rf"si se sacrifica {escaped}",
                rf"sacrificar a {escaped}",
                rf"{escaped} mismo",
                rf"{escaped} se sacrifica",
            ]

            if any(
                re.search(pattern, lower)
                for pattern in bad_patterns
            ):

                return True

    generic_bad_patterns = [
        "incluido el propio",
        "incluida la propia",
        "incluido él mismo",
        "incluido el mismo",
        "incluyéndose a sí mismo",
        "incluyendose a si mismo",
        "aún así activa su efecto",
        "aun así activa su efecto",
        "pero aún así activa",
        "pero aun así activa",
    ]

    return any(
        pattern in lower
        for pattern in generic_bad_patterns
    )

def _extract_card_names_from_knowledge(
    knowledge: str,
) -> list[str]:

    cards_block = _extract_cards_block(
        knowledge
    )

    if not cards_block:

        return []

    names = []

    lines = cards_block.splitlines()

    for index, line in enumerate(lines):

        clean = line.strip()

        if not clean:

            continue

        if index + 1 >= len(lines):

            continue

        next_line = lines[index + 1].strip()

        if next_line.startswith("Mana Cost:"):

            if clean not in names:

                names.append(clean)

    return names


def _card_reference_variants(
    name: str,
) -> list[str]:

    variants = [
        name,
    ]

    if "," in name:

        short = name.split(",", 1)[0].strip()

        if short:

            variants.append(short)

    first_word = name.split()[0].strip(
        " ,.:;!?\"“”‘’"
    )

    if first_word:

        variants.append(first_word)

    unique = []

    for variant in variants:

        if variant and variant not in unique:

            unique.append(variant)

    return unique