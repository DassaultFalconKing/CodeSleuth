# CodeSleuth release process

This document is the maintainer contract for numbered releases.

## Branch policy

`main` is the accepted release line. Do not use it as a work branch.

Normal development lives on:

```text
dev/release-X.Y.Z     integration/release-candidate line for the next numbered release
feature/*              product extensions and host integrations
chore/*                maintenance, dependency, documentation, CI and release work
fix/*                   focused correctness/hardening fixes
```

Feature/chore/fix work is integrated into the active `dev/release-X.Y.Z` branch first. `main` advances only when that release candidate has passed the release gates and is intentionally accepted as version `X.Y.Z`.

Do not push an unreviewed implementation change directly to `main`. An emergency fix still becomes a numbered release: fix branch -> release-candidate branch -> acceptance -> `main`.

The repository currently has historical branches that predate this policy. They are not release authority.

## Version authority

Source-distribution version authority is the repository-root:

```text
VERSION
```

It contains one semantic version such as `0.4.0`.

Installed CodeSleuth materializes that value into:

```text
.opencode/review-pack.json -> version
```

If `.opencode/codesleuth.json` is also present and differs, version resolution fails closed. Canonical `codesleuth.json` is preferred when both files exist and are identical. 0.4.0 still materializes the live compatibility filename `review-pack.json`.

The installed metadata is the authority for the version actually present in a target repository. A source checkout and an installed target can therefore honestly report different versions during an upgrade.

Runtime code must not contain a numeric fallback version. Missing or malformed version metadata is an error.

The version must be projected from those metadata sources into user-visible surfaces:

- source `codesleuth --version` -> root `VERSION`;
- installed `codesleuth --version` -> installed `review-pack.json.version`;
- installer/update/smoke logs -> the same source/installed metadata they act on;
- TUI status -> installed target metadata;
- release notes/changelog -> the numbered release being accepted.

Documentation should not duplicate a mutable numeric "current version" when it can point to `VERSION` or a release tag instead.

## Numbered release gate

Before `dev/release-X.Y.Z` may enter `main`:

1. `VERSION` is exactly the intended `X.Y.Z` and passes the version-contract tests.
2. The full Python suite passes on supported Linux and Windows runners.
3. Ruff passes on the same source tree.
4. Bun installs from the frozen lockfile and both durable-state/context-graph smokes pass.
5. MCP tests run as part of the clean development dependency install; they are not silently omitted.
6. Documentation contract tests pass and the README describes current behavior.
7. Install/update/Verify/uninstall behavior relevant to the release has regression coverage using disposable real Git repositories where practical.
8. No accepted finding from the release-readiness review remains unresolved.
9. For a public release, repository licensing is explicit and intentional.
10. The release candidate is mergeable into the exact current `main` without unrelated scope.

GitHub branch/ruleset policy should require the acceptance checks before `main` is updated. Repository settings are infrastructure authority; this file documents the required policy but does not substitute for it.

## Accepting a release

When the release candidate is green:

1. review the complete `main...dev/release-X.Y.Z` diff;
2. merge it into `main` as the numbered release;
3. verify the resulting `main` commit again;
4. create immutable tag `vX.Y.Z` at that exact accepted commit;
5. create/update release notes from `CHANGELOG.md`;
6. treat the tag and `main` commit as the release identity;
7. start the next `dev/release-A.B.C` line from that accepted `main`.

Do not move an existing numbered tag to a different commit. A correction is a new version.

## Release record

`CHANGELOG.md` is the human release ledger. Each accepted release records:

- version and UTC release date;
- user-visible changes;
- compatibility or migration notes;
- known limitations that remain intentionally accepted.

Commit SHA identity belongs to Git and the immutable `vX.Y.Z` tag, not to a self-referential value embedded in the release commit.

## Current first release-candidate line

The first release prepared under this contract is:

```text
dev/release-0.4.0
```

It establishes the release process itself, CI acceptance, version-metadata discipline, the hardened TUI/lifecycle work, and the current OpenCode/NovaClaw integration baseline. It is not a release until the gates above pass and `main` is intentionally advanced.
