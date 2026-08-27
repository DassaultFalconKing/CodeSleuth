# CodeSleuth durable evidence store contract

**Status:** Accepted
**Classification:** CORE-HARDENING + SKILL-EXTENSION + DOCS
**Scope:** OpenCode-installed durable review/evidence state under `.opencode/state/`

## 1. Contract

CodeSleuth uses a small local filesystem evidence store rather than a separate
SQL/database service. It is intentionally boring: text-native, inspectable,
worktree-local, and owned by narrow CodeSleuth tools.

It behaves like a specialized evidence database, but it is **not** a
general-purpose CRUD database and must not grow database-like authority by
accident.

The compact rule is:

> **Mutable progress is snapshotted; historical evidence is appended; derived
> views are rebuildable; model context is never durable authority.**

## 2. Authority chain

```text
tracked Git source + exact blob/SHA identity
        |
        v
.opencode/state/reviews/<reviewId>/
        |
        +--> state.json       mutable atomic checkpoint snapshot
        +--> findings.ndjson  append-only verified finding ledger
        +--> eha.ndjson       append-only EHA/SIB/repair event ledger
        |
        +-----------------------------+
        |                             |
        v                             v
RepositoryContextProjection      reports / EHA Mermaid
(rebuildable linkage state)      (human-readable derived views)
        |                             |
        +--------------+--------------+
                       v
                OpenCode/LLM context
                ephemeral working memory
```

Authority is one-way. A downstream representation never upgrades itself into
upstream evidence.

- Git/current tracked content plus blob/SHA identity is source authority.
- The review evidence store is durable review/evidence/progress authority.
- RepositoryContextProjection is bounded, derived, rebuildable linkage/context
  state.
- Reports and Mermaid are presentation/read models.
- LLM conversation/context is ephemeral working memory.

## 3. Physical layout

The review store lives under:

```text
.opencode/state/reviews/
    latest.txt
    sessions/
        <sessionId>.txt
    <reviewId>/
        state.json
        findings.ndjson
        eha.ndjson
```

Not every review must contain every ledger. For example, `eha.ndjson` appears
only when EHA/SIB work is recorded.

`latest.txt` and `sessions/*.txt` are mutable discovery pointers. They help tools
resolve a review ID but are **not evidence** and must never be cited as proof of
a finding, verdict, SHA, or acceptance state.

## 4. Record semantics

### `state.json`: mutable checkpoint snapshot

`state.json` is the current resumable review checkpoint. It may be atomically
replaced by `review_state` as progress changes.

It stores current operational state such as:

- review/session identity;
- target and starting HEAD;
- phase/completed work;
- reviewed paths plus blob-bound coverage evidence;
- open questions and next actions;
- current dirty/staleness observations.

This is the intentionally mutable part of the store. Replacement must remain
atomic so a crash does not expose a partially-written checkpoint.

### `findings.ndjson`: append-only finding ledger

`findings.ndjson` records verified material findings captured through
`review_state_record_finding` with exact path/range, excerpt, blob identity,
HEAD, worktree status, severity and explanation.

Ordinary operation must never edit or delete an existing finding line in place.
A future need for correction/supersession must be represented by an explicit,
versioned evidence operation rather than history rewriting.

### `eha.ndjson`: append-only EHA event ledger

`eha.ndjson` records EHA campaign starts, SIB0/SIB1/SIB2 verdicts and EHA repair
lineage through `eha_state`.

Existing events are historical facts and remain present after later events. A
failed SHA is not converted into PASS by editing an older line; a repair creates
new repair/candidate evidence and a new EHA campaign on the new exact SHA.

Multiple later events may refine the current read model, but the underlying
ledger remains append-only.

## 5. Write boundary

The supported write boundary is the CodeSleuth tool API:

```text
review_state_start
review_state_checkpoint
review_state_record_finding

eha_state_start_campaign
eha_state_record_verdict
eha_state_record_repair
```

The implementation may perform atomic file replacement or append internally,
but agents, Skills, Playbooks and reports must not bypass these semantics by
opening the state files and rewriting JSON/NDJSON directly.

Direct raw writes are forbidden because they bypass identity capture,
validation, staleness checks, EHA exact-head checks, classification rules and
future schema migrations.

## 6. Read and search boundary

Tool-mediated reads are the canonical operational interface because they apply
the store's semantics:

```text
review_state_load
review_state_get_finding

eha_state_load
eha_state_mermaid
```

Raw `cat`, `grep`, editor inspection, filesystem search or similar reads are
allowed for:

- human audit;
- debugging;
- disaster recovery;
- locating a review/event when a normal tool path is unavailable;
- confirming that durable text state exists.

But raw text search is a **read-only discovery mechanism**, not a semantic API.
A grep hit does not by itself establish that evidence is current, blob-valid,
claimable, non-stale, or attached to the current exact HEAD. Re-load through the
appropriate CodeSleuth tool before making a material acceptance/review claim.

This distinction is deliberate: the store remains transparent to humans and
LLMs without making "whatever grep found first" the database query planner from
hell.

## 7. No ordinary CRUD contract

The store deliberately does not expose generic create/read/update/delete over
arbitrary records.

Instead it exposes domain operations:

- start/checkpoint a review;
- record/reload a verified finding;
- start an EHA campaign;
- record a SIB verdict;
- record EHA repair lineage;
- derive bounded status/presentation.

There is no supported operation whose purpose is "delete this failed verdict"
or "rewrite this old finding."

A future retention/garbage-collection feature may remove whole obsolete local
review histories only through an explicit retention contract. It must never be
used to manufacture a different historical acceptance result, and it must not
silently invalidate a report that still claims the deleted evidence exists.

## 8. Derived state contract

The following are **not** evidence-store authorities:

### RepositoryContextProjection

Stored under `.opencode/state/context-graphs/`. It is bounded linkage/context
state derived from source plus review knowledge and may be rebuilt. Its graph
relations help navigation and context selection; they do not replace exact
finding evidence.

### Mermaid

`repo_context_graph_mermaid` and `eha_state_mermaid` produce deterministic or
bounded human-readable projections. Mermaid source is presentation, never a
write path back into evidence state.

Do not parse edited Mermaid and write it back into `review_state`,
`findings.ndjson`, `eha.ndjson`, or repository truth.

### Analytical reports

`.codesleuth/reports/*.md` are assistant/human-readable summaries. They may quote
or summarize structured evidence but cannot override it. When report prose and
the structured store disagree, resolve the underlying evidence through its
proper tool semantics and regenerate/correct the report.

## 9. LLM consumption contract

LLMs are consumers of bounded tool results, not owners of persistence.

Preferred flow:

```text
LLM / build agent
   |
   v
CodeSleuth load/query tools
   |
   v
bounded validated state/evidence
   |
   +--> reasoning / next tool request
   +--> bounded context projection
   +--> report / Mermaid presentation
```

After compaction or restart, reload durable state. Do not reconstruct project
truth from remembered conversation prose when the store can answer it.

For large stores, search/grep may locate candidate IDs, but material reasoning
should rehydrate the exact record through the relevant tool rather than dumping
entire ledgers into model context.

## 10. Concurrency and transactional scope

This store is not a transactional multi-user database service. Current guarantees
are intentionally narrow:

- checkpoint snapshots use atomic replacement;
- historical ledgers use append operations;
- IDs are generated to avoid line-count/racy identity schemes;
- CodeSleuth tools own validation and write semantics.

Do not assume arbitrary cross-process transactions, relational constraints,
joins, locks, or SQL-style isolation. If those become required by real product
scale, that is a persistence-architecture decision, not permission to quietly
bolt SQLite/Postgres onto one Skill.

## 11. Persistence-authority rule

Do not introduce a second durable evidence database, ledger or canonical state
store for the same facts.

A proposed SQLite/Postgres/graph/vector/index layer must be classified first as
one of:

- **derived index/cache**: rebuildable from the existing evidence authority;
- **migration/replacement of authority**: requires an explicit architecture
  decision, migration plan and SIB0 reconsideration;
- **duplicate authority**: prohibited.

Storage convenience is not sufficient reason to split truth across two places.

## 12. Skills and Playbooks that consume this contract

The installed atomic Skills and Playbooks that currently touch this evidence
boundary are:

- `repository-deep-review` — starts/checkpoints review state, records findings,
  reloads after compaction and binds context projection work to verified review
  state;
- `codesleuth-reports` — reads the structured store and writes derived
  human-readable reports;
- `eha-candidate-selection` — selects literal release-stream exact-head SIB
  candidates without inventing a second evidence authority;
- `eha-campaign-evidence` — records exact-head campaigns, SIB verdicts, and
  derived history through `eha_state_*` in `eha.ndjson`;
- `eha-repair-protocol` — records EHA repair-loop decisions and lineage without
  raw-rewriting append-only ledger history;
- `eha-sib-acceptance` (Playbook) — orchestrates SIB0/SIB1/SIB2 exact-head
  acceptance from atomic Skills and `eha_state_*` tools;
- `eha-repair` (Playbook) — orchestrates the EHA repair loop from atomic Skills
  and `eha_state_*` tools;
- `feature-porting-discipline` — uses review state during substantial porting
  work and explicitly forbids creation of a duplicate evidence ledger.

Those Skills and Playbooks inherit this contract even when they mention only one
file/tool from the store. They may narrow behavior for their domain but may not
weaken the authority/write/append-only rules here.

## 13. Change policy

Changes to record fields, schemas or load summaries are ordinary hardening when
they preserve this authority model and have migration/backward-compatibility
coverage where needed.

The following require an explicit architecture review and normally reopen SIB0:

- replacing filesystem evidence authority with a database service;
- making context graphs, reports or Mermaid canonical evidence;
- adding a second independently writable evidence ledger for the same facts;
- allowing model prose/raw grep output to promote itself into verified evidence;
- adding generic destructive CRUD that can rewrite acceptance/finding history.

## 14. Canonical invariant

> **The filesystem is the storage mechanism; CodeSleuth domain tools are the
> write semantics; append-only ledgers preserve history; derived projections are
> disposable; exact Git identity remains the root of evidence.**
