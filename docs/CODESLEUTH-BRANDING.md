# CodeSleuth UI Branding & Interaction Runbook

**Status:** Accepted / canonical / feature-frozen core  
**Applies to:** CodeSleuth TUI/CLI control surfaces, OpenCode runtime theme, help, Playbooks, extension-management UI, screenshots/reference layouts  
**Architecture authority:** [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md)

## 1. Product identity

```text
CodeSleuth
Evidence-first repository intelligence
CodeSleuth · Evidence Console
```

CodeSleuth is a **control surface over OpenCode**, not a replacement runtime.

```text
CodeSleuth = UX / control panel / configuration / catalog / safe lifecycle
OpenCode   = execution runtime / native build controller / models / agents / tool calls / Skills
```

Do not present CodeSleuth as a second supervisor. Agent profile is model-family selection for OpenCode's native `build` prompt, not a custom system prompt.

The interface must make this relationship obvious enough that users understand what they are about to do, while remaining thin enough that existing OpenCode commands, tools, Skills, and long-context review behavior continue to work directly.

## 2. Accepted visual direction

Dark terminal-native evidence console with restrained cyan/steel accents and semantic green/amber/red state colors.

The product should feel like an inspection instrument, not a generic AI skin.

Canonical flow language:

```text
repository -> inventory -> inspect -> evidence -> verify -> finding
```

Do not turn every label into detective cosplay. Canonical operational terms remain `Repository`, `Review`, `Evidence`, `Verify`, `Finding`, `Coverage`, `Playbooks`, `Tools`, `Profiles`, `Skills`, and `Settings`.

## 3. Approved reference layouts

These files are **visual contracts**, not literal screenshots of the current Textual implementation:

- [Mobile / narrow-terminal reference board](assets/branding/mobile-reference-board.svg)
- [Desktop / wide-terminal reference board](assets/branding/desktop-reference-board.svg)

### Mobile / narrow-terminal family

![CodeSleuth mobile reference layouts](assets/branding/mobile-reference-board.svg)

The mobile family covers:

1. Home / Evidence Console
2. Configuration
3. Verify
4. Playbooks
5. Help

Navigation is compact and persistent:

```text
Home | Review | Evidence | Tools | Settings
```

On a terminal this is a **narrow-layout navigation model**, not a promise of a native mobile application.

### Desktop / wide-terminal family

![CodeSleuth desktop reference layouts](assets/branding/desktop-reference-board.svg)

Desktop uses the same information architecture, normally with a persistent left rail:

```text
Home
Review
Evidence
Tools
Settings
```

The mobile and desktop families may rearrange components, but must not invent different semantics or different workflows.

## 4. Navigation semantics

The five navigation labels are orientation surfaces over existing infrastructure, not five new CodeSleuth subsystems.

| Surface | Purpose | Execution owner |
|---|---|---|
| Home | repository/readiness/activity/next action | CodeSleuth presentation + existing checks |
| Review | discover and invoke repository-review commands/Playbooks | OpenCode |
| Evidence | explain/show evidence state, durable review state, findings/coverage where available | OpenCode state + CodeSleuth presentation |
| Tools | discover/manage/invoke OpenCode-native tools, Skills, extensions, Verify/update utilities | OpenCode; CodeSleuth may manage installation/catalog UX |
| Settings | CodeSleuth/OpenCode project-local configuration, profiles, permissions, lifecycle | CodeSleuth configuration layer |

A menu item may route to an existing OpenCode command or capability. It must not duplicate that capability in a second orchestration engine.

## 5. Screen playbook

### 5.1 Home / Evidence Console

Must answer, in order:

1. Which repository am I operating on?
2. Is the CodeSleuth installation ready?
3. Which profiles/runtime policy are active?
4. What is the recommended next action?
5. What happened recently?

Core actions remain:

```text
Configure
Verify
Playbooks
Help
Open CodeSleuth
```

Update actions may be surfaced contextually rather than consuming permanent space.

### 5.2 Configuration

Title:

```text
CodeSleuth Configuration
```

Sections:

1. Installation
2. Repository profile
3. Agent profile (OpenCode model family; native `build` controller)
4. Evidence permissions
5. Runtime
6. Planned policy

Configuration must preserve explicit consent for web search/fetch, edits, and external directories.

### 5.3 Verify

`Verify` is the user-facing name for the installed smoke/integrity gate.

Compatibility output may continue to use:

```text
PACK SMOKE PASS
product: CodeSleuth
theme: codesleuth
```

### 5.4 Playbooks

Playbooks are ready-to-run task recipes. They are **not** Skills.

```text
Skill    = reusable OpenCode capability/protocol
Playbook = task recipe for a concrete repository operation
```

Playbooks should route into OpenCode execution and stable `/repo-*` commands where appropriate.

### 5.5 Help

Help explains the product model, not only button mechanics:

- CodeSleuth vs OpenCode
- quick start
- Skills vs Playbooks vs Tools vs Profiles vs Agent profile
- OpenCode `build` as the native controller; CodeSleuth does not replace its prompt
- evidence/durable state
- permissions
- Verify/update lifecycle
- extension installation/management when present
- safe removal

### 5.6 Open CodeSleuth

Launches OpenCode with CodeSleuth project-local configuration/theme when CodeSleuth owns those managed defaults.

User-owned OpenCode TUI/theme configuration must be preserved.

## 6. Extension surfaces

Core feature development is frozen, but the ecosystem is intentionally open-ended.

Allowed extension growth:

- repository profiles (`rust`, `typescript`, `python`, `node`, future ecosystems);
- OpenCode Skills;
- Playbooks;
- OpenCode-native tools/plugins/integrations;
- small user-authored tools that can be installed or loaded into OpenCode;
- catalog/discovery/install/update/remove UI for those extensions in CLI/TUI;
- metadata, validation, compatibility checks, and safe lifecycle around extensions.

CodeSleuth may make these extensions easy to find and install. **OpenCode remains responsible for running them and for model/tool orchestration.**

Extension-management UI is allowed to grow because it scales the existing infrastructure rather than adding a new core workflow.

## 7. Explicit feature freeze

After this branding/production track, do **not** add new CodeSleuth core workflows or a parallel execution stack.

Out of scope without a new architecture decision:

- a CodeSleuth-specific agent loop;
- a CodeSleuth supervisor prompt on OpenCode `build`;
- a second tool router/tool-calling protocol;
- a second model/session runtime;
- replacement repository-review engine that bypasses OpenCode;
- duplicate implementations of OpenCode Skills/tools merely to expose them in the menu;
- unrelated dashboards/workflows that do not improve control of existing OpenCode infrastructure or extension lifecycle.

From this point, core changes are limited to:

```text
bug fixes
compatibility
security/safety
accessibility/readability
performance
packaging/install/update correctness
tests/CI
production hardening
```

## 8. Canonical ASCII identity

Full console mark is permitted on entry/brand surfaces; compact identity is preferred when space is constrained.

```text
+-------------------------------------------------+
|  CODE:SLEUTH // EVIDENCE OPERATIONS CONSOLE    |
+----------------------+--------------------------+
                   [ TARGET : SOURCE ]
                   [ EVIDENCE : LIVE ]
```

Essential state must never exist only inside ASCII art.

## 9. Colormap contract

Machine-readable source: [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json).  
OpenCode implementation: [`../pack/.opencode/themes/codesleuth.json`](../pack/.opencode/themes/codesleuth.json).

Dark-mode core:

| Role | Hex | Meaning |
|---|---|---|
| background | `#081018` | app background |
| panel | `#0E1822` | panels/header/footer |
| element | `#13212D` | elevated controls |
| border | `#29404F` | inactive border |
| border-active | `#3E718A` | focus/active border |
| primary | `#63D5F4` | identity/navigation |
| text | `#D8E3EB` | normal text |
| muted | `#71879A` | secondary/unknown |
| success | `#62D394` | verified/ready/pass |
| warning | `#F0C36A` | attention/incomplete |
| error | `#F07178` | failure/blocking |

Green is never generic decoration. It means successful/verified state.

## 10. Responsive rules

Production acceptance must include at least:

```text
80x24
120x35
```

Also exercise narrower layouts representative of a phone/Termux/remote-terminal viewport.

At narrow widths:

- use one-column cards/rows;
- navigation may move to a compact footer/selector;
- full ASCII art may collapse to `CODE:SLEUTH // EVIDENCE CONSOLE`;
- repository, readiness, Verify, Help, extension discovery, and launch must remain reachable;
- no essential content may require horizontal scrolling.

At wide widths:

- prefer a persistent navigation rail;
- use the additional width for status/evidence detail, not feature proliferation.

## 11. Production acceptance runbook

Required static checks:

```bash
python3 -m py_compile \
  pack/.opencode/bin/codesleuth_tui.py \
  pack/.opencode/bin/review_pack_tui_bootstrap.py \
  pack/.opencode/bin/review-pack-smoke.py \
  smoke.py \
  tests/test_lifecycle.py

python3 -m json.tool pack/.opencode/themes/codesleuth.json >/dev/null
python3 -m json.tool pack/.opencode/tui.json >/dev/null
python3 -m json.tool docs/CODESLEUTH-COLORMAP.json >/dev/null
```

Then run the complete repository test suite/gates present on the branch, including TUI and project-lifecycle tests where available.

Manual acceptance:

- normal install on disposable repo;
- update existing versioned install;
- preserve user-owned OpenCode config/theme;
- Verify passes;
- Help/Playbooks remain readable;
- OpenCode launches successfully through CodeSleuth;
- existing OpenCode commands, Skills, and tools remain directly usable;
- long-running/large-context repository review is not constrained by the CodeSleuth shell;
- narrow and wide layouts remain usable.

## 12. Governance

This runbook and `CODESLEUTH-PRODUCT-CONTRACT.md` are canonical.

A core feature outside the allowed extension seams requires an explicit architecture decision. Otherwise the default answer is **do not add it**.

Production work should now converge by fixing defects against these contracts, not by expanding scope.
