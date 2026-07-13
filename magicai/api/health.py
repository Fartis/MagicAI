from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from magicai.llm.ollama import MODEL, OLLAMA_URL
from magicai.sources.health import SourceHealth, get_source_health
from magicai.versioning import (
    API_CONTRACT_VERSION,
    JUDGE_RESULT_SCHEMA_VERSION,
    get_project_version,
)


@dataclass(frozen=True, slots=True)
class ServiceProbe:
    status: str
    available: bool
    detail: str = ""
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "available": self.available,
            "detail": self.detail,
            "model": self.model,
        }


def probe_ollama(timeout: float = 2.0) -> ServiceProbe:
    tags_url = _ollama_tags_url(OLLAMA_URL)

    try:
        response = requests.get(tags_url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        return ServiceProbe(
            status="unavailable",
            available=False,
            detail=f"Ollama did not respond successfully: {error.__class__.__name__}.",
            model=MODEL,
        )

    models = {
        str(item.get("name", ""))
        for item in payload.get("models", [])
        if isinstance(item, dict)
    }
    model_available = (
        MODEL in models
        or any(name.split(":", 1)[0] == MODEL.split(":", 1)[0] for name in models)
    )

    return ServiceProbe(
        status="available" if model_available else "degraded",
        available=model_available,
        detail=(
            "Ollama and the configured model are available."
            if model_available
            else "Ollama is reachable, but the configured model was not listed."
        ),
        model=MODEL,
    )


def build_health_payload(
    *,
    source_health: SourceHealth | None = None,
    ollama_probe: ServiceProbe | None = None,
) -> dict[str, Any]:
    sources = source_health or get_source_health()
    ollama = ollama_probe or probe_ollama()

    ready = sources.ready
    full_service = ready and ollama.available

    if not ready:
        status = "unavailable"
    elif full_service and sources.complete:
        status = "ok"
    else:
        status = "degraded"

    return {
        "status": status,
        "ready": ready,
        "full_service": full_service,
        "project_version": get_project_version(),
        "api_contract_version": API_CONTRACT_VERSION,
        "judge_result_schema_version": JUDGE_RESULT_SCHEMA_VERSION,
        "sources": sources.to_dict(),
        "services": {
            "ollama": ollama.to_dict(),
        },
    }


def _ollama_tags_url(chat_url: str) -> str:
    parsed = urlsplit(chat_url)
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            "/api/tags",
            "",
            "",
        )
    )
