# RC7+ Thought Experiment: Apache Doris as a Large-Evidence Analytical Plane

**Status:** NON-NORMATIVE THOUGHT EXPERIMENT  
**Scope authority:** none  
**Implementation commitment:** none  
**Relationship to RC7:** exploratory follow-up only; this document MUST NOT expand accepted RC7 scope by implication.

## 1. Question

If a future CodeSleuth deployment accumulates evidence at a scale where local worktree ledgers are no longer sufficient for cross-repository analytics, could Apache Doris provide a useful secondary analytical/search plane without becoming a competing evidence authority?

This document explores that possibility only.

## 2. Starting invariant

The existing CodeSleuth persistence discipline remains the authority unless a separately accepted architecture migration explicitly replaces it:

```text
tracked Git source + exact SHA/blob identity
        |
        v
local authoritative snapshots / append-only ledgers
        |
        +--> findings.ndjson
        +--> findings-amendments.ndjson
        +--> eha.ndjson
        +--> future implementation ledgers
        |
        v
rebuildable projections / reports / search indexes
```

Doris, if introduced under this thought experiment, begins strictly below that authority boundary.

```text
canonical local ledgers
        |
        | one-way ingest / CDC-like projection
        v
Apache Doris analytical plane
        |
        +--> cross-repository SQL
        +--> text/inverted search
        +--> vector/semantic retrieval
        +--> hybrid lexical + vector retrieval
        +--> AI-assisted classification / summarization / filtering
        +--> trend / regression / lineage analytics
```

No Doris query result may write historical truth back into a canonical CodeSleuth ledger without going through the normal domain tool and evidence rules.

## 3. Why Doris is interesting only at large scale

For one repository or one active review, NDJSON is cheaper, more transparent, easier to audit, and easier to recover. A database would create installation, lifecycle, migration, backup, service-availability, networking, schema-versioning and failure-mode obligations without solving a real problem.

Doris becomes interesting only when evidence volume or query topology changes materially, for example:

- hundreds or thousands of repositories;
- tens or hundreds of millions of evidence events;
- multiple teams producing independent ledgers;
- long-term historical comparison across releases and repositories;
- cross-ledger queries that are impractical as filesystem scans;
- semantic retrieval over large evidence corpora;
- aggregate analysis over findings, contracts, repairs, gates and lineage.

## 4. Candidate data model

The first experiment should preserve raw event identity rather than immediately collapsing history into mutable rows.

### 4.1 Raw immutable event projection

Conceptual columns:

```text
project_id
repo_identity
ledger_domain
ledger_generation
source_path
source_digest
event_id
event_type
event_time
target_sha
recorded_head_sha
requirement_or_finding_id
payload_hash
payload_json
ingested_at
```

The natural uniqueness boundary should be derived from stable event identity and source digest, not wall-clock time alone.

Time is useful for ordering and partitioning. It is not sufficient authority identity because clocks collide, skew and lie with admirable consistency.

### 4.2 Latest-state projection

A separate derived/latest table may use Doris `UNIQUE KEY` semantics to maintain one current row per logical entity:

```text
(project_id, ledger_domain, logical_entity_id) UNIQUE KEY
sequence / version
latest_event_id
latest_event_time
latest_target_sha
latest_status
latest_payload
```

Newer versions may replace older rows in this **derived read model**. This does not erase history because the raw event projection remains append-only and rebuildable from canonical ledgers.

The conceptual rule is:

```text
raw immutable history -> authority-preserving projection
latest UNIQUE table   -> acceleration/read model only
```

## 5. Search plane

Apache Doris 4.x now exposes the combination that makes this experiment worth revisiting later:

- inverted indexes for lexical/full-text retrieval;
- native ANN vector indexes on `ARRAY<FLOAT>` columns;
- HNSW and IVF-family vector retrieval;
- SQL predicates and analytics beside vector search;
- hybrid text + vector retrieval;
- AI functions callable from SQL.

A future evidence table could therefore maintain both textual evidence and embeddings:

```text
evidence_text STRING
embedding ARRAY<FLOAT>
```

with:

- inverted index over `evidence_text` for exact/explainable retrieval;
- ANN index over `embedding` for semantic recall;
- ordinary SQL filters for repository, SHA, capability, severity, lifecycle, date, domain and authority class.

This is attractive for CodeSleuth because semantic search without exact identity filtering would be dangerous. Doris permits the semantic candidate search and exact structured predicates to live in the same query plane.

## 6. AI integration thought experiment

Doris 4.x also exposes SQL AI functions including classification, extraction, filtering, generation, masking, semantic similarity, summarization and aggregation.

Potential future analytical uses include:

- classify large populations of historical findings into stable taxonomies;
- summarize clusters of repeated regressions;
- compare semantic similarity between evidence packets;
- extract recurring failure patterns from long-running histories;
- perform coarse semantic filtering before exact CodeSleuth verification;
- generate analyst-facing summaries over bounded query results.

These functions must remain **analytical/inference surfaces**, never evidence authority.

For example:

```text
AI_FILTER result             -> lead
AI_CLASSIFY result           -> derived label
AI_SUMMARIZE result          -> presentation
vector nearest neighbour     -> candidate evidence
canonical CodeSleuth reopen  -> verified evidence
```

No LLM-backed Doris function may manufacture `PASS`, `CLOSED`, `PROTECTED`, `verified`, or another authoritative CodeSleuth state.

## 7. Hybrid retrieval experiment

The most interesting future research direction is not "put ledgers in SQL". It is evidence retrieval across very large histories.

Conceptually:

```text
user / agent question
        |
        v
structured filters
(repo / SHA / domain / lifecycle / time / capability)
        |
        +--> inverted lexical retrieval
        +--> ANN semantic retrieval
        |
        v
hybrid candidate set
        |
        v
bounded CodeSleuth evidence rehydration
        |
        v
exact source/ledger verification
```

This preserves the distinction between retrieval and proof.

## 8. Repair implications

If RC7 later introduces ledger generations for structural recovery, Doris ingestion must preserve them explicitly.

A repaired generation must not overwrite the corrupted predecessor in the raw analytical history.

Conceptual lineage fields:

```text
ledger_generation
predecessor_generation
predecessor_digest
repair_manifest_id
trust_status
```

The latest-state projection may point at the newest accepted generation, while raw history retains every generation and its trust classification.

## 9. Failure modes to study before any implementation

A serious future design would need to answer at least:

1. How is canonical-ledger -> Doris ingest made idempotent?
2. How are event IDs and source digests used to reject duplicates?
3. How is partial ingestion detected without making absence look authoritative?
4. How is a new recovered ledger generation represented without hiding its predecessor?
5. What is the rebuild story if the entire Doris cluster disappears?
6. Can every Doris row be traced back to exact canonical bytes?
7. How are embeddings versioned when the embedding model changes?
8. How are AI-function outputs labeled as non-authoritative inference?
9. How are secrets and sensitive evidence excluded or masked before remote-model AI functions?
10. What scale threshold justifies the operational cost at all?

A correct answer to item 5 should be close to:

> Recreate Doris from canonical ledgers plus explicitly versioned derived enrichments.

If that is not possible, Doris has silently become persistence authority and the architecture has changed.

## 10. Explicit non-goals

This thought experiment does NOT propose:

- adding Doris to RC7;
- requiring a database for Ledger Repair;
- replacing local CodeSleuth state;
- using database `UNIQUE KEY` replacement as historical-event deletion;
- making embeddings canonical evidence;
- making AI-function output authoritative;
- introducing a network service into ordinary single-repository CodeSleuth workflows.

## 11. Future research packet

If a sufficiently large evidence corpus appears, research should be split into separate experiments:

1. **Doris raw-event ingestion** — identity, deduplication, generations and rebuildability.
2. **Doris latest-state projection** — `UNIQUE KEY`/version semantics strictly as derived read model.
3. **Lexical evidence search** — inverted index and `SEARCH` DSL.
4. **Semantic evidence search** — embedding model/version contract plus HNSW/IVF evaluation.
5. **Hybrid evidence retrieval** — structured + lexical + vector query behavior.
6. **Doris AI functions** — classification, filtering, summarization, similarity and aggregation as non-authoritative analytical helpers.
7. **Scale economics** — identify the evidence volume/query workload where Doris becomes materially better than local NDJSON + bounded indexes.

## 12. Current conclusion

For present CodeSleuth scale:

```text
NDJSON + atomic snapshots + derived Markdown
```

is the better architecture.

For a future large multi-repository evidence system, Doris is interesting as a **rebuildable analytical/search/AI plane over canonical ledger history**, not as the first place where truth is written.

## References for the future experiment

- Apache Doris 4.x AI overview: https://doris.apache.org/docs/4.x/ai/ai-overview/
- Apache Doris 4.x vector search overview: https://doris.apache.org/docs/4.x/table-design/index/vector-index/overview/
- Apache Doris 4.x HNSW: https://doris.apache.org/docs/4.x/table-design/index/vector-index/hnsw/
- Apache Doris hybrid search: https://doris.apache.org/docs/4.x/key-features/hybrid-search/
- Apache Doris AI function overview: https://doris.apache.org/docs/dev/sql-manual/sql-functions/ai-functions/overview/
- Apache Doris inverted/text search overview: https://doris.apache.org/docs/dev/table-design/index/inverted-index/overview/
