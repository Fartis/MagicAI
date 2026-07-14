from html.parser import HTMLParser
from pathlib import Path

from magicai.ui.routes import INDEX_FILE, UI_ROOT


class ControlCollector(HTMLParser):
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


def read_stylesheet() -> str:
    return (UI_ROOT / "app.css").read_text(encoding="utf-8")


def test_disambiguation_candidates_are_interactive_and_persisted() -> None:
    javascript = read_javascript()

    assert "function getClarificationCandidates(result)" in javascript
    assert 'result?.status !== "needs_clarification"' in javascript
    assert "function renderDisambiguationActions(candidates, selectedCandidate = null)" in javascript
    assert "function submitClarificationCandidate(candidate)" in javascript
    assert 'button.className = "clarification-option"' in javascript
    assert 'button.addEventListener("click", () => submitClarificationCandidate(candidate))' in javascript
    assert "normalizeCandidates(message.candidates)" in javascript
    assert "function markClarificationResolved(candidate)" in javascript
    assert "message.selectedCandidate = normalized" in javascript
    assert "MAX_DISAMBIGUATION_CANDIDATES = 8" in javascript


def test_copy_and_export_controls_use_the_last_structured_result() -> None:
    parser = ControlCollector()
    parser.feed(INDEX_FILE.read_text(encoding="utf-8"))
    javascript = read_javascript()

    for control_id in (
        "copy-answer-button",
        "copy-evidence-button",
        "export-result-button",
        "export-feedback-button",
    ):
        attributes = parser.attributes_by_id[control_id]
        assert attributes.get("type") == "button"
        assert "disabled" in attributes

    assert "async function copyLastAnswer()" in javascript
    assert "async function copyLastEvidence()" in javascript
    assert "function buildEvidenceText(result)" in javascript
    assert 'appendEvidenceTextSection(lines, "Versiones de fuentes"' in javascript
    assert "function exportLastResult()" in javascript
    assert 'new Blob([payload], {type: "application/json;charset=utf-8"})' in javascript
    assert "magicai-judge-result-${formatExportTimestamp(new Date())}.json" in javascript
    assert "function downloadJson(value, filename)" in javascript
    assert "function exportFeedbackCase()" in javascript
    assert "magicai-community-feedback-${timestamp}.json" in javascript
    assert 'artifact_purpose: "evaluation"' in javascript
    assert "training_allowed: false" in javascript
    assert "automatic_learning: false" in javascript
    assert "automatic_promotion: false" in javascript
    assert 'mode: "exploratory"' in javascript
    assert 'paraphrased: true' in javascript
    assert 'contains_verbatim_quote: false' in javascript
    assert 'contains_personal_data: false' in javascript


def test_evidence_sections_open_from_actual_content() -> None:
    javascript = read_javascript()
    stylesheet = read_stylesheet()

    assert "function configureEvidenceSections" in javascript
    assert '["cards-section", cards.length, cards.length > 0]' in javascript
    assert '["warnings-section", warnings.length, warnings.length > 0]' in javascript
    assert 'section.classList.toggle("is-empty", count === 0)' in javascript
    assert "STATUS_EXPLANATIONS" in javascript
    assert 'oracle.className = "oracle-text"' in javascript
    assert 'node.className = "evidence-card rule-card"' in javascript
    assert ".evidence-card-header" in stylesheet
    assert ".oracle-text" in stylesheet
    assert ".evidence-note.is-warnings" in stylesheet


def test_copy_fallback_and_rendering_remain_local_and_safe() -> None:
    javascript = read_javascript()

    assert "navigator.clipboard?.writeText" in javascript
    assert 'document.execCommand("copy")' in javascript
    assert 'textarea.className = "clipboard-fallback"' in javascript
    assert "textContent" in javascript
    assert "innerHTML" not in javascript
    assert "eval(" not in javascript


def test_quickstart_documents_branches_ui_and_ollama_modes() -> None:
    quickstart = Path("docs/QUICKSTART.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "git clone https://github.com/Fartis/MagicAI.git" in quickstart
    assert "git clone -b develop https://github.com/Fartis/MagicAI.git" in quickstart
    assert "http://127.0.0.1:8000/ui" in quickstart
    assert "Ollama en el mismo equipo" in quickstart
    assert "Ollama en un contenedor existente" in quickstart
    assert "Ollama en otra máquina de la red local" in quickstart
    assert "216/216" in readme
    assert "No significa" in readme
    assert "docs/QUICKSTART.md" in readme


def main() -> int:
    tests = [
        test_disambiguation_candidates_are_interactive_and_persisted,
        test_copy_and_export_controls_use_the_last_structured_result,
        test_evidence_sections_open_from_actual_content,
        test_copy_fallback_and_rendering_remain_local_and_safe,
        test_quickstart_documents_branches_ui_and_ollama_modes,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI usability tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
