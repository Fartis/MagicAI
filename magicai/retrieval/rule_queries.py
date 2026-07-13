import re


LEXICAL_BRIDGE = {
    "capa": [
        "layers",
        "series of layers",
        "continuous effects",
        "interaction of continuous effects",
    ],
    "capas": [
        "layers",
        "series of layers",
        "continuous effects",
        "interaction of continuous effects",
    ],
    "efecto continuo": [
        "continuous effect",
        "continuous effects",
    ],
    "efectos continuos": [
        "continuous effects",
    ],

    "prioridad": [
        "timing and priority",
        "priority",
        "cast spells activate abilities special actions",
    ],
    "responder": [
        "in response",
        "priority",
        "stack",
        "resolves",
    ],
    "respuesta": [
        "in response",
        "priority",
        "stack",
        "resolves",
    ],
    "antes de que se resuelva": [
        "in response",
        "priority",
        "stack",
        "resolves",
    ],

    "fuerza y resistencia": [
        "power toughness",
        "base power toughness",
        "set power toughness",
        "set power and/or toughness",
        "specific number or value",
        "modify power toughness",
        "modify power and/or toughness",
    ],
    "fuerza": [
        "power",
    ],
    "resistencia": [
        "toughness",
    ],
    "fija": [
        "set",
        "base",
        "specific number or value",
    ],
    "fijar": [
        "set",
        "base",
        "specific number or value",
    ],
    "establece": [
        "set",
        "specific number or value",
    ],
    "modifica": [
        "modify",
    ],
    "modificar": [
        "modify",
    ],
    "+1/+1": [
        "+1/+1",
        "counter",
        "counters",
        "modify power and/or toughness",
    ],

    "contador": [
        "counter",
    ],
    "contadores": [
        "counters",
    ],
    "cementerio": [
        "graveyard",
    ],
    "campo de batalla": [
        "battlefield",
    ],
    "exilio": [
        "exile",
    ],
    "exiliar": [
        "exile",
    ],
    "muere": [
        "dies",
        "graveyard",
        "battlefield",
    ],
    "morir": [
        "dies",
        "graveyard",
        "battlefield",
    ],
    "lanzar": [
        "cast",
        "spell",
        "priority",
    ],
    "lanzo": [
        "cast",
        "spell",
        "priority",
    ],
    "hechizo": [
        "spell",
    ],
    "mulligan": [
        "mulligan",
        "starting hand size",
    ],
}


LEXICAL_BRIDGE.update(
    {
        "pila": [
            "stack",
            "priority",
            "resolves",
        ],
        "resuelve de golpe": [
            "stack",
            "priority",
            "top object resolves",
        ],
        "resuelve entera": [
            "stack",
            "priority",
            "top object resolves",
        ],
        "resuelve el siguiente": [
            "stack",
            "priority",
            "after a spell or ability resolves",
        ],
        "resolviendo": [
            "resolving spells and abilities",
            "no player has priority",
        ],
        "resolviéndose": [
            "resolving spells and abilities",
            "no player has priority",
        ],
        "resolviendose": [
            "resolving spells and abilities",
            "no player has priority",
        ],
        "resolverse": [
            "resolving spells and abilities",
            "priority",
        ],
        "resolución": [
            "resolving spells and abilities",
            "priority",
        ],
        "resolucion": [
            "resolving spells and abilities",
            "priority",
        ],
        "activar": [
            "activate abilities",
            "priority",
        ],
        "habilidad disparada": [
            "triggered ability",
            "triggered abilities",
        ],
        "habilidades disparadas": [
            "triggered abilities",
            "APNAP",
            "stack",
        ],
        "habilidad desencadenada": [
            "triggered ability",
        ],
        "se dispara": [
            "triggered ability",
            "triggered abilities",
        ],
        "habilidad activada": [
            "activated ability",
        ],
        "habilidades activadas": [
            "activated abilities",
        ],
        "habilidad de maná": [
            "mana ability",
            "mana abilities",
            "do not use the stack",
        ],
        "habilidad de mana": [
            "mana ability",
            "mana abilities",
            "do not use the stack",
        ],
        "añadir maná": [
            "mana ability",
            "mana abilities",
            "add mana",
            "do not use the stack",
        ],
        "anadir mana": [
            "mana ability",
            "mana abilities",
            "add mana",
            "do not use the stack",
        ],
        "agregar maná": [
            "mana ability",
            "mana abilities",
            "add mana",
            "do not use the stack",
        ],
        "agregar mana": [
            "mana ability",
            "mana abilities",
            "add mana",
            "do not use the stack",
        ],
        "paso de enderezar": [
            "untap step",
            "no player receives priority",
        ],
        "paso final": [
            "end step",
            "triggered abilities",
            "APNAP",
        ],
        "paso de limpieza": [
            "cleanup step",
            "no player receives priority",
        ],
        "tamaño máximo de mano": [
            "maximum hand size",
            "cleanup step",
        ],
        "jugador activo": [
            "active player",
            "APNAP",
        ],
        "jugador no activo": [
            "nonactive player",
            "APNAP",
        ],
        "apnap": [
            "APNAP",
            "active player",
            "nonactive player",
        ],
        "puedes": [
            "may",
            "triggered ability",
            "resolution",
        ],
        "zona de mando": [
            "command zone",
            "commander",
        ],
        "comandante": [
            "commander",
            "command zone",
        ],
        "mano": [
            "hand",
        ],
        "biblioteca": [
            "library",
        ],
        "efecto de reemplazo": [
            "replacement effect",
        ],
        "efectos de reemplazo": [
            "replacement effects",
        ],
        "reemplazo": [
            "replacement effect",
        ],
        "fuente": [
            "source",
            "activated ability",
        ],
        "mato": [
            "source",
            "activated ability",
        ],
        "destruir": [
            "destroy",
            "destroy a permanent",
        ],
        "destruye": [
            "destroy",
            "destroy a permanent",
        ],
        "destrucción": [
            "destruction",
            "destroy",
        ],
        "destruccion": [
            "destruction",
            "destroy",
        ],
        "ward": [
            "ward",
            "triggered ability",
        ],
    }
)


def build_rule_queries(
    question: str,
    keywords: list[str] | None = None,
    action_terms: list[str] | None = None,
) -> list[str]:
    """
    Construye búsquedas textuales para Comprehensive Rules.

    No devuelve números de regla.
    No sabe respuestas.
    Solo transforma lenguaje de usuario en términos útiles para buscar.
    """

    queries = []

    translated_terms = _translate_question_terms(question)

    for query in _rule_number_queries(question):

        _add_unique(
            queries,
            query,
        )

    for query in _specialized_queries(question):

        _add_unique(
            queries,
            query,
        )

    if translated_terms:

        _add_unique(
            queries,
            " ".join(translated_terms),
        )

        for term in translated_terms:

            _add_unique(
                queries,
                term,
            )

    for keyword in keywords or []:

        _add_unique(
            queries,
            keyword,
        )

    for query in _action_queries(action_terms or []):

        _add_unique(
            queries,
            query,
        )

    return _remove_noisy_action_queries(
        queries,
        action_terms or [],
    )



def _rule_number_queries(question: str) -> list[str]:

    q = _normalize_question(
        question
    )

    queries = []

    def add(*numbers: str):
        for number in numbers:
            _add_unique(
                queries,
                number,
            )

    if _is_copied_ability_source_removed_question(q):
        # Highest-priority evidence for copied abilities whose source leaves
        # the battlefield while the original ability remains on the stack.
        add(
            "707.10",
            "113.7a",
            "608.2d",
            "405.5",
            "117.3b",
        )

    # Las interacciones que cambian tipos, habilidades o fuerza/resistencia
    # necesitan capas antes que reglas incidentales de lanzamiento o Commander.
    if _is_characteristic_continuous_effect_question(q):

        add(
            "611.3",
            "613.1d",
            "613.1f",
            "613.4b",
            "613.6",
            "613.8",
        )

        if _mentions_basic_land_type_interaction(q):
            add("305.7")

    if _mentions_mana_value(q):
        add("202.3")

    if _contains_any(
        q,
        [
            "prioridad",
            "priority",
        ],
    ):

        add(
            "117",
        )

    if _contains_any(
        q,
        [
            "responder",
            "respuesta",
            "antes de que se resuelva",
            "antes de resolverse",
            "in response",
        ],
    ):

        add(
            "117",
            "405",
        )

    if _contains_any(
        q,
        [
            "pila",
            "stack",
            "resuelve de golpe",
            "resuelve entera",
            "resuelva el siguiente",
            "resuelve el siguiente",
        ],
    ):

        add(
            "405",
            "608",
            "117",
        )

    if _contains_any(
        q,
        [
            "resolviendo",
            "resolviendose",
            "resolverse",
            "resolucion",
            "termine de resolver",
        ],
    ):

        add(
            "117",
            "608",
        )

    if _contains_any(
        q,
        [
            "paso de enderezar",
            "untap step",
        ],
    ):

        add(
            "502",
            "117",
            "603",
        )

    if _contains_any(
        q,
        [
            "paso final",
            "end step",
        ],
    ):

        add(
            "513",
            "405",
            "603",
            "101",
        )

    if _contains_any(
        q,
        [
            "habilidades disparadas",
            "habilidad disparada",
            "habilidad desencadenada",
            "triggered ability",
            "triggered abilities",
            "se dispara",
            "al mismo tiempo",
            "apnap",
            "jugador activo",
            "jugador no activo",
        ],
    ):

        add(
            "603",
            "405",
        )

    if _contains_any(
        q,
        [
            "puedes",
            "may",
        ],
    ) and _contains_any(
        q,
        [
            "habilidad disparada",
            "habilidad desencadenada",
            "triggered ability",
        ],
    ):

        add(
            "603",
            "608",
        )

    if _contains_any(
        q,
        [
            "paso de limpieza",
            "limpieza",
            "cleanup step",
            "tamano maximo de mano",
            "tamaño máximo de mano",
        ],
    ):

        add(
            "514",
            "117",
        )

    if _contains_any(
        q,
        [
            "habilidad de mana",
            "habilidad de maná",
            "mana ability",
            "añadir maná",
            "añadir mana",
            "anadir mana",
            "agregar maná",
            "agregar mana",
        ],
    ):

        add(
            "605",
            "405",
            "117",
        )

    if _is_sacrifice_as_cost_death_trigger_question(q):

        add(
            "601",
            "117",
            "603",
            "405",
            "701.21",
            "700.4",
        )

    elif _is_casting_cost_question(q):

        add(
            "601",
            "117",
        )

    if _contains_any(q, ["sacrificar", "sacrificio", "sacrifice"]):

        add(
            "701.21",
            "700.4",
        )

    if _contains_any(q, ["exilio", "exiliar", "exiliado", "exiliada", "exile"]):

        add(
            "701.13",
        )

        if "undying" in q:
            add(
                "702.93",
                "700.4",
            )

    if (
        _contains_any(q, ["sacrificar", "sacrificio", "sacrifice"])
        and _contains_any(q, ["destruir", "destruye", "destruccion", "destroy"])
    ):

        queries.extend(
            [
                "sacrificing a permanent doesn't destroy it",
                "regeneration or replacement effects that replace destruction can't affect sacrifice",
                "to sacrifice a permanent controller moves it directly from battlefield to graveyard",
            ]
        )

    if _contains_any(
        q,
        [
            "ward",
        ],
    ):

        add(
            "702.21",
            "603",
            "405",
        )

    if _is_commander_rules_question(q):

        add(
            "903.3",
            "903.9a",
            "903.9b",
            "700.4",
            "704",
            "614",
        )

    if (
        _contains_any(
            q,
            [
                "sacrificar",
                "sacrificio",
                "sacrifice",
            ],
        )
        and _contains_any(
            q,
            [
                "destruir",
                "destruye",
                "destruccion",
                "destroy",
            ],
        )
    ):

        add(
            "701.8",
            "701.21",
        )

    if _is_counter_replacement_interaction(q):

        add(
            "614.1c",
            "616.1",
            "616.1f",
            "122.6",
        )

    if "persist" in q and "undying" in q:

        add(
            "702.79",
            "702.93",
            "603",
            "405",
            "400.7",
            "700.4",
        )

    if (
        "persist" in q
        and _contains_any(q, ["0/0", "cero cero"])
    ):

        add(
            "702.79",
            "704.5f",
            "704.5q",
            "122.3",
            "603",
            "405",
            "700.4",
        )

    if "persist" in q:

        add(
            "702.79",
            "603",
            "405",
            "704",
            "122",
            "700.4",
        )

    if "undying" in q:

        add(
            "702.93",
            "603",
            "405",
            "704",
            "122",
            "700.4",
        )

    if _contains_any(
        q,
        [
            "habilidad activada",
            "habilidades activadas",
            "activated ability",
            "activo una habilidad",
            "activa una habilidad",
            "activar una habilidad",
            "fuente",
            "origen",
            "mato",
            "matar",
            "destruyen esa criatura",
            "destruir esa criatura",
            "desaparece de la pila",
            "contrarresta la habilidad",
        ],
    ):

        add(
            "602",
            "113",
            "405",
        )

    return queries


def _normalize_question(text: str) -> str:

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

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

def _specialized_queries(question: str) -> list[str]:

    q = question.lower()

    queries = []

    if _is_copied_ability_source_removed_question(_normalize_question(q)):
        queries.extend(
            [
                "707.10 copy activated or triggered ability choices made on resolution are not copied",
                "113.7a ability on stack exists independently of its source",
                "608.2d choices made while resolving a spell or ability",
                "405.5 top object on stack resolves first",
                "117.3b active player receives priority after an ability resolves",
            ]
        )

    if _is_characteristic_continuous_effect_question(q):

        queries.extend(
            [
                "continuous effects interaction of continuous effects layers",
                "type-changing effects layer 4",
                "ability-adding and ability-removing effects layer 6",
                "set power and toughness specific number layer 7b",
                "effect starts applying in one layer continues in later layers even if ability is removed",
                "dependency system continuous effects same layer",
            ]
        )

        if _mentions_basic_land_type_interaction(q):
            queries.append(
                "basic land type loses abilities generated from rules text 305.7"
            )

    if _contains_any(
        q,
        [
            "capa",
            "capas",
            "layers",
        ],
    ):

        queries.extend(
            [
                "layers continuous effects",
                "series of layers continuous effects",
                "interaction of continuous effects layers",
            ]
        )

    if _contains_any(
        q,
        [
            "prioridad",
            "priority",
        ],
    ):

        queries.extend(
            [
                "timing and priority",
                "priority cast spells activate abilities special actions",
                "active player receives priority after a spell or ability resolves",
                "no player has priority while a spell or ability is resolving",
            ]
        )

    if _contains_any(
        q,
        [
            "responder",
            "respuesta",
            "antes de que se resuelva",
            "in response",
        ],
    ):

        queries.extend(
            [
                "in response priority stack resolves",
                "casts a spell priority in response resolves first",
                "active player receives priority after a spell or ability resolves",
            ]
        )

    if (
        _contains_any(
            q,
            [
                "fuerza",
                "power",
            ],
        )
        and _contains_any(
            q,
            [
                "resistencia",
                "toughness",
            ],
        )
    ):

        queries.extend(
            [
                "set power and/or toughness specific number or value",
                "base power and/or toughness",
                "modify power and/or toughness counters",
            ]
        )

    if "+1/+1" in q:

        queries.extend(
            [
                "+1/+1 counters modify power and/or toughness",
                "counters modify power and/or toughness",
            ]
        )

    if _contains_any(
        q,
        [
            "pila",
            "stack",
            "resuelve de golpe",
            "resuelve entera",
            "resuelva el siguiente",
            "resuelve el siguiente",
        ],
    ):

        queries.extend(
            [
                "stack top object resolves all players pass priority",
                "active player receives priority after a spell or ability resolves",
                "top object on the stack resolves priority",
            ]
        )

    if _contains_any(
        q,
        [
            "resolviendo",
            "resolviéndose",
            "resolviendose",
            "resolverse",
            "resolución",
            "resolucion",
        ],
    ):

        queries.extend(
            [
                "no player has priority while a spell or ability is resolving",
                "no other spells can normally be cast and no other abilities can normally be activated during resolution",
                "resolving spells and abilities no player has priority",
            ]
        )

    if _contains_any(
        q,
        [
            "paso de enderezar",
            "untap step",
        ],
    ):

        queries.extend(
            [
                "no player receives priority during the untap step",
                "untap step triggered ability held until next time a player would receive priority",
            ]
        )

    if _contains_any(
        q,
        [
            "paso final",
            "end step",
        ],
    ):

        queries.extend(
            [
                "beginning of the end step triggered abilities active player nonactive player APNAP stack",
                "multiple triggered abilities active player nonactive player APNAP stack",
            ]
        )

    if _contains_any(
        q,
        [
            "al mismo tiempo",
            "simult",
            "apnap",
            "jugador activo",
            "jugador no activo",
        ],
    ):

        queries.extend(
            [
                "multiple triggered abilities active player nonactive player APNAP stack",
                "triggered abilities controlled active player nonactive player order stack",
            ]
        )

    if (
        _contains_any(q, ["puedes", "may"])
        and _contains_any(q, ["habilidad disparada", "habilidad desencadenada", "triggered ability"])
    ):

        queries.extend(
            [
                "triggered ability may choice made on resolution",
                "may triggered ability resolves controller chooses",
            ]
        )

    if _contains_any(
        q,
        [
            "paso de limpieza",
            "limpieza",
            "cleanup step",
            "tamaño máximo de mano",
        ],
    ):

        queries.extend(
            [
                "cleanup step normally no player receives priority maximum hand size",
                "cleanup step triggered abilities active player gets priority",
            ]
        )

    if _contains_any(
        q,
        [
            "habilidad de maná",
            "habilidad de mana",
            "mana ability",
            "añadir maná",
            "anadir mana",
            "agregar maná",
            "agregar mana",
        ],
    ):

        queries.extend(
            [
                "mana abilities do not use the stack",
                "mana abilities resolve immediately",
                "activated mana ability could add mana no target not loyalty ability",
            ]
        )

    if _contains_any(
        q,
        [
            "ward",
        ],
    ):

        queries.extend(
            [
                "ward triggered ability counter unless pays",
                "ward ability triggers becomes target opponent spell or ability",
            ]
        )

    if _is_sacrifice_as_cost_death_trigger_question(q):

        queries.extend(
            [
                "triggered abilities trigger during casting wait until a player would receive priority",
                "triggered ability put on stack after spell becomes cast",
                "sacrifice as additional cost dies trigger above spell on stack",
            ]
        )

    elif _is_casting_cost_question(q):

        queries.extend(
            [
                "total cost includes mana cost alternative costs additional costs cost increases and cost reductions",
                "casting a spell determine total cost then pay costs",
            ]
        )

    elif _mentions_mana_value(q):

        queries.extend(
            [
                "mana value derived from mana cost",
            ]
        )

    if _is_commander_rules_question(q):

        queries.extend(
            [
                "commander card retains designation when it changes zones copy of commander is not a commander",
                "commander graveyard exile owner may put it into command zone state-based action",
                "commander hand library owner may put it into command zone instead replacement effect",
                "dies means put into a graveyard from the battlefield commander",
            ]
        )

        if _contains_any(q, ["copia", "copy"]):
            queries.extend(
                [
                    "permanent copying a commander is not a commander",
                    "commander designation is an attribute of the card itself not copiable",
                ]
            )

        if _contains_any(q, ["mano", "biblioteca", "hand", "library"]):
            queries.extend(
                [
                    "903.9b commander hand library command zone instead replacement effect",
                ]
            )

        if _contains_any(q, ["muere", "muerto", "cementerio", "dies", "graveyard"]):
            queries.extend(
                [
                    "903.9a commander graveyard command zone state-based action",
                    "700.4 dies graveyard from battlefield",
                ]
            )

    if _is_counter_replacement_interaction(q):

        queries.extend(
            [
                "616.1 affected object's controller or affected player chooses one replacement effect to apply",
                "616.1f repeat replacement effect process until none apply",
                "614.1c enters with counters replacement effect",
                "122.6 counters put on object as it enters battlefield",
            ]
        )

    if "persist" in q:
        queries.extend(
            [
                "702.79a persist triggered ability no -1/-1 counters return battlefield with -1/-1 counter",
                "704.5f creature toughness zero or less put into graveyard state-based action",
                "704.5q +1/+1 and -1/-1 counters removed state-based action",
            ]
        )

    if "undying" in q:
        queries.extend(
            [
                "702.93a undying triggered ability no +1/+1 counters return battlefield with +1/+1 counter",
            ]
        )

        if _contains_any(q, ["exilio", "exiliar", "exiliado", "exiliada", "exile"]):
            queries.extend(
                [
                    "701.13a to exile an object move it to the exile zone",
                    "700.4 dies means put into a graveyard from the battlefield",
                    "undying does not trigger when a permanent is exiled instead of dying",
                ]
            )

    if "persist" in q and "undying" in q:
        queries.extend(
            [
                "multiple triggered abilities controlled by same player choose order on stack",
                "400.7 object that moves zones becomes a new object",
                "triggered ability returning card from graveyard second ability cannot find card",
            ]
        )

    if _contains_any(
        q,
        [
            "fuente",
            "origen",
            "mato",
            "matar",
            "destruyen esa criatura",
            "destruir esa criatura",
            "desaparece de la pila",
            "contrarresta la habilidad",
        ],
    ):

        queries.extend(
            [
                "activated ability on the stack exists independently of its source",
                "removing source of activated ability from battlefield does not counter ability",
            ]
        )

    if (
        _contains_any(q, ["habilidad activada", "activated ability"])
        and _contains_any(q, ["habilidad disparada", "habilidad desencadenada", "triggered ability"])
    ):

        queries.extend(
            [
                "activated ability written cost colon effect",
                "triggered ability begins with when whenever at",
            ]
        )

    return queries


def _translate_question_terms(question: str) -> list[str]:

    lower = question.lower()

    terms = []

    for source, targets in LEXICAL_BRIDGE.items():

        if source in {"comandante", "commander"} and not _is_commander_rules_question(lower):
            continue

        if source in lower:

            for target in targets:

                _add_unique(
                    terms,
                    target,
                )

    if not _looks_spanish(lower):

        for token in _english_tokens(lower):

            _add_unique(
                terms,
                token,
            )

    return terms


def _english_tokens(text: str) -> list[str]:

    tokens = re.findall(
        r"[a-z][a-z0-9/+_-]{2,}",
        text,
    )

    stopwords = {
        "the",
        "and",
        "you",
        "what",
        "how",
        "does",
        "with",
        "from",
        "that",
        "this",
    }

    return [
        token
        for token in tokens
        if token not in stopwords
    ]


def _is_characteristic_continuous_effect_question(question: str) -> bool:

    markers = [
        "efecto continuo",
        "efectos continuos",
        "capa",
        "capas",
        "convierte en",
        "lo convierte en",
        "la convierte en",
        "se convierte en",
        "sigue siendo",
        "deja de ser",
        "vuelve a ser",
        "pierde todas las habilidades",
        "pierde habilidades",
        "gana habilidades",
        "otros tipos",
        "type-changing",
        "ability-removing",
        "loses all abilities",
        "in addition to its other types",
    ]

    if _contains_any(question, markers):
        return True

    # A bare printed power/toughness such as ``0/0`` is not enough to infer
    # a layers question. It is also common in state-based-action, combat and
    # counter interactions. Only treat P/T as a continuous-effect signal when
    # the wording also describes an effect changing or setting characteristics.
    has_power_toughness = re.search(r"\b\d+/\d+\b", question) is not None
    has_characteristic_change = _contains_any(
        question,
        [
            "fija",
            "fijar",
            "establece",
            "se vuelve",
            "pasa a ser",
            "gana",
            "pierde",
            "base power",
            "base toughness",
            "set power",
            "set toughness",
            "becomes",
            "gets",
        ],
    )

    return has_power_toughness and has_characteristic_change


def _mentions_basic_land_type_interaction(question: str) -> bool:

    return _contains_any(
        question,
        [
            "basic land type",
            "tipo de tierra básica",
            "tipo de tierra basica",
            "plains",
            "island",
            "swamp",
            "mountain",
            "forest",
            "llanura",
            "isla",
            "pantano",
            "montaña",
            "montana",
            "bosque",
            "song of the dryads",
        ],
    )


def _mentions_mana_value(question: str) -> bool:

    if _contains_any(
        question,
        [
            "valor de maná",
            "valor de mana",
            "mana value",
            "converted mana cost",
            "coste de maná convertido",
            "coste de mana convertido",
        ],
    ):
        return True

    return bool(
        re.search(
            r"\b(?:coste|costo)\s+(?:de\s+)?\d+\b",
            question,
        )
    )


def _is_copied_ability_source_removed_question(question: str) -> bool:
    mentions_copy = _contains_any(
        question,
        [
            "copiar la habilidad",
            "copio la habilidad",
            "copia la habilidad",
            "copia de la habilidad",
            "habilidad copiada",
            "copy the ability",
            "copy of the ability",
            "copied ability",
        ],
    )

    mentions_original = _contains_any(
        question,
        [
            "habilidad original",
            "la original",
            "original se resuelve",
            "original resuelve",
            "suya propia",
            "las dos",
            "ambas",
            "original ability",
        ],
    )

    source_leaves = _contains_any(
        question,
        [
            "sacrific",
            "destruy",
            "muere",
            "exili",
            "deja el campo",
            "ya no esta",
            "no estar",
            "retir",
            "elimin",
        ],
    )

    asks_resolution = _contains_any(
        question,
        [
            "se resuelve",
            "resuelve normalmente",
            "sigue resolviendo",
            "se resuelven",
            "resolveria",
            "resolvera",
            "resolve",
        ],
    )

    return mentions_copy and mentions_original and source_leaves and asks_resolution


def _is_sacrifice_as_cost_death_trigger_question(question: str) -> bool:

    return (
        "sacrific" in question
        and _contains_any(
            question,
            [
                "como coste",
                "como costo",
                "as a cost",
                "additional cost",
            ],
        )
        and _contains_any(
            question,
            [
                "habilidad de morir",
                "habilidad disparada",
                "habilidad desencadenada",
                "se dispara",
                "dies trigger",
                "death trigger",
                "undying",
                "persist",
            ],
        )
    )


def _is_casting_cost_question(question: str) -> bool:

    cost_markers = [
        "coste",
        "costo",
        "cost",
    ]

    if not _contains_any(question, cost_markers):
        return False

    casting_cost_markers = [
        "pagar",
        "pago",
        "pagando",
        "sin pagar",
        "coste adicional",
        "costo adicional",
        "coste alternativo",
        "costo alternativo",
        "reducir el coste",
        "reducir el costo",
        "aumentar el coste",
        "aumentar el costo",
        "cuesta lanzar",
        "cuesta jugar",
        "total cost",
        "additional cost",
        "alternative cost",
        "cost reduction",
        "cost increase",
    ]

    return _contains_any(question, casting_cost_markers)


def _is_commander_rules_question(question: str) -> bool:

    mentions_command_zone = _contains_any(
        question,
        [
            "zona de mando",
            "command zone",
        ],
    )

    if not (
        mentions_command_zone
        or _contains_any(question, ["comandante", "commander"])
    ):
        return False

    return _contains_any(
        question,
        [
            "zona de mando",
            "command zone",
            "muere",
            "dies",
            "cementerio",
            "graveyard",
            "exilio",
            "exile",
            "mano",
            "hand",
            "biblioteca",
            "library",
            "daño de comandante",
            "commander damage",
            "identidad de color",
            "color identity",
            "copia de mi comandante",
            "copy of my commander",
            "designación",
            "designation",
        ],
    )


def _is_counter_replacement_interaction(question: str) -> bool:

    mentions_counters = _contains_any(
        question,
        [
            "contador",
            "contadores",
            "counter",
            "counters",
        ],
    )

    if not mentions_counters:

        return False

    explicitly_mentions_replacement = _contains_any(
        question,
        [
            "efecto de reemplazo",
            "efectos de reemplazo",
            "replacement effect",
            "replacement effects",
            "reemplazo",
            "doubling season",
            "vorinclex",
        ],
    )

    mentions_multiple_effects = _contains_any(
        question,
        [
            "varios efectos",
            "dos efectos",
            "ambos efectos",
            "efectos que",
            "multiple effects",
            "two effects",
        ],
    )

    asks_how_they_interact = _contains_any(
        question,
        [
            "orden",
            "elige",
            "decide",
            "como se aplican",
            "cómo se aplican",
            "se aplica",
            "se aplican",
            "modifican",
            "se suman",
            "se reemplazan",
            "doblan",
            "duplican",
            "order",
            "choose",
            "apply",
            "modify",
        ],
    )

    return explicitly_mentions_replacement or (
        mentions_multiple_effects and asks_how_they_interact
    )


def _contains_any(text: str, items: list[str]) -> bool:

    return any(
        item in text
        for item in items
    )


def _add_unique(items: list[str], item: str):

    if item and item not in items:

        items.append(item)


def _looks_spanish(text: str) -> bool:

    markers = [
        "¿",
        "qué",
        "que ",
        " si ",
        "sacrifico",
        "muere",
        "exilio",
        "lanzar",
        "campo de batalla",
        "prioridad",
        "capas",
        "explícame",
        "explicame",
        "merece la pena",
    ]

    return any(
        marker in text
        for marker in markers
    )

def _action_queries(action_terms: list[str]) -> list[str]:

    if not action_terms:

        return []

    terms = set(
        term.lower()
        for term in action_terms
    )

    queries = []

    if {
        "sacrifice",
        "permanent",
        "graveyard",
    }.issubset(terms):

        queries.extend(
            [
                "to sacrifice a permanent controller moves it from the battlefield directly to its owner's graveyard",
                "sacrifice permanent battlefield graveyard",
            ]
        )

    elif "sacrifice" in terms:

        queries.append(
            "to sacrifice a permanent"
        )

    if {
        "dies",
        "graveyard",
        "battlefield",
    }.issubset(terms):

        queries.extend(
            [
                "dies graveyard from the battlefield",
                "put into a graveyard from the battlefield",
            ]
        )

    elif "dies" in terms:

        queries.append(
            "dies graveyard from the battlefield"
        )

    if "exile zone" in terms:

        queries.append(
            "to exile an object exile zone"
        )

    elif "exile" in terms:

        queries.append(
            "to exile an object"
        )

    if "enters the battlefield" in terms:

        queries.append(
            "enters the battlefield"
        )

    if {
        "cast",
        "spell",
        "priority",
    }.issubset(terms):

        queries.extend(
            [
                "cast spell priority",
                "casts a spell receives priority afterward",
            ]
        )

    elif "cast" in terms and "spell" in terms:

        queries.append(
            "cast spell"
        )

    return queries

def _remove_noisy_action_queries(
    queries: list[str],
    action_terms: list[str],
) -> list[str]:

    if not action_terms:

        return queries

    terms = {
        term.lower()
        for term in action_terms
    }

    noisy_exact_queries = set()

    if "sacrifice" in terms:

        noisy_exact_queries.update(
            {
                "sacrifice",
                "permanent",
                "graveyard",
                "battlefield",
            }
        )

    if "dies" in terms:

        noisy_exact_queries.update(
            {
                "dies",
                "graveyard",
                "battlefield",
                "dies graveyard battlefield",
            }
        )

    if "exile" in terms or "exile zone" in terms:

        noisy_exact_queries.update(
            {
                "exile",
                "exile zone",
            }
        )

    if "cast" in terms and "spell" in terms:

        noisy_exact_queries.update(
            {
                "cast",
                "spell",
                "priority",
            }
        )

    filtered = []

    for query in queries:

        normalized = query.lower().strip()

        if normalized in noisy_exact_queries:

            continue

        if query not in filtered:

            filtered.append(
                query
            )

    return filtered