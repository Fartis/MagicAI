QUALITY_CASES = [
    {
        "id": "RG-001",
        "name": "Undying + sacrifice",
        "tags": ["undying", "sacrifice", "dies"],
        "steps": [
            {
                "question": "Si sacrifico Young Wolf teniendo Undying, ¿qué ocurre?",
                "required_all": [
                    "sacrificar",
                    "cementerio",
                    "+1/+1",
                ],
                "required_any": [
                    ["Undying"],
                    ["muere", "morir", "muerte", "dies"],
                    ["vuelve", "regresa", "retorna"],
                    ["campo de batalla", "campo"],
                ],
                "forbidden": [
                    "Food",
                    "forage",
                    "no se activa",
                    "no se dispara",
                    "no vuelve",
                ],
            }
        ],
    },
    {
        "id": "RG-002",
        "name": "Persist + dies",
        "tags": ["persist", "dies", "counters"],
        "steps": [
            {
                "question": "¿Qué ocurre si Safehold Elite muere con Persist?",
                "required_all": [
                    "Persist",
                    "-1/-1",
                    "campo de batalla",
                ],
                "required_any": [
                    ["muere", "dies"],
                    ["vuelve", "regresa"],
                ],
                "forbidden": [
                    "+1/+1",
                    "Undying",
                    "no vuelve",
                ],
            }
        ],
    },
    {
        "id": "RG-003",
        "name": "Sacrifice is not destroy",
        "tags": ["sacrifice", "destroy"],
        "steps": [
            {
                "question": "¿Sacrificar una criatura cuenta como destruirla?",
                "required_all": [
                    "sacrificar",
                ],
                "required_any": [
                    ["destruir", "destruye", "destrucción"],
                    ["no"],
                    ["no cuenta", "no es lo mismo", "no la destruye"],
                ],
                "forbidden": [
                    "sí cuenta como destruir",
                    "se destruye al sacrificar",
                ],
            }
        ],
    },
    {
        "id": "RG-004",
        "name": "Sacrifice counts as dies",
        "tags": ["sacrifice", "dies"],
        "steps": [
            {
                "question": "Si sacrifico una criatura, ¿cuenta como que muere?",
                "required_all": [
                    "sacrificar",
                    "cementerio",
                    "campo de batalla",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["muere", "dies"],
                ],
                "forbidden": [
                    "no cuenta como morir",
                    "no muere",
                ],
            }
        ],
    },
    {
        "id": "RG-005",
        "name": "Exile does not trigger Undying",
        "tags": ["undying", "exile"],
        "steps": [
            {
                "question": "Si exilio Young Wolf, ¿vuelve por Undying?",
                "required_all": [
                    "exilio",
                    "Undying",
                ],
                "required_any": [
                    ["no"],
                    ["no se activa", "no se dispara", "no se desencadena"],
                    ["no muere", "no va al cementerio", "no al cementerio"],
                ],
                "forbidden": [
                    "vuelve al campo de batalla con un contador +1/+1",
                    "sí vuelve",
                ],
            }
        ],
    },
    {
        "id": "RG-006",
        "name": "Sacrifice as cost vs death trigger",
        "tags": ["costs", "stack", "dies", "triggered"],
        "steps": [
            {
                "question": "Si sacrifico Young Wolf como coste para lanzar Village Rites, ¿su habilidad de morir se resuelve antes que el hechizo?",
                "required_all": [
                    "pila",
                ],
                "required_any": [
                    ["coste", "costo"],
                    ["habilidad disparada", "habilidad desencadenada", "se dispara"],
                    ["encima", "por encima", "antes que Village Rites", "antes que el hechizo"],
                    ["prioridad"],
                ],
                "forbidden": [
                    "la habilidad de Undying es parte del coste",
                    "la habilidad de Undying es parte del costo",
                    "porque es parte del coste",
                    "porque es parte del costo",
                    "la habilidad se resuelve durante el lanzamiento",
                    "Undying se resuelve durante el lanzamiento",
                    "se resuelve al momento de sacrificar",
                    "se resuelve inmediatamente al sacrificar",
                    "no se dispara",
                    "la pila entera se resuelve",
                ],
            }
        ],
    },
    {
        "id": "RG-007",
        "name": "No priority during resolution",
        "tags": ["priority", "resolution"],
        "steps": [
            {
                "question": "Si una habilidad está resolviéndose y pone una carta en mesa, ¿puedo activar esa carta antes de que termine de resolver la habilidad?",
                "required_all": [
                    "prioridad",
                    "resolviendo",
                ],
                "required_any": [
                    ["no"],
                    ["durante la resolución", "mientras se resuelve"],
                ],
                "forbidden": [
                    "sí puedes activarla antes de que termine",
                    "puedes responder durante la resolución",
                ],
            }
        ],
    },
    {
        "id": "RG-008",
        "name": "Stack does not resolve all at once",
        "tags": ["stack", "priority"],
        "steps": [
            {
                "question": "Si hay dos hechizos en la pila, ¿la pila entera se resuelve de golpe?",
                "required_all": [
                    "pila",
                ],
                "required_any": [
                    ["no"],
                    ["uno", "uno a uno", "objeto"],
                ],
                "recommended_any": [
                    ["prioridad"],
                    ["entre", "después"],
                ],
                "forbidden": [
                    "se resuelve entera",
                    "todo se resuelve de golpe",
                ],
            }
        ],
    },
    {
        "id": "RG-009",
        "name": "Opponent can respond before resolution",
        "tags": ["stack", "priority", "response"],
        "steps": [
            {
                "question": "Si lanzo un hechizo, ¿mi oponente puede responder antes de que se resuelva?",
                "required_all": [
                    "prioridad",
                    "antes",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["responder", "respuesta"],
                ],
                "forbidden": [
                    "durante la resolución",
                    "después de que se resuelva",
                    "no puede responder",
                ],
            }
        ],
    },
    {
        "id": "RG-010",
        "name": "Priority between stack objects",
        "tags": ["stack", "priority"],
        "steps": [
            {
                "question": "Después de que se resuelve un hechizo de la pila, ¿puedo responder antes de que se resuelva el siguiente?",
                "required_all": [
                    "prioridad",
                ],
                "required_any": [
                    ["sí"],
                    ["antes de que se resuelva el siguiente", "entre"],
                ],
                "recommended_all": [
                    "pila",
                ],
                "forbidden": [
                    "la pila continúa resolviéndose sin prioridad",
                    "no puedes responder",
                ],
            }
        ],
    },
    {
        "id": "RG-011",
        "name": "Untap step priority",
        "tags": ["turn-steps", "priority", "triggers"],
        "steps": [
            {
                "question": "Si una habilidad se dispara al comienzo del paso de enderezar, ¿se puede responder?",
                "required_all": [
                    "paso de enderezar",
                    "prioridad",
                ],
                "required_any": [
                    ["normalmente no", "no reciben prioridad", "no hay prioridad"],
                    ["pila"],
                ],
                "forbidden": [
                    "siempre se puede responder en el paso de enderezar",
                ],
            }
        ],
    },
    {
        "id": "RG-012",
        "name": "Simultaneous triggers order",
        "tags": ["triggers", "apnap"],
        "steps": [
            {
                "question": "Si varias habilidades disparadas se disparan al mismo tiempo, ¿quién decide el orden?",
                "required_all": [
                    "habilidades disparadas",
                    "pila",
                ],
                "required_any": [
                    ["APNAP", "jugador activo", "jugador no activo"],
                    ["controlador", "controladores", "controla", "controlan"],
                    ["orden"],
                ],
                "forbidden": [
                    "se resuelven todas a la vez",
                    "orden aleatorio",
                ],
            }
        ],
    },
    {
        "id": "RG-013",
        "name": "End step APNAP triggers",
        "tags": ["triggers", "end-step", "apnap"],
        "steps": [
            {
                "question": "Si dos jugadores tienen habilidades al comienzo del paso final, ¿en qué orden van a la pila?",
                "required_all": [
                    "paso final",
                    "pila",
                ],
                "required_any": [
                    ["jugador activo", "jugador no activo", "APNAP"],
                    ["orden"],
                ],
                "forbidden": [
                    "orden aleatorio",
                    "se resuelven simultáneamente",
                ],
            }
        ],
    },
    {
        "id": "RG-014",
        "name": "May trigger decision",
        "tags": ["triggers", "may"],
        "steps": [
            {
                "question": "Si una habilidad disparada dice 'puedes', ¿cuándo decido si hago el efecto?",
                "required_all": [
                    "habilidad disparada",
                ],
                "required_any": [
                    ["al resolverse", "cuando se resuelve"],
                    ["puedes", "may"],
                ],
                "forbidden": [
                    "antes de que vaya a la pila obligatoriamente",
                ],
            }
        ],
    },
    {
        "id": "RG-015",
        "name": "Cleanup hand size priority",
        "tags": ["cleanup", "priority"],
        "steps": [
            {
                "question": "Si descarto una carta por tamaño máximo de mano en el paso de limpieza, ¿hay prioridad?",
                "required_all": [
                    "paso de limpieza",
                    "prioridad",
                ],
                "required_any": [
                    ["no", "normalmente no", "no reciben prioridad"],
                ],
                "recommended_any": [
                    ["normalmente no", "no reciben prioridad"],
                    ["si se disparan habilidades", "acciones basadas en estado"],
                ],
                "forbidden": [
                    "siempre hay prioridad",
                ],
            }
        ],
    },
    {
        "id": "RG-016",
        "name": "Commander death trigger and command zone",
        "tags": ["commander", "dies", "zone"],
        "steps": [
            {
                "question": "Si mi comandante muere, ¿puedo mandarlo a la zona de mando y aun así disparar habilidades de 'cuando muera'?",
                "required_all": [
                    "comandante",
                    "zona de mando",
                ],
                "required_any": [
                    ["muere", "dies"],
                    ["cementerio"],
                    ["sí", "puedes"],
                ],
                "forbidden": [
                    "no se dispara porque va a la zona de mando",
                    "no se dispara",
                    "no se activan",
                    "no se activa",
                    "no lo considera muerto",
                    "no se considera que muera",
                    "no se considera que \"muera\"",
                ],
            }
        ],
    },
    {
        "id": "RG-017",
        "name": "Commander hand/library replacement",
        "tags": ["commander", "replacement", "zones"],
        "steps": [
            {
                "question": "Si mi comandante fuera a mi mano o biblioteca, ¿la zona de mando funciona igual que cuando muere?",
                "required_all": [
                    "comandante",
                    "mano",
                    "biblioteca",
                    "zona de mando",
                ],
                "required_any": [
                    ["no exactamente", "no igual", "diferente", "en cambio"],
                    ["reemplazo", "replacement"],
                ],
                "forbidden": [
                    "funciona exactamente igual",
                ],
            }
        ],
    },
    {
        "id": "RG-018",
        "name": "Elenda death trigger command zone",
        "tags": ["commander", "dies", "death-trigger"],
        "steps": [
            {
                "question": "Si Elenda, the Dusk Rose muere y la mando a la zona de mando, ¿se dispara su habilidad?",
                "required_all": [
                    "Elenda",
                    "zona de mando",
                ],
                "required_any": [
                    ["muere", "dies"],
                    ["se dispara", "habilidad disparada", "habilidad desencadenada"],
                    ["sí"],
                ],
                "forbidden": [
                    "no se dispara",
                    "no se activa",
                    "no se desencadena",
                    "por lo tanto, su habilidad no",
                ],
            }
        ],
    },
    {
        "id": "RG-019",
        "name": "Commander graveyard then command zone",
        "tags": ["commander", "dies", "zone"],
        "steps": [
            {
                "question": "Si un comandante va al cementerio y luego lo muevo a la zona de mando, ¿sigue habiendo muerto?",
                "required_all": [
                    "comandante",
                    "cementerio",
                    "zona de mando",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["muere", "dies"],
                ],
                "forbidden": [
                    "no murió",
                    "nunca estuvo en el cementerio",
                    "no se considera que haya muerto",
                    "no se considera que muera",
                ],
            }
        ],
    },
    {
        "id": "RG-020",
        "name": "Commander copy and command zone",
        "tags": ["commander", "copy", "zone"],
        "steps": [
            {
                "question": "Si una copia de mi comandante muere, ¿puedo mover esa copia a la zona de mando?",
                "required_all": [
                    "copia",
                    "comandante",
                    "zona de mando",
                ],
                "required_any": [
                    ["no"],
                ],
                "recommended_any": [
                    ["carta", "no es la carta", "no es una carta"],
                ],
                "forbidden": [
                    "sí puedes mover la copia",
                    "no existe una regla que permita mover una criatura a la zona de mando",
                ],
            }
        ],
    },
    {
        "id": "RG-021",
        "name": "Multiple replacement effects counters",
        "tags": ["replacement", "counters"],
        "steps": [
            {
                "question": "Si controlo Doubling Season y Vorinclex, Monstrous Raider, ¿cómo se aplican los efectos que doblan contadores?",
                "required_all": [
                    "contadores",
                ],
                "required_any": [
                    ["efectos de reemplazo", "replacement"],
                    ["orden"],
                    ["jugador afectado", "controlador", "elige"],
                ],
                "forbidden": [
                    "son habilidades disparadas",
                    "van a la pila",
                ],
            }
        ],
    },
    {
        "id": "RG-022",
        "name": "Permanent enters with counters replacement",
        "tags": ["replacement", "counters"],
        "steps": [
            {
                "question": "Si un permanente entra con contadores y hay varios efectos que modifican esos contadores, ¿se suman o se reemplazan?",
                "required_all": [
                    "contadores",
                    "entra",
                ],
                "required_any": [
                    ["efectos de reemplazo", "replacement"],
                    ["aplican", "orden"],
                ],
                "forbidden": [
                    "se disparan al entrar",
                    "van a la pila",
                ],
            }
        ],
    },
    {
        "id": "RG-023",
        "name": "0/0 with counter and Persist",
        "tags": ["persist", "state-based-actions", "counters"],
        "steps": [
            {
                "question": "Si una criatura 0/0 entra con un contador +1/+1 y tiene Persist, ¿qué pasa cuando muere?",
                "required_all": [
                    "Persist",
                    "-1/-1",
                ],
                "required_any": [
                    ["muere", "dies"],
                    ["vuelve", "regresa"],
                    ["acciones basadas en estado", "state-based"],
                ],
                "forbidden": [
                    "vuelve con +1/+1 por Persist",
                ],
            }
        ],
    },
    {
        "id": "RG-024",
        "name": "Persist and Undying together",
        "tags": ["persist", "undying", "triggers", "counters"],
        "steps": [
            {
                "question": "Si una criatura tiene Persist y Undying a la vez y muere sin contadores, ¿puede volver infinitamente?",
                "required_all": [
                    "Persist",
                    "Undying",
                    "pila",
                ],
                "required_any": [
                    ["ambas", "dos habilidades"],
                    ["contador +1/+1", "+1/+1"],
                    ["contador -1/-1", "-1/-1"],
                ],
                "forbidden": [
                    "vuelve infinitamente automáticamente",
                    "no se dispara ninguna",
                ],
            }
        ],
    },
    {
        "id": "RG-025",
        "name": "Layer 7b before 7c",
        "tags": ["layers", "power-toughness"],
        "steps": [
            {
                "question": "Si una criatura tiene un efecto que fija su fuerza y resistencia y otro que le da +1/+1, ¿qué se aplica antes?",
                "required_all": [
                    "7b",
                    "7c",
                    "+1/+1",
                ],
                "required_any": [
                    ["fija", "establece"],
                    ["antes"],
                ],
                "forbidden": [
                    "se aplica primero el +1/+1",
                ],
            }
        ],
    },
    {
        "id": "RG-026",
        "name": "Ward is triggered ability",
        "tags": ["ward", "triggered"],
        "steps": [
            {
                "question": "¿Ward es un coste adicional o una habilidad disparada?",
                "required_all": [
                    "Ward",
                ],
                "required_any": [
                    ["habilidad disparada", "habilidad desencadenada", "se dispara"],
                ],
                "recommended_any": [
                    ["pila"],
                    ["no es un coste adicional", "no es un costo adicional"],
                ],
                "forbidden": [
                    "Ward es un coste adicional",
                    "Ward es un costo adicional",
                    "Ward es una habilidad activada",
                    "es una habilidad activada",
                ],
            }
        ],
    },
    {
        "id": "RG-027",
        "name": "Respond to Ward trigger",
        "tags": ["ward", "stack", "priority"],
        "steps": [
            {
                "question": "Si una criatura con Ward es objetivo de un hechizo, ¿puedo responder al trigger de Ward?",
                "required_all": [
                    "Ward",
                    "pila",
                ],
                "required_any": [
                    ["sí", "si"],
                    ["responder", "prioridad"],
                    ["habilidad disparada", "trigger"],
                ],
                "forbidden": [
                    "no se puede responder porque es un coste",
                ],
            }
        ],
    },
    {
        "id": "RG-028",
        "name": "Mana ability does not use stack",
        "tags": ["mana-ability", "stack", "sol-ring"],
        "steps": [
            {
                "question": "¿Puedo responder a la habilidad de Sol Ring?",
                "required_all": [
                    "Sol Ring",
                    "habilidad de maná",
                    "pila",
                ],
                "required_any": [
                    ["no"],
                    ["no usa la pila", "no va a la pila"],
                ],
                "forbidden": [
                    "sí puedes responder a la habilidad de maná",
                    "habilidad disparada",
                ],
            }
        ],
    },
    {
        "id": "RG-029",
        "name": "Killing source does not counter activated ability",
        "tags": ["activated-ability", "stack", "source"],
        "steps": [
            {
                "question": "Si una criatura activa una habilidad y luego mato esa criatura, ¿se contrarresta la habilidad?",
                "required_all": [
                    "habilidad",
                    "pila",
                    "fuente",
                ],
                "required_any": [
                    ["no"],
                    ["no se contrarresta", "sigue resolviéndose"],
                ],
                "forbidden": [
                    "se contrarresta automáticamente",
                    "desaparece de la pila",
                ],
            }
        ],
    },
    {
        "id": "RG-030",
        "name": "Activated vs triggered abilities",
        "tags": ["activated", "triggered"],
        "steps": [
            {
                "question": "¿Una habilidad activada y una habilidad disparada son lo mismo?",
                "required_all": [
                    "habilidad activada",
                    "habilidad disparada",
                ],
                "required_any": [
                    ["no"],
                    ["coste", ":"],
                    ["cuando", "whenever", "when", "at"],
                ],
                "forbidden": [
                    "son lo mismo",
                ],
            }
        ],
    },
]
