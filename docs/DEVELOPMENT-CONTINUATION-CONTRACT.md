# Development Continuation Contract

Status: **NORMATIVE RC6 PRODUCT CONTRACT**

This document defines the CodeSleuth contract for evidence-bound continuation of development in an unfamiliar or mature repository. It governs the RC6 Development Authority Map, pre-registry change-surface derivation, Development Continuation Packet, scope guard, Native Gate Map, brownfield contract adoption, and ExternalEvidenceManifestV1.

The central rule is simple: **CodeSleuth may discover and bind repository evidence, but it may not manufacture project authority.** A model's confidence, a plausible filename, a recent timestamp, or a coherent story is never enough to decide what the repository authorizes next.

## 1. Exact target first

Every continuation analysis is bound to one literal repository SHA. Repository claims, authority edges, change-surface evidence, native gates, brownfield contract candidates, and external evidence records must identify that target.

If tracked evidence changes while the claimed SHA does not, the affected claim is invalid. Exact-head identity is therefore a content/evidence boundary, not decorative metadata.

## 2. Development Authority Map

The Development Authority Map records evidence-bound relationships among planning, architecture, session, handoff, acceptance, and historical documents.

Supported relationship classes are semantically distinct:

- `CANONICAL_PLANNING_AUTHORITY` — the repository's declared planning source of truth for the relevant scope.
- `ACTIVE_IMPLEMENTATION_SCOPE` — the currently admissible implementation packet, track, milestone, session, or bounded work item.
- `NORMATIVE_ARCHITECTURE` — accepted architecture/ADR authority relevant to the active scope.
- `ACCEPTANCE_AUTHORITY` — repository-owned Definition of Done, gate, verification, or acceptance source.
- `ACCEPTED_PREDECESSOR` — an accepted prior packet/handoff whose completion is a prerequisite.
- `SUPPORTING_EVIDENCE` — current-state or analytical material that informs work but does not define the plan.
- `SUPERSEDES` / `SUPERSEDED_BY` — explicit replacement relationships.
- `HISTORICAL_ARCHIVE` — retained history that is not current instruction.
- `ADJACENT_PARALLEL_TRACK` — legitimate work that exists beside, but not inside, the active scope.
- `FORBIDDEN_COMPETING_AUTHORITY` — a source explicitly barred from acting as a parallel roadmap or authority.

### Authority evidence

A confirmed authority edge must carry exact tracked evidence. Discovery hints may come from filenames, directory layout, timestamps, headings, or model interpretation, but those hints remain non-authoritative until supported by repository text or another accepted repository-owned authority.

`confidence` is therefore discovery metadata. It is never authority.

### Direction and self-reference

Continuation relations are directional claims, not unordered labels. When a relation is used to authorize a continuation packet, the following endpoint semantics apply:

```text
CANONICAL_PLANNING_AUTHORITY
    repository/context subject -> planning-authority object

ACTIVE_IMPLEMENTATION_SCOPE
    selected planning-authority subject -> active-scope object

ACCEPTED_PREDECESSOR
    selected active-scope subject -> accepted-predecessor object
```

A matching relation name and object are insufficient when the subject is wrong. Packet creation fails closed when a selected authority edge does not have the required direction.

Confirmed semantic relations that are inherently irreflexive must not be self-loops. In particular, `ACTIVE_IMPLEMENTATION_SCOPE`, `ACCEPTED_PREDECESSOR`, `SUPERSEDES`, `SUPERSEDED_BY`, `HISTORICAL_ARCHIVE`, `ADJACENT_PARALLEL_TRACK`, and `FORBIDDEN_COMPETING_AUTHORITY` reject `subject == object` after repository-entity normalization. A self-referential edge is evidence of invalid authority construction, not a harmless graph curiosity.

`development_authority_state_load` fails closed on contradictory confirmed roles and records `AUTHORITY CONTRADICTION LATCHED` for the exact target SHA. `development_authority_state_start` must not mint a replacement map while that latch is active. A successor map requires recorded `operatorAdjudication.decision = SUPERSEDE_CONTRADICTION`. Failed maps remain evidence; they do not become an implicit license to start a cleaner map.

## 3. Pre-registry change surface

A repository may not yet have `docs/protected-capabilities.json`. CodeSleuth must still be able to navigate likely impact without pretending that an inferred dependency map is a protected registry.

The **pre-registry change surface** is a deterministic, bounded, non-authoritative map derived from tracked repository evidence such as:

- language/package/workspace manifests;
- module/import ownership;
- migrations and schemas;
- API, protocol, DTO, or interface definitions;
- CI and verification scripts;
- tests that reference the affected surfaces;
- documentation ownership links;
- explicit allowed-path or session ownership declarations.

Every derived surface item binds the tracked evidence used to derive it. The map may guide review, contract archaeology, and scope checking. It must not invent lifecycle maturity, protected status, compatibility obligations, or positive mutation authority.

A derived change surface can explain why another path deserves investigation. It never expands `allowedPaths` and never converts an undeclared path into an authorized mutation surface.

`save_packet` must not infer `pathScopeAuthority = DECLARED` from a non-empty `allowedPaths` array. Positive mutation allowlists require an explicit `pathScopeAuthority = DECLARED` argument. Copying exact change-surface seeds or entries into `allowedPaths` fails closed as path-scope fabrication.

## 4. Development Continuation Packet

A Development Continuation Packet is a bounded navigation artifact for one exact target and one confirmed active scope. It is not a new roadmap.

A packet must include, directly or through bounded resolved projections:

- exact target SHA;
- selected canonical planning authority;
- active objective/scope;
- prerequisites and `ACCEPTED_PREDECESSOR` evidence;
- required reading when declared;
- allowed/owned paths when declared;
- restricted or forbidden paths;
- adjacent tracks;
- unresolved blockers;
- pre-registry change surface when no protected registry exists;
- `authorityEvidence` — bounded resolved evidence for the authority relationships on which the packet relies;
- `nativeGates` — bounded resolved project-native verification/acceptance gates;
- durable Step-isolation events relevant to the exact target;
- an explicit distinction between directly declared facts and derived navigation.

Internal durable state may reference `authorityEdgeIds`, `nativeGateMapId`, `isolationEventIds`, or equivalent identifiers, but packet load/output must expose bounded `authorityEvidence`, `nativeGates`, and referenced isolation events. A consumer must not have to trust an opaque identifier to know why the scope, gate, or isolation claim exists.

A packet cannot be created as authoritative continuation state unless both `CANONICAL_PLANNING_AUTHORITY` and `ACTIVE_IMPLEMENTATION_SCOPE` are confirmed.

### Monotonic same-scope retries

A retry on the same exact target SHA and the same normalized active scope must not erase knowledge that has already been bound merely to make formal validation succeed.

The following previously bound obligations are monotonic across such retries:

- planning-authority references and authority edge ids needed by preserved claims;
- prerequisites;
- accepted predecessors;
- required reading;
- forbidden/adjacent restrictions;
- repository-provable, hosted-CI, and live-runtime gate obligations;
- operator-decision obligations;
- blockers;
- uncertainties.

Omitting one of these fields in a later save request does not remove the prior obligation. Replacing or retiring an obligation requires a different accepted authority/scope decision rather than omission from a retry payload.

Positive `allowedPaths` are deliberately different. CodeSleuth must never union old and new allowlists automatically, because automatic accumulation would expand mutation authority. A retry may narrow the declared positive path set; an empty set becomes `pathScopeAuthority = NOT_DECLARED` and therefore fails closed for positive scope claims. A non-empty `allowedPaths` array without explicit `pathScopeAuthority = DECLARED` is not a declared allowlist.

## 5. Scope guard

The scope guard compares a proposed or actual change against the confirmed continuation packet. It is deterministic and may classify paths as:

- `IN_SCOPE`
- `UNDECLARED`
- `ADJACENT_TRACK`
- `FORBIDDEN_BY_ACTIVE_SCOPE`
- `SCOPE_AUTHORITY_UNPROVEN`

Restricted/forbidden and adjacent classifications take precedence over optimistic inclusion.

The scope guard **never auto-expands scope** because an implementation appears to need another file. If the work genuinely must grow, the authority packet must be changed through explicit repository/user authority first.

Path patterns are repository path expressions, not conceptual work labels. Traversal/absolute-path forms and conceptual prose that cannot denote a repository path fail closed rather than becoming mutation authority.

A declared pattern ending in `/` denotes a directory boundary and includes descendants. An ordinary file literal remains exact. Explicit glob syntax remains deterministic. Thus `docs/baseline/` may authorize `docs/baseline/hybrid-retrieval.json`, while `src/lib.rs` does not authorize unrelated files under `src/`.

## 6. Native Gate Map

CodeSleuth records target-owned verification and acceptance requirements rather than replacing them with a generic green badge.

Every native gate is classified by where its proof can honestly be obtained:

- `REPO_PROVABLE` — deterministic proof available from the repository checkout itself.
- `HOSTED_CI_PROVABLE` — proof available on ordinary hosted CI infrastructure.
- `SERVICE_DEPENDENT_REPRODUCIBLE` — proof requires reproducible services/containers but not a privileged live deployment.
- `LIVE_RUNTIME_REQUIRED` — proof requires the actual runtime, deployment, credentials, topology, or persistent service state.
- `OPERATOR_DECISION_REQUIRED` — acceptance depends on an explicit human/operator judgment rather than an executable oracle.

### Cloud-testability boundary

The handoff state is fail-closed:

```text
any required REPO_PROVABLE or HOSTED_CI_PROVABLE gate not PASS
    -> CLOUD_TESTABILITY_REMAINING

all required REPO_PROVABLE and HOSTED_CI_PROVABLE gates PASS
    -> LIVE_HANDOFF_READY
```

`LIVE_HANDOFF_READY` does not mean the release is accepted. It means cloud-testable work is exhausted and remaining proof is legitimately live/service/operator dependent.

Live dogfood begins only after that boundary. It must never be used to compensate for a repository-testable defect.

## 7. Step isolation and fallback ordering

A Playbook Step marked `fresh_subagent` claims an execution property, not a writing style. If the host cannot prove that the fresh child was materialized, the orchestration boundary must durably append `STEP_ISOLATION_UNPROVEN` for the exact target SHA and Step id **before** any same-session fallback executes that Step.

The required order is:

```text
fresh child attempt
    -> isolation cannot be proven
    -> development_continuation_state_record_isolation_unproven
    -> durable event id returned
    -> only then same-session fallback may begin
```

The final continuation packet binds matching exact-target isolation event ids, and packet load exposes the resolved events. Final prose must derive the isolation status from those durable records. A controller may not execute fallback first and reconstruct a cleaner ordering later in the report.

`STEP_ISOLATION_UNPROVEN` does not necessarily prohibit all useful read-only analysis, but it prohibits any claim that the affected Step actually ran in a fresh isolated context.

## 8. Brownfield contract archaeology and adoption

A registryless repository may have real contracts distributed across implementation, normative/public documentation, and executable tests. CodeSleuth may discover candidates and triangulate them, but discovery confidence is not contract authority.

Candidate statuses retain the existing triangulation vocabulary, including `AGREE`, `UNPROVEN`, and drift/contradiction states.

Adoption is explicitly bounded:

- an `AGREE` candidate may be explicitly adopted with initial lifecycle no stronger than `implemented`;
- an `UNPROVEN` candidate requires a distinct explicit `adopt_unproven` decision and may be materialized no stronger than `experimental`;
- contradicted/drifting evidence cannot be silently adopted;
- discovery never auto-promotes any candidate to `PROTECTED`;
- a foreign/generic repository never inherits CodeSleuth SIB0/SIB1/SIB2 history or maturity claims.

Human/user adjudication occurs outside isolated analytical Playbook Steps. The analyst proposes; the owner decides what becomes canon.

## 9. ExternalEvidenceManifestV1

Live or service-dependent observations use `ExternalEvidenceManifestV1` so runtime truth can be consumed without masquerading as repository authority.

The manifest is append-only and binds at least:

- exact target repository SHA;
- source/adapter identity;
- observation time;
- freshness / TTL semantics;
- sanitized command, endpoint, or native-check identity;
- structured observation/result;
- evidence locator where applicable.

Freshness is explicit. Expired evidence remains visible as stale rather than disappearing or being silently reused as current truth.

An external observation is non-authoritative for repository contracts by itself. It may prove runtime state, but it cannot rewrite the Development Authority Map, protected registry, or planning authority merely because the live system disagrees.

`PASS` / `FAIL` may be recorded only when the underlying native check itself defines those outcomes. Otherwise the evidence remains an observation or `UNKNOWN`.

Raw credentials, private keys, obvious tokens, or equivalent secrets must be rejected before persistence.

## 10. Authority hierarchy

For RC6 continuation work, use this hierarchy:

```text
exact tracked repository evidence
    -> confirmed Development Authority Map
    -> bounded Development Continuation Packet
    -> deterministic scope guard + Native Gate Map
    -> repository/hosted proof
    -> LIVE_HANDOFF_READY
    -> live dogfood / ExternalEvidenceManifestV1
```

External runtime evidence may refine knowledge of runtime truth. It does not travel backward through that chain and create repository authority.

## 11. Non-goals

RC6 does not add:

- a new primary coding agent;
- an autonomous project manager;
- a generic replacement for target-native tests/gates;
- automatic roadmap generation;
- automatic protected-contract promotion;
- PII Parser-specific or Aleph-specific adapters in the CodeSleuth core.

The point of RC6 is not to tell a project what it should value. It is to recover what the project itself says is authoritative, expose contradictions and missing proof, keep implementation inside the admissible scope, and stop at the precise point where live evidence is actually required.
