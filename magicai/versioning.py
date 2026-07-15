from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


JUDGE_RESULT_SCHEMA_VERSION = "1.0"
API_CONTRACT_VERSION = "1.2"
TACTICIAN_RESULT_SCHEMA_VERSION = "0.2"
PROJECT_FALLBACK_VERSION = "0.1.0"
NEXT_BETA_VERSION = "0.1"
NEXT_BETA_CODENAME = "Ponder"
V1_CODENAME = "NicolAI Bolas"


def get_project_version() -> str:
    try:
        return version("magicai")
    except PackageNotFoundError:
        return PROJECT_FALLBACK_VERSION
