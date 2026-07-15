# Local MagicAI UI

The UI is served by FastAPI and uses local HTML, CSS, and JavaScript. It does not require Node or an external frontend service.

## Profiles

- **Judge:** factual rules and Oracle questions.
- **Estratega:** Tactician analysis for strategy, combos, synergies, and lines.

Strategic questions sent to the normal `/ask` endpoint can hand off automatically, so users do not need to repeat the question after the Judge detects a strategy boundary.

## Evidence panel

The UI can display:

- cards and Oracle text;
- rules and rulings;
- assumptions and warnings;
- source health and versions;
- answer origin and authority;
- Tactician synergies and risks;
- combo classification, steps, outcomes, inherited cards, and Judge query trace.

## Local history

Conversations are stored in local SQLite and can be opened, renamed, or deleted. No account or remote service is required.

## Security

Rendered content uses DOM text nodes rather than injecting model-generated HTML. Scryfall links use an allowlist.
