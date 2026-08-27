# Optional Graphify structural provider

**Status:** incubating optional provider; builtin repository mapping remains default  
**Package:** `graphifyy==0.9.50`  
**Upstream tag/commit:** `v0.9.50` / `43d54acbfa9e731f7a592bb582c1f4b9d48ed73e`

The M2 adapter calls Graphify's local `graphify.extract.extract(paths, root=...,` 
`parallel=False)` library boundary. It does not call the Graphify CLI, installer,
Skill, hooks, MCP/HTTP server, global graph, reports, HTML exporter, semantic/LLM
providers, or credential paths.

## Explicit installation

The provider is absent from normal CodeSleuth dependencies. For the verified Windows
Python 3.14 profile, install its isolated lock explicitly:

```text
python -m pip install --target .runtime/graphify-provider -r tools/graphify-provider/requirements-lock.txt
```

`.runtime/` is ignored and rebuildable. Other Python/platform profiles must resolve and
record their own compatible exact lock before they can become supported; the shorter
`requirements.txt` records the upstream top-level pin but is not a cross-platform
transitive lock.

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
when both endpoints carry exact tracked source identity. Candidate output is bounded
before it becomes model-visible, and edges to omitted nodes are removed.

Network socket creation is denied during extraction, parallel extraction is disabled,
and provider cache is confined to a disposable temporary directory. The response
reports provider version/commit, exact input provenance, selection/truncation and
bounded diagnostics. It remains a candidate structural projection: CodeSleuth Git/blob
validation is authority.
