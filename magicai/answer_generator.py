from magicai.llm.ollama import generate
from magicai.prompts.answer import SYSTEM_PROMPT
from magicai.validation import build_fallback_answer, validate_answer
from magicai.validation.rule_renderer import render_rule_answer
from magicai.validation.oracle_renderer import render_oracle_relation_answer
from magicai.validation.strategy_boundary import render_strategy_boundary_answer


MAX_ATTEMPTS = 2


def generate_answer(knowledge: str) -> str:
    """
    Genera una respuesta utilizando únicamente el conocimiento proporcionado.

    Flujo:
    1. Intenta renderizadores deterministas de reglas y relaciones Oracle.
    2. Si no aplican, genera respuesta con el LLM.
    3. Valida la respuesta contra las fuentes recuperadas.
    4. Si falla, reintenta con feedback de validación.
    5. Si sigue fallando, devuelve fallback seguro basado en fuentes.
    """

    print("=" * 80)
    print("KNOWLEDGE SENT TO LLM")
    print("=" * 80)
    print(knowledge)
    print("=" * 80)

    rendered_rule_answer = render_rule_answer(knowledge)

    if rendered_rule_answer:

        return rendered_rule_answer

    rendered_oracle_relation = render_oracle_relation_answer(knowledge)

    if rendered_oracle_relation:

        return rendered_oracle_relation

    strategy_boundary = render_strategy_boundary_answer(knowledge)

    if strategy_boundary:

        return strategy_boundary

    last_answer = ""
    last_violations = []

    prompt = knowledge

    for attempt in range(1, MAX_ATTEMPTS + 1):

        response = generate(
            SYSTEM_PROMPT,
            prompt,
        )

        answer = response.strip()

        violations = validate_answer(
            answer,
            knowledge,
        )

        if not violations:

            return answer

        last_answer = answer
        last_violations = violations

        print("=" * 80)
        print(f"VALIDATION FAILED attempt {attempt}")
        print("=" * 80)

        for violation in violations:

            print(f"- {violation}")

        print("=" * 80)

        prompt = _build_retry_prompt(
            knowledge=knowledge,
            previous_answer=answer,
            violations=violations,
        )

    return build_fallback_answer(
        knowledge,
        last_violations,
    )


def _build_retry_prompt(
    knowledge: str,
    previous_answer: str,
    violations: list[str],
) -> str:

    return (
        knowledge
        + "\n\n"
        + "=" * 60
        + "\n"
        + "VALIDATION FEEDBACK\n"
        + "\n"
        + "The previous answer was rejected by the validator.\n"
        + "Generate a new answer using only the recovered CARD and RULE sources.\n"
        + "Do not repeat the rejected mistakes.\n"
        + "\n"
        + "Rejected answer:\n"
        + previous_answer
        + "\n\n"
        + "Validation violations:\n"
        + "\n".join(f"- {violation}" for violation in violations)
        + "\n"
    )
