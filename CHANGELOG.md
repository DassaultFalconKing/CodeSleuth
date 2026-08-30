# Changelog

Numbered CodeSleuth releases are recorded here. Published release identity is the promoted exact `main` commit plus the immutable `vX.Y.Z` tag; the source version authority is the root `VERSION` file.

## [0.4.0-Rc4] - 2026-08-30

Release-readiness repair candidate for the platform-native GitHub-to-OpenCode EHA invocation boundary. Rc3 is repository-accepted on its own exact SHA and repaired the report-persistence ownership conflict, but fresh EHA run `33334931489` then exposed a separate Windows adapter error before canonical `/eha-test` could start.

### Repairs

- selects the shipped OpenCode launcher by host platform instead of asking Windows CPython to execute the POSIX extensionless `opencode-review` shell script;
- keeps the existing POSIX `pack/.opencode/bin/opencode-review` path unchanged;
- invokes the existing Windows `pack/.opencode/bin/opencode-review.ps1` through `pwsh`, with Windows PowerShell fallback, and fails closed if the required platform launcher is unavailable;
- adds focused regression coverage for POSIX launcher selection, Windows PowerShell launcher selection, and missing-PowerShell failure.

### Evidence boundary

- Rc3 EHA run `33334931489` verified the exact `fff3f3998e980155f34c182ecf34d28e44478691` release-stream head and passed trusted host setup before failing with `WinError 193`; it is an adapter execution `ERROR`, not a SIB0/SIB1/SIB2 `FAIL`;
- Rc4 changes the transport adapter only. EHA authority, durable ledger semantics, persistence wiring, exact-head identity checks, permissions, and SIB policy remain unchanged;
- Rc4 has a distinct exact source identity and must earn fresh repository acceptance and fresh canonical EHA. No Rc3 PASS evidence transfers to it.

## [0.4.0-Rc3] - 2026-08-30

Release-readiness repair candidate for the GitHub-to-OpenCode EHA persistence boundary. Rc2 remains repository-accepted on its exact SHA, but remote EHA run `33276120595` stopped fail-closed before OpenCode created a canonical campaign because the Rc2 application tree still tracked `.codesleuth/reports/**`, the same path the bridge must bind to host-persistent report storage.

### Repairs

- removes the accidentally tracked local `.codesleuth/reports/` mirror from the current application tree while preserving its historical Git commits; the canonical shared report transport remains the separate orphan `reports` branch;
- keeps the existing bridge refusal to overwrite an already-present persistence path: the repair removes the ownership conflict instead of weakening the safety check;
- adds a repository regression requiring the application tree to track no `.codesleuth/reports/**` paths and requiring `.codesleuth/` to remain ignored;
- preserves `.opencode/state` as the durable EHA authority path and `.codesleuth/reports` as a derived report mirror, both eligible for host-persistent binding only when absent from the exact application tree.

### Evidence boundary

- Rc2 EHA run `33276120595` is an adapter/persistence `ERROR`, not a SIB0/SIB1/SIB2 `FAIL`: the bridge stopped before invoking the canonical OpenCode `/eha-test` Playbook or recording a new durable campaign;
- the self-hosted `codesleuth-eha` runner did accept the Rc2 job and passed trusted-source/OpenCode-host setup, so runner availability is no longer the identified root cause;
- Rc3 has a distinct source identity. Rc2 repository acceptance and the failed bridge attempt do not transfer acceptance to Rc3; the literal Rc3 SHA must earn fresh hosted acceptance and fresh canonical EHA.

## [0.4.0-Rc2] - 2026-08-29

Release-readiness repair candidate for the 0.4.0 prerelease line. Rc1 remains a historical repository-green prerelease, but Rc2 has a distinct source identity and must earn its own exact-head acceptance rather than inheriting Rc1 evidence.

### Repairs

- restores the branded Settings controls for repository-policy enforcement and context-graph provider selection, with a focused regression that opens the real CodeSleuth configuration screen and exercises inherited settings collection;
- moves that Settings regression into the canonical TUI acceptance profile so the configuration surface cannot disappear while Home/Tools screenshots remain green;
- narrows purge cleanup from recursive `.opencode/**/__pycache__` and bytecode deletion to cache entries corresponding to CodeSleuth-managed Python source files that did not pre-exist and are not being preserved as local changes;
- removes only the exact CodeSleuth transient TUI backup file instead of claiming the whole `.opencode/state/tui-backups/` directory;
- adds a disposable install/Verify/purge regression proving unmanaged bytecode and sibling TUI state survive while CodeSleuth-owned runtime residue is removed.

### Prerelease policy

- no stable tag or GitHub Release is created for this candidate;
- no SIB evidence transfers from an ancestor, Rc1, source branch, PR head, merge ref, or tree-equivalent commit;
- the literal Rc2 commit must pass the complete hosted acceptance profile before it may become the current prerelease source;
- GitHub promotion-ref protection remains a separate pre-publication repository-host requirement tracked by the surviving governance issue; ref protection never substitutes for exact-SHA acceptance.

## [0.4.0-Rc1] - 2026-08-29

Temporary owner-authorized prerelease on the existing `main` self-update channel. This snapshot is intentionally not a stable numbered release, immutable tag, or GitHub Release; `SIB` remains the separately accepted baseline.

### Included

- retained graph and TUI export surfaces with exact-source provenance and bounded output;
- strict UTF-8 Git subprocess decoding and physical report-index reconstruction;
- declared publication routes for report-producing Skills, with installed-pack integrity coverage;
- deterministic TUI modal-abort synchronization and the Evidence-Based Code Analysis vocabulary/contract hardening;
- conflict-safe purge removal of generated Python bytecode and transient TUI backup residue, covered through a real disposable install/Verify/uninstall round trip;
- the accepted Mermaid/Graphify runtime and hosted sandbox repair already present in the 0.4.0 line.

### Downstream feedback boundary

- reviewed the Aleph_Rugent tooling/skills feedback recorded at `bf1320a` against the exact CodeSleuth source integrated there (`881d7af`);
- the report UTF-8, index-lifecycle, publication-route, Windows portability, and hosted Mermaid concerns are covered by this candidate and its canonical gates;
- Aleph_Rugent domain findings (collection identifiers, retrieval continuations, vector limits, lease ownership, image pins, worker wiring, and its missing project-owned protected-capability registry) remain downstream application work and are not misreported as CodeSleuth fixes;
- Aleph_Rugent binds CodeSleuth as an exact Git dependency, so it remains deliberately pinned until its gitlink is advanced explicitly; floating installations continue to update from `origin/main`.

### Prerelease policy

- no parallel download/update branch is introduced;
- no stable tag or GitHub Release is created for this snapshot;
- promotion requires the exact committed candidate to pass the complete local and hosted acceptance profiles; a failing SHA remains failed and any repair must use a new SHA.

## [0.4.0] - Unreleased

First release prepared under the release-only `main` contract and the `dev/release-0.4.0` candidate stream.

### Added

- terminal-native CodeSleuth control console with Home, Review, Evidence, Tools and Settings surfaces;
- atomic on-demand Skills plus manifest-driven, step-isolated Playbooks for repository review, documentation, mapping, protected-capability assessment, feature refit/port work, and SIB/EHA campaigns;
- thin OpenCode Command entry points that route multi-step work through Playbooks while leaving the host `build` agent as the primary controller;
- durable review state, exact-source findings, append-only finding-amendment and EHA/SIB/repair evidence, deterministic inventory, and bounded repository context graphs with optional Mermaid projection;
- bounded scoped Mermaid neighborhood rendering that reuses the context-graph query selection semantics instead of introducing a second traversal implementation;
- uniform versioned provenance envelopes for all Mermaid views, isolated exact-pinned Mermaid parser/render QA, and an explicitly enabled Graphify structural provider with tracked-input validation, corpus hardening, TUI/provider lifecycle visibility, and topology-assisted bounded root selection;
- Protected Capability Registry with code/docs/test provenance, dependency/impact metadata, contract fingerprints, contract-owned forbidden-regression ledgers, and dependency-aware assessment tooling;
- Exact-Head Acceptance discipline for SIB0/SIB1/SIB2, including immutable target identity, failed-target repair lineage, and literal release-stream candidate selection;
- a GitHub-to-OpenCode EHA bridge: owner-gated remote requests execute the real `/eha-test` on a trusted self-hosted OpenCode runner while the canonical durable `eha.ndjson` ledger remains acceptance authority;
- Semantic Refit contract separating semantic/normative claim status from delivery disposition and preserving evidenced semantic continuity across divergent or stale work;
- a negative-claim evidence protocol that records forbidden states, constructive invariants, counterexample predicates, scope, oracle and provenance, with adversarial counterexample search rather than happy-path-only evidence;
- optional managed `AGENTS.md` workflow enforcement without transferring host execution ownership away from OpenCode;
- local analytical report workspace under `.codesleuth/reports/` as a derived human-readable view of structured evidence;
- reversible install/update/bind/unbind/uninstall lifecycle with conflict-safe restoration;
- read-only repository evidence over MCP, with NovaClaw as the first tested external host;
- comprehensive operator/CLI/TUI/extension documentation and text-first documentation policy;
- compact root `AGENTS.md` plus `docs/LLM-OPERATOR.md` for cross-agent install/configure/remove workflows;
- machine-readable `pack/.opencode/codesleuth-naming.json` inventory for the remaining `review-pack` to CodeSleuth namespace cutover;
- maintained Russian and Ukrainian README translations with blob-parity checks;
- verified self-update path: post-update Verify, restart request, and TUI bootstrap supervision;
- a seven-job repository acceptance workflow: Python 3.10/3.12 on Linux and Windows, Bun durable-state/context-graph smokes, headless TUI visual regression with diagnostic artifacts, and an isolated Graphify-enabled Ubuntu/Python 3.12 profile.

### Hardened

- MCP Git evidence boundary: sanitized Git environment, no optional index refresh, fsmonitor disabled, textconv/external diff disabled, bounded subprocess output, unresolved-index fail-closed behavior, regular-file-only reads, and filesystem reads bounded before oversized evidence is allocated;
- durable review identities use collision-resistant IDs so a rapid new review cannot silently reuse an earlier findings ledger;
- finding amendments preserve append-only correction/supersession/retraction/closure history instead of rewriting prior evidence in place;
- compaction degrades safely on corrupt/torn local review state, preserves valid neighboring finding evidence, and reports degraded completeness instead of aborting the host session;
- EHA verdicts are immutable per campaign/SIB level, and a failed exact SHA cannot be rehabilitated by starting another campaign on the same durable evidence history;
- the GitHub EHA bridge rejects stale release-head requests, exact SHAs with persisted FAIL evidence, disposable in-checkout evidence storage, controller-source drift, source mutation, and public leakage of the full OpenCode transcript;
- Mermaid comments and scoped selection metadata escape hostile source-derived keys/scopes so untrusted content cannot be smuggled into generated markup or comments;
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

- `main` is the numbered-release promotion line;
- active release integration uses `dev/release-X.Y.Z`, with feature/chore/fix/refit branches feeding it;
- SIB candidates are selected from the literal exact head of the active release stream and receive fresh EHA rather than inheriting evidence from source branches, prior CI, PR heads, merge refs, ancestors, or tree-equivalent commits;
- the ordinary seven-job GitHub Actions repository acceptance workflow is an exact-checkout development/repository gate and does not itself create SIB0/SIB1/SIB2 verdicts;
- canonical EHA executes through OpenCode `/eha-test`, calls the durable `eha_state_*` tools, and binds SIB verdicts to one exact candidate SHA;
- GitHub may act as a remote trigger/execution envelope for that canonical OpenCode EHA, but GitHub workflow status is a derived transport signal rather than acceptance authority;
- runtime version output is required to derive from source or installed metadata instead of numeric fallback constants;
- GNU AGPL v3 is the explicit repository license for this release line.

### Known release decisions and pre-publish checks

- GitHub `main` protection/ruleset must require the intended repository acceptance gate before public release promotion. This repository-host setting is not established by source documentation; maintainers must verify it in GitHub before advancing a public release.
- Remote GitHub-triggered EHA requires a trusted self-hosted runner carrying the `codesleuth-eha` label, a working OpenCode/provider configuration, and persistent host storage outside the disposable Actions checkout. The source bridge deliberately fails rather than substituting a GitHub-hosted runner or temporary artifact store for durable EHA authority.
- Human/operator acceptance remains a deliberate final release-readiness check after automated EHA, especially for installation, TUI usability, update/restart behavior, and external-host operation on a real workstation.
