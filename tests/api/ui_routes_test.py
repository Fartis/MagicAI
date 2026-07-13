from pathlib import Path

from fastapi.responses import FileResponse

from magicai.api import app
from magicai.ui.routes import INDEX_FILE, ui_index


def test_application_exposes_ui_routes_and_assets() -> None:
    paths = {route.path for route in app.routes}

    assert "/ui" in paths
    assert "/ui/" in paths
    assert "/ui/assets" in paths


def test_ui_index_returns_packaged_html() -> None:
    response = ui_index()

    assert isinstance(response, FileResponse)
    assert Path(response.path) == INDEX_FILE
    assert response.media_type == "text/html"
    assert response.headers.get("cache-control") == "no-cache"


def main() -> int:
    tests = [
        test_application_exposes_ui_routes_and_assets,
        test_ui_index_returns_packaged_html,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"UI route tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
