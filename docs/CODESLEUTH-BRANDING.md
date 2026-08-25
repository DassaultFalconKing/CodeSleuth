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

OpenCode is the current full installed host. NovaClaw is the first tested external MCP host. Other host integrations may reuse the same Skills and evidence discipline without moving execution authority into CodeSleuth.

## Visual direction

Dark terminal-native evidence console with restrained cyan/steel accents and semantic green/amber/red state colors.

The product should feel like an inspection instrument, not a generic AI skin.

Canonical flow:

```text
repository -> inventory -> inspect -> evidence -> verify -> finding
```

Operational labels remain simple: `Repository`, `Review`, `Evidence`, `Verify`, `Finding`, `Coverage`, `Playbooks`, `Tools`, `Profiles`, `Skills`, and `Settings`.

## Reference layouts

These are text design sketches, not screenshots and not separate product surfaces.

### Desktop / wide terminal

```text
┌─ CodeSleuth · Evidence Console ─────────────────────────────────────────────┐
│ Home       Repository   ./project                               READY       │
│ Review     Profile      python · Open-weight                                │
│ Evidence   Runtime      OpenCode build                                      │
│ Tools      Next         /repo-review                                        │
│ Settings                                                                    │
│            ──────────────────────────────────────────────────────────────    │
│            Verify       PASS                                                │
│            Evidence     no active review                                    │
│            Recent       installation verified                              │
│                                                                             │
│            [ Configure ]  [ Verify ]  [ Playbooks ]  [ Help ]              │
└─────────────────────────────────────────────────────────────────────────────┘
```

Desktop normally uses a persistent navigation rail:

```text
Home
Review
Evidence
Tools
Settings
```

### Narrow terminal

```text
┌─ CodeSleuth ─────────────────────┐
│ ./project                 READY  │
│ Profile  python                  │
│ Runtime  OpenCode build          │
│ Next     /repo-review            │
│                                 │
│ [ Configure ]   [ Verify ]       │
│ [ Playbooks ]   [ Help ]         │
├─────────────────────────────────┤
│ Home · Review · Evidence · Tools │
│ Settings                         │
└─────────────────────────────────┘
```

Narrow mode is a terminal layout, not a promise of a native mobile application.

## Navigation semantics

| Surface | Purpose |
|---|---|
| Home | repository/readiness/activity/next action |
| Review | discover and invoke repository-review commands/Playbooks |
| Evidence | evidence state, findings, coverage and durable review state |
| Tools | Skills, tools, extensions, Verify/update utilities |
| Settings | profiles, permissions, runtime and lifecycle configuration |

A menu item may route to host-native functionality. It must not duplicate that functionality in a second CodeSleuth orchestration engine.

## Core actions

```text
Configure
Verify
Playbooks
Help
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

Core work is production hardening: bug fixes, compatibility, security, accessibility, performance, packaging, tests and CI.

## ASCII identity

Full mark is permitted on README/entry surfaces; compact identity is preferred when space is constrained.

```text
        .--------.
       /  .----.  \            ____          _      ____  _            _   _
      /__/______\__\          / ___|___   __| | ___/ ___|| | ___ _   _| |_| |__
         |  • •  |           | |   / _ \ / _` |/ _ \___ \| |/ _ \ | | | __| '_ \
         |   ▿   |           | |__| (_) | (_| |  __/___) | |  __/ |_| | |_| | | |
        /|  ---  |\           \____\___/ \__,_|\___|____/|_|\___|\__,_|\__|_| |_|
       / |       | \
         |  ◯    |
         | /|\   |            CODE:SLEUTH // EVIDENCE OPERATIONS CONSOLE
        /  / \    \           repository → evidence → verify → finding
```

Essential state must never exist only inside ASCII art.

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

At narrow widths use one column and compact navigation. At wide widths use the extra space for status/evidence detail, not more features. No essential content should require horizontal scrolling.

## Governance

This runbook and `CODESLEUTH-PRODUCT-CONTRACT.md` are canonical. Core behavior outside the allowed extension seams requires an explicit architecture decision.
