# CodeSleuth LLM operator README

<!-- README-SOURCE-BLOB: 4d459a70cb13bf37d8d0c566d867cd57d57471fd -->

This is the task-specific operating manual for a coding agent or LLM when a user asks it to install, configure, use, update, remove, or reason about CodeSleuth. Root [`AGENTS.md`](../AGENTS.md) is the compact cross-agent discovery entry point. [`../README.md`](../README.md) remains the canonical product/manual surface. When this guide and current source disagree, verify the source and follow the source.

## 1. Mental model

CodeSleuth is a discipline layer and control panel around a host coding agent. It packages repository review Skills, profiles, durable evidence conventions, local reports, context mapping, a TUI, and bounded repository tools.

Do not describe or configure CodeSleuth as a second agent runtime, second primary controller, or general-purpose tool router.

For the current full OpenCode integration:

```text
CodeSleuth -> configuration / Skills / profiles / evidence discipline / TUI
OpenCode   -> model / primary build controller / agents / tools / execution
```

The host remains the execution authority. CodeSleuth must not replace the host's native controller prompt.

Current external-host support is narrower. NovaClaw has a read-only MCP evidence adapter. Do not claim that arbitrary hosts automatically support CodeSleuth MCP, `/repo-*` commands, or OpenCode-specific configuration.

## 2. Before you change a user's repository

Only install CodeSleuth when the user asks for CodeSleuth or clearly asks you to set it up. Do not silently install it as a generic review dependency.

Before installation:

1. Resolve the target to its Git repository root.
2. Inspect `git status --short` and note pre-existing changes.
3. Check whether `.opencode/review-pack.json` already exists.
4. Check whether `tools/codesleuth` is already a tracked gitlink/submodule.
5. Check whether the repository already has OpenCode configuration that the user expects to preserve.
6. Determine whether the user wants a local/development installation, a reproducibly pinned dependency, or a release-clean repository.
7. Do not commit, push, reset, clean, or discard user changes unless the user explicitly asks for that Git operation.

CodeSleuth creates a pre-install snapshot and performs conflict-safe restoration later. Do not defeat that mechanism by manually deleting pre-existing `.opencode` files before installation.

## 3. Requirements

For the current full OpenCode integration, verify:

- Git 2.35 or newer;
- Python 3.10 or newer;
- `opencode` available when the user intends to run the OpenCode integration;
- Bun only when CodeSleuth's TypeScript development/smoke gates need to run.

The installer itself enforces the Git minimum.

## 4. Obtain CodeSleuth

Prefer an existing CodeSleuth checkout when one is already available and clearly identified by the user or repository.

If no checkout exists and the user asked you to install CodeSleuth, obtain the current repository from:

```text
https://github.com/DassaultFalconKing/CodeSleuth.git
```

For a temporary installer checkout on POSIX systems:

```bash
git clone https://github.com/DassaultFalconKing/CodeSleuth.git /tmp/codesleuth
```

For PowerShell, use a normal user-writable temporary or tools directory rather than inventing a repository-local dependency unless binding was requested.

Do not use `tools/codesleuth` merely as a convenient clone destination. That path has tracked dependency semantics when CodeSleuth binding is enabled.

## 5. Choose the installation lifecycle intentionally

Runtime installation and dependency binding are independent.

### Development/local installation without a tracked CodeSleuth dependency

Use the normal installer without `--bind-dependency`.

Resulting lifecycle: normally `unbound-active`.

This is the safer default when the user wants CodeSleuth available in a worktree but does not want the CodeSleuth source dependency committed to the project.

### Self-install into the CodeSleuth source checkout

When the target Git root is the CodeSleuth source repository itself, pass `--self-install`:

```bash
/path/to/codesleuth/install.sh . --self-install
```

Rules:

- `--self-install` is required for that target and invalid for any other repository;
- never combine `--self-install` with `--bind-dependency`;
- the TUI passes `--self-install` automatically when the selected target is the source checkout.

Successful installs upsert the target into the host-local tracked-repository registry (name, CodeSleuth source with exact commit, version). Inspect it with:

```bash
.opencode/bin/codesleuth-project --list
```

Refresh drops only paths that no longer exist; an existing but broken repository remains visible with degraded state. To remove a still-reachable entry:

```bash
.opencode/bin/codesleuth-project /path/to/repo --forget
```

`--forget` uses registry path normalization, returns exit code 1 when the entry does not exist, does not require a successful lifecycle probe, and deletes nothing from the target repository itself.

### Reproducibly pinned development dependency

Use `--bind-dependency` only when the user wants the target repository to record the exact CodeSleuth source revision.

CodeSleuth then stages normal Git submodule state:

```text
.gitmodules
tools/codesleuth  # gitlink to an exact CodeSleuth commit
```

The installer does not commit or push those changes.

Resulting lifecycle after runtime installation: `bound-active`.

### Release-clean repository

If the production/release repository must not contain CodeSleuth runtime files, reports, documentation traces, or a CodeSleuth dependency, do not leave a bound installation in that release state. Use the purge removal procedure in section 11 and inspect the resulting Git diff before producing the release commit.

A common policy is:

- developer branch/worktree: CodeSleuth installed, optionally bound;
- release branch/worktree: CodeSleuth fully uninstalled and purged before the release commit.

Do not implement this by `rm -rf`. Use CodeSleuth's lifecycle commands so pre-existing OpenCode files can be restored safely.

## 6. Configure unattended from user intent

The supported unattended path is `--settings-file` with a validated JSON payload.

Use defaults unless the user has a reason to change them. Do not manufacture aggressive permissions or arbitrary timeout tuning just because unattended operation is possible.

Supported settings schema:

```json
{
  "schemaVersion": 1,
  "profiles": ["generic"],
  "profilesMode": "auto",
  "permissions": {
    "preset": "review-safe",
    "websearch": "ask",
    "webfetch": "ask",
    "externalDirectory": "ask",
    "edit": "ask",
    "question": "allow",
    "doomLoop": "ask",
    "managePolicy": true
  },
  "runtime": {
    "exaEnabled": true,
    "watchdogEnabled": true,
    "stallSeconds": 480,
    "maxStallRecoveries": 2,
    "webStallSeconds": 180,
    "compactionReserved": 20000,
    "checkUpdatesOnStart": true
  },
  "agent": {
    "profile": "native",
    "model": ""
  }
}
```

Valid built-in profiles are:

```text
generic
rust
python
node
typescript
```

With `profilesMode: "auto"`, CodeSleuth detects profiles from tracked Git files. Prefer auto mode unless the user explicitly needs a manual profile selection.

Valid permission presets are:

- `review-safe`: least privilege; safe Git inspection is allowed while broad shell/edit/web work remains controlled;
- `balanced`: also allows common project verification commands such as pytest, cargo tests/checks, and common package-manager lint/typecheck/test commands;
- `autonomous`: broad shell access, while destructive/publishing Git operations remain guarded.

The individual values `websearch`, `webfetch`, `externalDirectory`, `edit`, `question`, and `doomLoop` accept only:

```text
allow
ask
deny
```

Valid agent profiles are:

```text
native
open-weight
codex
claude
```

`agent.model` is an optional model id string. Selecting a profile/model must not install a CodeSleuth primary prompt. OpenCode's native provider-specific `build` controller remains authoritative.

### Permission mapping from typical user requests

Use the user's stated intent, not your own appetite for permissions.

Review-only, no edits:

```json
{
  "permissions": {
    "preset": "review-safe",
    "edit": "deny"
  }
}
```

Review plus normal local tests/lint:

```json
{
  "permissions": {
    "preset": "balanced",
    "edit": "ask"
  }
}
```

No network access:

```json
{
  "permissions": {
    "websearch": "deny",
    "webfetch": "deny"
  },
  "runtime": {
    "exaEnabled": false
  }
}
```

User explicitly wants broad autonomous implementation work:

```json
{
  "permissions": {
    "preset": "autonomous",
    "edit": "allow"
  }
}
```

Do not infer `autonomous` merely from the fact that the installation is unattended.

### Existing OpenCode permission policy

If the repository has an existing OpenCode permission policy that the user wants to keep authoritative, do not blindly replace it. `permissions.managePolicy: false` tells CodeSleuth not to manage the permission policy while still allowing other CodeSleuth settings to be applied.

## 7. Perform an unattended installation

Write the settings payload to a temporary file outside the target repository unless the user wants it versioned.

POSIX example:

```bash
/path/to/codesleuth/install.sh /path/to/target-repo \
  --settings-file /tmp/codesleuth-settings.json
```

Pinned dependency example:

```bash
/path/to/codesleuth/install.sh /path/to/target-repo \
  --settings-file /tmp/codesleuth-settings.json \
  --bind-dependency
```

PowerShell uses the equivalent wrapper and the same installer arguments:

```powershell
C:\path\to\codesleuth\install.ps1 C:\path\to\target-repo --settings-file C:\Temp\codesleuth-settings.json
```

For an already versioned installation, use `--update` rather than pretending it is a fresh install:

```bash
/path/to/codesleuth/install.sh /path/to/target-repo \
  --update \
  --settings-file /tmp/codesleuth-settings.json
```

Use `--adopt-existing-pack` only for the older unversioned review-pack state that the installer identifies as a legacy installation. It is not a general force option.

Avoid `--force-pack-files` unless the user explicitly wants locally modified CodeSleuth-managed files replaced after you have inspected the conflicts.

Installed floating updates use `.opencode/bin/review-pack-update.py`. After a successful update, Verify must pass before any automatic TUI restart. See [`SELF-UPDATE.md`](SELF-UPDATE.md). Use `--restart` only when the user wants the updated TUI to replace the current CodeSleuth process.

Live 0.4.0 compatibility filenames remain `review-pack.json`, `review-pack-smoke.py`, and `REVIEW_PACK_*` environment names. Do not invent a parallel `codesleuth.json` write path unless the current installer already materializes it. The naming inventory is [`CODESLEUTH-NAMING-CUTOVER.md`](CODESLEUTH-NAMING-CUTOVER.md).

## 8. Verify after installation or configuration

Run verification from the target repository.

Primary installed smoke/integrity gate:

```bash
python3 .opencode/bin/review-pack-smoke.py .
```

Then inspect:

```bash
git status --short
git diff -- .
git diff --cached -- .
```

If dependency binding was requested, verify that `tools/codesleuth` is a gitlink at the intended commit and that the `.gitmodules` change is expected.

Do not report a check as passed unless you actually ran it successfully.

## 9. How to use CodeSleuth after installation

For the full OpenCode integration, launch through the installed wrapper:

```bash
.opencode/bin/opencode-review
```

PowerShell:

```powershell
.\.opencode\bin\opencode-review.ps1
```

Current OpenCode command entry points include:

```text
/repo-prompts
/repo-profile
/repo-review
/repo-review-resume
/repo-docs
/repo-report
/repo-map
/repo-contracts
/eha-test
/eha-repair
/eha-status
/playbook
```

Use `/repo-prompts` when the user wants help choosing the next repository-analysis task. Use `/repo-review` for an evidence-first whole-repository or PR review. Use `/repo-review-resume` only when durable review state already exists. Use `/repo-map` for a bounded repository-context neighborhood, `/repo-contracts` for bounded protected-capability dependency/impact navigation, and `/eha-status` for bounded campaign/SIB/repair history. `/playbook` routes stored multi-step workflows without creating a second controller.

All three Mermaid surfaces report their bounds and provenance, but remain derived presentation. Material findings still require exact current source evidence and blob/line identity. Protected meaning remains in `docs/protected-capabilities.json`; EHA/SIB verdicts remain in `eha.ndjson` and do not transfer between commits through a diagram.

### If you are not OpenCode

Do not pretend OpenCode slash commands are native commands in your own host.

You may:

- install/configure CodeSleuth for the user's OpenCode workflow when asked;
- inspect CodeSleuth's ordinary Markdown reports under `.codesleuth/reports/` when they exist and the user authorizes it;
- use a documented host adapter when that adapter actually exists.

Do not claim that your host is a supported CodeSleuth runtime merely because you can read these files.

## 10. Reports, local state, and publication

CodeSleuth keeps operational/report state local by default through the repository-local Git exclude file, not by silently rewriting the project's tracked `.gitignore`.

Known local state includes:

```text
.codesleuth/
.opencode/state/
.opencode/cache/
.opencode/logs/
.opencode/sessions/
.opencode/snapshots/
```

Report bodies can contain source excerpts, credentials, API responses, or diagnostics. Do not commit or publish them automatically.

A maintainer may intentionally track sanitized guidance such as `.codesleuth/reports/README.md`, but fresh clones should not inherit local evidence accidentally.

## 11. Remove CodeSleuth correctly

Never remove CodeSleuth with a blind recursive delete of `.opencode`, `.codesleuth`, or `tools/codesleuth`. Those locations can contain pre-existing user configuration, recovery evidence, or a submodule with local work.

### Remove runtime and bound dependency, preserve local traces

Default uninstall restores pre-CodeSleuth configuration, removes the CodeSleuth runtime, removes a bound dependency by default, and archives known CodeSleuth traces locally:

```bash
/path/to/codesleuth/install.sh /path/to/target-repo --uninstall
```

The resulting lifecycle is `uninstalled-preserved` when an archive is retained.

Sensitive evidence can be present in `.codesleuth/archive`; it remains locally excluded by default.

### Remove runtime and dependency and purge ordinary traces

Use this for a release-clean target when the user wants CodeSleuth removed from the repository/worktree:

```bash
/path/to/codesleuth/install.sh /path/to/target-repo \
  --uninstall \
  --purge-traces
```

The intended lifecycle is `uninstalled-purged`.

Purge removes the active runtime, bound dependency, CodeSleuth backups, and ordinary known local traces after conflict-safe restore. If a pre-existing file changed after installation, restore-conflict evidence under `.codesleuth/restore-conflicts/` is retained rather than destroying user work.

After purge, inspect the working tree and staged changes. In particular, confirm the intended removal/restoration of:

```text
.opencode/ CodeSleuth-managed runtime files
tools/codesleuth
CodeSleuth's .gitmodules entry
CodeSleuth-managed AGENTS.md reports pointer
ordinary .codesleuth local state
```

Do not claim the repository is release-clean until the resulting Git state has been inspected.

### Remove runtime but keep the pinned dependency

```bash
/path/to/codesleuth/install.sh /path/to/target-repo \
  --uninstall \
  --keep-dependency
```

This intentionally leaves the exact CodeSleuth dependency while removing the active runtime.

### Remove only the dependency and keep the runtime

From an installed target:

```bash
.opencode/bin/codesleuth-project . --unbind
```

This removes the project-level dependency using normal tracked submodule semantics. It does not uninstall the runtime.

CodeSleuth refuses dependency removal when the submodule worktree is dirty or when its checked-out HEAD diverges from the superproject gitlink. Do not bypass that refusal by deleting the directory unless the user explicitly resolves the local work first.

## 12. Release-clean developer workflow

When the same project uses CodeSleuth heavily during development but production/release commits must not carry it:

1. Keep CodeSleuth installed in the developer worktree or development branch.
2. Optionally bind the dependency there if exact reproducibility is valuable.
3. Before preparing the production/release commit, make sure unrelated user changes are understood and protected.
4. Run uninstall with `--purge-traces` in the release target.
5. Let lifecycle restoration preserve any pre-existing OpenCode configuration.
6. Inspect unstaged and staged Git diffs.
7. Resolve any `.codesleuth/restore-conflicts/` evidence instead of deleting it blindly.
8. Confirm that the release tree contains no unintended CodeSleuth gitlink, `.gitmodules` entry, managed runtime files, local report bodies, or managed reports pointer.
9. Commit the release cleanup only when the user asked you to create that commit.

If the release is produced from a separate clean clone/worktree that never installs CodeSleuth, prefer that simpler boundary over repeatedly installing and uninstalling in the release worktree.

## 13. Safety invariants

- Preserve the user's pre-existing OpenCode configuration.
- Do not widen permissions beyond the user's request.
- Do not convert unattended installation into autonomous coding authority.
- Do not install a second primary controller or CodeSleuth supervisor prompt.
- Do not treat inventory, summaries, graphs, or Mermaid as verified finding evidence.
- Do not claim tests or verification passed unless they ran successfully.
- Do not publish local reports without reviewing them for sensitive material.
- Do not silently commit or push installer changes.
- Do not discard dirty or divergent CodeSleuth submodule work.
- Prefer the existing lifecycle commands over manual cleanup.

## 14. Canonical references when behavior is unclear

Read the smallest authoritative source needed for the question:

- [`../README.md`](../README.md): current product/manual surface and CLI reference;
- [`PROJECT-LIFECYCLE.md`](PROJECT-LIFECYCLE.md): install/bind/unbind/uninstall and restoration rules;
- [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md): product/runtime ownership and frozen-core boundaries;
- [`NOVACLAW-MCP.md`](NOVACLAW-MCP.md): current external-host MCP boundary;
- [`../install.py`](../install.py): actual installer arguments and settings-file path;
- [`../pack/.opencode/bin/review_pack_tui_core.py`](../pack/.opencode/bin/review_pack_tui_core.py): settings defaults, validation, and permission mapping;
- [`../pack/.opencode/bin/codesleuth_project.py`](../pack/.opencode/bin/codesleuth_project.py): lifecycle implementation and conflict-safe removal;
- [`../tests/test_project_lifecycle.py`](../tests/test_project_lifecycle.py): executable lifecycle acceptance behavior.

If documentation and executable behavior diverge, report the divergence instead of choosing whichever text is more convenient.

## 15. Maintaining this file

This guide intentionally tracks the canonical English `README.md` through the `README-SOURCE-BLOB` marker near the top.

When `README.md` changes:

1. inspect whether the product model, supported hosts, commands, installer behavior, settings, permissions, lifecycle, or removal semantics changed;
2. update this guide when those changes affect agent operation;
3. verify the implementation sources above when a README change touches lifecycle/configuration behavior;
4. only then refresh the `README-SOURCE-BLOB` marker to the new English README blob.

Do not refresh the marker merely to make a parity test green without reviewing operational parity.
