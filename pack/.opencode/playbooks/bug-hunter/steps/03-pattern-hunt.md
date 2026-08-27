# Step: repository-wide pattern hunt

Consume `hunt_scope`. Search the whole repository for siblings of the suspected engineering assumption, not only the submitted diff. Use bounded `repository-deep-review` slices and reopen exact source before recording a candidate.

Hunt all contributor classes from `docs/CONTRIBUTOR-ERROR-PATTERNS.md`:

- **EP-01 exact identity loss:** mutable branch/ref/path/name/version/display identity displaces exact SHA/blob/hash/runtime identity.
- **EP-02 failure becomes absence:** probe/read/parse/dependency failure collapses into missing and then prune/delete/forget.
- **EP-03 default-contract inversion:** old no-argument/default behavior changes while compatibility requires a newly introduced flag.
- **EP-04 exposure exceeds proof:** TUI/settings/CLI/docs expose support beyond the enabled runtime/platform profiles actually exercised.
- **EP-05 green-by-skip/orphan tests:** critical paths skip, xfail, or are absent from the canonical umbrella/workflow.
- **EP-06 ambient runtime identity:** correctness depends on an executable/runtime selected through ambient PATH or another unbound locator.
- **EP-07 scope resurrection:** `DEFER`, `NOT PLANNED`, `RETIRED`, `SUPERSEDED`, or `BLOCKED` work returns without a new current adoption decision.
- **EP-08 evidence overclaim:** `PASS`, `supported`, `complete`, `verified`, `exact`, or `compatible` is stronger than executed evidence.
- **EP-09 provenance over-promotion:** external parser/provider/LLM output becomes authoritative without CodeSleuth-side exact source/blob/range/mapping verification.
- **EP-10 incomplete optional lifecycle:** normal installed product can expose/select/use/remove an optional feature but lacks a reproducible absent→install/activate→use→remove path.

Also search for catch-all exceptions on authority/lifecycle paths; silently ignored parse failures; destructive actions after uncertain state; stale caller assumptions; code/docs/tests disagreement; caller-supplied provenance accepted without recomputation; locale or nondeterministic ordering in deterministic paths; hidden network/filesystem/process side effects; development-only paths becoming production dependencies; new capability paths missing canonical acceptance; provenance ratios described as semantic precision; and tests that duplicate implementation logic instead of using an independent oracle.

Use `dependency-impact-closure` when changed paths touch registered protected contracts. Use `forbidden-regression-ledger` only to inspect relevant contract-owned negative obligations, not to manufacture speculative FR entries.

Do not fix anything. Do not promote grep/search hits directly into findings.

Return only `pattern_candidates`. For each: EP/rule id or `OTHER`, exact path/symbol, suspected witness, producer/consumer/test/gate locations to verify, repository sibling locations, and candidate state `CONFIRM` or `INVESTIGATE`.
