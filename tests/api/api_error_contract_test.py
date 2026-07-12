from pydantic import ValidationError

from magicai.api import app
from magicai.api.errors import build_error_payload
from magicai.api.schemas import AskRequest
from magicai.versioning import JUDGE_RESULT_SCHEMA_VERSION


def test_empty_question_is_rejected() -> None:
    try:
        AskRequest(question="   ")
    except ValidationError:
        return
    raise AssertionError("Whitespace-only question was accepted.")


def test_error_payload_is_versioned_and_structured() -> None:
    payload = build_error_payload(
        code="invalid_request",
        message="Invalid request.",
        retryable=False,
        details=[{"location": ["body", "question"]}],
    )

    assert payload["schema_version"] == JUDGE_RESULT_SCHEMA_VERSION
    assert payload["error"]["code"] == "invalid_request"
    assert payload["error"]["retryable"] is False
    assert payload["error"]["details"]


def test_application_has_custom_error_handlers() -> None:
    handler_names = {
        exception.__name__
        for exception in app.exception_handlers
        if hasattr(exception, "__name__")
    }

    assert "RequestValidationError" in handler_names
    assert "RequestException" in handler_names
    assert "Exception" in handler_names


def main() -> int:
    tests = [
        test_empty_question_is_rejected,
        test_error_payload_is_versioned_and_structured,
        test_application_has_custom_error_handlers,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"API error contract tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
