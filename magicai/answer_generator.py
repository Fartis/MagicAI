from magicai.llm.ollama import generate
from magicai.prompts.answer import SYSTEM_PROMPT
from magicai.validation import build_fallback_answer, validate_answer


MAX_ATTEMPTS = 2


def generate_answer(knowledge: str) -> str:
    """
    Genera una respuesta utilizando únicamente el conocimiento proporcionado.

    Flujo:
    1. Genera respuesta con el LLM.
    2. Valida la respuesta contra las fuentes recuperadas.
    3. Si falla, reintenta con feedback de validación.
    4. Si sigue fallando, devuelve fallback seguro basado en fuentes.
    """

    print("=" * 80)
    print("KNOWLEDGE SENT TO LLM")
    print("=" * 80)
    print(knowledge)
    print("=" * 80)

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
