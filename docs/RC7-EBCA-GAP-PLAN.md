# RC7 EBCA Gap Plan

**Status:** ACCEPTED RC7 / POST-RC7 PLANNING INPUT  
**Source semantic baseline:** [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md)  
**RC7 base planning:** [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md), [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md), [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md)  
**Existing post-0.4 direction:** [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md), [`ROAD/ROAP.md`](ROAD/ROAP.md)

## 1. Purpose

This document audits RC7 planning against the canonical Evidence-Based Code Analysis (EBCA) thesaurus and records mechanisms that are required to make the vocabulary operational rather than ceremonial.

The audit distinguishes:

- **RC7 MUST** — required for generic SIB/EHA, implementation-ledger, repair and projection work to satisfy EBCA honestly;
- **POST-RC7** — important assurance hardening that should remain a separate future capability or release track rather than expanding RC7 into a universal assurance platform.

RC7 already covers several major EBCA invariants: exact subject identity, authority/presentation separation, append-only historical evidence, failed-SHA immutability, human adjudication, project-portable SIB semantics, generic EHA repair lineage, Markdown/NDJSON/Graphify/Mermaid projection parity and host-executed repair. This plan records the remaining important gaps.

---

# 2. RC7 MUST — first-class EBCA claim envelope

## Gap

The thesaurus defines a material claim through:

```text
subject
property
scope
assumptions
authority
evidence[]
environment[]
observedAt
result
limitations[]
```

Current RC7 planning uses those ideas but does not yet require a common typed envelope for cross-domain workflow artifacts.

## Requirement

RC7 must define a small non-authoritative transport/read-model type equivalent to `EvidenceClaimV1` / `ClaimEnvelopeV1`.

It is NOT a new evidence authority or generic claim database. It is a common typed way for SIB evaluation, Repair Cases, Repair Packets, implementation-ledger projections and assurance/report renderers to preserve the same EBCA dimensions.

At minimum:

```text
claimId
subject
property
scope
assumptions[]
authorityRefs[]
evidenceRefs[]
environment[]
observedAt
result
limitations[]
```

Where a workflow does not need one field, omission must be schema-defined rather than silently discarded by a renderer.

---

# 3. RC7 MUST — non-binary epistemic outcomes

## Gap

A generic EHA engine cannot honestly collapse all outcomes to PASS/FAIL.

EBCA requires at least:

```text
PASS
FAIL
INCONCLUSIVE
UNAVAILABLE
NOT_APPLICABLE
```

## Requirement

Project-portable SIB/EHA, Repair Case diagnosis and relevant gate results must preserve these distinct outcomes.

Rules:

- `INCONCLUSIVE` cannot become PASS because a model has a preferred interpretation;
- `UNAVAILABLE` cannot become PASS because a live service/credential/runner was unavailable;
- `NOT_APPLICABLE` requires explicit profile rationale;
- only profile-defined acceptance aggregation may produce a campaign-level PASS;
- missing required evidence is never silently treated as success.

The broader Context Epistemics vocabulary (`UNKNOWN`, `CONFLICTED`, etc.) remains post-RC7 except where a specific RC7 workflow needs it as a stop state.

---

# 4. RC7 MUST — acceptance-profile identity

## Gap

Exact SHA identity alone is insufficient. EBCA acceptance evidence is scoped by a named acceptance profile, environments and obligations.

Two runs called “SIB2” are not equivalent if they used different jobs, runtime versions, environments or acceptance obligations.

## Requirement

Introduce a project-portable acceptance-profile identity, likely part of `ProjectSibProfileV1` or a referenced `AcceptanceProfileV1`.

Minimum identity:

```text
profileId
profileVersion
profileDigest
project/profile authority evidence
required obligations[]
required gates[]
environment matrix[]
material tool/runtime identities[]
aggregation policy
NOT_APPLICABLE policy
```

Every EHA verdict must bind:

```text
exact subject SHA
+ profile identity/digest
+ environment/tool identities material to the claim
+ run/result identities
```

Acceptance invalidates for the current claim when subject identity, profile identity, required environment, or authoritative contract state changes. Historical evidence remains historical evidence.

---

# 5. RC7 MUST — completeness and truncation semantics

## Gap

SIB0 requires a capability-class inventory, but EBCA explicitly distinguishes bounded analysis from a completeness claim.

“I found 11 capability classes” does not prove “all fundamental capability classes are known.”

## Requirement

SIB profile discovery and brownfield capability discovery must record:

```text
discovery universe / method
bounded paths/sources
truncation state
unread/unavailable authority sources
completeness claim status
limitations
```

A SIB0 proposal must not be claimable if the inventory relies on hidden truncation or an uncontrolled universe without explicit human acceptance of the limitation.

Any UI/report/prompt that presents a complete inventory must be able to show why completeness is supportable.

---

# 6. RC7 MUST — evidence freshness and source rehydration

## Gap

RC6 handles exact-head and ExternalEvidence freshness, but generic RC7 repair packets may carry source excerpts, summaries or derived graph evidence into a later host session.

EBCA requires rehydration/source reopening before material action.

## Requirement

Before mutation, a repair host workflow must revalidate/reopen material refs against the exact current target/worktree.

A packet may carry excerpts for context, but each material tracked-source reference should retain path/blob/locator identity. If the blob no longer matches, the packet becomes stale for mutation and must be regenerated/revalidated.

Derived Graphify/Mermaid/Markdown evidence may navigate the repair but cannot substitute for reopening source authority.

---

# 7. RC7 MUST — smallest honest obligation reopening

## Gap

The thesaurus requires change-impact analysis to reopen the smallest honest obligation set. Current Repair Packet planning has change surface, but RC7 must make the verification semantics explicit.

## Requirement

For each repair delta derive/review:

```text
invariant core
+ affected contract/consumer closure
+ repair-specific positive obligations
+ applicable forbidden regressions
```

This is the focused repair/development verification profile.

It MUST NOT be confused with full SIB2/RC/release acceptance. A new exact candidate still runs whatever full profile is required for the maturity claim being made.

If affected-closure evidence is incomplete or contradictory, expose `AFFECTED_CLOSURE_UNTRUSTED` and widen verification or stop rather than under-test confidently.

---

# 8. RC7 MUST — semantic refit inside root-cause analysis

## Gap

Auto-repair must not assume production code is always the defective side. A failure may indicate stale code, stale docs, stale tests, deliberate semantic change or unresolved contradiction.

## Requirement

Repair diagnosis must reuse CodeSleuth contract triangulation / semantic-refit classifications such as:

```text
AGREE
CODE_AHEAD
DOC_AHEAD
TEST_AHEAD
CONTRADICTED
UNPROVEN
```

A Repair Case must identify which claim/authority is believed violated and why.

When current authorities disagree and deterministic evidence cannot establish the intended canon, the result is `OPERATOR_DECISION_REQUIRED`, not an automatic patch to whichever file is easiest.

Historical/stale work contributes semantic claims and rationale, not transferable acceptance.

---

# 9. RC7 MUST — regression witness and durable negative knowledge promotion

## Gap

The current auto-repair concept repairs a failure and reruns gates, but EBCA requires reproduced/repaired failures to become durable preservation knowledge when accepted.

## Requirement

A repair lineage should normally be:

```text
failed subject/evidence
    -> diagnosed defect
    -> repair delta
    -> regression witness
    -> new candidate
    -> fresh acceptance
```

`RepairPacketV1` must carry required regression-witness obligations where applicable.

After successful fresh acceptance, CodeSleuth should produce a candidate preservation update linking:

```text
contract/capability
negative state
regression witness
repair lineage
accepted candidate
```

Promotion into a protected/forbidden-regression authority still follows project authority and human/adjudicated policy. CodeSleuth may propose the negative obligation automatically; it may not silently rewrite project canon.

The full generic Negative Claim / Forbidden Inference subsystem remains post-RC7 under the existing Context Epistemics roadmap.

---

# 10. RC7 MUST — postcondition verification after host mutation

## Gap

Host output such as “fixed”, a successful patch command, or exit code 0 is not authority for the resulting repository state.

## Requirement

After every material repair mutation, re-observe:

```text
actual changed paths
diff / worktree state
scope-guard result
new commit SHA if committed
required new/changed test witness
focused gate results
```

The resulting state becomes a new candidate only after re-observation.

No EHA campaign may be launched for a candidate identity inferred only from host prose.

This is the RC7 repair-specific adoption of the broader postcondition-verification doctrine already described by ROAD/ROAP.

---

# 11. RC7 MUST — assumptions, limitations and residual uncertainty

## Gap

Repair/EHA outputs can become falsely definitive if they preserve evidence but drop the assumptions/limitations that made the evidence valid.

## Requirement

`ProjectSibProfile`, claim envelopes, Repair Cases, Repair Packets and EHA reports must have a way to preserve material:

```text
assumptions[]
limitations[]
residualUncertainty[]
```

Examples:

- a third-party oracle is assumed correct;
- a live environment was unavailable;
- a dependency graph may be incomplete;
- only Linux was in the accepted profile;
- a negative/absence claim used a bounded search universe.

Renderers may summarize these fields but must not silently omit material uncertainty.

---

# 12. RC7 MUST — traceability trust guard

## Gap

Affected closure and repair scope depend on traceability. EBCA explicitly warns that a graph selects correctly only if dependency/trace records are complete enough.

## Requirement

RC7 does not need a perfect global traceability auditor, but it needs a fail-closed trust marker for closure calculations.

A change-surface/affected-closure result should expose evidence such as:

```text
traceability sources used
known missing registry relations
pre-registry inference status
coverage/truncation
closureTrust = TRUSTWORTHY | DEGRADED | UNTRUSTED
```

An `UNTRUSTED` affected closure cannot justify a narrow verification set by itself.

A deeper bidirectional traceability-completeness audit is POST-RC7.

---

# 13. RC7 MUST — cross-ledger repair lineage

## Gap

RC7 intentionally preserves separate authorities for findings, implementation history and EHA. Without stable cross-references, however, a repair can become difficult to reconstruct.

## Requirement

Domain ledgers remain separate but must be linkable through stable IDs:

```text
finding / failed gate
    -> RepairCase
    -> RepairPacket
    -> implementation event(s)
    -> repair commit / candidate SHA
    -> regression witness
    -> EHA campaign/verdict
```

Cross-references do not merge authorities. They provide traceability across them.

Derived Markdown/Graphify/Mermaid should be able to render this lineage from the authoritative IDs.

---

# 14. RC7 MUST — typed packet + Jinja2 rendering boundary

The accepted rendering design is defined in [`RC7-REPAIR-PACKET-RENDERING.md`](RC7-REPAIR-PACKET-RENDERING.md).

Key requirements:

- validated typed data precedes rendering;
- Jinja2 is presentation/orchestration formatting only;
- host/project templates are customizable without changing repair semantics;
- `StrictUndefined` or equivalent fail-closed rendering;
- template/packet digests recorded in derived render provenance;
- untrusted repository excerpts are structurally delimited as data;
- cross-host semantic parity tests;
- no policy/authority decision exists only inside a template.

---

# 15. RC7 MUST — conservative terminology in machine output

## Gap

Once CodeSleuth generates generic EHA/repair reports for arbitrary projects, casual use of `proof`, `trusted`, `validated`, `attested`, or `reproducible` can overstate what happened.

## Requirement

RC7 report/render tests must enforce EBCA vocabulary where material:

- acceptance -> `accepted under profile <id>` for exact subject;
- verification -> contract/oracle named;
- validation -> intended-use/environment evidence only;
- `trusted` avoided unless trust boundary stated;
- plain provenance metadata never called attestation;
- rerunnable checks never called reproducible builds unless the declared reproducibility criterion is actually satisfied.

This is a documentation/rendering contract, not a new runtime subsystem.

---

# 16. RC7 acceptance additions implied by this audit

RC7 acceptance should add adversarial fixtures for at least:

1. required EHA evidence unavailable -> `UNAVAILABLE`, never PASS;
2. code/docs/tests conflict -> `OPERATOR_DECISION_REQUIRED`;
3. capability discovery with hidden truncation -> no SIB0 completeness claim;
4. same SHA with changed acceptance profile digest -> previous PASS not claimable under new profile;
5. same source SHA with materially different environment/tool identity -> profile semantics preserved;
6. stale Repair Packet blob ref after host/repo drift -> mutation blocked/revalidation required;
7. host reports repair success but worktree unchanged -> no new candidate;
8. repair changes an undeclared adjacent path -> scope stop;
9. affected closure marked untrusted -> narrow gate cannot be treated as sufficient;
10. reproduced defect repaired without regression witness -> repair completion rejected where witness is required;
11. accepted repaired defect emits candidate negative preservation obligation without silently modifying project canon;
12. cross-ledger lineage can reconstruct failed gate -> repair -> candidate -> fresh EHA;
13. Cursor/Codex/OpenCode Jinja renderings preserve the same material Repair Packet semantics;
14. malicious repository text containing prompt-like instructions remains quoted evidence, not host policy;
15. `NOT_APPLICABLE` requires explicit profile rationale;
16. assumptions/limitations survive NDJSON -> Markdown -> graph/Mermaid projections where declared by the domain.

---

# 17. POST-RC7 — full Context Epistemics / durable Negative Claims

The existing [`ROAD/ROADMAP.md`](ROAD/ROADMAP.md) already designs the larger system and should remain the primary future plan rather than being duplicated into RC7.

Post-RC7 work includes:

- canonical epistemic states beyond the minimum EHA result set;
- durable generic Negative Claim schema/ledger;
- `FORBIDDEN_INFERENCE` relations;
- negative-knowledge retrieval;
- epistemic-status triangulation;
- negative-edge context graph;
- retrieval policy mixing positive/negative/authority/risk/freshness relevance.

RC7 should create compatible hooks and IDs, not implement the whole subsystem.

---

# 18. POST-RC7 — risk classes and mutation evidence gates

Retain the ROAD design for:

```text
R0 read-only
R1 reversible local mutation
R2 shared-state mutation
R3 destructive/production mutation
```

and structured mutation preflight / fail-closed tool integration.

RC7 auto-repair needs repair-specific scope/authority/postcondition guards, but it should not become the universal destructive-action policy engine in the same release.

---

# 19. POST-RC7 — structured assurance-case projection

EBCA identifies a useful future read model inspired by assurance-case practice / OMG SACM.

A future projection may explicitly connect:

```text
claim
argument/reasoning
assumptions/context
supporting evidence
counter-evidence
limitations
```

It must remain a derived read model over existing authorities, not a new write authority.

This is a strong candidate for a post-RC7 Graphify/Markdown/Mermaid projection because RC7 will already provide typed claims and cross-ledger lineage.

---

# 20. POST-RC7 — independent assurance

A model verifying its own patch is useful but not independent assurance.

Future high-assurance workflows should support explicit producer/verifier separation, for example:

```text
repair producer host/model
        ↓
independent verification session/model/agent
        ↓
canonical acceptance profile
```

Hosted CI provides machine/environment separation, not automatically organizational or reviewer independence.

This should be modeled honestly rather than assigning a decorative “independent” badge.

---

# 21. POST-RC7 — bidirectional traceability completeness audit

RC7 adds a closure-trust guard. A later capability should audit traceability more deeply across:

```text
requirements/contracts
architecture/design
code
verification/tests
findings/non-conformances
repair/change lineage
```

It should find orphan contracts, untraced tests/code, missing reverse dependencies and closure blind spots.

Graph existence is not enough; completeness itself is an assurance claim.

---

# 22. POST-RC7 — authenticated provenance and attestations

Future assurance strengthening may add support for externally established schemes such as SLSA/in-toto-compatible source/build provenance or other signed/tamper-resistant attestations.

Requirements:

- preserve the distinction between attribution watermark and authenticated provenance;
- verify scheme identity and signatures/authenticity where claimed;
- never widen the property scope merely because provenance is signed;
- keep existing local evidence authority semantics unless an explicit architecture migration changes them.

---

# 23. POST-RC7 — reproducible-build evidence

Where projects build artifacts, future profiles may define a genuine reproducibility criterion.

Do not equate rerunning tests or deterministic Markdown generation with a reproducible build.

A reproducible-build claim should identify source, build instructions, environment and artifact comparison criterion, with bit-for-bit identity when using the established Reproducible Builds meaning.

---

# 24. POST-RC7 — promotion-ref governance

Generic EHA should understand project promotion refs, but enforcing repository governance/rulesets is a distinct future hardening layer.

Potential checks:

- required reviews;
- required status checks;
- strict/up-to-date/merge-queue policy;
- force-push/deletion restrictions;
- explicit bypass rules;
- tag/release immutability controls.

These strengthen control-plane integrity. They do not replace exact-subject acceptance.

---

# 25. POST-RC7 — remote operator assurance

Continue the existing ROAP direction for disconnected/live-host work:

- external mutation accounting;
- independent anchors;
- service/runtime post-state observation;
- residual uncertainty;
- remote recovery discipline.

RC7 `ExternalEvidenceManifestV1` and repair postcondition verification are compatible prerequisites, not replacements for the broader ROAP capability.

---

# 26. POST-RC7 — code-generator grounding and long-context degradation suites

Retain the existing ROAD plans for adversarial coding-agent tests involving:

- misleading stale facts;
- repeated historical accepted SHAs;
- distant negative claims;
- conflicting summaries/freshness;
- tempting but forbidden inference paths;
- risky mutations under incomplete evidence.

Metrics should include authority-selection accuracy, preservation of UNKNOWN/uncertainty and forbidden-inference compliance, not merely final-answer correctness.

---

# 27. POST-RC7 — assurance-strength read model

EBCA's L0-L8 assurance-strength ladder is useful, but RC7 should not pretend to implement all levels.

A later read model may classify the actual achieved assurance characteristics, for example:

```text
source-bound evidence
executable verification
profile acceptance
independent corroboration
authenticated provenance
structured assurance case
formal verification
```

It must report achieved properties, not award a single misleading scalar confidence score.

---

# 28. Scope conclusion

RC7 should operationalize the EBCA concepts that are necessary for **evidence-bound development and maturity convergence**:

```text
typed claims
+ exact acceptance-profile identity
+ non-binary outcomes
+ completeness/freshness limits
+ semantic reconciliation
+ bounded obligation reopening
+ repair packets
+ regression witnesses
+ postcondition verification
+ cross-ledger lineage
+ projection/render parity
```

Post-RC7 should build the broader **assurance and epistemic-control platform**:

```text
durable generic negative knowledge
+ forbidden inference
+ risk-gated mutation
+ independent assurance
+ traceability completeness audit
+ authenticated provenance
+ reproducible builds
+ assurance cases
+ long-context/grounding benchmarks
+ promotion governance
+ remote operator assurance
```

This boundary keeps RC7 coherent: it can learn to discover project maturity rules, run SIB0/SIB1/SIB2 EHA loops, diagnose and repair failures through host agents, and preserve what it learned without simultaneously becoming a supply-chain attestation platform, universal production safety controller and formal-methods laboratory.
