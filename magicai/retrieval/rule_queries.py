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
            "sol ring",
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
                "commander graveyard exile owner may put it into command zone state-based action",
                "commander hand library owner may put it into command zone replacement effect",
                "commander dies graveyard command zone",
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
    ):

        queries.extend(
            [
                "replacement effects affected player or controller of affected permanent chooses order",
                "two or more replacement effects are attempting to modify event affected player chooses one",
                "replacement effects modifying how a permanent enters the battlefield counters",
            ]
        )

    if _contains_any(
        q,
        [
            "fuente",
            "mato",
            "matar",
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