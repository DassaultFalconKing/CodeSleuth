# Mermaid/context-graph audit and Graphify provider evaluation

**Status:** roadmap / incubation decision; no Graphify runtime is approved or installed by this document  
**Classification:** TOOL-EXTENSION + DOCS; future implementation may also touch EXTENSION-MANAGEMENT-UX  
**Audit baseline:** CodeSleuth `main` at `aa410498ed92418b0c6deeedec0e6ea1ac247c53`  
**Graphify evaluated:** `Graphify-Labs/graphify` release `v0.9.50`, tag commit `43d54acbfa9e731f7a592bb582c1f4b9d48ed73e`, package `graphifyy==0.9.50`  

## Decision

Keep the existing CodeSleuth `RepositoryContextProjection` and Mermaid renderer as the
CodeSleuth graph contract.

Graphify is a promising **optional structural graph provider** because it can move a
large part of repository topology discovery from agent-authored assertions to local,
deterministic tree-sitter extraction. It must not become a second source of repository
truth, replacement review engine, host controller, mandatory dependency, or directly
model-visible parallel graph authority.

The first implementation spike should use Graphify's Python library from an isolated,
explicitly installed and version-pinned optional runtime. Do **not** begin by copying
Graphify source into the CodeSleuth tree, installing its host Skill, enabling its Git
hooks, exposing its MCP server, or committing `graphify-out/` to target repositories.

If later testing proves that the published package boundary is insufficient and a
source-level vendor relationship is genuinely required, prefer an **inactive Git
submodule pinned to an exact upstream commit** over `git subtree` or copied source.
That source-vendoring decision is deferred until the package-first spike supplies a
concrete reason for it.

## 1. Existing CodeSleuth contract

The accepted authority chain stays:

```text
tracked Git source + blob identity
        |
        v
durable review state
        |
        v
bounded RepositoryContextProjection
        |
        +--> bounded model context
        |
        +--> deterministic Mermaid source
```

The projection is derived and rebuildable. Mermaid is presentation only. Material
findings still require reopened exact source and durable finding evidence.

This is the boundary any Graphify integration must preserve.

## 2. Audit of the current Mermaid/context-graph implementation

### What is already strong

#### A. Correct authority placement

Mermaid is downstream of the renderer-neutral projection and cannot become evidence or
repository truth. This is the most important property and should not change.

#### B. Presentation-independent identity

Node, edge, and projection identities are SHA-256 values over explicit semantic fields.
Labels, aliases, layout, and Mermaid metadata do not participate in identity.

#### C. Git-bound provenance and staleness

`verified_source` elements require tracked source paths. CodeSleuth captures Git blob
identity server-side and audits stored linkage against the current worktree on load.

#### D. Bounded model-visible operations

Saved projections and queries have strict node/edge limits, explicit truncation, and
continuation. A large repository graph is not silently dumped into model context.

Current implementation limits include:

```text
save:    500 nodes / 800 edges
view:    default 40 nodes / 60 edges
view:    max 200 nodes / 300 edges
query:   max 3 hops
```

#### E. Inference separation

CodeSleuth distinguishes `verified_source` from `review_inference`. Inference requires
an explanatory note, cannot carry a SourceRef, and is visually dashed in Mermaid.

#### F. Mermaid hardening

The renderer uses stable aliases, clamps labels, strips control characters, escapes
markup-sensitive content, removes backticks from labels, emits explicit bounded-subset
state, and never invokes Chromium/Puppeteer/mmdc.

#### G. Disposable state

Projection state stays under ignored `.opencode/state/`. Removing it does not destroy
repository truth.

### Current limitations

#### L1. Structural discovery is still substantially agent-authored

`/repo-map` asks the host agent/scouts to inspect the repository and submit nodes and
edges to `repo_context_graph_save`. The save tool validates schema, origin rules,
tracked paths, line ranges and Git blob provenance, but it does not independently parse
the source to prove the semantic relation represented by an edge.

Therefore `verified_source` currently means roughly:

> the host claims it captured this relation from source, and CodeSleuth has tied that
> claim to a real tracked source/blob location.

That is consistent with the accepted agent-evidence discipline, but it is not the same
as machine-derived structural proof. A deterministic AST provider can strengthen this
specific part of the pipeline.

**Roadmap priority: high.**

#### L2. Mapping cost scales with host-agent reading

Building a useful map across a large repository consumes model/tool turns because the
host has to discover many structural relations before save. This is exactly the class
of deterministic work CodeSleuth should prefer to delegate to a narrow tool.

**Roadmap priority: high.**

#### L3. Mermaid selection is bounded but not topology-aware

`repo_context_graph_mermaid` renders a bounded prefix of the saved projection. It does
not currently accept semantic roots/hops or render the result of a neighborhood query.
Because projection nodes are identity-sorted, a deterministic prefix is not
necessarily the most informative architectural slice.

**Roadmap priority: medium.**

A near-term improvement can be implemented without Graphify: let Mermaid rendering use
an explicit bounded neighborhood selection (roots/hops/relation/origin) before
rendering.

#### L4. The closed relation vocabulary is intentionally smaller than real AST graphs

Current relations are:

```text
imports
calls
implements
registers
persists_to
reads_from
tests
configures
documents
depends_on
review_inference
```

A richer structural provider will emit relations for which CodeSleuth has no exact
semantic equivalent. The adapter must not rename them approximately merely to fit the
schema.

**Roadmap priority: medium.**

#### L5. There is no renderer runtime or interactive graph UI

This remains an intentional deferral, not a defect. SVG/HTML/interactive graph output
should not be added merely because an upstream dependency can produce it.

**Roadmap priority: deferred.**

## 3. What Graphify contributes

At the evaluated release, Graphify provides a Python library/CLI with a deterministic
code extraction path based on tree-sitter. Its documented pipeline is approximately:

```text
detect -> extract -> build -> cluster -> analyze -> report -> export
```

The library communicates through Python dictionaries and NetworkX graphs. For code,
its structural path can run locally without an LLM. Its extraction schema includes
nodes with `source_file` / `source_location` and edges carrying relation plus confidence
labels such as `EXTRACTED`, `INFERRED`, and `AMBIGUOUS`.

This makes Graphify useful to CodeSleuth primarily for:

- deterministic multi-language AST extraction;
- cross-file calls/imports and similar structural links;
- graph topology used to choose useful bounded neighborhoods;
- optional community/centrality signals after the structural adapter is proven;
- a mature upstream corpus of parser and incremental-update tests.

Graphify also includes many capabilities CodeSleuth does **not** need for this
integration: host Skills, semantic extraction for docs/media, URL ingest, Git hooks,
committed `graphify-out/`, an MCP server, global graphs, PR dashboards, Neo4j/FalkorDB,
interactive HTML, and its own Mermaid call-flow HTML exporter. Those capabilities stay
outside the initial CodeSleuth provider boundary.

## 4. Critical semantic mismatch: `EXTRACTED` is not `verified_source`

Graphify's extraction provenance is useful but weaker/different than the CodeSleuth
source identity contract. Its documented extraction schema records source file/location
and confidence, but not the current Git blob hash required by CodeSleuth.

Therefore the adapter MUST NOT implement:

```text
Graphify EXTRACTED -> CodeSleuth verified_source   # directly
```

Instead:

```text
Graphify EXTRACTED candidate
    -> path must be tracked by the exact target Git index/worktree policy
    -> reject path escape / non-regular entry / unsupported gitlink/symlink state
    -> relation must have an exact approved semantic mapping
    -> parse and validate source line range when supplied
    -> CodeSleuth captures current Git blob identity itself
    -> only then materialize verified_source
```

Graphify `INFERRED` or `AMBIGUOUS` data can never be promoted this way. If retained at
all, it maps to CodeSleuth `review_inference` with an explanatory note and no SourceRef.

## 5. Provider boundary

The integration should look like this:

```text
tracked files selected by CodeSleuth
        |
        v
optional Graphify AST runtime
        |  candidate nodes/edges only
        v
CodeSleuth Graphify adapter
        |  tracked-path + relation + Git/blob validation
        v
RepositoryContextProjection v1 (or explicit later schema revision)
        |
        +--> repo_context_graph_query
        +--> CodeSleuth Mermaid renderer
```

### Explicit non-goals

The adapter must not:

- run `graphify install`;
- install/modify OpenCode, Cursor, Codex, Claude, or other host Skills;
- run `graphify hook install` or install merge drivers;
- start Graphify MCP or HTTP servers;
- enable `graphify global` state;
- ingest URLs;
- send repository content to Graphify semantic/LLM backends;
- automatically read project-local Graphify provider credentials/config;
- commit `graphify-out/` or other generated Graphify state to the target repository;
- make Graphify graph ids canonical CodeSleuth ids;
- expose Graphify's full graph to the model as an unbounded alternate evidence tool;
- replace CodeSleuth's Mermaid escaping, provenance legend, or truncation semantics.

## 6. Input discipline

Do not let Graphify decide the CodeSleuth repository scope by recursively scanning the
filesystem in the first adapter version.

CodeSleuth should enumerate allowed inputs from Git, then pass the explicit file list to
Graphify's library extraction API with the repository root supplied explicitly.

Benefits:

- tracked-only policy remains a CodeSleuth decision;
- `.graphifyignore` cannot silently broaden or redefine CodeSleuth evidence scope;
- untracked secrets and generated files do not enter the provider merely because they
  exist on disk;
- source ids remain anchored to a stable repository root;
- scope can be bounded before parser work starts.

Graphify's own ignore support can remain an additional narrowing mechanism later, never
a widening mechanism.

## 7. Relation mapping policy

Phase 1 should use an allowlist and report unmapped relations rather than inventing
near-synonyms.

Initial examples:

| Graphify candidate | CodeSleuth mapping | Policy |
| --- | --- | --- |
| `imports` | `imports` | exact candidate; eligible for verified promotion after Git validation |
| `calls` | `calls` | exact candidate; eligible for verified promotion after Git validation |
| exact test relationship where provenance is structural | `tests` | only after a dedicated mapping/test proves equivalence |
| `inherits` | none in v1 | do not silently call this `implements`; retain as diagnostic/unmapped |
| `uses` | none | too broad; do not coerce to `depends_on` |
| `references` | none | too broad |
| `method` / membership-style edges | none | topology aid only unless schema is deliberately extended |
| any Graphify `INFERRED` relation | `review_inference` or drop | never `verified_source` |
| any Graphify `AMBIGUOUS` relation | `review_inference` or drop | include ambiguity in note |

If discarded relations materially limit usefulness, evolve the
`RepositoryContextProjection` relation vocabulary explicitly with schema/tests. Do not
let an adapter smuggle an upstream ontology into the existing closed set.

## 8. Node mapping policy

The same rule applies to node types. Initial mapping should remain narrow:

- source-file concepts -> `file`;
- functions/classes/methods/modules with stable source identity -> `symbol`;
- external import placeholders -> `external` only when the adapter can distinguish
  them safely;
- Graphify communities are selection metadata, not automatically CodeSleuth
  `component` nodes;
- generated reports, visual clusters and labels never become identity inputs.

## 9. State policy

Graphify's normal CLI intentionally creates `graphify-out/` and even documents a team
workflow where that directory can be committed. CodeSleuth must not adopt that default.

Provider-private cache, if needed, belongs under the existing local state boundary, for
example:

```text
.opencode/state/context-graphs/providers/graphify/
```

or another explicitly ignored CodeSleuth state path.

The cache must be rebuildable and disposable. It must record at least:

```text
provider: graphify
providerVersion: 0.9.50
providerCommit: 43d54acbfa9e731f7a592bb582c1f4b9d48ed73e
headSha: <target repository HEAD>
scope: <tracked path scope>
createdAt: <timestamp>
```

No Graphify state may become required to reproduce repository truth or a material
finding.

## 10. Dependency strategy

### Phase 1 recommendation: isolated package, not source vendoring

Use the official package distribution in a dedicated optional environment. The first
compatibility spike should pin the exact tested release:

```text
graphifyy==0.9.50
```

The exact pin is intentional for incubation because the adapter imports Graphify library
APIs and the project is currently moving quickly within a pre-1.0 series. Updating the
provider should be a reviewed CodeSleuth change, not an ambient package upgrade.

This runtime must be absent when the feature is disabled. Installation must be explicit
through a future extension/dependency management action or documented developer command.
It must not be pulled in by ordinary CodeSleuth install.

### Why package-first

- Graphify already publishes the official `graphifyy` package and CLI;
- source vendoring would add repository/submodule lifecycle before proving the adapter;
- vendoring source does not solve transitive Python dependency reproducibility by itself;
- a package boundary makes it easier to prove that CodeSleuth depends only on a small
  public library surface;
- it avoids making every CodeSleuth clone aware of a large optional source tree.

### If true source vendoring becomes necessary

Use a Git submodule, not copied files or subtree:

```text
vendor/graphify -> exact upstream commit gitlink
```

Requirements:

1. keep it inactive/uninitialized by default;
2. pin the gitlink to an exact reviewed commit, never treat mutable `v8` as runtime
   authority;
3. record the matching upstream release/tag when available;
4. retain upstream `LICENSE`, `LICENSE-MIT`, and `NOTICE` obligations;
5. do not carry local patches directly in an unreachable submodule commit;
6. if patches become necessary, use a maintained CodeSleuth fork with explicit
   upstream provenance or contribute them upstream;
7. update by a dedicated PR that advances the gitlink after compatibility/security
   gates pass;
8. do not recursively copy the optional vendor tree into target repositories unless
   Graphify was explicitly enabled there.

A subtree is not preferred because it imports the dependency source/history into the
CodeSleuth repository and weakens the clean independent-update boundary that makes an
optional provider useful.

## 11. Upstream observations relevant to adoption

### Positive

- Apache-2.0 project license is compatible with use as a separate optional dependency,
  subject to retaining required license/NOTICE attribution when redistributing source
  or derivatives.
- Python 3.10+ matches CodeSleuth's current Python floor.
- Structural code extraction is local and tree-sitter based.
- The library exposes plain Python extraction/build APIs; CodeSleuth does not need to
  install Graphify's host Skill to use them.
- The project explicitly distinguishes extracted, inferred and ambiguous edges.
- Security documentation covers path traversal, label sanitization, symlink traversal,
  non-network default operation, and prompt-injection boundaries for its semantic path.
- Upstream has substantial tests and active incremental/parser hardening.

### Risks / due-diligence flags

- The dependency surface is large because the default package pulls many tree-sitter
  language grammars plus NetworkX/Numpy/RapidFuzz.
- Graphify is pre-1.0 and moving rapidly; the evaluated release was published on the
  same date as this audit. Exact compatibility pinning is appropriate during incubation.
- Upstream's `SECURITY.md` supported-version table still says `0.3.x` while the current
  release is `0.9.50`; the threat-model content is useful, but this documentation drift
  is a maintenance signal worth watching.
- Graphify's own host Skill can auto-install/upgrade its package and strongly instruct
  the host to use Graphify first. CodeSleuth must bypass that Skill and call only the
  library boundary it owns.
- Graphify's normal team workflow can commit generated graph state and install Git
  hooks/merge drivers. That conflicts with CodeSleuth's local, rebuildable context-state
  discipline and is therefore disabled in the integration.
- Graphify supports semantic extraction and network/provider integrations. None of those
  permissions are implied by enabling the structural provider.
- Upstream relation/node vocabularies are richer and evolve independently. Mapping must
  fail closed on unknown semantics.

## 12. Mermaid roadmap

### M0 — audit and contract freeze (this document)

Acceptance:

- current authority chain is unchanged;
- known limitations are explicit;
- Graphify integration boundary is documented before code is added.

### M1 — scoped Mermaid rendering, no Graphify required

**Current-native status:** complete. `repo_context_graph_query` and
`repo_context_graph_mermaid` share `selectNeighborhood()` semantics for roots,
hops, relation/origin filters and bounds. Regression coverage includes
determinism, explicit truncation, omitted-node edge safety, hostile labels and
comments, provenance styling, dirty rename/delete drift, large graphs,
zero-match scopes, and Windows/newline path behavior. Protected-capability and
EHA Mermaid views are separate derived projections over their existing registry
and ledger authorities; they do not imply approval of an external provider.

Extend CodeSleuth Mermaid generation so a caller can render an explicit bounded
neighborhood rather than only the projection prefix.

Preferred surface:

```text
roots
hops
relation filter
origin filter
nodeLimit
edgeLimit
direction
```

Reuse the existing `selectNeighborhood()` logic. Do not add a second query language.

Acceptance:

- same deterministic output for the same projection + selection;
- all current escaping and inference styling retained;
- subset/truncation state remains explicit;
- tests cover scoped selection, dangling-edge exclusion and injection-resistant labels.

### M2 — Graphify structural-provider spike

**Feature-branch status:** implemented. The exact-pinned optional adapter accepts only
an explicit tracked-file manifest, calls the local structural library with networking
disabled, validates Git/blob identity, maps a closed relation vocabulary, and bounds
candidate output. It does not install or invoke Graphify host/runtime side effects.

Add a narrow Python adapter/helper that consumes an explicit Git-selected file list and
returns candidate structural nodes/edges.

Do not change `/repo-map` default behavior yet.

Acceptance:

- optional dependency absent by default;
- code-only, no network, no semantic LLM path;
- no `graphify install`, hooks, MCP, global graph, HTML or report generation;
- exact provider version/provenance reported;
- tracked-only inputs supplied by CodeSleuth;
- unknown relation/node kinds counted and rejected/dropped explicitly;
- `EXTRACTED` does not bypass CodeSleuth Git/blob capture;
- `INFERRED`/`AMBIGUOUS` cannot become `verified_source`;
- bounded output before it reaches model-visible tools.

### M3 — corpus comparison and hardening

**Feature-branch status:** implemented for deterministic fixtures and the current
Windows development host. The harness covers the listed language/drift/security shapes
and reports honest time, Python-memory, size, truncation and unmapped-semantics metrics.
Linux/macOS execution remains an adoption-gate item, not an inferred PASS.

Test built-in mapping against representative repositories covering at least:

```text
CodeSleuth itself
Python
TypeScript/Node
Rust
mixed-language repository
large repository above the current projection cap
worktree with dirty tracked files
renames/deletions between graph build and load
symlink/gitlink/non-regular path cases
malicious labels / odd encodings
```

Measure:

- structural edge precision on sampled source evidence;
- useful-node/edge recall versus current agent-built maps;
- wall time and memory;
- host/model tokens spent constructing the map;
- provider output size and truncation rate;
- number and distribution of unmapped Graphify relations;
- cross-platform behavior on Linux/macOS/Windows.

Stop the integration if it does not materially reduce agent mapping work or if semantic
normalization produces too many unverifiable/coerced relations.

### M4 — optional provider behind `/repo-map`

**Feature-branch status:** implemented. `builtin` remains default in settings/TUI and
the Playbook. Explicit Graphify status/extraction exposes version, origin, permissions,
compatibility and removal; candidates still pass consolidated context-graph save
validation.

Only after M2/M3 pass, expose provider selection without changing the safe default
silently.

Conceptual setting:

```text
contextGraph.provider = builtin | graphify
```

or an equivalent extension registry entry.

The user/TUI should be able to see:

```text
provider
installed/not installed
version
origin
update available
permissions/capabilities
```

This belongs naturally to the already-allowed extension-management UX.

### M5 — topology-assisted Mermaid selection

**Feature-branch status:** implemented as ephemeral, deterministic community/centrality
root hints. Hints match an existing projection by closed semantic identity and feed the
same roots into the accepted query/Mermaid traversal; they never alter identity,
provenance or evidence origin.

Use Graphify communities/centrality only as **selection hints** for which verified
CodeSleuth nodes to render. They must not become identity or evidence.

Examples:

- choose representative hubs per bounded component;
- choose cross-community edges for architecture overview;
- derive focused call-flow neighborhoods;
- retain explicit provider/selection metadata in the rendering response.

Do not embed Graphify's HTML renderer as the canonical CodeSleuth diagram path.

### Deferred / separate decisions

The following require separate justification and are not implied by provider adoption:

- SVG/Chromium renderer runtime;
- interactive graph UI in CodeSleuth TUI;
- Graphify MCP exposure;
- persistent global graph;
- semantic docs/media ingestion;
- Neo4j/FalkorDB;
- committing generated graph artifacts;
- auto-rebuild Git hooks;
- automatic dependency updates without compatibility review.

## 13. Update policy for the optional provider

An update is a compatibility event, not `pip install -U` hidden inside an agent session.

For each proposed Graphify release:

1. resolve release tag and exact Git commit;
2. review upstream release notes for extraction/schema/security changes;
3. review `pyproject.toml` dependency and Python-floor changes;
4. run the Graphify adapter contract tests and representative corpus suite;
5. record relation/node mapping deltas;
6. run CodeSleuth context-graph smoke tests;
7. verify disabled CodeSleuth operation does not require Graphify;
8. update the pinned package version (or vendored gitlink, if that later model is
   accepted) in one reviewable PR;
9. update provider provenance metadata and this compatibility record if behavior
   changed.

Do not track mutable upstream `v8` directly at runtime.

## 14. Security and permission gate

Enabling the initial Graphify structural provider grants only local read/parse work over
CodeSleuth-selected tracked files and local writes under CodeSleuth ignored state.

It does **not** grant:

```text
web access
URL ingest
LLM/API calls
project-local provider credential loading
Git hook installation
host Skill installation
MCP/HTTP server startup
external-directory access
writes to tracked repository files
```

Any later feature needing one of those capabilities must ask through the host's normal
permission model and be separately documented/tested.

## 15. Adoption gate

Graphify may graduate from `incubating` to `supported optional provider` only when all of
the following are true:

- [x] M1 scoped Mermaid rendering is complete or explicitly shown unnecessary;
- [ ] optional Graphify runtime is isolated and absent by default;
- [ ] explicit tracked-file input policy is implemented;
- [ ] exact relation/node mapping is documented and tested;
- [ ] Git/blob promotion gate is implemented;
- [ ] inference cannot be mislabeled verified;
- [ ] large-output bounds are enforced before model exposure;
- [ ] provider cache is local/rebuildable and lifecycle-clean;
- [ ] no Graphify host Skill/hook/MCP/global side effects are required;
- [ ] dependency provenance/version is visible;
- [ ] Linux/macOS/Windows smoke coverage exists;
- [ ] representative corpus comparison demonstrates a meaningful reduction in agent
      mapping cost without unacceptable precision loss;
- [ ] update and uninstall/remove behavior is tested;
- [ ] upstream license/NOTICE obligations are documented for the chosen distribution
      model.

Until then, Graphify remains a roadmap candidate, not a production dependency.

## 16. Practical recommendation

The full M1-M5 feature implementation is now available on its feature branch. Keep
Graphify classified as incubating until the remaining adoption gates above—especially
Linux/macOS execution and distribution compatibility—are independently satisfied.

The likely high-value end state is deliberately boring:

```text
Graphify does deterministic AST discovery.
CodeSleuth decides what is allowed, verifies Git identity, normalizes semantics,
bounds context, stores the derived projection, and renders Mermaid.
The host model reasons over the bounded result and reopens exact source for findings.
```

That division uses Graphify where it is stronger without outsourcing CodeSleuth's
source/evidence discipline or growing a second analysis runtime.
