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

    if _contains_any(
        q,
        [
            "coste",
            "costo",
            "como coste",
            "como costo",
        ],
    ):

        add(
            "601",
            "117",
            "603",
            "405",
            "701.21",
            "700.4",
        )

    if _contains_any(q, ["sacrificar", "sacrificio", "sacrifice"]):

        add(
            "701.21",
            "700.4",
        )

    if _contains_any(q, ["exilio", "exiliar", "exiliado", "exiliada", "exile"]):

        add(
            "701.11",
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

    if _contains_any(
        q,
        [
            "zona de mando",
            "command zone",
            "comandante",
            "commander",
        ],
    ):

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

    if _contains_any(
        q,
        [
            "efecto de reemplazo",
            "efectos de reemplazo",
            "replacement effect",
            "replacement effects",
            "reemplazo",
            "doubling season",
            "vorinclex",
        ],
    ):

        add(
            "614.1c",
            "616.1",
            "616.1f",
            "122.6",
        )

    if (
        _contains_any(q, ["entra", "entrar", "enters"])
        and _contains_any(q, ["contador", "contadores", "counter", "counters"])
        and _contains_any(
            q,
            [
                "varios efectos",
                "dos efectos",
                "efectos que",
                "modifican",
                "se suman",
                "se reemplazan",
            ],
        )
    ):

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

    if _contains_any(
        q,
        [
            "coste",
            "costo",
            "como coste",
            "como costo",
        ],
    ):

        queries.extend(
            [
                "triggered abilities can trigger while a spell is being cast put on stack next time a player would receive priority",
                "if multiple abilities have triggered since last time a player received priority placed on the stack",
                "total cost includes mana payment activate mana abilities costs are paid",
            ]
        )

    if _contains_any(
        q,
        [
            "zona de mando",
            "command zone",
            "comandante",
            "commander",
        ],
    ):

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

    if _contains_any(
        q,
        [
            "efecto de reemplazo",
            "efectos de reemplazo",
            "replacement effect",
            "replacement effects",
            "doubling season",
            "vorinclex",
        ],
    ) or (
        _contains_any(q, ["entra", "entrar", "enters"])
        and _contains_any(q, ["contador", "contadores", "counter", "counters"])
        and _contains_any(q, ["varios efectos", "efectos que", "modifican", "se suman", "se reemplazan"])
    ):

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
                    "701.11a to exile an object move it to the exile zone",
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