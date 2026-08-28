# Provenance watermark contract

CodeSleuth records an **attribution watermark** for coding-agent work and for reports/proofs produced by an agent session.

The watermark answers one narrow question:

> Which declared producer/session authored or recorded this change or evidence output?

It is **not** a cryptographic signature, identity proof, authorization token, acceptance result, or substitute for Git GPG/SSH signing. Anyone who knows an actor code and this public algorithm can reproduce a watermark. Exact Git SHA/blob identity, tests, durable review/EHA ledgers, and canonical gates remain stronger engineering authority.

## Mandatory coding-session rule

Before the first repository modification, every coding agent must read this contract and keep one stable opaque actor code for the logical session. Installed CodeSleuth targets receive the packaged copy at `.opencode/PROVENANCE-WATERMARK.md`; the CodeSleuth source repository keeps this normative copy at `docs/PROVENANCE-WATERMARK.md`.

Use an opaque short identifier such as `s56` or another maintainer/agent-assigned code. Do not silently change actor code within one logical session. Do not infer a model or human identity from Git author metadata when the actual producer is unknown. Use `anon` when attribution is unavailable instead of inventing provenance.

## Commit watermark

For a commit authored by a coding agent, append this trailer when the workflow permits commit-message control:

```text
Trace-Id: <actor>-<12 lowercase hex>
```

The v1 digest is deterministic:

```text
SHA256(
  "codesleuth-provenance-v1|commit|" +
  <actor> + "|" +
  <full parent commit SHA> + "|" +
  <normalized commit subject>
)[:12]
```

Normalize the subject by taking only the first commit-message line, trimming it, lowercasing it, collapsing every whitespace run to one ASCII space, and encoding as UTF-8.

For explicitly historical `s56` records only, a verifier may accept the original v0 domain:

```text
SHA256("codesleuth-sol56-v1|" + <parent SHA> + "|" + <normalized subject>)[:12]
```

New `s56` watermarks use the generic v1 domain.

## Session/evidence watermark

Reports and proof workflows need attribution before a future commit exists. Their session digest is:

```text
SHA256(
  "codesleuth-provenance-v1|session|" +
  <actor> + "|" +
  <current full HEAD SHA> + "|" +
  <host session id>
)[:12]
```

After `review_state_start`, bind the producer with `provenance_state_bind`. CodeSleuth stores an immutable sidecar beside the durable review evidence:

```text
.opencode/state/reviews/<reviewId>/provenance.json
```

The sidecar contains at least:

```json
{
  "schemaVersion": 1,
  "actor": "<opaque actor>",
  "watermark": "<actor>-<12 hex>",
  "kind": "session-attribution",
  "headSha": "<full SHA>",
  "reviewId": "<review id>"
}
```

The host session identifier participates in verification and is kept in the local sidecar, but reports normally expose only the opaque watermark. Rebinding the same review to a different producer, session, or HEAD fails closed. A changed HEAD is reported as a freshness mismatch, not silently re-attributed.

The sidecar is part of the durable evidence directory but is **attribution metadata**, not a replacement for `state.json`, `findings.ndjson`, or `eha.ndjson`. Existing ledgers remain semantically authoritative for their own claims.

## Reports

Every newly generated CodeSleuth analytical report must include:

```text
- provenance: <actor>-<12 hex>
```

A report produced from the active review loads `provenance_state_load` and copies the verified watermark. If the sidecar is missing for historical evidence, report that provenance is unavailable/`anon`; do not invent a producer.

If a report combines evidence from multiple producer sessions, record the renderer watermark as `provenance` and list source watermarks separately as `source provenance`.

## EHA and durable proof

Before starting a new EHA campaign, bind provenance to its active durable review. EHA reports must load and include that watermark together with the exact campaign/review IDs and target SHA.

Provenance does **not** participate in SIB claimability. A correct watermark cannot turn stale, moved-head, incomplete, corrupt, or failing evidence into PASS. Conversely, missing attribution does not rewrite an old verdict; it means producer attribution is unavailable and must be reported honestly.

EHA authority remains:

- exact target SHA;
- append-only `eha.ndjson` campaign/verdict/repair history;
- required profile evidence and canonical gates;
- exact-head freshness rules.

## Coding-agent behavior

A coding or review agent must:

1. read this document before the first repository write;
2. keep one opaque actor code for the logical session;
3. after starting durable review state, call `provenance_state_bind` with that actor code when evidence/reports are being produced;
4. include the deterministic `Trace-Id` trailer on agent-authored commits when it controls the commit message;
5. load and include the verified session watermark in CodeSleuth reports and EHA proof reports;
6. use `anon` when attribution is unavailable instead of guessing;
7. never describe the watermark as a cryptographic signature or proof of model identity.

Review-only agents that do not modify application code still attach session provenance to reports/proofs they produce.

## Verification helpers

- `scripts/provenance_watermark.py` computes and verifies deterministic commit/session values outside OpenCode.
- `provenance_state_bind` creates the immutable review-session sidecar.
- `provenance_state_load` verifies that sidecar and reports whether its recorded HEAD equals current HEAD.

These helpers implement the contract. They do not create acceptance authority.
