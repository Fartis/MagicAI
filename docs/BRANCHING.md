# Branching policy

MagicAI uses a simple release-oriented branching model.

## Permanent branches

### `main`

`main` contains published releases and release candidates that are ready to be presented to users. Tags are created from `main`.

### `develop`

`develop` is the integration branch for the next development cycle and the preferred default branch while MagicAI remains under active beta development.

## Short-lived branches

Use a focused branch for each change:

```text
feature/<scope>
fix/<scope>
chore/<scope>
docs/<scope>
test/<scope>
```

Examples:

```text
feature/sprint12-2-judge-tool-gateway
fix/undying-evidence-contract
chore/repository-health-foundation
```

Open pull requests against `develop` unless the change is an urgent release fix.

## Release flow

1. Merge completed feature, fix, test, and chore branches into `develop`.
2. Run the required CI and release validation on `develop`.
3. Open a release pull request from `develop` to `main`.
4. Merge the release pull request without rewriting public history.
5. Create the canonical release tag from `main`.
6. Merge any release-only corrections from `main` back into `develop`.

## Hotfix flow

Urgent corrections to a published release may branch from `main` using `fix/` or `hotfix/`. After release, merge the hotfix back into `develop`.

## Branch cleanup

Delete merged short-lived branches after their pull request is complete. Preserve important milestones through tags, releases, changelogs, and documented commits rather than permanent sprint or backup branches.

Local safety branches may be created before risky operations, but they should not normally be pushed to the shared repository. Remove them after the operation has been verified.

## Protection recommendations

Protect `main` and `develop` with:

- required pull requests;
- required CI checks;
- blocked force pushes;
- blocked deletion;
- resolved review conversations before merge.

A sole maintainer may temporarily keep review requirements lightweight, but CI and history protection should remain enabled.
