# User Guide

This guide explains how to install, configure, validate, update, and use the
OpenCode Repository Deep Review Pack in any Git repository.

The recommended workflow is:

```text
review-pack source
      ↓
setup TUI
      ↓
install managed .opencode environment
      ↓
smoke validation
      ↓
launch OpenCode through pack launcher
      ↓
/repo-prompts
      ↓
/repo-review | /repo-docs | /repo-profile | /repo-review-resume
```

## 1. Prerequisites

Required:

- Git;
- Python 3.9 or newer;
- OpenCode installed and available as `opencode`;
- a Git repository that you want to review or document.

For the interactive TUI, the first launch may require network access. The pack
creates an isolated Python virtual environment and installs the pinned
`textual==8.2.8` dependency there. It does not add Textual to the target
repository's Python dependencies.

For self-update from GitHub, Git must be able to reach the recorded pack remote.

## 2. Recommended installation: setup TUI

From a standalone checkout of the review pack, launch the setup UI and point it
at the target repository.

Linux/macOS/WSL:

```bash
./review-pack /path/to/target-repo
```

PowerShell:

```powershell
.\review-pack.ps1 C:\path\to\target-repo
```

The distribution TUI can install a fresh pack, safely overlay an existing
`.opencode` environment, adopt an older unversioned review-pack installation, or
update a managed installation.

### Questions the TUI asks

The setup screen collects the project policy instead of silently choosing it.

1. **Installation operation**
   - fresh/safe overlay;
   - adopt an older unversioned pack with backup;
   - update an existing managed installation;
   - configure an already installed pack without replacing pack files.

2. **Repository profile**
   - automatic profile detection from tracked files; or
   - manual selection for mixed/unusual repositories.

   Built-in profile families are:

   ```text
   generic
   rust
   python
   node
   typescript
   ```

3. **Permission preset**
   - `review-safe` (recommended): read-oriented, destructive Git actions denied,
     most non-read shell work asks first;
   - `balanced`: common local verification commands may run automatically;
   - `autonomous`: broad local shell access, but destructive Git operations still
     require explicit confirmation.

4. **Explicit sensitive permissions**
   - `websearch`: allow / ask / deny;
   - `webfetch`: allow / ask / deny;
   - repository edits: allow / ask / deny;
   - access outside the repository: allow / ask / deny.

5. **Runtime behavior**
   - enable/disable Exa-backed web search runtime;
   - enable/disable `opencode-keepalive` watchdog;
   - global stall timeout;
   - web tool stall timeout;
   - maximum watchdog recoveries;
   - reserved compaction tokens;
   - whether the TUI should check upstream updates when opened.

Before applying, the TUI shows the resulting policy/configuration preview.

## 3. Security defaults

The default `review-safe` policy is intentionally conservative.

Pack defaults include:

- tracked repository reads are allowed;
- `.env` and `.env.*` are denied, while `.env.example` remains readable;
- normal read-only Git inspection commands are allowed;
- other shell commands ask by default;
- `git push*`, `git reset --hard*`, and `git clean*` are denied in the default
  project policy;
- reviewer/scout agents remain read-only even if the project policy later becomes
  more permissive;
- external directory access asks by default;
- web search/fetch ask by default;
- the repository deep-review skill is allowed while unrelated skills ask.

Web tools are deliberately separate from the Exa runtime switch. Enabling
`OPENCODE_ENABLE_EXA=1` only makes Exa-backed `websearch` available; the OpenCode
permission still controls whether the agent may execute it without asking.

Web search queries and fetched URLs may be sent to external services. Choose
`ask` or `deny` for repositories where that disclosure is inappropriate.

## 4. Non-interactive installation

The TUI is a front-end over the same installer contract. CI and scripted setups
should call the deterministic installer directly.

Linux/macOS/WSL:

```bash
./install.sh /path/to/target-repo
```

PowerShell:

```powershell
.\install.ps1 C:\path\to\target-repo
```

Both wrappers delegate all logic to the same `install.py` implementation.

Force a profile set when automatic detection is not desired:

```bash
./install.sh /path/to/target-repo \
  --profile generic \
  --profile rust \
  --profile typescript
```

Do not use `--force-pack-files` casually. It intentionally overwrites locally
modified pack-managed files.

## 5. What is installed

A normal target repository receives:

```text
.opencode/
├── agents/
├── commands/
├── skills/
├── tools/
├── plugins/
├── profiles/
│   ├── builtin/
│   └── detected.json
├── bin/
│   ├── review-pack
│   ├── review-pack.ps1
│   ├── review-pack-smoke.py
│   ├── review-pack-update
│   ├── review-pack-update.ps1
│   ├── review-pack-update.py
│   ├── opencode-review
│   └── opencode-review.ps1
├── opencode.json
├── review-pack.json
└── review-pack-user.json
```

Important files:

- `review-pack.json`: installer/update metadata, pack version, source commit/ref,
  managed-file hashes, conflicts;
- `review-pack-user.json`: project-level settings selected through the TUI;
- `opencode.json`: effective OpenCode configuration;
- `profiles/detected.json`: active profile set;
- `.opencode/state/`: local runtime state, checkpoints, update conflicts,
  backups, TUI runtime. This directory is ignored by Git.

## 6. Validate the installation

Always run the target-local smoke test after initial install, adoption, or
update.

Linux/macOS/WSL:

```bash
cd /path/to/target-repo
python3 .opencode/bin/review-pack-smoke.py .
```

PowerShell:

```powershell
cd C:\path\to\target-repo
python .opencode\bin\review-pack-smoke.py .
```

Expected prefix:

```text
PACK SMOKE PASS
```

The smoke validates the managed pack surface, metadata schema, active profiles,
permission shape, TUI files, launchers, and update tooling. Warnings about an
intentionally permissive policy are warnings, not fabricated failures.

## 7. Open the installed control TUI

After installation the target repository is self-contained for normal use.

Linux/macOS/WSL:

```bash
.opencode/bin/review-pack
```

PowerShell:

```powershell
.opencode\bin\review-pack.ps1
```

The installed TUI can:

- inspect installation/version/profile state;
- edit project permission/runtime settings;
- apply the settings to `opencode.json`;
- run smoke validation;
- check for upstream pack updates;
- apply a self-update;
- show/save suggested prompts;
- launch OpenCode with the correct runtime environment.

## 8. Launch OpenCode correctly

Prefer the pack launcher instead of plain `opencode`.

Linux/macOS/WSL:

```bash
.opencode/bin/opencode-review
```

PowerShell:

```powershell
.opencode\bin\opencode-review.ps1
```

The launcher reads `review-pack-user.json`. When Exa runtime is enabled it sets:

```text
OPENCODE_ENABLE_EXA=1
```

When disabled, the launcher does not expose that flag.

## 9. First command inside OpenCode

Start with:

```text
/repo-prompts
```

The prompt advisor inspects the actual repository and proposes 5-8
copy/paste-ready tasks appropriate to the detected stack and current repository
state.

The main commands are:

```text
/repo-prompts
/repo-profile
/repo-review
/repo-docs
/repo-review-resume
```

### Typical review prompt

```text
/repo-review map the repository architecture, identify authority boundaries and
invariants, then perform an in-depth correctness review. Inspect callers,
callees, tests, CI, migrations and documentation, not only obvious entrypoints.
Record exact evidence for every material finding.
```

### Typical branch/PR-style review prompt

```text
/repo-review compare current HEAD and worktree against the canonical base branch.
Review changed code and unchanged consumers/contracts/tests/CI. Distinguish
blockers from improvements and state all unreviewed areas.
```

### Documentation prompt

```text
/repo-docs build an evidence-first repository guide from current source,
manifests, CI and tests. Separate documented guarantees from behavior inferred
from code and call out stale or contradictory documentation.
```

## 10. Profiles and profile generation

Automatic detection writes the initial active profile set. For a deeper,
repository-specific profile use:

```text
/repo-profile
```

The profile architect follows this order:

```text
local manifests / lockfiles / CI / config
        ↓
identify uncertain or version-sensitive facts
        ↓
websearch discovery, if permitted
        ↓
webfetch primary official documentation, if permitted
        ↓
profile proposal
        ↓
effective edit permission
        ↓
generated project profile
```

Search snippets are not treated as authority. No successful tool call means no
claim of external verification.

## 11. Update the pack

Check whether the recorded upstream source moved:

```bash
.opencode/bin/review-pack-update --check
```

PowerShell:

```powershell
.opencode\bin\review-pack-update.ps1 --check
```

Apply an update:

```bash
.opencode/bin/review-pack-update
```

or:

```powershell
.opencode\bin\review-pack-update.ps1
```

The updater clones the new source into a temporary directory and runs the **new
version's installer**. This allows the installer/update protocol itself to
evolve safely.

### Update safety

For pack-managed files:

- unchanged local file -> replace with upstream version;
- locally modified file -> preserve local file and save incoming version under
  `.opencode/state/update-conflicts/<timestamp>/...incoming`;
- new upstream file -> install;
- retired upstream file -> delete only if still identical to the old managed
  hash.

`opencode.json` uses a previous-default/current-user/new-default merge so normal
user overrides survive pack updates.

After an update with unresolved managed-file conflicts,
`review-pack.json` records:

```json
{
  "complete": false
}
```

Resolve the conflict and run smoke again.

## 12. Adopt an older unversioned installation

Older installations without `.opencode/review-pack.json` cannot safely
self-update because no trusted managed-file hashes exist.

Use the current distribution once:

```bash
./install.sh /path/to/target-repo --adopt-existing-pack
```

PowerShell:

```powershell
.\install.ps1 C:\path\to\target-repo --adopt-existing-pack
```

Known old pack files are backed up under:

```text
.opencode/state/installer-backups/legacy-adoption/<timestamp>/
```

After adoption the installation becomes versioned and can use normal update
commands.

## 13. What should be committed in the target repository

Recommended to commit:

```text
.opencode/.gitignore
.opencode/agents/
.opencode/commands/
.opencode/plugins/
.opencode/profiles/builtin/
.opencode/skills/
.opencode/tools/
.opencode/bin/
.opencode/opencode.json
.opencode/review-pack.json
.opencode/review-pack-user.json
```

Generated project profiles may also be committed once reviewed.

Do not commit:

```text
.opencode/state/
.opencode/cache/
.opencode/logs/
.opencode/sessions/
.opencode/node_modules/
.opencode/**/__pycache__/
```

This keeps the project policy and review machinery reproducible while keeping
session/checkpoint/runtime state local.

## 14. Large-context operating rule

A 1M-token context is headroom, not a target occupancy.

The review pack intentionally uses:

```text
deterministic inventory
→ bounded scouts
→ exact parent verification
→ durable findings/checkpoints
→ compaction-safe recovery
→ selective evidence rehydration
```

Do not defeat the design by asking the model to ingest the entire repository at
once. The repository should remain addressable; only the current reasoning set
should be resident in model context.
