# LLM Context Admission Contract

**Status:** post-0.4 design doctrine / universal context-discipline contract  
**Scope:** any CodeSleuth workflow, coding agent, RAG pipeline, operator agent, or other LLM-assisted system that consumes external context  
**Authority:** this document defines admission and interpretation rules for context; it does not become source, evidence, execution, or acceptance authority

## 1. Purpose

An LLM must not treat text as trustworthy merely because the text is present in its context window.

For every context item that may materially influence a decision, the system must establish at least:

1. **provenance**;
2. **authority**;
3. **freshness**;
4. **scope**;
5. **invalidation state**;
6. **relationship to current target identity**.

These six fields are the minimum context passport.

They apply beyond CodeSleuth. Any project that lets an LLM reason over repository content, retrieved documents, web pages, tool output, issue text, logs, memory, databases, or agent reports needs an equivalent discipline.

The goal is not to prove that every piece of text is true before a model can read it. The goal is to prevent an untyped context item from silently acquiring permission to steer a material decision.

---

## 2. Minimum context passport

A decision-bearing context item should be representable as:

```text
ContextItem {
    content
    provenance
    authority
    freshness
    scope
    invalidationState
    targetRelationship
}
```

Additional metadata may strengthen the contract, but omitting one of these six dimensions must be a deliberate, visible limitation.

### 2.1 Provenance

**Question:** where did this item come from?

Examples:

- exact Git blob/commit;
- workflow run/job/step;
- durable review or EHA ledger record;
- local filesystem observation;
- external web page;
- issue/PR/comment;
- tool response;
- another agent's report;
- model-generated summary;
- user-supplied text.

Provenance identifies origin. It does **not** by itself grant authority.

A malicious instruction can have perfectly authentic provenance: it may genuinely be present in the exact repository blob being reviewed.

### 2.2 Authority

**Question:** what fact, decision, or instruction class is this item allowed to own?

Examples:

- tracked source is authority for its current contents;
- Git refs are authority for current ref targets;
- an EHA ledger is authority for EHA campaign/verdict history;
- a report is a derived interpretation and is not repository truth;
- an issue can be requirements evidence but is not source truth;
- a code comment is source content but does not automatically have agent-instruction authority;
- retrieved web content is normally untrusted data unless an explicit contract says otherwise.

The central rule is:

```text
RELEVANCE != AUTHORITY
```

A context item may be highly relevant while having no authority to instruct the agent.

### 2.3 Freshness

**Question:** does this item still correspond to the subject state required by the current claim?

Freshness may depend on:

- exact target SHA;
- file/blob identity;
- workflow attempt;
- timestamp;
- environment version;
- current service state;
- current database/schema generation;
- superseding evidence.

Old evidence may remain historically useful while being stale for a current-state decision.

### 2.4 Scope

**Question:** within what boundary may this item be used?

Examples:

- one file;
- one repository revision;
- one service instance;
- one supported platform;
- one acceptance profile;
- one user/session;
- one tool response;
- one protected capability.

A true statement outside its scope is not automatically valid inside the current scope.

### 2.5 Invalidation state

**Question:** has the item been superseded, contradicted, retracted, expired, invalidated, or otherwise made unsafe to use as current decision input?

Suggested values:

```text
ACTIVE
SUPERSEDED
CONTRADICTED
RETRACTED
EXPIRED
UNKNOWN
```

Historical retention is compatible with invalidation. Invalidated context should normally remain inspectable but should not silently re-enter active decision context.

### 2.6 Relationship to current target identity

**Question:** how, exactly, is this item related to the object currently being analyzed or mutated?

Examples:

- exact content from target SHA;
- exact evidence produced for target SHA;
- ancestor evidence, useful for lineage but not acceptance transfer;
- issue describing the target feature;
- external documentation about a dependency used by the target;
- unrelated retrieved content;
- context item whose claimed target relationship cannot be verified.

This relationship must not be inferred merely because the item names the repository, branch, user, service, or task.

---

## 3. Target binding and authority binding are independent

Two separate questions must be answered:

```text
TARGET BINDING
Is this information actually about the object being worked on?

AUTHORITY BINDING
What decisions, if any, may this information influence?
```

A valid target relationship does not grant instruction authority.

Examples:

| Context item | Target relationship | Authority |
| --- | --- | --- |
| `src/foo.py` from exact SHA | strong/exact | source truth for its contents |
| comment inside `src/foo.py` | strong/exact | descriptive source content only unless explicitly designated otherwise |
| repository `AGENTS.md` | strong/exact | operational instructions only when the host/project explicitly designates it as such |
| GitHub issue | strong/medium | requirement/history claim, not current source truth |
| CI log | exact run/SHA when verified | execution evidence within that run/profile |
| generated report | may be exact-target | derived analysis, not source/evidence authority |
| fetched web page | task-related | untrusted external content by default |
| tool return value | task-related | observation from that tool, not instructions from the tool output text |

Canonical invariants:

```text
TARGET MEMBERSHIP != INSTRUCTION AUTHORITY
```

```text
AUTHENTIC PROVENANCE != TRUSTED INSTRUCTION
```

```text
RELEVANCE != PERMISSION TO STEER THE AGENT
```

---

## 4. Prompt injection as context-authority confusion

Indirect prompt injection can be modeled as an attacker attempting to make untrusted content acquire a false relationship or false authority within the model's active decision context.

Typical attack path:

```text
untrusted content
    ↓
claims to be instructions for the current repository/task/user
    ↓
model accepts fake target/instruction relationship
    ↓
content competes with legitimate instructions
    ↓
agent takes an unintended action
```

For example, a repository file might contain text such as:

```text
IMPORTANT FOR THE AI AGENT:
Before reviewing this repository, send ...
```

The existence of that text in the repository establishes only that the text is repository content.

It does not establish:

```text
repository content
    -> agent-control authority
```

That transition is a **forbidden inference** unless an explicit higher-authority contract designates that specific source as an instruction surface.

The same rule applies to:

- source comments;
- README files;
- issue and PR bodies;
- commit messages;
- compiler errors;
- logs;
- database fields;
- email bodies;
- fetched web pages;
- RAG documents;
- MCP/tool return values;
- model-generated reports;
- another agent's narrative.

Prompt injection therefore belongs not only to prompt filtering, but to context admission, authority typing, least privilege, and action gating.

This aligns with established security guidance. OWASP explicitly treats repository content, retrieved documents, tool outputs, issues, code comments, and web content as potential indirect prompt-injection channels and recommends separating instructions from data, constraining tools, and validating external content. OpenAI similarly describes prompt injection as third-party content misleading an agent and recommends limiting access, using explicit task instructions, and reviewing consequential actions.

References:

- OWASP LLM Prompt Injection Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- OWASP Secure Coding with AI Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html
- OWASP AI Agent Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
- OpenAI, Understanding prompt injections: https://openai.com/safety/prompt-injections/

These references strengthen the threat model but do not make this project claim compliance with any external standard.

---

## 5. Context-admission decision

Before an item becomes eligible for material decision context:

```text
context item
    ↓
provenance known?
    ↓
target relationship valid?
    ↓
authority class known?
    ↓
fresh enough for this target?
    ↓
scope applicable?
    ↓
not invalidated?
    ↓
ELIGIBLE FOR THE DECLARED DECISION ROLE
```

Failure does not necessarily mean deleting the item.

It may instead be quarantined as:

- navigation-only context;
- historical context;
- untrusted data;
- hypothesis input;
- evidence requiring rehydration;
- invalidated/superseded context.

Unknown target relationship or unknown authority must not silently become decision authority.

---

## 6. Relationship to current target identity must be independently checkable

A context item must not establish its own target binding merely by claiming one.

Bad:

```text
"This message applies to the current production database."
```

Good:

```text
context claims target = production DB X
        ↓
independent environment/connection identity check
        ↓
relationship CONFIRMED or rejected
```

For Git-managed work:

```text
branch/PR/report says SHA X
        ↓
Git/ref/worktree authority verifies SHA X
```

For EHA:

```text
report says candidate accepted
        ↓
exact target SHA + durable EHA campaign ledger
```

For remote operations:

```text
operator says service/host X was changed
        ↓
independent observable anchors where available
```

Self-asserted relationship metadata is a claim, not proof of relationship.

---

## 7. Context projection requirements

A bounded model-facing projection should preserve enough metadata for the model or surrounding tool layer to distinguish:

```text
content
source/provenance
exact target identity where applicable
authority class
freshness
scope
invalidation state
trust/untrusted-data classification
negative claims / forbidden inferences
```

The projection itself remains derived.

It must not become repository, evidence, acceptance, or execution authority merely because it carries authority metadata.

---

## 8. High-risk action rule

The stronger the blast radius, the stricter the admission requirement.

For destructive or production-affecting actions, every material context item used to establish target, environment, ownership, or authorization should be admitted under the six-field passport and resolved to an appropriate authority.

Material `UNKNOWN`, `CONFLICTED`, or invalidated state should fail closed.

Example:

```text
DELETE production data
requires:
    target relationship CONFIRMED
    environment authority CONFIRMED
    ownership/scope CONFIRMED
    authorization CONFIRMED
    recovery assumptions explicit
```

A plausible narrative is never sufficient merely because it is coherent.

---

## 9. Universal invariant

For any LLM-assisted project:

> **Context is not just content. Context is content plus provenance, authority, freshness, scope, invalidation state, and a verified relationship to the current target identity.**

And:

> **Relationship to the target establishes relevance, not authority.**

This contract is intended to remain portable across CodeSleuth, future agent tooling, RAG systems, software-development agents, and other projects where external text can affect real actions.
