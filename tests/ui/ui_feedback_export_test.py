from html.parser import HTMLParser

from magicai.ui.routes import INDEX_FILE, UI_ROOT


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: dict[str, dict[str, str | None]] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids[element_id] = attributes


def read_javascript() -> str:
    return (UI_ROOT / "app.js").read_text(encoding="utf-8")


def test_ui_exposes_feedback_case_export_control() -> None:
    parser = IdCollector()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))
    attributes = parser.ids["export-feedback-button"]
    assert attributes.get("type") == "button"
    assert "disabled" in attributes
    assert "feedback-export-notice" in parser.ids


def test_feedback_export_contains_only_user_turns_and_safe_flags() -> None:
    javascript = read_javascript()
    assert "function exportFeedbackCase()" in javascript
    assert '.filter(message => message?.role === "user"' in javascript
    assert 'artifact_purpose: "evaluation"' in javascript
    assert "training_allowed: false" in javascript
    assert "automatic_learning: false" in javascript
    assert "automatic_promotion: false" in javascript
    assert 'mode: "exploratory"' in javascript
    assert 'platform: "manual"' in javascript
    assert "paraphrased: true" in javascript
    assert "contains_verbatim_quote: false" in javascript
    assert "contains_personal_data: false" in javascript
    assert 'tags: ["ui-feedback", "manual-feedback"]' in javascript


def test_feedback_export_does_not_embed_assistant_answer_or_judge_result() -> None:
    javascript = read_javascript()
    start = javascript.index("function exportFeedbackCase()")
    end = javascript.index("function buildFeedbackTitle", start)
    block = javascript[start:end]

    assert "state.lastResult.answer" not in block
    assert "judge_result" not in block
    assert "assistant" not in block
    assert "raw_post" not in block
    assert "username" not in block


def main() -> int:
    tests = [
        test_ui_exposes_feedback_case_export_control,
        test_feedback_export_contains_only_user_turns_and_safe_flags,
        test_feedback_export_does_not_embed_assistant_answer_or_judge_result,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI feedback export tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
