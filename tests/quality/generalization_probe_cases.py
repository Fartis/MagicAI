GENERALIZATION_CASES = [
    {
        "id": "GQ-001",
        "name": "Mana ability with Arcane Signet",
        "tags": ["mana-ability", "stack", "generalization"],
        "steps": [
            {
                "question": "¿La habilidad de maná de Arcane Signet usa la pila o se puede responder?",
                "required_all": [
                    "habilidad de maná",
                    "pila",
                ],
                "required_any": [
                    [
                        "no usa la pila",
                        "no va a la pila",
                        "no se coloca en la pila",
                        "sin pasar por la pila",
                    ],
                    ["no se puede responder", "no puedes responder", "no"],
                ],
                "recommended_any": [
                    ["Arcane Signet", "esa habilidad"],
                    ["se resuelve inmediatamente", "resuelve inmediatamente"],
                ],
                "forbidden": [
                    "sí puedes responder",
                    "si puedes responder",
                    "sí usa la pila",
                    "si usa la pila",
                    "se coloca en la pila y permite respuestas",
                ],
            }
        ],
    },
    {
        "id": "GQ-002",
        "name": "Mana ability with mana creature",
        "tags": ["mana-ability", "stack", "generalization"],
        "steps": [
            {
                "question": "Cuando giro Llanowar Elves para añadir maná, ¿mi rival puede responder a esa habilidad?",
                "required_all": [
                    "habilidad de maná",
                    "pila",
                ],
                "required_any": [
                    [
                        "no usa la pila",
                        "no va a la pila",
                        "no se coloca en la pila",
                        "sin pasar por la pila",
                    ],
                    ["no", "no puede responder", "no puedes responder"],
                ],
                "recommended_any": [
                    ["Llanowar Elves", "esa habilidad"],
                    ["añadir maná", "agregar maná"],
                ],
                "forbidden": [
                    "sí puede responder",
                    "si puede responder",
                    "sí puedes responder",
                    "si puedes responder",
                ],
            }
        ],
    },
    {
        "id": "GQ-003",
        "name": "No priority during resolution paraphrase",
        "tags": ["priority", "resolution", "generalization"],
        "steps": [
            {
                "question": "Durante la resolución de una habilidad que crea una ficha, ¿puedo usar esa ficha antes de que termine de resolverse?",
                "required_all": [
                    "prioridad",
                    "resolución",
                ],
                "required_any": [
                    ["no"],
                    ["durante la resolución", "mientras se resuelve", "antes de que termine"],
                ],
                "forbidden": [
                    "sí puedes usarla antes de que termine",
                    "si puedes usarla antes de que termine",
                    "puedes responder durante la resolución",
                ],
            }
        ],
    },
    {
        "id": "GQ-004",
        "name": "Stack resolves one object at a time paraphrase",
        "tags": ["stack", "priority", "generalization"],
        "steps": [
            {
                "question": "Si hay dos objetos esperando en la pila, ¿se resuelven todos automáticamente sin dar prioridad entre medias?",
                "required_all": [
                    "pila",
                    "prioridad",
                ],
                "required_any": [
                    ["no"],
                    ["uno a uno", "uno", "objeto"],
                    ["entre", "después", "luego"],
                ],
                "forbidden": [
                    "se resuelven todos automáticamente",
                    "se resuelve toda de golpe",
                    "sin dar prioridad",
                ],
            }
        ],
    },
    {
        "id": "GQ-005",
        "name": "APNAP paraphrase",
        "tags": ["apnap", "triggered", "stack", "generalization"],
        "steps": [
            {
                "question": "Mis habilidades disparadas y las de mi oponente se disparan al mismo tiempo. ¿Cómo se ordenan?",
                "required_all": [
                    "habilidades disparadas",
                    "pila",
                ],
                "required_any": [
                    ["APNAP", "jugador activo", "jugador no activo"],
                    ["orden", "ordena", "ponen"],
                    ["controla", "controlador", "controladores"],
                ],
                "forbidden": [
                    "orden aleatorio",
                    "se resuelven simultáneamente",
                ],
            }
        ],
    },
    {
        "id": "GQ-006",
        "name": "Ward trigger paraphrase",
        "tags": ["ward", "triggered", "stack", "generalization"],
        "steps": [
            {
                "question": "Una criatura con Ward es objetivo de un removal. ¿Puedo responder a esa habilidad de Ward?",
                "required_all": [
                    "Ward",
                    "pila",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["habilidad disparada", "habilidad desencadenada", "trigger"],
                    ["responder", "prioridad"],
                ],
                "forbidden": [
                    "no se puede responder porque es un coste",
                    "Ward es un coste adicional",
                    "Ward es un costo adicional",
                ],
            }
        ],
    },
    {
        "id": "GQ-007",
        "name": "Killing source paraphrase",
        "tags": ["activated-ability", "source", "stack", "generalization"],
        "steps": [
            {
                "question": "Si activo una habilidad de una criatura y después destruyen esa criatura, ¿la habilidad desaparece de la pila?",
                "required_all": [
                    "habilidad",
                    "pila",
                ],
                "required_any": [
                    ["no"],
                    ["no se contrarresta", "sigue resolviéndose", "permanece en la pila"],
                    ["fuente", "origen"],
                ],
                "forbidden": [
                    "desaparece de la pila",
                    "se contrarresta automáticamente",
                    "matar la fuente contrarresta",
                ],
            }
        ],
    },
    {
        "id": "GQ-008",
        "name": "Activated vs triggered paraphrase",
        "tags": ["activated", "triggered", "generalization"],
        "steps": [
            {
                "question": "¿Cómo distingo una habilidad activada de una habilidad disparada?",
                "required_all": [
                    "habilidad activada",
                    "habilidad disparada",
                ],
                "required_any": [
                    ["coste", "costo", ":"],
                    ["cuando", "whenever", "when", "at", "siempre que", "al comienzo"],
                ],
                "forbidden": [
                    "son lo mismo",
                    "no hay diferencia",
                ],
            }
        ],
    },
    {
        "id": "GQ-009",
        "name": "Commander destroyed then command zone",
        "tags": ["commander", "dies", "zone", "generalization"],
        "steps": [
            {
                "question": "Mi comandante es destruido, pasa por el cementerio y después lo pongo en la zona de mando. ¿Las habilidades de cuando muera se disparan?",
                "required_all": [
                    "comandante",
                    "cementerio",
                    "zona de mando",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["muere", "cuando muera"],
                    ["acciones basadas en estado", "state-based"],
                ],
                "forbidden": [
                    "no se dispara",
                    "no se considera que muera",
                    "nunca estuvo en el cementerio",
                ],
            }
        ],
    },
    {
        "id": "GQ-010",
        "name": "Commander library replacement paraphrase",
        "tags": ["commander", "library", "replacement", "generalization"],
        "steps": [
            {
                "question": "Si un efecto fuera a poner mi comandante en la biblioteca, ¿puedo enviarlo a la zona de mando en vez de dejar que llegue allí?",
                "required_all": [
                    "comandante",
                    "biblioteca",
                    "zona de mando",
                ],
                "required_any": [
                    ["efecto de reemplazo", "reemplazo"],
                    ["en su lugar", "no llega"],
                ],
                "forbidden": [
                    "primero llega a la biblioteca",
                    "solo puede hacerse después",
                ],
            }
        ],
    },
    {
        "id": "GQ-011",
        "name": "Copying a commander does not copy designation",
        "tags": ["commander", "copy", "zone", "generalization"],
        "steps": [
            {
                "question": "Una criatura copia al comandante de otro jugador y luego muere. ¿Esa copia puede ir a la zona de mando?",
                "required_all": [
                    "copia",
                    "comandante",
                    "zona de mando",
                ],
                "required_any": [
                    ["no"],
                    ["carta", "designación"],
                ],
                "forbidden": [
                    "sí puede ir a la zona de mando",
                    "la copia también es comandante",
                ],
            }
        ],
    },
    {
        "id": "GQ-012",
        "name": "Cleanup priority exception paraphrase",
        "tags": ["cleanup", "priority", "generalization"],
        "steps": [
            {
                "question": "En el paso de limpieza, después de descartar hasta mi tamaño máximo de mano, ¿los jugadores reciben prioridad normalmente?",
                "required_all": [
                    "paso de limpieza",
                    "prioridad",
                ],
                "required_any": [
                    ["normalmente no", "ningún jugador recibe prioridad"],
                    ["acciones basadas en estado", "habilidades disparadas"],
                ],
                "forbidden": [
                    "siempre reciben prioridad",
                    "el jugador activo recibe prioridad automáticamente",
                ],
            }
        ],
    },
    {
        "id": "GQ-013",
        "name": "Generic multiple counter replacement effects",
        "tags": ["replacement", "counters", "generalization"],
        "steps": [
            {
                "question": "Dos efectos de reemplazo quieren cambiar cuántos contadores recibe el mismo permanente. ¿Quién decide el orden?",
                "required_all": [
                    "efectos de reemplazo",
                    "contadores",
                    "orden",
                ],
                "required_any": [
                    ["controlador", "jugador afectado"],
                    ["elige", "decide"],
                    ["se aplica uno", "aplicar uno", "sucesivamente"],
                ],
                "forbidden": [
                    "son habilidades disparadas",
                    "van a la pila",
                ],
            }
        ],
    },
    {
        "id": "GQ-014",
        "name": "Counters modified as permanent enters",
        "tags": ["replacement", "enters", "counters", "generalization"],
        "steps": [
            {
                "question": "Un permanente va a entrar con contadores y dos efectos cambian esa cantidad. ¿Se disparan o modifican la entrada?",
                "required_all": [
                    "entra",
                    "contadores",
                    "efectos de reemplazo",
                ],
                "required_any": [
                    ["no se disparan", "no van a la pila"],
                    ["modifican", "evento de entrada"],
                    ["orden", "controlador"],
                ],
                "forbidden": [
                    "se disparan al entrar",
                    "son habilidades disparadas",
                ],
            }
        ],
    },
    {
        "id": "GQ-015",
        "name": "Persist and Undying stack ordering paraphrase",
        "tags": ["persist", "undying", "stack", "generalization"],
        "steps": [
            {
                "question": "Una criatura sin contadores tiene Persist y Undying y muere. ¿Las dos la devuelven a la vez?",
                "required_all": [
                    "Persist",
                    "Undying",
                    "pila",
                ],
                "required_any": [
                    ["dos habilidades", "ambas"],
                    ["orden", "elige"],
                    ["+1/+1"],
                    ["-1/-1"],
                ],
                "forbidden": [
                    "las dos la devuelven a la vez",
                    "vuelve infinitamente de forma automática",
                ],
            }
        ],
    },
    {
        "id": "GQ-016",
        "name": "Zero toughness Persist state-based action paraphrase",
        "tags": ["persist", "state-based-actions", "generalization"],
        "steps": [
            {
                "question": "Una criatura base 0/0 con Persist vuelve del cementerio con su contador. ¿Qué comprueba el juego después?",
                "required_all": [
                    "Persist",
                    "-1/-1",
                ],
                "required_any": [
                    ["acciones basadas en estado", "state-based"],
                    ["resistencia", "toughness"],
                    ["0 o menos", "-1", "cementerio"],
                ],
                "forbidden": [
                    "sobrevive automáticamente",
                    "vuelve con +1/+1 por Persist",
                    "fuerza 0 o menos",
                    "su fuerza es -1, lo que la hace morir",
                ],
            }
        ],
    },

    {
        "id": "GQ-017",
        "name": "Undying does not return an exiled creature",
        "tags": ["undying", "exile", "generalization"],
        "steps": [
            {
                "question": "Una criatura con Undying es exiliada directamente desde el campo de batalla. ¿La habilidad la devuelve?",
                "required_all": [
                    "Undying",
                    "exilio",
                    "cementerio",
                ],
                "required_any": [
                    ["no se dispara", "no se activa", "no se desencadena"],
                    ["no muere", "no va al cementerio"],
                    ["no vuelve", "no regresa", "no la devuelve"],
                ],
                "forbidden": [
                    "vuelve al campo de batalla con un contador +1/+1",
                    "Undying se dispara al ser exiliada",
                ],
            }
        ],
    },

    {
        "id": "GQ-018",
        "name": "Bello loses abilities through two different land auras",
        "tags": ["layers", "continuous-effects", "dependency", "generalization"],
        "steps": [
            {
                "question": (
                    "Tengo en mesa a Bello, Bard of the Brambles como mi "
                    "comandante. Es mi turno y controlo un encantamiento de "
                    "coste 4 sin habilidades de criatura, por lo que Bello lo "
                    "convierte en una criatura Elemental 4/4 con indestructible "
                    "y prisa. Un oponente encanta a Bello con Imprisoned in the "
                    "Moon o con Song of the Dryads. ¿El encantamiento sigue "
                    "siendo una criatura 4/4 que puede atacar o vuelve a ser un "
                    "encantamiento normal?"
                ),
                "required_all": [
                    "Imprisoned",
                    "Song",
                    "4/4",
                ],
                "required_any": [
                    ["sigue siendo", "permanece", "continúa siendo"],
                    ["vuelve a ser", "deja de ser", "ya no es criatura"],
                    ["capa", "capas", "efecto continuo", "dependencia"],
                ],
                "forbidden": [
                    "habilidades desencadenadas por cambios de zona",
                    "ambas auras producen exactamente el mismo resultado",
                    "ambos efectos producen el mismo resultado",
                    "en los dos casos vuelve a ser un encantamiento normal",
                    "Imprisoned en la Luna y Song of the Dryads convierten a Bello en una tierra",
                ],
            }
        ],
    },


]
