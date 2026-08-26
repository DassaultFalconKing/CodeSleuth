# CodeSleuth agent instructions

CodeSleuth is a discipline layer and control panel around a host coding agent. The host owns the model, primary controller, session, permissions, tool routing, and execution. Do not introduce a second CodeSleuth runtime, supervisor, or general-purpose tool router.

## Read the right authority

- Product/manual truth: [`README.md`](README.md).
- Product ownership and extension boundaries: [`docs/CODESLEUTH-PRODUCT-CONTRACT.md`](docs/CODESLEUTH-PRODUCT-CONTRACT.md).
- Playbook/Step/Skill/Command/Tool composition: [`docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md`](docs/PLAYBOOK-SKILL-COMMAND-TOOL-CONTRACT.md).
- Protected capability and forbidden-regression semantics: [`docs/PROTECTED-CAPABILITY-CONTRACTS.md`](docs/PROTECTED-CAPABILITY-CONTRACTS.md).
- Machine-readable Protected Capability Registry: [`docs/protected-capabilities.json`](docs/protected-capabilities.json).
- Install/bind/unbind/uninstall truth: [`docs/PROJECT-LIFECYCLE.md`](docs/PROJECT-LIFECYCLE.md).
- Coding-agent operator workflow: [`docs/LLM-OPERATOR.md`](docs/LLM-OPERATOR.md).

If the user asks you to install, configure unattended, use, update, bind, unbind, remove, or prepare a release-clean repository with CodeSleuth, read `docs/LLM-OPERATOR.md` before changing the target repository.

For multi-step work, use a stored Playbook when one exists. Read only its manifest initially, materialize one Step at a time, and load only the atomic Skills declared for that Step. Prefer fresh host-native child context for Step isolation; retain bounded Step outputs rather than the whole Step prompt. Do not turn a long workflow back into one giant Skill.

For one atomic competence, load the relevant Skill directly. A Skill must have independently decidable input/objective/output/stop/must-not boundaries. User-facing Skills may also be slash-invoked where the host supports it.

If the task adds or changes a feature after SIB2, reviews a PR for regression, prepares SIB/EHA/RC/release acceptance, or asks which accepted contracts a diff can affect, use the `protected-capability-assessment` Playbook for broad work. For one narrow registry lookup, use the atomic `protected-capability-registry` Skill.

## Source-development invariants

- Make the smallest change that satisfies the current contract.
- Preserve OpenCode `build` as the primary controller for the full OpenCode integration.
- Do not treat context graphs, Mermaid, scout summaries, retrieval scores, or prior reports as stronger evidence than exact current source.
- Preserve pre-existing OpenCode/user configuration and conflict-safe lifecycle behavior.
- Do not widen permissions, commit, push, reset, clean, or discard user work unless the user explicitly asks for that operation.
- Run the relevant executable checks and only report checks that actually ran successfully.
- Do not silently change a protected contract, remove one of its forbidden regressions, or promote a capability to `protected` without the required SIB1/SIB2 exact-head evidence.
- For ordinary feature candidates, prove the new feature plus the invariant core and affected protected-capability closure. For SIB2, accepted integration heads, RCs, and releases, run the full acceptance profile required by that claim.
- Commands are entry points, Playbooks own multi-step order, Skills own atomic reasoning, Tools own bounded execution primitives. Do not hide unique semantic contracts only inside a Command.

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
