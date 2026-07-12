from magicai.llm.ollama import generate
from magicai.prompts.answer import SYSTEM_PROMPT
from magicai.validation import build_fallback_answer, validate_answer
from magicai.validation.rule_renderer import render_rule_answer
from magicai.validation.oracle_renderer import render_oracle_relation_answer
from magicai.validation.strategy_boundary import render_strategy_boundary_answer
from magicai.judge_result import (
    JudgeConfidence,
    JudgeOrigin,
    JudgeStatus,
    build_judge_result,
)


MAX_ATTEMPTS = 2


def generate_answer(knowledge: str) -> str:
    """Backward-compatible text-only answer entrypoint."""

    return generate_judge_result(knowledge).answer


def generate_judge_result(knowledge: str, context=None):
    """Generate a structured, source-grounded Judge result."""

    print("=" * 80)
    print("KNOWLEDGE SENT TO ANSWER GENERATOR")
    print("=" * 80)
    print(knowledge)
    print("=" * 80)

    question = getattr(context, "question", None) or _extract_question(knowledge)

    rendered_rule_answer = render_rule_answer(knowledge)

    if rendered_rule_answer:
        return build_judge_result(
            question=question,
            answer=rendered_rule_answer,
            status=JudgeStatus.ANSWERED,
            origin=JudgeOrigin.DETERMINISTIC_RULE,
            confidence=JudgeConfidence.HIGH,
            context=context,
        )

    rendered_oracle_relation = render_oracle_relation_answer(knowledge)

    if rendered_oracle_relation:
        return build_judge_result(
            question=question,
            answer=rendered_oracle_relation,
            status=JudgeStatus.ANSWERED,
            origin=JudgeOrigin.DETERMINISTIC_ORACLE,
            confidence=JudgeConfidence.HIGH,
            context=context,
        )

    strategy_boundary = render_strategy_boundary_answer(knowledge)

    if strategy_boundary:
        return build_judge_result(
            question=question,
            answer=strategy_boundary,
            status=JudgeStatus.STRATEGY_REQUIRED,
            origin=JudgeOrigin.STRATEGY_BOUNDARY,
            confidence=JudgeConfidence.HIGH,
            context=context,
            warnings=[
                "A strategic recommendation requires Deck Master; the Judge only validates recovered facts."
            ],
        )

    last_violations: list[str] = []
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
            return build_judge_result(
                question=question,
                answer=answer,
                status=JudgeStatus.ANSWERED,
                origin=JudgeOrigin.LLM_VALIDATED,
                confidence=JudgeConfidence.MEDIUM,
                context=context,
                validation_attempts=attempt,
            )

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

    fallback_answer = build_fallback_answer(
        knowledge,
        last_violations,
    )
    fallback_is_incomplete = _is_insufficient_fallback(fallback_answer)

    return build_judge_result(
        question=question,
        answer=fallback_answer,
        status=(
            JudgeStatus.INSUFFICIENT_EVIDENCE
            if fallback_is_incomplete
            else JudgeStatus.ANSWERED
        ),
        origin=JudgeOrigin.SAFE_FALLBACK,
        confidence=(
            JudgeConfidence.LOW
            if fallback_is_incomplete
            else JudgeConfidence.MEDIUM
        ),
        context=context,
        warnings=list(last_violations),
        validation_attempts=MAX_ATTEMPTS,
    )


def _extract_question(knowledge: str) -> str:
    marker = "QUESTION"
    if marker not in knowledge:
        return ""

    remainder = knowledge.split(marker, 1)[1]
    return remainder.split("=" * 10, 1)[0].strip()


def _is_insufficient_fallback(answer: str) -> bool:
    lower = answer.strip().lower()
    return lower.startswith(
        (
            "no he podido generar",
            "i could not generate",
        )
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
