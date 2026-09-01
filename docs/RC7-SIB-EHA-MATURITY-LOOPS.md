# RC7 Addendum — Project-Portable SIB0/SIB1/SIB2 and EHA Maturity Loops

**Status:** ACCEPTED RC7 PLANNING INPUT  
**Parent:** `docs/RC7-FEATURE-PLAN.md`  
**Semantic authority:** `docs/EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`  
**Scope:** project-portable SIB0/SIB1/SIB2 discovery, adjudication, EHA execution, failure triage and evidence-bound auto-repair orchestration

This document is an accepted addendum to the RC7 feature plan. The formal RC7 design must incorporate it into the main RC7 scope authority before implementation begins.

## 1. Objective

RC7 must teach CodeSleuth to conduct SIB0/SIB1/SIB2 and EHA maturity loops on arbitrary software projects without importing CodeSleuth-specific capability inventory, gates, release topology or historical acceptance into those projects.

The three SIB meanings remain universal:

- **SIB0 — Stable Initialization Baseline:** the project's fundamental capability-class inventory and architectural ownership boundaries for one architecture generation are identified and frozen.
- **SIB1 — Stable Implementation Baseline:** every SIB0 capability class has a real basic implementation satisfying its declared contract.
- **SIB2 — Stable Integration Baseline:** those implementations are proven to work together through the project's canonical integration/system acceptance obligations.

Projects customize the evidence, inventory, contracts, environments, gates and promotion authority. They do not redefine SIB0/SIB1/SIB2 into unrelated maturity stages.

## 2. EBCA semantic binding

All generic SIB/EHA machinery MUST use the canonical Evidence-Based Code Analysis vocabulary and claim model.

A SIB or EHA conclusion is a material EBCA claim and is claimable only when it has:

```text
exact subject identity
+ authority boundary
+ bounded property/scope
+ explicit evidence
+ relevant environment identity
+ freshness
+ change lineage
= claimable engineering conclusion
```

The following EBCA rules are binding:

1. **Identity before claim.** A SIB/EHA verdict belongs to one exact candidate configuration, normally an immutable Git SHA plus more specific blob/tree/environment identities where material.
2. **Authority precedes representation.** Markdown, Mermaid, Graphify, search indexes, model summaries and reports are derived representations and cannot create acceptance authority.
3. **Evidence is claim-relative.** A green test supports only the obligations represented by its oracle, scope and environment.
4. **Acceptance is scoped.** PASS means the named exact subject satisfied the named acceptance profile within its declared obligations and environments, not that the project is universally correct.
5. **Acceptance is configuration-specific.** PASS does not transfer automatically to descendants, rebases, squashes, cherry-picks, tree-equivalent commits, later worktrees or another environment.
6. **Ancestry transfers context, not acceptance.** Prior accepted states may narrow the next review/repair problem but never manufacture a new PASS.
7. **Reopen the smallest honest obligation set.** Repair and ordinary development should use impact/traceability evidence to identify affected obligations, while full SIB2 claimability still requires its complete accepted profile.
8. **Negative knowledge is durable.** Reproduced and repaired failures become preservation obligations with retained regression witnesses where possible.
9. **Unknown remains unknown.** Missing, stale, ambiguous, conflicting, corrupt or unavailable evidence cannot be silently converted into PASS.
10. **Strong language requires strong evidence.** `PASS`, `verified`, `accepted`, `validated`, `trusted`, `attested` and `proof` retain their distinct EBCA meanings.

## 3. Project SIB profile discovery

For a repository without an accepted SIB profile, CodeSleuth must derive one as a proposal from project-owned evidence.

The discovery pipeline is:

```text
exact repository target
-> Development Authority Map
-> architecture/contract archaeology
-> code/docs/tests triangulation
-> capability-class candidates
-> capability contracts
-> Native Gate Map
-> release/candidate-selection evidence
-> proposed ProjectSibProfile
-> human adjudication
-> accepted ProjectSibProfile
```

Discovery may use filenames, graph topology, search, embeddings, model reasoning and historical documents as navigation. Material profile claims must be rehydrated from exact tracked authority.

### 3.1 Alternative interpretations

When evidence supports more than one plausible capability model, authority chain, acceptance boundary or gate mapping, CodeSleuth must show the alternatives rather than averaging them into one confident answer.

A proposal should be able to present, for example:

```text
Option A
- Persistence is one fundamental capability class.
- Review, EHA and implementation ledgers populate the same persistence class.

Option B
- Review evidence persistence and release-acceptance persistence are distinct fundamental classes.

Evidence for each option:
- exact tracked paths/blobs/locators
- supporting and contradictory tests/docs/code

Recommendation:
- selected option + rationale

Operator choices:
- adopt recommendation
- adopt alternate
- edit profile
- defer / keep UNPROVEN
```

Model confidence is advisory metadata. It is never project authority.

## 4. ProjectSibProfileV1

The accepted RC7 design must provide a project-local profile equivalent to `ProjectSibProfileV1`.

Minimum semantic content:

```text
profile identity / schema version
repository identity
architecture-generation identity
profile source/digest/blob identity

capability classes
capability contracts
architecture ownership/boundaries

SIB0 claims and acceptance obligations
SIB1 claims and acceptance obligations
SIB2 claims and acceptance obligations

native gates and their evidence locators
required environments
candidate-selection authority
integration/release-stream authority where declared
architecture-reopen conditions
repair/refit policy
promotion/adjudication authority
limitations / unresolved evidence
```

A profile revision creates a new acceptance profile identity. Old acceptance evidence does not silently attach to a materially changed profile.

## 5. Human adjudication boundary

CodeSleuth may discover, triangulate, rank and recommend a SIB profile. It may not manufacture project canon.

Explicit user/maintainer adjudication is required to:

- adopt a proposed capability-class inventory;
- choose among materially different authority interpretations;
- define or amend architecture-generation boundaries;
- accept project-specific SIB0/SIB1/SIB2 obligations;
- resolve code/docs/tests contradictions where evidence does not establish one current authority;
- promote a profile revision to accepted project policy.

A repository that already declares equivalent architecture/capability/acceptance authority may allow CodeSleuth to bind to that authority without creating a duplicate competing document.

## 6. Generic EHA engine

RC7 should generalize the existing EHA machinery rather than create per-project EHA implementations.

The generic engine owns only cross-project mechanics:

```text
exact candidate identity
campaign identity/lifecycle
profile identity
SIB level ordering
claim/evidence recording
verdict semantics
repair lineage
failed-subject immutability
campaign completion
```

The project profile supplies project meaning:

```text
capability inventory
contracts
SIB0 obligations
SIB1 obligations
SIB2 obligations
native gates
environments
candidate-selection rules
promotion authority
architecture-reopen policy
```

## 7. Cumulative SIB claimability

SIB maturity is cumulative on one exact acceptance subject.

A claimable SIB2 requires:

```text
ONE exact candidate/profile/environment subject
+ SIB0 PASS
+ SIB1 PASS
+ SIB2 PASS
+ durable campaign completion
```

The following is invalid:

```text
SHA A -> SIB0 PASS
SHA B -> SIB1 PASS
SHA C -> SIB2 PASS
therefore SHA C is SIB2
```

Historical PASS is useful context and may reduce the honest affected-obligation set during development. It does not transfer acceptance to a new exact subject.

## 8. EHA maturity loop

The generic loop is:

```text
accepted ProjectSibProfile
        |
        v
select literal candidate
        |
        v
freeze exact subject/environment
        |
        v
start durable campaign
        |
        v
SIB0 assessment
        |
        v
SIB1 assessment
        |
        v
SIB2 assessment
        |
        v
campaign_completed
```

Any failed required obligation enters the repair path. `INCONCLUSIVE`, `UNAVAILABLE` or materially stale evidence does not count as PASS.

## 9. Failure becomes an evidence-bound RepairCase

A failed gate must produce more than an error string.

RC7 must define a bounded repair problem equivalent to `RepairCaseV1` containing at least:

```text
repairCaseId
campaignId
candidateSha
profile identity
failed SIB level
failed claim / gate
observed failure
reproducer
violated contract / acceptance obligation
exact authority evidence
relevant environment identity
current finding/evidence references
affected capability class
change surface / dependency closure
recent relevant delta when known
forbidden regressions / protected obligations
known-good historical context
uncertainties
live evidence requirement
limitations
```

The RepairCase is an EBCA claim/evidence package, not permission to mutate the repository.

## 10. Repair strategy generation

From a trustworthy RepairCase, CodeSleuth may produce candidate repair strategies.

Each strategy must state:

```text
root-cause hypothesis
supporting evidence
proposed change surface
expected semantic effect
required regression witness
focused verification
broader reopened obligations
risks
forbidden changes
stop conditions
```

The repair analysis must explicitly consider that the drifting side may be:

- implementation (`CODE_AHEAD` or implementation defect);
- normative/public documentation (`DOC_AHEAD` or stale docs);
- executable tests/gates (`TEST_AHEAD` or stale oracle);
- multiple contradictory authorities (`CONTRADICTED`);
- insufficient evidence (`UNPROVEN`).

A strategy that changes an accepted contract/profile/architecture merely to make a test green is not an ordinary auto-repair.

## 11. Evidence-bound auto-repair through the host

Auto-repair does not make CodeSleuth a primary coding agent or controller.

The authority split remains:

```text
CodeSleuth
- exact identity
- evidence
- SIB/EHA state
- RepairCase
- bounded RepairPacket
- scope/forbidden-regression rules
- verification requirements

Host coding agent
- actual source edits
- shell/tool execution
- patch creation
- project-native commands

Human/operator
- project authority
- ambiguous contract resolution
- profile acceptance
- architecture reopen
- material scope expansion
- baseline promotion where project policy requires it
```

A host may execute an approved or policy-permitted repair packet automatically. The resulting bytes are a new candidate subject.

## 12. RepairPacketV1

The accepted RC7 design must define a host-consumable packet equivalent to `RepairPacketV1`.

Minimum fields:

```text
repairCaseId
exact failed candidate
project/profile identity
objective
root-cause hypothesis
allowed change surface
forbidden/adjacent paths
violated obligations
preservation obligations
required regression witness
focused verification
broader native gates to rerun
expected stop conditions
operator decisions already granted
unresolved questions
```

The packet must be concrete enough that a fresh Cursor/Codex/OpenCode session can perform the repair without relying on hidden chat memory.

## 13. New candidate and fresh campaign

A successful patch produces a new exact Git subject.

Canonical repair loop:

```text
candidate A
-> EHA FAIL
-> RepairCase
-> RepairPacket
-> host repair
-> focused verification
-> integrate according to project authority
-> candidate B
-> fresh EHA campaign
```

Candidate A remains historical failed evidence forever. Repair cannot edit it into PASS.

Where the project defines a canonical release/integration stream, repair must return through that stream before candidate selection. Tree equality with the repair commit does not transfer acceptance to the integrated commit.

## 14. Mandatory auto-repair stop conditions

Automatic repair MUST stop and request operator/authority action when any of the following applies.

### 14.1 `OPERATOR_DECISION_REQUIRED`

Current project authorities conflict or several interpretations remain materially plausible.

### 14.2 `SCOPE_EXPANSION_REQUIRED`

The repair requires changing paths/capabilities outside the accepted active scope or contradicts a scope guard.

### 14.3 `ARCHITECTURE_REOPEN_REQUIRED`

The repair requires introducing/removing/redefining a fundamental capability class or materially changing architecture-generation ownership.

The current SIB0 profile is not silently stretched. A new architecture generation/profile adjudication and new SIB0 are required.

### 14.4 `LIVE_EVIDENCE_REQUIRED`

The remaining claim cannot honestly be verified from repository/hosted evidence and requires a live runtime, deployment, credentials, persistent service state or operator observation.

### 14.5 `REPAIR_LOOP_STALLED`

Repeated repair attempts cycle, reproduce the same failure topology, oscillate between regressions or fail to increase justified evidence.

The system must preserve lineage and stop rather than spend tokens indefinitely.

### 14.6 `EVIDENCE_UNTRUSTED`

The ledger/profile/source evidence required for repair is corrupt, stale, ambiguous or otherwise unable to support a trustworthy repair decision.

Ledger Repair may be required before development repair continues.

## 15. Architecture reopen loop

A genuine new capability class is not ordinary feature population or repair.

```text
existing architecture generation
-> architecture-changing requirement discovered
-> ARCHITECTURE_REOPEN_REQUIRED
-> proposal + evidence
-> user/maintainer adjudication
-> new architecture generation
-> revised ProjectSibProfile
-> new SIB0
-> SIB1
-> SIB2
```

This preserves the semantic value of SIB0 instead of letting its inventory mutate under the same label.

## 16. Relationship to RC7 ledgers

RC7 must keep domain authorities distinct.

```text
Git/source authority
    = which exact bytes exist

Finding ledger
    = what material defects/claims were recorded and amended

Implementation ledger
    = what development-plan work and verification events occurred

EHA ledger
    = what maturity claims were accepted/rejected for exact candidates/profiles
```

Cross-links are required; authority merging is not.

A repair attempt may reference findings, implementation events and EHA campaigns, but it must not duplicate or rewrite their historical facts into a generic super-ledger.

## 17. Projection parity

SIB profile, RepairCase, RepairPacket and EHA lineage should participate in the RC7 projection-parity model where applicable:

```text
authoritative domain events/state
        |
        +--> NDJSON
        +--> Markdown status/report
        +--> Graphify relationships
        +--> Mermaid presentation
```

All projections must preserve declared semantic identity, profile/campaign IDs, exact candidate SHA, claim/result state, authority/provenance links and lineage. Presentation remains derived.

## 18. Required tool surfaces

Exact API names remain design-time decisions, but RC7 must provide bounded primitives equivalent to:

### SIB profile

- `sib_profile_discover`
- `sib_profile_validate`
- `sib_profile_adjudicate`
- `sib_profile_load`

### EHA maturity

- generic campaign start/load/status/completion primitives reusing the existing EHA authority where possible;
- SIB0/SIB1/SIB2 claim/evidence recording against a project profile;
- exact candidate/profile/environment validation.

### Repair

- `eha_repair_case_build`
- `eha_repair_strategy_propose`
- `eha_repair_packet_build`
- `eha_repair_attempt_record`
- repair-loop/stall evaluation.

The design should minimize new APIs and reuse existing `eha_state`, review/findings, continuation, scope and gate primitives where their semantics already fit.

## 19. Required Skills

At minimum, RC7 design must provide or compose Skills equivalent to:

- `sib-profile-discovery`
- `sib-profile-triangulation`
- `sib0-architecture-assessment`
- `sib1-implementation-assessment`
- `sib2-integration-assessment`
- `eha-failure-root-cause`
- `repair-strategy-generation`
- `repair-evidence-validation`

Every Skill must use EBCA vocabulary consistently and distinguish observation, evidence, authority, verification, validation, acceptance and claimability.

## 20. Required Playbooks

### `sib-profile-bootstrap`

1. freeze exact repository target;
2. resolve project development/architecture/acceptance authority;
3. perform contract archaeology and triangulation;
4. propose capability classes/contracts;
5. map native gates/environments;
6. present alternatives/uncertainties;
7. stop for human adjudication;
8. materialize/bind accepted profile only through explicit authority.

### `eha-maturity-loop`

1. select/freeze candidate according to project authority;
2. bind accepted profile/environment;
3. start/load campaign;
4. assess SIB0;
5. assess SIB1;
6. assess SIB2;
7. on PASS, complete durably;
8. on FAIL, create RepairCase and enter bounded repair workflow;
9. on unknown/live/operator boundary, stop with the correct explicit state.

### `eha-repair-loop`

1. load exact failed campaign/claim;
2. build RepairCase;
3. perform root-cause analysis;
4. propose bounded alternatives;
5. enforce stop conditions;
6. build RepairPacket;
7. dispatch execution to the host under granted permissions;
8. run focused verification;
9. record repair attempt/outcome;
10. integrate according to project authority;
11. select the resulting new exact candidate;
12. start a fresh EHA campaign.

### `architecture-reopen`

A separate explicit workflow for changes that invalidate the current capability-class inventory/profile generation.

## 21. Command surface

Prefer extension of the existing command family over command proliferation.

Expected direction:

- `/sib-bootstrap` or a similarly narrow profile-bootstrap entry;
- `/eha-test` becomes project-portable and profile-aware;
- `/eha-repair` consumes RepairCase/RepairPacket semantics;
- `/eha-status` exposes profile identity, exact subject, campaign lineage and claimability.

The accepted design must decide whether `sib-bootstrap` belongs as a standalone command or as an explicit mode of an existing repository bootstrap/continuation workflow.

## 22. Adversarial fixtures and acceptance

RC7 acceptance must include projects with materially different structures, not merely a renamed CodeSleuth fixture.

Required scenarios include:

1. project with explicit capability registry and native SIB-equivalent policy;
2. brownfield project with capability model distributed across code/docs/tests;
3. two plausible capability decompositions requiring user adjudication;
4. architecture/doc/test disagreement producing `CONTRADICTED` rather than automatic adoption;
5. SIB0 PASS then new fundamental capability requirement causing architecture reopen;
6. SIB1 implementation failure producing a RepairCase and bounded repair packet;
7. stale test oracle where the correct disposition is test repair rather than code repair;
8. stale documentation where code+tests establish `CODE_AHEAD`;
9. SIB2 integration failure requiring cross-capability repair;
10. live-only gate causing `LIVE_EVIDENCE_REQUIRED` rather than false PASS;
11. repair that would cross an adjacent/forbidden scope and therefore stops;
12. repeated repair oscillation causing `REPAIR_LOOP_STALLED`;
13. candidate B descended from accepted candidate A where A's PASS is context only and B receives fresh acceptance;
14. tree-equivalent but non-identical commits that do not share acceptance;
15. profile revision invalidating silent reuse of the prior profile's acceptance evidence;
16. retained regression witness proving durable negative knowledge after repair.

## 23. RC7 acceptance criteria for this slice

This slice is acceptable only when:

- CodeSleuth can propose a meaningful SIB0/SIB1/SIB2 profile for an unfamiliar repository from exact project evidence;
- the user can inspect alternatives, uncertainty and authority evidence before adoption;
- accepted project profiles are versioned/bound and cannot inherit unrelated CodeSleuth maturity history;
- SIB0/SIB1/SIB2 retain one stable cross-project meaning;
- generic EHA campaigns operate against project-local profiles and native gates;
- claimability is cumulative on one exact subject;
- failed candidates remain immutable historical FAIL evidence;
- a failed gate yields an evidence-bound RepairCase rather than an unstructured error;
- a fresh host session can execute a RepairPacket without relying on hidden conversation context;
- bounded auto-repair can iterate through new exact candidates and fresh campaigns;
- ambiguity, scope expansion, architecture reopen, live-only proof, untrusted evidence and repair cycling stop automatically rather than being guessed through;
- regression witnesses and negative knowledge persist after successful repair;
- existing EBCA, durable evidence, scope, native-gate and ledger authority invariants remain intact;
- Markdown/NDJSON/Graphify/Mermaid views remain derived and semantically consistent;
- at least two structurally different real projects pass read-only profile discovery/dogfood before release acceptance;
- at least one controlled live repair loop demonstrates fail -> RepairCase -> host repair -> new exact candidate -> fresh EHA without rewriting prior history.

## 24. Scope restraint

This slice does not authorize:

- autonomous invention of project contracts;
- automatic architecture/profile adoption without project/user authority;
- a CodeSleuth-owned general coding runtime;
- automatic merge/release decisions;
- arbitrary mutation outside RepairPacket scope;
- universal replacement of project-native acceptance with CodeSleuth-specific generic tests;
- reinterpretation of SIB0/SIB1/SIB2 per project;
- generic workflow stages beyond SIB0/SIB1/SIB2 merely because the engine could be generalized;
- changing historical FAIL to PASS on the same exact subject;
- allowing a derived report/graph/model summary to become acceptance authority.

The purpose is narrower and concrete: **make CodeSleuth capable of discovering, proposing, adjudicating, executing and repairing evidence-backed architectural maturity loops for arbitrary projects while preserving EBCA claim semantics and host/user authority boundaries.**
