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
                    "Cuando activo la habilidad de maná de {card}, "
                    "¿mi rival puede responder antes de que se añada el maná?"
                ),
            ),
            QuestionTemplate(
                id="mana-stack",
                text=(
                    "¿La habilidad de maná de {card} usa la pila o se "
                    "resuelve sin dar oportunidad de responder?"
                ),
            ),
            QuestionTemplate(
                id="mana-priority",
                text=(
                    "Activo {card} para añadir maná. ¿Se pone esa habilidad "
                    "en la pila y recibimos prioridad para responder?"
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
        selector="activated_nonmana",
        tags=("dynamic", "activated-ability", "source", "stack"),
        templates=(
            QuestionTemplate(
                id="source-destroyed",
                text=(
                    "Activo una habilidad de {card} y después destruyen ese "
                    "permanente. ¿La habilidad desaparece de la pila?"
                ),
            ),
            QuestionTemplate(
                id="source-removed",
                text=(
                    "Después de activar una habilidad de {card}, eliminan su "
                    "fuente. ¿Eso contrarresta automáticamente la habilidad?"
                ),
            ),
            QuestionTemplate(
                id="source-resolution",
                text=(
                    "Una habilidad activada de {card} ya está en la pila y "
                    "destruyen la carta. ¿Se contrarresta o deja de resolverse "
                    "por perder su fuente?"
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
