from __future__ import annotations

from pathlib import Path
import re
import tomllib

from magicai.versioning import (
    NEXT_BETA_CODENAME,
    NEXT_BETA_VERSION,
    PACKAGE_FALLBACK_VERSION,
    PUBLIC_VERSION,
    RELEASE_CHANNEL,
    RELEASE_CODENAME,
    RELEASE_TAG,
    V1_CODENAME,
)


ROOT = Path(__file__).resolve().parents[2]


def test_release_identity_is_consistent() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == PACKAGE_FALLBACK_VERSION
    assert PUBLIC_VERSION == "0.1.1-beta"
    assert RELEASE_TAG == "v0.1.1-beta"
    assert RELEASE_CHANNEL == "beta"
    assert RELEASE_CODENAME == "Force of Will"
    assert NEXT_BETA_VERSION == "0.2.0-beta"
    assert NEXT_BETA_CODENAME == "Ponder"
    assert V1_CODENAME == "NicolAI Bolas"


def test_required_community_and_automation_files_exist() -> None:
    required = [
        ".github/workflows/ci.yml",
        ".github/dependabot.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
        "docs/BRANCHING.md",
        "docs/RELEASE_PROCESS.md",
        "docs/REPOSITORY_HEALTH.md",
        "scripts/ci_check.py",
        "scripts/package_release.py",
        "scripts/export_github_analysis.sh",
    ]
    missing = [relative for relative in required if not (ROOT / relative).is_file()]
    assert not missing, f"Missing repository-health files: {missing}"


def test_ci_is_fast_and_does_not_require_bulk_sources_or_ollama() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python scripts/ci_check.py" in workflow
    assert "download_sources.sh" not in workflow
    assert "oracle_exhaustive_test" not in workflow
    assert "ollama pull" not in workflow
    assert "permissions:\n  contents: read" in workflow


def test_release_packaging_uses_git_and_ignores_local_exports() -> None:
    script = (ROOT / "scripts/package_release.py").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    exporter = (ROOT / "scripts/export_github_analysis.sh").read_text(encoding="utf-8")

    assert '"ls-files", "-z"' in script
    assert "FULL_SOURCE_FILES" in script
    assert "/github-analysis-*/" in gitignore
    assert "/dist/releases/" in gitignore
    assert "--slurp" not in exporter
    assert "if len(parts) < 6" in exporter
    assert '--list-file="$OUT/git/tracked_files.txt"' in exporter


def test_markdown_is_english_and_personal_letter_is_preserved() -> None:
    markdown_files = sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in {"backups", "github-analysis-20260715-025523"} for part in path.parts)
    )
    spanish_markers = re.compile(
        r"[¿¡]|\b(?:por motivos|si has llegado|nos vemos|me gustaría|mientras mi salud|gracias por dedicar)\b",
        flags=re.IGNORECASE,
    )
    violations = []
    for path in markdown_files:
        content = path.read_text(encoding="utf-8")
        if spanish_markers.search(content):
            violations.append(str(path.relative_to(ROOT)))
    assert not violations, f"Markdown must remain English-only: {violations}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "# ❤️ A personal letter" in readme
    assert "Due to health reasons" in readme
    assert "See you in the next game." in readme
    assert "Force of Will" in readme
    assert "Ponder" in readme
    assert "NicolAI Bolas" in readme


def main() -> int:
    tests = [
        test_release_identity_is_consistent,
        test_required_community_and_automation_files_exist,
        test_ci_is_fast_and_does_not_require_bulk_sources_or_ollama,
        test_release_packaging_uses_git_and_ignores_local_exports,
        test_markdown_is_english_and_personal_letter_is_preserved,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Repository health tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
