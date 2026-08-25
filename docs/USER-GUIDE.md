# CodeSleuth User Guide

CodeSleuth is an evidence-first OpenCode repository auditor. The normal workflow is: install it into a Git repository, choose repository/profile policy, run deep reviews, keep durable local review state, and optionally pin the exact CodeSleuth source commit as a project dependency.

## Start from a CodeSleuth checkout

Linux/macOS/WSL:

```bash
./codesleuth /path/to/project
```

PowerShell:

```powershell
.\codesleuth.ps1 C:\path\to\project
```

The TUI creates an isolated `textual==8.2.8` runtime if needed and does not install Textual into the target application's Python environment.

## TUI setup

The setup screen controls:

- install / update / legacy adoption;
- automatic or manual repository profiles;
- explicit OpenCode permission policy;
- Exa web runtime;
- keepalive/watchdog settings;
- compaction reserve;
- update checks;
- whether CodeSleuth is pinned as `tools/codesleuth` Git submodule.

Before first install CodeSleuth writes a pre-install backup under `.codesleuth/backups/pre-install/` and adds a managed root `.gitignore` block for local CodeSleuth/OpenCode state.

`tools/codesleuth` is never ignored by CodeSleuth. If the target project's own ignore rules hide that path, dependency binding refuses to proceed until the project owner resolves the policy intentionally.

## Security warning

OpenCode may have access to development credentials because the application under review may genuinely need them to run tests or access development services. CodeSleuth does not blanket-redact evidence. Findings, snippets, logs, reports, generated prompts and preserved review state may therefore contain secrets visible to the authorized runtime.

Local CodeSleuth state and preserved uninstall archives are gitignored by default. Inspect/sanitize audit output before sharing or force-adding ignored artifacts to Git.

## Project layout

A fully pinned development repository normally looks like:

```text
project/
├── .gitmodules
├── tools/
│   └── codesleuth/       # exact CodeSleuth gitlink/submodule
├── .opencode/            # project-owned installed auditor/runtime policy
└── .codesleuth/          # local backups/archives, ignored
```

`.opencode/state/` is local runtime/review state and remains ignored.

## Non-interactive installation

Install without adding a project dependency:

```bash
./install.sh /path/to/project
```

Install and pin CodeSleuth in the target repository:

```bash
./install.sh /path/to/project --bind-dependency
```

The bind operation stages `.gitmodules` and `tools/codesleuth`. It does not commit or push the target repository.

## Installed controls

After installation:

```bash
.opencode/bin/codesleuth
```

Compatibility alias:

```bash
.opencode/bin/review-pack
```

Validate the installation:

```bash
python3 .opencode/bin/review-pack-smoke.py .
```

Launch the configured OpenCode runtime:

```bash
.opencode/bin/opencode-review
```

## Main OpenCode commands

```text
/repo-prompts
/repo-profile
/repo-review
/repo-docs
/repo-review-resume
```

The deep-review workflow uses deterministic repository inventory, bounded scouts, parent re-verification of exact source, durable finding/checkpoint state, compaction-safe recovery and selective evidence rehydration.

## Durable state

Review state lives under:

```text
.opencode/state/reviews/
```

Reviewed source paths are bound to current Git blob hashes. If a tracked file changes after review, resume can detect stale coverage rather than claiming the old evidence is still current.

This local state is intentionally ignored by Git because it may be large and may contain sensitive evidence.

## Updating a pinned project

A superproject records an exact CodeSleuth commit. Advance it deliberately:

```bash
git -C tools/codesleuth fetch origin
git -C tools/codesleuth checkout --detach <accepted-sha>
./tools/codesleuth/install.sh . --update
```

Then inspect the project diff and commit the gitlink plus intended `.opencode` changes together.

Detached CodeSleuth checkouts are normal. CodeSleuth records the exact source commit and does not infer a floating branch from `origin/HEAD`.

## Uninstall while preserving audit traces

```bash
.opencode/bin/codesleuth-project --uninstall .
```

This archives known CodeSleuth settings/profiles/review state under `.codesleuth/archive/`, restores the pre-install `.opencode` baseline when available, removes CodeSleuth-owned runtime files, and removes a clean bound CodeSleuth submodule.

The archive stays gitignored.

## Uninstall and purge CodeSleuth traces

```bash
.opencode/bin/codesleuth-project --uninstall . --purge-traces
```

This restores prior project configuration and deletes CodeSleuth backups/known local traces. CodeSleuth does not guess at arbitrary report files authored elsewhere in the repository; those remain project-owned.

To remove only the installed runtime while keeping the pinned source dependency:

```bash
.opencode/bin/codesleuth-project --uninstall . --keep-dependency
```

The TUI exposes Preserve/Purge choices and requires an explicit uninstall action.

## Development and tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
ruff check .
```

The TUI tests use Textual's headless `App.run_test()` / `Pilot` facilities. The Git lifecycle tests build disposable repositories and exercise actual submodule add/remove behavior rather than mocking Git's most important semantics.

The TypeScript durable-state smoke remains:

```bash
bun tests/review_state_smoke.ts
```

## Permission ownership

Repository profiles describe stack evidence, verification commands and review focus. They do not grant web/edit/external permissions. Permission changes belong to the explicit project/TUI policy layer, so applying a profile cannot silently widen a stricter project policy.
