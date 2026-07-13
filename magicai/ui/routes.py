from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


UI_ROOT = Path(__file__).resolve().parent / "static"
INDEX_FILE = UI_ROOT / "index.html"


def ui_index() -> FileResponse:
    return FileResponse(
        INDEX_FILE,
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


def install_ui(app: FastAPI) -> None:
    """Install the dependency-free Judge beta UI on an existing FastAPI app."""

    app.mount(
        "/ui/assets",
        StaticFiles(directory=UI_ROOT),
        name="ui-assets",
    )
    app.add_api_route(
        "/ui",
        ui_index,
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/ui/",
        ui_index,
        methods=["GET"],
        include_in_schema=False,
    )
