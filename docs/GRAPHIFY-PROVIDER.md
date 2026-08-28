# Optional Graphify structural provider

**Status:** incubating optional provider; builtin repository mapping remains default
**Package:** `graphifyy==0.9.50`
**Upstream tag/commit:** `v0.9.50` / `43d54acbfa9e731f7a592bb582c1f4b9d48ed73e`

The M2 adapter calls Graphify's local `graphify.extract.extract(paths, root=...,`
`parallel=False)` library boundary. It does not call the Graphify CLI, installer,
Skill, hooks, MCP/HTTP server, global graph, reports, HTML exporter, semantic/LLM
providers, or credential paths.

## Explicit installation

The provider is absent from normal CodeSleuth dependencies. An installed CodeSleuth
instance carries the hash-locked manifest inside its managed pack and exposes one
explicit lifecycle action (there is no automatic installation):

```text
.opencode/bin/codesleuth-project --install-graphify-runtime .
```

The action executes pip with `--require-hashes --only-binary=:all:` into a staging
directory and publishes `.runtime/graphify-provider` only after success. It also writes
`codesleuth-runtime.json`, binding provider identity to the absolute interpreter that
performed the install. Provider execution uses only that recorded interpreter and
fails closed if the manifest is missing, malformed, tampered, or stale; it never falls
back to ambient `python`. In a source checkout, the equivalent development command uses
`tools/graphify-provider/requirements-lock.txt`. `.runtime/` is ignored and rebuildable.

## Adapter request

Send JSON on stdin:

```json
{
  "root": "C:/absolute/path/to/worktree",
  "files": ["src/app.py", "src/worker.ts"],
  "nodeLimit": 200,
  "edgeLimit": 500
}
```

```text
python scripts/graphify_adapter.py < request.json
```

The explicit root must equal the Git worktree root. Every path must be normalized,
stage-0 tracked, regular, non-symlink and beneath that root. The adapter records index
and working blob ids, content SHA-256 and byte size before importing Graphify. Untracked
files never enter the provider. Dirty tracked files may be structurally inspected but
cannot produce `verified_source` candidates.

Only exact `imports` and `calls` relations enter the initial closed mapping. Unknown
relations are counted and dropped. `INFERRED` and `AMBIGUOUS` relations remain
`review_inference`; an `EXTRACTED` relation is eligible for verified promotion only
when both endpoints carry exact tracked source identity and the relation's source file
and one-based line resolve inside the captured source. Bogus, zero, out-of-range, or
wrong-file locations fail closed to `review_inference`. Candidate output is bounded
before it becomes model-visible, and edges to omitted nodes are removed.

Python socket `connect` and `create_connection` calls are denied before provider import
and through extraction. This is narrow in-process socket isolation, not an OS sandbox
or a universal no-network proof. Parallel extraction is disabled, and provider cache
is confined to a disposable temporary directory. The response
reports provider version/commit, exact input provenance, selection/truncation and
bounded diagnostics. It remains a candidate structural projection: CodeSleuth Git/blob
validation is authority.

## Repository-map integration

`repo_context_provider_status` reports `builtin` (the default) or the optional
`graphify` runtime, including installed/compatible state, origin, capabilities,
permissions and removal path. `repo_context_provider_extract` requires an explicit
provider choice. Both provider tools are denied globally and allowed only to the host
`build` controller in the managed OpenCode policy. Its builtin branch delegates to the established source-review flow;
its Graphify branch accepts only an explicit tracked manifest and returns bounded
candidate `projectionInput` values.

The repository-map Playbook reviews those candidates and sends selected values through
`repo_context_graph_save`, which independently revalidates current Git blobs and the
closed node/edge contract. The provider tool never persists a projection, silently
installs dependencies, or falls back from an explicitly requested incompatible
Graphify runtime.

Remove only the ignored optional runtime through the installed lifecycle CLI:

```text
.opencode/bin/codesleuth-project --remove-graphify-runtime .
```

This permanently removes `.runtime/graphify-provider` and nothing else; reinstall from
the exact lock to recover it. Normal CodeSleuth uninstall does not silently broaden its
scope to this separately installed dependency.

The canonical enabled-provider acceptance profile is Ubuntu with Python 3.12. Windows
and other interpreter/platform combinations retain fixture and lifecycle coverage but
are compatibility-gated, not claimed as supported enabled-runtime profiles during
incubation.

## Topology-assisted selection

The adapter may additionally run Graphify's local `build()` and `cluster()` over the
same already bounded extraction. Returned nodes carry an optional community id and
undirected degree-centrality score. These fields are `derivedSelectionHintsOnly`: they
never enter node keys, projection identity, source provenance or evidence origin.

`repo_context_graph_topology` accepts the bounded provider result rather than separate
caller-authored version/commit strings, binds its output to a SHA-256 of that payload,
and matches the embedded hints against an already saved projection
by its existing closed `(kind, key)` identity. It drops and counts stale hints, then
deterministically selects bounded `community_hubs` or validated `cross_community`
bridge roots. When no cross-community projection edge exists it reports a fallback to
community hubs. Ties use invariant Unicode code-point ordering rather than host locale.
The returned roots must be passed unchanged to both
`repo_context_graph_query` and `repo_context_graph_mermaid`; those tools continue to
share the accepted M1 neighborhood traversal and omitted-node edge safety.
