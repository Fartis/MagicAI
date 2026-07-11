#!/usr/bin/env python3
"""
MagicAI Parallel Regression Suite

Ejecuta cada escenario de regresión en un proceso separado.

Importante:

- Las preguntas dentro de un mismo escenario se ejecutan en orden.
- Cada escenario tiene su propia Conversation().
- Cada proceso tiene su propio MagicAI().
- El paralelismo se controla con MAGICAI_TEST_WORKERS.

Ejemplo:

    MAGICAI_TEST_WORKERS=2 python tests/regression/regression_parallel.py
"""

from __future__ import annotations

import io
import os
import sys
import time
import platform
import traceback
import contextlib

from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

if __package__:
    from .regression_cases import TESTS
else:
    # Compatibilidad con ejecución directa:
    # python tests/regression/regression_parallel.py.py
    from regression_cases import TESTS


###############################################################################
#
# Configuración
#
###############################################################################

RUN_ID = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

OUTPUT_DIR = Path("tests") / "regression" / "output" / f"{RUN_ID}_parallel"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REGRESSION_FILE = OUTPUT_DIR / "regression.txt"
RESPONSES_FILE = OUTPUT_DIR / "responses.txt"
SUMMARY_FILE = OUTPUT_DIR / "summary.txt"
ENVIRONMENT_FILE = OUTPUT_DIR / "environment.txt"

DEFAULT_WORKERS = 2

MAX_WORKERS = int(
    os.getenv(
        "MAGICAI_TEST_WORKERS",
        str(DEFAULT_WORKERS),
    )
)


###############################################################################
#
# Worker
#
###############################################################################


def run_test_case(index: int, total: int, test: dict) -> dict:

    #
    # Imports dentro del worker para que cada proceso tenga su propio estado.
    #

    from magicai.assistant import MagicAI
    from magicai.conversation import Conversation

    assistant = MagicAI()
    conversation = Conversation()

    regression_lines = []
    responses_lines = []
    console_lines = []

    stats = {
        "tests": 1,
        "questions": 0,
        "errors": 0,
        "total_time": 0.0,
    }

    test_name = test["name"]

    _title(
        regression_lines,
        f"TEST {index}: {test_name}",
    )

    _title(
        responses_lines,
        f"TEST {index}: {test_name}",
    )

    console_lines.append(
        f"[{index}/{total}] {test_name}"
    )

    for question in test["questions"]:

        stats["questions"] += 1

        console_lines.append("")
        console_lines.append(f"[{test_name}]")
        console_lines.append(f"  USER : {question}")

        start = time.perf_counter()

        answer = ""
        error_text = None

        #
        # Capturamos el stdout interno de assistant.ask().
        # En procesos separados esto es seguro.
        #

        internal_log = io.StringIO()

        try:

            with contextlib.redirect_stdout(internal_log):

                answer = assistant.ask(
                    conversation,
                    question,
                )

        except Exception:

            error_text = traceback.format_exc()

        elapsed = time.perf_counter() - start

        stats["total_time"] += elapsed

        if error_text is not None:

            stats["errors"] += 1

        #
        # regression.txt
        #

        _write_question(
            regression_lines,
            question,
        )

        if internal_log.getvalue().strip():

            regression_lines.append("INTERNAL LOG")
            regression_lines.append("")
            regression_lines.append(internal_log.getvalue().strip())
            regression_lines.append("")

        if error_text is None:

            _write_answer(
                regression_lines,
                answer,
            )

        else:

            _write_answer(
                regression_lines,
                f"ERROR:\n{error_text}",
            )

        _write_state(
            regression_lines,
            conversation,
        )

        regression_lines.append(f"Elapsed    : {elapsed:.2f}s")
        _separator(regression_lines)

        #
        # responses.txt
        #

        _write_question(
            responses_lines,
            question,
        )

        if error_text is None:

            _write_answer(
                responses_lines,
                answer,
            )

        else:

            _write_answer(
                responses_lines,
                f"ERROR:\n{error_text}",
            )

        _separator(responses_lines)

        #
        # Console summary
        #

        if error_text is None:

            console_lines.append(f"  OK ({elapsed:.2f}s)")

        else:

            console_lines.append(f"  ERROR ({elapsed:.2f}s)")

    return {
        "index": index,
        "name": test_name,
        "stats": stats,
        "regression_lines": regression_lines,
        "responses_lines": responses_lines,
        "console_lines": console_lines,
    }


###############################################################################
#
# Helpers
#
###############################################################################


def _separator(buffer: list[str]):

    buffer.append("")
    buffer.append("-" * 80)
    buffer.append("")


def _title(buffer: list[str], text: str):

    buffer.append("")
    buffer.append("=" * 80)
    buffer.append(text)
    buffer.append("=" * 80)
    buffer.append("")


def _write_question(buffer: list[str], question: str):

    buffer.append("USER")
    buffer.append("")
    buffer.append(question)
    buffer.append("")


def _write_answer(buffer: list[str], answer: str):

    buffer.append("ASSISTANT")
    buffer.append("")
    buffer.append(answer)
    buffer.append("")


def _write_state(buffer: list[str], conversation):

    buffer.append("STATE")
    buffer.append("")

    try:

        names = [
            card.name
            for card in conversation.active_cards
        ]

    except Exception:

        names = []

    buffer.append(f"Cards      : {names}")

    if hasattr(conversation, "active_keywords"):

        buffer.append(f"Keywords   : {conversation.active_keywords}")

    if hasattr(conversation, "active_rules"):

        buffer.append(f"Rules      : {conversation.active_rules}")

    if hasattr(conversation, "last_intent"):

        buffer.append(f"Intent     : {conversation.last_intent}")

    if hasattr(conversation, "history"):

        buffer.append(f"History    : {len(conversation.history)}")

    buffer.append("")


def _build_header() -> list[str]:

    return [
        "=" * 80,
        "MagicAI Parallel Regression Suite",
        "=" * 80,
        "",
        f"Run ID  : {RUN_ID}",
        f"Fecha   : {datetime.now()}",
        f"Workers : {MAX_WORKERS}",
        "",
    ]


###############################################################################
#
# Main
#
###############################################################################


def main():

    global_stats = {
        "tests": 0,
        "questions": 0,
        "errors": 0,
        "total_time": 0.0,
    }

    wall_start = time.perf_counter()

    header = _build_header()

    regression_lines = list(header)
    responses_lines = list(header)
    summary_lines = list(header)

    environment_lines = list(header)

    environment_lines.extend(
        [
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
        ]
    )

    print()
    print("=" * 80)
    print(" MagicAI Parallel Regression Suite")
    print("=" * 80)
    print()
    print(f"Run ID  : {RUN_ID}")
    print(f"Workers : {MAX_WORKERS}")
    print()
    print("Executing regression suite...")
    print()

    futures = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:

        for index, test in enumerate(TESTS, start=1):

            futures.append(
                executor.submit(
                    run_test_case,
                    index,
                    len(TESTS),
                    test,
                )
            )

        results = []

        for future in as_completed(futures):

            result = future.result()

            results.append(result)

            for line in result["console_lines"]:

                print(line)

            print()

    #
    # Ordenamos por índice para que los ficheros salgan estables.
    #

    results.sort(
        key=lambda item: item["index"]
    )

    for result in results:

        stats = result["stats"]

        global_stats["tests"] += stats["tests"]
        global_stats["questions"] += stats["questions"]
        global_stats["errors"] += stats["errors"]
        global_stats["total_time"] += stats["total_time"]

        regression_lines.extend(
            result["regression_lines"]
        )

        responses_lines.extend(
            result["responses_lines"]
        )

    wall_elapsed = time.perf_counter() - wall_start

    summary_lines.extend(
        [
            "Summary",
            "",
            f"Tests             : {global_stats['tests']}",
            f"Questions         : {global_stats['questions']}",
            f"Errors            : {global_stats['errors']}",
            f"Model time total  : {global_stats['total_time']:.2f}s",
            f"Wall time         : {wall_elapsed:.2f}s",
            "",
        ]
    )

    if global_stats["questions"]:

        summary_lines.append(
            "Average model time: "
            f"{global_stats['total_time'] / global_stats['questions']:.2f}s"
        )

        summary_lines.append("")

    REGRESSION_FILE.write_text(
        "\n".join(regression_lines),
        encoding="utf8",
    )

    RESPONSES_FILE.write_text(
        "\n".join(responses_lines),
        encoding="utf8",
    )

    SUMMARY_FILE.write_text(
        "\n".join(summary_lines),
        encoding="utf8",
    )

    ENVIRONMENT_FILE.write_text(
        "\n".join(environment_lines),
        encoding="utf8",
    )

    print()
    print("=" * 80)
    print(" Parallel regression finished")
    print("=" * 80)
    print()
    print(f"Run ID            : {RUN_ID}")
    print(f"Workers           : {MAX_WORKERS}")
    print(f"Tests             : {global_stats['tests']}")
    print(f"Questions         : {global_stats['questions']}")
    print(f"Errors            : {global_stats['errors']}")
    print(f"Model time total  : {global_stats['total_time']:.2f}s")
    print(f"Wall time         : {wall_elapsed:.2f}s")

    if global_stats["questions"]:

        print(
            "Average model time: "
            f"{global_stats['total_time'] / global_stats['questions']:.2f}s"
        )

    print()
    print("Generated files:")
    print(f"  {REGRESSION_FILE}")
    print(f"  {RESPONSES_FILE}")
    print(f"  {SUMMARY_FILE}")
    print(f"  {ENVIRONMENT_FILE}")
    print()
    print("=" * 80)
    print("Done.")
    print("=" * 80)
    print()


if __name__ == "__main__":

    main()