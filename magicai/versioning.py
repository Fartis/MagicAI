from __future__ import annotations

JUDGE_RESULT_SCHEMA_VERSION = "1.0"
JUDGE_TOOL_RESULT_SCHEMA_VERSION = "1.0"
API_CONTRACT_VERSION = "1.8"
TACTICIAN_RESULT_SCHEMA_VERSION = "0.7"

# Packaging metadata must follow PEP 440. Public release names remain SemVer-like.
PACKAGE_FALLBACK_VERSION = "0.1.1b0"
PUBLIC_VERSION = "0.1.1-beta"
RELEASE_TAG = "v0.1.1-beta"
RELEASE_CHANNEL = "beta"
RELEASE_CODENAME = "Force of Will"

NEXT_BETA_VERSION = "0.2.0-beta"
NEXT_BETA_CODENAME = "Ponder"
V1_CODENAME = "NicolAI Bolas"


def get_package_version() -> str:
    """Return the canonical PEP 440 package version."""

    return PACKAGE_FALLBACK_VERSION


def get_project_version() -> str:
    """Return the public release version used by the API and UI."""

    return PUBLIC_VERSION


def get_release_identity() -> dict[str, str]:
    """Return the canonical public release identity."""

    return {
        "version": PUBLIC_VERSION,
        "tag": RELEASE_TAG,
        "channel": RELEASE_CHANNEL,
        "codename": RELEASE_CODENAME,
        "package_version": get_package_version(),
    }
