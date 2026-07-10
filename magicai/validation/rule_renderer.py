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
    "exile": ["701.11", "701.11a"],
    "commander_designation": ["903.3"],
    "commander_graveyard_exile": ["903.9a"],
    "commander_hand_library": ["903.9b"],
    "replacement": ["614", "614."],
    "replacement_interaction": ["616", "616."],
    "counters": ["122", "122."],
    "state_based": ["704", "704."],
    "zero_toughness": ["704.5f"],
    "counter_cancellation": ["704.5q", "122.3"],
    "zone_change": ["400.7"],
    "persist": ["702.79", "702.79a"],
    "undying": ["702.93", "702.93a"],
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

    if _is_no_priority_during_resolution(q) and _has_rules(
        knowledge,
        ["priority"],
    ):
        return (
            "No. Mientras una habilidad se está resolviendo, los jugadores no "
            "tienen prioridad. Aunque esa habilidad ponga una carta en el campo "
            "de batalla, no puedes activar esa carta durante la resolución salvo "
            "que el propio efecto te indique explícitamente que lo hagas."
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

    if _is_source_independence_question(q) and _has_rules(
        knowledge,
        ["abilities", "stack"],
    ):
        return (
            "No. La habilidad no se contrarresta por destruir o retirar su "
            "fuente. Una vez activada, existe en la pila de forma independiente "
            "de la criatura que la originó; permanece en la pila y normalmente "
            "seguirá resolviéndose."
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
    return (
        "habilidad" in question
        and (
            "resolviendo" in question
            or "resolviendose" in question
            or "resolucion" in question
            or "termine de resolver" in question
        )
        and (
            "activar" in question
            or "activa" in question
            or "usar" in question
            or "puedo" in question
        )
    )


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
