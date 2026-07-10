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