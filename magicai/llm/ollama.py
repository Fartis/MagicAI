import os
import re

import requests

from magicai.validation import build_fallback_answer
from magicai.validation import validate_answer


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

    violations = validate_answer(
        answer=answer,
        knowledge=prompt,
    )

    if not violations:

        return answer

    retry_prompt = _build_retry_prompt(
        prompt=prompt,
        previous_answer=answer,
        violations=violations,
    )

    retry_answer = _chat(
        system=system,
        prompt=retry_prompt,
    )

    retry_answer = _clean_answer(retry_answer)

    retry_violations = validate_answer(
        answer=retry_answer,
        knowledge=prompt,
    )

    if not retry_violations:

        return retry_answer

    fallback_answer = build_fallback_answer(
        knowledge=prompt,
        violations=retry_violations,
    )

    if fallback_answer:

        return fallback_answer

    return retry_answer


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
                "num_predict": 512,
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


def _build_retry_prompt(
    prompt: str,
    previous_answer: str,
    violations: list[str],
) -> str:

    return (
        "/no_think\n\n"
        + prompt
        + "\n\n"
        + _build_dynamic_guardrails(prompt)
        + "\n\n"
        + "The previous answer failed validation.\n\n"
        + "Validation problems:\n"
        + _format_violations(violations)
        + "\n\n"
        + "Previous answer:\n"
        + previous_answer
        + "\n\n"
        + "Return a corrected final answer only. "
        + "Do not include analysis. "
        + "Use the same language as QUESTION. "
        + "Keep the answer under 90 words."
    )


def _format_violations(violations: list[str]) -> str:

    return "\n".join(
        f"- {violation}"
        for violation in violations
    )


def _build_dynamic_guardrails(prompt: str) -> str:

    source = prompt.lower()

    rules = [
        "Additional answer contract:",
        "- Use only the recovered CARD and RULE sources.",
        "- Do not use memorized card text, rulings, prices, legality, or strategy unless it appears in the recovered sources.",
        "- If CARDS are present, explain the visible Oracle text literally.",
        "- If the recovered Oracle text directly answers the question, prefer a short literal explanation instead of fallback.",
        "- Do not cite a rule number unless that rule appears in RULES and directly supports the sentence.",
        "- Do not invent named examples when no card example appears in the recovered sources.",
        "- Explain the recovered sources; do not add new rules or interactions.",
        "- If a symbol such as {T}, {C}, {W}, {U}, {B}, {R}, {G}, {X}, or +1/+1 is not explained by recovered sources, preserve the exact symbol instead of inventing a meaning.",
        "- Do not fail only because a symbol is not explained; describe the printed ability exactly.",
        "- In Spanish answers, translate 'costs' as 'cuesta', never as 'costa'.",
        "- In Spanish MTG explanations, say 'cuesta {X}' for mana cost.",
        "- In Spanish answers, translate 'draw a card' as 'roba una carta'.",
        "- In Spanish answers, translate 'tap this permanent' as 'girar este permanente' or 'girarlo'.",
        "- Translate generic mana as 'maná genérico' and colorless mana as 'maná incoloro'. Do not call generic mana 'maná general'.",
    ]

    if "any target" in source:

        rules.extend(
            [
                "- If Oracle text says 'any target', say 'cualquier objetivo válido'.",
                "- If Oracle text says 'any target', do not say it requires no target.",
                "- If Oracle text says 'any target', do not expand it into categories such as object, other object, card, permanent, creature, player, planeswalker, or battle unless those categories appear in recovered sources.",
            ]
        )

    if "deals" in source and "damage" in source:

        rules.extend(
            [
                "- Translate 'deals damage' as 'hace daño' or 'causa daño'.",
                "- Do not translate 'deals damage' as 'attacks', 'ataca', or 'puede atacar'.",
            ]
        )

    if "{t}: add" in source:

        rules.extend(
            [
                "- A card line with the pattern 'cost: effect' normally describes an activated ability, not a triggered ability.",
                "- Do not confuse a card's mana cost with the activation cost of an ability.",
                "- If Oracle text is '{T}: Add {C}{C}.', the activation cost is tapping the permanent, not paying its mana cost again.",
            ]
        )

    if "triggered ability" in source or "when " in source or "whenever " in source or " at " in source:

        rules.extend(
            [
                "- Translate 'triggered ability' as 'habilidad disparada' or 'habilidad desencadenada'.",
                "- Do not translate 'triggered ability' as 'habilidad activada'.",
                "- Do not call an ability 'habilidad disparada' unless the recovered sources contain 'triggered ability' or Oracle text with 'When', 'Whenever', or 'At'.",
            ]
        )

    if "activated ability" in source or ":" in source:

        rules.extend(
            [
                "- Translate 'activated ability' as 'habilidad activada'.",
            ]
        )

    if "dies" in source or "graveyard from the battlefield" in source:

        rules.extend(
            [
                "- Do not say a creature 'dies in the graveyard'. A creature dies when it is put into a graveyard from the battlefield.",
            ]
        )

    if "117." in source or "priority" in source or "prioridad" in source:

        rules.extend(
            [
                "- Do not say a player responds during the resolution of the original spell. Responses happen before it resolves, while players have priority and the spell or ability is on the stack.",
                "- A spell or ability resolves only after all players pass priority in succession.",
                "- After a player casts a spell, that player receives priority again; the opponent can respond once priority is passed before the spell resolves.",
            ]
        )

    if "whenever you sacrifice a permanent" in source:

        rules.extend(
            [
                "- If Oracle text says 'Whenever you sacrifice a permanent', you may explain that sacrificing a permanent causes that printed ability to apply, as long as you do not add extra effects.",
            ]
        )

    return "\n".join(rules)


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
