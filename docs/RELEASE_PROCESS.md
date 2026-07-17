# Release process

## Canonical release identity

MagicAI separates its public release label from Python package metadata:

```text
Public version: 0.1.1-beta
Git tag:        v0.1.1-beta
Package version: 0.1.1b0
Codename:       Force of Will
```

Python package versions follow PEP 440. Public tags use lowercase prerelease identifiers consistently.

## Pre-release checklist

1. Confirm the release identity in `magicai/versioning.py` and `pyproject.toml`.
2. Update `README.md`, `docs/STATUS.md`, and `docs/ROADMAP.md`.
3. Run the focused CI suite:

   ```bash
   python scripts/ci_check.py
   ```

4. Run the release-specific regression and quality campaigns.
5. Confirm the working tree contains no databases, logs, backups, reports, large downloaded sources, or private files.
6. Build clean source and full packages from tracked files:

   ```bash
   python scripts/package_release.py --source
   python scripts/package_release.py --full
   ```

7. Verify the generated SHA-256 files.
8. Open and merge the release pull request from `develop` to `main`.
9. Create the exact lowercase tag declared in `magicai/versioning.py`.
10. Publish release notes that include known limitations and validation performed.

## Package types

### Source package

Contains tracked repository files required for development and installation. It excludes downloaded Scryfall bulk data and local runtime artifacts.

### Full package

Contains the same clean tracked repository snapshot and additionally includes the local Oracle and rulings bulk files when present.

Both packages include a generated `INFO.txt` and `PACKAGE_MANIFEST.json`.

## Tag policy

Use consistent lowercase identifiers:

```text
v0.1.0-alpha
v0.1.1-beta
v0.2.0-beta
v1.0.0
```

Do not create variants such as `Alpha`, `Beta`, or differently formatted tags for the same release.

## Release notes

Release notes should describe:

- user-visible changes;
- authority or source-boundary changes;
- migration steps;
- tests and campaigns executed;
- known limitations;
- package checksums;
- the release codename.
