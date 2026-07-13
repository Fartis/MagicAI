from html.parser import HTMLParser
from pathlib import Path

from magicai.ui.routes import INDEX_FILE, UI_ROOT


class AttributeCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attributes_by_id: dict[str, dict[str, str | None]] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.attributes_by_id[element_id] = attributes


def read_javascript() -> str:
    return (UI_ROOT / "app.js").read_text(encoding="utf-8")


def test_active_question_can_be_cancelled_and_times_out() -> None:
    javascript = read_javascript()

    assert "const ASK_TIMEOUT_MS = 180000" in javascript
    assert "new AbortController()" in javascript
    assert 'signal: controller.signal' in javascript
    assert "function cancelActiveRequest()" in javascript
    assert 'activeRequest.controller.abort("user")' in javascript
    assert 'controller.abort("timeout")' in javascript
    assert "function isCurrentRequest(requestId)" in javascript
    assert "state.activeRequest?.id === requestId" in javascript


def test_storage_is_validated_and_failures_are_visible() -> None:
    javascript = read_javascript()

    assert "function loadStoredSession()" in javascript
    assert "function loadStoredMessages()" in javascript
    assert "function loadStoredResult()" in javascript
    assert "function isValidStoredMessage(value)" in javascript
    assert "function markStorageUnavailable()" in javascript
    assert "function flushStorageWarning()" in javascript
    assert "no permite guardar el historial local" in javascript
    assert "localStorage.removeItem(STORAGE.session)" not in javascript
    assert "localStorage.removeItem(STORAGE.transcript)" not in javascript
    assert "localStorage.removeItem(STORAGE.lastResult)" not in javascript


def test_scryfall_links_are_allowlisted() -> None:
    javascript = read_javascript()

    assert "function getTrustedScryfallUrl(value)" in javascript
    assert 'url.protocol !== "https:"' in javascript
    assert '["scryfall.com", "www.scryfall.com"]' in javascript
    assert "link.href = scryfallUrl" in javascript
    assert "link.href = card.scryfall_uri" not in javascript


def test_accessible_request_state_and_cancel_control_exist() -> None:
    parser = AttributeCollector()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))

    cancel = parser.attributes_by_id["cancel-request-button"]
    form = parser.attributes_by_id["question-form"]
    messages = parser.attributes_by_id["message-list"]
    input_attributes = parser.attributes_by_id["question-input"]
    request_status = parser.attributes_by_id["request-status"]

    assert cancel.get("type") == "button"
    assert "hidden" in cancel
    assert form.get("aria-busy") == "false"
    assert messages.get("role") == "log"
    assert messages.get("aria-busy") == "false"
    assert input_attributes.get("aria-describedby") == "composer-hint"
    assert request_status.get("role") == "status"
    assert request_status.get("aria-live") == "polite"
    assert request_status.get("aria-atomic") == "true"


def test_health_polling_does_not_overlap() -> None:
    javascript = read_javascript()

    assert "healthRequestPending: false" in javascript
    assert "if (state.healthRequestPending)" in javascript
    assert "state.healthRequestPending = true" in javascript
    assert "state.healthRequestPending = false" in javascript
    assert "const AUXILIARY_TIMEOUT_MS = 10000" in javascript


def main() -> int:
    tests = [
        test_active_question_can_be_cancelled_and_times_out,
        test_storage_is_validated_and_failures_are_visible,
        test_scryfall_links_are_allowlisted,
        test_accessible_request_state_and_cancel_control_exist,
        test_health_polling_does_not_overlap,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI resilience tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
