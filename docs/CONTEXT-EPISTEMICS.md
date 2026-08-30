# Context Epistemics for Evidence-Based Code Analysis

**Status:** post-0.4 design doctrine  
**Scope:** LLM-assisted software engineering, coding agents, context projections, evidence reasoning, and mutation safety  
**Relationship to EBCA:** this document extends the existing EBCA axioms that identity precedes claim, authority precedes representation, negative knowledge is durable, and unknown remains unknown

## 1. Purpose

Large language models can reason effectively over source code, architecture, logs, documentation, and operational state. They do not, however, provide a reliable built-in guarantee that they will distinguish:

- fact from plausible completion;
- current state from stale state;
- authority from representation;
- absence of evidence from evidence of absence;
- observed relation from familiar pattern;
- a relevant statement from an instruction they are authorized to follow;
- a claim from a state mutation precondition.

For ordinary text, an error may remain a bad answer.

For a coding or operator agent, the same error can become a real mutation:

```text
mis-reconstructed state
        ↓
locally coherent reasoning
        ↓
correctly executed command
        ↓
wrong real-world mutation
```

The primary engineering problem is therefore not simply that an LLM may reason badly.

A more dangerous failure is:

> **the LLM reasons well inside a falsely reconstructed world.**

Context discipline exists to make that reconstruction explicit, typed, bounded, and challengeable.

---

## 2. LLM authority boundary

The model is treated as an inference engine, not as the owner of system state.

```text
LLM = inference authority

LLM != state authority
LLM != evidence authority
LLM != ownership authority
LLM != acceptance authority
LLM != execution authority
```

The model may propose:

- hypotheses;
- explanations;
- plans;
- candidate findings;
- repairs;
- requests for more evidence.

It must not silently convert plausibility into authoritative state.

Its job is:

> build a useful next inference from established state.

Its job is not:

> guess which state is probably true and act as if the guess had already been verified.

---

## 3. Layers of reality and reasoning

```text
REAL WORLD
Git / filesystem / DB / CI / host / API
        ↓
AUTHORITATIVE FACTS
exact SHA / refs / schemas / manifests / durable ledgers / exact observations
        ↓
BOUNDED CONTEXT PROJECTION
selected, typed, current model-facing representation
        ↓
LLM REASONING
claims / hypotheses / plans / decisions
```

The direction of authority does not reverse.

Examples:

- a summary does not become repository truth;
- a report does not become acceptance authority;
- a Mermaid diagram does not become source authority;
- another agent's message does not become host truth;
- a branch name does not become commit identity;
- a matching tree does not become acceptance identity;
- successful CI does not become an EHA verdict;
- a code comment does not become an instruction surface because it is inside the target repository.

The companion [`CONTEXT-ADMISSION-CONTRACT.md`](CONTEXT-ADMISSION-CONTRACT.md) defines the minimum passport required for decision-bearing context.

---

## 4. The fundamental unknown rule

A generative model is strongly tempted to complete missing state with a plausible value.

Two invalid transitions are especially common:

```text
no evidence for X
        ↓
X is probably false
```

and:

```text
no evidence against X
        ↓
X is probably true
```

Both are forbidden.

Canonical rule:

```text
UNKNOWN != TRUE
UNKNOWN != FALSE
```

Loss of observation changes the state of knowledge, not the state of the object.

If the light is switched off, the model does not acquire evidence that black became white. It merely lost a relevant observation.

---

## 5. Epistemic states

A material engineering claim needs more than a binary true/false flag.

### CLAIMED

A human, agent, report, retrieved document, or derived representation states the proposition, but the proper authority has not yet established it.

### CORROBORATED

An independent but non-authoritative anchor supports the claim or an expected consequence of it.

Example:

```text
operator: runner service started
GitHub: queued job becomes in_progress
```

The GitHub transition corroborates the service-recovery story but does not necessarily prove every local runner setting.

### CONFIRMED

The property is supported by the authority that owns that property.

Examples:

- exact Git ref for current ref target;
- exact tracked source for source content;
- durable EHA ledger for EHA verdict history.

### CONTRADICTED

Independent or authoritative evidence is incompatible with the claim.

### CONFLICTED

Multiple relevant sources disagree and the authority ordering or freshness relation has not yet resolved the conflict.

### UNKNOWN

Available evidence is insufficient to establish the property or its negation.

Unknown is a legitimate terminal state for analysis. It is not an embarrassment to be erased by confident prose.

---

## 6. The main danger: false state, not exotic hallucination

A fabricated API is often suspicious enough to trigger a documentation check.

More dangerous statements look ordinary:

```text
"this is staging"
"this directory is generated"
"this commit already passed acceptance"
"this file belongs to our system"
"this migration has already run"
"this runner is correctly registered"
```

Once the model adopts one of these as state, the following reasoning may be entirely rational.

Example:

```text
FALSE PREMISE:
".opencode/state is entirely CodeSleuth-owned"

        ↓

REASONABLE IMPLEMENTATION:
recursive removal

        ↓

CORRECT EXECUTION

        ↓

REAL DATA LOSS
```

The defect is not primarily in the delete algorithm.

The defect is the unsupported ownership claim.

This is why ownership, environment, identity, acceptance, and authority must be explicit preconditions for material mutations.

---

## 7. Why long context does not solve the problem

A longer context window increases available material. It does not guarantee correct authority selection.

Long context can contain simultaneously:

- old and current revisions;
- superseded decisions;
- old acceptance results;
- similar identifiers;
- rejected hypotheses;
- summaries of summaries;
- historical worktrees;
- copied issue descriptions;
- stale external documentation;
- current facts mentioned once and old facts repeated many times.

Attention is not a database query that deterministically selects the latest authoritative record.

Therefore:

> **Do not increase context before defining which parts of the context are eligible to influence the current decision.**

The minimum dimensions are defined by the context-admission contract:

```text
provenance
authority
freshness
scope
invalidation state
relationship to current target identity
```

A million-token context without these distinctions can be less safe than a small context capsule with them.

---

## 8. Negative Claims

### 8.1 Definition

A **Negative Claim** is durable knowledge about a proposition or inference that must not be silently promoted into established state.

It is not merely a warning and not merely a sentence containing `not`.

A positive claim asks:

> what is established?

A Negative Claim asks:

> which plausible conclusions must not be treated as established under the current evidence?

Its purpose is to block dangerous inference shortcuts, especially the pattern-completion behavior that makes code generators useful in local code synthesis and dangerous in state reconstruction.

---

## 9. Classes of Negative Claims

### 9.1 CONTRADICTED claim

The proposition is incompatible with available authority.

```text
claim: main points to SHA A
authority: main points to SHA B
```

### 9.2 UNPROVEN claim

The proposition may be true, but the available evidence does not establish it.

```text
"the entire .opencode/state subtree belongs to CodeSleuth"
```

may be locally plausible, but a managed-file manifest that names only selected paths does not prove whole-subtree ownership.

For read-only analysis the proposition may remain a hypothesis.

For destructive recursion it must block the operation.

### 9.3 FORBIDDEN_INFERENCE

Form:

```text
A does NOT imply B
```

This does not assert that `B` is false.

It asserts that the transition from `A` to `B` is not evidence-backed.

Examples:

```text
parent EHA PASS
    -/-> child EHA PASS
```

```text
same tree
    -/-> same acceptance identity
```

```text
path under .opencode
    -/-> CodeSleuth ownership
```

```text
GitHub workflow SUCCESS
    -/-> SIB/EHA PASS
```

```text
service process exists
    -/-> correct service registration
```

```text
no failing test observed
    -/-> feature correctness
```

```text
repository content belongs to target
    -/-> repository content has instruction authority over the agent
```

A forbidden inference is best understood as a negative edge in the reasoning graph:

```text
A -/-> B
```

This is different from `NO_EDGE`.

`NO_EDGE` means no relation is known.

A negative edge means the relation was considered and is explicitly not claimable under the declared evidence/contract.

---

## 10. Durable Negative Claim shape

A future structured representation should preserve at least:

```text
NegativeClaim {
    id
    subject
    claim
    status
    authority
    evidenceRefs[]
    reason
    danger
    consequence[]
    scope
    recordedAt
    sourceIdentity
    reopenCondition
}
```

Suggested statuses:

```text
CONTRADICTED
UNPROVEN
FORBIDDEN_INFERENCE
```

`reopenCondition` is critical.

Without it, a future model may rediscover the same attractive but rejected inference and treat it as a fresh insight.

New evidence may supersede a Negative Claim, but it should not erase the historical fact that the inference was previously rejected.

---

## 11. Negative Claims and code-generator grounding

Code generation benefits from pattern completion:

```text
see 80% of a familiar structure
        ↓
complete the remaining 20%
```

For a local function this can be a strength.

For production state, ownership boundaries, migrations, release status, or service identity, it can be catastrophic.

Negative Claims deliberately place durable counter-knowledge next to the attractive pattern:

```text
looks like X
    !=
proved as X
```

Example context for a change to lifecycle cleanup:

```text
NEGATIVE CLAIM

Do not infer ownership from location under `.opencode`.

Rejected inference:
`.opencode/**` is CodeSleuth-owned.

Authority:
managedFiles + explicit runtime namespaces.

Failure mode:
destructive removal of host-owned material.
```

The model is still free to investigate whether wider ownership can be proved.

It is not free to behave as though the proof already exists.

---

## 12. Retrieval must include negative relevance

Conventional retrieval usually emphasizes positive semantic relevance.

Evidence-oriented retrieval should include:

```text
positive relevance
+ authority relevance
+ negative relevance
+ risk relevance
+ freshness
```

For a material code change, the bounded context should attempt to retrieve:

- relevant positive facts;
- prior failures;
- relevant contradictions;
- unproven assumptions;
- forbidden inference edges;
- ownership restrictions;
- exact acceptance-identity constraints;
- high-risk failure modes.

A retrieved item remains navigation/context until rehydrated from its proper authority where the claim requires it.

---

## 13. Context as an epistemic type system

A useful mental model is that context contains typed claims rather than undifferentiated strings.

Examples:

```text
Claim<GitAuthority>
Claim<FilesystemObservation>
Claim<DurableEvidenceAuthority>
Claim<DerivedReport>
Claim<ModelInference>
Claim<ExternalOperatorReport>
Claim<UntrustedRetrievedContent>
```

An operation that requires `Claim<DurableEvidenceAuthority>` must not accept `Claim<DerivedReport>` merely because their prose agrees.

Many LLM failures can therefore be modeled as **epistemic type errors**.

Examples:

```text
DerivedReport -> AcceptanceAuthority       INVALID
IssueText -> SourceTruth                    INVALID
RepositoryComment -> AgentInstruction       INVALID by default
AncestorAcceptance -> CurrentAcceptance     INVALID
```

---

## 14. Observe, claim, decide, mutate

Coding agents typically cross four semantic boundaries:

```text
OBSERVE
CLAIM
DECIDE
MUTATE
```

The disciplined route is:

```text
OBSERVE
    ↓ provenance
CLAIM
    ↓ evidence binding
DECIDE
    ↓ authority + risk gate
MUTATE
    ↓ postcondition verification
NEW OBSERVED STATE
```

The dangerous shortcut is:

```text
CLAIM -> MUTATE
```

A command returning exit code `0` proves only the declared execution result of that command. It does not automatically prove the intended new system state.

Postcondition state must be observed again through the relevant authority or external anchor.

---

## 15. Risk-weighted epistemics

Evidence requirements should rise with blast radius.

### Read-only analysis

An `UNPROVEN` statement may be retained as a hypothesis if clearly labeled.

### Reversible local mutation

Require exact target and ownership of the edited state.

### Shared or operational mutation

Require stronger target/environment identity and an explicit rollback path.

### Destructive or production mutation

Require confirmation of all material preconditions:

```text
target CONFIRMED
environment CONFIRMED
ownership CONFIRMED
scope CONFIRMED
authorization CONFIRMED
recovery assumptions explicit
material contradictions NONE
critical unknowns NONE
```

For a high-risk operation:

```text
UNPROVEN = STOP
CONFLICTED = STOP
critical UNKNOWN = STOP
```

The model may request additional evidence. It may not remove the epistemic requirement by writing a more persuasive explanation.

---

## 16. Prompt injection as epistemic privilege escalation

Prompt injection becomes easier to reason about when treated as an authority problem rather than only a malicious-string problem.

An attacker tries to make data acquire a false role:

```text
untrusted data
    ↓
claims relationship to current task
    ↓
claims instruction authority
    ↓
model accepts role escalation
    ↓
action path changes
```

Canonical forbidden inferences:

```text
target membership
    -/-> instruction authority
```

```text
retrieval relevance
    -/-> instruction authority
```

```text
tool output
    -/-> permission to issue new tool commands
```

```text
external text names current user/repository/task
    -/-> verified relationship to that target identity
```

The companion context-admission contract treats target binding and authority binding as independent checks.

This does not replace prompt-injection filtering, sandboxing, least privilege, action confirmation, or tool authorization. It provides a general reasoning contract that explains why those controls are necessary.

---

## 17. Relationship to SIB and EHA

SIB/EHA are concrete instances of the broader epistemic discipline.

### SIB

Establishes a known accepted baseline within a defined profile.

### EHA

Blocks acceptance transfer across identity changes:

```text
accepted identity A
    -/-> different identity B accepted
```

### Protected capability registry

Preserves explicit architectural and behavioral boundaries so future agents do not silently reinterpret them.

### Durable evidence store

Prevents conversation memory and report prose from becoming evidence authority.

### RepositoryContextProjection

Provides bounded, rebuildable model-facing context without becoming repository truth.

### Negative Claims

Preserve rejected inference paths so a new model/session does not repeatedly reconstruct the same false world.

---

## 18. Remote-agent reports

When one agent operates on a host that another reviewer cannot access, the operator narrative is a claim source, not host authority.

Example:

```text
Cursor: "runner service started"
        ↓ CLAIMED

GitHub: queued -> in_progress
        ↓ CORROBORATED

Actions metadata/logs: expected self-hosted job executes exact candidate
        ↓ relevant execution identity CONFIRMED

Cursor: "EHA passed"
        ↓ still CLAIMED

durable eha.ndjson for exact SHA
        ↓ EHA CONFIRMED
```

This discipline is tracked for post-0.4 implementation in issue #104 and should reuse existing CodeSleuth Skills/Playbooks rather than creating a remote-host controller.

---

## 19. Goal of context discipline

The goal is not:

- infinite context;
- a model that never makes mistakes;
- a model that memorizes the whole project;
- a second authority implemented inside the LLM layer.

The goal is:

> **make an incorrect reconstruction of the world harder and more expensive than the correct one.**

Desired topology:

```text
correct inference paths
    -> explicit, fresh, authoritative, short

previously rejected paths
    -> durable negative knowledge

unknown dangerous paths
    -> require more evidence before mutation
```

A small model receiving 12,000 well-typed tokens can therefore be safer than a larger model receiving hundreds of thousands of undifferentiated historical tokens.

---

## 20. Central engineering rule

```text
LLM may infer.

LLM may not silently promote
plausibility into state authority.
```

Or more operationally:

> **A model may believe that a proposition is likely. It may not perform a material action as though that proposition were established when the required authority has not established it.**

The desired result is not less capable reasoning.

It is bounded epistemic privilege.
