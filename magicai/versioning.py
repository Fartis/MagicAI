from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


JUDGE_RESULT_SCHEMA_VERSION = "1.0"
API_CONTRACT_VERSION = "1.1"
TACTICIAN_RESULT_SCHEMA_VERSION = "0.1"
PROJECT_FALLBACK_VERSION = "0.1.0"


def get_project_version() -> str:
    try:
        return version("magicai")
    except PackageNotFoundError:
        return PROJECT_FALLBACK_VERSION
