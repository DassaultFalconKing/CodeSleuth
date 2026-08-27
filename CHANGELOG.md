# Changelog

Numbered CodeSleuth releases are recorded here. Release identity is the accepted `main` commit plus immutable `vX.Y.Z` tag; the source version authority is the root `VERSION` file.

## [0.4.0] - Unreleased

First release prepared under the release-only `main` contract.

### Added

- terminal-native CodeSleuth control console with Home, Review, Evidence, Tools and Settings surfaces;
- atomic on-demand Skills plus manifest-driven, step-isolated Playbooks for repository review, documentation, mapping, protected-capability assessment, feature refit/port work, and SIB/EHA campaigns;
- thin OpenCode Command entry points that route multi-step work through Playbooks while leaving the host `build` agent as the primary controller;
- durable review state, exact-source findings, append-only EHA/SIB/repair evidence, deterministic inventory, and bounded repository context graphs with optional Mermaid projection;
- Protected Capability Registry with code/docs/test provenance, dependency/impact metadata, contract fingerprints, and contract-owned forbidden-regression ledgers;
- Exact-Head Acceptance discipline for SIB0/SIB1/SIB2, including immutable target identity, failed-target repair lineage, and literal release-stream candidate selection;
- Semantic Refit contract separating semantic/normative claim status from delivery disposition and preserving evidenced semantic continuity across divergent or stale work;
- local analytical report workspace under `.codesleuth/reports/` as a derived human-readable view of structured evidence;
- reversible install/update/bind/unbind/uninstall lifecycle with conflict-safe restoration;
- read-only repository evidence over MCP, with NovaClaw as the first tested external host;
- comprehensive operator/CLI/TUI/extension documentation and text-first documentation policy;
- compact root `AGENTS.md` plus `docs/LLM-OPERATOR.md` for cross-agent install/configure/remove workflows;
- machine-readable `pack/.opencode/codesleuth-naming.json` inventory for the remaining `review-pack` to CodeSleuth namespace cutover;
- maintained Russian and Ukrainian README translations with blob-parity checks;
- verified self-update path: post-update Verify, restart request, and TUI bootstrap supervision;
- canonical six-job exact-head acceptance matrix: Python 3.10/3.12 on Linux and Windows, Bun durable-state/context-graph smokes, and headless TUI visual regression with uploaded diagnostic artifacts.

### Hardened

- MCP Git evidence boundary: sanitized Git environment, no optional index refresh, fsmonitor disabled, textconv/external diff disabled, bounded subprocess output, unresolved-index fail-closed behavior, regular-file-only reads, and filesystem reads bounded before oversized evidence is allocated;
- durable review identities use collision-resistant IDs so a rapid new review cannot silently reuse an earlier findings ledger;
- compaction degrades safely on corrupt/torn local review state, preserves valid neighboring finding evidence, and reports degraded completeness instead of aborting the host session;
- EHA verdicts are immutable per campaign/SIB level, and a failed exact SHA cannot be rehabilitated by another campaign in the same durable review ledger;
- source-checkout Update explicitly tracks `origin/main` instead of trusting stale local branch tracking configuration;
- active TUI surfaces stay visible across narrow viewports;
- logo, Footer and side panels can be collapsed independently; the right Keys/Help panel can be dismissed for the current session;
- project-local ignore policy avoids silently rewriting a tracked root `.gitignore`;
- TUI collapse/restore toggles remain immediately clickable; Tools actions stay on the operational surface at 120x35;
- Verify and Update actions are covered by exact-head visual interaction checks for single dispatch and immediate visible operator feedback;
- dependency binding remains independent from installed runtime state and refuses unsafe/recursive submodule operations;
- installed version metadata may be read from `codesleuth.json` or `review-pack.json`, and fails closed if both exist and differ;
- isolated TUI bootstrap derives the compatible Textual range from `requirements-tui.txt`, accepts any installed version inside that range, and records the actual installed Textual version instead of a lower-bound literal.

### Release-process changes

- `main` becomes the numbered-release line;
- active release integration uses `dev/release-X.Y.Z`, with feature/chore/fix branches feeding it;
- SIB candidates are selected from the literal exact head of the active release stream and receive fresh EHA rather than inherited evidence from source branches or tree-equivalent commits;
- runtime version output is required to derive from source or installed metadata instead of numeric fallback constants;
- GNU AGPL v3 is the explicit repository license for this release line.

### Known release decisions and pre-publish checks

- GitHub `main` protection/ruleset must require the canonical acceptance gate before the public release is promoted. Source documentation cannot establish that repository-host setting; maintainers must verify it in GitHub before advancing `main`.
- Human/operator acceptance remains a deliberate final release-readiness check after automated SIB2/EHA, especially for installation, TUI usability, update/restart behavior, and external-host operation on a real workstation.
