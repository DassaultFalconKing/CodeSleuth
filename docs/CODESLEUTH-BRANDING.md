# CodeSleuth UI Branding & Interaction Runbook

**Status:** Accepted / canonical / feature-frozen core  
**Architecture authority:** [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md)

## Product identity

```text
CodeSleuth
Code-discipline for LLM repository work
Evidence-first repository intelligence
```

CodeSleuth is a thin discipline/control layer, not a replacement runtime.

```text
CodeSleuth = Skills / control surface / evidence discipline / lifecycle
Host       = controller / model / agents / tools / execution
```

OpenCode is the current full installed host. NovaClaw is the first tested external MCP host. Other host integrations may reuse the same Skills, evidence discipline and narrow tools without moving execution authority into CodeSleuth.

## Visual direction

Dark terminal-native evidence console with restrained cyan/steel accents and semantic green/amber/red state colors.

The product should feel like an inspection instrument, not a generic AI skin.

Canonical flow:

```text
repository -> inventory -> inspect -> evidence -> verify -> finding
```

Operational labels remain simple: `Repository`, `Review`, `Evidence`, `Verify`, `Finding`, `Coverage`, `Playbooks`, `Tools`, `Profiles`, `Skills`, and `Settings`.

## Graphics and documentation rule

The visual design is considered settled. Do not repeatedly regenerate interface art.

### Canonical brand

The only canonical ASCII brand is the implemented `CODESLEUTH_ART` constant in:

```text
pack/.opencode/bin/codesleuth_tui.py
```

The top-level README may copy that block verbatim. Other documentation should reference the implementation instead of maintaining another hand-edited copy.

### UI documentation

User-facing UI documentation must be terminal-native and cheap to maintain:

- use terminal/text snapshots captured from the real application;
- use exact implemented labels and button names;
- highlight controls with Markdown text/backticks or annotations around the captured text;
- do not create synthetic PNG/JPEG/WebP/SVG UI mockups, reference boards, decorative renders, or pseudo-screens that need to be manually kept in sync;
- do not ask code assistants to redraw the TUI merely to update a manual.

If the real UI changes, update the textual snapshot from the real TUI. The documentation should be cheaper than taking an ordinary screenshot, not more expensive.

### Mermaid exception

Mermaid is the only maintained general diagram format allowed for product documentation.

It is allowed because it **encodes relationships as readable/reviewable text**, not because CodeSleuth needs decorative graphs. Use it only where structure is materially clearer as a diagram, especially repository context/architecture relationships.

Generated Mermaid must remain a presentation of verified structure. It is never branding, a UI mockup, or a second source of repository truth.

## Navigation semantics

Current navigation is:

```text
Home
Review
Evidence
Tools
Settings
```

| Surface | Purpose |
|---|---|
| Home | repository/readiness/activity/next action |
| Review | discover and invoke repository-review commands/Playbooks |
| Evidence | evidence state, findings, coverage and durable review state |
| Tools | Skills, tools, extensions, Verify/update utilities |
| Settings | profiles, permissions, runtime and lifecycle configuration |

A menu item may route to host-native functionality. It must not duplicate that functionality in a second CodeSleuth orchestration engine.

## Core actions

The implemented console currently exposes these user-facing actions contextually:

```text
Configure
Verify
Check Updates
Update
Playbooks
Help
Uninstall
Open CodeSleuth
```

`Verify` is the user-facing name for the installed smoke/integrity gate.

Playbooks are task recipes; Skills are reusable capabilities/protocols.

## Extension surfaces

Allowed growth remains intentionally simple:

- repository profiles;
- Skills;
- Playbooks;
- host-native tools/plugins/integrations;
- small user-authored tools;
- catalog/install/update/remove UI around those extensions;
- additional agent-host integrations such as Codex, Cursor, Hermes, BodegaOne and Pi-harness.

CodeSleuth may help discover and configure these extensions. The host remains responsible for model/tool orchestration.

## Feature freeze

Do not add:

- a CodeSleuth-specific agent loop;
- a second supervisor/controller;
- a second model/session runtime;
- a replacement review engine that bypasses the host;
- duplicate implementations of host Skills/tools only to expose them in the menu.

Core work is production hardening plus the explicitly allowed extension/integration seams: bug fixes, compatibility, security, accessibility, performance, packaging, tests and CI.

## Colormap

Machine-readable source: [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json).  
OpenCode implementation: [`../pack/.opencode/themes/codesleuth.json`](../pack/.opencode/themes/codesleuth.json).

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

Green means successful/verified state, not decoration.

## Responsive acceptance

Exercise at least:

```text
80x24
120x35
```

Also exercise narrower terminal/Termux/remote-terminal viewports when relevant.

At narrow widths use one column and compact navigation. At wide widths use extra space for status/evidence detail, not more features. No essential content should require horizontal scrolling.

Documentation for responsive behavior uses captured terminal text/output from those real runs, not separate artwork.

## Governance

This runbook and `CODESLEUTH-PRODUCT-CONTRACT.md` are canonical. Core behavior outside the allowed extension seams requires an explicit architecture decision.

The branding direction is settled. Future maintainers should spend model/context budget on correctness, host compatibility, evidence discipline and user instructions, not on regenerating visual assets.
