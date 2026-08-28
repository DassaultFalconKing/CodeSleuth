# Provenance watermark contract

CodeSleuth records an **attribution watermark** for coding-agent work and for the reports/evidence produced by an agent session.

The watermark answers a narrow question:

> Which declared producer/session authored or recorded this change or evidence object?

It is **not** a cryptographic signature, identity proof, authorization token, acceptance result, or substitute for Git/GPG/SSH signing. Anyone who knows an actor code and the public algorithm can reproduce a watermark. Exact Git SHA, blob identity, tests, review ledgers, and EHA remain the engineering authorities.

## Mandatory session rule

Before the first repository modification in a coding-agent session, read this document and declare one stable opaque actor code for that session.

Use an opaque short identifier such as `s56` or another maintainer/agent-assigned code. Do not silently change actor code within one logical coding session. Do not infer a human or model identity from Git author metadata when the actual producer is unknown.

If the producer cannot be attributed, use `anon` rather than inventing provenance.

## Commit watermark

For a commit authored by a coding agent, append this trailer to the commit body when the workflow permits commit-message control:

```text
Trace-Id: <actor>-<12 lowercase hex>
```

The digest is deterministic:

```text
SHA256(
  "codesleuth-provenance-v1|commit|" +
  <actor> + "|" +
  <full parent commit SHA> + "|" +
  <normalized commit subject>
)[:12]
```

Normalize the subject as follows:

1. take only the first commit-message line;
2. trim leading/trailing whitespace;
3. convert to lowercase;
4. collapse every whitespace run to one ASCII space;
5. encode as UTF-8.

For historical compatibility, the `s56` actor may also be verified with the original v0 domain:

```text
SHA256("codesleuth-sol56-v1|" + <parent SHA> + "|" + <normalized subject>)[:12]
```

New `s56` watermarks SHOULD use the v1 generic domain above. A verifier MAY accept the v0 form only for explicitly historical records.

## Session/evidence watermark

Structured review and EHA evidence uses a session-level watermark so evidence can be attributed before a future commit exists.

The session digest is:

```text
SHA256(
  "codesleuth-provenance-v1|session|" +
  <actor> + "|" +
  <current full HEAD SHA> + "|" +
  <host session id>
)[:12]
```

Structured producers persist an envelope with at least:

```json
{
  "schemaVersion": 1,
  "actor": "<opaque actor>",
  "watermark": "<actor>-<12 hex>",
  "kind": "session-attribution",
  "headSha": "<full SHA>"
}
```

When the host exposes a session identifier, it participates in the digest but need not be copied into reports. The existing review checkpoint may already contain its own host session ID for routing; that does not make the watermark a security credential.

## Reports

Every newly generated CodeSleuth analytical report MUST include:

```text
- provenance: <actor>-<12 hex>
```

If a report summarizes structured review/EHA state, copy the watermark from the structured state that produced the report. Do not invent a new actor identity for historical findings merely because another agent rendered the Markdown.

If a report combines evidence from multiple producer sessions, record the renderer watermark as `provenance` and list source watermarks under a separate `source provenance` item or section.

## EHA and durable proof

`state.json` and new `eha.ndjson` events carry a provenance envelope. Provenance does **not** affect SIB claimability. A correct watermark cannot turn stale, moved-head, incomplete, corrupt, or failing evidence into PASS.

EHA rules remain:

- exact target SHA is authority;
- verdict evidence belongs only to the exact SHA on which it was recorded;
- provenance is attribution metadata, not acceptance authority;
- repair descendants must earn fresh evidence regardless of producer identity.

## Coding-agent behavior

A coding agent that changes the repository MUST:

1. read this document before the first write;
2. keep one opaque actor code for the logical session;
3. pass that actor code into CodeSleuth review/evidence producers when supported;
4. include the deterministic `Trace-Id` trailer on agent-authored commits when it controls the commit message;
5. include/report the structured provenance watermark in CodeSleuth reports;
6. use `anon` when attribution is unavailable instead of guessing;
7. never describe a watermark as a cryptographic signature or proof of model identity.

Review-only agents that do not modify code still attach session provenance to reports/evidence they produce.

## Verification helper

The repository provides `scripts/provenance_watermark.py` to compute and verify deterministic commit/session watermarks. The helper implements this document; this document remains the normative semantic contract.
