from __future__ import annotations

import os

import magicai.answer_generator as answer_generator
from magicai.judge_result import JudgeOrigin, JudgeStatus


def test_deterministic_evaluation_gate_blocks_llm_fallback():
    previous = os.environ.get("MAGICAI_EVALUATION_DETERMINISTIC_ONLY")
    original_generate = answer_generator.generate
    os.environ["MAGICAI_EVALUATION_DETERMINISTIC_ONLY"] = "1"

    def forbidden_generate(*_args, **_kwargs):
        raise AssertionError("Ollama was called during deterministic-only evaluation")

    answer_generator.generate = forbidden_generate
    try:
        result = answer_generator.generate_judge_result(
            "QUESTION\nA deliberately unsupported evaluation question.\n"
        )
        assert result.origin == JudgeOrigin.SAFE_FALLBACK
        assert result.status == JudgeStatus.INSUFFICIENT_EVIDENCE
        assert "bloqueó deliberadamente" in result.answer
        assert result.warnings
    finally:
        answer_generator.generate = original_generate
        if previous is None:
            os.environ.pop("MAGICAI_EVALUATION_DETERMINISTIC_ONLY", None)
        else:
            os.environ["MAGICAI_EVALUATION_DETERMINISTIC_ONLY"] = previous


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
