from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path


_RULES_VERSION_RE = re.compile(
    r"effective as of\s+(?P<date>[A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
    flags=re.IGNORECASE,
)


def get_source_versions(source_root: str | Path | None = None) -> dict[str, str]:
    """Return only source versions that can be established locally.

    Comprehensive Rules expose an effective date in their contents. Scryfall
    bulk files do not embed their bulk update timestamp, so their filesystem
    modification time is exposed explicitly as a file timestamp rather than
    pretending it is a semantic dataset version.
    """

    root = _source_root(source_root)
    versions: dict[str, str] = {}

    rules_path = root / "rules" / "MagicCompRules.txt"
    rules_version = _rules_effective_date(rules_path)
    if rules_version:
        versions["comprehensive_rules"] = rules_version

    _add_file_timestamp(
        versions,
        key="scryfall_oracle_file_mtime",
        path=root / "scryfall" / "oracle-cards.json",
    )
    _add_file_timestamp(
        versions,
        key="scryfall_symbology_file_mtime",
        path=root / "scryfall" / "symbology.json",
    )

    return versions


def _source_root(source_root: str | Path | None) -> Path:
    if source_root is not None:
        return Path(source_root)

    configured = os.environ.get("MAGICAI_SOURCES_DIR")
    if configured:
        return Path(configured)

    return Path(__file__).resolve().parents[2] / "sources"


def _rules_effective_date(path: Path) -> str | None:
    if not path.is_file():
        return None

    try:
        header = path.read_text(encoding="utf-8-sig")[:1000]
    except OSError:
        return None

    match = _RULES_VERSION_RE.search(header)
    if not match:
        return None

    try:
        parsed = datetime.strptime(match.group("date"), "%B %d, %Y")
    except ValueError:
        return match.group("date")

    return parsed.date().isoformat()


def _add_file_timestamp(
    versions: dict[str, str],
    *,
    key: str,
    path: Path,
) -> None:
    if not path.is_file():
        return

    try:
        modified = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=timezone.utc,
        )
    except OSError:
        return

    versions[key] = modified.isoformat(timespec="seconds")
