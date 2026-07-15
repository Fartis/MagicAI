# Contributing to MagicAI

## Principles

- Keep the Judge as the sole factual authority.
- Keep strategic source access behind the Judge gateway.
- Prefer generic semantic fixes over card-name conditions.
- Add focused tests for every repaired family.
- Preserve source provenance and version information.
- Treat evaluation artifacts as evaluation only.

## Development flow

```text
main       published or stable work
develop    integrated development
feature/*  isolated sprint branches
```

Before opening a pull request:

```bash
python scripts/ci_check.py
git status --short
```

Run the focused modules related to the change and document anything that could not be tested in the local environment.

Contributions are expected to use English for Markdown documentation and code-facing messages unless the output is intentionally localized for users.


## Branches and releases

Open ordinary changes against `develop`. Published releases are promoted to `main`. See [BRANCHING.md](BRANCHING.md) and [RELEASE_PROCESS.md](RELEASE_PROCESS.md).

## Pull requests

Keep pull requests focused, explain source-authority impact, list the tests actually executed, and document limitations. New behavior should include a regression test. Generated sources, reports, logs, databases, analysis bundles, and private data must not be committed.

All contributors must follow [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md), [../SECURITY.md](../SECURITY.md), and [../SUPPORT.md](../SUPPORT.md).
