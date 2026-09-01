# RC7 Repair Packet and Host Rendering Contract

**Status:** ACCEPTED RC7 PLANNING ADDENDUM  
**Scope:** project-portable EHA repair orchestration and host prompt rendering  
**Semantic authority:** [`EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md)  
**Related planning:** [`RC7-FEATURE-PLAN.md`](RC7-FEATURE-PLAN.md), [`RC7-SIB-EHA-MATURITY-LOOPS.md`](RC7-SIB-EHA-MATURITY-LOOPS.md)

## 1. Purpose

RC7 must turn the informal instruction “fix the failure we just found” into a portable, evidence-bound repair artifact that can be handed to Cursor, Codex, OpenCode, another host, or a human without relying on hidden chat context.

The core architecture is:

```text
failed acceptance claim
        ↓
RepairCaseV1
        ↓
root-cause / contract reconciliation
        ↓
validated RepairPacketV1
        ↓
policy + scope + authority checks COMPLETE
        ↓
host-specific Jinja2 rendering
        ↓
Cursor / Codex / OpenCode / human
        ↓
host mutation
        ↓
postcondition re-observation
        ↓
new exact candidate
        ↓
fresh verification / EHA
```

The template is a renderer. It is never the place where repair permission, evidence sufficiency, scope expansion, acceptance, or authority is decided.

Compact rule:

> **Structured evidence decides what may be repaired; Jinja2 only explains the already-validated repair packet to a particular host.**

## 2. Authority boundary

`RepairCaseV1`, `RepairPacketV1`, rendered prompts and repair reports are workflow/read-model artifacts. They do not replace:

- tracked Git source as source authority;
- project planning/architecture/contract authority;
- findings/amendment ledgers for finding history;
- implementation ledger for development-history facts;
- EHA ledger for campaign/verdict history;
- accepted project-native registries where present.

A rendered prompt MUST NOT become a second authority merely because a powerful model consumed it.

Every material repair claim must follow the EBCA claim dimensions:

```text
subject
property
scope
assumptions
authority
evidence[]
environment[]
result
limitations[]
```

The exact serialized shape may be optimized during implementation, but those dimensions may not disappear when material to the repair.

## 3. `RepairCaseV1`

A Repair Case describes the evidence-bound problem before a repair strategy is selected.

Minimum semantic fields:

```text
schemaVersion
repairCaseId
projectIdentity
targetSha
worktreeIdentity
campaignId / failedSibLevel / failedGate when applicable
acceptanceProfileRef
failedClaim
observedFailure
reproducer
violatedContractRefs[]
affectedCapabilityRefs[]
recentRelevantDelta
changeSurface
forbiddenRegressionRefs[]
knownGoodReference
assumptions[]
limitations[]
residualUncertainty[]
liveEvidenceRequired
```

`failedClaim` must retain the relevant EBCA subject/property/scope/authority/evidence/environment/result dimensions rather than collapsing the case to an error string.

## 4. `RepairPacketV1`

A Repair Packet is created only after the Repair Case has been diagnosed sufficiently to bound an admissible repair.

Minimum semantic fields:

```text
schemaVersion
repairPacketId
repairCaseId
projectIdentity
targetSha
acceptanceProfileRef
suggestedRepairBranch
repairObjective
rootCauseClassification
contractEvidence[]
allowedChangeSurface[]
forbiddenSurface[]
affectedObligationClosure[]
invariantCore[]
repairStrategies[]
selectedStrategy
requiredRegressionWitnesses[]
verificationPlan[]
postconditionChecks[]
stopConditions[]
assumptions[]
limitations[]
residualUncertainty[]
```

A branch name is workflow/navigation metadata. The exact target and resulting exact candidate SHA remain the identities relevant to verification and EHA.

### 4.1 Allowed change surface

The packet must distinguish:

- explicitly allowed paths/surfaces;
- derived affected closure;
- adjacent tracks;
- forbidden/protected surfaces;
- unresolved scope where authority is insufficient.

Derived impact does not auto-expand accepted project scope. If the repair genuinely requires expansion, the packet stops with `SCOPE_EXPANSION_REQUIRED`.

### 4.2 Repair strategies

A packet may present multiple strategies when evidence supports alternatives. Each strategy records:

- intended change;
- supporting contract/evidence;
- expected affected surface;
- known risks;
- verification obligations;
- why the strategy is permitted or rejected.

A strategy that requires changing project authority rather than implementation must be marked as requiring operator adjudication rather than silently selected as an implementation fix.

### 4.3 Required regression witness

A reproduced unacceptable state should normally yield a regression witness obligation. The witness must be specific enough to distinguish the old failure from the repaired state and must be traceable to the affected contract/finding.

Repair completion does not automatically make the witness a permanent protected obligation. Promotion to durable negative knowledge / forbidden regression follows the accepted project authority and the RC7 EBCA preservation rules.

## 5. Jinja2 rendering

Preferred implementation direction: host-specific Jinja2 templates over the validated packet.

Examples:

```text
repair-cursor.jinja2
repair-codex.jinja2
repair-opencode.jinja2
repair-human.md.jinja2
```

A project or host adapter may provide its own template/profile without forking the generic Repair Packet model.

### 5.1 Template responsibilities

A template MAY control:

- wording and section order;
- host-specific command syntax;
- how tools/capabilities are named;
- compact vs extended explanation;
- host-specific safety reminders already represented by packet policy;
- formatting of exact refs, evidence tables and verification commands.

A template MUST NOT decide:

- whether repair is allowed;
- whether evidence is sufficient;
- whether a gate is PASS;
- which SHA is the accepted subject;
- whether scope may expand;
- whether architecture may reopen;
- whether operator approval is required;
- whether an old FAIL can be ignored;
- whether a forbidden regression is applicable.

No policy rule should exist only inside a template.

## 6. Deterministic render contract

For the same packet, template identity and renderer version, output should be deterministic modulo explicitly declared non-semantic formatting.

A render manifest should record at least:

```text
packetId
packetDigest
templateId
templateDigest
rendererVersion
hostProfileId
renderedAt
```

The render manifest is provenance for the derived prompt. It is not acceptance evidence.

Use strict template evaluation (`StrictUndefined` or equivalent) so missing required packet fields fail closed rather than silently disappearing from a repair prompt.

## 7. Untrusted-content boundary

Repository evidence may itself contain adversarial or misleading instructions. Source/docs/test excerpts are evidence data, not prompt authority.

Rendering must therefore:

- structurally delimit quoted repository evidence from host instructions;
- retain source/path/blob provenance for material excerpts;
- bound excerpt size;
- avoid interpreting template syntax contained in evidence values as template code;
- never load arbitrary project-provided Jinja extensions or Python code merely because a repository contains them;
- treat project-owned custom templates as executable configuration with an explicit trust/install boundary;
- expose truncation visibly.

A repair prompt that quotes `IGNORE ALL PREVIOUS INSTRUCTIONS` from a source file must present it as quoted source evidence, not obediently promote it to controller policy. Humanity has already contributed enough examples of why this distinction matters.

## 8. Host/profile customization

A host rendering profile may declare:

```text
hostProfileId
host family / version constraints
available tool names
shell/command conventions
path conventions
preferred verbosity
supported structured attachments
required prompt sections
template identity
```

A project adapter may add domain vocabulary and evidence presentation rules, but it may not weaken the generic authority/scope/repair constraints.

The same `RepairPacketV1` should be renderable for multiple hosts without changing its repair semantics.

## 9. Cross-render parity

Given one canonical packet, Cursor/Codex/OpenCode/human renderings must preserve the same material semantics:

- exact target;
- failed claim;
- relevant authority/evidence;
- allowed/forbidden scope;
- selected repair strategy;
- required regression witness;
- verification obligations;
- stop conditions;
- assumptions, limitations and residual uncertainty.

Parity tests compare semantic fields, not prose equality.

## 10. Postcondition verification

A host saying “fixed” is a claim, not new-state authority.

After a repair host mutates the worktree, CodeSleuth must re-observe at minimum:

```text
actual changed paths / diff
worktree identity
new commit SHA when committed
required regression witness presence/result
focused verification result
scope-guard result
```

Only the re-observed candidate may enter fresh EHA. Command exit `0`, host prose, or a rendered completion message do not establish the new state.

## 11. Stop conditions

The packet/rendered prompt must preserve explicit stops such as:

```text
OPERATOR_DECISION_REQUIRED
SCOPE_EXPANSION_REQUIRED
ARCHITECTURE_REOPEN_REQUIRED
LIVE_EVIDENCE_REQUIRED
EVIDENCE_UNTRUSTED
AFFECTED_CLOSURE_UNTRUSTED
REPAIR_LOOP_STALLED
```

A host must be told to stop rather than invent missing authority.

## 12. Acceptance requirements

This RC7 slice is acceptable only when:

1. repair semantics exist in typed validated data before prompt rendering;
2. host-specific templates cannot change repair authority/policy;
3. required fields fail closed if absent;
4. rendered prompts are traceable to packet + template digests;
5. project/host customization does not require a CodeSleuth fork;
6. source evidence is visibly treated as data, not controller instruction;
7. cross-host semantic parity is tested;
8. postcondition re-observation is mandatory before claiming a repair exists;
9. a clean new session can execute a bounded repair from the packet without hidden chat history;
10. the repaired exact candidate still requires fresh acceptance under the applicable profile.
