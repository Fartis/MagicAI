from magicai.validation.rule_renderer import render_rule_answer


def assert_contains(text: str, expected: list[str], label: str):
    lower = text.lower()

    missing = [
        item
        for item in expected
        if item.lower() not in lower
    ]

    if missing:
        raise AssertionError(
            f"{label}: missing {missing!r} in answer:\n{text}"
        )


def assert_not_contains(text: str, forbidden: list[str], label: str):
    lower = text.lower()

    present = [
        item
        for item in forbidden
        if item.lower() in lower
    ]

    if present:
        raise AssertionError(
            f"{label}: unexpected {present!r} in answer:\n{text}"
        )


def test_no_priority_during_resolution():
    knowledge = """
QUESTION

Si una habilidad está resolviéndose y pone una carta en mesa, ¿puedo activar esa carta antes de que termine de resolver la habilidad?

============================================================
RULES

117
Timing and Priority

117.2e
No player has priority while a spell or ability is resolving.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "resolviendo",
            "prioridad",
            "durante la resolución",
        ],
        "no priority during resolution",
    )


def test_untap_step_priority():
    knowledge = """
QUESTION

Si una habilidad se dispara al comienzo del paso de enderezar, ¿se puede responder?

============================================================
RULES

502
Untap Step

502.4
No player receives priority during the untap step. Any ability that triggers during this step will be held until the next time a player would receive priority.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "paso de enderezar",
            "prioridad",
            "no",
            "pila",
        ],
        "untap step priority",
    )


def test_apnap_triggers():
    knowledge = """
QUESTION

Si varias habilidades disparadas se disparan al mismo tiempo, ¿quién decide el orden?

============================================================
RULES

603
Handling Triggered Abilities

405
Stack

405.3
If an effect puts two or more objects on the stack at the same time, those controlled by the active player are put on lowest, followed by each other player's objects in APNAP order.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "habilidades disparadas",
            "APNAP",
            "jugador activo",
            "jugador no activo",
            "controla",
            "pila",
            "orden",
        ],
        "apnap triggers",
    )


def test_mana_ability_uses_recovered_arcane_signet_oracle():
    knowledge = """
QUESTION

¿La habilidad de maná de Arcane Signet usa la pila o se puede responder?

============================================================
CARDS

Arcane Signet
Artifact

{T}: Add one mana of any color in your commander's color identity.

============================================================
RULES

605
Mana Abilities

605.3b
An activated mana ability doesn't go on the stack, so it can't be responded to and resolves immediately.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Arcane Signet",
            "habilidad de maná",
            "pila",
            "no se puede responder",
        ],
        "mana ability Arcane Signet",
    )

    assert_not_contains(
        answer,
        ["Sol Ring"],
        "mana ability Arcane Signet",
    )


def test_mana_ability_is_inferred_from_recovered_oracle():
    knowledge = """
QUESTION

Cuando giro Llanowar Elves para añadir maná, ¿mi rival puede responder a esa habilidad?

============================================================
CARDS

Llanowar Elves
Creature — Elf Druid

{T}: Add {G}.

============================================================
RULES

605
Mana Abilities

605.3b
An activated mana ability doesn't go on the stack, so it can't be responded to and resolves immediately.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Llanowar Elves",
            "habilidad de maná",
            "añadir maná",
            "pila",
            "no se puede responder",
        ],
        "mana ability Llanowar Elves",
    )



def test_single_recovered_mana_ability_supports_generic_card_reference():
    knowledge = """
QUESTION

¿Puedo responder a la habilidad de Mind Stone?

============================================================
CARDS

Mind Stone
Artifact

{T}: Add {C}.

============================================================
RULES

605
Mana Abilities

605.3b
An activated mana ability doesn't go on the stack and resolves immediately.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Mind Stone",
            "habilidad de maná",
            "pila",
            "no se puede responder",
        ],
        "generic recovered mana ability",
    )

def test_sol_ring_mana_ability_ignores_mana_cost_metadata():
    knowledge = """
QUESTION

¿Puedo responder a la habilidad de Sol Ring?

============================================================
CARDS

Sol Ring
Mana Cost: {1}
Artifact

{T}: Add {C}{C}.

============================================================
RULES

605
Mana Abilities

605.3b
An activated mana ability doesn't go on the stack and resolves immediately.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Sol Ring",
            "habilidad de maná",
            "añadir maná",
            "pila",
            "no se puede responder",
        ],
        "Sol Ring mana ability with metadata",
    )


def test_mana_renderer_requires_recovered_rule_evidence():
    knowledge = """
QUESTION

Cuando giro Llanowar Elves para añadir maná, ¿mi rival puede responder a esa habilidad?

============================================================
CARDS

Llanowar Elves
Creature — Elf Druid

{T}: Add {G}.
"""

    answer = render_rule_answer(knowledge)

    if answer is not None:
        raise AssertionError(
            "mana renderer must not answer without recovered rule 605 evidence"
        )


def test_stack_resolves_one_object_then_returns_priority():
    knowledge = """
QUESTION

Si hay dos objetos esperando en la pila, ¿se resuelven todos automáticamente sin dar prioridad entre medias?

============================================================
RULES

405
Stack

405.5
When all players pass in succession, the top spell or ability on the stack resolves.

117
Timing and Priority

117.3b
The active player receives priority after a spell or ability resolves.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "pila",
            "uno a uno",
            "prioridad",
            "entre",
        ],
        "stack progression",
    )


def test_priority_returns_between_stack_objects():
    knowledge = """
QUESTION

Después de que se resuelve un hechizo de la pila, ¿puedo responder antes de que se resuelva el siguiente?

============================================================
RULES

405
Stack

117
Timing and Priority

117.3b
The active player receives priority after a spell or ability resolves.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Sí",
            "pila",
            "prioridad",
            "antes de que se resuelva el siguiente",
        ],
        "priority between stack objects",
    )


def test_opponent_can_respond_before_spell_resolves():
    knowledge = """
QUESTION

Si lanzo un hechizo, ¿mi oponente puede responder antes de que se resuelva?

============================================================
RULES

117
Timing and Priority

405
Stack

405.5
When all players pass in succession, the top object on the stack resolves.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Sí",
            "oponente",
            "prioridad",
            "antes",
            "se resuelva",
        ],
        "response before resolution",
    )


def test_ward_is_triggered_and_can_be_responded_to():
    knowledge = """
QUESTION

Una criatura con Ward es objetivo de un removal. ¿Puedo responder a esa habilidad de Ward?

============================================================
RULES

702.21
Ward

702.21a
Ward is a triggered ability.

603
Handling Triggered Abilities

405
Stack
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Ward",
            "habilidad disparada",
            "pila",
            "Sí",
            "responder",
        ],
        "Ward trigger",
    )



def test_copied_triggered_ability_survives_sacrificing_its_source():
    knowledge = """
QUESTION

Si tengo la posibilidad de copiar la habilidad, la copia entra después de la original en la pila y sacrifico a Braids con la copia, ¿la habilidad original se resuelve normalmente aunque Braids ya no esté?

============================================================
CARDS

Braids, Arisen Nightmare
Mana Cost: {1}{B}{B}
Legendary Creature — Nightmare

At the beginning of your end step, you may sacrifice an artifact, creature, enchantment, land, or planeswalker. If you do, each opponent may sacrifice a permanent that shares a card type with it. For each opponent who doesn't, that player loses 2 life and you draw a card.

============================================================
RULES

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

405.5
When all players pass in succession, the top (last-added) spell or ability on the stack resolves.

608.2d
If an effect offers choices not already made while putting it on the stack, the player announces these while applying the effect.

707.10
To copy an activated or triggered ability means to put a copy of it onto the stack. Choices that are normally made on resolution are not copied.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "copia",
            "se resuelve primero",
            "Braids",
            "no desaparece",
            "independientemente de su fuente",
            "original se resuelve normalmente",
            "otro permanente válido",
            "si lo haces",
        ],
        "copied triggered ability source removal",
    )
    assert_not_contains(
        answer,
        [
            "las habilidades desencadenadas se resuelven antes de la prioridad",
            "la original no se resuelve",
        ],
        "copied triggered ability source removal",
    )


def test_copied_ability_renderer_requires_source_independence_evidence():
    knowledge = """
QUESTION

Si copio una habilidad y sacrifico su fuente con la copia, ¿la original se resuelve?

============================================================
RULES

405.5
The top object on the stack resolves first.

707.10
To copy an ability means to put a copy of it onto the stack.
"""

    answer = render_rule_answer(knowledge)

    if answer is not None:
        raise AssertionError(
            "copied ability renderer must require rule 113.7a and resolution-choice evidence"
        )

def test_activated_ability_exists_independently_of_source():
    knowledge = """
QUESTION

Si activo una habilidad de una criatura y después destruyen esa criatura, ¿la habilidad desaparece de la pila?

============================================================
RULES

113
Abilities

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

405
Stack

608.2h
An effect may use last known information about a source no longer in the expected zone.

609.3
An effect attempts to do as much as possible.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "pila",
            "fuente",
            "no se contrarresta",
            "permanece",
        ],
        "ability source independence",
    )


def test_source_independence_uses_type_neutral_wording():
    knowledge = """
QUESTION

Activo una habilidad de un artefacto y después destruyen ese artefacto. ¿La habilidad desaparece de la pila?

============================================================
RULES

113
Abilities

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

405
Stack

608.2h
An effect may use last known information about a source no longer in the expected zone.

609.3
An effect attempts to do as much as possible.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["independiente de su fuente", "permanece en la pila"],
        "type-neutral source independence wording",
    )
    assert_not_contains(
        answer,
        ["criatura que la originó"],
        "type-neutral source independence wording",
    )


def test_source_independence_wins_over_resolution_wording():
    knowledge = """
QUESTION

Una habilidad activada de Marble Gargoyle ya está en la pila y destruyen la carta. ¿La habilidad sigue resolviéndose?

============================================================
RULES

113
Abilities

113.7a
Once activated or triggered, an ability exists on the stack independently of its source.

405
Stack

608.2h
An effect may use last known information about a source no longer in the expected zone.

609.3
An effect attempts to do as much as possible.

117
Timing and Priority

117.2e
No player has priority while a spell or ability is resolving.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["pila", "fuente", "no se contrarresta", "seguirá resolviéndose"],
        "source independence resolution wording",
    )
    assert_not_contains(
        answer,
        ["no tienen prioridad", "durante la resolución"],
        "source independence resolution wording",
    )



def test_activated_and_triggered_ability_taxonomy():
    knowledge = """
QUESTION

¿Cómo distingo una habilidad activada de una habilidad disparada?

============================================================
RULES

602
Activating Activated Abilities

602.1
Activated abilities have a cost and an effect. They are written as “[Cost]: [Effect.]”.

603
Handling Triggered Abilities

603.1
Triggered abilities begin with “when,” “whenever,” or “at.”
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "habilidad activada",
            "habilidad disparada",
            "coste",
            ":",
            "cuando",
        ],
        "ability taxonomy",
    )



def test_cleanup_step_normally_has_no_priority():
    knowledge = """
QUESTION

Si descarto una carta por tamaño máximo de mano en el paso de limpieza, ¿hay prioridad?

============================================================
RULES

514
Cleanup Step

514.3
Normally, no player receives priority during the cleanup step.

514.3a
If any state-based actions are performed or any triggered abilities are waiting to be put onto the stack, the active player gets priority.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Normalmente no",
            "paso de limpieza",
            "prioridad",
            "acciones basadas en estado",
            "habilidades disparadas",
        ],
        "cleanup priority",
    )


def test_sacrifice_is_not_destroy():
    knowledge = """
QUESTION

¿Sacrificar una criatura cuenta como destruirla?

============================================================
RULES

701.8
Destroy

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard. Sacrificing a permanent doesn't destroy it.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "Sacrificar",
            "no cuenta como destruir",
            "campo de batalla",
            "cementerio",
        ],
        "sacrifice is not destroy",
    )


def test_commander_dies_before_state_based_move():
    knowledge = """
QUESTION

Si mi comandante muere, ¿puedo mandarlo a la zona de mando y aun así disparar habilidades de 'cuando muera'?

============================================================
RULES

700.4
The term dies means “is put into a graveyard from the battlefield.”

903.9a
If a commander is in a graveyard or in exile and was put there since the last state-based action check, its owner may put it into the command zone.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Sí",
            "muere",
            "cementerio",
            "zona de mando",
            "cuando muera",
            "acciones basadas en estado",
        ],
        "commander death trigger",
    )


def test_commander_hand_library_is_replacement_effect():
    knowledge = """
QUESTION

Si mi comandante fuera a mi mano o biblioteca, ¿la zona de mando funciona igual que cuando muere?

============================================================
RULES

903.9a
If a commander is in a graveyard or exile, its owner may put it into the command zone as a state-based action.

903.9b
If a commander would be put into its owner's hand or library from anywhere, its owner may put it into the command zone instead. This is a replacement effect.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Sí",
            "mano",
            "biblioteca",
            "efecto de reemplazo",
            "zona de mando",
            "cementerio",
        ],
        "commander hand library replacement",
    )


def test_copy_of_commander_is_not_commander():
    knowledge = """
QUESTION

Si una copia de mi comandante muere, ¿puedo mover esa copia a la zona de mando?

============================================================
RULES

903.3
Each deck has a legendary card designated as its commander. This designation is an attribute of the card itself. A permanent copying a commander is not a commander.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "No",
            "copia",
            "comandante",
            "carta",
            "zona de mando",
            "propia designación",
            "no por la copia",
        ],
        "copy commander designation",
    )


def test_elenda_commander_death_uses_recovered_card_name():
    knowledge = """
QUESTION

Si Elenda, the Dusk Rose muere y la mando a la zona de mando, ¿se dispara su habilidad?

============================================================
CARDS

Elenda, the Dusk Rose
Mana Cost: {2}{W}{B}
Legendary Creature — Vampire Knight
When Elenda, the Dusk Rose dies, create X 1/1 white Vampire creature tokens with lifelink.

============================================================
RULES

700.4
The term dies means “is put into a graveyard from the battlefield.”

903.9a
If a commander is in a graveyard and was put there since the last state-based action check, its owner may put it into the command zone.
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "Elenda",
            "muere",
            "se disparan",
            "cementerio",
            "zona de mando",
        ],
        "Elenda commander death",
    )



def test_sacrifice_as_cost_death_trigger_is_rendered_deterministically():
    knowledge = """
QUESTION

Si sacrifico Young Wolf como coste para lanzar Village Rites, ¿su habilidad de morir se resuelve antes que el hechizo?

============================================================
RULES

601.2h
The player pays the total cost in any order.

117.3b
The active player receives priority after a spell or ability resolves.

603.3
Once an ability has triggered, its controller puts it on the stack the next time a player would receive priority.

405.1
When a spell is cast, the spell itself is put on the stack.

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard.

700.4
The term dies means “is put into a graveyard from the battlefield.”
"""

    answer = render_rule_answer(knowledge)

    assert answer

    assert_contains(
        answer,
        [
            "coste",
            "pila",
            "prioridad",
            "encima",
            "antes que el hechizo",
        ],
        "sacrifice as cost death trigger",
    )


def test_sacrifice_counts_as_dies_is_rendered_deterministically():
    knowledge = """
QUESTION

¿Sacrificar una criatura cuenta como morir para sus habilidades?

============================================================
RULES

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard.

700.4
The term dies means “is put into a graveyard from the battlefield.”
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "Sí",
            "campo de batalla",
            "cementerio",
            "muere",
            "cuando muera",
            "sin ser lo mismo que destruir",
        ],
        "sacrifice counts as dies",
    )


def test_power_toughness_set_then_modify_uses_layers_7b_and_7c():
    knowledge = """
QUESTION

Si un efecto fija la fuerza y resistencia de una criatura en 3/3 y otro le da +1/+1, ¿cuál se aplica primero?

============================================================
RULES

613.4b
Layer 7b: Effects that set power and/or toughness to a specific number or value are applied.

613.4c
Layer 7c: Effects and counters that modify power and/or toughness are applied.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "capa 7b",
            "capa 7c",
            "primero",
            "+1/+1",
            "después",
        ],
        "power toughness set then modify",
    )

def test_undying_sacrifice_is_rendered_deterministically():
    knowledge = """
QUESTION

Si sacrifico Young Wolf teniendo Undying, ¿qué ocurre?

============================================================
RULES

700.4
The term dies means “is put into a graveyard from the battlefield.”

701.21a
To sacrifice a permanent, its controller moves it from the battlefield directly to its owner's graveyard.

702.93a
Undying is a triggered ability. When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield with a +1/+1 counter on it.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["sacrificar", "cementerio", "Undying", "vuelve", "campo de batalla", "+1/+1"],
        "deterministic undying",
    )
    assert_not_contains(answer, ["no se activa"], "deterministic undying")


def test_exile_does_not_trigger_undying():
    knowledge = """
QUESTION

Si exilio Young Wolf, ¿vuelve por Undying?

============================================================
RULES

700.4
The term dies means “is put into a graveyard from the battlefield.”

701.13a
To exile an object, move it to the exile zone from wherever it is.

702.93a
Undying is a triggered ability. When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield with a +1/+1 counter on it.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["exilio", "Undying", "no se dispara", "no muere", "cementerio", "no vuelve"],
        "undying exile",
    )


def test_multiple_counter_replacement_effects_choose_order():
    knowledge = """
QUESTION

Si controlo dos efectos que doblan contadores, ¿cómo se aplican?

============================================================
RULES

122.6
Counters put on an object as it enters are counters put on that object.

614.1c
Effects that read enters with are replacement effects.

616.1
If two or more replacement effects attempt to modify an event, the affected object's controller or affected player chooses one.

616.1f
After applying one effect, repeat the process until none remain.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "efectos de reemplazo",
            "contadores",
            "precedencia",
            "616.1",
            "misma categoría",
            "controlador",
            "elige",
            "orden",
            "4N",
        ],
        "counter replacement order",
    )


def test_entering_with_counters_uses_replacement_sequence():
    knowledge = """
QUESTION

Si un permanente entra con contadores y varios efectos los modifican, ¿se suman o se reemplazan?

============================================================
RULES

122.6
Counters put on an object as it enters are counters put on that object.

614.1c
Effects that read enters with are replacement effects.

616.1
The affected object's controller chooses one replacement effect to apply.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["contadores", "entra", "efectos de reemplazo", "orden", "aplica"],
        "enter counters replacements",
    )


def test_zero_zero_persist_mentions_state_based_actions():
    knowledge = """
QUESTION

Si una criatura 0/0 entra con un contador +1/+1 y tiene Persist, ¿qué pasa cuando muere?

============================================================
RULES

122.3
+1/+1 and -1/-1 counters are removed as a state-based action.

704.5f
A creature with toughness 0 or less is put into its owner's graveyard.

702.79a
Persist returns the permanent with a -1/-1 counter if it had no -1/-1 counters.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["Persist", "muere", "vuelve", "-1/-1", "acciones basadas en estado"],
        "zero zero persist",
    )


def test_persist_and_undying_share_stack_but_only_one_returns_card():
    knowledge = """
QUESTION

Si una criatura tiene Persist y Undying a la vez y muere sin contadores, ¿puede volver infinitamente?

============================================================
RULES

405
The Stack

400.7
An object that moves from one zone to another becomes a new object.

603
Handling Triggered Abilities

702.79a
Persist returns the permanent with a -1/-1 counter.

702.93a
Undying returns the permanent with a +1/+1 counter.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        ["Persist", "Undying", "dos habilidades", "pila", "+1/+1", "-1/-1"],
        "persist undying",
    )




def test_layered_static_source_comparison_is_deterministic():
    knowledge = """
QUESTION

Tengo a Bello, Bard of the Brambles y un encantamiento de coste 4. Un oponente encanta a Bello con Imprisoned in the Moon o con Song of the Dryads. ¿El encantamiento sigue siendo una criatura 4/4 o vuelve a ser normal?

============================================================
CARDS

Bello, Bard of the Brambles
Mana Cost: {1}{R}{G}
Legendary Creature — Raccoon Bard

During your turn, each non-Equipment artifact and non-Aura enchantment you control with mana value 4 or greater is a 4/4 Elemental creature in addition to its other types and has indestructible, haste, and "Whenever this creature deals combat damage to a player, draw a card."

Imprisoned in the Moon
Mana Cost: {2}{U}
Enchantment — Aura

Enchant creature, land, or planeswalker
Enchanted permanent is a colorless land with "{T}: Add {C}" and loses all other card types and abilities.

Song of the Dryads
Mana Cost: {2}{G}
Enchantment — Aura

Enchant permanent
Enchanted permanent is a colorless Forest land.

============================================================
RULES

305.7
If an effect sets a land's subtype to one or more of the basic land types, the land loses all abilities generated from its rules text and gains the appropriate mana ability.

611.3
A continuous effect may be generated by the static ability of an object.

613.1d
Layer 4: Type-changing effects are applied.

613.1f
Layer 6: Ability-adding effects, keyword counters, ability-removing effects, and effects that say an object can't have an ability are applied.

613.4b
Layer 7b: Effects that set power and/or toughness to a specific number or value are applied.

613.6
If an effect starts to apply in one layer, it will continue to be applied to the same set of objects in each other applicable layer.

613.8
Within a layer or sublayer, determining which order effects are applied in is sometimes done using a dependency system.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "Imprisoned in the Moon",
            "Song of the Dryads",
            "resultados distintos",
            "permanece",
            "4/4",
            "capa",
            "dependencia",
            "vuelve a ser",
        ],
        "layered static source comparison",
    )
    assert_not_contains(
        answer,
        [
            "los dos casos vuelve",
            "ambos efectos producen el mismo resultado",
        ],
        "layered static source comparison",
    )


def test_direct_undying_definition_is_deterministic():
    knowledge = """
QUESTION

¿Cómo funciona Undying?

============================================================
RULES

Undying

702.93a
Undying is a triggered ability. When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "habilidad disparada",
            "muere",
            "no tenía contadores +1/+1",
            "vuelve",
            "contador +1/+1",
        ],
        "direct Undying definition",
    )


def test_keyword_difference_uses_recovered_rules():
    knowledge = """
QUESTION

¿Qué diferencias tienen?

============================================================
RULES

Undying
702.93a
Undying is a triggered ability.

Persist
702.79a
Persist is a triggered ability.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "Undying",
            "Persist",
            "+1/+1",
            "-1/-1",
            "muere",
        ],
        "keyword difference",
    )


def test_rule_followup_example_uses_active_undying_rule():
    knowledge = """
QUESTION

¿Puedes explicarla con un ejemplo?

============================================================
RULES

Undying
702.93a
Undying is a triggered ability.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "Por ejemplo",
            "muere",
            "cementerio",
            "+1/+1",
            "vuelve",
        ],
        "rule follow-up example",
    )

def test_undying_with_existing_positive_counter_is_deterministic():
    knowledge = """
QUESTION

¿Y si además tiene un contador +1/+1?

============================================================
RULES

Undying
702.93a
Undying is a triggered ability. When this permanent is put into a graveyard from the battlefield, if it had no +1/+1 counters on it, return it to the battlefield with a +1/+1 counter on it.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "ya tiene un contador +1/+1",
            "Undying no se dispara",
            "permanece en el cementerio",
        ],
        "Undying with existing +1/+1 counter",
    )


def test_london_mulligan_definition_is_deterministic():
    knowledge = """
QUESTION

Explícame el London Mulligan.

============================================================
RULES

103.5
Each player draws a number of cards equal to their starting hand size, which is normally seven. To take a mulligan, a player draws a new hand equal to their starting hand size, then puts a number of those cards equal to the number of mulligans taken on the bottom of their library.

103.5c
In a multiplayer game and in any Brawl game, the first mulligan a player takes doesn't count toward the number of cards that player will put on the bottom of their library.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "siete cartas",
            "fondo",
            "mulligans",
            "multijugador",
            "primer mulligan es gratuito",
        ],
        "London Mulligan definition",
    )


def test_london_mulligan_draw_followup_is_deterministic():
    knowledge = """
QUESTION

¿Cuántas cartas robo después?

============================================================
RULES

103.5
Each player draws a number of cards equal to their starting hand size, which is normally seven. To take a mulligan, a player draws a new hand equal to their starting hand size, then puts a number of those cards equal to the number of mulligans taken on the bottom of their library.

103.5c
In a multiplayer game, the first mulligan doesn't count.
"""

    answer = render_rule_answer(knowledge)

    assert answer
    assert_contains(
        answer,
        [
            "tamaño inicial",
            "siete cartas",
            "fondo",
            "primero es gratuito",
        ],
        "London Mulligan draw follow-up",
    )


def main():
    tests = [
        test_no_priority_during_resolution,
        test_untap_step_priority,
        test_apnap_triggers,
        test_mana_ability_uses_recovered_arcane_signet_oracle,
        test_mana_ability_is_inferred_from_recovered_oracle,
        test_single_recovered_mana_ability_supports_generic_card_reference,
        test_sol_ring_mana_ability_ignores_mana_cost_metadata,
        test_mana_renderer_requires_recovered_rule_evidence,
        test_stack_resolves_one_object_then_returns_priority,
        test_priority_returns_between_stack_objects,
        test_opponent_can_respond_before_spell_resolves,
        test_ward_is_triggered_and_can_be_responded_to,
        test_copied_triggered_ability_survives_sacrificing_its_source,
        test_copied_ability_renderer_requires_source_independence_evidence,
        test_activated_ability_exists_independently_of_source,
        test_source_independence_uses_type_neutral_wording,
        test_source_independence_wins_over_resolution_wording,
        test_activated_and_triggered_ability_taxonomy,
        test_cleanup_step_normally_has_no_priority,
        test_sacrifice_is_not_destroy,
        test_commander_dies_before_state_based_move,
        test_commander_hand_library_is_replacement_effect,
        test_copy_of_commander_is_not_commander,
        test_elenda_commander_death_uses_recovered_card_name,
        test_sacrifice_as_cost_death_trigger_is_rendered_deterministically,
        test_sacrifice_counts_as_dies_is_rendered_deterministically,
        test_power_toughness_set_then_modify_uses_layers_7b_and_7c,
        test_undying_sacrifice_is_rendered_deterministically,
        test_exile_does_not_trigger_undying,
        test_multiple_counter_replacement_effects_choose_order,
        test_entering_with_counters_uses_replacement_sequence,
        test_zero_zero_persist_mentions_state_based_actions,
        test_persist_and_undying_share_stack_but_only_one_returns_card,
        test_layered_static_source_comparison_is_deterministic,
        test_direct_undying_definition_is_deterministic,
        test_keyword_difference_uses_recovered_rules,
        test_rule_followup_example_uses_active_undying_rule,
        test_undying_with_existing_positive_counter_is_deterministic,
        test_london_mulligan_definition_is_deterministic,
        test_london_mulligan_draw_followup_is_deterministic,
    ]

    errors = []

    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")

        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}")
            print(exc)

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Tests : {len(tests)}")
    print(f"Errors: {len(errors)}")

    if errors:
        raise SystemExit(1)

    print("OK")


if __name__ == "__main__":
    main()
