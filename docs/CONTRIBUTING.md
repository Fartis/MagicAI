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
python -m compileall -q magicai tests
git diff --check
git status --short
```

Run the focused modules related to the change and document anything that could not be tested in the local environment.

Contributions are expected to use English for Markdown documentation and code-facing messages unless the output is intentionally localized for users.
