# CodeSleuth Product & Architecture Contract

**Status:** Accepted / production target  
**Core feature state:** Frozen after current branding/production track  
**Current installed host:** OpenCode  
**Current external-host seam:** read-only MCP adapter (NovaClaw first)

## 1. One-sentence contract

**CodeSleuth is a lightweight code-discipline layer for LLM repository work: a reusable Skill pool, thin control surface, durable evidence discipline, and a few narrow tools; it never owns the host model runtime or controller.**

OpenCode is the current full installed integration. For an external host, CodeSleuth exposes only the capabilities that integration deliberately supports, such as the bounded read-only MCP repository-evidence adapter. In every mode the host remains the execution authority.

The canonical durable evidence storage semantics are defined in [`DURABLE-EVIDENCE-STORE.md`](DURABLE-EVIDENCE-STORE.md).

## 2. Runtime ownership

The active host owns:

- model sessions and context;
- primary controller/supervisor behavior;
- agent/subagent execution;
- tool calling/routing;
- host-native command and Skill execution;
- installed plugin/tool execution;
- permissions and execution policy;
- reasoning/orchestration behavior provided by the selected model/runtime.

For the installed OpenCode integration this means OpenCode owns `build`, its native provider-specific prompt, native `explore` / `general` Task subagents, OpenCode commands, Skills, tools and long-running repository review. The canonical public controller description is [`OpenCode build controller`](../README.md#opencode-build-controller); this contract links to it instead of duplicating the controller diagram.

For an external host, that host owns the equivalent runtime responsibilities. The current MCP server owns only deterministic bounded repository evidence and never replaces the host controller.

CodeSleuth owns the surrounding discipline and operator experience:

- reusable repository-review Skills and protocols;
- clear repository/readiness/status presentation;
- project-local configuration and permission UX where the host integration supports it;
- repository profile selection/detection;
- Agent profile/model-family selection for the installed OpenCode integration;
- safe install/adopt/update/remove lifecycle;
- Verify/smoke presentation;
- Playbook discovery;
- evidence/state conventions and analytical report-folder conventions, governed by `DURABLE-EVIDENCE-STORE.md`;
- Help/documentation;
- extension and integration discovery/catalog/install/update/remove UX;
- small bounded evidence/helper tools where a host needs them;
- theme/branding defaults that do not overwrite user-owned configuration.

## 3. Non-duplication rule

If the active host can already run a tool, Skill, command, model workflow, or orchestration primitive, CodeSleuth must **invoke, expose, configure, document, or package it**, not reimplement it.

A CodeSleuth menu action or adapter endpoint may be a friendly route to host-native functionality. That route is not evidence that CodeSleuth owns the underlying execution.

The same rule applies internally to durable evidence. `review_state` plus its
append-only finding/EHA ledgers form one evidence authority. New caches,
indexes, graph stores, SQL databases, vector stores or report formats must be
rebuildable derivatives unless an explicit architecture decision replaces that
authority.

## 4. Integration model

The host-integration surface is deliberately open-ended, while the CodeSleuth core remains small.

Current integrations:

- **OpenCode** — full installed host integration;
- **NovaClaw** — tested external-host integration through the read-only MCP evidence adapter.

Planned/targeted integrations after current hardening include **Codex, Cursor, Hermes, BodegaOne, Pi-harness**, and other coding-agent hosts that can reuse the same review Skills, evidence discipline, and narrow tools without moving runtime ownership into CodeSleuth.

A new host integration must preserve these invariants:

1. the host keeps controller/model/session/tool-routing authority;
2. CodeSleuth does not grow a parallel agent loop to compensate for host differences;
3. integrations reuse the common Skills/evidence discipline where practical;
4. host-specific adapters stay as small as the host contract permits;
5. integration-specific state must not become a second source of truth for host execution.

## 5. Extension model

Users and maintainers may continue to add:

- profiles for languages/frameworks/repository types;
- Skills;
- Playbooks;
- tools and plugins;
- host adapters/connectors/integrations;
- small custom tools written by users and installed/loaded through supported CLI/TUI surfaces.

CodeSleuth may provide an increasingly convenient extension manager, including:

```text
discover
inspect metadata/permissions
install/load
enable/disable
update
remove
validate compatibility
show origin/version
```

Execution after installation remains host-native.

The shared operator units for that manager are Catalog (loaded list), Detail (one item), and Load wizard (`Source → Inspect → Validate → Confirm → Result`). Playbooks is the first instance. Skills, profiles, tools/plugins, and host adapters MUST reuse those units rather than a second wizard family. See [`EXTENSION-LOAD-UNITS.md`](EXTENSION-LOAD-UNITS.md).

## 6. Allowed future UI growth

Allowed without reopening the core architecture:

- richer profile catalog;
- Skills/Playbooks/tool catalog views;
- local/remote package or file installation UI for host-native extensions;
- host-integration setup/status views;
- extension compatibility and provenance display;
- safe extension update/remove UX;
- better narrow/wide responsive navigation;
- accessibility and discoverability improvements.

These are management surfaces for existing infrastructure, not new analysis engines.

## 7. Core feature freeze

Do not add new first-class CodeSleuth analysis/orchestration features without an explicit architecture decision.

Specifically prohibited:

- independent CodeSleuth model runtime;
- independent CodeSleuth agent loop;
- a CodeSleuth supervisor/orchestrator/"main AI" that replaces the host controller;
- replacing a host-native controller prompt with a CodeSleuth supervisor prompt;
- independent general-purpose tool-call router;
- replacement review engine that bypasses the host;
- duplicate copies of host capabilities hidden behind CodeSleuth-specific implementations;
- state formats that become a second source of truth for host tool/model execution;
- a second independently writable evidence database/ledger for facts already owned by `review_state` / EHA evidence;
- destructive generic CRUD that can rewrite verified finding or EHA acceptance history.

The MCP adapter is not an exception: it is read-only, repository-bound, and exposes no independent model runtime, controller, router, or durable execution state.

Core work after freeze is production hardening plus the explicitly allowed profile/Skill/Playbook/tool/integration extension seams.

## 8. OpenCode compatibility invariant

A repository that already works with OpenCode must remain understandable and usable with OpenCode after CodeSleuth installation.

CodeSleuth must not block direct use of:

```text
/repo-prompts
/repo-profile
/repo-review
/repo-docs
/repo-review-resume
/repo-report
```

or other OpenCode-native tools/Skills added later.

The CodeSleuth launcher/theme/configuration layer must not reduce model context capacity or interfere with successful large-context review sessions merely because the user chooses to launch through the branded console.

## 9. User-facing goal

The control surface exists so a user can immediately answer:

```text
Where am I?
Is this repository/integration ready?
What can I do here?
Which actions are safe?
What will the host actually run?
Where do I install more capabilities?
What evidence/state exists?
What happened?
```

Clarity is a product feature. Owning more runtime is not.

## 10. Documentation and graphics invariant

CodeSleuth documentation is terminal-native and text-first.

- The canonical ASCII brand is implemented in `pack/.opencode/bin/codesleuth_tui.py` as `CODESLEUTH_ART` (documentation identity; not rendered by the live TUI) and may be copied verbatim to the top-level README.
- UI documentation uses text/terminal snapshots captured from the real application. Do not maintain synthetic PNG/JPEG/WebP/SVG UI mockups or reference boards.
- Mermaid is the only general diagram format allowed in maintained documentation because it encodes understandable, reviewable structure as text. It is for relationships/context/architecture, not branding or decorative UI art.
- Generated Mermaid remains presentation of verified structure, never a second source of repository truth or durable evidence.

## 11. Production gate

Before merge/release, prove the gates relevant to the changed surface. For the installed OpenCode integration this includes:

1. install/update/adopt/remove safety;
2. user-owned OpenCode configuration preservation;
3. TUI behavior at narrow and wide sizes;
4. direct OpenCode command/Skill/tool usability after installation;
5. CodeSleuth launch path still enters normal OpenCode execution;
6. Verify and lifecycle tests are green;
7. durable evidence-store authority/write/append-only contracts remain intact when evidence tooling changes.

For external-host adapters, prove the adapter-specific safety/compatibility boundary and that the host retains execution authority. No integration may introduce a new core subsystem outside this contract.

## 12. Change policy

Future PRs should classify themselves as one of:

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

Anything else should explain why it does not violate the feature freeze before implementation begins.

Replacing the current durable evidence authority, making a derived view canonical,
or introducing another independently writable evidence store is an architecture
change and normally reopens SIB0 rather than fitting into an ordinary extension
classification.
