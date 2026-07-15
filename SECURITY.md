# Security policy

## Supported versions

MagicAI is under active beta development. Security fixes are applied to the latest published release and the current `develop` branch. Older alpha and beta snapshots are not maintained unless explicitly stated in their release notes.

## Reporting a vulnerability

Do not publish exploit details, credentials, private data, or reproducible attack steps in a public issue.

Use GitHub's private vulnerability reporting feature for this repository when it is available. If private reporting is unavailable, open a minimal public issue asking the maintainers for a private contact channel. Include no sensitive technical details in that issue.

A useful private report includes:

- affected version or commit;
- affected component;
- reproduction steps;
- realistic impact;
- suggested mitigation, when known;
- whether the issue involves local files, network exposure, dependencies, or source data.

## Security boundaries

MagicAI is designed as a local-first application, but users remain responsible for their deployment environment.

- Do not expose an unauthenticated Ollama endpoint to the public Internet.
- Do not commit `.env` files, credentials, private decklists, conversation databases, logs, or generated analysis bundles.
- Treat imported community data and user-supplied files as untrusted input.
- Keep Python, Ollama, MagicAI dependencies, and operating-system packages updated.

Security reports are evaluated separately from ordinary rules-answer accuracy reports.
