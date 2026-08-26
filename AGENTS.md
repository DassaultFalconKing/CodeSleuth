# CodeSleuth agent instructions

CodeSleuth is a discipline layer and control panel around a host coding agent. The host owns the model, primary controller, session, permissions, tool routing, and execution. Do not introduce a second CodeSleuth runtime, supervisor, or general-purpose tool router.

## Read the right authority

- Product/manual truth: [`README.md`](README.md).
- Product ownership and extension boundaries: [`docs/CODESLEUTH-PRODUCT-CONTRACT.md`](docs/CODESLEUTH-PRODUCT-CONTRACT.md).
- Install/bind/unbind/uninstall truth: [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md).
- Coding-agent operator workflow: [`docs/LLM-OPERATOR.md`](docs/LLM-OPERATOR.md).

If the user asks you to install, configure unattended, use, update, bind, unbind, remove, or prepare a release-clean repository with CodeSleuth, read `docs/LLM-OPERATOR.md` before changing the target repository.

## Source-development invariants

- Make the smallest change that satisfies the current contract.
- Preserve OpenCode `build` as the primary controller for the full OpenCode integration.
- Do not treat context graphs, Mermaid, scout summaries, or prior reports as stronger evidence than exact current source.
- Preserve pre-existing OpenCode/user configuration and conflict-safe lifecycle behavior.
- Do not widen permissions, commit, push, reset, clean, or discard user work unless the user explicitly asks for that operation.
- Run the relevant executable checks and only report checks that actually ran successfully.

## Development gates

For ordinary Python/documentation changes:

```bash
python -m pytest
ruff check .
```

For durable-state/context-graph changes also run:

```bash
bun install --frozen-lockfile
bun tests/review_state_smoke.ts
bun tests/context_graph_smoke.ts
```

For MCP changes, `python -m pytest` already includes MCP tests after `python -m pip install -r requirements-dev.txt`. Do not skip those tests in release acceptance.

Nested `AGENTS.md` files, if introduced later, may add narrower instructions for their subtree. Direct user instructions still take precedence.

<!-- BEGIN CodeSleuth reports -->
Analytical reports for this worktree live in `.codesleuth/reports/` (see `INDEX.md`). Format: `.opencode/CODESLEUTH-REPORTS.md`. OpenCode `build` writes them. They are local-only by default because reports may contain source excerpts or credentials; reuse them in this worktree, and only publish sanitized reports or guidance intentionally when cross-clone reuse is desired.
<!-- END CodeSleuth reports -->
