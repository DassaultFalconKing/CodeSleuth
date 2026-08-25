# CodeSleuth

**Evidence-first repository intelligence**

CodeSleuth is an evidence-oriented control panel, configuration layer, and lifecycle manager for OpenCode repository review. It keeps repositories directly usable by OpenCode, presents readiness and evidence state clearly, and installs project-specific policy and profiles without replacing OpenCode's models, agents, tools, commands, or durable review execution.

OpenCode is the current runtime/integration environment. Historical `review-pack*` commands remain compatibility aliases while the public surface moves to `codesleuth`.

## What CodeSleuth owns

A target repository can contain three deliberately separate layers:

```text
project/
├── tools/codesleuth/        # optional pinned Git submodule; reusable CodeSleuth source
├── .opencode/               # project-owned CodeSleuth/OpenCode policy, agents, profiles and tools
└── .codesleuth/             # local backups / preserved review artifacts; gitignored by default
```

`tools/codesleuth/` is intentionally **not** gitignored when the user chooses dependency mode. The superproject records an exact CodeSleuth commit as a Git gitlink. `.opencode/` is the target project's installed contract. `.codesleuth/` is local safety state and is ignored by default.

## Security and credential warning

CodeSleuth audits a developer repository through OpenCode. If the operator grants OpenCode permission to read files, run tests, invoke tools, or access development services, those operations may legitimately use environment variables, local credentials, test tokens, API keys, cookies, connection strings, or other secrets available on that developer host.

CodeSleuth **does not blindly redact all evidence**. Blanket redaction would make some real test and audit workflows incorrect. Consequently, review findings, excerpts, logs, preserved traces, generated prompts, or reports may contain sensitive values that were visible to the authorized runtime.

Safety defaults:

- `.codesleuth/` is gitignored;
- `.opencode/state/`, logs, caches, sessions and snapshots are gitignored;
- preserved uninstall archives remain gitignored;
- CodeSleuth warns before destructive uninstall choices;
- project policy controls web/edit/external-directory permissions;
- built-in repository profiles do not grant extra permissions;
- **inspect and sanitize reports before sharing or force-adding ignored artifacts to Git.**

CodeSleuth cannot guarantee that arbitrary reports authored by an LLM outside its managed local-state paths contain no secrets. Treat audit output like other developer diagnostics.

## Install into any Git repository

Prerequisites: Git, Python 3.10+, and OpenCode available as `opencode`.

From a CodeSleuth checkout:

```bash
./codesleuth /path/to/project
```

PowerShell:

```powershell
.\codesleuth.ps1 C:\path\to\project
```

The TUI lets you choose profiles, permission policy, runtime settings, and whether CodeSleuth should pin itself into the target repository as:

```text
tools/codesleuth
```

For a non-interactive install without a persistent submodule:

```bash
./install.sh /path/to/project
```

For a reproducible development-repository install with a pinned CodeSleuth dependency:

```bash
./install.sh /path/to/project --bind-dependency
```

The binding is an explicit Git change: `.gitmodules` and the `tools/codesleuth` gitlink are staged for the operator to review and commit. CodeSleuth never commits or pushes the target repository on the user's behalf.

CLI targets are normalized to the containing Git root, so passing `/path/to/project/subdir` still installs into `/path/to/project`.

## Reversible first install

Before the first install CodeSleuth snapshots the pre-existing project OpenCode configuration under:

```text
.codesleuth/backups/pre-install/<timestamp>/
```

The backup records hashes and copies project configuration while excluding obvious ephemeral caches, logs, sessions, state, virtual/runtime dependencies, and bytecode. Existing `.gitignore` and `.gitmodules` are backed up for recovery, but uninstall does not blindly replace them because that could erase unrelated changes made after installation.

A pointer is kept at `.codesleuth/preinstall.json`. An upgrade from an older already-installed review-pack records a `pre-0.3-upgrade` baseline instead of falsely claiming it predates CodeSleuth.

The installer also writes a managed block to the target root `.gitignore` for local CodeSleuth/OpenCode state. It does not add an ignore for `tools/codesleuth`. If the project already ignores that dependency path, CodeSleuth refuses to override the project's ignore policy and explains the conflict.

## Uninstall

From the installed project:

```bash
.opencode/bin/codesleuth-project --uninstall .
```

Default uninstall behavior:

1. archive CodeSleuth settings, profiles and known review state under `.codesleuth/archive/<timestamp>/`;
2. restore the pre-CodeSleuth `.opencode` snapshot when safe;
3. remove CodeSleuth-owned runtime files;
4. remove the bound `tools/codesleuth` submodule/gitlink when present and clean;
5. keep the archive gitignored.

To remove CodeSleuth and its local traces/backups:

```bash
.opencode/bin/codesleuth-project --uninstall . --purge-traces
```

To remove the installed runtime while intentionally retaining the pinned submodule:

```bash
.opencode/bin/codesleuth-project --uninstall . --keep-dependency
```

Restore compares pre-install, post-install, and current files. A post-install edit to a pre-existing `.opencode` file stays in the worktree; baseline/current copies and an explicit manifest are retained under gitignored `.codesleuth/restore-conflicts/`. Required conflict evidence survives purge.

The TUI exposes the same **Preserve traces** / **Purge traces** choice. CodeSleuth refuses to remove either a dirty submodule or a clean detached local commit that differs from the recorded gitlink.

CodeSleuth only knows how to archive/delete its managed settings and local review-state namespaces. Reports deliberately authored elsewhere in the project are project files and are never guessed at or deleted automatically.

Runtime and dependency are independent: `--uninstall --keep-dependency` leaves a **dependency-only** state, while `.opencode/bin/codesleuth-project --unbind .` removes only the dependency and keeps the installed runtime.

## Update model

For reproducible projects, advance the pinned CodeSleuth submodule intentionally, then materialize that exact version into `.opencode`:

```bash
git -C tools/codesleuth fetch origin
git -C tools/codesleuth checkout --detach <accepted-codesleuth-sha>
./tools/codesleuth/install.sh . --update
```

Then review and commit both the gitlink change and project `.opencode` changes together.

Fresh clone and recovery administration:

```bash
git clone --recurse-submodules <project-url>
git submodule update --init --recursive  # for an existing clone
```

To revert a pin, checkout the previous accepted SHA in `tools/codesleuth`, materialize that checkout with `install.sh . --update`, inspect, and commit both changes. The TUI disables target-local floating update controls in pinned detached mode; an explicit `remote + ref` is required for floating updates.

A detached CodeSleuth checkout records its exact source commit but **does not invent a floating branch from `origin/HEAD`**. Floating update behavior requires an explicit source ref.

## Main OpenCode commands

```text
/repo-prompts
/repo-profile
/repo-review
/repo-docs
/repo-review-resume
```

Review state is durable under local `.opencode/state/reviews/` and is bound to tracked source blob hashes so changed files can invalidate stale coverage.

## Development

Install development/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the Python gates:

```bash
python -m pytest
ruff check .
```

The dev set includes `pytest`, `pytest-asyncio`, Ruff, and the pinned Textual runtime used by the TUI. Textual UI tests use `App.run_test()` and `Pilot` rather than terminal scraping.

The existing Bun durable-state smoke remains part of acceptance:

```bash
bun install --frozen-lockfile
bun tests/review_state_smoke.ts
```

## Current compatibility names

The imported v0.2.1 implementation used `review-pack`, `review-pack-user.json`, `review-pack.json`, and `ReviewPackApp`. Those names remain compatibility surfaces during the CodeSleuth migration. New user-facing entrypoints use `codesleuth` where practical without breaking existing installed targets.

## Provenance

CodeSleuth was extracted from `DassaultFalconKing/Aleph_Rugent`.

- frozen Aleph source commit: `b00f83b81d50b2ac804fd24c83df0db86fe01c00`
- source subtree: `opencode-repo-review-pack/`
- imported behavior/version: `0.2.1`
- initial imported tree: `0037ea6c33584bc280dfc9152d623125d35f2f15`

The first standalone import preserved that tree exactly. CodeSleuth development is now owned by this repository.

## Watchdog roadmap

The current runtime retains the existing OpenCode keepalive watchdog. A separate follow-up will integrate the stronger watchdog/recovery functionality developed in Aleph_Rugent. That work is intentionally separate from installation/dependency/uninstall semantics so a runtime watchdog cannot accidentally become the package manager. Civilization has limits.
