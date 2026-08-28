# Playbooks catalog TUI (design sketch)

**Status:** first instance of the shared extension-load units; sketches remain non-canonical UI art
**Classification:** ordinary feature population inside `CC-TUI` + `CC-PACK` (load wizard also touches lifecycle-safe overlay install)  
**SIB0:** not reopened. Catalog and install/load UX are already allowed by [`CODESLEUTH-PRODUCT-CONTRACT.md`](CODESLEUTH-PRODUCT-CONTRACT.md) §5–6.

Shared Catalog / Detail / Load-wizard contract (kinds beyond Playbooks): [`EXTENSION-LOAD-UNITS.md`](EXTENSION-LOAD-UNITS.md).

This document is a feature request plus design notes. It does **not** change
Playbook execution, host ownership, or user-facing UI manuals. Canonical
composition remains [`PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md).
User-facing UI docs stay terminal-native; the Cursor canvases below are
incubation sketches, not maintained mockups of the live TUI.

Interactive sketches (Cursor canvas sources):

- as-is: [`sketches/playbooks-current-screen.canvas.tsx`](sketches/playbooks-current-screen.canvas.tsx)
- to-be: [`sketches/playbooks-unit-sketches.canvas.tsx`](sketches/playbooks-unit-sketches.canvas.tsx)

## Problem

The TUI control labeled **Playbooks** (`#playbooks`, binding `p`) opens
`CodeSleuthPlaybookScreen`, a modal over `PromptScreen`. That screen is a
`RichLog` of profile-generated `/repo-*` recipes from `generate_prompts()`.
**Save playbooks** writes `.opencode/state/tui/suggested-prompts.md`.

Stored Playbooks already exist at `pack/.opencode/playbooks/<id>/` with
`playbook.json`, `PLAYBOOK.md`, and isolated `steps/`. Operators can start them
only through the host (`/playbook <id>` and command aliases). There is no
clickable catalog, no step/skill/tool inspection, and no load wizard.

The live modal therefore collides on the product word **Playbooks** while showing
a different object: suggested prompts.

Current pack catalog (implementation fact on this lineage, not acceptance):

| id | command alias |
| --- | --- |
| `repository-deep-review` | `/repo-review` |
| `repository-map` | `/repo-map` |
| `repository-documentation` | `/repo-docs` |
| `protected-capability-assessment` | `/repo-contracts` |
| `feature-port` | `/repo-port` |
| `eha-sib-acceptance` | `/eha-test` |
| `eha-repair` | `/eha-repair` |

## Goal

Replace the prompt-log modal with a Playbooks unit that:

1. lists installed Playbooks as selectable rows;
2. opens a detail view with the step DAG and highlighted Skills/Tools the
   model should apply on each step;
3. provides a load wizard for a new Playbook (inspect → validate → install).

Suggested prompts remain available under a **different** name (Review surface
and/or host `/repo-prompts`). Do not keep two features called Playbooks.

## Non-goals

- A CodeSleuth Playbook runner, scheduler, or session database.
- Materializing or executing Steps from the TUI.
- Silent overwrite of builtin `pack/.opencode/playbooks/`.
- Remote registry/URL install in the first slice (local folder or zip only).
- Weakening TUI viewport / visual-regression acceptance.

Launch from the TUI is a route to the host: copy `/playbook <id>` or
**Open CodeSleuth**. Execution stays OpenCode `build`, one Step at a time.

## Proposed UX

### Surface

New nav-route `playbooks` (peer of Review/Evidence/Tools). Home `#playbooks`
and `p` open this surface, not `generate_prompts()`.

### Catalog

Rows sourced from target overlay `.opencode/playbooks/*/playbook.json`, then
the installed pack catalog. Each row is a control (not log text): id, step
count, command alias, origin (`pack` / overlay). Actions: open detail,
copy `/playbook <id>`, **Load playbook**. Remove **Save playbooks**.

### Detail

Show identity, description, origin, and the step list from `playbook.json`:

```text
step.id · execution kind · isolation · output
  skills[] as chips
  tools[] as chips
```

Skill/Tool chips open the atomic contract or tool purpose. They do not invoke
the host, load a Skill into a model session, or call a Tool.

The card shows the whole DAG for the operator. The host still materializes
exactly one Step and loads only that Step's Skills.

### Load wizard

```text
Source → Inspect → Validate → Confirm → Result
```

Validate against the same invariants as
`tests/test_playbook_skill_contract.py` (`schema_version`, id equals folder
name, `PLAYBOOK.md` present, steps exist, DAG acyclic). Missing Skills or
empty `tools[]` are warnings, not invented names from markdown.

Install writes the target overlay `.opencode/playbooks/<id>/`. Collision with
a pack id requires explicit confirm or reject. The wizard does not start
`/playbook`.

## Manifest delta

`playbook.json` steps today declare `skill` / `skills` but not tools. Tools
live in step markdown. For reliable highlights, add optional per-step
`tools[]` as catalog metadata, not as a CodeSleuth tool router.

Builtin Playbooks should be filled from the actual Step texts. User-loaded
Playbooks may ship `tools: []` with a warning.

## Acceptance (when implemented)

Not claimed by this sketch commit.

1. Playbooks surface lists installed overlay+pack ids; rows are selectable.
2. Opening `eha-sib-acceptance` shows its six steps and declared Skills/Tools.
3. Skill chip does not start an agent.
4. Suggested prompts survive under another name; `#playbooks` no longer writes
   `suggested-prompts.md`.
5. Wizard installs a valid local Playbook into the overlay catalog and rejects
   a broken package with a reason.
6. Pack id collision is not a silent overwrite.
7. Launch copies `/playbook <id>` / opens OpenCode; TUI does not run Steps.
8. Viewport usable at `80x24` and `120x35`; Escape/Abort writes nothing.
9. Focused tests + `ruff check .` + `python -m pytest` for TUI and Playbook
   contract. Visual regression if surface layout changes.

## Sketch comments

The to-be canvas carries numbered comments **C1–C17** (nav placement, no
second runner, row-as-object, overlay install, isolation honesty). Treat those
as design notes for the implementation PR, not as accepted UI chrome.
