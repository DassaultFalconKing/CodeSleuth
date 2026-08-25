# Changelog

Numbered CodeSleuth releases are recorded here. Release identity is the accepted `main` commit plus immutable `vX.Y.Z` tag; the source version authority is the root `VERSION` file.

## [0.3.9-Rc0] - 2026-08-25

Temporary pre-release/update-channel snapshot. The repository owner explicitly authorized `main` to carry this RC as an exception so the self-update path, which fetches `origin/main`, can be tested end-to-end. This is **not** the stable numbered-release publication pattern and is intentionally not an immutable GitHub Release/tag.

### Test-channel integration

- verified self-update and restart supervision from PR #16;
- maintained Russian and Ukrainian README translations from PR #17;
- bounded compatible dependency ranges from PR #14;
- cross-platform acceptance CI and metadata-derived product version authority staged for 0.4.0;
- Textual bootstrap honors the manifest range `textual>=8.2.8,<9` and records the actual installed Textual version instead of pretending the lower bound was installed;
- CLI, TUI bootstrap, Verify/smoke and installer obtain the CodeSleuth product version from source or installed metadata rather than numeric fallback constants.

## [0.4.0] - Unreleased

First release prepared under the release-only `main` contract after the temporary 0.3.9-Rc0 update-channel exception is retired.

### Added

- terminal-native CodeSleuth control console with Home, Review, Evidence, Tools and Settings surfaces;
- repository-deep-review, reports and feature-porting Skills plus bounded specialist subagents;
- durable review state, deterministic inventory and bounded repository context graph with optional Mermaid projection;
- local analytical report workspace under `.codesleuth/reports/`;
- reversible install/update/bind/unbind/uninstall lifecycle with conflict-safe restoration;
- read-only repository evidence over MCP, with NovaClaw as the first tested external host;
- comprehensive operator/CLI/TUI/extension README and text-only documentation policy;
- cross-platform Python acceptance gate plus frozen Bun durable-state/context-graph smokes.

### Hardened

- MCP Git evidence boundary: sanitized Git environment, no optional index refresh, fsmonitor disabled, textconv/external diff disabled, bounded subprocess output, unresolved-index fail-closed behavior, and regular-file-only reads;
- source-checkout Update explicitly tracks `origin/main` instead of trusting stale local branch tracking configuration;
- active TUI surfaces stay visible across narrow viewports;
- logo, Footer and side panels can be collapsed independently; the right Keys/Help panel can be dismissed for the current session;
- project-local ignore policy avoids silently rewriting a tracked root `.gitignore`;
- dependency binding remains independent from installed runtime state and refuses unsafe/recursive submodule operations.

### Release-process changes

- after the temporary RC exception, `main` becomes the numbered-release line;
- active release integration uses `dev/release-X.Y.Z`, with feature/chore/fix branches feeding it;
- runtime version output is required to derive from source or installed metadata instead of numeric fallback constants.

### Known release decisions

- The public repository currently needs an explicit license decision before `0.4.0` is published as a public numbered release.
- GitHub `main` protection/ruleset must require the acceptance gate; the repository setting is not encoded by source files alone.
