# Lessons Learned: Building the CodeSleuth 0.4.0 SIB2 Head

**Status:** engineering retrospective, not normative product authority  
**Accepted baseline discussed:** `2b0044cb61a698b31d179e59cc486990d217b134`  
**Acceptance level:** SIB0 + SIB1 + SIB2 by Exact-Head Acceptance  
**Canonical accepted run:** `33026013398`  
**Scope:** the integration, Semantic Refit, hardening, evidence, promotion, and branch-triage work that produced the first accepted 0.4.0 SIB2 composition.

This document records what actually happened while assembling the CodeSleuth 0.4.0 SIB2 head and what the project should remember from it.

It is deliberately a retrospective rather than another normative contract. Product, SIB, EHA, Protected Capability, lifecycle, release, and Semantic Refit documents remain authoritative for their respective subjects. This file preserves the engineering experience behind those rules so a future maintainer or coding agent does not have to rediscover the same failure modes by reenacting them.

The central conclusion is simple:

> The discipline was useful not because it created more process, but because it repeatedly prevented convenient, plausible, and wrong integration decisions.

Several times, the easiest operation was mechanically valid Git and semantically incorrect engineering. The final baseline is valuable partly because those shortcuts were rejected.

---

## 1. What the session was really doing

The superficial task sounded familiar: collect work spread across branches and pull requests, obtain one final head, test it, and prepare a release.

The actual repository state was more complicated. Valuable work existed across different architectural moments:

- protected-capability and SIB0 convergence;
- atomic Skill and Playbook staging;
- durable EHA state and release-candidate selection;
- TUI visual regression work;
- Semantic Refit documentation;
- pre-SIB hardening fixes;
- release-stream history;
- local and historical review reports containing negative knowledge;
- many already-absorbed integration, test-carrier, repair, and provenance branches.

The danger was not primarily merge conflicts. A clean merge could be more dangerous than a conflicted one because it could silently restore stale assumptions while giving the maintainer a comforting lack of red markers.

The real task therefore became:

1. identify the exact current semantic authority;
2. recover still-valid intent from divergent work;
3. separate claims, assumptions, mechanisms, evidence, and provenance;
4. reject obsolete mechanisms and stale authority;
5. implement the surviving intent in current-native form;
6. preserve negative knowledge and attribution;
7. test the exact resulting composition;
8. keep failed candidates failed;
9. promote only the literal accepted identity where possible;
10. freeze SIB2 before resuming ordinary growth;
11. triage the remaining branch population against that accepted baseline.

That became the practical meaning of Semantic Refit in CodeSleuth.

---

## 2. The important identities

Several commits matter because the session repeatedly demonstrated that a tree, a branch name, and an acceptance claim are not interchangeable.

Important points in the final lineage included:

- `1778209716d3bb54d8d9aaabbcaa8ffaf8707cf0` — protected-capability/SIB0 lineage after the docs-only Playbook/Skill composition refit;
- `33fe1b303283db0e6914521daea7f747853271cf` — first landed EHA/Packet-B refit candidate, later rejected in review;
- `bb5b2fbe342dbff93f5d31469b93d84600b8c352` — repair candidate that still failed the visual gate;
- `2b05a12e3d68c2a93ec7c448ec36411c99849550` — corrected repair candidate with six-job acceptance success;
- `a7522943a277c5fccf314188670ce2a867184796` — hardened integration assembly after Semantic Refit docs and state/MCP repairs, six-job accepted;
- `2b0044cb61a698b31d179e59cc486990d217b134` — release-stream composition later accepted through SIB0, SIB1, and SIB2 EHA;
- `65f0946bcf7e33b256e9ce312ac6466062b64c22` — a later release-readiness documentation commit with its own green acceptance, intentionally not used to mutate the already accepted SIB2 identity before manual product testing.

The accepted SIB2 target was:

```text
2b0044cb61a698b31d179e59cc486990d217b134
```

After deliberate promotion, the principal refs were aligned to the same object:

```text
SIB
main
dev/release-0.4.0
        |
        v
2b0044cb61a698b31d179e59cc486990d217b134
```

That topology was not cosmetic. It avoided creating a new synthetic commit merely to say that an already accepted composition had been promoted.

---

# 3. Exact identity is part of correctness

This was the most repeatedly useful rule of the session.

A common shortcut is:

> The tree is the same, therefore the evidence is the same.

That is not sufficient for Exact-Head Acceptance.

The effective evidence identity is closer to:

```text
exact SHA
+ acceptance profile
+ required environments/jobs
+ actual PASS results
= claimable evidence
```

not merely:

```text
similar content + old green CI = probably fine
```

This mattered several times.

## 3.1 Historical CI was provenance, not inherited acceptance

Older release-stream work had strong CI evidence. It proved the source packet was real, exercised, and worth taking seriously.

It did **not** prove the new refit composition.

Once EHA behavior was reorganized under the atomic Skill/Playbook architecture, the composition had changed. The mechanism responsible for acceptance itself had changed. Inheriting acceptance from the pre-refit implementation would have been circular.

## 3.2 Tree-equivalent objects can still have different evidence identities

When assembling the release stream, a two-parent merge commit was used to preserve both the previous release lineage and the selected accepted assembly tree.

The selected tree matched the accepted assembly, but the merge commit had a different SHA.

Therefore it received its own acceptance.

Git was correctly representing a new historical object. The evidence model had to respect that fact instead of pretending content equivalence erased commit identity.

## 3.3 Fast-forward is a promotion primitive

Later, when `main` remained a strict ancestor of the accepted SIB2 head, promotion did **not** need another merge commit.

The correct operation was a non-force fast-forward directly to:

```text
2b0044cb61a698b31d179e59cc486990d217b134
```

This preserved:

```text
SIB == dev/release-0.4.0 == main
```

without inventing a new object and then needing to re-prove it.

The important qualification is ancestry. Fast-forward was correct because `main` was verified to be behind the accepted head with no divergent commits.

A useful default follows:

> When promotion can preserve the literal accepted SHA through a verified fast-forward, prefer that over manufacturing a merge commit for ceremony.

---

# 4. Semantic Refit is not a prettier spelling of cherry-pick

The session produced a concrete example of why the term is useful.

One source packet contained atomic Skill/Playbook infrastructure. Another contained durable EHA, release-head selection, visual acceptance, and an older EHA workflow organization.

A mechanical integration order could have been:

```text
old SIB lineage
-> bring in EHA packet
-> bring in atomic Playbooks
```

That would have created an intermediate state where the newly accepted composition contract was violated by an old monolithic whole-campaign EHA Skill.

The correct order became:

```text
Packet A: atomic Skills + Playbooks
        |
        v
current orchestration semantics
        |
        v
Packet B: durable EHA refit into that model
```

The old EHA behavior survived.

The old EHA packaging did not.

Specifically:

- durable evidence intent survived;
- exact-target identity survived;
- release-head selection survived;
- visual-gate intent survived;
- EHA repair semantics survived;
- the monolithic campaign Skill was retired;
- the workflow was re-expressed as Playbooks, Steps, and atomic Skills.

A cherry-pick asks whether source changes can be applied.

Semantic Refit asks what the old work was trying to make true, which of those claims are still required, and what current-native change should make them true now.

Those are different questions.

---

# 5. The useful unit of preservation is the claim, not the hunk

One old commit can simultaneously contain:

- still-required behavior;
- obsolete mechanism;
- stale documentation;
- a valid test idea;
- an invalid test assumption;
- useful negative knowledge;
- historical provenance worth preserving.

These components may deserve different outcomes.

Therefore the semantic review unit is closer to:

```text
claim
invariant
user journey
authority boundary
compatibility obligation
forbidden state
bound
```

than to:

```text
commit
file
hunk
```

Git remains essential for provenance and topology. It simply does not define the semantic granularity of integration.

---

# 6. Semantic status and delivery action must be separate

One of the strongest refinements was recognizing that labels such as `REAPPLY`, `REFIT`, `SUPERSEDED`, and `DROP` can mix two independent questions:

1. What is true about the historical claim now?
2. What implementation action should be taken now?

A claim may remain **REQUIRED**, while delivery could be:

- REUSE;
- PORT / ADAPT;
- REIMPLEMENT;
- NEW CHANGE;
- NO CHANGE;
- DEFER;
- BLOCK.

A claim may be **SUPERSEDED** because the target already satisfies it, with delivery **NO CHANGE**.

A claim may be **RETIRED** only because current authority explicitly no longer requires it, not because porting it is inconvenient.

A vague `DROP` can otherwise conceal several very different states:

- deliberate retirement;
- actual supersession;
- implementation difficulty;
- misunderstanding;
- lack of investigation.

Only the first two are legitimate semantic outcomes, and both need evidence.

The better ledger shape is:

```text
source claim
-> semantic status
-> delivery disposition
-> target evidence
```

not merely “what happened to this old file?”

---

# 7. Target authority outranks source convenience

This rule saved the integration repeatedly.

Several useful branches were based on older `main` states. Their files were coherent in their original context but newer branches contained stronger contracts and newer ownership semantics.

The wrong heuristic is:

> The old file applies cleanly, therefore use it.

The correct heuristic is:

> Current accepted target semantics are authority. Historical work supplies intent, evidence, provenance, negative knowledge, and implementation ideas.

This is why the Semantic Refit documentation branch itself was not simply merged from a stale base. Its useful concepts were extracted and adapted to current docs and current EHA operating semantics.

The Semantic Refit document itself requiring a Semantic Refit was not merely amusing. It was a useful self-test of the discipline.

---

# 8. Do not repair while performing acceptance

Acceptance and repair are different roles.

The separation used here was:

```text
candidate
-> tester
-> PASS or FAIL

FAIL
-> preserved failed SHA
-> separate repair activity
-> new SHA
-> new acceptance
```

A tester who repairs while testing destroys the meaning of the campaign because the target is no longer the object that entered the campaign.

The final EHA tester role explicitly prohibited:

- source edits;
- test edits;
- documentation edits;
- commits;
- amend;
- cherry-pick;
- merge;
- rebase;
- repair-in-place.

If a blocker appeared, the tester had to record evidence, record the appropriate failure, and stop.

This matters especially with coding agents. Their natural instinct is to be “helpful” by immediately fixing a defect. During acceptance, that helpfulness is evidence destruction.

---

# 9. A failed SHA must remain failed

The first EHA refit exposed a subtle state-model defect.

The durable ledger was append-only, but the read model selected the latest verdict for each SIB level. Nothing initially prevented:

```text
SIB1 FAIL
SIB1 PASS
```

inside one campaign.

The storage history was append-only, but the **semantic result** could still be rewritten by appending another verdict.

This produced an important lesson:

> Append-only storage does not automatically imply immutable meaning.

The implementation was changed so a verdict for a `(campaignId, SIB level)` becomes immutable after first recording. Regressions were added for:

- `FAIL -> PASS` rejection in the same campaign;
- second-campaign rehabilitation of the same failed target within the same durable ledger;
- preservation of the failed read model after later events.

The project-level rule is stronger and simpler:

> Repair creates a new candidate identity. It does not reinterpret a failed candidate.

Without this, EHA would eventually become a ceremony in which failures can be narrated into success without changing the tested object.

---

# 10. Acceptance infrastructure is product infrastructure

Another defect appeared not in product logic but in the workflow trigger.

The new integration branch did not initially receive a fresh acceptance run because the workflow's push filters did not include:

```text
integration/**
```

That meant the project had a rule saying exact integration heads require acceptance while its own automation silently ignored the branch family used to build them.

The correction included both the trigger and executable structural protection.

The lesson is straightforward:

> A gate that does not run is not a gate.

And slightly more importantly:

> CI configuration is part of the acceptance system and deserves regression protection like any other product-critical component.

---

# 11. Visual regression caught what review missed

A repair candidate fixed the major EHA semantics and looked substantially correct.

Five canonical jobs passed.

The TUI visual job failed.

The reason was tiny: the test expected mojibake text:

```text
Tools ┬À OpenCode-native capabilities
```

while the real product correctly rendered:

```text
Tools · OpenCode-native capabilities
```

The previous repair had even claimed UTF-8 cleanup.

The visual gate therefore proved that the cleanup was incomplete across all maintained surfaces.

Several lessons followed:

1. A small failure still invalidates the exact candidate when the gate is canonical.
2. The correct fix was the corrupt test, not corrupting the product string to satisfy it.
3. A prose claim like “encoding cleanup complete” is weaker than a relevant executable oracle.
4. “Visual” tests can protect semantic consistency, not just aesthetics.

---

# 12. Do not weaken the oracle to promote the candidate

A docs-contract test initially failed because it asserted convenient literal wording rather than the actual normative requirement.

Two bad repairs were available:

- weaken the semantic requirement until the candidate passes;
- rewrite normative prose merely so the test finds its favorite sentence.

Instead, the test was corrected to bind to real normative clauses:

- implementation may change freely;
- Git conflict count does not determine semantic correctness;
- `DROP` is ambiguous;
- `DROP` cannot be a shortcut for requirement deletion.

This is the distinction between **test hardening** and **test gaming**.

A good test repair makes the oracle more faithful to authority.

A bad repair makes authority easier for the current candidate.

---

# 13. Negative knowledge is a first-class asset

After SIB2 acceptance, a historical report branch looked unsuitable as a delivery object because it contained a self-installed `.opencode/` tree and local report material.

It would have been easy to declare the entire branch junk.

Instead, findings were independently rechecked against the accepted SIB2 tree.

Some historical findings were already repaired:

- MCP slurp-before-cap;
- review ID collision and stale findings reuse;
- compaction crash on corrupt state;
- old README/version drift.

Other findings still reproduced on SIB2:

- TUI worker/DOM boundary issues;
- installed Verify manifest weaker than source smoke manifest;
- MCP overview bounded collections without explicit truncation signal;
- `generic.json` packaging parity drift;
- README claim about profile `extends` without demonstrated resolver behavior;
- zero-commit repository inventory requiring an existing `HEAD`.

Those surviving findings were moved into a durable issue before the report branch was classified for deletion.

General rule:

> Delete stale delivery refs only after extracting any unique negative knowledge they still contain.

A branch can be obsolete as code and still valuable as evidence.

---

# 14. Negative claims need constructive counterparts

Post-SIB2 Semantic Refit work developed the next useful refinement.

A naked prohibition such as:

```text
DO NOT create a second update authority.
```

is weaker than a structured record containing:

```text
Forbidden state:
    two independent authorities can make authoritative update/restart decisions

Constructive invariant:
    exactly one accepted authority owns update/restart decisions

Violation witness:
    two components can independently issue conflicting authoritative decisions

Scope:
    supported update/restart paths

Oracle:
    architecture inspection plus targeted failure/concurrency tests
```

The constructive invariant tells an implementer what valid state should exist. The violation witness tells a reviewer what to actively try to produce.

This is especially useful in LLM-driven development, where a naked `DO NOT X` written thousands of tokens earlier can become a remarkably fragile memory mechanism.

The next accepted Semantic Refit contract cycle should preserve material negative claims, where practical, as:

```text
forbidden state
+ constructive invariant
+ violation witness
+ scope
+ oracle
+ provenance
```

Finite happy-path tests do not prove a universal negative.

---

# 15. Bounded behavior must be bounded at the real boundary

The MCP adapter provided a representative example.

Its contract described bounded evidence reads, and it rejected evidence files larger than the configured cap.

But the old implementation effectively performed:

```text
read entire file
-> measure payload
-> reject if too large
```

The response was bounded.

The I/O and allocation were not.

The corrected implementation reads at most:

```text
MAX_FILE_BYTES + 1
```

before deciding whether to reject.

The regression checks the actual read size so implementation cannot quietly return to whole-file allocation while preserving the same outward error.

Broader rule:

> A bounded contract must be enforced at the resource boundary it claims to bound, not only at the final serialization boundary.

This applies to memory, files, pagination, retries, concurrency, context projection, and tool output.

---

# 16. Durable identity needs collision semantics, not only unique-looking names

Review-state IDs originally combined time, HEAD, and session-related material. Under a rare rapid repeated start, two review starts could reuse the same directory.

The dangerous part was not only duplicate-looking IDs. Directory creation semantics allowed an existing directory to be reused, so stale findings could survive into what looked like a fresh review.

The fix therefore needed two properties:

1. stronger collision resistance;
2. collision-fail-closed directory creation rather than silent reuse.

General rule:

> Durable identity should have both collision resistance and explicit collision behavior.

A random-looking identifier with reuse-friendly storage semantics is not enough.

---

# 17. Fail-soft must be explicit about degraded evidence

The compaction hook originally parsed durable JSON state and NDJSON findings directly. A torn/corrupt checkpoint or one malformed findings line could crash compaction.

The hardened path preserves valid evidence where possible:

- corrupt state does not crash the compaction path;
- one malformed finding does not destroy valid neighboring findings;
- the resulting context explicitly warns that evidence completeness is degraded.

That last point matters.

Fail-soft must not mean:

> catch everything and pretend the data is complete.

That merely converts visible failure into invisible evidence loss.

The safer pattern is:

> preserve valid evidence, degrade gracefully, and state the degradation explicitly.

---

# 18. Documentation can be authority, evidence, or stale cargo

The session contained all three.

## Authority

Current contracts were used to determine what historical implementation intent still belonged in the product.

## Evidence

Historical docs helped recover what old branches were trying to accomplish.

## Stale cargo

One refit retained old wording that described `eha-sib-acceptance` as a Skill after the current architecture had refit it into a Playbook using atomic Skills.

Runtime semantics had moved. One accompanying claim had not.

That small mismatch was a precise example of incomplete Semantic Refit.

The lesson is:

> Documentation must be classified by authority and time just like code.

Copying old prose is no safer than copying old implementation.

---

# 19. Local state and remote state are separate authorities

A local report said a worktree was synchronized and contained only specific untracked draft Playbooks.

That report was valid when produced.

Later, the remote branch was fast-forwarded independently, making the local “matches origin” statement stale.

The correct distinctions were preserved:

- GitHub could verify remote refs;
- GitHub could not verify the user's current local untracked state;
- untracked draft Playbooks were intentionally not touched;
- local `.codesleuth/reports/` content was not claimed reviewed unless supplied or committed.

This sounds elementary but automation often blurs it.

A remote integration agent must not claim current facts about untracked local files because an earlier local report mentioned them.

A local coding agent must fetch before assuming an earlier remote head is still authority.

---

# 20. Protect known untracked user work explicitly

The user's worktree contained untracked draft Playbooks that were deliberately outside the frozen candidate.

The integration instructions named them and explicitly prohibited:

- `git reset --hard`;
- `git clean`;
- deleting them;
- accidental `git add .` capture;
- using the existing worktree as the risky assembly workspace.

A separate worktree/branch was preferred.

General rule:

> When known untracked work exists, preservation should be an explicit integration invariant, not a vague request to “be careful.”

Name the files and the dangerous operations.

---

# 21. Separate integration branches are useful only while they have a job

`integration/final-sib-candidate` was useful while divergent packets were being assembled and tested.

After SIB2 promotion it had no unique commits ahead of the accepted baseline. It became a historical assembly ref.

The same was true for many impressive-sounding branches that were in fact:

- entirely behind SIB2;
- alternate histories of code already absorbed;
- test-carrier refs;
- repair candidates;
- source packets whose semantics had already been refit.

Branch names are not authority.

Ancestry, unique semantic delta, current claims, and preserved provenance are.

---

# 22. Large branch triage should happen after a real baseline exists

Classifying sixty-plus branches while target semantics were still moving would have created repeated work and ambiguous conclusions.

Once SIB2 existed, triage became much cheaper:

```text
for each branch:
    compare to SIB2
    determine ahead / behind / diverged
    inspect unique current semantic delta
    preserve unique negative knowledge
    classify KEEP / DEFER / PROVENANCE / DELETE
```

This produced three useful categories.

## Permanent authority refs

- `SIB`;
- `main`;
- `dev/release-0.4.0` during the release cycle.

## Real post-SIB2 deltas

- release-readiness documentation;
- later Semantic Refit negative-claim work;
- deferred naming cutover.

## Historical/provenance/delete queue

Everything else after checking for unique knowledge.

General lesson:

> Establish one accepted semantic baseline before doing serious branch archaeology.

Without it, every comparison is against a moving target.

---

# 23. Git-divergent does not necessarily mean semantically unabsorbed

One refit branch showed divergent Git history and unique commits relative to SIB2.

A superficial triage script could classify it as active work.

But the key Textual bootstrap file had the same blob SHA on the branch and on SIB2. The divergent commits represented an alternate path to code already present in the accepted product.

Therefore:

```text
Git divergent != semantically unabsorbed
```

The converse also matters:

```text
Git behind != safe to delete without checking unique external knowledge
```

The graph is a powerful filter, not final semantic authority.

---

# 24. Historical report branches should be mined, not merged

The old deep-review branch supplied a useful pattern:

```text
historical report branch
-> extract findings
-> reproduce against accepted SIB2
-> classify repaired / live / obsolete
-> move surviving knowledge to durable issue
-> retire branch as delivery candidate
```

This is another legitimate form of Semantic Refit.

The source artifact's delivery form was retired.

Its valid negative claims survived.

---

# 25. Test-carrier refs can preserve exact identity

When a candidate branch family did not naturally trigger the required workflow, a temporary test-carrier branch could point to the exact same candidate commit.

Creating another ref does not create another commit.

That allows a branch-triggered workflow to run while preserving:

```text
candidate SHA == tested SHA
```

This is preferable to creating a meaningless no-op commit merely to wake CI.

Carrier refs are infrastructure, not new candidates, and should later be triaged accordingly.

---

# 26. SIB acceptance and release acceptance are different claims

SIB2 answered whether the exact composition was architecturally complete, minimally implemented across the frozen capability classes, and integrated under the canonical acceptance profile.

It did not prove every release concern.

Release validation still includes human and repository-admin concerns such as:

- real workstation installation;
- real provider-backed OpenCode use;
- manual TUI journeys at representative viewport sizes;
- real update/restart behavior;
- uninstall/restoration;
- GitHub branch/ruleset protection;
- final immutable tag and release publication.

The process deliberately kept these separate.

This prevented “SIB2 PASS” from quietly turning into “every meaningful human workflow has been personally observed.”

---

# 27. Machine evidence must not impersonate human evidence

The EHA report explicitly recorded residual limitations.

Automation did not prove:

- every manual TUI journey;
- real provider credentials;
- production install/bind/unbind on operator machines;
- Windows visual regression;
- every historical branch delta outside selected release history.

That honesty is part of the acceptance result.

The useful model is:

```text
machine-verifiable claim
-> executable gate

human/operational claim
-> manual validation

unknown claim
-> recorded as unknown
```

The unhealthy model is treating a green CI badge as a universal truth token.

---

# 28. Testing from real `main` improves installer fidelity

After SIB2 was accepted, `main` was fast-forwarded directly to the same accepted SHA.

This made installer and self-update testing more representative because parts of the product depend on real repository topology and default-branch behavior:

- default source ref;
- `origin/main` update behavior;
- installer metadata;
- source-checkout update mode;
- release/main naming assumptions.

Testing only from an internal integration branch can miss these.

The safe promotion was possible because the exact accepted identity could be preserved.

---

# 29. Post-SIB release polish is allowed, but it creates a new candidate

A later release-readiness documentation commit had its own green six-job acceptance.

It was still intentionally kept separate from the immediate SIB2 manual-test identity.

Even a docs-only change creates a new SHA.

If the release branch advances to it, the release candidate has changed and needs fresh exact-head release evidence.

The honest state transition is:

```text
accepted SIB2 head
-> post-SIB release-only change
-> new SHA
-> fresh release acceptance
```

not:

```text
branch name stayed the same
-> old evidence magically follows
```

---

# 30. Normative discipline should be executable where practical

Several improvements became durable only after receiving tests or executable checks:

- EHA verdict immutability;
- integration branch workflow coverage;
- Playbook manifest/DAG/reference structure;
- atomic Skill contracts;
- protected-capability registry integrity;
- MCP bounded reads;
- review-state collision behavior;
- corrupt-state compaction behavior;
- TUI visual behavior;
- Semantic Refit documentation clauses.

A prose rule can guide a careful maintainer.

An executable rule can also catch a future maintainer who never read it.

The preferred pattern for important invariants remains:

```text
normative contract
+ executable regression/oracle
```

Not every sentence belongs in a test, but repeatedly violated or release-critical invariants deserve serious executable protection.

---

# 31. Do not turn the forbidden-regression registry into a bug tracker

The opposite failure is possible.

Several hardening defects were concrete witnesses of broader existing forbidden regressions.

Creating a new `FR-*` entry for every implementation bug would make the registry noisy and less useful.

The better question is:

> Is this a genuinely distinct must-not-return product or architecture state, or a new executable witness for an existing forbidden regression?

A registry should preserve durable negative semantics, not become a bug tracker with JSON braces.

---

# 32. The host owns orchestration execution; CodeSleuth owns discipline

Atomic Skills and Playbooks could easily have grown into a second workflow runtime.

They did not.

The accepted ownership model remained:

```text
OpenCode / host
    owns controller, model session, child sessions, execution, tool routing

CodeSleuth
    owns Playbook definitions, Step contracts, Skills, evidence discipline,
    bounded tools, reports, lifecycle UX, and acceptance conventions
```

A Playbook describes multi-step work.

It does not imply a CodeSleuth scheduler, daemon, workflow database, second controller, or model runtime.

This boundary is worth repeatedly checking because “we need a workflow” is a reliable way for software to accidentally acquire a second execution plane.

---

# 33. Atomic Skills improved refit quality, not merely organization

Breaking giant procedures into atomic Skills had benefits beyond tidy directories.

It allowed EHA and review workflows to reuse distinct competencies such as:

- exact target identity;
- candidate selection;
- campaign evidence;
- repair protocol;
- contract triangulation;
- dependency impact closure;
- forbidden-regression handling;
- acceptance matrix design.

This made it easier to inspect whether a Step had one decidable objective and bounded output.

It also made Semantic Refit easier because old workflow intent could be mapped onto current competencies rather than carried as one indivisible prompt blob.

A monolithic prompt entangles mechanism, order, policy, and reasoning. Atomicity makes intent easier to preserve while mechanisms evolve.

---

# 34. Large prompts become Playbooks only when steps have real boundaries

Local draft SIB0/SIB1 mega-prompts were intentionally **not** committed into the accepted baseline merely because they existed.

That was correct.

A long prompt does not become a good Playbook by slicing it every few hundred lines.

A useful Step needs:

- independent objective;
- declared input;
- bounded output;
- stop condition;
- declared atomic Skills;
- an actual reason for its isolation boundary.

Those drafts should be migrated later against the accepted framework, not smuggled into the baseline as unexamined local material.

---

# 35. “Already green” is a dangerous integration phrase

Several source packets were green.

Several ancestors were green.

One repair parent was mostly green.

None of those facts replaced exact-target evidence.

“Already green” must always be completed with:

```text
which exact SHA?
which profile?
which environments?
which claim?
before or after which refit?
```

Without those qualifiers, the phrase conveys confidence while saying very little.

---

# 36. A failed gate is useful information, not a promotion obstacle

The process became healthier when failures were treated as facts rather than inconveniences.

Examples included:

- visual mojibake mismatch;
- docs-contract assertion mismatch;
- missing integration-branch workflow coverage;
- review findings on the first EHA refit.

The objective was not “make CI green.”

The objective was “learn whether this exact candidate satisfies the intended contract.”

Green was the consequence, not the optimization target.

This distinction matters because optimizing directly for green encourages skips, weakened tests, and semantic drift.

---

# 37. Exact-head discipline improves repair history

A healthy repair sequence looked like:

```text
candidate A
-> finding / failure

candidate B
-> new SHA
-> fresh run
-> still FAIL

candidate C
-> new SHA
-> fresh run
-> PASS
```

The failed objects remain inspectable.

This is much more useful than repeatedly amending one branch tip until the final history contains only a mysterious green endpoint.

The preserved sequence tells future maintainers:

- what was wrong;
- what repair attempted to change;
- what still failed;
- which candidate first passed the complete oracle.

---

# 38. Commit topology can express governance decisions

Git history was used not only for versioning but to express integration intent.

Examples:

- fast-forward promotion preserved an accepted exact identity;
- a two-parent release merge preserved both historical release lineage and selected assembly ancestry;
- separate repair commits preserved failed candidates;
- test-carrier refs triggered workflows without altering candidate identity;
- SIB promotion used a ref move rather than content mutation.

The lesson is not to fetishize history shape.

It is that history shape can support or undermine evidence semantics.

Merge strategy should therefore be chosen with acceptance identity in mind, not only repository habit.

---

# 39. Branch cleanup is not Semantic Refit

Once a branch's useful semantics have been absorbed and its unique negative knowledge extracted, deleting the ref is repository hygiene.

It does not need a philosophical refit ceremony.

Conversely, calling every branch cleanup a Semantic Refit would dilute the term until it meant any Git operation involving old code.

Keep the distinctions:

```text
Semantic Refit
    reconcile meaning across changed semantic environments

Branch triage
    determine whether a ref has unique current value

Branch deletion
    remove an unnecessary pointer after provenance/knowledge is safe
```

---

# 40. Semantic Refit has a stop condition

The technique should not be used everywhere.

If source and target semantics are still aligned and a normal merge, rebase, cherry-pick, or port faithfully preserves the intended behavior, use the ordinary operation.

Semantic Refit becomes valuable when historical organization no longer maps cleanly to current semantic authority.

Useful signals include:

- source assumptions changed;
- target independently implemented part of the intent;
- ownership boundaries moved;
- old tests encode old architecture;
- source files disappeared;
- an old mechanism conflicts with current capability ownership;
- one old patch maps to several current components;
- several old patches collapse into one current implementation;
- a branch contains valuable knowledge but is not a viable delivery object.

Using Semantic Refit for every routine clean port would turn a useful discipline into ceremony.

---

# 41. A refit must remain attributable

If implementation may change freely, a legitimate question appears:

> When does this stop being a refit and become unrelated new work inspired by an old branch?

The answer is traceability.

A defensible refit should allow a reviewer to answer:

- what historical claim was recovered;
- where it came from;
- whether it remains required;
- what current authority supports that status;
- where it is represented now;
- which mechanisms were deliberately retired;
- what evidence protects the current implementation;
- what remains uncertain.

The new code should not require the old branch in order to be understood.

But the integration record should still make it possible to understand **why the behavior exists and how historical intent survived**.

The desired tension is:

```text
target-native implementation
+ preserved provenance
```

not permanent dependence on old code and not erased history.

---

# 42. Praise is evidence too, but findings drive operations

Retrospectives naturally focus on defects. Several patterns from the session are worth deliberately repeating:

- EHA atomic Skills gained clear Input / Objective / Output / Stop / Must-not boundaries;
- EHA repair and EHA acceptance became separate Playbooks;
- reports remained derived views instead of becoming a second evidence database;
- OpenCode remained execution authority;
- promotions preserved exact identities when topology allowed it;
- stale source PRs were retained as provenance instead of merged for ceremonial closure;
- the six-job matrix supplied genuinely heterogeneous evidence;
- residual human-only limitations were stated explicitly rather than flattened into PASS.

These were not accidental niceties. They are patterns to keep.

---

# 43. One accepted baseline dramatically reduces cognitive load

Before SIB2, many branches could plausibly claim to contain the “latest good” version of some subsystem.

After SIB2, the default question became:

```text
How does this differ from SIB?
```

That turns a many-to-many comparison problem into a mostly one-to-many problem.

This is one of the strongest practical reasons to maintain a deliberate stable integration baseline even when `main` exists.

`main` answers where normal product history currently points.

`SIB` answers which exact composition has the strongest explicit integration claim.

Sometimes they coincide, as they do after this promotion. They still express different meanings.

---

# 44. Promote refs only after evidence exists

The `SIB` ref was not moved merely because CI looked green.

It was promoted after:

- SIB0 capability inventory was frozen;
- capability classes were represented;
- protected contracts preserved forbidden regressions;
- SIB1 minimum implementations were verified;
- SIB2 composition was assessed;
- exact-head six-job CI was green;
- the EHA campaign recorded SIB0 PASS, SIB1 PASS, and SIB2 PASS on the same SHA.

The ref move was a maintainer designation of evidence that already existed.

Moving `SIB` does not make a SHA accepted.

Acceptance evidence justifies moving `SIB`.

---

# 45. Repository-admin state is a separate authority from source state

Source documents can require branch protection.

They cannot make GitHub branch protection exist merely by describing it.

Repository rulesets were queried separately and were not configured at that time. That remained a release-admin concern even after source documentation correctly described the desired policy.

Authority distinction:

```text
source documents
    define desired repository governance

GitHub repository settings
    determine actual repository governance
```

A release checklist must inspect both.

---

# 46. Real distribution topology belongs in release testing

Once `main` was aligned to the accepted SHA, installer and source-checkout update testing became more representative because the product could exercise the topology users actually consume.

A practical release pattern follows:

1. establish accepted release/SIB candidate;
2. where safe, expose that exact identity on the real distribution/default branch without creating a new SHA;
3. perform real installer/update/manual journeys there;
4. finalize immutable tagging only after those checks.

This produces better operator evidence than testing exclusively from an internal branch.

---

# 47. Role separation was one of the strongest controls

The most effective division of work was asymmetric.

## Integration/controller role

- maintain the authoritative ledger;
- inspect GitHub state;
- compare exact commits;
- decide semantic dispositions;
- choose integration order;
- create and advance refs;
- review evidence;
- preserve identity;
- promote accepted heads.

## Local implementation/Cursor role

- perform bounded local Semantic Refit tasks;
- resolve code conflicts;
- write focused regressions;
- run local gates;
- return one clean candidate SHA.

## EHA tester role

- make no code changes;
- run established acceptance procedure;
- record PASS or FAIL;
- stop on blocker.

This reduced the chance that one agent would simultaneously define the requirement, implement it, reinterpret failure, and declare success.

That pattern generalizes beyond CodeSleuth.

---

# 48. What should be improved next time

The process worked, but it can be made cheaper and clearer.

## 48.1 Maintain a lightweight branch inventory earlier

Final semantic triage belongs after an accepted baseline exists, but a non-authoritative early inventory of source packets, repair refs, and obvious ancestors can reduce noise during integration.

Use two ledgers:

- early inventory, no deletion claims;
- post-SIB semantic triage against accepted baseline.

## 48.2 Require source-claim disposition in every refit handoff

Some disposition records had to be reconstructed during review.

Future refit handoffs should include a compact table:

```text
claim | source evidence | semantic status | delivery | target evidence
```

## 48.3 Treat workflow branch coverage as an explicit contract

The missing `integration/**` trigger should have been detectable from the beginning by a general workflow-contract test covering all branch classes used in the integration/release process.

## 48.4 Scan maintained text surfaces for known mojibake patterns

The visual failure showed that encoding cleanup can remain incomplete across tests/docs even when product text is correct. A cheap repository scan for known corruption markers can prevent recurrence.

## 48.5 Decide global versus review-local failed-SHA semantics explicitly

Current EHA hardening prevents rehabilitation inside the same durable review ledger. A future policy decision may still be needed on whether a SHA that failed in one review should be globally unclaimable across all review IDs.

That is a semantic policy decision and should not be smuggled into a small implementation patch.

## 48.6 Refit the post-SIB negative-claim protocol after the release cycle

The newer Semantic Refit branch introduced useful ideas around constructive invariants, violation witnesses, scope, and adversarial oracles. They should be integrated deliberately after 0.4.0 manual/release validation rather than rushed into the frozen release baseline.

## 48.7 Reduce duplicated declarative truth

The surviving `generic.json` parity drift and source-Smoke versus installed-Verify drift share a theme: duplicated manifests diverge.

Future hardening should prefer one canonical manifest with derived/projection surfaces where practical.

---

# 49. Recommended operating defaults distilled from the session

These are retrospective recommendations, not automatically normative merely because they appear here.

## Integration

1. Freeze source and target identities before refit.
2. Treat current accepted target contracts as semantic authority.
3. Recover source claims, assumptions, mechanisms, evidence, provenance, and negative knowledge separately.
4. Record semantic status independently from delivery action.
5. Prefer target-native implementation over source-file resemblance.
6. Preserve attribution even when no source code survives.
7. Do not weaken current contracts/tests merely to make stale work fit.

## Evidence

8. Historical CI is provenance, never automatic acceptance for a new composition.
9. Acceptance belongs to the exact tested SHA.
10. A failed SHA remains failed.
11. Repair produces a new SHA and fresh acceptance.
12. Acceptance workflow/configuration is protected product infrastructure.
13. Record machine-verifiable, human-verifiable, and unverified claims separately.

## Git topology

14. Prefer non-force fast-forward promotion when it preserves the exact accepted SHA and ancestry permits it.
15. Do not create no-op commits merely to trigger CI; use a carrier ref when appropriate.
16. Preserve failed candidates rather than amending them into green history.
17. Use merge commits deliberately when historical parentage matters, then accept the resulting new SHA.

## Negative knowledge

18. Before deleting historical refs, extract unique findings and negative knowledge.
19. Reproduce old findings on the current accepted baseline before carrying them forward.
20. Where practical, represent material negative claims as forbidden state + constructive invariant + violation witness/scope/oracle.
21. Do not turn every bug into a new top-level forbidden-regression ID if it is already a witness of an existing one.

## LLM role separation

22. Integrator decides authority, order, disposition, and promotion.
23. Coding worker performs bounded implementation/refit work.
24. Acceptance tester does not repair the candidate under test.
25. Reports and model summaries remain evidence aids, never stronger authority than verified source/contracts.

## Release

26. SIB2 is not synonymous with complete manual release validation.
27. Test installer/update behavior from realistic distribution topology.
28. Repository-admin controls must be checked in the actual hosting platform.
29. Any post-SIB release commit creates a new exact release candidate even when docs-only.
30. Tag only an exact `main` commit that has its required acceptance.

---

# 50. Compact Semantic Refit checklist

```text
IDENTITY
[ ] source exact SHA recorded
[ ] target exact SHA recorded
[ ] target authority identified

RECOVERY
[ ] source intent recovered
[ ] source assumptions identified
[ ] mechanisms separated from claims
[ ] negative knowledge preserved
[ ] provenance recorded

DISPOSITION
[ ] semantic status recorded per material claim
[ ] delivery action recorded separately
[ ] SUPERSEDED supported by target coverage evidence
[ ] RETIRED supported by explicit current authority
[ ] no requirement vanished merely because implementation was hard

IMPLEMENTATION
[ ] target-native delta is minimal
[ ] no stale authority/runtime/persistence plane restored
[ ] current contracts and forbidden regressions preserved
[ ] duplicated truth not introduced unnecessarily

EVIDENCE
[ ] focused regression evidence added
[ ] negative claims tested adversarially where practical
[ ] full required acceptance run on exact resulting SHA
[ ] failed SHA preserved on failure
[ ] repair creates a new SHA

PROMOTION
[ ] tested SHA equals promoted SHA where topology permits
[ ] ancestry checked before fast-forward
[ ] no synthetic merge SHA introduced without reason
[ ] stable refs moved only after evidence exists

CLEANUP
[ ] old branches checked for unique negative knowledge
[ ] surviving knowledge moved to durable issue/docs/contract
[ ] branch classified KEEP / DEFER / PROVENANCE / DELETE
```

---

# 51. An operator mistake reinforced the same identity lesson

Immediately after the accepted SIB2 head had been fast-forwarded to `main`, a documentation operation attempted to create a new retrospective branch but accidentally issued one placeholder file write against `main` before the branch existed.

The error was detected immediately.

The correct recovery was **not** to add another “revert” commit and quietly accept a new `main` identity. Because the accidental commit contained only the mistaken placeholder and no legitimate concurrent work, `main` was restored directly to the exact accepted SIB2 SHA, and the documentation branch was then created from that identity before any retrospective content was written.

The episode is worth recording because it applies the same principles to the maintainer tooling itself:

- verify the target ref before writes;
- create the intended branch before file mutations;
- do not allow a tooling mistake to silently advance an accepted baseline;
- after an accidental ref mutation, restore the intended exact authority explicitly and verify it;
- distinguish “revert content” from “restore accepted identity.”

The discipline must apply to the people and automation operating Git, not only to the code being reviewed.

---

# 52. The deeper lesson

Git is exceptionally good at preserving textual ancestry.

It can tell us that one commit descends from another, which hunks changed, which parents a merge has, and whether a ref can move by fast-forward.

That information was necessary throughout the session.

It was not the whole engineering problem.

The difficult part was preserving things Git does not model directly:

- why a change existed;
- which behavior mattered and which mechanism was accidental;
- which failures must never return;
- which authority currently owns a decision;
- which evidence belongs to which exact composition;
- which historical branch is still meaningful and which is only a pointer to already absorbed work.

Semantic Refit was useful because it forced those questions to become first-class integration work.

Exact-Head Acceptance was useful because it stopped confidence from floating freely across commits.

SIB was useful because it gave the repository one explicit integration baseline from which future work and branch archaeology could proceed.

Protected forbidden regressions were useful because they preserved negative knowledge that ordinary feature descriptions tend to forget.

The combination mattered more than any individual mechanism.

The strongest evidence for the discipline is not simply that the final candidate passed.

It is that the process repeatedly produced:

```text
STOP
REQUEST CHANGES
NEW SHA
FRESH TEST
DO NOT MERGE THIS BRANCH
PRESERVE THIS FINDING
FAST-FORWARD THE TESTED IDENTITY
```

at moments when a less disciplined process would have accepted a plausible shortcut.

That friction was productive.

A development discipline earns its cost when it changes engineering decisions **before** bad assumptions become release history.

This one did.
