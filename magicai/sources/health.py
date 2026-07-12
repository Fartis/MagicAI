from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceProbe:
    name: str
    status: str
    required: bool
    detail: str = ""

    @property
    def available(self) -> bool:
        return self.status == "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "required": self.required,
            "available": self.available,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class SourceHealth:
    status: str
    ready: bool
    complete: bool
    sources: dict[str, SourceProbe]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready": self.ready,
            "complete": self.complete,
            "sources": {
                name: probe.to_dict()
                for name, probe in self.sources.items()
            },
        }


def get_source_health(source_root: str | Path | None = None) -> SourceHealth:
    root = _source_root(source_root)

    probes = {
        "scryfall_oracle": _probe_json(
            name="scryfall_oracle",
            path=root / "scryfall" / "oracle-cards.json",
            required=True,
        ),
        "comprehensive_rules": _probe_text(
            name="comprehensive_rules",
            path=root / "rules" / "MagicCompRules.txt",
            required=True,
            expected_marker="Comprehensive Rules",
        ),
        "scryfall_symbology": _probe_json(
            name="scryfall_symbology",
            path=root / "scryfall" / "symbology.json",
            required=False,
        ),
        "scryfall_rulings": _probe_json(
            name="scryfall_rulings",
            path=root / "scryfall" / "rulings.json",
            required=False,
        ),
    }

    required_ready = all(
        probe.available
        for probe in probes.values()
        if probe.required
    )
    complete = all(probe.available for probe in probes.values())

    if not required_ready:
        status = "unavailable"
    elif complete:
        status = "ready"
    else:
        status = "degraded"

    return SourceHealth(
        status=status,
        ready=required_ready,
        complete=complete,
        sources=probes,
    )


def _source_root(source_root: str | Path | None) -> Path:
    if source_root is not None:
        return Path(source_root)

    configured = os.environ.get("MAGICAI_SOURCES_DIR")
    if configured:
        return Path(configured)

    return Path(__file__).resolve().parents[2] / "sources"


def _probe_json(*, name: str, path: Path, required: bool) -> SourceProbe:
    if not path.is_file():
        return SourceProbe(
            name=name,
            status="missing",
            required=required,
            detail="Local source file is missing.",
        )

    try:
        size = path.stat().st_size
        if size <= 1:
            raise ValueError("file is empty")

        with path.open("rb") as handle:
            first = _first_non_whitespace(handle.read(4096))
            handle.seek(max(0, size - 4096))
            last = _last_non_whitespace(handle.read(4096))
    except (OSError, ValueError) as error:
        return SourceProbe(
            name=name,
            status="invalid",
            required=required,
            detail=f"Local JSON source is unreadable: {error}",
        )

    matching = {
        b"{": b"}",
        b"[": b"]",
    }
    if first not in matching or last != matching[first]:
        return SourceProbe(
            name=name,
            status="invalid",
            required=required,
            detail="Local JSON source does not look complete.",
        )

    return SourceProbe(
        name=name,
        status="available",
        required=required,
        detail=f"Local source available ({size} bytes).",
    )


def _probe_text(
    *,
    name: str,
    path: Path,
    required: bool,
    expected_marker: str,
) -> SourceProbe:
    if not path.is_file():
        return SourceProbe(
            name=name,
            status="missing",
            required=required,
            detail="Local source file is missing.",
        )

    try:
        header = path.read_text(encoding="utf-8-sig")[:4096]
        size = path.stat().st_size
    except OSError as error:
        return SourceProbe(
            name=name,
            status="invalid",
            required=required,
            detail=f"Local text source is unreadable: {error}",
        )

    if expected_marker.lower() not in header.lower():
        return SourceProbe(
            name=name,
            status="invalid",
            required=required,
            detail=f"Expected marker {expected_marker!r} was not found.",
        )

    return SourceProbe(
        name=name,
        status="available",
        required=required,
        detail=f"Local source available ({size} bytes).",
    )


def _first_non_whitespace(payload: bytes) -> bytes:
    for value in payload:
        character = bytes([value])
        if not character.isspace():
            return character
    return b""


def _last_non_whitespace(payload: bytes) -> bytes:
    for value in reversed(payload):
        character = bytes([value])
        if not character.isspace():
            return character
    return b""
