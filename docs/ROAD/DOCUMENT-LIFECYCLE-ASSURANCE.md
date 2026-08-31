# Document Lifecycle Assurance: retiring, moving, and disappearing context

**Status:** ROAD / operating doctrine for documentation lifecycle and LLM context safety.  
**Scope:** documentation, navigation, archival state, replacement authority, and verification of document removal/reorganization.  
**Non-authority:** this document does not create a new runtime, evidence, Git, acceptance, or instruction authority.  
**Related:** [`INDEX.md`](INDEX.md), [`Whitepaper.md`](Whitepaper.md), [`ROAP.md`](ROAP.md), [`../EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md`](../EVIDENCE-BASED-CODE-ANALYSIS-THESAURUS.md), [`../SEMANTIC-REFIT.md`](../SEMANTIC-REFIT.md).

## 1. Purpose

Documentation is part of the context surface presented to humans and models. A documentation change can therefore alter reasoning even when no runtime file changes.

The dangerous case is not only a deleted file. A document may still exist in Git while the **meaning that made it discoverable, current, or authoritative disappears from the active context surface**.

Examples:

```text
file deleted
file moved without replacement pointer
old path preserved but current authority not named
index rewritten and required semantic anchor omitted
historical design packet still reachable and reads like live instruction
canonical document exists but is no longer discoverable from the normal entry point
summary replaces a contract and silently drops one invariant
```

This doctrine answers:

> When documentation changes, what evidence is required to prove that current guidance, historical provenance, negative knowledge, and replacement authority remain correctly represented?

## 2. Core rule

```text
document presence != context continuity
```

And conversely:

```text
document absence != knowledge invalidation
```

Removing or moving a document does not by itself prove that the knowledge it carried is obsolete. The lifecycle operation must establish what happened to the document's role.

A safe documentation transition must account for at least:

```text
previous identity
previous role
previous authority class
replacement authority
retained historical value
navigation continuity
semantic anchors
machine consumers
current target relationship
verification result
```

## 3. Documentation is a context-bearing artifact

For LLM-assisted engineering, a documentation artifact should be treated as context with the same minimum admission properties used elsewhere:

- provenance;
- authority;
- freshness;
- scope;
- invalidation state;
- relationship to current target identity.

A document can have valid provenance and still be stale for the current target. A document can be strongly related to the repository and still have no instruction authority. A historical packet can remain useful evidence while being forbidden as current procedure.

Therefore:

```text
TARGET MEMBERSHIP != CURRENT INSTRUCTION AUTHORITY
```

and:

```text
HISTORICAL VALUE != CURRENT OPERATING STATUS
```

## 4. Five disappearance classes

### 4.1 Physical disappearance

The file path no longer exists.

This is the easiest case to detect and the least interesting one epistemically. The important questions are:

- was deletion intentional;
- what replaced the document;
- whether inbound links were updated;
- whether historical content must remain available;
- whether any test/tool still consumes the path.

### 4.2 Navigational disappearance

The document still exists, but normal entry points no longer expose it.

Example:

```text
canonical EHA contract exists
        ↓
docs index rewritten
        ↓
EHA entry/authority pointer omitted
        ↓
model browsing from index does not retrieve it
```

Nothing was deleted from Git, yet the effective context supplied to an agent changed.

### 4.3 Semantic disappearance

The document or index still exists, but a required concept, invariant, formula, or authority marker is removed during summarization/reorganization.

Example:

```text
long docs index
        ↓
shorter cleaner index
        ↓
most links preserved
        ↓
critical literal/invariant omitted
```

This is dangerous because ordinary link checking can still pass.

Semantic disappearance is exactly the class caught by contract tests that assert normative concepts rather than file existence.

### 4.4 Authority disappearance

The content remains available, but the transition no longer tells the reader **which document now owns the present-tense claim**.

Bad retirement:

```text
old plan -> archive
```

Better retirement:

```text
old plan
   -> RETIRED tombstone
   -> exact archived historical text
   -> named current replacement authority
```

Without the replacement pointer, an LLM may retrieve the archived plan and reconstruct current behavior from obsolete future-tense assumptions.

### 4.5 Identity disappearance

A document is copied, summarized, regenerated, or moved in a way that loses the identity needed to establish what historical object is being referenced.

Examples:

- an archive copy silently edited while presented as the historical packet;
- a summary claims to preserve an old contract but cannot identify the source revision;
- a moved document points to a mutable branch when the claim depends on an exact historical state.

For historically significant material, preserve either the exact Git history/path or an exact archived blob whose provenance is explicit.

## 5. The disappeared-document negative claim

A useful Negative Claim for documentation work is:

```text
"I cannot find this document/concept in the new navigation"
    -/->
"the document/concept is obsolete"
```

Absence from the new surface establishes at most a retrieval observation.

The correct next questions are:

1. Did the file move?
2. Was it retired?
3. Was its role superseded?
4. Is it still referenced by tests, manifests, skills, playbooks, workflows, or other contracts?
5. Does another current document own the same claim?
6. Was a semantic anchor accidentally dropped?
7. Is the missing item historical evidence that must remain retrievable even though it is no longer current instruction?

Until those questions are resolved, the lifecycle status is `UNKNOWN`, not `REMOVED` or `OBSOLETE`.

## 6. Safe lifecycle states

The documentation index currently uses lifecycle classes such as:

```text
CANONICAL
OPERATING
ROAD
IMPLEMENTATION REFERENCE
RETROSPECTIVE
RETIRED
DERIVED
```

A safe transition should be explicit.

Examples:

```text
ROAD -> IMPLEMENTED -> RETIRED design packet

OPERATING v1 -> RETIRED tombstone -> OPERATING v2

CANONICAL old contract -> superseded historical record -> CANONICAL new contract

RETROSPECTIVE -> RETROSPECTIVE
```

Age alone is not a transition condition.

A retrospective is not stale merely because it is old. A future-tense implementation plan becomes stale when the implementation has landed and the plan still reads like a current instruction packet.

## 7. Tombstones are context-safety devices

A tombstone is not bureaucratic decoration. It is a fail-safe response to stale retrieval.

A good tombstone says at minimum:

```text
RETIRED
not current instruction
why it was retired
what current authority replaces it
where exact historical content is preserved
```

This protects several consumers simultaneously:

- humans following old links;
- search engines;
- repository code search;
- LLM retrieval;
- old issues/PRs that link the former path;
- protected-capability provenance that still names the historical file.

The tombstone converts a stale retrieval result from an ambiguous old instruction into an explicit lifecycle state.

## 8. Why archive-only moves are insufficient

Moving an obsolete packet directly to `archive/` can remove it from normal navigation but does not guarantee safe interpretation.

Potential failure:

```text
old issue links docs/OLD-PLAN.md
        ↓
path now 404s
        ↓
agent searches repository for similar title
        ↓
finds archive/OLD-PLAN.md
        ↓
no lifecycle marker
        ↓
uses old plan as present instruction
```

Preferred shape:

```text
docs/OLD-PLAN.md
    = short RETIRED tombstone

archive/OLD-PLAN.md.retired
    = preserved historical text

ROAD/INDEX.md
    = lifecycle record + current replacement authority
```

## 9. Experience from the ROAD/index cleanup

The documentation cleanup that introduced `ROAD/INDEX.md`, ROAP, and retired design packets exposed a useful failure mode.

The first shortened `docs/README.md` remained syntactically valid and retained most topic links, but full contract testing found that three required semantic anchors had disappeared from the live index surface:

```text
eha.ndjson
semantic-continuity criterion
semantic surface -> claim reconciliation -> evidence
```

The underlying EHA and semantic-refit documents still existed. The failure was therefore not physical deletion.

It was **semantic/navigational disappearance**.

The important lesson is:

> A documentation reorganization can preserve files and links while still changing the epistemic surface seen by agents.

This is why documentation verification cannot be reduced to `all Markdown links resolve`.

## 10. What the failed check proved

The failed checks did not prove a runtime regression.

They proved narrower documentation contract regressions:

```text
current docs entry point
    no longer exposed required EHA authority marker

current docs entry point
    no longer exposed required semantic-refit terminology/formula
```

The repairs restored those semantic anchors on new exact documentation heads.

This is a useful example of evidence scoping:

```text
docs contract failure
    != runtime failure

runtime matrix success
    != proof that documentation context is complete
```

Each claim needs the authority and test appropriate to the property being asserted.

## 11. Pre-retirement inventory

Before retiring, moving, or substantially shortening a documentation file, inspect:

### 11.1 Inbound references

Search for the path and distinctive normative phrases in:

- root/documentation indexes;
- tests;
- machine-readable registries;
- workflows;
- Skills and Playbooks;
- Commands and agent prompts;
- issues/PR references where practical;
- other canonical contracts.

A reference from a test or machine-readable registry changes the risk classification. The file is no longer "just prose" for verification purposes.

### 11.2 Role and authority

Determine whether the file is:

- current authority;
- operating guidance;
- implementation reference;
- roadmap/design;
- retrospective;
- derived presentation;
- already retired.

### 11.3 Unique semantic content

Identify concepts that are not safely duplicated elsewhere.

Useful signals:

- exact formulas;
- authority statements;
- STOP conditions;
- Negative Claims;
- must-not constraints;
- literal command/path identity;
- exact-SHA semantics;
- ownership boundaries;
- terms asserted by contract tests.

## 12. Retirement/reorganization protocol

```text
freeze exact starting SHA
        ↓
classify document role
        ↓
find inbound references and machine consumers
        ↓
identify replacement authority
        ↓
identify unique semantic anchors
        ↓
preserve historical text if useful
        ↓
write RETIRED tombstone when old path should fail safe
        ↓
update navigation/lifecycle ledger
        ↓
run documentation-specific verification
        ↓
classify residual uncertainty
```

Do not delete first and search for consequences afterward. Filesystems are wonderfully obedient that way.

## 13. Verification layers

### Layer A: changed-path eligibility

Prove whether the delta is truly documentation-only.

A `DOCUMENTATION-ONLY` claim is invalid if the change also touches:

- runtime/source code;
- workflows;
- dependency/version manifests;
- machine-consumed registries;
- OpenCode Skills/Playbooks/Commands/tools/policy;
- executable scripts;
- generated runtime data.

### Layer B: path continuity

Verify:

- internal Markdown links resolve;
- tombstone paths exist;
- archive targets exist;
- replacement authority links exist.

### Layer C: semantic continuity

Run contract tests that assert concepts, not merely files.

Examples in the current repository include checks that require the docs index to retain EHA and semantic-refit invariants.

### Layer D: authority continuity

For each retired current-purpose document, verify that a live replacement authority is explicitly named.

### Layer E: historical integrity

When exact historical text is promised, verify that the archived artifact corresponds to the historical source rather than a rewritten summary masquerading as the original.

## 14. Reduced documentation-only verification

For an eligible prose-only delta, a reduced profile is preferable to blindly spending a full runtime matrix while still failing to test the actual documentation property.

Minimum claim:

```text
DOCUMENTATION-ONLY PASS
```

Suggested evidence:

```text
exact docs head SHA
changed-path proof
internal-link/docs contract test
focused semantic contract tests
retirement/tombstone/archive checks
no runtime/config/workflow delta
```

The claim remains narrow:

```text
DOCUMENTATION-ONLY PASS
    -/-> full repository acceptance
    -/-> EHA PASS
    -/-> SIB promotion
```

If the ordinary full workflow runs automatically, its result is useful additional evidence, but it does not change the logical scope of the documentation-only claim.

## 15. Escalation rules

Escalate beyond the reduced profile when any of the following is true:

- a machine-consumed documentation/registry file changed;
- a prompt/Skill/Playbook/Command changed;
- a normative document changed an accepted operational behavior rather than merely its explanation;
- the documentation change exposes a possible implementation/document mismatch;
- executable examples or generated configuration changed;
- a release/SIB/EHA contract changed materially;
- the retirement operation cannot identify a replacement authority for a present-tense claim.

## 16. Relationship to Context Epistemics

Document lifecycle is an instance of context invalidation management.

A retrieved context item should not be admitted into decision-bearing context merely because its path exists.

The lifecycle state contributes to at least:

```text
freshness
scope
invalidation state
relationship to current target identity
authority
```

A `RETIRED` document may remain admissible as historical evidence while being inadmissible as current instruction.

That distinction should eventually be machine-visible to context retrieval.

## 17. Relationship to prompt injection

A stale or historical document can unintentionally behave like an injection even without an attacker if it contains imperative language and the model mistakes target relevance for instruction authority.

Therefore retirement also reduces an instruction-confusion surface:

```text
historical content belongs to repository
    -/->
historical content may instruct current agent
```

A tombstone and lifecycle index provide explicit negative context against that inference.

## 18. Relationship to ROAP

ROAP treats remote operator reports as claims rather than host authority. Documentation lifecycle assurance applies the same discipline to referenced documents.

If an operator report says:

```text
"I followed docs/OLD-RUNBOOK.md"
```

and that path has disappeared or been retired, the reviewer must establish:

- which historical object was meant;
- whether it was current for the target identity at execution time;
- whether a replacement authority existed;
- whether following it was permitted;
- what externally observable effects corroborate the operation.

A missing document reference in an operator report is therefore an identity/freshness problem, not a reason to guess which runbook the operator probably meant.

## 19. Proposed future automation

Future tooling may make this discipline cheaper without creating a new documentation authority.

Useful derived checks include:

- enumerate removed/moved Markdown paths;
- find inbound repository references;
- detect files with future-tense status against already-landed implementation;
- verify every RETIRED tombstone names a replacement or explicitly states that no replacement is required;
- compare promised archived blobs with their historical source blobs;
- maintain a derived lifecycle inventory;
- retrieve relevant retired/negative knowledge when a model touches the superseding implementation.

Any such tool remains a validator/navigation aid. Git history and the named live contracts remain the underlying authorities.

## 20. Canonical working rule

Before removing documentation from the active context surface, answer three questions:

```text
What knowledge is being removed from current navigation?
What current authority replaces it?
What historical or negative knowledge must remain retrievable?
```

If any answer is unknown, the safe state is not `DELETE`.

It is:

```text
STOP_DOCUMENT_LIFECYCLE_UNPROVEN
```
