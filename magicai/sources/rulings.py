from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


_CACHE_PATH: Path | None = None
_CACHE_MTIME_NS: int | None = None
_CACHE_INDEX: dict[str, list[dict[str, str]]] = {}


def find_rulings_by_oracle_id(
    oracle_id: str,
    *,
    source_root: str | Path | None = None,
    limit: int = 8,
) -> list[dict[str, str]]:
    """Return locally cached Scryfall rulings for one Oracle ID.

    The Judge never performs a network request at answer time. If the optional
    rulings bulk file is absent or malformed, this function returns an empty
    list and the rest of the factual pipeline continues normally.
    """

    if not oracle_id or limit <= 0:
        return []

    index = _load_index(source_root)
    return [dict(item) for item in index.get(str(oracle_id), [])[:limit]]


def _load_index(source_root: str | Path | None) -> dict[str, list[dict[str, str]]]:
    global _CACHE_PATH, _CACHE_MTIME_NS, _CACHE_INDEX

    path = _rulings_path(source_root)

    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return {}

    if path == _CACHE_PATH and mtime_ns == _CACHE_MTIME_NS:
        return _CACHE_INDEX

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, list):
        return {}

    index: dict[str, list[dict[str, str]]] = {}

    for raw in payload:
        normalized = _normalize_ruling(raw)
        if normalized is None:
            continue

        index.setdefault(normalized["oracle_id"], []).append(normalized)

    for items in index.values():
        items.sort(key=lambda item: item.get("published_at", ""), reverse=True)

    _CACHE_PATH = path
    _CACHE_MTIME_NS = mtime_ns
    _CACHE_INDEX = index
    return index


def _normalize_ruling(raw: Any) -> dict[str, str] | None:
    if not isinstance(raw, dict):
        return None

    oracle_id = _clean(raw.get("oracle_id"))
    comment = _clean(raw.get("comment"))

    if not oracle_id or not comment:
        return None

    return {
        "oracle_id": oracle_id,
        "source": _clean(raw.get("source")),
        "published_at": _clean(raw.get("published_at")),
        "comment": comment,
    }


def _rulings_path(source_root: str | Path | None) -> Path:
    if source_root is not None:
        root = Path(source_root)
    elif configured := os.environ.get("MAGICAI_SOURCES_DIR"):
        root = Path(configured)
    else:
        root = Path(__file__).resolve().parents[2] / "sources"

    return root / "scryfall" / "rulings.json"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
