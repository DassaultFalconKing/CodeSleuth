# Branch Triage Ledger

This document records maintainer dispositions for historical or ambiguous Git branches after exact comparison against the current release line.

It is a provenance and maintenance ledger, not a source of runtime, SIB, EHA, or release authority. Exact Git identity and canonical acceptance evidence remain authoritative.

## Disposition vocabulary

- **KEEP** — branch still has an active repository role.
- **REQUIRED** — branch carries a material delta that still needs target-native delivery.
- **DEFER** — material delta exists but is intentionally postponed.
- **RETIRED** — branch no longer carries an independent delivery obligation.
- **SUPERSEDED** — the relevant semantics are already represented more precisely elsewhere.

Delivery decisions:

- **REUSE** — use the branch delta directly after normal review/gates.
- **PORT / ADAPT** — recover semantics into the current target rather than merge stale history wholesale.
- **NO CHANGE** — no repository change is required from this branch.
- **BLOCK** — do not integrate until the stated conflict is resolved.

Archival refs preserve historical branch-tip identity under `archive/YYYY-MM-DD/<original-branch>` where available. Archiving does not transfer acceptance and does not make the archived branch an active authority.

## `supervisor`

**Reviewed against:** current release lineage rooted at `dev/release-0.4.0 @ 2d62781f70bbf079a84afcb8c429e8d8c5e87413`.

**Historical tip:** `a0ba3177ca43c2f71b553641b3177da33b37ec4a`

**Parent:** `2c0480039746e490c5bb6da26837f50c253d3fb2`

**Commit:** `chore(supervisor): initialize supervisor branch from findings-ledger integration`

### Mechanical evidence

- `supervisor` is one commit ahead of parent `2c048003...`.
- Comparing `2c048003...` to `a0ba3177...` yields **no changed files**.
- The `supervisor` commit tree is identical to its parent tree (`d558916ade906c864a89a99a343fb839b6f83f1e`).
- Against current `main`, Git reports the ref as diverged because of the empty marker commit, but it carries no unique repository content.
- Historical controller work already established that OpenCode's native host controller remains execution authority; CodeSleuth does not introduce a second supervisor/model-controller runtime.

### Verdict

- **Semantic status:** `RETIRED`
- **Delivery:** `NO CHANGE`
- **Merge:** `NO`
- **Cherry-pick:** `NO`
- **Semantic Refit:** `NO`
- **Unique runtime delta:** `NONE`
- **Architecture reopened:** `NO`
- **Archive:** `archive/2026-08-27/supervisor`

`supervisor` is therefore provenance only. Do not use it as a merge candidate, release candidate, controller-design source, or evidence that a separate CodeSleuth supervisor runtime exists.
