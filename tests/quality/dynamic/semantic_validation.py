from __future__ import annotations

import re
import unicodedata

from tests.quality.dynamic.models import DynamicScenario


def validate_dynamic_answer(
    scenario: DynamicScenario,
    answer: str,
) -> list[str]:
    if scenario.concept_id == "ward":
        return _validate_ward(answer)
    if scenario.concept_id == "source_independence":
        return _validate_source_independence(scenario, answer)
    return []


def _validate_ward(answer: str) -> list[str]:
    text = _normalize(answer)
    failures: list[str] = []
    if not re.search(r"\bward\b", text):
        failures.append("Ward is not identified.")
    if not any(marker in text for marker in ("habilidad disparada", "habilidad desencadenada", "triggered ability")):
        failures.append("Ward is not identified as a triggered ability.")
    if "pila" not in text and "stack" not in text:
        failures.append("Ward is not placed on the stack.")
    if "contrarrest" not in text and "counter" not in text:
        failures.append("The answer does not say what Ward counters.")
    if not (
        any(marker in text for marker in (
            "si no paga", "si no se paga", "a menos que pague",
            "unless that player pays", "unless its controller pays",
        ))
        or re.search(r"\bsi\b[^.]{0,100}\bno\s+paga\b", text)
    ):
        failures.append("The counter effect is not linked to failure to pay the Ward cost.")
    if re.search(r"\bward\s+se\s+activa\b|\bse\s+activa\s+ward\b", text):
        failures.append("Ward is incorrectly described as activated.")
    if any(marker in text for marker in (
        "responder durante su resolucion",
        "responder durante la resolucion de ward",
        "respond during its resolution",
    )):
        failures.append("The answer incorrectly allows responses during resolution.")
    if any(marker in text for marker in (
        "pagar para evitar que el hechizo se resuelva",
        "paga para evitar que el hechizo se resuelva",
        "pay to stop the spell from resolving",
    )):
        failures.append("The Ward payment is incorrectly described as stopping resolution.")
    return failures


def _validate_source_independence(
    scenario: DynamicScenario,
    answer: str,
) -> list[str]:
    text = _normalize(answer)
    failures: list[str] = []
    if "pila" not in text and "stack" not in text:
        failures.append("The activated ability is not kept on the stack.")
    if not any(marker in text for marker in (
        "independiente de su fuente",
        "no se contrarresta",
        "permanece en la pila",
        "independent of its source",
    )):
        failures.append("The answer does not establish source independence.")

    dependency = scenario.source_dependency
    if dependency == "source_object" and not any(marker in text for marker in (
        "puede no hacer nada",
        "esa parte puede no hacer nada",
        "no puede modificar",
        "ya no esta",
        "missing source",
    )):
        failures.append("A source-object effect is not qualified for a missing source.")
    elif dependency == "information" and not any(marker in text for marker in (
        "ultima informacion conocida",
        "last known information",
    )):
        failures.append("An information-dependent effect does not mention last known information.")
    elif dependency == "partial" and not any(marker in text for marker in (
        "parte",
        "todo lo posible",
        "puede no hacer nada",
        "as much as possible",
    )):
        failures.append("A partially source-dependent effect is not split into resolvable parts.")
    return failures


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", (text or "").casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.split())
