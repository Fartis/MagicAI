import os
import re

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/chat",
)

MODEL = os.getenv(
    "MAGICAI_MODEL",
    "qwen3:8b",
)


def generate(system: str, prompt: str):

    final_prompt = _prepare_prompt(prompt)

    answer = _chat(
        system=system,
        prompt=final_prompt,
    )

    answer = _clean_answer(answer)

    if _needs_retry(answer, prompt):

        retry_prompt = _build_retry_prompt(
            prompt=prompt,
            previous_answer=answer,
        )

        answer = _chat(
            system=system,
            prompt=retry_prompt,
        )

        answer = _clean_answer(answer)

    return answer


def _chat(system: str, prompt: str) -> str:

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "stream": False,
            "keep_alive": "30m",
            "messages": [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "options": {
                "temperature": 0,
                "top_p": 0.8,
                "num_predict": 384,
            },
        },
        timeout=300,
    )

    response.raise_for_status()

    payload = response.json()

    message = payload.get("message", {})

    return message.get("content", "")


def _prepare_prompt(prompt: str) -> str:

    return (
        "/no_think\n\n"
        + prompt
        + "\n\n"
        + _build_dynamic_guardrails(prompt)
        + "\n\n"
        + "Return only the final answer. "
        + "Do not include reasoning, analysis or hidden thoughts. "
        + "Answer in the same language as QUESTION. "
        + "Keep the answer under 90 words."
    )


def _build_retry_prompt(prompt: str, previous_answer: str) -> str:

    return (
        "/no_think\n\n"
        + prompt
        + "\n\n"
        + _build_dynamic_guardrails(prompt)
        + "\n\n"
        + "The previous answer was empty, incomplete, in the wrong language, "
        + "or contradicted the provided rules.\n\n"
        + "Previous answer:\n"
        + previous_answer
        + "\n\n"
        + "Return a corrected final answer only. "
        + "Do not include analysis. "
        + "Use the same language as QUESTION. "
        + "Keep the answer under 90 words."
    )


def _build_dynamic_guardrails(prompt: str) -> str:

    guardrails = []

    if "Exile" in prompt and "701.13a" in prompt:

        guardrails.append(
            "The provided Exile rule says that exiling an object moves it "
            "to the exile zone. Never say that exiling moves the object "
            "to the graveyard or cementerio."
        )

    if "Sacrifice" in prompt and "701.21a" in prompt:

        guardrails.append(
            "The provided Sacrifice rule says that sacrificing a permanent "
            "moves it from the battlefield to its owner's graveyard. "
            "If the sacrificed permanent is a creature, the creature dies. "
            "Do not say that the player dies."
        )

    if "700.4" in prompt:

        guardrails.append(
            "The provided dies rule says that dies means being put into "
            "a graveyard from the battlefield."
        )

    if not guardrails:

        return ""

    return "\n".join(
        [
            "Additional answer guardrails:",
            *[
                f"- {guardrail}"
                for guardrail in guardrails
            ],
        ]
    )


def _clean_answer(answer: str) -> str:

    if not answer:

        return ""

    answer = re.sub(
        r"<think>.*?</think>",
        "",
        answer,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return answer.strip()


def _needs_retry(answer: str, prompt: str) -> bool:

    if not answer:

        return True

    if len(answer.split()) < 6:

        return True

    if _looks_incomplete(answer):

        return True

    if _is_spanish_question(prompt) and _looks_like_wrong_language(answer):

        return True

    if _is_spanish_question(prompt) and _contains_bad_spanish_terms(answer):

        return True

    if _is_exile_context(prompt) and _contradicts_exile_rule(answer):

        return True

    return False


def _looks_incomplete(answer: str) -> bool:

    text = answer.strip()

    if not text:

        return True

    unfinished_endings = (
        " con",
        " de",
        " que",
        " si",
        " porque",
        " cuando",
        " with",
        " of",
        " that",
        " because",
        " when",
    )

    lower = text.lower()

    if lower.endswith(unfinished_endings):

        return True

    if text[-1] not in ".!?…":

        return True

    return False


def _is_spanish_question(prompt: str) -> bool:

    question = _extract_question(prompt)

    lower = question.lower()

    spanish_markers = [
        "¿",
        "qué",
        "que ",
        "si ",
        "sacrifico",
        "muere",
        "exilio",
        "lanzar",
        "campo de batalla",
    ]

    return any(
        marker in lower
        for marker in spanish_markers
    )


def _extract_question(prompt: str) -> str:

    match = re.search(
        r"QUESTION\s+(.*?)(?:={10,}|$)",
        prompt,
        flags=re.DOTALL,
    )

    if not match:

        return ""

    return match.group(1).strip()


def _looks_like_wrong_language(answer: str) -> bool:

    lower = answer.strip().lower()

    english_starts = (
        "if ",
        "when ",
        "exiling ",
        "sacrificing ",
        "young wolf is ",
        "you ",
    )

    if lower.startswith(english_starts):

        return True

    english_phrases = (
        "does not trigger",
        "if you exile",
        "when it dies",
    )

    return any(
        phrase in lower
        for phrase in english_phrases
    )


def _contains_bad_spanish_terms(answer: str) -> bool:

    lower = answer.lower()

    bad_terms = [
        "tumba",
        "gravedad",
        "tumba de batalla",
    ]

    return any(
        term in lower
        for term in bad_terms
    )


def _is_exile_context(prompt: str) -> bool:

    return (
        "Exile" in prompt
        and "701.13a" in prompt
    )


def _contradicts_exile_rule(answer: str) -> bool:

    lower = answer.lower()

    bad_patterns = [
        "exiliarlo al cementerio",
        "exiliarlo a cementerio",
        "exiliar a young wolf lo movería al cementerio",
        "exiliar a young wolf lo mueve al cementerio",
        "exilias a young wolf lo movería al cementerio",
        "exilias a young wolf lo mueve al cementerio",
        "lo movería al cementerio",
        "lo mueve al cementerio",
        "lo coloca en el cementerio",
        "es colocada en el cementerio",
        "es colocado en el cementerio",
    ]

    return any(
        pattern in lower
        for pattern in bad_patterns
    )