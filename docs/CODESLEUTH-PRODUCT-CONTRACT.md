# CodeSleuth Product & Architecture Contract

**Status:** Accepted / production target  
**Core feature state:** Frozen after current branding/production PR  
**Primary runtime dependency:** OpenCode

## 1. One-sentence contract

**CodeSleuth is a convenient evidence-oriented control panel, configuration layer, catalog, and lifecycle manager for OpenCode infrastructure; OpenCode and its models remain the execution authority.**

## 2. Runtime ownership

OpenCode owns:

- model sessions and context;
- the primary controller agent (`build`) and its native provider-specific prompt;
- agent execution, including native `explore` / `general` Task subagents;
- tool calling/routing;
- Skills execution;
- OpenCode commands;
- installed tool/plugin execution;
- long-running and large-context repository review;
- reasoning/orchestration behavior provided by the selected model/runtime.

CodeSleuth owns only the surrounding operator experience:

- clear repository/readiness/status presentation;
- project-local configuration and permission UX;
- repository profile selection/detection;
- **Agent profile** as model-family selection (Open-weight / Codex / Claude / native);
- safe install/adopt/update/remove lifecycle;
- Verify/smoke presentation;
- Playbook discovery;
- analytical report folder convention (`.codesleuth/reports/`), written by OpenCode `build`;
- Help/documentation;
- extension discovery/catalog/install/update/remove UX;
- theme/branding defaults that do not overwrite user-owned configuration.

Controller boundary, prompt-replacement rule, and execution diagram: [OpenCode `build` controller](../README.md#opencode-build-controller). Commands stay `agent: build`; do not set `agent.build.prompt`.

## 3. Non-duplication rule

If OpenCode can already run a tool, Skill, command, or model workflow, CodeSleuth must **invoke, expose, configure, or document it**, not reimplement it.

A CodeSleuth menu action may be a friendly route to an OpenCode-native capability. The menu is not evidence that CodeSleuth owns that capability.

## 4. Extension model

The extension surface is deliberately open-ended.

Users/maintainers may continue to add:

- profiles for languages/frameworks/repository types;
- Skills;
- Playbooks;
- tools and plugins;
- connectors/integrations supported by OpenCode;
- small custom tools written by users and installed/loaded through CLI or TUI.

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

Execution after installation remains OpenCode-native.

## 5. Allowed future UI growth

Allowed without reopening the core architecture:

- richer profile catalog;
- Skills/Playbooks/tool catalog views;
- local/remote package or file installation UI for OpenCode-native extensions;
- extension compatibility and provenance display;
- safe extension update/remove UX;
- better narrow/wide responsive navigation;
- accessibility and discoverability improvements.

These are management surfaces for existing infrastructure, not new analysis engines.

## 6. Core feature freeze

Do not add new first-class CodeSleuth analysis/orchestration features after this PR.

Specifically prohibited without a new ADR/product decision:

- independent CodeSleuth model runtime;
- independent CodeSleuth agent loop;
- a CodeSleuth supervisor / orchestrator / "main AI" that replaces OpenCode `build`;
- injecting `prompt` onto `build` or another primary agent (this clobbers OpenCode's provider prompt);
- independent tool-call protocol/router;
- replacement review engine;
- duplicate copies of OpenCode capabilities hidden behind CodeSleuth-specific implementations;
- state formats that become a second source of truth for tool/model execution.

Core work after freeze is production hardening only.

## 7. Compatibility invariant

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

## 8. User-facing goal

The menu exists so a user can immediately answer:

```text
Where am I?
Is the repository/installation ready?
What can I do here?
Which actions are safe?
What will OpenCode actually run?
Where do I install more capabilities?
What happened?
```

Clarity is a product feature. Owning more runtime is not.

## 9. Production gate

Before merge/release, prove:

1. install/update/adopt/remove safety;
2. user-owned OpenCode configuration preservation;
3. TUI behavior at narrow and wide sizes;
4. direct OpenCode command/Skill/tool usability after installation;
5. CodeSleuth launch path still enters normal OpenCode execution;
6. Verify and lifecycle tests are green;
7. no new core subsystem was introduced outside this contract.

## 10. Change policy

Future PRs should classify themselves as one of:

```text
CORE-HARDENING
PROFILE-EXTENSION
SKILL-EXTENSION
PLAYBOOK-EXTENSION
TOOL-EXTENSION
EXTENSION-MANAGEMENT-UX
DOCS
```

Anything else should explain why it does not violate the feature freeze before implementation begins.
