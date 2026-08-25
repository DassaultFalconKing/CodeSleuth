# CodeSleuth UI Branding Runbook

**Status:** Accepted / canonical for the current CodeSleuth branding track  
**Applies to:** user-facing Textual TUI, OpenCode runtime theme, terminal screenshots, help/playbook surfaces, and future CodeSleuth interaction shells  
**Compatibility boundary:** internal `review-pack*` filenames, `review-pack.json`, `review-pack-user.json`, and `/repo-*` commands remain compatibility contracts until a separate migration changes them.

## 1. Product identity

Product name:

```text
CodeSleuth
```

Primary descriptor:

```text
Evidence-first repository intelligence
```

Primary TUI name:

```text
CodeSleuth · Evidence Console
```

Runtime relationship:

```text
CodeSleuth = product / evidence workflow
OpenCode   = execution and integration runtime
```

OpenCode may be named in attribution, help, diagnostics, and runtime surfaces. It must not replace CodeSleuth as the primary user-facing product identity.

## 2. Accepted visual direction

The accepted direction is a dark terminal-native evidence console with restrained cyan/steel accents and semantic success/warning/error colors.

The interface should feel like an inspection instrument rather than a generic AI chat skin:

```text
repository
    |
    v
 inventory
    |
    v
 inspect
    |
    v
 evidence
    |
    v
 verify
    |
    v
 finding
```

Visual motifs may use investigator/source/evidence imagery, but function and evidence state must remain more prominent than decoration.

Do not turn every control into detective-themed vocabulary. `Repository`, `Evidence`, `Verify`, `Finding`, `Coverage`, `Playbooks`, and `Review` are the canonical operational terms.

## 3. Canonical ASCII identity

The current full console mark is:

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

The canonical evidence-chain mark is:

```text
+-- source --+     +-- evidence --+
| repository | --> | verified    |
+------------+     +--------------+
```

Rules:

- Full ASCII art belongs on entry/dashboard or other deliberate brand surfaces.
- Compact evidence marks may appear in configuration/help/verification surfaces.
- Do not repeat the full mark inside every modal.
- ASCII must remain readable in monospaced terminals and must not encode essential state that is absent from text.
- If a terminal is too narrow, prefer a compact text identity (`CODE:SLEUTH // EVIDENCE CONSOLE`) over broken art.
- ASCII art is presentation only; accessibility and automation must rely on normal labels/status text.

## 4. Screen playbook

### 4.1 Evidence Console

Primary composition:

```text
[ CodeSleuth ASCII identity ]
Evidence-first repository intelligence

Repository
[ /path/to/repository ]

+-- STATUS --------------------------------------------------+
| READY / ATTENTION / SETUP                                 |
| CodeSleuth version                                        |
| installation state / completeness                         |
| detected profiles                                         |
| recommended next action                                   |
+------------------------------------------------------------+

[ Configure ] [ Verify ] [ Check Updates ] [ Update ]
[ Playbooks ] [ Help ] [ Open CodeSleuth ]

+-- ACTIVITY / LOG ------------------------------------------+
| evidence/runtime/update output                            |
+------------------------------------------------------------+
```

The dashboard answers, in order:

1. What repository am I operating on?
2. Is CodeSleuth ready?
3. What evidence/runtime profile is active?
4. What should I do next?
5. What just happened?

### 4.2 Configuration

Use the title:

```text
CodeSleuth Configuration
```

Sections remain task-oriented:

1. Installation
2. Repository profile
3. Evidence permissions
4. Runtime
5. Planned policy

The configuration screen may display the compact source/evidence ASCII mark. It must keep explicit consent controls for web search/fetch, edits, and external directories.

### 4.3 Verify

`Verify` is the user-facing name for the installed smoke gate.

Successful terminal output should make the product and theme explicit, for example:

```text
PACK SMOKE PASS
product: CodeSleuth
theme: codesleuth
```

Compatibility output such as `PACK SMOKE PASS` may remain until the underlying pack contract is migrated.

### 4.4 Playbooks

`Playbooks` are user-facing, ready-to-run task recipes generated from repository profiles.

They are **not** OpenCode Skills.

Use:

```text
CodeSleuth Playbooks
```

Distinction:

```text
Skill     = reusable OpenCode capability/protocol
Playbook  = prompt/task recipe for a concrete repository operation
```

A Playbook should be:

- specific enough to run without rewriting the intent;
- evidence-first;
- explicit about scope/ref when relevant;
- clear about verification/coverage expectations;
- compatible with the stable `/repo-*` commands where appropriate.

### 4.5 Help

Help should explain the actual product model, not merely button mechanics:

- CodeSleuth vs OpenCode;
- quick start;
- Skills vs Playbooks;
- stable commands;
- evidence and durable state;
- permissions;
- verify/update behavior;
- safe deinstallation.

### 4.6 Open CodeSleuth / OpenCode runtime

The launcher enters OpenCode with the project-local CodeSleuth theme when CodeSleuth owns the theme/TUI configuration.

Recommended attribution:

```text
CodeSleuth · OpenCode
```

or:

```text
CodeSleuth
Powered by OpenCode
```

A user-owned OpenCode theme/TUI override must be preserved. Branding must not overwrite unrelated project-local OpenCode configuration merely to achieve visual uniformity.

## 5. Canonical interaction vocabulary

Prefer:

| Purpose | Canonical user-facing term |
|---|---|
| product | CodeSleuth |
| main TUI | Evidence Console |
| target | Repository |
| readiness test | Verify |
| suggested tasks | Playbooks |
| deep analysis | Review |
| proof material | Evidence |
| accepted result | Finding |
| source completeness | Coverage |
| continuation | Resume |
| config screen | CodeSleuth Configuration |
| runtime launch | Open CodeSleuth |

Compatibility names such as `review-pack`, `smoke`, and `/repo-*` remain valid implementation/API identifiers where already established.

## 6. Status semantics

Status words carry meaning and should not be used decoratively.

| Status | Meaning | Color role |
|---|---|---|
| `READY` | installed/validated and usable | success |
| `ATTENTION` | installed but incomplete, conflicting, or invalid | warning |
| `SETUP` | not installed / initial configuration required | primary |
| `VERIFIED` | evidence or validation contract satisfied | success |
| `BLOCKED` | cannot proceed without external/user action | error or warning by severity |
| `UNKNOWN` | state cannot be established | muted |

Never use green merely for “active”. Green is reserved for successful/verified state.

## 7. Colormap contract

The machine-readable source of the branding roles is [`CODESLEUTH-COLORMAP.json`](CODESLEUTH-COLORMAP.json).

The runtime OpenCode implementation is [`../pack/.opencode/themes/codesleuth.json`](../pack/.opencode/themes/codesleuth.json).

Dark-mode core:

| Role | Hex | Intended use |
|---|---|---|
| background | `#081018` | application background |
| panel | `#0E1822` | panels/header/footer |
| element | `#13212D` | controls/elevated elements |
| border | `#29404F` | inactive borders |
| border-active | `#3E718A` | focus/active border |
| primary | `#63D5F4` | identity/navigation/active headings |
| secondary | `#8AA7B8` | secondary labels/runtime attribution |
| accent | `#A7E3F2` | emphasis without state semantics |
| text | `#D8E3EB` | normal text |
| muted | `#71879A` | unknown/de-emphasized metadata |
| success | `#62D394` | verified/ready/pass |
| warning | `#F0C36A` | attention/incomplete/caution |
| error | `#F07178` | failure/contradiction/blocking error |

Light mode is supported by the OpenCode theme and the machine-readable colormap, but the CodeSleuth Textual console currently treats the dark evidence-console presentation as its canonical branded surface.

## 8. Component rules

Buttons:

- primary/navigation action: primary cyan family;
- successful launch/confirmed positive action: success family;
- ordinary actions: neutral panel/element;
- destructive actions, when added, must use error semantics and explicit wording.

Panels:

- use borders to communicate grouping;
- active/focused borders may use `border-active`;
- avoid large solid cyan surfaces: cyan is an information/navigation accent, not wallpaper.

Logs:

- success/verified lines: success;
- incomplete/warnings: warning;
- failures: error;
- ordinary trace/output: text or muted;
- never color entire multi-line logs green because the command returned zero.

Diffs:

- additions use success roles;
- removals use error roles;
- context remains muted/neutral.

## 9. Responsive terminal rules

Local visual acceptance must include at least:

```text
80x24
120x35
```

At narrow widths:

- controls may wrap or scroll, but labels must remain understandable;
- the full ASCII identity may be replaced by a compact identity if it causes unusable vertical or horizontal pressure;
- no essential status may exist only inside ASCII art;
- the repository path, readiness state, Verify, Help, and launch path must remain reachable.

The current Textual surface may scroll vertically; that is acceptable. Horizontal destruction of the ASCII identity is not.

## 10. Change playbook

When adding or changing a user-facing CodeSleuth surface:

1. Reuse the canonical product name and vocabulary.
2. Assign colors by semantic role, not by aesthetic preference.
3. Reuse `CODESLEUTH-COLORMAP.json` / `codesleuth.json`; do not invent one-off hex values unless extending the palette intentionally.
4. Keep OpenCode attribution secondary to CodeSleuth product identity.
5. Preserve user-owned OpenCode configuration.
6. Keep compatibility identifiers stable unless the change explicitly includes a migration.
7. Add/adjust smoke or lifecycle coverage for new managed branding assets.
8. Run syntax/JSON checks and lifecycle tests.
9. Inspect at 80x24 and 120x35.
10. Treat broken readability, misleading state color, or overwritten user theme configuration as release-blocking branding defects.

## 11. Local acceptance runbook

From the repository root:

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

python3 tests/test_lifecycle.py
```

Then launch against a disposable Git repository and inspect:

```bash
./review-pack /path/to/test-repo
```

Acceptance checks:

- CodeSleuth is the primary identity.
- ASCII identity is legible and not mistaken for status.
- `Verify` runs the smoke gate.
- `Playbooks` and `Help` use current terminology.
- configuration uses evidence-permission language.
- OpenCode starts through the CodeSleuth launcher/theme path.
- user-owned OpenCode theme/TUI configuration survives install/update.
- semantic colors match the colormap.
- 80x24 and 120x35 remain usable.

## 12. Governance

This document is the accepted branding runbook for the current product track.

If implementation and this runbook diverge:

- compatibility/safety behavior wins temporarily;
- the divergence must be documented as a defect or intentional migration;
- update this runbook in the same change that intentionally changes the accepted visual/interaction contract.

Do not silently reinterpret the colormap or vocabulary in individual components.
