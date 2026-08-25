# OpenCode Repository Deep Review Pack

Portable, evidence-first OpenCode environment for deep repository review,
architecture documentation, profile generation, and long-running large-context
analysis.

The pack is designed for arbitrary Git repositories and keeps the repository
**addressable rather than resident** in model context. It combines deterministic
inventory, bounded scouts, exact evidence recording, durable checkpoints,
compaction recovery, watchdog support, Exa/web verification, safe updates, and a
cross-platform setup/control TUI.

Current distribution version: see [`VERSION`](VERSION).

## Recommended start

Prerequisites: Git, Python 3.9+, and OpenCode available as `opencode`.

From a standalone pack checkout:

Linux/macOS/WSL:

```bash
./review-pack /path/to/target-repo
```

PowerShell:

```powershell
.\review-pack.ps1 C:\path\to\target-repo
```

The first TUI launch creates an isolated runtime and installs pinned
`textual==8.2.8`; it does not modify the target project's Python dependencies.

In the TUI, review and apply:

- install/adopt/update operation;
- automatic or manual repository profiles;
- `review-safe`, `balanced`, or `autonomous` permission preset;
- `websearch`, `webfetch`, edit, and external-directory permissions;
- Exa runtime enablement;
- watchdog timeouts/recovery policy;
- compaction reserve;
- update-check behavior.

Then validate the installed target:

```bash
cd /path/to/target-repo
python3 .opencode/bin/review-pack-smoke.py .
```

Expected prefix:

```text
PACK SMOKE PASS
```

Launch OpenCode through the pack launcher:

```bash
.opencode/bin/opencode-review
```

PowerShell:

```powershell
.opencode\bin\opencode-review.ps1
```

Inside OpenCode, start with:

```text
/repo-prompts
```

The advisor inspects the actual repository and proposes copy/paste-ready prompts
for the highest-value review, documentation, profile, CI/runtime, and external
API verification tasks.

## Main OpenCode commands

```text
/repo-prompts
/repo-profile
/repo-review
/repo-docs
/repo-review-resume
```

## Built-in profiles

```text
generic
rust
python
node
typescript
```

Mixed repositories may activate several profiles at once.

## Security model

The default `review-safe` policy is deliberately conservative:

- `.env` and `.env.*` reads are denied; `.env.example` remains readable;
- normal read-only Git inspection is allowed;
- other shell work asks by default;
- destructive Git actions such as `git push*`, `git reset --hard*`, and
  `git clean*` are denied by the default project policy;
- reviewer/scout agents remain read-only;
- external-directory access asks by default;
- `websearch` and `webfetch` ask by default;
- Exa runtime availability and permission to execute web tools are separate
  controls.

When enabled, the launcher sets:

```text
OPENCODE_ENABLE_EXA=1
```

The profile/review workflow uses web search only for discovery and web fetch for
primary-source verification. No successful web tool call means no claim of web
verification.

## Installed control center

After installation, use the target-local TUI:

```bash
.opencode/bin/review-pack
```

PowerShell:

```powershell
.opencode\bin\review-pack.ps1
```

It can reconfigure project policy, run smoke, check/apply updates, show suggested
prompts, and launch OpenCode.

## Non-interactive install

Linux/macOS/WSL:

```bash
./install.sh /path/to/target-repo
```

PowerShell:

```powershell
.\install.ps1 C:\path\to\target-repo
```

Both wrappers delegate to the same `install.py`; platform wrappers contain no
separate install semantics.

Manual profile example:

```bash
./install.sh /path/to/target-repo \
  --profile generic \
  --profile rust \
  --profile typescript
```

## Managed installation state

The target receives:

```text
.opencode/review-pack.json
.opencode/review-pack-user.json
```

`review-pack.json` records version/source/managed-file hashes/update conflicts.
`review-pack-user.json` records the project-level TUI policy and profile/runtime
choices.

Local runtime state is kept under `.opencode/state/` and ignored by Git.

## Safe updates

Check:

```bash
.opencode/bin/review-pack-update --check
```

Update:

```bash
.opencode/bin/review-pack-update
```

PowerShell equivalents:

```powershell
.opencode\bin\review-pack-update.ps1 --check
.opencode\bin\review-pack-update.ps1
```

Locally modified managed files are preserved; incoming versions are written to
`.opencode/state/update-conflicts/`. `opencode.json` uses a three-way defaults
merge so ordinary project overrides survive.

For a project that pins this pack as a Git submodule, prefer **pinned update
mode**: advance the submodule intentionally, then run that exact checkout's
`install.sh . --update`. This keeps the installed `.opencode` and submodule
revision auditable together.

## Documentation

Complete daily-use guide:

- [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md)

Maintainer guide for extracting this pack into a standalone repository and using
it as a project submodule/subrepo:

- [`docs/MAINTAINER-SUBREPO.md`](docs/MAINTAINER-SUBREPO.md)

## Lifecycle verification

Run from the pack repository:

```bash
python3 tests/test_lifecycle.py
```

The lifecycle gate covers installation, profile detection, managed metadata,
config preservation, update safety, legacy adoption, and target smoke behavior.

## Large-context discipline

A 1M-token context is headroom, not a target occupancy. The protocol is:

```text
deterministic inventory
→ bounded component scouts
→ parent re-verification of exact source
→ durable finding ledger/checkpoints
→ compaction-safe recovery
→ selective evidence rehydration
```

Do not bulk-load an entire large repository merely because the model technically
accepts it. The working set belongs in model context; the repository belongs on
disk.
