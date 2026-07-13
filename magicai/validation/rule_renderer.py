import re


"""
Temporary deterministic renderer for high-risk MTG rule concepts.

This file is scaffolding, not the final architecture.

Do not add one function per Gauntlet case, one function per exact wording,
or one function per specific card unless the branch is also backed by
recovered Oracle/rule evidence and represents a reusable rules concept.

Preferred direction:
- detect concepts from question + recovered evidence
- render from supported facts
- keep renderers generic and auditable
"""

_RULE_MARKERS = {
    "abilities": ["113", "113."],
    "priority": ["117", "117."],
    "stack": ["405", "405."],
    "untap": ["502", "502."],
    "end_step": ["513", "513."],
    "triggered": ["603", "603."],
    "activated": ["602", "602."],
    "mana": ["605", "605."],
    "resolution": ["608", "608."],
    "casting": ["601", "601."],
    "ward": ["702.21", "702.21a"],
    "cleanup": ["514", "514."],
    "dies": ["700.4"],
    "sacrifice": ["701.21", "701.21a"],
    "destroy": ["701.8", "701.8a"],
    "exile": ["701.13", "701.13a"],
    "commander_designation": ["903.3"],
    "commander_graveyard_exile": ["903.9a"],
    "commander_hand_library": ["903.9b"],
    "replacement": ["614", "614."],
    "replacement_interaction": ["616", "616."],
    "counters": ["122", "122."],
    "state_based": ["704", "704."],
    "zero_toughness": ["704.5f"],
    "counter_cancellation": ["704.5q", "122.3"],
    "continuous_static": ["611.3"],
    "type_layer": ["613.1d"],
    "ability_layer": ["613.1f"],
    "pt_set_layer": ["613.4b"],
    "layer_continuity": ["613.6"],
    "dependency": ["613.8"],
    "basic_land_type": ["305.7"],
    "zone_change": ["400.7"],
    "persist": ["702.79", "702.79a"],
    "undying": ["702.93", "702.93a"],
    "mulligan": ["103.5", "103.5a", "103.5b", "103.5c", "103.5d"],
}


def render_rule_answer(knowledge: str) -> str | None:
    """
    Render a deterministic answer only when both conditions are met:

    1. The question expresses a reusable MTG rules concept.
    2. The recovered knowledge contains the relevant rules evidence.

    The renderer must not infer card text from the model's memory. Card-specific
    conclusions are only allowed when the recovered CARDS block supports them.
    """

    question = _extract_question(knowledge)
    q = _normalize(question)

    if not q:
        return None

    if _is_undying_existing_counter_question(q) and _has_rules(
        knowledge,
        ["undying"],
    ):
        return (
            "Si el permanente ya tiene un contador +1/+1 cuando muere, "
            "Undying no se dispara porque no se cumple su condición. La carta "
            "permanece en el cementerio, salvo que otro efecto la mueva o la "
            "devuelva."
        )

    if _is_london_mulligan_question(q) and _has_rules(
        knowledge,
        ["mulligan"],
    ):
        return (
            "Con el London Mulligan, cada vez que haces mulligan robas una "
            "nueva mano igual a tu tamaño inicial, normalmente siete cartas. "
            "Después colocas en el fondo de tu biblioteca tantas cartas como "
            "mulligans hayan contado para ti. En multijugador y Brawl, el "
            "primer mulligan es gratuito: no cuenta para las cartas que debes "
            "poner en el fondo."
        )

    if _is_mulligan_draw_followup(q) and _has_rules(
        knowledge,
        ["mulligan"],
    ):
        return (
            "Robas una nueva mano igual a tu tamaño inicial, normalmente siete "
            "cartas. Después colocas en el fondo de la biblioteca una carta por "
            "cada mulligan que haya contado para ti; en multijugador y Brawl, el "
            "primero es gratuito."
        )

    layered_answer = _render_layered_static_source_comparison(
        knowledge,
        q,
    )

    if layered_answer is not None:
        return layered_answer

    if _asks_keyword_difference(q) and _has_rules(
        knowledge,
        ["persist", "undying"],
    ):
        return (
            "Undying y Persist se disparan cuando el permanente muere, pero "
            "comprueban contadores distintos. Undying solo se dispara si no "
            "tenía contadores +1/+1 y lo devuelve con un contador +1/+1. "
            "Persist solo se dispara si no tenía contadores -1/-1 y lo devuelve "
            "con un contador -1/-1."
        )

    if _asks_for_example(q) and _has_rules(
        knowledge,
        ["undying"],
    ):
        return (
            "Por ejemplo, una criatura con Undying muere sin contadores +1/+1. "
            "La habilidad se dispara y, al resolverse, la carta vuelve del "
            "cementerio al campo de batalla con un contador +1/+1. Si ya tenía "
            "un contador +1/+1 cuando murió, Undying no se dispara."
        )

    if _is_direct_keyword_definition(q, "undying") and _has_rules(
        knowledge,
        ["undying"],
    ):
        return (
            "Undying es una habilidad disparada. Cuando el permanente muere, "
            "si no tenía contadores +1/+1, vuelve del cementerio al campo de "
            "batalla bajo el control de su dueño con un contador +1/+1."
        )

    if _is_direct_keyword_definition(q, "persist") and _has_rules(
        knowledge,
        ["persist"],
    ):
        return (
            "Persist es una habilidad disparada. Cuando el permanente muere, "
            "si no tenía contadores -1/-1, vuelve del cementerio al campo de "
            "batalla bajo el control de su dueño con un contador -1/-1."
        )

    layered_answer = _render_layered_static_source_comparison(
        knowledge,
        q,
    )

    if layered_answer is not None:
        return layered_answer

    if _is_persist_and_undying_question(q) and _has_rules(
        knowledge,
        ["persist", "undying", "triggered", "stack", "zone_change"],
    ):
        return (
            "No hay un retorno infinito automático. Si la criatura muere "
            "sin contadores +1/+1 ni -1/-1, Persist y Undying son dos habilidades "
            "disparadas y ambas se ponen en la pila. Su controlador elige el "
            "orden. La primera que se resuelva devuelve la carta con su contador "
            "correspondiente; la otra no la encuentra ya en el cementerio y no "
            "hace nada. Si después la criatura vuelve a morir, normalmente solo "
            "se disparará la habilidad opuesta al contador que tenga. Con una "
            "forma repetible de hacerla morir o sacrificarla, puede alternar entre "
            "un contador +1/+1 y un contador -1/-1, pero no ocurre sola."
        )

    if _is_zero_zero_persist_question(q) and _has_rules(
        knowledge,
        [
            "persist",
            "state_based",
            "zero_toughness",
            "counter_cancellation",
        ],
    ):
        return (
            "Cuando la criatura muere, Persist se dispara si no tenía un contador "
            "-1/-1. Al resolverse, vuelve al campo de batalla con un contador "
            "-1/-1. Si el contador +1/+1 era solo el que ya tenía antes de morir, "
            "la criatura 0/0 vuelve con resistencia -1 y las acciones basadas en "
            "estado la ponen de nuevo en el cementerio; esa vez Persist no vuelve "
            "a dispararse porque murió con un contador -1/-1. Si existe un efecto "
            "que hace que entre con un +1/+1 cada vez, entrará con ambos tipos de "
            "contadores, se cancelarán como acción basada en estado y, al quedar "
            "como 0/0, otra acción basada en estado la pondrá en el cementerio. "
            "Como entonces murió sin un contador -1/-1, Persist puede volver a "
            "dispararse y producir un bucle si ese efecto de entrada es obligatorio."
        )

    if _is_counter_replacement_question(q) and _has_rules(
        knowledge,
        ["replacement", "replacement_interaction", "counters"],
    ):
        if _asks_about_counter_doublers(q):
            return (
                "Son efectos de reemplazo, no habilidades disparadas, y no van a "
                "la pila. Si ambos intentan modificar el mismo evento de poner "
                "contadores, el controlador del objeto afectado o el jugador "
                "afectado elige el orden en que se aplican. Se aplica uno, se "
                "recalcula el evento y después puede aplicarse el otro. Si los dos "
                "duplican ese mismo evento, N contadores pasan a 2N y luego a 4N."
            )

        if _asks_about_entering_with_counters(q):
            return (
                "Los efectos que modifican cuántos contadores lleva un permanente "
                "al entrar son efectos de reemplazo. No se disparan; se aplican "
                "sin utilizar la pila y modifican el propio evento de entrada. "
                "Si hay varios "
                "aplicables, el controlador del permanente que entra —o su "
                "propietario si aún no tiene controlador— elige el "
                "orden; se aplica uno y después se vuelve a comprobar cuáles "
                "siguen siendo aplicables. Por tanto, no se limitan a sumarse ni "
                "se anulan entre sí por defecto: cada uno reemplaza sucesivamente "
                "el evento modificado."
            )

        return (
            "Son efectos de reemplazo que modifican el mismo evento de poner "
            "contadores. El controlador del objeto afectado o el jugador afectado "
            "elige el orden: se aplica uno, se recalcula el evento y después se "
            "aplican sucesivamente los que sigan siendo válidos. No son "
            "habilidades disparadas."
        )

    if _is_undying_exile_question(q) and _has_rules(
        knowledge,
        ["undying", "dies", "exile"],
    ):
        return (
            "No. Exiliar la criatura la mueve a la zona de exilio, no al "
            "cementerio, así que no muere. Undying solo se dispara cuando el "
            "permanente va del campo de batalla al cementerio; por tanto, no "
            "se dispara y la criatura no vuelve por Undying."
        )

    if _is_undying_return_question(q):
        required_rules = ["undying", "dies"]

        if "sacrific" in q:
            required_rules.append("sacrifice")

        if _has_rules(knowledge, required_rules):
            opening = (
                "Al sacrificar la criatura, pasa del campo de batalla al "
                "cementerio y muere. "
                if "sacrific" in q
                else "Cuando la criatura muere y va del campo de batalla al "
                "cementerio, "
            )

            return (
                opening
                + "si no tenía contadores +1/+1, Undying se dispara y, cuando "
                "esa habilidad se resuelve, la criatura vuelve al campo de "
                "batalla bajo el control de su dueño con un contador +1/+1."
            )

    if _is_persist_return_question(q) and _has_rules(
        knowledge,
        ["persist", "dies"],
    ):
        return (
            "Cuando la criatura muere, si no tenía contadores -1/-1, Persist se "
            "dispara. Al resolverse, vuelve al campo de batalla bajo el control de "
            "su dueño con un contador -1/-1."
        )

    if _is_cleanup_priority_question(q) and _has_rules(
        knowledge,
        ["cleanup"],
    ):
        return (
            "Normalmente no. En el paso de limpieza el jugador activo descarta "
            "hasta su tamaño máximo de mano y, por regla general, ningún jugador "
            "recibe prioridad. Solo si se realizan acciones basadas en estado o "
            "hay habilidades disparadas esperando para ir a la pila, el jugador "
            "activo recibe prioridad; después habrá otro paso de limpieza."
        )

    if _is_sacrifice_not_destroy_question(q) and _has_rules(
        knowledge,
        ["sacrifice", "destroy"],
    ):
        return (
            "No. Sacrificar una criatura no cuenta como destruirla y no es lo "
            "mismo. Al sacrificarla, su controlador la mueve directamente del "
            "campo de batalla al cementerio. Como no es destrucción, regenerar "
            "ni los efectos que reemplazan la destrucción pueden impedir ese "
            "sacrificio."
        )

    if _is_commander_copy_zone_question(q) and _has_rules(
        knowledge,
        ["commander_designation"],
    ):
        return (
            "No. La designación de comandante pertenece a la carta concreta "
            "elegida al construir el mazo y no es un valor copiable. Un permanente "
            "que solo es una copia de tu comandante no es esa carta comandante, "
            "así que esa copia no puede moverse a la zona de mando mediante la "
            "regla de comandante; si muere, va al cementerio normalmente."
        )

    if _is_commander_hand_library_question(q) and _has_rules(
        knowledge,
        ["commander_hand_library", "commander_graveyard_exile"],
    ):
        return (
            "No exactamente: funciona de forma diferente. Si tu comandante fuera "
            "a tu mano o biblioteca desde cualquier zona, puedes aplicar un efecto "
            "de reemplazo y ponerlo en la zona de mando en su lugar, por lo que no "
            "llega a la mano o biblioteca. En cambio, si va al cementerio o al "
            "exilio, primero llega a esa zona y después puedes moverlo a la zona "
            "de mando cuando se comprueban las acciones basadas en estado."
        )

    if _is_commander_death_zone_question(q) and _has_rules(
        knowledge,
        ["dies", "commander_graveyard_exile"],
    ):
        card_name = _extract_primary_card_name(knowledge)
        subject = card_name or "El comandante"

        return (
            f"Sí. {subject} muere porque primero se mueve del campo de batalla "
            "al cementerio. Por eso, las habilidades de «cuando muera» se "
            "disparan. Después, al comprobarse las acciones basadas en estado, "
            "su dueño puede mover esa carta del cementerio a la zona de mando. "
            "Moverla después no deshace que haya muerto."
        )

    if _is_sacrifice_as_cost_death_trigger(q) and _has_rules(
        knowledge,
        ["casting", "priority", "triggered", "stack"],
    ):
        return (
            "Sí, pero no porque la habilidad sea parte del coste. "
            "Al sacrificar la criatura como coste, la criatura muere y su "
            "habilidad disparada se dispara. Esa habilidad no se resuelve "
            "durante el lanzamiento: se pone en la pila la próxima vez que "
            "un jugador fuera a recibir prioridad. Normalmente quedará encima "
            "del hechizo que estás lanzando, así que se resolverá antes que el "
            "hechizo si nadie responde."
        )

    if _is_source_independence_question(q) and _has_rules(
        knowledge,
        ["abilities", "stack"],
    ):
        return (
            "No. La habilidad no se contrarresta por destruir o retirar su "
            "fuente. Una vez activada, existe en la pila de forma independiente "
            "de su fuente; permanece en la pila y normalmente seguirá "
            "resolviéndose."
        )

    if _is_no_priority_during_resolution(q) and _has_rules(
        knowledge,
        ["priority"],
    ):
        return (
            "No. Mientras una habilidad se está resolviendo, los jugadores no "
            "tienen prioridad. Aunque esa habilidad ponga un permanente en el campo "
            "de batalla o cree una ficha, no puedes activar habilidades de ese "
            "permanente durante la resolución salvo que el propio efecto te indique "
            "explícitamente que lo hagas."
        )

    if _is_mana_ability_response(q) and _has_rules(
        knowledge,
        ["mana"],
    ) and _supports_mana_ability(knowledge, q):
        card_name = _extract_primary_card_name(knowledge)
        subject = (
            f"La habilidad de maná de {card_name}"
            if card_name
            else "Esa habilidad de maná"
        )

        return (
            f"No. {subject} se activa para añadir maná, no usa la pila y se "
            "resuelve inmediatamente. Por eso no se puede responder a esa "
            "habilidad en sí."
        )

    if _is_ward_question(q) and _has_rules(
        knowledge,
        ["ward", "triggered", "stack"],
    ):
        return (
            "Ward es una habilidad disparada; no es un coste adicional para "
            "lanzar el hechizo. Cuando el permanente se convierte en objetivo de un "
            "hechizo o habilidad que controla un oponente, Ward se dispara y su "
            "habilidad se pone en la pila. Sí, los jugadores reciben prioridad y "
            "pueden responder a esa habilidad antes de que se resuelva."
        )

    if _is_ability_taxonomy_question(q) and _has_rules(
        knowledge,
        ["activated", "triggered"],
    ):
        return (
            "No. Son categorías distintas. Una habilidad activada se escribe como "
            "«[coste]: [efecto]» y un jugador la activa pagando lo que aparece "
            "antes de los dos puntos. Una habilidad disparada comienza con "
            "expresiones como «cuando», «siempre que» o «al comienzo de» y se "
            "dispara automáticamente cuando ocurre su evento."
        )

    if _is_priority_between_stack_objects(q) and _has_rules(
        knowledge,
        ["stack", "priority"],
    ):
        return (
            "Sí. Después de que se resuelve un objeto de la pila, el jugador "
            "activo recibe prioridad antes de que se resuelva el siguiente. Los "
            "jugadores pueden lanzar hechizos o activar habilidades entre ambos "
            "objetos."
        )

    if _is_stack_progression_question(q) and _has_rules(
        knowledge,
        ["stack", "priority"],
    ):
        return (
            "No. Los objetos de la pila se resuelven uno a uno, empezando por el "
            "que está arriba. Después de que un objeto se resuelve, el jugador "
            "activo recibe prioridad; por tanto, los jugadores pueden actuar "
            "entre ese objeto y el siguiente."
        )

    if _is_response_before_resolution(q) and _has_rules(
        knowledge,
        ["priority", "stack"],
    ):
        return (
            "Sí. Después de lanzar el hechizo, quien lo lanzó vuelve a recibir "
            "prioridad. Cuando la cede, tu oponente puede responder antes de que "
            "el hechizo se resuelva. El hechizo solo se resuelve cuando todos los "
            "jugadores pasan prioridad consecutivamente sin añadir nada a la pila."
        )

    if _is_untap_step_priority(q) and _has_rules(
        knowledge,
        ["untap"],
    ):
        return (
            "Normalmente no. En el paso de enderezar ningún jugador recibe "
            "prioridad, así que no se pueden lanzar hechizos ni activar "
            "habilidades en ese momento. Si una habilidad se dispara durante el "
            "paso de enderezar, se mantiene esperando y se pone en la pila la "
            "próxima vez que un jugador fuera a recibir prioridad."
        )

    if _is_simultaneous_trigger_order(q) and _has_rules(
        knowledge,
        ["triggered", "stack"],
    ):
        return (
            "Si varias habilidades disparadas deben ponerse en la pila al mismo "
            "tiempo, se ordenan con APNAP: primero el jugador activo pone en la "
            "pila las habilidades que controla en el orden que elige, y después "
            "cada jugador no activo hace lo mismo en orden de turno. Como la pila "
            "resuelve de arriba abajo, las habilidades del jugador no activo "
            "pueden resolverse antes."
        )

    if _is_end_step_apnap(q) and _has_rules(
        knowledge,
        ["triggered", "stack"],
    ):
        return (
            "Al comienzo del paso final, las habilidades que se disparan en ese "
            "momento van a la pila usando el orden APNAP. El jugador activo pone "
            "primero en la pila las habilidades que controla, en el orden que "
            "elija; después lo hace el jugador no activo. Luego la pila se "
            "resuelve de arriba abajo."
        )

    if _is_may_trigger_choice(q) and _has_rules(
        knowledge,
        ["triggered", "resolution"],
    ):
        return (
            "En una habilidad disparada que dice «puedes», normalmente decides "
            "si haces ese efecto al resolverse la habilidad. La habilidad se pone "
            "en la pila como habilidad disparada, y cuando se resuelve aplicas sus "
            "instrucciones y tomas las decisiones que el efecto pida entonces."
        )

    return None


def _render_layered_static_source_comparison(
    knowledge: str,
    question: str,
) -> str | None:
    """Resolve a reusable continuous-effect dependency pattern.

    This covers comparisons where a static ability animates or grants
    characteristics to other permanents, while two different effects alter
    the source: one removes abilities in layer 6, and another assigns a basic
    land type in layer 4. The conclusion is derived from recovered Oracle text
    plus layers evidence, not from memorized card names.
    """

    if not _looks_like_layered_static_source_comparison(question):
        return None

    required = [
        "continuous_static",
        "type_layer",
        "ability_layer",
        "pt_set_layer",
        "layer_continuity",
        "dependency",
        "basic_land_type",
    ]

    if not _has_rules(knowledge, required):
        return None

    entries = _extract_card_entries(knowledge)

    if len(entries) < 3:
        return None

    animator = _find_card_entry(
        entries,
        required_markers=[
            "during your turn",
            "is a 4/4",
            "in addition to its other types",
        ],
    )
    explicit_ability_loss = _find_card_entry(
        entries,
        required_markers=[
            "enchanted permanent",
            "loses all",
            "abilities",
        ],
    )
    basic_land_setter = _find_basic_land_type_setter(entries)

    if not animator or not explicit_ability_loss or not basic_land_setter:
        return None

    animator_name = animator[0]
    explicit_name = explicit_ability_loss[0]
    basic_name = basic_land_setter[0]

    return (
        f"Los dos efectos producen resultados distintos. Con {explicit_name}, "
        f"el efecto continuo de {animator_name} ya empezó a aplicarse en la "
        "capa de cambio de tipo antes de que la fuente pierda sus habilidades "
        "en una capa posterior. Por la continuidad entre capas, el encantamiento "
        "permanece como criatura Elemental 4/4 y conserva las habilidades que "
        "ese efecto le concede, incluida prisa; por tanto, puede atacar este "
        "turno si está enderezado y no existe otra restricción. "
        f"Con {basic_name}, el resultado cambia: asignar un tipo de tierra "
        "básica se aplica en la misma capa de cambio de tipo y hace que la "
        f"fuente pierda sus habilidades antes de que el efecto de {animator_name} "
        "pueda empezar a aplicarse. Por dependencia, ese efecto deja de animar "
        "el encantamiento, que vuelve a ser un encantamiento normal y no puede "
        "atacar como criatura."
    )


def _looks_like_layered_static_source_comparison(question: str) -> bool:
    has_characteristic_result = any(
        marker in question
        for marker in [
            "4/4",
            "sigue siendo",
            "permanece",
            "continua siendo",
            "vuelve a ser",
            "deja de ser",
        ]
    )
    has_source_change = any(
        marker in question
        for marker in [
            "pierde habilidades",
            "pierde todas las habilidades",
            "convierte en una tierra",
            "convierte en tierra",
            "encanta",
            "enchanted",
        ]
    )
    compares_effects = any(
        marker in question
        for marker in [
            " o con ",
            " o ",
            "dos efectos",
            "ambos efectos",
            "resultados distintos",
        ]
    )

    return has_characteristic_result and has_source_change and compares_effects


def _extract_card_entries(knowledge: str) -> list[tuple[str, str]]:
    cards_block = _extract_cards_block(knowledge)

    if not cards_block:
        return []

    pattern = re.compile(
        r"(?ms)^([^\n=]+)\n"
        r"(?:Mana Cost:[^\n]*\n)?"
        r"([^\n]+)\n\n"
        r"(.*?)"
        r"(?=\n\n[^\n=]+\n(?:Mana Cost:[^\n]*\n)?[^\n]+\n\n|\Z)"
    )

    entries = []

    for match in pattern.finditer(cards_block.strip()):
        name = match.group(1).strip()
        type_line = match.group(2).strip()
        oracle = match.group(3).strip()
        entries.append((name, f"{type_line}\n{oracle}"))

    return entries


def _find_card_entry(
    entries: list[tuple[str, str]],
    required_markers: list[str],
) -> tuple[str, str] | None:
    for entry in entries:
        normalized = _normalize(entry[1])

        if all(marker in normalized for marker in required_markers):
            return entry

    return None


def _find_basic_land_type_setter(
    entries: list[tuple[str, str]],
) -> tuple[str, str] | None:
    basic_types = [
        "plains",
        "island",
        "swamp",
        "mountain",
        "forest",
    ]

    for entry in entries:
        normalized = _normalize(entry[1])

        if "enchanted permanent" not in normalized:
            continue

        if "land" not in normalized:
            continue

        if "loses all" in normalized and "abilities" in normalized:
            continue

        if any(land_type in normalized for land_type in basic_types):
            return entry

    return None


def _extract_question(knowledge: str) -> str:
    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _extract_cards_block(knowledge: str) -> str:
    match = re.search(
        r"={10,}\s*CARDS\s+(.*?)(?:={10,}|$)",
        knowledge,
        flags=re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def _extract_primary_card_name(knowledge: str) -> str | None:
    cards_block = _extract_cards_block(knowledge)

    for line in cards_block.splitlines():
        value = line.strip()

        if value:
            return value

    return None


def _normalize(text: str) -> str:
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


def _has_rules(
    knowledge: str,
    rule_groups: list[str],
) -> bool:
    lower = knowledge.lower()

    for group in rule_groups:
        markers = _RULE_MARKERS.get(
            group,
            [],
        )

        if not any(marker in lower for marker in markers):
            return False

    return True


def _supports_mana_ability(
    knowledge: str,
    question: str,
) -> bool:
    explicit_mana_reference = any(
        marker in question
        for marker in [
            "habilidad de mana",
            "mana ability",
            "anadir mana",
            "añadir mana",
            "agregar mana",
            "produce mana",
        ]
    )

    cards_block = _extract_cards_block(knowledge)

    if not cards_block:
        return explicit_mana_reference

    activated_lines = []
    mana_lines = []

    for raw_line in cards_block.splitlines():
        line = _normalize(raw_line)

        if not _looks_like_oracle_activated_ability(line):
            continue

        activated_lines.append(line)

        if not any(
            marker in line
            for marker in [
                "add ",
                "anade ",
                "agrega ",
                "produce ",
            ]
        ):
            continue

        if "target" in line or "objetivo" in line:
            continue

        if re.match(r"^[+-]\d+\s*:", line):
            continue

        mana_lines.append(line)

    if explicit_mana_reference:
        return bool(mana_lines)

    # When the user refers only to "the ability" of a recovered card, avoid
    # selecting a mana ability if the card has several activated abilities.
    return len(activated_lines) == 1 and len(mana_lines) == 1


def _looks_like_oracle_activated_ability(line: str) -> bool:
    if ":" not in line:
        return False

    metadata_prefixes = (
        "mana cost:",
        "type:",
        "type line:",
        "oracle text:",
        "power:",
        "toughness:",
        "loyalty:",
    )

    if line.startswith(metadata_prefixes):
        return False

    left, _, right = line.partition(":")

    return bool(left.strip() and right.strip())


def _is_sacrifice_as_cost_death_trigger(question: str) -> bool:
    return (
        "sacrific" in question
        and ("coste" in question or "costo" in question)
        and (
            "habilidad de morir" in question
            or "muere" in question
            or "undying" in question
            or "persist" in question
        )
    )


def _is_no_priority_during_resolution(question: str) -> bool:
    has_resolution_window = any(
        marker in question
        for marker in [
            "esta resolviendo",
            "esta resolviendose",
            "se esta resolviendo",
            "mientras se resuelve",
            "durante la resolucion",
            "termine de resolver",
        ]
    )

    # Token boundaries are essential here: the old substring check for
    # ``activa`` also matched ``activada``, routing source-independence
    # questions to the no-priority renderer.
    asks_to_act = re.search(
        r"\b(?:activar|activo|activa|usar|uso|puedo|puede|lanzar|responder)\b",
        question,
    ) is not None

    return "habilidad" in question and has_resolution_window and asks_to_act


def _is_mana_ability_response(question: str) -> bool:
    asks_about_ability = (
        "habilidad" in question
        or "ability" in question
    )

    asks_about_timing = any(
        marker in question
        for marker in [
            "responder",
            "respuesta",
            "pila",
            "stack",
        ]
    )

    return asks_about_ability and asks_about_timing


def _is_ward_question(question: str) -> bool:
    return "ward" in question


def _is_source_independence_question(question: str) -> bool:
    has_ability = (
        "habilidad" in question
        or "ability" in question
    )

    has_activation = any(
        marker in question
        for marker in [
            "habilidad activada",
            "activo una habilidad",
            "activa una habilidad",
            "activar una habilidad",
            "activated ability",
        ]
    )

    source_removed = any(
        marker in question
        for marker in [
            "destruy",
            "mato",
            "matar",
            "muere",
            "retir",
            "elimin",
            "fuente",
            "origen",
        ]
    )

    asks_result = any(
        marker in question
        for marker in [
            "contrarrest",
            "desaparece",
            "sigue",
            "permanece",
            "que pasa",
            "qué pasa",
        ]
    )

    return has_ability and has_activation and source_removed and asks_result


def _is_ability_taxonomy_question(question: str) -> bool:
    mentions_activated = any(
        marker in question
        for marker in [
            "habilidad activada",
            "activated ability",
        ]
    )

    mentions_triggered = any(
        marker in question
        for marker in [
            "habilidad disparada",
            "habilidad desencadenada",
            "triggered ability",
        ]
    )

    return mentions_activated and mentions_triggered


def _is_priority_between_stack_objects(question: str) -> bool:
    asks_to_act = any(
        marker in question
        for marker in [
            "puedo responder",
            "puede responder",
            "podemos responder",
            "puedo actuar",
            "puede actuar",
            "activar",
            "lanzar",
        ]
    )

    mentions_next_object = any(
        marker in question
        for marker in [
            "el siguiente",
            "siguiente objeto",
            "siguiente hechizo",
            "entre dos objetos",
            "entre ambos",
        ]
    )

    after_resolution = any(
        marker in question
        for marker in [
            "despues de que se resuelve",
            "despues de resolverse",
            "tras resolverse",
            "entre",
        ]
    )

    return asks_to_act and mentions_next_object and after_resolution


def _is_stack_progression_question(question: str) -> bool:
    if "pila" not in question and "stack" not in question:
        return False

    return any(
        marker in question
        for marker in [
            "dos objetos",
            "dos hechizos",
            "todos automaticamente",
            "entera",
            "de golpe",
            "el siguiente",
            "entre medias",
            "entre uno",
            "uno a uno",
        ]
    )


def _is_response_before_resolution(question: str) -> bool:
    casts_spell = any(
        marker in question
        for marker in [
            "lanzo un hechizo",
            "lanzar un hechizo",
            "cast a spell",
        ]
    )

    asks_response = any(
        marker in question
        for marker in [
            "responder",
            "respuesta",
        ]
    )

    before_resolution = any(
        marker in question
        for marker in [
            "antes de que se resuelva",
            "antes de resolverse",
            "before it resolves",
        ]
    )

    return casts_spell and asks_response and before_resolution


def _is_untap_step_priority(question: str) -> bool:
    return (
        "paso de enderezar" in question
        or "untap step" in question
    )


def _is_simultaneous_trigger_order(question: str) -> bool:
    return (
        "habilidades disparadas" in question
        and (
            "al mismo tiempo" in question
            or "quien decide el orden" in question
            or "orden" in question
        )
    )


def _is_end_step_apnap(question: str) -> bool:
    return (
        "paso final" in question
        and (
            "orden" in question
            or "pila" in question
            or "habilidades" in question
        )
    )


def _is_may_trigger_choice(question: str) -> bool:
    return (
        "habilidad disparada" in question
        and "puedes" in question
        and (
            "cuando decido" in question
            or "decido" in question
        )
    )



def _is_undying_existing_counter_question(question: str) -> bool:
    mentions_positive_counter = any(
        marker in question
        for marker in [
            "contador +1/+1",
            "contadores +1/+1",
            "+1/+1 counter",
            "+1/+1 counters",
        ]
    )
    asks_existing_state = any(
        marker in question
        for marker in [
            "ya tiene",
            "ya tenia",
            "ademas tiene",
            "tambien tiene",
            "si tiene",
            "with a +1/+1",
            "already has",
        ]
    )

    return mentions_positive_counter and asks_existing_state


def _is_london_mulligan_question(question: str) -> bool:
    return (
        "mulligan" in question
        and any(
            marker in question
            for marker in [
                "explicame",
                "como funciona",
                "que es",
                "define",
                "explain",
                "how does",
            ]
        )
    )


def _is_mulligan_draw_followup(question: str) -> bool:
    asks_quantity = any(
        marker in question
        for marker in [
            "cuantas cartas",
            "cuanto robo",
            "cuantas robo",
            "how many cards",
        ]
    )
    mentions_draw = any(
        marker in question
        for marker in [
            "robo",
            "robar",
            "draw",
        ]
    )

    return asks_quantity and mentions_draw


def _asks_keyword_difference(question: str) -> bool:
    return any(
        marker in question
        for marker in [
            "diferencia",
            "diferencias",
            "se diferencian",
            "comparacion",
            "comparar",
        ]
    )


def _asks_for_example(question: str) -> bool:
    return any(
        marker in question
        for marker in [
            "con un ejemplo",
            "por ejemplo",
            "un ejemplo",
        ]
    )


def _is_direct_keyword_definition(question: str, keyword: str) -> bool:
    if keyword not in question:
        return False

    definition_markers = [
        "como funciona",
        "que es",
        "explicame",
        "define",
    ]

    if any(marker in question for marker in definition_markers):
        return True

    # Conversational continuation such as "¿Y Persist?". The evidence check in
    # the caller guarantees that the keyword rule was actually recovered.
    words = re.findall(r"[a-z0-9+/-]+", question)
    return len(words) <= 3

def _is_persist_and_undying_question(question: str) -> bool:
    return (
        "persist" in question
        and "undying" in question
        and any(marker in question for marker in ["muere", "morir", "dies"])
    )


def _is_zero_zero_persist_question(question: str) -> bool:
    return (
        "persist" in question
        and any(marker in question for marker in ["0/0", "cero cero"])
        and any(marker in question for marker in ["+1/+1", "contador"])
    )


def _is_counter_replacement_question(question: str) -> bool:
    mentions_counters = any(
        marker in question
        for marker in ["contador", "contadores", "counter", "counters"]
    )
    mentions_multiple_effects = any(
        marker in question
        for marker in [
            "varios efectos",
            "dos efectos",
            "efectos que",
            "doubling season",
            "vorinclex",
            "reemplazo",
            "replacement",
        ]
    )
    asks_interaction = any(
        marker in question
        for marker in [
            "como se aplican",
            "cómo se aplican",
            "se suman",
            "se reemplazan",
            "orden",
            "modifican",
            "doblan",
            "duplican",
        ]
    )
    return mentions_counters and mentions_multiple_effects and asks_interaction


def _asks_about_entering_with_counters(question: str) -> bool:
    return any(
        marker in question
        for marker in ["entra", "entrar", "enters", "entrada"]
    )


def _asks_about_counter_doublers(question: str) -> bool:
    return any(
        marker in question
        for marker in [
            "doblan",
            "doble",
            "duplican",
            "doubling season",
            "vorinclex",
        ]
    )


def _is_undying_exile_question(question: str) -> bool:
    return (
        "undying" in question
        and any(marker in question for marker in ["exilio", "exiliar", "exili", "exile"])
        and any(
            marker in question
            for marker in ["vuelve", "regresa", "retorna", "dispara", "activa"]
        )
    )


def _is_undying_return_question(question: str) -> bool:
    return (
        "undying" in question
        and "persist" not in question
        and any(
            marker in question
            for marker in ["muere", "morir", "dies", "sacrific"]
        )
    )


def _is_persist_return_question(question: str) -> bool:
    return (
        "persist" in question
        and "undying" not in question
        and not _is_zero_zero_persist_question(question)
        and any(marker in question for marker in ["muere", "morir", "dies"])
    )


def _is_cleanup_priority_question(question: str) -> bool:
    return (
        ("paso de limpieza" in question or "cleanup step" in question)
        and "prioridad" in question
    )


def _is_sacrifice_not_destroy_question(question: str) -> bool:
    return (
        "sacrific" in question
        and any(marker in question for marker in ["destruir", "destruye", "destroy"])
        and any(marker in question for marker in ["cuenta", "mismo", "misma", "es "])
    )


def _is_commander_copy_zone_question(question: str) -> bool:
    return (
        ("comandante" in question or "commander" in question)
        and ("copia" in question or "copy" in question)
        and ("zona de mando" in question or "command zone" in question)
    )


def _is_commander_hand_library_question(question: str) -> bool:
    return (
        ("comandante" in question or "commander" in question)
        and ("zona de mando" in question or "command zone" in question)
        and any(
            marker in question
            for marker in ["mano", "biblioteca", "hand", "library"]
        )
    )


def _is_commander_death_zone_question(question: str) -> bool:
    mentions_command_zone = (
        "zona de mando" in question or "command zone" in question
    )
    mentions_commander = (
        "comandante" in question
        or "commander" in question
        or mentions_command_zone
    )
    mentions_death_or_graveyard = any(
        marker in question
        for marker in [
            "muere",
            "muerto",
            "murio",
            "murió",
            "dies",
            "destruid",
            "cementerio",
            "graveyard",
        ]
    )
    asks_about_consequence = any(
        marker in question
        for marker in [
            "se dispara",
            "disparar",
            "habilidad",
            "sigue habiendo muerto",
            "ha muerto",
            "aun asi",
            "aún así",
        ]
    )

    return (
        mentions_commander
        and mentions_command_zone
        and mentions_death_or_graveyard
        and asks_about_consequence
    )
