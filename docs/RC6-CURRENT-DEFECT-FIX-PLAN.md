# RC6 Current Defect Fix Plan

Status: planning authority for the current RC6 feature branch until superseded by an accepted RC6 feature plan.

Target branch: `feature/rc6-eha-brownfield-bootstrap`

Planning baseline: `94c77236e4a5f5100ae4785d246118a6925bcaf7`

RC5d base: `4370c0d63173d27556b11d629746afee07f3cf62`

Latest hosted acceptance observed at this baseline: run `33534916789`.

## Goal

Bring the RC6 implementation to the boundary where every defect that can be tested deterministically in the repository or on GitHub-hosted runners is closed. Only after that boundary may live OpenCode/provider/runtime behavior be handed to Work, Cursor or OpenCode for host-specific debugging.

Do not use live-host debugging to compensate for repository-testable defects.

## Current evidence

At `94c77236e4a5f5100ae4785d246118a6925bcaf7`:

- Durable state/context graph: PASS.
- Graphify enabled runtime: PASS.
- TUI visual regression: PASS.
- Python lint: PASS on tested Linux and Windows jobs.
- Python test matrix: FAIL with three repository-contract failures repeated across the Python jobs.
- The earlier `contract_bootstrap_state.start` parent-directory ENOENT is fixed; the durable Bun smoke now passes.

The remaining known defects are therefore contract/integration defects, not an unexplained runtime failure.

## D1 — EHA workflow entry-point contract drift

### Symptom

`tests/test_eha_github_bridge.py::test_workflow_is_a_delegating_owner_gated_self_hosted_bridge` still requires `scripts/eha_github_bridge.py`, while `.github/workflows/eha.yml` now invokes `scripts/eha_github_bridge_rc6.py`.

### Root cause

RC6 introduced a wrapper entry point instead of evolving the canonical bridge entry point, leaving two apparent authorities:

- `eha_github_bridge.py` — established bridge implementation and tests;
- `eha_github_bridge_rc6.py` — new production workflow entry point.

This is architectural debt, not merely a stale assertion. A release workflow should have one canonical bridge entry point.

### Fix

1. Refactor pre-provider bootstrap into a reusable helper/module.
2. Integrate that helper into the canonical `scripts/eha_github_bridge.py` execution path.
3. Remove the RC6-only wrapper once parity tests prove the canonical script owns both prestart and completion handshake.
4. Keep workflow assertions pointed at one canonical script.
5. Add a regression test that the canonical bridge writes `campaign_started` before invoking the provider.

### Exit gate

- workflow invokes only `scripts/eha_github_bridge.py`;
- no RC6-only production bridge remains;
- legacy bridge tests and prestart tests agree on the same entry point.

## D2 — Prestarted-campaign prompt contract is tested by prose

### Symptom

`tests/test_eha_campaign_bootstrap.py::test_workflow_and_rc6_prompt_use_prestarted_campaign` expects the literal phrase `created the review checkpoint` inside the RC6 wrapper source.

### Root cause

The test binds behavior to incidental prose rather than to an executable contract.

### Fix

Replace prose matching with behavioral assertions:

1. deterministic bootstrap is called before provider invocation;
2. returned `reviewId` and `campaignId` are injected into the provider request/environment as immutable identifiers;
3. the provider path is explicitly told to load the prestarted campaign and must not create another campaign;
4. a test double proves `invoke_opencode` cannot execute before bootstrap succeeds;
5. a second-start attempt for the same bridge run fails closed.

### Exit gate

No production behavior depends on a magic English sentence. The test proves ordering and identity.

## D3 — Provenance binding is no longer guaranteed before EHA evidence

### Symptom

`tests/test_provenance_watermark_contract.py::test_reports_and_eha_require_verified_provenance_without_promoting_it_to_authority` fails because `pack/.opencode/commands/eha-test.md` no longer contains `provenance_state_bind`.

### Root cause

RC6 moved review/campaign creation into the trusted pre-provider controller but did not move provenance binding into the same deterministic authority boundary. Removing the model-owned bind without replacing it creates an attribution gap.

### Fix

1. Keep provenance metadata non-authoritative for SIB claimability.
2. Move the EHA producer binding into deterministic pre-provider bootstrap.
3. Reuse the canonical provenance implementation or extract a shared helper; do not create a second watermark algorithm in the bridge.
4. Bind one stable opaque producer identity to the new review before `campaign_started` is written.
5. Pass the verified provenance identity to OpenCode as existing state to load, not as a request to invent/rebind it.
6. Preserve exact-head verification after binding.

### Exit gate

- every trusted-bridge EHA campaign has a verified provenance binding before its first EHA event;
- provider failure before first response still leaves an attributable prestarted campaign;
- provenance remains metadata and cannot upgrade PASS/claimability.

## D4 — Brownfield exact-head discovery is not yet dirty-worktree safe

### Symptom

`contract_bootstrap_state` verifies `git rev-parse HEAD`, but a tracked file may be modified without changing HEAD. Discovery can therefore record evidence from content that is not represented by the claimed target SHA.

### Fix

Use both worktree cleanliness and blob-bound evidence:

1. `start` refuses tracked dirty state.
2. `record_candidate`, `record_decision`, `load` and pre-materialization checks verify the tracked worktree is still clean.
3. Candidate evidence records store `{path, blobHash}` for code/doc/test evidence.
4. Before decision and materialization, every recorded blob hash is revalidated.
5. `.opencode/state/**` remains ignored/durable state and does not count as candidate dirtiness.
6. `materialize` verifies the old exact target first, writes the registry, and explicitly returns that the worktree now represents a new uncommitted candidate identity.

### Exit gate

No candidate can be adopted from tracked bytes that differ from its claimed SHA.

## D5 — Brownfield registry materialization needs a generic target schema boundary

### Symptom

The current materializer can create `docs/protected-capabilities.json` in a repository that has no registry, but CodeSleuth's own registry has stronger self-host-specific fields and tests. A generic repository must not inherit CodeSleuth-specific SIB inventory assumptions by accident.

### Fix

Define two compatible layers:

1. generic Protected Capability Registry core:
   - schema identity/version;
   - target-local authority reference;
   - lifecycle status vocabulary;
   - contracts, dependencies and forbidden regressions;
   - bootstrap provenance;
2. optional CodeSleuth self-host profile:
   - frozen SIB0 capability-class inventory;
   - CodeSleuth-specific authority files;
   - self-host-only invariants.

The brownfield materializer may create only the generic core in foreign repositories. It must never copy CodeSleuth's own contract inventory or historical SIB evidence.

### Exit gate

A synthetic foreign repository with no prior registry can bootstrap a valid minimal registry, while CodeSleuth's stricter self-registry tests remain unchanged and green.

## D6 — Human adjudication continuation surface is incomplete

### Symptom

The Playbook correctly stops before human authority, but the user needs an explicit and resumable product path from `AWAITING_USER_ADJUDICATION` to durable decision and materialization.

### Fix

1. Keep analytical Steps `fresh_subagent`.
2. Playbook returns an adjudication packet and `bootstrapId`; it does not write decisions.
3. The primary controller accepts explicit named decisions only.
4. Add a resumable command/action surface that loads the bootstrap by ID and applies only the user's stated decisions.
5. Require a separate explicit materialize instruction after decisions when the user did not already include it.
6. Re-check exact target and evidence blob hashes before every mutation.

### Exit gate

A bootstrap can stop, survive session change, resume by ID, accept explicit user decisions and materialize without any subagent self-approval.

## D7 — New RC6 surfaces are not yet fully integrated into distribution contracts

### Required surfaces

- command: brownfield contract bootstrap/resume;
- Playbook: `repository-contract-bootstrap`;
- Skill: `contract-archaeology`;
- tool: `contract_bootstrap_state`;
- canonical EHA prestart helper/bridge behavior.

### Fix

Update and test:

- `pack/.opencode/opencode.json` permissions;
- Playbook catalog command aliases where appropriate;
- `smoke.py` and installed `review-pack-smoke.py` required surfaces;
- install/update managed-file inventory and lifecycle parity;
- docs discovery pointers;
- Playbook/Skill/Command/Tool contract tests;
- Windows path/shell parity for any new command path.

### Exit gate

A clean installed CodeSleuth instance exposes the same RC6 surfaces as a source checkout, and uninstall/update behavior remains reversible.

## D8 — EHA and brownfield documentation are behind the implementation

### Fix

Update normative docs only after D1-D7 stabilize:

- GitHub EHA bridge operating contract: prestart, completion handshake, transport vs authority, provenance binding;
- EHA operating playbook;
- Protected Capability Registry contract: generic core vs CodeSleuth self profile;
- brownfield bootstrap operator contract;
- docs index and LLM operator guide.

Do not document a temporary RC6 wrapper as canonical if D1 removes it.

## D9 — Hosted acceptance must become exact-head green before live-host handoff

### Required hosted sequence

1. focused Python tests for D1-D8;
2. full `pytest` Python 3.10/3.12 on Ubuntu and Windows;
3. Bun durable-state/context graph suite;
4. TUI visual regression;
5. Graphify enabled runtime;
6. contributor anti-pattern gate;
7. exact-head checkout assertions.

### Cloud-testability boundary

Live Work/Cursor/OpenCode debugging is permitted only when the final RC6 head is 7/7 green and the remaining open questions require an actual host/provider/runtime, for example:

- real OpenCode loads the trusted prestarted review/campaign/provenance state;
- provider transport can stall without losing durable campaign identity;
- a real foreign repository can be interactively adjudicated through the host controller;
- live external/runtime evidence adapters behave correctly against real services.

## Implementation order

1. D1 canonicalize bridge entry point.
2. D3 deterministic provenance prebind.
3. D2 replace prose-based prestart test with behavior.
4. D4 dirty/blob-bound brownfield evidence.
5. D5 generic foreign-registry schema.
6. D6 resumable human adjudication boundary.
7. D7 packaging/install parity.
8. D8 documentation.
9. D9 full exact-head hosted acceptance.

Every repair commit produces a new candidate SHA. Failed SHA evidence remains immutable.