# Changelog

Numbered CodeSleuth releases are recorded here. Release identity is the accepted `main` commit plus immutable `vX.Y.Z` tag; the source version authority is the root `VERSION` file.

## [0.4.0] - Unreleased

First release prepared under the release-only `main` contract.

### Added

- terminal-native CodeSleuth control console with Home, Review, Evidence, Tools and Settings surfaces;
- repository-deep-review, reports and feature-porting Skills plus bounded specialist subagents;
- durable review state, deterministic inventory and bounded repository context graph with optional Mermaid projection;
- local analytical report workspace under `.codesleuth/reports/`;
- reversible install/update/bind/unbind/uninstall lifecycle with conflict-safe restoration;
- read-only repository evidence over MCP, with NovaClaw as the first tested external host;
- comprehensive operator/CLI/TUI/extension README and text-only documentation policy;
- compact root `AGENTS.md` plus `docs/LLM-OPERATOR.md` for cross-agent install/configure/remove workflows;
- machine-readable `pack/.opencode/codesleuth-naming.json` inventory for the remaining `review-pack` to CodeSleuth namespace cutover;
- maintained Russian and Ukrainian README translations with blob-parity checks;
- verified self-update path: post-update Verify, restart request, and TUI bootstrap supervision;
- cross-platform Python acceptance gate plus frozen Bun durable-state/context-graph smokes.

### Hardened

- MCP Git evidence boundary: sanitized Git environment, no optional index refresh, fsmonitor disabled, textconv/external diff disabled, bounded subprocess output, unresolved-index fail-closed behavior, and regular-file-only reads;
- source-checkout Update explicitly tracks `origin/main` instead of trusting stale local branch tracking configuration;
- active TUI surfaces stay visible across narrow viewports;
- logo, Footer and side panels can be collapsed independently; the right Keys/Help panel can be dismissed for the current session;
- project-local ignore policy avoids silently rewriting a tracked root `.gitignore`;
- TUI collapse/restore toggles remain immediately clickable; Tools actions stay on the operational surface at 120x35;
- dependency binding remains independent from installed runtime state and refuses unsafe/recursive submodule operations;
- installed version metadata may be read from `codesleuth.json` or `review-pack.json`, and fails closed if both exist and differ;
- isolated TUI bootstrap derives the compatible Textual range from `requirements-tui.txt`, accepts any installed version inside that range, and records the actual installed Textual version instead of a lower-bound literal.

### Release-process changes

- `main` becomes the numbered-release line;
- active release integration uses `dev/release-X.Y.Z`, with feature/chore/fix branches feeding it;
- runtime version output is required to derive from source or installed metadata instead of numeric fallback constants.

### Known release decisions

- The public repository currently needs an explicit license decision before `0.4.0` is published as a public numbered release.
- GitHub `main` protection/ruleset must require the acceptance gate; the repository setting is not encoded by source files alone.
