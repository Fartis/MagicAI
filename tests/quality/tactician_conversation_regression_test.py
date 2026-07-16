from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from tests.quality.tactician_conversations.runner import run_gauntlet


CASES = Path(__file__).parent / "cases" / "tactician_conversations"


def test_fixture_conversation_gauntlet_passes() -> None:
    with TemporaryDirectory() as directory:
        result = run_gauntlet(CASES, mode="fixture", output_dir=directory)
        assert result["scenario_count"] == 40
        assert result["turn_count"] == 58
        assert result["passed_scenarios"] == 40
        assert result["failed_scenarios"] == 0
        assert result["passed_turns"] == 58
        assert result["failed_turns"] == 0
        assert (Path(directory) / "summary.json").exists()
        assert (Path(directory) / "report.html").exists()


def main() -> int:
    test_fixture_conversation_gauntlet_passes()
    print("OK: test_fixture_conversation_gauntlet_passes")
    print("Tactician conversation regression tests: 40/40 scenarios, 58/58 turns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
