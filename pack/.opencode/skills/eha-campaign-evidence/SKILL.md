---
name: eha-campaign-evidence
description: Record and inspect Exact-Head Acceptance campaigns, SIB verdicts, provenance, and derived history through durable evidence
slash: true
---

# EHA campaign evidence

## Atomic contract

**Input:** one immutable exact target SHA, an active durable review checkpoint, a bound producer provenance sidecar, and the required SIB0/SIB1/SIB2 profile results or status request.

**Objective:** start, record, or load EHA campaigns through `eha_state_*` while preserving producer attribution through `provenance_state_*`, without inventing a second evidence authority.

**Output:** campaign ID, structured verdict/repair history, claimable SIB degrees, verified producer watermark for proof/report output, and optional bounded Mermaid projection.

**Stop:** literal current HEAD differs from the campaign target SHA, required review checkpoint is missing, provenance sidecar cannot be verified for the active proof session, or a material claim would require raw-rewriting append-only ledger history.

**Must not:** repair the target during a test campaign, inherit PASS across SHAs, raw-rewrite `eha.ndjson`, treat Mermaid as acceptance authority, or treat provenance as cryptographic identity or SIB claimability evidence.

Read `docs/DURABLE-EVIDENCE-STORE.md`, `.opencode/PROVENANCE-WATERMARK.md`, `docs/EXACT-HEAD-ACCEPTANCE.md`, `docs/SIB-CANDIDATE-SELECTION.md`, and `docs/EHA-REPAIR-LOOP.md`.

After `review_state_start`, call `provenance_state_bind` once with the stable opaque actor for this producer session before `eha_state_start_campaign`. Before producing the final EHA proof/report, call `provenance_state_load` and include its verified watermark. If historical evidence predates provenance, report attribution unavailable rather than inventing it.

EHA records live under `.opencode/state/reviews/<reviewId>/eha.ndjson` as append-only history alongside `review_state`; producer attribution lives in immutable `provenance.json` in that same review directory. The sidecar does not alter ledger verdicts or claimability.

Use `eha_state_start_campaign`, `eha_state_record_verdict`, `eha_state_record_repair`, `eha_state_load`, and `eha_state_mermaid`. SIB levels define what is proven; EHA defines which exact SHA the proof belongs to; provenance records who the producer session declared itself to be. A repair commit inherits code history, not acceptance evidence.

For SIB2 interface composition, the canonical `TUI visual regression / Ubuntu` job in `docs/TUI-VISUAL-REGRESSION.md` is required evidence. Inspect `screen.svg`, `ui.log`, `events.log`, and `analysis.json` when a visual scenario fails.

When stale or divergent work is involved, apply `docs/SEMANTIC-REFIT.md` (`semantic-refit`) before starting a new campaign on the integrated `dev/release-X.Y.Z` head.
