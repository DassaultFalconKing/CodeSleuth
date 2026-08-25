# CodeSleuth

```text
+-------------------------------------------------+
|  CODE:SLEUTH // EVIDENCE OPERATIONS CONSOLE    |
+----------------------+--------------------------+
                       .-""""-.
                     .'  ____  '.
                    /   /_  _\   \
                   |   |o || o|   |
                   |   |__||__|   |
                   |      /\      |
                    \   .____.   /
                 ____'.\____/.'____
               .' ___/|  /\  |\___ '.
              /__/    | /  \ |    \__\
                   [ TARGET : SOURCE ]
                   [ EVIDENCE : LIVE ]
```

**Code-discipline for LLM repository work.**

CodeSleuth is a small discipline layer for coding agents. It packages reusable review Skills, repository profiles, durable evidence conventions, a terminal control panel, and a few bounded repository tools. The host agent still owns the model, controller, session, permissions, tool routing, and execution loop.

Current version: **0.3.0**.

Current implementation baseline:

- source-checkout **Update** explicitly fetches current `origin/main` and only fast-forwards a clean local `main`, ignoring stale branch-tracking metadata;
- the active TUI surface stays at the top of the content area; the large brand block and bottom Footer can be hidden independently;
- the left navigation can collapse/restore, while the right Keys/Help panel can collapse/restore or be closed for the current TUI session;
- the external MCP evidence adapter is repository-bound, bounded and hardened as a read-only evidence surface rather than an alternate agent runtime.

| Surface | Status |
| --- | --- |
| OpenCode | current full installed host integration |
| NovaClaw | current external host through read-only MCP evidence |
| Codex, Cursor, Hermes, BodegaOne, Pi-harness | planned host-integration targets after hardening |
| CodeSleuth-owned model runtime / supervisor | intentionally not part of the product |

## Contents

- [Basics](#basics)
- [User manual](#user-manual)
  - [Quickstart](#quickstart)
  - [In depth](#in-depth)
  - [TUI reference](#tui-reference)
  - [CLI reference](#cli-reference)
  - [Environment reference](#environment-reference)
- [Extending CodeSleuth](#extending-codesleuth)
- [Contributing](#contributing)
- [Roadmap and chores](#roadmap-and-chores)
- [Security and local state](#security-and-local-state)

# Basics

## What problem does CodeSleuth solve?

LLMs are good at reading code, but large repository work fails in very predictable ways:

- the repository is larger than the model's useful working context;
- finding files is not the same thing as understanding them;
- a scout or subagent summary can be wrong;
- a long review can lose state after compaction or a new session;
- a PR can look correct locally while breaking an unchanged caller, schema, migration, test, or operational contract;
- agents often claim more coverage than they actually performed.

CodeSleuth gives the host agent a repeatable discipline for these problems:

```text
repository
  -> deterministic inventory
  -> bounded inspection
  -> architecture/context map
  -> exact source evidence
  -> verification
  -> finding/report/checkpoint
```

The simple rule is: **discover broadly, verify narrowly, and persist what matters.**

## What can it do today?

CodeSleuth can support:

- whole-repository review;
- large PR or commit-range review;
- architecture and component mapping;
- repository documentation derived from current code/config/tests;
- code-contract and API/schema review;
- test/CI/documentation consistency review;
- security, authorization, scope, state, recovery, concurrency, persistence and migration passes;
- resource-bound and large-input review;
- resumable reviews with durable findings and checkpoints;
- repository profiles for language/framework-specific focus and verification advice;
- local analytical reports reusable by later sessions in the same worktree;
- bounded context projections with optional Mermaid rendering;
- read-only repository evidence for external MCP hosts;
- reversible install/update/uninstall and optional exact-version dependency pinning.

It does this **without replacing OpenCode's models, agents, tools, commands** or the equivalent runtime facilities of another host.

## What does it not do?

CodeSleuth is not:

- a model runtime;
- a general-purpose agent supervisor;
- a second tool router;
- an independent replacement review engine;
- a magic coverage oracle;
- a reason to trust a generated diagram or scout summary as evidence;
- a package manager for arbitrary extensions yet.

The core is intentionally small. Growth belongs in Skills, profiles, Playbooks, tools, plugins, and host adapters.

## Current execution model

For the installed OpenCode integration:

```text
CodeSleuth -> configuration / Skills / profiles / evidence discipline / TUI
OpenCode   -> model / controller / agents / tools / execution
```

For an external host:

```text
CodeSleuth -> supported Skills and/or narrow evidence interfaces
Host       -> model / controller / permissions / tools / execution
```

The host always remains execution authority.

# User manual

## Quickstart

### Requirements

For the current full OpenCode integration:

- Git **2.35+**;
- Python **3.10+**;
- OpenCode available as `opencode`;
- optional Bun when running the TypeScript state/context-graph development gates.

The TUI uses `textual==8.2.8` in an isolated runtime when Textual is not already available at that exact version.

### Start the TUI from a CodeSleuth checkout

Linux/macOS/WSL:

```bash
./codesleuth /path/to/project
```

PowerShell:

```powershell
.\codesleuth.ps1 C:\path\to\project
```

A nested path is accepted; CodeSleuth normalizes it to the containing Git repository root.

### First run

1. Open **Configure**.
2. Choose install/update/adopt behavior.
3. Keep repository profile detection on automatic unless the repository is unusual or mixed.
4. Choose the permission preset. `review-safe` is the least-privilege default.
5. Optionally select an Agent profile/model for the OpenCode integration.
6. Apply the configuration.
7. Run **Verify**.
8. Select **Open CodeSleuth** to launch the configured OpenCode runtime.
9. In OpenCode, start with `/repo-prompts` for task advice or `/repo-review` for a full evidence-first review.

For a direct non-interactive install:

```bash
./install.sh /path/to/project
```

PowerShell:

```powershell
.\install.ps1 C:\path\to\project
```

For a project that should record the exact CodeSleuth source revision as a Git dependency:

```bash
./install.sh /path/to/project --bind-dependency
```

That stages `.gitmodules` and the `tools/codesleuth` gitlink. CodeSleuth does **not** commit or push the target repository.

## In depth

### The important nouns

| Term | Meaning |
| --- | --- |
| **Host** | The real coding-agent runtime. It owns the model session, controller, tool routing and execution. OpenCode is the current full host; NovaClaw is the first external MCP host. |
| **Skill** | A reusable protocol/instruction package for how the host should perform a class of work. |
| **Command** | A user-facing host command that routes into a Skill or workflow. In OpenCode these are `/repo-*` commands. |
| **Playbook** | A ready-to-run task recipe generated for a concrete repository/task. It is a prompt recipe, not a Skill. |
| **Profile** | Repository-type metadata: detection evidence, review focus, configuration defaults and recommended verification. Profiles do not grant permissions. |
| **Agent profile** | OpenCode-specific model-family selection (`native`, `open-weight`, `codex`, `claude`). It does not install a CodeSleuth supervisor prompt. |
| **Tool** | A small executable capability, such as deterministic inventory, durable review state or context-graph operations. |
| **Plugin** | Host-native integration loaded by the host, for example review-compaction support. |
| **Review state** | Local structured continuation state under `.opencode/state/`, used to resume safely after compaction/session interruption. |
| **Report** | Human/assistant-readable Markdown under `.codesleuth/reports/`. Reports summarize work; they are not runtime state. |
| **Context graph** | A bounded derived repository projection for navigation/context. It is rebuildable and never stronger evidence than source. |

### Built-in Skills

Current distributed Skills are under `pack/.opencode/skills/`:

- **`repository-deep-review`** — large-repository mapping, documentation, whole-repo review and large PR review with durable checkpoints;
- **`codesleuth-reports`** — writes and maintains analytical reports under `.codesleuth/reports/`;
- **`feature-porting-discipline`** — evidence-first porting of capabilities between repositories without copying source-specific architecture or creating duplicate runtime authority.

The deep-review protocol has several non-negotiable rules:

1. context is working memory, not the repository;
2. inventory/discovery is not semantic coverage;
3. scout summaries are leads, not findings;
4. material findings require exact current source evidence;
5. durable state, not chat history, owns continuation state;
6. a test/check is only reported as passed when it actually ran successfully;
7. the agent reviews the real requested HEAD/range/worktree, not a stale summary.

### Built-in repository profiles

Current built-in profiles are:

```text
generic
rust
python
node
typescript
```

Automatic profile detection uses **tracked Git files**, not arbitrary filesystem contents. Examples:

- `Cargo.toml` / tracked `.rs` -> Rust;
- `pyproject.toml`, `requirements.txt`, `setup.py` or tracked `.py` -> Python;
- `package.json` -> Node;
- `tsconfig*.json`, tracked `.ts` / `.tsx` -> TypeScript.

Profiles may add review focus and verification advice. They do **not** silently widen web, edit, shell or external-directory permissions.

### Permission presets

The TUI exposes three presets:

| Preset | Intent |
| --- | --- |
| `review-safe` | least privilege; safe Git inspection is allowed while broad shell/edit/web actions remain controlled |
| `balanced` | additionally allows common project verification commands such as pytest, cargo tests/checks and package-manager lint/typecheck/test commands |
| `autonomous` | broadly allows shell work while still asking before destructive/publishing Git actions such as push/reset/clean |

Explicit TUI controls for web search, web fetch, edit/write and external directories remain authoritative policy choices.

### How a deep analysis works

A typical `/repo-review` run is expected to:

1. capture exact `HEAD`, dirty state and requested scope/ref;
2. read project authority such as `AGENTS.md`, README, ADRs, manifests, CI and build/test scripts;
3. call deterministic repository inventory before broad reading;
4. map authoritative entry points and component boundaries;
5. delegate independent bounded slices to scouts where useful;
6. perform component and cross-cutting review passes;
7. reopen exact current source before accepting a material defect;
8. record findings with source ranges and blob/worktree identity;
9. checkpoint work after meaningful phases;
10. persist a final report with explicit scope, checks, findings and limitations.

For a PR/range review, CodeSleuth's discipline explicitly follows changes into **unchanged** consumers, dependencies, tests, migrations, docs and CI. Reviewing only the textual diff is not considered sufficient for a deep review.

### What the analysis looks for

The built-in review protocol specifically calls out:

- canonical vs derived data and identity/provenance;
- validation and fail-open/fail-closed behavior;
- error propagation and partial failure;
- retries, idempotency, recovery and state transitions;
- concurrency, races and stale state;
- authorization, tenant/scope isolation and secrets;
- persistence and transaction boundaries;
- migrations and compatibility;
- API/schema contracts and downstream consumers;
- pagination, truncation, resource limits and large inputs;
- adversarial tests rather than happy-path-only tests;
- local-vs-CI verification parity;
- documentation/runtime truth.

### Durable state and context compaction

Review state lives under:

```text
.opencode/state/reviews/
```

Reviewed paths are tied to content identity. If source changes, stale evidence can be detected instead of silently reused.

The review-compaction plugin can rehydrate a bounded continuation checkpoint after host compaction. The goal is to continue from recorded `next` work, not restart repository discovery because the chat was shortened.

### Reports

Analytical reports live under:

```text
.codesleuth/reports/
```

Expected report content includes target identity, scope, findings with source locations, paths inspected, checks actually run, recommendations and limitations. `INDEX.md` is the local catalog.

Reports are local-only by default because they may contain source excerpts, diagnostics or credentials. `.codesleuth/reports/README.md` may be intentionally tracked to share the convention.

### Repository context graph and Mermaid

The context-graph tools maintain a bounded `RepositoryContextProjection` with closed node/relation vocabularies. Elements captured directly from tracked source may be marked verified; model/scout assertions remain inference.

Use the graph for:

- navigation;
- architecture/component context;
- bounded neighborhood queries;
- selective context rehydration;
- optional Mermaid presentation.

Do **not** use the graph or Mermaid as finding evidence. Material claims still require reopened exact source.

### OpenCode commands

Current installed commands are:

| Command | Purpose |
| --- | --- |
| `/repo-prompts` | task advisor / suggested next repository work |
| `/repo-profile` | inspect or derive repository profile information |
| `/repo-review` | deep evidence-first repository or PR review |
| `/repo-review-resume` | continue a durable review |
| `/repo-docs` | produce evidence-first repository documentation |
| `/repo-report` | persist analytical report material |
| `/repo-map` | build/refresh a bounded architecture/context map, optionally render Mermaid |

### OpenCode `build` controller

OpenCode's primary controller is `build`. CodeSleuth does not add a second supervisor. Agent profile (Open-weight / Codex / Claude) selects a model so OpenCode's native provider prompt is used; it does not inject a CodeSleuth system prompt.

```text
CodeSleuth TUI
    ↓
profile / skill / command / model / permissions
    ↓
OpenCode primary build
    ↓
native provider-specific controller prompt
    ↓
Task → explore / general / CodeSleuth skills and subagents
```

The CodeSleuth-specific agents in `.opencode/agents/` are bounded **subagents**, not replacement primary controllers.

### External hosts and MCP

The current external-host adapter exposes one repository over MCP stdio with six read-only evidence tools:

| Tool | Purpose |
| --- | --- |
| `overview` | HEAD, branch, dirty state, tracked-file count and bounded repository shape |
| `inventory` | cursor-based tracked-file inventory with index blob identity |
| `read_evidence` | exact bounded source lines with working/index blob identity |
| `search` | bounded Git grep with path, line and text |
| `test_map` | likely test/build/CI surfaces; explicitly **not** coverage |
| `diff_evidence` | bounded staged/unstaged diff tied to current HEAD |

The adapter rejects path traversal, untracked reads, symlinks/gitlinks, non-regular entries, unresolved index stages and binary source reads. Git probes are hardened to stay non-interactive/read-only at the evidence boundary. See [`docs/NOVACLAW-MCP.md`](docs/NOVACLAW-MCP.md).

## TUI reference

### Main navigation

The current main surfaces are exact implemented labels:

| Surface | What it shows | Contextual actions |
| --- | --- | --- |
| **Home** | repository readiness, active policy/profile summary, safe next action | Configure, Verify, Playbooks, Help, Open CodeSleuth |
| **Review** | OpenCode review commands and Playbooks | Playbooks, Open CodeSleuth |
| **Evidence** | durable review state and checkpoint provenance visible in `.opencode/state/` | Help, Open CodeSleuth |
| **Tools** | installed commands, Skills, tools/plugins and lifecycle utilities | Verify, Check Updates, Update, Open CodeSleuth |
| **Settings** | profile, permission, runtime and dependency/lifecycle configuration | Configure, Uninstall |

The active surface is placed at the top of the main content area and is brought into view when navigation changes.

### Main status card

The status card is operational information, not decoration.

| Field | Meaning |
| --- | --- |
| `READY` | versioned CodeSleuth installation with complete metadata |
| `ATTENTION` | versioned installation exists but metadata says it is incomplete |
| `SETUP` | no versioned CodeSleuth installation yet |
| `Installation` | detected install form such as `versioned`, `legacy-pack`, `existing-opencode`, or `fresh` |
| `lifecycle` | combined runtime/dependency state |
| `complete` | whether the installed metadata declares the install complete |
| `Profiles` | currently detected/selected repository profiles |
| `Runtime policy` | permission preset plus Exa/keepalive state |
| `Dependency` | exact pinned CodeSleuth gitlink commit, or `not pinned` |
| `Update path` | how updates can be obtained for this target |
| `Agent profile` | selected OpenCode model-family profile and optional model id |
| `Reports` | local analytical report directory |
| `Next action` | install/update/adopt/configure recommendation derived from current state |

### Lifecycle states

Runtime installation and source dependency are independent. The lifecycle contract includes:

- `unbound-inactive` — no runtime and no tracked CodeSleuth dependency;
- `unbound-active` — runtime installed, no tracked dependency;
- `bound-active` — runtime installed and exact CodeSleuth commit pinned;
- `dependency-only` / bound-inactive — dependency retained, runtime absent;
- `uninstalled-preserved` — runtime removed, known traces archived locally;
- `uninstalled-purged` — runtime/dependency/ordinary traces removed after conflict-safe restore.

See [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md) for the authoritative restore/binding rules.

### Update-path messages

| Message form | Meaning |
| --- | --- |
| `source checkout: origin/main` | CodeSleuth is controlling its own source checkout; Check Updates/Update explicitly fetch current `origin/main` |
| `floating: <remote> <ref>` | installed target can use recorded floating source metadata |
| `pinned: advance/revert the gitlink...` | project uses exact `tools/codesleuth` dependency; update the gitlink deliberately |
| `unavailable: no explicit floating source ref` | no safe automatic update authority is recorded |

For the CodeSleuth source checkout itself, **Update does not trust local branch tracking configuration**. It fetches `origin/main` explicitly and only fast-forwards a clean local `main` branch. This avoids stale `branch.main.merge` configuration redirecting the update to a deleted feature branch.

### Recent activity

`Recent activity` contains output from control-shell actions such as Verify, update and uninstall. On a fresh TUI session it states that no CodeSleuth control action has run yet. Treat this as an operator log, not a repository analysis report.

### Panels and keyboard controls

| Key/control | Action |
| --- | --- |
| `q` | quit |
| `c` | configure |
| `p` | Playbooks |
| `h` | Help |
| `v` | Verify |
| `k` | Check Updates |
| `u` | Uninstall |
| `b` | show/hide the large CodeSleuth brand block |
| `F2` | show/hide the bottom Footer |
| `F3` | collapse/restore the left navigation panel |
| `F4` | collapse/restore the right Keys/Help panel |
| left-panel `<` / `>` | collapse/restore left navigation |
| right-panel `<` / `>` | collapse/restore the right Keys/Help panel |
| right-panel `X` | close the right Keys/Help panel for the rest of the current TUI session |

Closing the right panel is deliberately different from collapsing it: collapse is reversible; `X` is a session-level dismissal.

### Configure screen

The configuration screen controls:

1. installation/update/legacy adoption and optional dependency binding;
2. repository profile auto-detection vs manual selection;
3. OpenCode Agent profile and optional model id;
4. explicit evidence/web/edit/external-directory permissions;
5. Exa, keepalive, stall/recovery limits, compaction reserve and update checks;
6. the resulting planned policy summary.

**Apply** writes the selected configuration. **Cancel**, **Back**, or Escape aborts without applying.

## CLI reference

### Start the source-checkout TUI

```bash
./codesleuth [repository]
```

```powershell
.\codesleuth.ps1 [repository]
```

### Start the installed TUI

From the target repository:

```bash
.opencode/bin/codesleuth
```

```powershell
.\.opencode\bin\codesleuth.ps1
```

`review-pack` remains a compatibility alias during the naming migration.

### Install / update materialized OpenCode files

```bash
./install.sh [repository] [options]
```

PowerShell:

```powershell
.\install.ps1 [repository] [options]
```

Important installer options:

| Option | Meaning |
| --- | --- |
| `--version` | print CodeSleuth version |
| `--profile <name>` | manually add a built-in profile; repeatable |
| `--settings-file <path>` | load validated settings JSON, normally produced by the TUI |
| `--update` | update an existing versioned installation |
| `--adopt-existing-pack` | adopt an older unversioned review-pack installation with backups |
| `--bind-dependency` | pin the current CodeSleuth source as `tools/codesleuth` |
| `--dependency-path <path>` | override the dependency path |
| `--force-pack-files` | replace locally modified CodeSleuth-managed files; use deliberately |
| `--uninstall` | uninstall through the installer entry point |
| `--purge-traces` | with uninstall, remove ordinary local CodeSleuth traces/backups instead of archiving |
| `--keep-dependency` | with uninstall, keep the CodeSleuth gitlink/submodule |
| `--source-remote`, `--source-ref`, `--source-subdir`, `--source-commit` | advanced explicit source identity/update metadata |

### Runtime/dependency lifecycle CLI

The installed lifecycle manager is:

```bash
.opencode/bin/codesleuth-project [repository] ACTION
```

PowerShell:

```powershell
.\.opencode\bin\codesleuth-project.ps1 [repository] ACTION
```

Actions are mutually exclusive:

```text
--bind
--unbind
--uninstall
```

Useful combinations:

Remove only the tracked dependency and keep the installed runtime:

```bash
.opencode/bin/codesleuth-project . --unbind
```

Uninstall runtime and dependency while preserving known audit traces:

```bash
.opencode/bin/codesleuth-project . --uninstall
```

Uninstall runtime but keep the pinned dependency:

```bash
.opencode/bin/codesleuth-project . --uninstall --keep-dependency
```

Uninstall and purge ordinary CodeSleuth traces/backups:

```bash
.opencode/bin/codesleuth-project . --uninstall --purge-traces
```

CodeSleuth refuses unsafe submodule removal such as a dirty dependency checkout or a checkout whose local HEAD does not match the superproject gitlink.

### Verify

Direct smoke/integrity check:

```bash
python3 .opencode/bin/review-pack-smoke.py .
```

The TUI **Verify** button invokes this installed smoke gate.

### Launch OpenCode with CodeSleuth project settings

```bash
.opencode/bin/opencode-review
```

PowerShell:

```powershell
.\.opencode\bin\opencode-review.ps1
```

The launcher applies CodeSleuth-managed OpenCode environment/configuration and then executes normal `opencode`.

### Updating a pinned project

A pinned project records an exact CodeSleuth gitlink. Update it deliberately:

```bash
git -C tools/codesleuth fetch origin
git -C tools/codesleuth checkout --detach <accepted-codesleuth-sha>
./tools/codesleuth/install.sh . --update
```

Then inspect and commit the gitlink and intended `.opencode` changes together.

For a fresh clone:

```bash
git clone --recurse-submodules <project-url>
# or
git submodule update --init --recursive
```

### MCP server

Install its isolated dependency set:

```bash
python -m venv .venv-mcp
python -m pip install -r requirements-mcp.txt
```

Run one repository-bound MCP server:

```bash
python -m codesleuth_mcp.server --repo /path/to/repository
```

On PowerShell, the repository wrapper is:

```powershell
.\codesleuth-mcp.ps1 C:\path\to\repository
```

See [`docs/NOVACLAW-MCP.md`](docs/NOVACLAW-MCP.md) for current external-host registration details and adapter safety boundaries.

## Environment reference

CodeSleuth intentionally has a small environment surface.

| Variable | Owner / use | User-facing? |
| --- | --- | --- |
| `OPENCODE_ENABLE_EXA` | installed OpenCode launcher sets/unsets it from CodeSleuth runtime settings | normally managed by CodeSleuth |
| `OPENCODE_TUI_CONFIG` | installed launcher points OpenCode at `.opencode/tui.json` when present | normally managed by CodeSleuth |
| `REVIEW_PACK_DISTRIBUTION_ROOT` | source-checkout TUI tells the app where the CodeSleuth distribution lives | internal compatibility name |
| `REVIEW_PACK_TARGET_ROOT` | installed TUI/bootstrap identifies the target repository | internal compatibility name |
| `CODESLEUTH_MCP_PYTHON` | PowerShell MCP wrapper override for the Python executable | optional user override |
| `CODESLEUTH_MCP_DEBUG` | enables MCP diagnostic tracing to stderr | optional debugging |
| `PYTHONPATH` | standard Python mechanism that can expose a local CodeSleuth checkout to an MCP host without installing the package | optional integration aid |

The `REVIEW_PACK_*` names are retained compatibility surfaces from the imported implementation. New user-facing naming is CodeSleuth, but removing those internals without migration would break installed launch paths.

# Extending CodeSleuth

## What is extendable?

The accepted extension seams are:

```text
profiles
Skills
Playbooks / commands
small tools
plugins
bounded subagents
host adapters / connectors
extension-management UX
```

The following are **not** extension seams without a new architecture decision:

```text
second model runtime
second primary controller
independent agent loop
independent general-purpose tool router
replacement review engine
second canonical repository-truth store
```

## Current extension workflow

There is not yet a complete TUI package manager. Today, extension loading is primarily host-native/manual, while the CodeSleuth TUI discovers installed commands, Skills, tools and plugins.

For the OpenCode integration, distributed material lives under:

```text
pack/.opencode/
├── agents/
├── commands/
├── plugins/
├── profiles/
├── skills/
└── tools/
```

The installer materializes the pack into the target repository's `.opencode/` tree while preserving user-owned configuration according to the lifecycle/update contract.

### Add a Skill

Use an existing Skill directory as the template:

```text
.opencode/skills/<skill-name>/SKILL.md
```

The current Skills use YAML frontmatter with at least:

```yaml
---
name: skill-name
description: What the skill does
---
```

A Skill should define reusable behavior and invariants, not replace the host controller. If it records derived state, document the canonical input and invalidation/rebuild rule.

### Add an OpenCode command / Playbook entry point

Command files live under:

```text
.opencode/commands/<command>.md
```

Current CodeSleuth commands declare `agent: build` and route the task into Skills/tools rather than creating a new primary agent. Use existing `/repo-*` command files as templates.

### Add a bounded subagent

OpenCode subagent definitions live under:

```text
.opencode/agents/<name>.md
```

CodeSleuth's specialist agents are `mode: subagent`. Keep scope and permissions bounded. `repo-scout` is the reference for a read-only specialist that returns candidate evidence for parent verification.

### Add a tool

OpenCode-native tools live under:

```text
.opencode/tools/
```

Current examples are:

```text
repo_inventory.ts
repo_profile.ts
review_state.ts
repo_context_graph.ts
```

Prefer a small tool that exposes deterministic host-useful behavior. Do not recreate a capability the host already owns.

### Add a plugin

Local plugin code lives under `.opencode/plugins/`; package plugins may also be declared through the host configuration. `review-compaction.ts` is the current local example. The keepalive package is configured through `opencode.json`/CodeSleuth runtime settings.

Plugins remain host-native execution. CodeSleuth may configure or package them but does not become their runtime.

### Add a repository profile

Built-in profile files live under:

```text
.opencode/profiles/builtin/<profile>.json
```

A profile can describe:

- detection evidence;
- inherited profile (`extends`);
- recommended verification;
- review focus;
- compatible configuration defaults.

**Important:** adding a new profile file is not enough to make it a first-class TUI profile today. Current validation/detection explicitly knows `generic`, `rust`, `python`, `node`, and `typescript`; a new built-in profile contribution must also update the profile constants/detection/validation path and tests.

Profiles must never silently widen permissions.

### Add a host integration

A host adapter should be as thin as the host contract allows. Required invariants:

1. the host retains controller/model/session/tool-routing authority;
2. CodeSleuth does not compensate for host differences by growing a parallel agent loop;
3. shared Skills/evidence discipline are reused where practical;
4. integration-specific state does not become a second execution source of truth;
5. adapter permissions and safety boundaries are tested explicitly.

NovaClaw's MCP adapter is the current reference external-host seam.

# Contributing

## Developer contracts

Before changing behavior, identify which contract owns it.

| Contract/package | What it governs |
| --- | --- |
| [`docs/CODESLEUTH-PRODUCT-CONTRACT.md`](docs/CODESLEUTH-PRODUCT-CONTRACT.md) | product identity, host/runtime ownership, extension seams, core feature freeze, PR classifications |
| [`docs/CODESLEUTH-BRANDING.md`](docs/CODESLEUTH-BRANDING.md) | terminal-native UI/branding and responsive interaction rules |
| [`docs/CODESLEUTH-COLORMAP.json`](docs/CODESLEUTH-COLORMAP.json) | machine-readable semantic color map |
| [`docs/CONTEXT-GRAPH-DISCIPLINE.md`](docs/CONTEXT-GRAPH-DISCIPLINE.md) | source -> review state -> bounded context projection -> Mermaid authority chain |
| [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md) | reversible install/update/bind/unbind/uninstall and ignore/restore safety |
| [`docs/NOVACLAW-MCP.md`](docs/NOVACLAW-MCP.md) | current external MCP host boundary |
| [`docs/MAINTAINER-SUBREPO.md`](docs/MAINTAINER-SUBREPO.md) | standalone/subrepo maintenance rules |
| `pack/.opencode/` | the installed OpenCode integration package |
| `install.py` | materialization, update and configuration merge behavior |
| `pack/.opencode/bin/codesleuth_project.py` | project lifecycle/dependency implementation |
| `pack/.opencode/bin/codesleuth_tui.py` | current TUI, exact labels and canonical ASCII brand |
| `codesleuth_mcp/` | read-only external evidence adapter |
| `tests/` | executable regression/acceptance contracts |

Read [`docs/README.md`](docs/README.md) for the documentation contract map.

## Change classifications

PRs should classify themselves as one of:

```text
CORE-HARDENING
PROFILE-EXTENSION
SKILL-EXTENSION
PLAYBOOK-EXTENSION
TOOL-EXTENSION
HOST-INTEGRATION
EXTENSION-MANAGEMENT-UX
DOCS
```

A change outside those categories should explain why it does not violate the frozen-core architecture before implementation.

## Development gates

Install Python development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the Python suite and lint:

```bash
python -m pytest
ruff check .
```

Run durable-state/context-graph smokes:

```bash
bun install --frozen-lockfile
bun tests/review_state_smoke.ts
bun tests/context_graph_smoke.ts
```

If MCP changed:

```bash
python -m pip install -r requirements-mcp.txt
python -m pytest -q tests/test_mcp_server.py
ruff check codesleuth_mcp tests/test_mcp_server.py
```

TUI changes should be tested with Textual's headless `App.run_test()`/Pilot coverage at narrow and wide viewports and then checked in a real terminal. Lifecycle changes should exercise real disposable Git repositories/submodules rather than mock away the behavior being protected.

## Documentation rule

Documentation is text-first and terminal-native.

- Copy the canonical ASCII brand from `CODESLEUTH_ART`; do not redraw it repeatedly.
- UI manuals should describe exact implemented labels and use real terminal snapshots when a snapshot is needed.
- Do not maintain PNG/JPEG/WebP/SVG UI mockups or reference boards.
- Mermaid is the allowed diagram format when encoded relationships are useful; generated Mermaid remains presentation, not repository truth.

# Roadmap and chores

The direction is **agent-agnostic CodeSleuth with a small frozen core**, not a bigger CodeSleuth agent runtime.

## Current hardening track

Before widening integrations, the current 0.3 line is focused on:

- TUI usability and viewport behavior;
- lifecycle/update correctness;
- reversible configuration preservation;
- deterministic evidence safety;
- durable-state/context-graph correctness;
- documentation/runtime consistency;
- regression coverage around real Git behavior;
- adding CI around the already-defined acceptance gates.

## Host-agnostic direction

Planned sequence:

1. **Keep OpenCode production-solid.** It remains the current full installed reference integration.
2. **Keep NovaClaw MCP narrow and proven.** It demonstrates that CodeSleuth evidence can be consumed without CodeSleuth owning the agent runtime.
3. **Separate common discipline from host packaging.** Skills, evidence conventions and extension metadata should become reusable without pretending all hosts expose the same primitives.
4. **Add early host integrations for Codex and Cursor.** Each adapter should use host-native models/tools/controllers rather than emulate OpenCode inside CodeSleuth.
5. **Add Hermes, BodegaOne and Pi-harness integrations** using the same ownership rule.
6. **Build a host capability matrix.** An integration should state which Skills, evidence tools, permissions and lifecycle features it can actually support.
7. **Grow extension-management UX.** Discovery, provenance, compatibility, install/load, enable/disable, update and remove can become easier through CLI/TUI while execution stays host-native.
8. **Do not unfreeze the core by accident.** New capability should normally be a profile, Skill, Playbook, small tool, plugin or host adapter.

The end state is intentionally modest: CodeSleuth should be the reusable **discipline kit and control panel** around coding agents, not another coding agent competing with them.

# Security and local state

CodeSleuth operates through an authorized host. If that host can run tests, read files, access development services or use developer credentials, evidence and reports may contain those values. CodeSleuth does **not** blanket-redact all output because doing so would make some real audits/tests incorrect.

Default local-state behavior:

- `.codesleuth/` backups, archives and report bodies are excluded locally through Git's repository-local exclude file;
- `.opencode/state/`, caches, logs, sessions, snapshots, runtime dependencies and bytecode are excluded locally;
- CodeSleuth does not silently rewrite the target repository's tracked `.gitignore` for these patterns;
- `tools/codesleuth` is intentionally not ignored when dependency binding is selected;
- reports should be inspected/sanitized before intentional publication;
- uninstall uses conflict-safe restore and preserves recovery evidence when a user-modified pre-existing file cannot be restored automatically.

See [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md) for exact lifecycle semantics and [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md) for the older detailed operational guide retained for compatibility/reference.
