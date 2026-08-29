# Evidence-Based Code Analysis: Canonical Thesaurus and Assurance Vocabulary

**Working name:** Evidence-Based Code Analysis (EBCA)  
**Russian working name:** «Доказательный анализ кода»  
**Status:** vocabulary hardening / engineering doctrine  
**Scope:** CodeSleuth analysis, review, integration, acceptance, provenance, graph consumption, release construction, and future tooling

## 1. Purpose

CodeSleuth uses a deliberately strict engineering vocabulary for reasoning about source code, changes, evidence, acceptance, and preservation. The goal is not to invent impressive names for ordinary software engineering. The goal is to prevent materially different concepts from collapsing into convenient but ambiguous words such as *green*, *stable*, *verified*, *trusted*, *proof*, or *done*.

Evidence-Based Code Analysis (EBCA) is the project name for this discipline:

> **A material code claim is valid only within an explicit subject identity, authority boundary, scope, assumptions, and evidence set.**

EBCA is not an industry-standard name and CodeSleuth does not claim ownership of the underlying engineering ideas. Its vocabulary intentionally combines established practices from software configuration management, verification and validation, requirements traceability, change-impact analysis, software assurance, structured assurance cases, software supply-chain provenance, and reproducible-build practice.

The distinctive CodeSleuth contribution is the composition of those ideas into one operational rule set suitable for repository analysis by humans and coding agents:

```text
exact identity
    + authority
    + bounded claim
    + explicit evidence
    + freshness
    + change lineage
    = claimable engineering conclusion
```

This document is a **thesaurus and semantic contract**, not a new persistence authority, controller, or acceptance ledger. Existing normative contracts remain authoritative for their concrete mechanisms. When wording differs, this document should be used to interpret terms conservatively and to identify where a future explicit contract clarification is required.

---

## 2. Core axioms

### Axiom 1 — Identity before claim

A material claim must identify the subject it is about before evidence can support it.

For Git-managed source, the strongest ordinary subject identity is an exact immutable revision identifier, normally a full commit SHA, plus more specific blob/tree identities where the claim concerns individual content.

A movable branch name is navigation, not immutable identity.

### Axiom 2 — Authority precedes representation

Every material fact must have an identified authority. A derived representation does not become authoritative merely because it is easier to read, query, render, search, or feed to a model.

```text
source authority -> derived state -> bounded context -> presentation
```

The direction does not reverse by convenience.

### Axiom 3 — Evidence supports a claim; evidence is not the claim

A test result, source excerpt, trace, report, graph, attestation, or human review note is evidence only relative to a stated claim.

The same artifact can be strong evidence for one claim and irrelevant evidence for another.

### Axiom 4 — Acceptance is scoped

Acceptance never means “correct in every possible sense.” It means that a named subject satisfied a named acceptance profile within the profile's declared environments and obligations.

### Axiom 5 — Acceptance is configuration-specific

Acceptance evidence attaches to the exact tested configuration. It does not implicitly transfer to descendants, rebases, squashes, cherry-picks, divergent branches, tree-equivalent commits, or later working trees.

### Axiom 6 — Ancestry transfers context, not acceptance

A candidate descended from an accepted head begins from a known-good engineering context, but it is a new acceptance subject.

Ancestry narrows the review problem. It does not manufacture a new PASS.

### Axiom 7 — Change should reopen the smallest honest obligation set

Ordinary development should use traceability and impact analysis to determine which protected contracts a delta may affect. This allows bounded development gates without pretending that an affected-closure gate is equivalent to a full release/SIB2 acceptance profile.

### Axiom 8 — Negative knowledge is durable engineering knowledge

Once a concrete unacceptable state has been reproduced, repaired, attached to a contract, and accepted through the relevant process, “this must not happen again” becomes a preservation obligation.

A regression test is an executable witness for that obligation, not merely a historical bug souvenir.

### Axiom 9 — Unknown remains unknown

Missing, stale, ambiguous, corrupt, truncated, unverifiable, or conflicting evidence must remain visibly uncertain. Material ambiguity must not be silently converted into absence, success, or confidence.

### Axiom 10 — Retrieval is navigation, not semantic authority

Search, ranking, embeddings, graphs, BM25, grep, LLM summaries, and indexes may identify where to inspect. They do not create repository facts.

Material claims must be rehydrated from the proper exact authority.

### Axiom 11 — Reproducibility, provenance, and attestation strengthen evidence but do not widen its scope

A signed provenance record can make an artifact's origin harder to forge. A reproducible build can make a source-to-artifact relation independently checkable. Neither proves properties that were never tested or specified.

### Axiom 12 — Strong language requires strong evidence

Terms such as *proof*, *verified*, *validated*, *attested*, *reproducible*, *trusted*, and *accepted* have distinct meanings. Do not use a stronger term because it sounds convenient in a report.

---

## 3. The EBCA claim model

A defensible engineering conclusion can be modeled as:

```text
Claim {
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
}
```

No implementation is required to serialize every claim exactly this way. The model exists to prevent missing dimensions.

### Subject

The exact object about which the claim is made.

Examples:

- repository commit SHA;
- file blob SHA;
- protected contract ID;
- EHA campaign ID;
- build artifact digest;
- installed CodeSleuth version plus source identity.

### Property

The statement being evaluated.

Examples:

- “all SIB0 capability classes are represented”;
- “the update path restarts into the updated source”;
- “this finding reproduces at these exact lines”;
- “this artifact was built from this source revision”;
- “this candidate preserves FR-UPDATE-001.”

### Scope

The boundaries within which the claim is intended to hold.

Examples:

- specific paths;
- a protected capability closure;
- supported OS/Python matrix;
- a release acceptance profile;
- one repository/worktree;
- one renderer/runtime version.

### Assumptions

Conditions relied upon but not proved by the evidence set.

Examples:

- Git object integrity is trusted;
- the hosted runner reports its checked-out SHA honestly;
- a third-party dependency behaves according to its pinned release;
- a test oracle correctly represents the contract.

Assumptions should shrink as assurance requirements grow.

### Authority

The source that owns the underlying fact.

Examples:

- tracked Git source for current code content;
- `findings.ndjson` plus its amendment ledger for durable finding history;
- `eha.ndjson` for EHA campaign/verdict history;
- `docs/protected-capabilities.json` for protected-contract registry state.

### Evidence

Observed artifacts that support or contradict the property.

Examples:

- exact source ranges with blob identity;
- test results;
- workflow run and job records;
- static-analysis output;
- signed provenance;
- reproduced failure traces.

### Environment

Execution conditions material to the result.

Examples:

- OS;
- interpreter/runtime version;
- dependency lock identity;
- browser/Node identity for rendering;
- build platform identity.

### Result

At minimum:

- `PASS` — the required evidence supports the scoped claim;
- `FAIL` — required evidence contradicts or does not satisfy the claim;
- `INCONCLUSIVE` — evidence exists but is insufficient/conflicting;
- `UNAVAILABLE` — required evidence could not be produced or retrieved;
- `NOT_APPLICABLE` — the claim/profile does not apply, with explicit rationale.

Do not collapse `INCONCLUSIVE` or `UNAVAILABLE` into PASS.

---

## 4. Evidence vocabulary

### Observation

A recorded fact from an inspection or execution, before interpretation.

Examples:

- `git rev-parse HEAD` returned SHA `X`;
- a test process exited `1`;
- source line 42 contains a particular call;
- a workflow job reports `success`.

An observation can be wrong because the observer/tool can be wrong. It is still more precise than an unrecorded impression.

### Evidence

An observation or artifact used to support or contradict a claim.

Evidence is **claim-relative**. There is no context-free scalar called “amount of evidence.”

### Direct source evidence

Evidence taken from the authoritative current source/configuration itself, bound to exact identity.

Examples:

- current tracked source range + blob SHA;
- exact configuration file content + blob SHA;
- exact commit tree.

For claims about what code currently says or does structurally, this is normally stronger than remembered prose, graph edges, or report summaries.

### Executable verification evidence

Evidence produced by executing a check whose oracle corresponds to a contract or claim.

Examples:

- regression test;
- integration test;
- acceptance matrix;
- static checker with explicit rule;
- reproducible command with recorded inputs and result.

A passing test only supports the properties represented by its oracle and environment.

### Historical evidence

Evidence that was valid for an earlier subject state.

Historical evidence is useful provenance and regression context. It is not current exact-head acceptance for a different SHA.

### Derived evidence / derived view

A representation computed from authoritative state.

Examples:

- RepositoryContextProjection;
- generated INDEX;
- Mermaid view;
- Markdown report;
- export bundle;
- search index.

A derived view can be auditable and useful without becoming authority.

### Negative evidence

Evidence relevant to the absence of a state or behavior.

Examples:

- a regression test proving a previously reproduced failure no longer occurs under specified conditions;
- a structural rule proving no second persistence authority is present in a bounded architecture surface.

Absence claims require carefully bounded search/completeness assumptions. “I did not find it” is not automatically negative evidence.

### Regression witness

An executable or otherwise reproducible artifact that demonstrates a previously unacceptable state and then distinguishes the repaired state.

A good regression witness is:

- specific;
- deterministic enough for the contract;
- attached to the affected contract/finding;
- retained after repair;
- able to fail again if the forbidden state returns.

### Provenance

Information describing where a source revision or artifact came from and how it came to exist.

Within CodeSleuth, distinguish:

- **source provenance** — how a source revision was created/changed;
- **build/artifact provenance** — how an artifact was produced from inputs;
- **analysis provenance** — which review/session/tool produced analysis evidence;
- **attribution provenance** — declared producer/session attribution.

SLSA uses provenance for verifiable information tracing artifacts or source revisions through their creation process. CodeSleuth should use compatible meanings and avoid calling arbitrary metadata “provenance” when it cannot answer an origin question.

### Attribution watermark

The existing CodeSleuth provenance watermark is a deterministic attribution marker. It answers which declared actor/session authored or recorded work.

It is **not** a cryptographic signature, source-control attestation, authentication mechanism, or acceptance result.

### Attestation

A structured statement issued by an identified producer/authority about a subject and its properties, normally with integrity/authenticity protection appropriate to the assurance goal.

Examples include SLSA/in-toto-style provenance attestations.

Do not call unsigned local JSON an attestation merely because it contains a SHA. CodeSleuth may store evidence records without claiming attestation-level authenticity.

### Formal proof

A result derived within a formal system from explicit premises using mechanically or mathematically valid inference rules.

Ordinary unit/integration/acceptance testing is **not formal proof of program correctness**.

CodeSleuth documents historically use “prove/proven/proof obligation” in an engineering shorthand sense. The hardened interpretation is:

> **evidence-backed verification or acceptance within a declared profile, unless a formal method is explicitly named.**

Future documents SHOULD prefer `verification obligation`, `acceptance obligation`, `supported claim`, or `accepted evidence` when mathematical/formal proof is not intended.

### Verification

Evidence that specified requirements/contracts are satisfied by the implementation or artifact under evaluation.

Informally: **did we build the thing according to the specified contract?**

### Validation

Evidence that the requirements/behavior are appropriate for the intended use or user environment.

Informally: **is this the right thing for the intended purpose?**

Do not use verification and validation as synonyms. Code-level tests often verify implementation contracts; user/environment acceptance may contribute to validation.

### Assurance

The justified confidence that a system or property satisfies its intended requirements, based on evidence and reasoning.

Assurance is broader than test execution. It includes the quality, independence, traceability, relevance, and interpretation of evidence.

### Assurance case

A structured argument connecting claims to evidence through explicit reasoning and context.

OMG SACM and assurance-case practice separate **claims**, **argumentation**, **evidence/artifacts**, and **context**. CodeSleuth already has many of these ingredients but does not currently claim full SACM compliance or a formal assurance-case implementation.

A future CodeSleuth assurance-case view would be a useful read model if it remains subordinate to the existing source/evidence authorities.

---

## 5. Identity vocabulary

### Repository identity

The identity of the repository instance being analyzed, not merely its directory name.

Where material, record canonical remote/repository information together with the revision identity.

### Revision identity

An immutable source revision identifier. In Git this is normally a full commit object ID.

SLSA similarly treats a source revision as a specifically identifiable state, with Git commit object IDs as a canonical example.

### Branch

A named movable reference to a revision.

A branch is useful for workflow/navigation. It is not acceptance identity because it can move.

### Tag

A named reference usually intended to be more stable than a branch, but its trust depends on repository controls. A tag name alone does not replace the exact revision/object identity behind the claim.

### Tree identity

The identity of a Git tree object representing directory content.

Tree equality can show content equivalence at one layer. It does **not** imply equivalent source provenance, parentage, review process, commit metadata, or exact-head acceptance.

Therefore:

> **tree-equivalent != acceptance-equivalent**

### Blob identity

The identity of exact file content in Git.

Blob identity is strong evidence for source freshness at a specific file/content level.

### Worktree identity

The combination of checked-out revision plus relevant tracked/untracked/dirty state.

A clean exact commit and a dirty worktree are different analysis subjects when local modifications can affect the claim.

### Environment identity

The execution environment facts material to reproducibility or verification.

Examples: OS image, Python/Node/Bun/browser versions, dependency lock state, relevant environment variables.

### Tool identity

The exact tool/runtime version or digest whose behavior is material to the evidence.

A correctness-sensitive tool should not silently depend on whichever executable happens to be first on ambient `PATH` when an explicit identity can be required.

### Run identity

The identifier of a concrete execution that produced evidence, such as a GitHub Actions workflow run/job ID.

A run identity without exact subject SHA is insufficient for exact-head acceptance.

### Actor identity

The identity or declared attribution of the person/robot/session that produced a change or record.

Authentication strength must be stated honestly. A CodeSleuth watermark is declared attribution, not cryptographic identity proof.

---

## 6. Authority vocabulary

### Authority

The designated source that owns a class of truth for the engineering process.

Authority is semantic ownership, not merely storage location.

### Source authority

For current repository facts, tracked Git source plus exact object identity.

### Evidence authority

The canonical durable records that own review/acceptance history.

For current CodeSleuth this includes the domain-specific ledgers under `.opencode/state/reviews/**` according to their contracts.

### Registry authority

A tracked canonical registry that owns declared contract metadata, such as `docs/protected-capabilities.json` for protected capability records.

### Derived state

Rebuildable state computed from authorities for navigation, performance, or bounded consumption.

Deleting/rebuilding derived state must not destroy the underlying truth it represents.

### Projection

A bounded derived representation of a larger authority domain for a specific consumer purpose.

`RepositoryContextProjection` is the canonical CodeSleuth example.

### Read model

A consumer-oriented representation derived from authoritative state.

Reports, indexes, lifecycle summaries, graph selections, and assurance-case views can be read models without becoming write authorities.

### Presentation

Human-oriented derived rendering such as Mermaid or SVG.

Presentation cannot flow backward and redefine source/evidence identity.

### Ephemeral model context

LLM conversation/context used for reasoning. It is working memory, not durable authority.

After compaction/restart/staleness, material facts must be reloaded from authority.

### Publication artifact

A deliberately shared derived artifact, such as a report on the `reports` branch.

Publication increases reach, not authority.

### Export artifact

A retained derived copy produced by an explicit export operation.

An export manifest can accurately record provenance and hashes while still declaring `exportAuthority: none`.

### Authority inversion

A defect where a downstream derived representation starts deciding upstream truth.

Examples:

- edited Mermaid rewriting graph/evidence identity;
- report prose overriding EHA ledger state;
- retrieval score creating contract meaning;
- model memory replacing exact-source reopening.

Authority inversion is a forbidden architectural pattern unless an explicit architecture migration deliberately changes the owner of truth.

---

## 7. Baseline and acceptance vocabulary

### Baseline

An identified, agreed engineering state used as a controlled reference for change.

This aligns with classical software configuration management: a baseline provides a defined basis for managing and evaluating change.

### Capability class

A fundamental kind of ability the architecture is designed to possess, broader than a concrete feature/command/profile/adapter.

Capability classes define the architecture's shape.

### Feature population

Adding instances, depth, variants, operations, or UX inside an already accepted capability class without introducing a new fundamental authority/capability class.

### SIB0 — Stable Initialization Baseline

CodeSleuth project term for the exact state where the fundamental capability-class inventory and ownership/boundary model for an architectural generation are complete enough to freeze.

Closest established concepts include aspects of a controlled architecture/functional/allocated baseline, but SIB0 is not claimed to be identical to any one external baseline taxonomy.

### SIB1 — Stable Implementation Baseline

CodeSleuth project term for the exact state where every SIB0 capability class has a real basic implementation satisfying its own required contract.

There is no exact mainstream one-word equivalent. It resembles implementation/product-baseline maturity plus component-level verification, but SIB1 deliberately stops before proving full composition.

### SIB2 — Stable Integration Baseline

CodeSleuth project term for the smallest architecture-complete exact configuration where SIB1 implementations compose through intended end-to-end paths and the full canonical acceptance profile passes.

It is best understood as a **verified integrated configuration baseline**, not as a universal industry baseline category.

### Candidate

An exact state proposed for a claim or promotion but not yet carrying the required evidence for that claim.

### Accepted head

An exact commit for which the required acceptance profile succeeded and the result is recorded.

### Exact-Head Acceptance (EHA)

The rule that acceptance evidence belongs only to the exact revision on which the required acceptance profile executed.

Hardened definition:

> **Exact-head acceptance is configuration-specific evidence-backed acceptance: the tested revision identity and promoted revision identity must be identical.**

### Acceptance profile

The explicit set of gates, environments, obligations, and evidence requirements required for a particular claim.

A profile defines the scope/strength of PASS.

### Acceptance evidence

Recorded successful execution of an acceptance profile against an exact subject revision.

Minimum useful identity:

```text
exact subject SHA
+ profile identity
+ gates/environments
+ run/result identity
```

### Acceptance claim

The scoped conclusion supported by acceptance evidence.

Prefer this term over “proof” when no formal proof is involved.

### Claimability

Whether the available current evidence is sufficient to make a named engineering claim without overstating identity, scope, freshness, or authority.

A stale PASS can remain historical evidence while no longer being claimable for current HEAD.

### Promotion

Moving a workflow/reference state from candidate to an accepted role only after the required evidence exists for the exact promoted identity.

Moving a Git ref alone does not create acceptance.

### Reference protection / promotion control

Repository-enforced controls over mutable refs used for integration or promotion, such as required reviews, required status checks, up-to-date/merge-queue policy, force-push restrictions, deletion restrictions, and explicit bypass rules.

Reference protection strengthens **control-plane integrity**. It reduces accidental or unauthorized movement of `main`, `SIB`, release streams, or release tags, but it is not acceptance evidence and does not make a branch name authoritative over the exact commit it references.

> **protected ref != accepted revision**

A protected `SIB` ref is still only a controlled pointer. The accepted subject remains the exact SHA whose required EHA profile succeeded.

### Acceptance invalidation

The condition where previously valid evidence no longer supports the current claim subject, normally because subject identity, profile, environment requirements, or authoritative state changed.

Historical evidence is not erased. Its applicability changed.

### Acceptance non-transfer

The explicit rule that PASS does not automatically propagate across source-state identity changes.

```text
A accepted
A -> B

B inherits history/context from A.
B does not inherit A's exact-head PASS.
```

### Mergeability

A Git/platform property describing whether changes can be mechanically integrated without unresolved conflicts under the platform's merge rules.

`mergeable=true` is **not** acceptance evidence.

### Integratability / merge readiness

An engineering conclusion that a candidate is appropriate to merge because mechanical mergeability, contract preservation, candidate-specific verification, and required acceptance evidence are all satisfactory.

This is stronger than GitHub's `mergeable` flag.

---

## 8. Change lineage and preservation vocabulary

### Delta

The change between a known reference state and a candidate state.

EBCA prefers reasoning about exact deltas from a known accepted parent because that narrows the search space honestly.

### Known-good parent

An ancestor exact state with relevant accepted evidence.

The phrase is shorthand for “known-good under its recorded acceptance profile,” not universal correctness.

### Evidence inheritance context

The useful fact that a descendant starts from an ancestor whose properties were previously accepted, allowing review to focus on the delta and affected obligations.

This is **not acceptance inheritance**.

### Change-impact analysis

The process of determining which requirements/contracts/components/tests/consumers may be affected by a change.

This is established software-engineering practice and is central to post-SIB2 development.

### Traceability

Recorded relationships connecting requirements/contracts, design, code, tests, findings, and changes.

Bidirectional traceability supports both:

- forward reasoning: which implementation/tests realize this contract?;
- backward reasoning: which contract/reason justifies this code/test?

NASA software assurance explicitly emphasizes bidirectional traceability between requirements, design/code, verification, and non-conformances. EBCA's protected-capability graph is a project-specific operational form of the same general discipline.

### Affected closure

The bounded set of contracts/consumers reachable through declared dependency/impact relations from a candidate delta.

An affected closure selects development verification. It is not repository truth and can itself be incomplete; exact source may reveal missing relations that require registry correction.

### Invariant core

A small set of high-value checks always executed for ordinary development regardless of the calculated affected closure.

### Dependency-aware gate

```text
invariant core
+ affected contract closure
+ new/change-specific verification
```

Used to control ordinary development cost without weakening stronger SIB2/RC/release profiles.

### Protected capability

An accepted integrated capability whose contract and accepted behavior coverage are preservation obligations for later development.

### Protected contract

The explicit normative/public/architectural behavior associated with a protected capability, triangulated from code, docs, tests, and deliberate decisions.

### Invariant

A property intended to remain true across a defined class of allowed changes.

An invariant is stronger when it has explicit scope, authority, and executable/inspectable verification.

### Positive obligation

A property that must continue to hold.

Example: “update followed by restart executes the updated source.”

### Negative obligation / forbidden regression

A state that must not recur.

Example: “must not report update success while the running instance still uses the previous source.”

### Forbidden regression ledger

The contract-owned registry of negative obligations established from architecture decisions, accepted behavior, or reproduced/repaired failures.

### Contract fingerprint

A compact structural identity for aspects such as schema fields, public options, paths, environment variables, or authority values.

A fingerprint helps detect change. It does not autonomously interpret semantic compatibility.

### Semantic refit

The deliberate reconciliation of the **evidenced semantic surface** of stale or divergent work with current normative authority and current architecture. It recovers evidenced claims, assumptions, constraints, rationale, compatibility obligations, and negative knowledge, then decides what still belongs in the target and how it should be represented there.

Semantic refit does **not** assume that one metaphysical “true intent” can be recovered from historical work, and it is not a grander synonym for careful cherry-picking or porting.

### Repair lineage

The explicit historical relation:

```text
failed subject/evidence
    -> diagnosed defect
    -> repair delta
    -> regression witness
    -> new candidate
    -> fresh acceptance
```

Repair does not rewrite the old failure into success.

---

## 9. Analysis vocabulary

### Hypothesis

A proposition to investigate. It is not yet a finding.

### Candidate finding

A plausible issue with enough signal to investigate but not yet verified against the required current source/evidence.

### Verified finding

A material finding whose location, identity, reproduction/evidence, and reasoning have been validated sufficiently for the review contract.

“Verified” here means verified under the finding-recording contract, not formally proven universally true.

### Finding authority

The durable finding ledger and its amendment semantics, not report prose or model memory.

### Finding amendment

An append-only event that corrects metadata or changes lifecycle state without rewriting historical original evidence.

### Retraction

A finding lifecycle decision that the original material claim should no longer be treated as valid, while preserving the historical record that it was once made.

### Supersession

A lifecycle relation where a newer finding/record replaces the operational role of an older one while preserving lineage.

### Closure

A lifecycle decision that a finding has been addressed under specified verification evidence.

Closure is not equivalent to deleting the finding history.

### Reproduction

A controlled observation of the claimed failure/property under known subject/environment identity.

### Freshness

Whether evidence still corresponds to the current subject state required for the claim.

### Stale evidence

Evidence whose recorded identity no longer matches the current subject where exact-current applicability is required.

Stale evidence can remain historically valuable.

### Rehydration

Reloading exact authoritative records/source from durable authority after search, compaction, model memory, or derived context identified what to inspect.

### Source reopening

Re-reading the exact current tracked source before making a material code claim or edit based on derived context.

### Bounded analysis

Analysis with explicit scope/window/limits and visible truncation rather than pretending an unbounded exhaustive inspection occurred.

### Completeness claim

A claim that an inspection covered all relevant elements within a defined universe.

Completeness requires an enumerable/controlled universe or explicit method. Absence of discovered findings is not a completeness claim by default.

### Uncertainty

A first-class property of analysis describing incomplete knowledge, ambiguous evidence, uncertain inference, or unsupported extrapolation.

Good evidence systems preserve uncertainty rather than forcing binary confidence.

### Review inference

A derived analytical relation/hypothesis supported by review reasoning but not equivalent to direct verified source evidence.

Graph/provider inferred relations must remain visibly distinct from verified source relations.

---

## 10. Representation vocabulary

### Provider

A component that extracts candidate information from source or another input domain.

A provider does not automatically own canonical identity or authority.

### Normalization / adapter boundary

The layer that maps provider output into CodeSleuth's canonical contract after validation.

### RepositoryContextProjection

The bounded, derived, rebuildable CodeSleuth repository-context graph contract.

It is navigation/context state, not repository truth or finding evidence.

### Context capsule

A bounded exact-head model-facing projection containing structured SourceRefs, freshness state, selection/truncation information, and instructions to reopen source before material action.

### SourceRef

A structured reference linking derived context back to exact source identity/location.

### Mermaid

A human-readable derived diagram source. Mermaid is presentation, not machine authority or evidence.

### Report

A human/assistant-readable derived summary. Reports can carry exact provenance and useful conclusions but do not replace source/findings/EHA authorities.

### Index

A derived navigation structure over authoritative or retained data.

An index must not contain ghost records that imply underlying artifacts exist when they do not.

### Export bundle

A retained package of derived data/presentation created by an explicit export operation, ideally with manifest, hashes, provenance, selection/truncation metadata, and explicit non-authority declaration.

---

## 11. Crosswalk to established software-engineering practice

This table is conceptual. It is **not a compliance certification** for IEEE, NASA, NIST, SLSA, in-toto, OMG SACM, or any other external framework.

| CodeSleuth / EBCA concept | Closest established practice | Relationship / caution |
| --- | --- | --- |
| exact Git SHA as acceptance subject | configuration item/revision identification; SLSA source revision | Strong alignment: claims attach to an immutable revision rather than a branch name. |
| SIB0 | architecture/functional/allocated baseline ideas | Project-specific combination. Do not claim one-to-one equivalence with classical baseline taxonomies. |
| SIB1 | implementation/product baseline maturity + component verification | Project-specific stopping point before integrated-system acceptance. |
| SIB2 | verified integrated configuration/product baseline | Strong conceptual alignment with baselined product plus integration/acceptance evidence, but project-defined. |
| EHA | configuration-specific verification / verification summary tied to revision | Strong alignment with revision-bound verification. EHA is not a standard SLSA level or formal proof. |
| protected-capability registry | requirements/contract traceability + configuration control | Aligns with maintaining requirements-to-code/test traceability and impact analysis. |
| affected closure | change-impact analysis | Established idea; CodeSleuth uses a contract graph to operationalize it. |
| forbidden regression | defect/non-conformance traceability + regression verification | Project-specific ledger around established regression/change-control practice. |
| durable findings/EHA ledgers | configuration records / assurance evidence records | Similar objective: preserve auditable history. CodeSleuth remains local/text-native and domain-specific. |
| provenance watermark | attribution metadata | Weaker than authenticated/signed provenance. Must not be confused with SLSA/in-toto attestations. |
| hosted exact-head acceptance | independent/hosted verification execution | Strengthens reproducibility/independence but does not by itself provide signed supply-chain provenance. |
| reference protection / promotion control | protected branches/rulesets; source-control change management | Strengthens control of mutable promotion refs, but protected refs do not become acceptance identity. |
| Graphify/provider -> projection boundary | tool qualification / derived analysis model separation | Project-specific implementation of the general rule that tool output must be interpreted within defined authority/assurance boundaries. |
| Mermaid/report/export non-authority | assurance evidence vs presentation separation | Aligns with structured assurance cases where evidence artifacts and arguments are distinguished from presentations. |
| report lifecycle metadata | read-model traceability | Useful navigation, but authoritative lifecycle must remain in the structured evidence ledger. |
| regression witness | verification test linked to non-conformance/change | Strong alignment with traceability from defects/requirements to verification. |
| exact runtime identities | reproducibility / build-environment identification | Supports deterministic evidence. Full reproducible/hermetic builds require stronger controls than path pinning alone. |

### Where EBCA is already unusually strong

1. **Exact subject identity is central, not incidental.** Many teams say “CI passed on the PR” while losing track of the literal tested revision after rebases/squashes. EHA makes this ambiguity structurally unacceptable.
2. **Authority and presentation are explicitly separated.** Reports, Mermaid, retrieval, and LLM context are prevented from becoming accidental sources of truth.
3. **Negative obligations are first-class.** Repaired failures are retained as contract-owned forbidden regressions rather than disappearing into test history.
4. **Post-baseline development is change-impact-driven.** The baseline is used to reduce the honest proof/verification surface rather than forcing every engineer to mentally revalidate the whole architecture.
5. **Historical failure is immutable.** Repair lineage adds evidence; it does not edit old FAIL into PASS.

### Where world best practice can harden EBCA further

#### 1. Signed/tamper-resistant source and build provenance

SLSA Source/Build tracks go beyond recording SHAs and workflow IDs. Higher levels introduce contemporaneous provenance, hosted generation, signatures/authenticity verification, hardened build platforms, and stronger source-control change-management controls.

CodeSleuth should treat this as a future assurance-strengthening path, not claim equivalent protection today.

#### 2. Reproducible builds

The Reproducible Builds project defines reproducibility strictly: same source, build environment, and instructions produce bit-for-bit identical specified artifacts.

CodeSleuth should reserve **reproducible build** for that meaning. A rerunnable test or deterministic report is not automatically a reproducible build.

#### 3. Structured assurance cases

OMG SACM and assurance-case practice explicitly model claims, argumentation, evidence artifacts, and context. CodeSleuth already has claims, evidence, provenance, and read models; a future assurance-case projection could make the reasoning chain explicit without creating a new authority.

#### 4. Independent assurance

NASA software assurance emphasizes review/audit and, for higher assurance, organizational independence from the producer. A coding agent checking its own work is useful verification but should not be described as independent assurance.

Hosted CI provides execution independence from a developer workstation, not necessarily organizational/reviewer independence.

#### 5. Bidirectional traceability completeness

NASA and classical assurance practice expect traceability across requirements, design, code, verification, and non-conformances. CodeSleuth's protected-capability registry is a strong start, but completeness must be continuously audited. A graph can only select correct affected closure if its dependency/trace records are complete enough.

#### 6. Explicit threat models for “trusted” evidence

Supply-chain frameworks distinguish provenance existence from provenance authenticity and hardened production. EBCA should avoid the bare word `trusted` unless the trust assumptions and adversary model are stated.

#### 7. Enforced promotion-ref controls

GitHub protected branches/rulesets and OpenSSF source-control guidance add an operational layer that exact-SHA semantics alone do not provide: reviews and required checks can govern ref movement, force pushes/deletions can be constrained, and strict/up-to-date or merge-queue policies can reduce stale integration decisions.

This strengthens repository governance, not the logical scope of EHA. CodeSleuth should enforce such controls on promotion refs where practical while continuing to treat the exact tested SHA as the acceptance subject.

---

## 12. Terminology hardening decisions

### “Proof”

**Preferred:** use only for formal proof or clearly label `engineering proof` as shorthand.  
**Default replacement:** `evidence-backed acceptance`, `verification evidence`, `acceptance obligation`, `supported claim`.

### “Proven”

Allowed in informal historical text, but the precise interpretation is:

> supported by the named evidence/profile for the exact named subject and scope.

It must not imply mathematical completeness.

### “Verified”

Means checked against a specified contract/oracle. State what was verified and how.

Bad:

`the feature is verified`

Better:

`the update/restart contract is verified on exact SHA X by tests A/B under the hosted acceptance profile`

### “Validated”

Reserve for evidence that behavior/requirements are appropriate in the intended use/environment, not merely internally consistent with implementation tests.

### “Accepted”

Means the required acceptance profile passed for the exact subject and the evidence is current/claimable.

Never use `accepted branch` without naming the accepted exact revision.

### “Stable”

Must name the dimension:

- architecture-stable;
- implementation-stable;
- integration-accepted;
- release-stable;
- operationally stable.

SIB terms exist specifically because generic “stable” is too ambiguous.

### “Trusted”

Avoid unless the trust boundary and assumptions are named.

Prefer:

- `authoritative for X`;
- `accepted under profile Y`;
- `authenticated provenance`;
- `tamper-resistant attestation`;
- `verified source identity`.

### “Reproducible”

Use strictly for a defined process whose relevant inputs/environment/instructions can recreate the specified result according to the declared reproducibility criterion.

For builds, prefer the established bit-for-bit definition unless another criterion is explicitly named.

### “Attested”

Use for a structured assertion from an identified attesting authority/producer with the integrity/authenticity properties required by the attestation scheme.

A plain report is not automatically an attestation.

### “Evidence authority”

Means semantic ownership of evidence history, not “the file I happened to read.”

### “Derived”

Means reproducible/readable from upstream authority and non-authoritative for the underlying fact unless an explicit migration changes ownership.

---

## 13. Anti-terms and invalid shortcuts

The following phrases are insufficient as material engineering evidence unless expanded into exact identity, scope, and records.

### “CI is green”

Missing: which SHA, which workflow/profile, which jobs, which attempt, which environments.

### “This PR passed”

A PR is a moving workflow object. Name the exact tested head SHA.

### “The parent passed, so this is safe”

The parent provides a known-good base and narrows delta analysis. It does not accept the child.

### “It is only a docs/test/refactor change”

Classification does not prove non-impact. Map the actual delta to protected contracts.

### “GitHub says mergeable”

Mechanical conflict status, not product/contract acceptance.

### “The branch is protected, so it is accepted”

Ref protection controls who/how a mutable ref may move. It does not establish EHA evidence for the referenced commit.

### “The tree is identical”

Tree identity does not preserve commit provenance, parentage, review/attestation history, or EHA evidence.

### “The report says PASS”

A report is a derived read model. Rehydrate the authoritative structured acceptance record and exact source identity.

### “The graph says X depends on Y”

The graph is navigation/context. Reopen exact source/registry before material claims.

### “The model reviewed it”

Who/what model, which exact subject, which evidence, which coverage, which limitations? Model output is analysis, not self-authenticating evidence.

### “No issues found”

This means only that the performed bounded analysis produced no findings. It does not imply completeness unless completeness was a supported claim with an explicit search universe/method.

### “Same code, new SHA”

Potentially useful comparison evidence; never automatic acceptance transfer.

---

## 14. Minimal evidence-backed development loop

For ordinary post-SIB2 development:

```text
1. pin known accepted parent A
2. create candidate B = A + delta
3. identify exact B
4. map delta to protected contract seeds
5. compute/review affected closure
6. inspect exact current source for material impacts
7. add change-specific positive obligations
8. preserve applicable forbidden regressions
9. run invariant core + affected closure + new-feature tests
10. when promotion requires full acceptance, run the full profile on exact B
11. record exact evidence
12. promote only B, never an untested successor
```

After integration:

```text
accepted B
   -> becomes known-good parent/context for the next delta
```

The value of the baseline is not that future work becomes automatically safe. The value is that future verification can focus on **what changed and what that change can honestly affect**.

---

## 15. Assurance-strength ladder

The following ladder separates increasingly strong but non-equivalent statements.

```text
L0  assertion
    “I think property P holds.”

L1  observation
    “Tool/source observation O was recorded.”

L2  source-bound evidence
    “O is bound to exact source identity X.”

L3  executable verification
    “A defined oracle/check for P passed on X.”

L4  acceptance profile
    “All required checks/environments for scoped claim C passed on X.”

L5  independent/reproducible corroboration
    “A sufficiently independent party/process can reproduce/confirm the evidence.”

L6  authenticated/tamper-resistant provenance
    “The process/artifact evidence is cryptographically attributable and verified under a defined provenance scheme.”

L7  structured assurance case
    “Claims, assumptions, reasoning, counter-evidence, and supporting artifacts are explicitly linked and reviewable.”

L8  formal verification/proof where applicable
    “Specified properties are mechanically/mathematically proved under explicit formal assumptions.”
```

This is an EBCA explanatory ladder, not an external certification scheme. Higher levels do not automatically make a broader claim; they strengthen assurance for the properties actually represented.

CodeSleuth should state which rung(s) a particular workflow achieves rather than casually using the strongest vocabulary.

---

## 16. Canonical EBCA statements

> **Evidence-Based Code Analysis:** repository/code analysis in which every material conclusion is bound to explicit subject identity, authority, scope, evidence, freshness, and limitations.

> **Exact-head acceptance:** configuration-specific acceptance in which the exact tested revision identity and the revision promoted under the claim are identical.

> **SIB:** a project-specific sequence of controlled engineering baselines separating architectural freeze (SIB0), implementation completeness (SIB1), and integrated-system acceptance (SIB2).

> **Protected capability:** an accepted integrated capability whose contract and accepted positive/negative obligations must be preserved by later relevant changes unless explicitly superseded.

> **Forbidden regression:** a contract-owned negative acceptance obligation stating a concrete unacceptable state that must not recur.

> **Known-good parent:** an exact ancestor with relevant recorded acceptance evidence; it narrows descendant delta analysis but does not transfer its PASS.

> **Authority:** the source that semantically owns a class of truth; downstream projections, indexes, reports, diagrams, exports, and model context do not acquire that ownership by convenience.

> **Provenance:** verifiable origin/process information about how a source revision, artifact, or evidence record came to exist; attribution watermarks are a weaker, explicitly non-cryptographic subset of provenance metadata.

> **Verification:** evidence that a specified contract/property is satisfied under stated conditions.

> **Validation:** evidence that requirements/behavior are appropriate for intended use/environment.

> **Assurance:** justified confidence produced by relevant evidence plus explicit reasoning, assumptions, traceability, and appropriate independence.

The shortest operational rule is:

> **Name the exact thing. Name the exact claim. Read from the real authority. Show the evidence. State the limits. If the thing changes, prove the scoped claim again.**

---

## 17. External reference crosswalk

These sources inform the crosswalk above. Their terminology remains their own; inclusion here is not a claim of conformance.

### IEEE Computer Society — SWEBOK Guide V4.0

- https://www.computer.org/education/bodies-of-knowledge/software-engineering/resources/
- https://www.computer.org/education/bodies-of-knowledge/software-engineering/topics

Relevant areas include software requirements, verification/validation, maintenance and impact analysis, software configuration management, engineering management, architecture, operations, and security.

### NASA Software Engineering / Software Assurance Handbook

- Bidirectional traceability: https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052+-+Bidirectional+Traceability
- Requirements/change assurance: https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695435/SWE-053+-+Manage+Requirements+Changes
- Configuration management planning: https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695458/SWE-079+-+Develop+CM+Plan
- Configuration audits: https://swehb.nasa.gov/pages/viewpage.action?navigatingVersions=true&pageId=16453170
- Delivery verification/traceability: https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695529/SWE-194+-+Delivery+Requirements+Verification

NASA guidance is particularly relevant to traceability, independent assurance, configuration audits, and evidence that requirements/changes/defect resolutions were verified.

### NIST Secure Software Development Framework

- SSDF project: https://csrc.nist.gov/projects/ssdf
- NIST SP 800-218 v1.1: https://csrc.nist.gov/pubs/sp/800/218/final

SSDF reinforces disciplined, repeatable development practices, verification, vulnerability prevention, and root-cause/recurrence reduction.

### SLSA v1.2

- Specification: https://slsa.dev/spec/v1.2/
- Source requirements: https://slsa.dev/spec/v1.2/source-requirements
- Build track basics: https://slsa.dev/spec/v1.2/build-track-basics
- Provenance: https://slsa.dev/spec/v1.2/provenance
- Artifact verification: https://slsa.dev/spec/v1.2/verifying-artifacts

SLSA provides a strong external vocabulary for revision identity, source/build provenance, hosted/hardened build processes, verification of provenance, and source change-management controls.

### in-toto

- https://in-toto.io/docs/getting-started/

in-toto explicitly records supply-chain steps, materials/products, authorized functionaries, and link metadata so a verifier can check that the defined process was followed.

### Reproducible Builds

- https://reproducible-builds.org/docs/definition/

Use its strict definition when claiming a build is reproducible: the same source code, relevant build environment, and build instructions recreate bit-for-bit identical specified artifacts.

### OMG Structured Assurance Case Metamodel (SACM)

- https://www.omg.org/spec/SACM/About-SACM

SACM provides a standardized model for structured claims, argumentation, evidence/artifact references, context, counter-evidence, and assurance-case interchange.

---

## 18. Maintenance rule for this thesaurus

This vocabulary must evolve conservatively.

A new term should be added only when at least one of these is true:

1. two materially different concepts are being confused under one existing word;
2. a recurring workflow needs a stable name for a precise engineering state;
3. an external established term should replace a weaker project-local synonym;
4. a new architecture/assurance mechanism introduces a genuinely new semantic role.

Do not create terminology merely because a new tool exists.

When changing a definition:

- identify affected normative docs/tests/tools;
- classify whether the change is wording clarification or contract-semantic change;
- preserve historical meaning where evidence records depend on it;
- update cross-references deliberately;
- do not retroactively reinterpret old PASS/FAIL evidence beyond its original recorded profile.

The thesaurus itself is a controlled semantic baseline. It should reduce ambiguity, not become another source of ceremonial vocabulary.
