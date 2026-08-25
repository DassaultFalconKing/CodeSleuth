# NovaClaw MCP adapter

**Classification:** TOOL-EXTENSION + DOCS  
**Runtime owner:** NovaClaw  
**Evidence provider:** CodeSleuth

The adapter exposes bounded, read-only CodeSleuth repository evidence over MCP stdio. NovaClaw owns the model session, controller, permissions, tool routing, and report prose. CodeSleuth does not inject a system prompt or start a second agent loop.

## Install the MCP runtime

Use a virtual environment rather than installing packages system-wide:

```powershell
python -m venv .venv-mcp
.\.venv-mcp\Scripts\python.exe -m pip install -r requirements-mcp.txt
```

## Register one repository with NovaClaw

MCP bindings are instance configuration in NovaClaw's SQLite store. Register the server through the supported CLI surface and use absolute paths so the binding does not depend on the launch directory:

```powershell
$env:NOVACLAW_DB = "C:\path\to\isolated\instance.db"
$env:XDG_DATA_HOME = "C:\path\to\isolated\data"
$env:XDG_CONFIG_HOME = "C:\path\to\isolated\config"

bun run --conditions=browser C:\path\to\novaclaw\packages\novaclaw\src\index.ts `
  mcp add codesleuth -- `
  C:\path\to\.venv-mcp\Scripts\python.exe `
  -m codesleuth_mcp.server --repo C:\path\to\target-repository
```

Set the MCP process working directory to the CodeSleuth checkout through NovaClaw Settings if CodeSleuth is not installed into the Python environment. Alternatively set `PYTHONPATH` to the checkout when registering the local server.

Restart an already-running NovaClaw instance after changing MCP configuration.

## Tools

- `overview` — HEAD, branch, dirty state, tracked-file count, and bounded shape summaries.
- `inventory` — cursor-based tracked paths with exact index blob ids.
- `read_evidence` — exact source lines with current and index blob ids.
- `search` — bounded Git grep returning path, line, and matching text.
- `test_map` — likely tests/build/CI surfaces, explicitly not a coverage claim.
- `diff_evidence` — bounded unstaged or staged diff tied to current HEAD.

NovaClaw prefixes MCP tools with the configured server name, so these normally appear to the model as `codesleuth_overview`, `codesleuth_read_evidence`, and so on.

## Safety boundary

- The repository root is fixed when the MCP child starts; tools cannot select another directory.
- Git subprocesses receive a null stdin so they cannot consume or hold the MCP stdio wire. Inherited
  `GIT_*` variables are removed before repository discovery, so caller state cannot redirect probes to
  another index, object store, or worktree.
- Evidence probes disable optional locks and fsmonitor. Diffs also disable external diff and textconv,
  so read-only inspection neither refreshes the index nor launches repository-configured helpers.
- File reads accept tracked files only, reject path traversal and binary content, and cap bytes/lines.
- An unresolved index has no singular blob identity, so inventory and reads fail closed until merge
  stages are resolved.
- Search and diff output is streamed and the Git child is terminated at the evidence budget; bounds
  apply while producing evidence, not only after complete output has been captured.
- The adapter writes no project files and makes no coverage claim.
- A model-generated relationship remains inference until exact source is reopened through `read_evidence`.

## Verification

```powershell
.\.venv-mcp\Scripts\python.exe -m pytest -q tests\test_mcp_server.py
.\.venv-mcp\Scripts\ruff.exe check codesleuth_mcp tests\test_mcp_server.py
```
