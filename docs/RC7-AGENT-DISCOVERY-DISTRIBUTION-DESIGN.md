# RC7 Agent Discovery + Distribution Design

**Status:** USER-APPROVED RC7 IMPLEMENTATION DESIGN
**Scope:** N2 agent/operator discovery + N3 portable distribution namespace
**Runtime base for N2:** `integration/rc7 @ 64c1986ab26c16957c7f126106f7dc2020edfcae`
**Authority boundary:** This design does not override frozen evidence, EHA, SIB, ledger, repair, or host-execution authorities.

## Goal

Any coding agent that opens a repository with CodeSleuth installed should immediately discover where CodeSleuth reports, durable review state, context graphs, playbooks, skills, and distribution source live. Operators must be able to browse playbooks without memorizing internal IDs. Portable skills must use a collision-resistant `codesleuth-*` namespace and be distributable through thin host adapters rather than divergent semantic forks.

## N2: installed-repository discovery

A normal CodeSleuth project install/update MUST materialize an always-on, CodeSleuth-owned discovery block in root `AGENTS.md`. This is separate from the existing opt-in workflow-rules block because `policy.enforceAgentsMdRules` remains optional and defaults off.

The discovery block owns only text between distinct CodeSleuth markers and must use the existing fail-closed ownership discipline: preserve user bytes, reject malformed/duplicate managed markers, update idempotently, and remove only CodeSleuth-owned text during uninstall/purge. If CodeSleuth created `AGENTS.md` solely for managed content, lifecycle cleanup may remove the empty file; otherwise user content survives byte-for-byte where ownership anchors still prove the boundary.

The concise discovery map must identify:

- human-readable reports: `.codesleuth/reports/` and `.codesleuth/reports/INDEX.md`, explicitly derived/non-authoritative;
- durable review/evidence continuation: `.opencode/state/reviews/`;
- derived context graphs: `.opencode/state/context-graphs/`, explicitly navigation/rebuildable rather than source evidence authority;
- project playbook overlay: `.opencode/playbooks/`;
- built-in CodeSleuth playbooks through the installed distribution pack;
- browse command `/codesleuth/playbooks` and run command `/codesleuth/playbook <id>`;
- installed CodeSleuth skills under the future `codesleuth-*` namespace;
- canonical distribution source `DassaultFalconKing/CodeSleuth`.

Self-install/maintainer checkout behavior remains governed by existing lifecycle contracts and must not accidentally mutate the source checkout's maintainer `AGENTS.md` through target-install policy.

## N2: playbook discoverability

Add canonical `/codesleuth/playbooks` with compatibility alias `/playbooks`. It MUST enumerate the actual resolved overlay-over-pack playbook catalog using the existing catalog implementation. It must not maintain a second playbook ID table.

The catalog is deterministic and human/model readable. Each item exposes at least ID, one-line description/summary, origin (`overlay` or `pack`), and the exact invocation form `/codesleuth/playbook <id>`.

`/codesleuth/playbook <id>` remains execution. `/codesleuth/playbook` with no ID MUST show the same catalog and perform no playbook execution. Unknown IDs MUST fail closed and show deterministic available candidates rather than letting the model invent a near match.

Playbook IDs themselves remain semantic IDs such as `repository-map`; they are not lengthened to `codesleuth-playbooks-*` because invocation already carries the `/codesleuth/playbook` namespace.

## N3: portable skill namespace and distribution

Canonical portable Skill IDs use lowercase hyphenated `codesleuth-*` names. A bounded compatibility resolver may accept legacy IDs for one migration window, but discovery/catalog surfaces advertise only canonical IDs. Do not duplicate physical skills under both names as separate authorities.

One canonical CodeSleuth source produces generated host adapters. The portable center is Skills plus bounded MCP/tools; host-specific manifests are representations, not independent semantic sources.

Target channels, ordered by implementation priority:

1. Agent Skills / skills.sh-compatible package (`npx skills add ...`).
2. Agent Plugins-compatible bundle for Skills + MCP where supported.
3. Claude plugin marketplace wrapper.
4. OpenAI/Codex GitHub marketplace/plugin wrapper.
5. Cursor Agent Plugin wrapper.
6. Kimi plugin wrapper.
7. Hermes skill distribution.
8. OpenCode npm/native plugin distribution.
9. OpenClaw/ClawHub distribution.
10. NovaClaw adapter consuming the same canonical source; do not invent a NovaClaw marketplace contract before its host API provides one.

Skills-only installation MUST NOT claim that local durable stores, TUI, context-graph runtime, or full CodeSleuth lifecycle were installed. Plugin installation may add bounded tools/MCP. Full CodeSleuth project installation owns the managed AGENTS discovery, reports convention, durable state, context graphs, playbooks, tools, lifecycle and full host integration.

## Acceptance

N2 and N3 are separate serial packages. N2 starts from exact accepted `integration/rc7`. N3 starts only after N2 is integrated and that new integration SHA has fresh exact-head acceptance. Each package requires an honest test-only RED witness, focused GREEN, broad regression, hosted exact-head acceptance, coordinator review, serial integration, then fresh acceptance of the resulting integration SHA.
