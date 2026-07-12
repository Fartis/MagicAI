from magicai.retrieval.rule_queries import build_rule_queries


def assert_contains(
    items: list[str],
    expected: list[str],
    label: str,
):

    joined = "\n".join(items).lower()

    missing = [
        item
        for item in expected
        if item.lower() not in joined
    ]

    if missing:

        raise AssertionError(
            f"{label}: missing {missing!r} in queries:\n{joined}"
        )


def assert_not_contains_exact(
    items: list[str],
    forbidden: list[str],
    label: str,
):

    lower_items = [
        item.lower()
        for item in items
    ]

    present = [
        item
        for item in forbidden
        if item.lower() in lower_items
    ]

    if present:

        raise AssertionError(
            f"{label}: unexpected exact queries {present!r} in:\n{items}"
        )


def test_sacrifice_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si lo sacrifico?",
        keywords=[],
        action_terms=[
            "sacrifice",
            "permanent",
            "battlefield",
            "graveyard",
        ],
    )

    assert_contains(
        queries,
        [
            "sacrifice a permanent",
            "battlefield",
            "graveyard",
        ],
        "sacrifice queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "sacrifice",
            "permanent",
            "graveyard",
            "battlefield",
        ],
        "sacrifice queries",
    )


def test_dies_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si muere?",
        keywords=[],
        action_terms=[
            "dies",
            "graveyard",
            "battlefield",
        ],
    )

    assert_contains(
        queries,
        [
            "graveyard from the battlefield",
        ],
        "dies queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "dies",
            "graveyard",
            "battlefield",
        ],
        "dies queries",
    )


def test_exile_queries_are_specific():

    queries = build_rule_queries(
        question="¿Y si lo exilio?",
        keywords=[],
        action_terms=[
            "exile",
            "exile zone",
        ],
    )

    assert_contains(
        queries,
        [
            "exile",
            "exile zone",
        ],
        "exile queries",
    )

    assert_not_contains_exact(
        queries,
        [
            "exile",
            "exile zone",
        ],
        "exile queries",
    )


def test_resolution_queries_include_no_priority_during_resolution():

    queries = build_rule_queries(
        question="Si una habilidad está resolviéndose, ¿puedo activar otra habilidad?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "no player has priority",
            "resolving",
        ],
        "resolution priority queries",
    )


def test_end_step_queries_include_apnap_stack():

    queries = build_rule_queries(
        question="Si dos jugadores tienen habilidades al comienzo del paso final, ¿en qué orden van a la pila?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "end step",
            "APNAP",
            "stack",
        ],
        "end step APNAP queries",
    )


def test_generic_mana_ability_queries_include_stack_exception():

    queries = build_rule_queries(
        question="¿Puedo responder a una habilidad de maná?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "mana abilities",
            "do not use the stack",
            "resolve immediately",
        ],
        "mana ability queries",
    )



def test_mana_production_queries_include_rule_605_without_card_name():

    queries = build_rule_queries(
        question="Cuando giro una criatura para añadir maná, ¿se puede responder?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "605",
            "mana abilities",
            "do not use the stack",
        ],
        "generic mana production queries",
    )


def test_removed_source_queries_include_independent_ability_rule():

    queries = build_rule_queries(
        question="Si activo una habilidad y después destruyen esa criatura, ¿desaparece de la pila?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "113",
            "activated ability on the stack exists independently of its source",
        ],
        "source independence queries",
    )


def test_response_before_resolution_queries_include_priority_and_stack():

    queries = build_rule_queries(
        question="Si lanzo un hechizo, ¿mi oponente puede responder antes de que se resuelva?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "117",
            "405",
            "priority",
            "stack",
        ],
        "response before resolution queries",
    )



def test_cleanup_queries_include_normal_no_priority_exception():
    queries = build_rule_queries(
        question="Si descarto por tamaño máximo de mano en el paso de limpieza, ¿hay prioridad?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "514",
            "cleanup step normally no player receives priority",
            "triggered abilities",
        ],
        "cleanup priority queries",
    )


def test_sacrifice_destroy_queries_include_both_keyword_actions():
    queries = build_rule_queries(
        question="¿Sacrificar una criatura cuenta como destruirla?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "701.8",
            "701.21",
            "sacrificing a permanent doesn't destroy it",
        ],
        "sacrifice destroy queries",
    )


def test_commander_death_queries_include_state_based_move():
    queries = build_rule_queries(
        question="Si mi comandante muere, ¿puedo moverlo a la zona de mando y disparar cuando muera?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "903.9a",
            "700.4",
            "state-based action",
            "dies graveyard from battlefield",
        ],
        "commander death queries",
    )


def test_commander_hand_library_queries_include_replacement_effect():
    queries = build_rule_queries(
        question="Si mi comandante fuera a mi mano o biblioteca, ¿puedo ponerlo en la zona de mando?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "903.9b",
            "hand library",
            "replacement effect",
        ],
        "commander hand library queries",
    )


def test_commander_copy_queries_include_designation_rule():
    queries = build_rule_queries(
        question="Si una copia de mi comandante muere, ¿puede ir a la zona de mando?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "903.3",
            "copying a commander is not a commander",
            "designation",
        ],
        "commander copy queries",
    )


def test_counter_replacement_queries_include_exact_interaction_rules():
    queries = build_rule_queries(
        question="Si un permanente entra con contadores y varios efectos los modifican, ¿se suman o se reemplazan?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["614.1c", "616.1", "616.1f", "122.6"],
        "counter replacement exact rules",
    )


def test_counter_replacement_queries_detect_natural_language_order_paraphrase():
    queries = build_rule_queries(
        question=(
            "Hay dos efectos que modifican los contadores que va a recibir un "
            "permanente. ¿El controlador del objeto afectado elige el orden en "
            "que se aplican?"
        ),
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["614.1c", "616.1", "616.1f", "122.6"],
        "counter replacement natural-language order paraphrase",
    )


def test_persist_zero_zero_queries_include_keyword_and_state_based_rules():
    queries = build_rule_queries(
        question="Si una criatura 0/0 entra con un contador +1/+1 y tiene Persist, ¿qué pasa cuando muere?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["702.79", "704.5f", "704.5q", "122.3"],
        "persist zero zero rules",
    )


def test_undying_exile_queries_include_exile_and_dies_rules():
    queries = build_rule_queries(
        question="Si una criatura con Undying es exiliada, ¿vuelve?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["701.13", "702.93", "700.4"],
        "undying exile rules",
    )


def test_persist_undying_queries_include_both_keywords_and_stack():
    queries = build_rule_queries(
        question="Si una criatura tiene Persist y Undying y muere sin contadores, ¿qué ocurre?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["702.79", "702.93", "603", "405"],
        "persist undying rules",
    )



def test_bello_layer_interaction_prioritizes_continuous_effect_rules():
    question = (
        "Tengo a Bello, Bard of the Brambles como comandante y un "
        "encantamiento de coste 4 que Bello convierte en criatura 4/4. "
        "Un oponente encanta a Bello con Imprisoned in the Moon o Song "
        "of the Dryads. ¿El encantamiento sigue siendo criatura o vuelve "
        "a ser un encantamiento normal?"
    )

    queries = build_rule_queries(
        question=question,
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        [
            "611.3",
            "613.1d",
            "613.1f",
            "613.4b",
            "613.6",
            "613.8",
            "305.7",
        ],
        "Bello layers interaction",
    )

    assert_not_contains_exact(
        queries,
        [
            "603",
            "701.21",
            "903.9a",
            "903.9b",
        ],
        "Bello layers interaction",
    )


def test_mana_value_reference_does_not_become_casting_cost_question():
    queries = build_rule_queries(
        question="Controlo un encantamiento de coste 4. ¿Sigue siendo criatura?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["202.3"],
        "mana value reference",
    )

    assert_not_contains_exact(
        queries,
        ["601", "603", "701.21"],
        "mana value reference",
    )


def test_actual_casting_cost_question_still_recovers_rule_601():
    queries = build_rule_queries(
        question="¿Cómo calculo y pago el coste total para lanzar este hechizo?",
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["601", "total cost"],
        "casting cost question",
    )


def test_commander_as_role_does_not_inject_zone_rules():
    queries = build_rule_queries(
        question="Bello es mi comandante y pierde sus habilidades. ¿Qué ocurre con su efecto?",
        keywords=[],
        action_terms=[],
    )

    assert_not_contains_exact(
        queries,
        ["903.3", "903.9a", "903.9b"],
        "commander role mention",
    )



def test_bare_zero_zero_persist_is_not_misclassified_as_layers():
    queries = build_rule_queries(
        question=(
            "Una criatura base 0/0 con Persist vuelve del cementerio con su "
            "contador. ¿Qué comprueba el juego después?"
        ),
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["702.79", "704.5f", "704.5q", "122.3"],
        "zero-zero Persist exact rules",
    )

    assert_not_contains_exact(
        queries,
        ["611.3", "613.1d", "613.1f", "613.4b", "613.6", "613.8"],
        "zero-zero Persist must not route to layers",
    )


def test_sacrifice_as_cost_death_trigger_prioritizes_stack_and_trigger_rules():
    queries = build_rule_queries(
        question=(
            "Si sacrifico Young Wolf como coste para lanzar Village Rites, "
            "¿su habilidad de morir se resuelve antes que el hechizo?"
        ),
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["601", "117", "603", "405", "701.21", "700.4"],
        "sacrifice as cost death trigger",
    )


def test_command_zone_reference_is_enough_for_commander_zone_rules():
    queries = build_rule_queries(
        question=(
            "Si Elenda, the Dusk Rose muere y la mando a la zona de mando, "
            "¿se dispara su habilidad?"
        ),
        keywords=[],
        action_terms=[],
    )

    assert_contains(
        queries,
        ["903.9a", "700.4", "704"],
        "implicit commander through command zone",
    )


def main():

    tests = [
        test_sacrifice_queries_are_specific,
        test_dies_queries_are_specific,
        test_exile_queries_are_specific,
        test_resolution_queries_include_no_priority_during_resolution,
        test_end_step_queries_include_apnap_stack,
        test_generic_mana_ability_queries_include_stack_exception,
        test_mana_production_queries_include_rule_605_without_card_name,
        test_response_before_resolution_queries_include_priority_and_stack,
        test_removed_source_queries_include_independent_ability_rule,
        test_cleanup_queries_include_normal_no_priority_exception,
        test_sacrifice_destroy_queries_include_both_keyword_actions,
        test_commander_death_queries_include_state_based_move,
        test_commander_hand_library_queries_include_replacement_effect,
        test_commander_copy_queries_include_designation_rule,
        test_counter_replacement_queries_include_exact_interaction_rules,
        test_counter_replacement_queries_detect_natural_language_order_paraphrase,
        test_persist_zero_zero_queries_include_keyword_and_state_based_rules,
        test_undying_exile_queries_include_exile_and_dies_rules,
        test_persist_undying_queries_include_both_keywords_and_stack,
        test_bello_layer_interaction_prioritizes_continuous_effect_rules,
        test_mana_value_reference_does_not_become_casting_cost_question,
        test_actual_casting_cost_question_still_recovers_rule_601,
        test_commander_as_role_does_not_inject_zone_rules,
        test_bare_zero_zero_persist_is_not_misclassified_as_layers,
        test_sacrifice_as_cost_death_trigger_prioritizes_stack_and_trigger_rules,
        test_command_zone_reference_is_enough_for_commander_zone_rules,
    ]

    errors = []

    for test in tests:

        try:

            test()

            print(f"OK: {test.__name__}")

        except Exception as exc:

            errors.append(
                (
                    test.__name__,
                    exc,
                )
            )

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
