from html.parser import HTMLParser

from magicai.ui.routes import INDEX_FILE, UI_ROOT


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)


def test_ui_exposes_manageable_conversation_history() -> None:
    parser = IdCollector()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))
    javascript = (UI_ROOT / "app.js").read_text(encoding="utf-8")

    assert {"conversation-list", "history-status", "refresh-history-button"} <= parser.ids
    assert 'fetchJson("/conversations?limit=50")' in javascript
    assert "async function openConversation" in javascript
    assert "async function renameConversation" in javascript
    assert "async function deleteConversation" in javascript
    assert 'method: "PATCH"' in javascript
    assert 'method: "DELETE"' in javascript
    assert "innerHTML" not in javascript


def test_gauntlet_dashboard_palette_is_applied() -> None:
    stylesheet = (UI_ROOT / "app.css").read_text(encoding="utf-8")

    for declaration in (
        "--bg: #111827",
        "--surface: #1f2937",
        "--surface-strong: #273449",
        "--border: #374151",
        "--accent: #60a5fa",
        "--good: #22c55e",
        "--warn: #f59e0b",
        "--bad: #ef4444",
    ):
        assert declaration in stylesheet

    assert ".history-panel" in stylesheet
    assert ".conversation-item.is-active" in stylesheet
    assert "linear-gradient(180deg, var(--accent), var(--violet))" in stylesheet


def main() -> int:
    tests = [
        test_ui_exposes_manageable_conversation_history,
        test_gauntlet_dashboard_palette_is_applied,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI history/theme tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
