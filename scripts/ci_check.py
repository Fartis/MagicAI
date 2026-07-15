#!/usr/bin/env python3
"""Run MagicAI's fast, source-independent pull request checks."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]

TEST_MODULES = (
    "tests.repository.repository_health_test",
    "tests.repository.release_packaging_test",
    "tests.judge_tools.judge_tool_gateway_test",
    "tests.judge_tools.local_tools_test",
    "tests.api.judge_tool_api_test",
    "tests.tactician.tactician_tool_gateway_test",
    "tests.tactician.tactician_input_reasoning_test",
    "tests.tactician.tactician_followup_reasoning_test",
    "tests.tactician.tactician_reviewer_test",
    "tests.tactician.tactician_strategy_test",
    "tests.tactician.tactician_conversation_handoff_test",
    "tests.tactician.tactician_core_test",
    "tests.api.api_contract_metadata_test",
    "tests.api.tactician_api_contract_test",
    "tests.api.tactician_auto_handoff_test",
    "tests.api.judge_result_schema_test",
    "tests.api.api_error_contract_test",
    "tests.api.ui_routes_test",
    "tests.conversation.conversation_repository_test",
    "tests.conversation.tactician_strategy_context_test",
    "tests.validation.strategy_boundary_test",
    "tests.validation.oracle_derived_undying_test",
    "tests.validation.rule_renderer_test",
    "tests.ui.ui_assets_test",
    "tests.ui.ui_usability_test",
)


def run(command: list[str], *, environment: dict[str, str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def main() -> int:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment.setdefault("MAGICAI_QUIET_EVALUATION", "1")

    with tempfile.TemporaryDirectory(prefix="magicai-ci-") as directory:
        environment.setdefault(
            "MAGICAI_CONVERSATION_DB",
            str(Path(directory) / "conversations.sqlite3"),
        )

        run(
            [sys.executable, "-m", "compileall", "-q", "magicai", "tests", "scripts"],
            environment=environment,
        )

        if (ROOT / ".git").exists():
            run(["git", "diff", "--check"], environment=environment)

        bash = shutil.which("bash")
        if bash:
            for script in sorted((ROOT / "scripts").glob("*.sh")):
                run([bash, "-n", str(script.relative_to(ROOT))], environment=environment)

        node = shutil.which("node")
        if node:
            run([node, "--check", "magicai/ui/static/app.js"], environment=environment)

        for module in TEST_MODULES:
            run([sys.executable, "-m", module], environment=environment)

    print()
    print(f"MagicAI focused CI: {len(TEST_MODULES)}/{len(TEST_MODULES)} modules passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
