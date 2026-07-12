from html.parser import HTMLParser
from pathlib import Path

from magicai.ui.routes import INDEX_FILE, UI_ROOT


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: set[str] = set()
        self.scripts: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "link" and "href" in attributes:
            self.links.add(attributes["href"])
        if tag == "script" and "src" in attributes:
            self.scripts.add(attributes["src"])


def test_ui_assets_exist_and_are_packaged_together() -> None:
    expected = {
        UI_ROOT / "index.html",
        UI_ROOT / "app.css",
        UI_ROOT / "app.js",
    }
    assert all(path.is_file() for path in expected)
    assert INDEX_FILE == UI_ROOT / "index.html"


def test_index_exposes_chat_and_evidence_contract() -> None:
    parser = IdCollector()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))

    required_ids = {
        "message-list",
        "question-form",
        "question-input",
        "send-button",
        "evidence-panel",
        "result-status",
        "cards-list",
        "rules-list",
        "rulings-list",
        "health-badge",
    }

    assert required_ids <= parser.ids
    assert "/ui/assets/app.css" in parser.links
    assert "/ui/assets/app.js" in parser.scripts


def test_javascript_uses_structured_api_without_html_injection() -> None:
    javascript = (UI_ROOT / "app.js").read_text(encoding="utf-8")

    assert 'fetchJson("/ask"' in javascript
    assert 'fetchJson("/health"' in javascript
    assert 'fetchJson("/meta"' in javascript
    assert "JSON.stringify(payload)" in javascript
    assert "textContent" in javascript
    assert "innerHTML" not in javascript
    assert "localStorage" in javascript


def main() -> int:
    tests = [
        test_ui_assets_exist_and_are_packaged_together,
        test_index_exposes_chat_and_evidence_contract,
        test_javascript_uses_structured_api_without_html_injection,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI asset tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
