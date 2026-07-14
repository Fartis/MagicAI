from tests.quality.dynamic.models import (
    DynamicConcept,
    EvaluationContract,
    QuestionTemplate,
)


CONCEPTS: tuple[DynamicConcept, ...] = (
    DynamicConcept(
        id="mana_ability",
        name="Mana ability does not use the stack",
        selector="mana_ability",
        tags=("dynamic", "mana-ability", "stack"),
        templates=(
            QuestionTemplate(
                id="mana-response",
                text=(
                    "{card} tiene esta habilidad activada: «{ability}». "
                    "¿es una habilidad de maná y puede mi rival responder?"
                ),
            ),
            QuestionTemplate(
                id="mana-stack",
                text=(
                    "Para {card}, la habilidad «{ability}» ¿usa la pila o se "
                    "resuelve sin dar oportunidad de responder?"
                ),
            ),
            QuestionTemplate(
                id="mana-priority",
                text=(
                    "Activo en {card} exactamente «{ability}». ¿Se pone esa "
                    "habilidad en la pila y recibimos prioridad?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("habilidad de maná", "pila"),
            required_any=(
                (
                    "no usa la pila",
                    "no va a la pila",
                    "no se coloca en la pila",
                    "sin pasar por la pila",
                ),
                (
                    "no se puede responder",
                    "no puedes responder",
                    "no puede responder",
                ),
            ),
            recommended_any=(
                ("se resuelve inmediatamente", "resuelve inmediatamente"),
            ),
            forbidden=(
                "sí usa la pila",
                "si usa la pila",
                "sí se puede responder",
                "si se puede responder",
                "se coloca en la pila y permite respuestas",
            ),
        ),
    ),
    DynamicConcept(
        id="ward",
        name="Ward is a triggered ability",
        selector="ward",
        tags=("dynamic", "ward", "triggered", "stack"),
        templates=(
            QuestionTemplate(
                id="ward-cost-or-trigger",
                text=(
                    "{card} tiene Ward y pasa a ser objetivo de un hechizo "
                    "rival. ¿Ward es un coste adicional o una habilidad "
                    "disparada a la que se puede responder?"
                ),
            ),
            QuestionTemplate(
                id="ward-stack",
                text=(
                    "Mi oponente hace objetivo a {card}, que tiene Ward. "
                    "¿La habilidad de Ward usa la pila y permite respuestas?"
                ),
            ),
            QuestionTemplate(
                id="ward-priority",
                text=(
                    "Cuando se dispara Ward de {card}, ¿los jugadores reciben "
                    "prioridad antes de que se resuelva?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("Ward", "pila"),
            required_any=(
                ("habilidad disparada", "habilidad desencadenada", "trigger"),
                ("responder", "prioridad"),
            ),
            recommended_any=(("sí", "si"),),
            forbidden=(
                "Ward es un coste adicional",
                "Ward es un costo adicional",
                "no se puede responder porque es un coste",
                "no usa la pila",
            ),
        ),
    ),
    DynamicConcept(
        id="source_independence",
        name="Activated ability survives its source",
        selector="source_independence_ability",
        tags=("dynamic", "activated-ability", "source", "stack"),
        templates=(
            QuestionTemplate(
                id="source-destroyed",
                text=(
                    "Activo en {card} la habilidad «{ability}» y después destruyen "
                    "ese permanente. ¿La habilidad desaparece de la pila?"
                ),
            ),
            QuestionTemplate(
                id="source-removed",
                text=(
                    "Después de activar en {card} la habilidad «{ability}», eliminan "
                    "su fuente. ¿Eso contrarresta automáticamente la habilidad?"
                ),
            ),
            QuestionTemplate(
                id="source-resolution",
                text=(
                    "La habilidad «{ability}» de {card} ya está en la pila y "
                    "destruyen la fuente. ¿Se contrarresta o qué puede hacer al "
                    "resolverse sin esa fuente?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("habilidad", "pila"),
            required_any=(
                ("no",),
                (
                    "no se contrarresta",
                    "permanece en la pila",
                    "sigue resolviéndose",
                    "seguirá resolviéndose",
                ),
                ("fuente", "origen"),
                (
                    "todo lo posible",
                    "puede no hacer nada",
                    "última información conocida",
                    "ultima informacion conocida",
                ),
            ),
            forbidden=(
                "desaparece de la pila",
                "se contrarresta automáticamente",
                "matar la fuente contrarresta",
            ),
        ),
    ),
    DynamicConcept(
        id="undying_exile",
        name="Exile does not trigger Undying",
        selector="undying",
        tags=("dynamic", "undying", "exile", "dies"),
        templates=(
            QuestionTemplate(
                id="undying-direct-exile",
                text=(
                    "Exilio la criatura {card} directamente desde el campo de "
                    "batalla. ¿Undying se dispara y la devuelve?"
                ),
            ),
            QuestionTemplate(
                id="undying-no-graveyard",
                text=(
                    "{card} tiene Undying, pero es exiliada en lugar de ir al "
                    "cementerio. ¿Vuelve con un contador +1/+1?"
                ),
            ),
            QuestionTemplate(
                id="undying-dies-definition",
                text=(
                    "Si {card} pasa del campo de batalla al exilio, "
                    "¿Undying se dispara o cuenta como que la criatura murió?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("Undying", "exilio", "cementerio"),
            required_any=(
                ("no se dispara", "no se activa", "no se desencadena"),
                ("no muere", "no va al cementerio", "no al cementerio"),
                ("no vuelve", "no regresa", "no la devuelve"),
            ),
            forbidden=(
                "vuelve al campo de batalla con un contador +1/+1",
                "Undying se dispara al ser exiliada",
                "sí vuelve",
            ),
        ),
    ),
    DynamicConcept(
        id="priority_during_resolution",
        name="No priority during resolution",
        selector=None,
        tags=("dynamic", "priority", "resolution", "rules-only"),
        templates=(
            QuestionTemplate(
                id="resolution-created-token",
                text=(
                    "Durante la resolución de una habilidad que crea una ficha, "
                    "¿puedo activar una habilidad de esa ficha antes de que "
                    "termine de resolverse?"
                ),
            ),
            QuestionTemplate(
                id="resolution-entered-permanent",
                text=(
                    "Mientras se resuelve una habilidad y entra un permanente, "
                    "¿puedo usar ese permanente antes de que termine la "
                    "resolución?"
                ),
            ),
            QuestionTemplate(
                id="resolution-response-window",
                text=(
                    "Una habilidad se está resolviendo y pone una criatura en "
                    "el campo de batalla. ¿Puedo responder o activar algo "
                    "durante esa resolución?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("prioridad", "resolución"),
            required_any=(
                ("no",),
                (
                    "no tienen prioridad",
                    "ningún jugador recibe prioridad",
                    "sin prioridad",
                ),
                (
                    "durante la resolución",
                    "mientras una habilidad se está resolviendo",
                    "mientras se resuelve",
                ),
            ),
            forbidden=(
                "sí puedes activarla durante la resolución",
                "si puedes activarla durante la resolución",
                "puedes responder durante la resolución",
            ),
        ),
    ),
    DynamicConcept(
        id="stack_objects_one_by_one",
        name="Stack resolves one object at a time",
        selector=None,
        tags=("dynamic", "stack", "priority", "rules-only"),
        templates=(
            QuestionTemplate(
                id="stack-two-objects",
                text=(
                    "Si hay dos objetos en la pila, ¿se resuelven los dos "
                    "automáticamente sin dar prioridad entre medias?"
                ),
            ),
            QuestionTemplate(
                id="stack-whole-at-once",
                text=(
                    "¿La pila entera se resuelve de golpe cuando todos los "
                    "jugadores pasan prioridad?"
                ),
            ),
            QuestionTemplate(
                id="stack-next-object",
                text=(
                    "Con varios hechizos en la pila, ¿el siguiente se resuelve "
                    "inmediatamente después del primero sin que nadie pueda "
                    "actuar entre uno y otro?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("pila", "prioridad"),
            required_any=(
                ("no",),
                ("uno a uno", "un objeto", "objeto de la pila"),
                ("entre", "después", "antes del siguiente"),
            ),
            forbidden=(
                "se resuelve toda de golpe",
                "se resuelven todos automáticamente",
                "sin dar prioridad entre",
            ),
        ),
    ),
    DynamicConcept(
        id="cleanup_priority",
        name="Cleanup step priority exception",
        selector=None,
        tags=("dynamic", "cleanup", "priority", "rules-only"),
        templates=(
            QuestionTemplate(
                id="cleanup-normal-priority",
                text=(
                    "En el paso de limpieza, después de descartar hasta el "
                    "tamaño máximo de mano, ¿los jugadores reciben prioridad "
                    "normalmente?"
                ),
            ),
            QuestionTemplate(
                id="cleanup-can-act",
                text=(
                    "Durante el paso de limpieza, ¿puedo lanzar hechizos o "
                    "activar habilidades porque el jugador activo recibe "
                    "prioridad?"
                ),
            ),
            QuestionTemplate(
                id="cleanup-exception",
                text=(
                    "¿En qué excepción del paso de limpieza llegan los "
                    "jugadores a recibir prioridad?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("paso de limpieza", "prioridad"),
            required_any=(
                ("normalmente no", "ningún jugador recibe prioridad"),
                ("acciones basadas en estado", "habilidades disparadas"),
                ("otro paso de limpieza", "nuevo paso de limpieza"),
            ),
            forbidden=(
                "siempre reciben prioridad",
                "reciben prioridad normalmente",
            ),
        ),
    ),
    DynamicConcept(
        id="commander_dies",
        name="Commander dies before moving to command zone",
        selector=None,
        tags=("dynamic", "commander", "dies", "zone", "rules-only"),
        templates=(
            QuestionTemplate(
                id="commander-destroyed",
                text=(
                    "Mi comandante es destruido, llega al cementerio y después "
                    "lo muevo a la zona de mando. ¿Se dispara una habilidad de "
                    "cuando muera?"
                ),
            ),
            QuestionTemplate(
                id="commander-death-trigger",
                text=(
                    "Si mi comandante muere y luego elijo ponerlo en la zona de "
                    "mando, ¿sigue contando como que murió para sus habilidades?"
                ),
            ),
            QuestionTemplate(
                id="commander-graveyard-first",
                text=(
                    "Un comandante va del campo de batalla al cementerio y a "
                    "continuación a la zona de mando. ¿Las habilidades de muerte "
                    "llegan a dispararse?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("comandante", "cementerio", "zona de mando"),
            required_any=(
                ("sí", "si"),
                ("muere", "cuando muera", "ha muerto"),
                ("acciones basadas en estado", "state-based"),
            ),
            forbidden=(
                "no se dispara",
                "no se considera que muera",
                "nunca llega al cementerio",
            ),
        ),
    ),
    DynamicConcept(
        id="commander_library_replacement",
        name="Commander hand or library replacement",
        selector=None,
        tags=("dynamic", "commander", "library", "replacement", "rules-only"),
        templates=(
            QuestionTemplate(
                id="commander-library-instead",
                text=(
                    "Si un efecto fuera a poner mi comandante en la biblioteca, "
                    "¿puedo enviarlo a la zona de mando en su lugar?"
                ),
            ),
            QuestionTemplate(
                id="commander-hand-replacement",
                text=(
                    "Mi comandante va a volver a mi mano. ¿La elección de ponerlo "
                    "en la zona de mando ocurre antes de que llegue a la mano?"
                ),
            ),
            QuestionTemplate(
                id="commander-library-arrival",
                text=(
                    "Cuando el comandante va a la biblioteca, ¿primero entra en "
                    "ella y después se mueve a la zona de mando, o se reemplaza "
                    "ese cambio de zona?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("comandante", "zona de mando"),
            required_any=(
                ("biblioteca", "mano"),
                ("efecto de reemplazo", "reemplazo"),
                ("en su lugar", "no llega"),
            ),
            forbidden=(
                "primero llega a la biblioteca",
                "primero llega a la mano",
                "solo puede hacerse después",
            ),
        ),
    ),
    DynamicConcept(
        id="commander_copy",
        name="Commander designation is not copied",
        selector=None,
        tags=("dynamic", "commander", "copy", "zone", "rules-only"),
        templates=(
            QuestionTemplate(
                id="commander-copy-dies",
                text=(
                    "Una criatura copia a mi comandante y después muere. ¿Esa "
                    "copia puede ir a la zona de mando?"
                ),
            ),
            QuestionTemplate(
                id="commander-copy-designation",
                text=(
                    "Si un permanente se convierte en una copia de un comandante, "
                    "¿también copia la condición de comandante y su acceso a la "
                    "zona de mando?"
                ),
            ),
            QuestionTemplate(
                id="commander-clone-zone",
                text=(
                    "Un clon copia exactamente a un comandante y es destruido. "
                    "¿Puedo poner el clon en la zona de mando?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("copia", "comandante", "zona de mando"),
            required_any=(
                ("no",),
                ("carta", "designación", "no es un valor copiable"),
                ("cementerio", "va al cementerio"),
                (
                    "ya era comandante",
                    "designada como comandante",
                    "por su propia designación",
                    "por su propia designacion",
                ),
            ),
            forbidden=(
                "la copia también es comandante",
                "sí puede ir a la zona de mando",
                "si puede ir a la zona de mando",
            ),
        ),
    ),
    DynamicConcept(
        id="persist",
        name="Persist returns with a minus counter",
        selector=None,
        tags=("dynamic", "persist", "dies", "counters", "rules-only"),
        templates=(
            QuestionTemplate(
                id="persist-basic-return",
                text=(
                    "Una criatura con Persist y sin contadores -1/-1 muere. "
                    "¿Cómo vuelve al campo de batalla?"
                ),
            ),
            QuestionTemplate(
                id="persist-trigger-condition",
                text=(
                    "Si una criatura con Persist muere sin tener un contador "
                    "-1/-1, ¿la habilidad se dispara y con qué contador regresa?"
                ),
            ),
            QuestionTemplate(
                id="persist-minus-counter",
                text=(
                    "Una criatura muere con Persist y no tenía contadores -1/-1. "
                    "¿Vuelve bajo el control de su dueño con un contador -1/-1?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("Persist", "-1/-1"),
            required_any=(
                ("muere", "cuando la criatura muere"),
                ("se dispara", "habilidad"),
                ("vuelve", "regresa", "retorna"),
            ),
            forbidden=(
                "contador +1/+1",
                "no vuelve",
                "no se dispara",
            ),
        ),
    ),
    DynamicConcept(
        id="persist_and_undying",
        name="Persist and Undying stack ordering",
        selector=None,
        tags=("dynamic", "persist", "undying", "stack", "rules-only"),
        templates=(
            QuestionTemplate(
                id="persist-undying-same-death",
                text=(
                    "Una criatura sin contadores tiene Persist y Undying y "
                    "muere. ¿Las dos habilidades la devuelven a la vez?"
                ),
            ),
            QuestionTemplate(
                id="persist-undying-order",
                text=(
                    "Si una criatura con Persist y Undying muere sin contadores, "
                    "¿quién elige el orden de ambas habilidades en la pila?"
                ),
            ),
            QuestionTemplate(
                id="persist-undying-second-trigger",
                text=(
                    "Persist y Undying se disparan cuando la misma criatura "
                    "muere sin contadores. ¿Qué ocurre con la habilidad que se "
                    "resuelve en segundo lugar?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("Persist", "Undying", "pila"),
            required_any=(
                ("dos habilidades", "ambas"),
                ("orden", "elige"),
                ("+1/+1",),
                ("-1/-1",),
            ),
            forbidden=(
                "las dos la devuelven a la vez",
                "vuelve infinitamente de forma automática",
            ),
        ),
    ),
    DynamicConcept(
        id="counter_replacement_order",
        name="Multiple counter replacement effects",
        selector=None,
        tags=("dynamic", "replacement", "counters", "rules-only"),
        templates=(
            QuestionTemplate(
                id="counter-two-replacements",
                text=(
                    "Dos efectos de reemplazo quieren cambiar cuántos contadores "
                    "recibe el mismo permanente. ¿Quién decide el orden?"
                ),
            ),
            QuestionTemplate(
                id="counter-apply-one-by-one",
                text=(
                    "Si varios efectos de reemplazo modifican el mismo evento de "
                    "poner contadores, ¿se aplican todos a la vez o uno después "
                    "de otro?"
                ),
            ),
            QuestionTemplate(
                id="counter-affected-controller",
                text=(
                    "Hay dos efectos que modifican los contadores que va a recibir "
                    "un permanente. ¿El controlador del objeto afectado elige el "
                    "orden en que se aplican?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("efectos de reemplazo", "contadores", "orden"),
            required_any=(
                ("controlador", "jugador afectado"),
                ("elige", "decide"),
                ("se aplica uno", "sucesivamente", "uno después"),
                ("precedencia", "categoría", "categoria", "616.1"),
            ),
            forbidden=(
                "son habilidades disparadas",
                "van a la pila",
                "se aplican simultáneamente",
            ),
        ),
    ),
    DynamicConcept(
        id="counters_as_enters",
        name="Counters modified as a permanent enters",
        selector=None,
        tags=("dynamic", "replacement", "enters", "counters", "rules-only"),
        templates=(
            QuestionTemplate(
                id="enters-counter-modification",
                text=(
                    "Un permanente va a entrar con contadores y dos efectos de "
                    "reemplazo modifican esa cantidad. ¿Se disparan o cambian el "
                    "propio evento de entrada?"
                ),
            ),
            QuestionTemplate(
                id="enters-counters-stack",
                text=(
                    "Dos efectos cambian los contadores con los que entra un "
                    "permanente. ¿Esas habilidades van a la pila o modifican la "
                    "entrada sin usarla?"
                ),
            ),
            QuestionTemplate(
                id="enters-counters-order",
                text=(
                    "Cuando varios efectos de reemplazo cambian los contadores "
                    "con los que va a entrar un permanente, ¿quién elige el orden "
                    "y cómo se aplican?"
                ),
            ),
        ),
        contract=EvaluationContract(
            required_all=("entra", "contadores", "efectos de reemplazo"),
            required_any=(
                ("no se disparan", "no van a la pila", "sin utilizar la pila"),
                ("modifican", "evento de entrada"),
                ("orden", "controlador", "propietario"),
            ),
            forbidden=(
                "se disparan al entrar",
                "son habilidades disparadas",
            ),
        ),
    )
)


_CONCEPT_INDEX = {
    concept.id: concept
    for concept in CONCEPTS
}


def get_concepts(concept_ids: list[str] | tuple[str, ...] | None = None):
    if not concept_ids:
        return list(CONCEPTS)

    normalized = [concept_id.strip().lower() for concept_id in concept_ids]
    unknown = [concept_id for concept_id in normalized if concept_id not in _CONCEPT_INDEX]

    if unknown:
        raise ValueError(
            "Unknown dynamic concept(s): "
            + ", ".join(sorted(set(unknown)))
        )

    return [_CONCEPT_INDEX[concept_id] for concept_id in normalized]
