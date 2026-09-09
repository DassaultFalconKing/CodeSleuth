# Candidate Artifact Discipline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portable, fail-closed candidate-artifact identity verifier and handoff discipline that binds exact source commit/tree identity to exact artifact bytes and retained test/runtime evidence without creating a second build, runtime, persistence, promotion, or acceptance authority.

**Architecture:** Implement the first slice inside the installed CodeSleuth pack: one machine-readable `CandidateArtifactV1` schema, one bounded Python verifier under `pack/.opencode/bin/`, one atomic Skill that teaches agents how to use the verifier, and an additive `treeSha` extension to the existing exact-target identity Skill. Keep acceptance semantics upstream: the manifest can reference acceptance evidence but cannot manufacture an accepted state. All runtime/project-specific build and launch actions remain external and host-owned.

**Tech Stack:** Python 3.10+/3.12, stdlib (`argparse`, `hashlib`, `json`, `pathlib`), JSON Schema document as tracked contract, pytest, existing CodeSleuth Skill/publication tests, hosted exact-head acceptance.

**Spec:** `docs/superpowers/specs/2026-09-09-candidate-artifact-discipline-design.md`

## Global Constraints

- Design predecessor is `integration/rc7@3dbc2328ed091cbd793983edefc6e64a4c001343`; implementation remains on `feature/rc7-candidate-artifact-discipline` unless a coordinator explicitly refits it.
- No second controller, scheduler, build runtime, process supervisor, persistence authority, candidate ledger, promotion authority, or acceptance authority.
- `commitSha`, `treeSha`, SHA-256 digests, and evidence bindings are primary identities; branch/ref/path labels are presentation context only.
- `CandidateArtifactV1` v1 accepts only `source.dirty=false`; dirty builds are not candidates in v1.
- The manifest may reference acceptance evidence but must not assign semantic acceptance truth to itself.
- Candidate-relative paths must remain beneath the candidate directory after normalization and symlink/reparse resolution; absolute paths and `..` escapes fail closed.
- No new critical test may exist only as an ad-hoc command. Python contract tests must be reached by canonical `python -m pytest -q`.
- Existing exact-target/default caller behavior remains compatible; `treeSha` is additive.
- Missing, malformed, hash-mismatched, identity-mismatched, and untrusted evidence are separate machine-visible states.
- First slice does not mutate integration/release/freeze refs and does not implement an external artifact locator contract.

---

## File Structure

- `pack/.opencode/contracts/candidate-artifact-v1.schema.json` — sole machine-readable V1 manifest shape and vocabulary.
- `pack/.opencode/bin/candidate_artifact.py` — installed bounded verifier/inspector; no build or launch execution.
- `pack/.opencode/skills/candidate-artifact-discipline/SKILL.md` — atomic agent contract for candidate verification and evidence wording.
- `pack/.opencode/skills/exact-target-identity/SKILL.md` — additive `treeSha` output contract.
- `tests/test_candidate_artifact_contract.py` — RED/GREEN contract coverage for schema semantics, path containment, digests, runtime/test evidence consistency, and CLI output.
- `tests/test_skill_publication.py` — ensures the new Skill is bundled/published by the existing pack lifecycle.
- `tests/test_playbook_skill_contract.py` — protects Skill ID/metadata conventions if current publication contract requires it.
- `docs/CANDIDATE-ARTIFACT-DISCIPLINE.md` — operator-facing normative summary derived from the accepted design after runtime behavior is green.

---

### Task 1: Freeze the machine contract in RED tests

**Files:**
- Create: `tests/test_candidate_artifact_contract.py`
- Create: `pack/.opencode/contracts/candidate-artifact-v1.schema.json`

**Interfaces:**
- Consumes: candidate directory containing `candidate.manifest.json` plus referenced files.
- Produces contract vocabulary consumed by Task 2:
  - manifest `schemaVersion == 1`
  - `source.commitSha: str[40 hex]`
  - `source.treeSha: str[40 hex]`
  - `source.dirty: false`
  - `artifact.path: relative path`
  - `artifact.sha256: str[64 hex]`
  - `artifact.sizeBytes: int >= 0`
  - `tests.overall: NOT_RUN | PASS | FAIL | UNKNOWN | BLOCKED`
  - `acceptance.claim: NONE | PENDING | PASS_REFERENCED | FAIL_REFERENCED | UNKNOWN`
  - `acceptance.evidenceRefs: list[relative path]`

- [ ] **Step 1: Write the failing schema/fixture tests**

Create helper fixtures directly in `tests/test_candidate_artifact_contract.py`:

```python
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "pack/.opencode/contracts/candidate-artifact-v1.schema.json"
MODULE = ROOT / "pack/.opencode/bin/candidate_artifact.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_candidate(tmp_path: Path) -> Path:
    artifact = tmp_path / "ovms.exe"
    artifact.write_bytes(b"candidate-bytes")
    summary = tmp_path / "test-summary.json"
    summary.write_text('{"overall":"PASS"}\n', encoding="utf-8")
    manifest = {
        "schemaVersion": 1,
        "project": "fixture",
        "repository": "owner/repo",
        "source": {
            "commitSha": "1" * 40,
            "treeSha": "2" * 40,
            "branch": "test/fixture",
            "dirty": False,
        },
        "build": {
            "profile": "fixture",
            "command": "fixture-build",
            "toolchain": {"name": "fixture", "version": "1"},
        },
        "artifact": {
            "path": "ovms.exe",
            "sha256": sha256(artifact),
            "sizeBytes": artifact.stat().st_size,
        },
        "tests": {
            "summary": "test-summary.json",
            "summarySha256": sha256(summary),
            "overall": "PASS",
        },
        "acceptance": {"claim": "NONE", "evidenceRefs": []},
    }
    (tmp_path / "candidate.manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return tmp_path
```

Add assertions that the schema file exists and declares `schemaVersion` const `1`, `source.dirty` const `false`, closed acceptance/test vocabularies, 40-hex commit/tree patterns, 64-hex SHA-256 patterns, and `additionalProperties: false` at the top-level and major nested objects.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py
```

Expected: FAIL because the schema and verifier do not yet exist.

- [ ] **Step 3: Write the minimal JSON Schema**

Create `pack/.opencode/contracts/candidate-artifact-v1.schema.json` as draft-2020-12-compatible JSON with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "codesleuth:candidate-artifact-v1",
  "title": "CandidateArtifactV1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schemaVersion", "project", "repository", "source", "build", "artifact", "tests", "acceptance"],
  "properties": {
    "schemaVersion": {"const": 1},
    "project": {"type": "string", "minLength": 1},
    "repository": {"type": "string", "minLength": 1},
    "source": {
      "type": "object",
      "additionalProperties": false,
      "required": ["commitSha", "treeSha", "dirty"],
      "properties": {
        "commitSha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "treeSha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "branch": {"type": "string", "minLength": 1},
        "dirty": {"const": false}
      }
    },
    "build": {
      "type": "object",
      "additionalProperties": false,
      "required": ["profile", "command", "toolchain"],
      "properties": {
        "profile": {"type": "string", "minLength": 1},
        "command": {"type": "string", "minLength": 1},
        "toolchain": {
          "type": "object",
          "additionalProperties": false,
          "required": ["name", "version"],
          "properties": {
            "name": {"type": "string", "minLength": 1},
            "version": {"type": "string", "minLength": 1}
          }
        }
      }
    },
    "artifact": {
      "type": "object",
      "additionalProperties": false,
      "required": ["path", "sha256", "sizeBytes"],
      "properties": {
        "path": {"type": "string", "minLength": 1},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "sizeBytes": {"type": "integer", "minimum": 0}
      }
    },
    "tests": {
      "type": "object",
      "additionalProperties": false,
      "required": ["overall"],
      "properties": {
        "summary": {"type": "string", "minLength": 1},
        "summarySha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "overall": {"enum": ["NOT_RUN", "PASS", "FAIL", "UNKNOWN", "BLOCKED"]}
      }
    },
    "runtime": {
      "type": "object",
      "additionalProperties": false,
      "required": ["evidence", "evidenceSha256"],
      "properties": {
        "launchProfile": {"type": "string", "minLength": 1},
        "modelIdentity": {"type": "string", "minLength": 1},
        "evidence": {"type": "string", "minLength": 1},
        "evidenceSha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
      }
    },
    "acceptance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["claim", "evidenceRefs"],
      "properties": {
        "claim": {"enum": ["NONE", "PENDING", "PASS_REFERENCED", "FAIL_REFERENCED", "UNKNOWN"]},
        "evidenceRefs": {
          "type": "array",
          "items": {"type": "string", "minLength": 1},
          "uniqueItems": true
        }
      }
    }
  }
}
```

Do not introduce a runtime dependency on the `jsonschema` package merely to read this contract; Task 2 implements the bounded V1 checks directly in stdlib and tests schema/runtime parity.

- [ ] **Step 4: Run schema-focused tests**

Run:

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k schema
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/test_candidate_artifact_contract.py pack/.opencode/contracts/candidate-artifact-v1.schema.json
git commit -m "test(rc7): freeze candidate artifact v1 contract"
```

---

### Task 2: Implement fail-closed candidate verification

**Files:**
- Create: `pack/.opencode/bin/candidate_artifact.py`
- Modify: `tests/test_candidate_artifact_contract.py`

**Interfaces:**
- Consumes: `Path` to candidate directory containing `candidate.manifest.json`.
- Produces:

```python
class CandidateError(RuntimeError):
    code: str


def verify_candidate(candidate_dir: Path) -> dict[str, object]: ...

def inspect_candidate(candidate_dir: Path) -> dict[str, object]: ...
```

CLI:

```text
python candidate_artifact.py verify <candidate-dir>
python candidate_artifact.py inspect <candidate-dir>
```

Success JSON contains `valid: true`, exact source/artifact identity, tests state, acceptance claim, and verified evidence paths. Failure emits deterministic JSON to stderr and exits `2`.

- [ ] **Step 1: Add RED tests for valid verification and exact artifact bytes**

Add:

```python
def test_verify_valid_candidate(tmp_path):
    candidate = write_candidate(tmp_path)
    mod = load_candidate_module()
    result = mod.verify_candidate(candidate)
    assert result["valid"] is True
    assert result["source"]["commitSha"] == "1" * 40
    assert result["source"]["treeSha"] == "2" * 40
    assert result["artifact"]["sha256"] == sha256(candidate / "ovms.exe")


def test_artifact_hash_mismatch_fails_closed(tmp_path):
    candidate = write_candidate(tmp_path)
    (candidate / "ovms.exe").write_bytes(b"changed")
    mod = load_candidate_module()
    with pytest.raises(mod.CandidateError) as exc:
        mod.verify_candidate(candidate)
    assert exc.value.code == "HASH_MISMATCH"
```

Use an explicit `importlib.util.spec_from_file_location` helper so tests exercise the installed-pack file without modifying `sys.path` globally.

- [ ] **Step 2: Run focused tests and verify RED**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "verify_valid_candidate or artifact_hash_mismatch"
```

Expected: FAIL because `candidate_artifact.py` is absent.

- [ ] **Step 3: Implement deterministic parsing and core hash checks**

Implement stdlib-only helpers:

```python
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
TEST_STATES = {"NOT_RUN", "PASS", "FAIL", "UNKNOWN", "BLOCKED"}
ACCEPTANCE_CLAIMS = {"NONE", "PENDING", "PASS_REFERENCED", "FAIL_REFERENCED", "UNKNOWN"}

class CandidateError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
```

`verify_candidate()` must reject absent manifest as `NOT_A_CANDIDATE`, JSON parse/type errors as `MALFORMED`, malformed identities as `SOURCE_IDENTITY_MISMATCH`, `source.dirty is not False` as `DIRTY_SOURCE_UNSUPPORTED`, missing artifact as `MISSING`, wrong size as `SIZE_MISMATCH`, and wrong digest as `HASH_MISMATCH`.

- [ ] **Step 4: Run core verifier tests**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "valid_candidate or artifact_hash or bad_commit or bad_tree or dirty"
```

Expected: PASS.

- [ ] **Step 5: Commit core verifier**

```bash
git add pack/.opencode/bin/candidate_artifact.py tests/test_candidate_artifact_contract.py
git commit -m "feat(rc7): verify exact candidate artifact identity"
```

---

### Task 3: Enforce candidate-directory path containment

**Files:**
- Modify: `pack/.opencode/bin/candidate_artifact.py`
- Modify: `tests/test_candidate_artifact_contract.py`

**Interfaces:**
- Adds internal helper:

```python
def resolve_candidate_path(candidate_dir: Path, value: str, *, field: str) -> Path: ...
```

- [ ] **Step 1: Add RED path-escape tests**

Add cases for:

```python
@pytest.mark.parametrize("bad", ["../outside.bin", "/tmp/outside.bin"])
def test_artifact_path_cannot_escape_candidate_dir(tmp_path, bad): ...
```

and a symlink test on platforms where symlinks can be created:

```python
def test_symlink_escape_fails_closed(tmp_path):
    candidate = write_candidate(tmp_path / "candidate")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    link = candidate / "escape.bin"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable on this platform")
    # set artifact path/hash to escape.bin and assert PATH_ESCAPE
```

The symlink case may skip on Windows without privileges, but lexical `..` and absolute-path escape tests must never skip on any canonical Python job.

- [ ] **Step 2: Run escape tests and verify RED**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "escape_candidate_dir or symlink_escape"
```

Expected: FAIL until containment is implemented.

- [ ] **Step 3: Implement containment**

Use `Path.resolve(strict=False)` on the candidate root and referenced path, reject absolute input before joining, then require `resolved.is_relative_to(root)` on supported Python versions. Do not trust string prefix comparison.

```python
def resolve_candidate_path(candidate_dir: Path, value: str, *, field: str) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raise CandidateError("PATH_ESCAPE", f"{field} must be candidate-relative")
    root = candidate_dir.resolve()
    resolved = (root / raw).resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise CandidateError("PATH_ESCAPE", f"{field} escapes candidate directory")
    return resolved
```

- [ ] **Step 4: Run path tests**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "escape or path"
```

Expected: PASS, with only the platform-permitted symlink witness potentially skipped.

- [ ] **Step 5: Commit containment**

```bash
git add pack/.opencode/bin/candidate_artifact.py tests/test_candidate_artifact_contract.py
git commit -m "fix(rc7): contain candidate evidence paths"
```

---

### Task 4: Bind test, runtime, and acceptance references without inventing acceptance

**Files:**
- Modify: `pack/.opencode/bin/candidate_artifact.py`
- Modify: `tests/test_candidate_artifact_contract.py`

**Interfaces:**
- `verify_candidate()` result includes:

```python
{
  "tests": {"overall": str, "summarySha256": str | None},
  "runtime": {"evidenceSha256": str, "artifactSha256": str} | None,
  "acceptance": {"claim": str, "evidenceRefs": list[str]},
}
```

Runtime evidence V1 must be JSON containing at minimum `artifactSha256`, `sourceCommitSha`, and `sourceTreeSha` matching the manifest.

- [ ] **Step 1: Add RED test-summary consistency tests**

Add cases:

```python
def test_pass_requires_summary_and_digest(tmp_path): ...
def test_missing_summary_is_not_test_failure(tmp_path): ...
def test_wrong_summary_digest_is_hash_mismatch(tmp_path): ...
```

Required behavior:
- `tests.overall == PASS` or `FAIL` requires both `summary` and `summarySha256`.
- absent referenced summary => `MISSING`, not `FAIL`.
- unreadable/malformed JSON summary is not required to be semantically parsed in V1; digest identity is sufficient.

- [ ] **Step 2: Add RED runtime-binding tests**

Create `runtime/launch.json` with:

```json
{
  "artifactSha256": "<manifest artifact sha>",
  "sourceCommitSha": "1111...",
  "sourceTreeSha": "2222..."
}
```

Assert mismatched artifact/source fields fail with `RUNTIME_IDENTITY_MISMATCH` and matching evidence passes after its own `evidenceSha256` is verified.

- [ ] **Step 3: Add RED acceptance-reference tests**

Assert:

```python
def test_pass_referenced_requires_evidence_refs(tmp_path): ...
def test_acceptance_refs_are_verified_as_files_not_truth(tmp_path): ...
```

`PASS_REFERENCED` and `FAIL_REFERENCED` require at least one contained existing evidence file. The verifier verifies containment/presence and reports the references, but must not emit `accepted: true` or convert the claim into CodeSleuth EHA/SIB acceptance.

- [ ] **Step 4: Run new tests and verify RED**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "summary or runtime or acceptance"
```

Expected: FAIL before evidence binding is implemented.

- [ ] **Step 5: Implement minimal evidence binding**

Add `verify_digest_file()`, `verify_tests()`, `verify_runtime()`, and `verify_acceptance_refs()` helpers. Reuse `resolve_candidate_path()` for every manifest-provided path. Do not implement GitHub/EHA semantic parsing here.

- [ ] **Step 6: Run evidence-binding tests**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k "summary or runtime or acceptance"
```

Expected: PASS.

- [ ] **Step 7: Commit evidence binding**

```bash
git add pack/.opencode/bin/candidate_artifact.py tests/test_candidate_artifact_contract.py
git commit -m "feat(rc7): bind candidate runtime and test evidence"
```

---

### Task 5: Add stable CLI and handoff output

**Files:**
- Modify: `pack/.opencode/bin/candidate_artifact.py`
- Modify: `tests/test_candidate_artifact_contract.py`

**Interfaces:**
- CLI success:

```text
python candidate_artifact.py verify <candidate-dir>
```

stdout: one JSON document with `valid: true`.

- CLI inspect returns the same bounded identity plus `handoff` keys:

```text
BRANCH
HEAD_SHA
TREE_SHA
BUILD
BINARY_SHA256
TESTS
TEST_SUMMARY_SHA256
RUNTIME
RUNTIME_ARTIFACT_SHA256
ACCEPTANCE
```

- CLI failure exits `2` and emits JSON:

```json
{"valid":false,"error":{"code":"HASH_MISMATCH","message":"..."}}
```

- [ ] **Step 1: Add RED subprocess CLI tests**

Use `subprocess.run([sys.executable, str(MODULE), "verify", str(candidate)], ...)` and assert stdout/stderr/exit codes. Never invoke ambient `python` from runtime code.

- [ ] **Step 2: Run CLI tests and verify RED**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k cli
```

Expected: FAIL until argparse/main rendering exists.

- [ ] **Step 3: Implement CLI**

Use `argparse` with `verify` and `inspect` subcommands. Serialize with `json.dumps(..., sort_keys=True, separators=(",", ":"))` for deterministic output. Do not execute project build/test/runtime commands.

- [ ] **Step 4: Run CLI tests**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py -k cli
```

Expected: PASS.

- [ ] **Step 5: Commit CLI**

```bash
git add pack/.opencode/bin/candidate_artifact.py tests/test_candidate_artifact_contract.py
git commit -m "feat(rc7): expose bounded candidate artifact inspection"
```

---

### Task 6: Publish the atomic Skill and extend exact-target identity additively

**Files:**
- Create: `pack/.opencode/skills/candidate-artifact-discipline/SKILL.md`
- Modify: `pack/.opencode/skills/exact-target-identity/SKILL.md`
- Modify: `tests/test_skill_publication.py`
- Modify if required by current contract: `tests/test_playbook_skill_contract.py`

**Interfaces:**
- New Skill metadata:

```yaml
---
name: candidate-artifact-discipline
description: Verify exact source, artifact, runtime, and retained evidence identity for one built candidate without creating acceptance authority
slash: true
---
```

Atomic contract:
- Input: candidate directory or manifest plus requested claim.
- Objective: verify exact source commit/tree, artifact hash, and referenced evidence consistency.
- Output: bounded verifier JSON plus evidence-state vocabulary.
- Stop: identity/evidence mismatch, unsupported dirty source, path escape, or acceptance claim without evidence refs.
- Must not: build, launch, kill processes, move refs, rewrite evidence, or pronounce acceptance beyond upstream evidence.

- [ ] **Step 1: Add RED publication test**

Extend the existing publication test to require `candidate-artifact-discipline` among bundled Skills and verify the directory name equals frontmatter `name`.

- [ ] **Step 2: Run publication tests and verify RED**

```bash
python -m pytest -q tests/test_skill_publication.py tests/test_playbook_skill_contract.py
```

Expected: FAIL because the new Skill does not exist yet.

- [ ] **Step 3: Create the new Skill**

Document the exact CLI invocation using the installed pack path/host context and the allowed state vocabulary `PASS | FAIL | NOT_RUN | UNKNOWN | BLOCKED` for handoffs. Explicitly state that `PASS_REFERENCED` is a reference claim, not semantic acceptance.

- [ ] **Step 4: Extend exact-target identity**

Add `treeSha` to the output paragraph and recommend `git rev-parse HEAD^{tree}` alongside existing `git rev-parse`. Preserve all existing Stop/Must-not language and default semantics.

- [ ] **Step 5: Run publication/contract tests**

```bash
python -m pytest -q tests/test_skill_publication.py tests/test_playbook_skill_contract.py
```

Expected: PASS.

- [ ] **Step 6: Commit Skill publication**

```bash
git add pack/.opencode/skills/candidate-artifact-discipline/SKILL.md pack/.opencode/skills/exact-target-identity/SKILL.md tests/test_skill_publication.py tests/test_playbook_skill_contract.py
git commit -m "feat(rc7): publish candidate artifact discipline skill"
```

---

### Task 7: Document installed operator contract and lifecycle reachability

**Files:**
- Create: `docs/CANDIDATE-ARTIFACT-DISCIPLINE.md`
- Modify: `tests/test_docs_contract.py`
- Modify if current lifecycle test requires explicit pack witness: `tests/test_project_lifecycle.py`

**Interfaces:**
- Documentation points to the installed pack paths and repeats only normative public rules already implemented/tested.

- [ ] **Step 1: Add RED docs/lifecycle assertions**

Require the docs to state:

```text
No manifest, no candidate.
No exact artifact hash, no runtime claim.
The manifest is not acceptance authority.
Dirty source is unsupported by CandidateArtifactV1.
```

Require a lifecycle witness that a disposable/installed pack includes:

```text
.opencode/bin/candidate_artifact.py
.opencode/contracts/candidate-artifact-v1.schema.json
.opencode/skills/candidate-artifact-discipline/SKILL.md
```

Use the existing recursive pack-install mechanism; do not add a new installer code path unless the test proves the current one fails.

- [ ] **Step 2: Run docs/lifecycle tests and verify RED**

```bash
python -m pytest -q tests/test_docs_contract.py tests/test_project_lifecycle.py
```

Expected: FAIL on missing docs/new installed-file witness.

- [ ] **Step 3: Write concise operator documentation**

Document CandidateArtifactV1 purpose and trust boundary, manifest convention, `verify`/`inspect`, exact source/artifact identities, evidence binding, acceptance-reference non-authority, failure vocabulary, and first-slice exclusions.

- [ ] **Step 4: Run docs/lifecycle tests**

```bash
python -m pytest -q tests/test_docs_contract.py tests/test_project_lifecycle.py
```

Expected: PASS without installer production-code changes if recursive pack ownership works as intended.

- [ ] **Step 5: Commit docs/lifecycle closure**

```bash
git add docs/CANDIDATE-ARTIFACT-DISCIPLINE.md tests/test_docs_contract.py tests/test_project_lifecycle.py
git commit -m "docs(rc7): document candidate artifact discipline"
```

---

### Task 8: Protected-capability closure and canonical acceptance

**Files:**
- Modify only if evidence shows necessary: `docs/protected-capabilities.json`
- Modify only if existing registry contract requires evidence wiring: `tests/test_protected_capability_registry.py`
- No implementation files should change during this task except to fix a discovered regression with a new RED witness first.

**Interfaces:**
- Candidate feature is classified as hardening under existing acceptance/pack/lifecycle boundaries; no new SIB0 capability class.

- [ ] **Step 1: Run mandatory strict scanner on feature head**

```bash
python scripts/contributor_antipatterns.py scan --strict
```

Expected: exit `0`. Existing heuristic WARNs must be reviewed; no new ERROR may be introduced.

- [ ] **Step 2: Run focused feature closure**

```bash
python -m pytest -q tests/test_candidate_artifact_contract.py tests/test_skill_publication.py tests/test_playbook_skill_contract.py tests/test_docs_contract.py tests/test_project_lifecycle.py
```

Expected: PASS.

- [ ] **Step 3: Run full Python and lint gates**

```bash
python -m ruff check .
python -m pytest -q
```

Expected: both PASS. Report skips exactly; do not convert skipped optional profiles into feature PASS evidence.

- [ ] **Step 4: Inspect protected-capability impact**

Read `docs/protected-capabilities.json` entries for acceptance infrastructure, host integration pack, CLI/lifecycle, and persistent state. If the new files fit existing `affected_paths`/proof closure, do not churn registry metadata. If a protected contract needs a new explicit proof path, add only that bounded evidence pointer plus a corresponding registry test.

- [ ] **Step 5: Commit any bounded registry evidence update**

If no registry update is needed, record `NO_CHANGE` in the handoff and do not create an empty commit. If required:

```bash
git add docs/protected-capabilities.json tests/test_protected_capability_registry.py
git commit -m "test(rc7): bind candidate artifact protected evidence"
```

- [ ] **Step 6: Push exact feature head and obtain hosted acceptance**

Observe the normal CodeSleuth acceptance workflow for the literal resulting SHA. Required claims:

```text
FEATURE_HEAD_SHA: <40-hex>
CONTRIBUTOR_GATE: PASS for exact head
RUFF: PASS for exact head
PYTEST: PASS for exact head
HOSTED_ACCEPTANCE: PASS for exact head
```

Do not merge the branch into `integration/rc7`, `main`, `SIB`, `dev/release-0.4.0`, tags, or releases in this implementation session.

- [ ] **Step 7: Return canonical handoff**

Return exactly evidenced values:

```text
BRANCH:
BASE_SHA:
HEAD_SHA:
TREE_SHA:
COMMITS:
FILES_CHANGED:
BUILD: NOT_APPLICABLE (CodeSleuth Python/contract feature)
TESTS:
KNOWN_FAILURES:
ARTIFACTS:
BUNDLE_SHA256: NOT_APPLICABLE unless a bundle was actually produced
ACCEPTANCE:
PROMOTION_RECOMMENDATION:
```

Any command not executed is `NOT_RUN`; any evidence that cannot be resolved is `UNKNOWN`.
