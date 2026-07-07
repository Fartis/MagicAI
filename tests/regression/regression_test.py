#!/usr/bin/env python3
"""
MagicAI Regression Suite

Ejecuta conversaciones completas contra MagicAI y genera
un informe de regresión para detectar cambios de comportamiento.

Genera automáticamente:

tests/regression/output/<fecha>/

    regression.txt
    responses.txt
    summary.txt
    environment.txt
"""

from __future__ import annotations

import os
import sys
import time
import platform

from pathlib import Path
from datetime import datetime

from magicai.assistant import MagicAI
from magicai.conversation import Conversation

from regression_cases import TESTS

###############################################################################
#
# Configuración
#
###############################################################################

RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_DIR = Path("tests") / "regression" / "output" / RUN_ID

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REGRESSION_FILE = OUTPUT_DIR / "regression.txt"

RESPONSES_FILE = OUTPUT_DIR / "responses.txt"

SUMMARY_FILE = OUTPUT_DIR / "summary.txt"

ENVIRONMENT_FILE = OUTPUT_DIR / "environment.txt"

###############################################################################
#
# Asistente
#
###############################################################################

assistant = MagicAI()

###############################################################################
#
# Estadísticas
#
###############################################################################

stats = {"tests": 0, "questions": 0, "errors": 0, "total_time": 0.0}

###############################################################################
#
# Buffers de salida
#
###############################################################################

regression_lines = []

responses_lines = []

summary_lines = []

environment_lines = []

###############################################################################
#
# Cabecera
#
###############################################################################

header = [
    "=" * 80,
    "MagicAI Regression Suite",
    "=" * 80,
    "",
    f"Run ID : {RUN_ID}",
    f"Fecha  : {datetime.now()}",
    "",
]

regression_lines.extend(header)

responses_lines.extend(header)

summary_lines.extend(header)

environment_lines.extend(header)

###############################################################################
#
# Información del entorno
#
###############################################################################

environment_lines.extend([
    "Python",
    f"    {platform.python_version()}",
    "",
    "Sistema",
    f"    {platform.system()} {platform.release()}",
    "",
    "Arquitectura",
    f"    {platform.machine()}",
    "",
    "Ejecutable",
    f"    {sys.executable}",
    "",
    "Directorio",
    f"    {os.getcwd()}",
    "",
])

###############################################################################
#
# Consola
#
###############################################################################

print()

print("=" * 80)
print(" MagicAI Regression Suite")
print("=" * 80)

print()

print(f"Run ID : {RUN_ID}")

print()

###############################################################################
#
# Funciones auxiliares
#
###############################################################################


def separator(buffer):

    buffer.append("")
    buffer.append("-" * 80)
    buffer.append("")


def title(buffer, text):

    buffer.append("")
    buffer.append("=" * 80)
    buffer.append(text)
    buffer.append("=" * 80)
    buffer.append("")


def write_state(buffer, conversation):

    buffer.append("STATE")
    buffer.append("")

    #
    # Cartas activas
    #

    try:

        names = [card.name for card in conversation.active_cards]

    except Exception:

        names = []

    buffer.append(f"Cards      : {names}")

    #
    # Keywords
    #

    if hasattr(conversation, "active_keywords"):

        buffer.append(f"Keywords   : {conversation.active_keywords}")

    #
    # Reglas
    #

    if hasattr(conversation, "active_rules"):

        buffer.append(f"Rules      : {conversation.active_rules}")

    #
    # Último intent
    #

    if hasattr(conversation, "last_intent"):

        buffer.append(f"Intent     : {conversation.last_intent}")

    #
    # Historial
    #

    if hasattr(conversation, "history"):

        buffer.append(f"History    : {len(conversation.history)}")

    buffer.append("")


def write_question(buffer, question):

    buffer.append("USER")
    buffer.append("")
    buffer.append(question)
    buffer.append("")


def write_answer(buffer, answer):

    buffer.append("ASSISTANT")
    buffer.append("")
    buffer.append(answer)
    buffer.append("")


def write_elapsed(buffer, elapsed):

    buffer.append(f"Elapsed    : {elapsed:.2f}s")

    buffer.append("")


###############################################################################
#
# Ejecución de una pregunta
#
###############################################################################


def execute_question(
    conversation,
    question,
):

    start = time.perf_counter()

    error = None

    try:

        answer = assistant.ask(
            conversation,
            question,
        )

    except Exception as ex:

        answer = ""

        error = ex

    elapsed = time.perf_counter() - start

    return (
        answer,
        error,
        elapsed,
    )


###############################################################################
#
# Impresión por consola
#
###############################################################################


def print_progress(
    test_name,
    question,
):

    print()

    print(f"[{test_name}]")

    print(f"  USER : {question}")


def print_result(
    elapsed,
    error,
):

    if error is None:

        print(f"  OK ({elapsed:.2f}s)")

    else:

        print(f"  ERROR ({elapsed:.2f}s)")

        print(error)
        
###############################################################################
#
# Ejecución de la batería de pruebas
#
###############################################################################

print()
print("Executing regression suite...")
print()

for index, test in enumerate(TESTS, start=1):

    stats["tests"] += 1

    conversation = Conversation()

    title(
        regression_lines,
        f"TEST {index}: {test['name']}",
    )

    title(
        responses_lines,
        f"TEST {index}: {test['name']}",
    )

    print(f"[{index}/{len(TESTS)}] {test['name']}")

    for question in test["questions"]:

        stats["questions"] += 1

        print_progress(
            test["name"],
            question,
        )

        answer, error, elapsed = execute_question(
            conversation,
            question,
        )

        stats["total_time"] += elapsed

        if error is not None:

            stats["errors"] += 1

        #
        # regression.txt
        #

        write_question(
            regression_lines,
            question,
        )

        if error is None:

            write_answer(
                regression_lines,
                answer,
            )

        else:

            write_answer(
                regression_lines,
                f"ERROR: {error}",
            )

        write_state(
            regression_lines,
            conversation,
        )

        write_elapsed(
            regression_lines,
            elapsed,
        )

        separator(regression_lines, )

        #
        # responses.txt
        #

        write_question(
            responses_lines,
            question,
        )

        if error is None:

            write_answer(
                responses_lines,
                answer,
            )

        else:

            write_answer(
                responses_lines,
                f"ERROR: {error}",
            )

        separator(responses_lines, )

        #
        # Consola
        #

        print_result(
            elapsed,
            error,
        )

    print()

###############################################################################
#
# (Preparado para futuras versiones)
#
###############################################################################

#
# En el futuro guardaremos aquí el conocimiento enviado al LLM.
#
# OUTPUT_DIR /
#
#     knowledge.txt
#
# De momento dejamos preparada la estructura.
#

KNOWLEDGE_FILE = OUTPUT_DIR / "knowledge.txt"

knowledge_lines = [
    "=" * 80,
    "MagicAI Knowledge Log",
    "=" * 80,
    "",
    "Esta versión todavía no registra el conocimiento enviado al LLM.",
    "",
    "Se implementará cuando KnowledgeBuilder exponga el contexto generado.",
    "",
]

KNOWLEDGE_FILE.write_text(
    "\n".join(knowledge_lines),
    encoding="utf8",
)

###############################################################################
#
# Resumen por consola
#
###############################################################################

print()

print("=" * 80)
print(" Regression finished")
print("=" * 80)

print()

print(f"Run ID            : {RUN_ID}")

print(f"Tests             : {stats['tests']}")

print(f"Questions         : {stats['questions']}")

print(f"Errors            : {stats['errors']}")

print(f"Total time        : {stats['total_time']:.2f}s")

if stats["questions"]:

    print(f"Average time      : "
          f"{stats['total_time']/stats['questions']:.2f}s")

print()

print("Generated files:")

print(f"  {REGRESSION_FILE}")

print(f"  {RESPONSES_FILE}")

print(f"  {SUMMARY_FILE}")

print(f"  {ENVIRONMENT_FILE}")

print(f"  {KNOWLEDGE_FILE}")

print()

print("=" * 80)

print("Done.")

print("=" * 80)

print()
