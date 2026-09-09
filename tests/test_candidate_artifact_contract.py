from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "pack/.opencode/contracts/candidate-artifact-v1.schema.json"
MODULE = ROOT / "pack/.opencode/bin/candidate_artifact.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_schema() -> dict[str, object]:
    assert SCHEMA.is_file(), "CandidateArtifactV1 schema must be installed with the CodeSleuth pack"
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def load_candidate_module() -> ModuleType:
    assert MODULE.is_file(), "candidate_artifact verifier must be installed with the CodeSleuth pack"
    spec = importlib.util.spec_from_file_location("codesleuth_candidate_artifact_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_candidate(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / "ovms.exe"
    artifact.write_bytes(b"candidate-bytes")
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
        "tests": {"overall": "NOT_RUN"},
        "acceptance": {"claim": "NONE", "evidenceRefs": []},
    }
    write_manifest(tmp_path, manifest)
    return tmp_path


def read_manifest(candidate: Path) -> dict[str, object]:
    return json.loads((candidate / "candidate.manifest.json").read_text(encoding="utf-8"))


def write_manifest(candidate: Path, manifest: dict[str, object]) -> None:
    (candidate / "candidate.manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def point_artifact_at(candidate: Path, path_value: str, target: Path) -> None:
    manifest = read_manifest(candidate)
    manifest["artifact"] = {
        "path": path_value,
        "sha256": sha256(target),
        "sizeBytes": target.stat().st_size,
    }
    write_manifest(candidate, manifest)


def assert_error_code(module: ModuleType, expected: str, candidate: Path) -> None:
    with pytest.raises(module.CandidateError) as exc:
        module.verify_candidate(candidate)
    assert exc.value.code == expected


def test_candidate_artifact_v1_schema_is_closed_and_versioned() -> None:
    schema = load_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "codesleuth:candidate-artifact-v1"
    assert schema["title"] == "CandidateArtifactV1"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schemaVersion"] == {"const": 1}


def test_candidate_artifact_v1_exact_identity_patterns_are_not_interchangeable() -> None:
    schema = load_schema()
    source = schema["properties"]["source"]
    artifact = schema["properties"]["artifact"]

    assert source["additionalProperties"] is False
    assert source["properties"]["commitSha"] == {
        "type": "string",
        "pattern": "^[0-9a-f]{40}$",
    }
    assert source["properties"]["treeSha"] == {
        "type": "string",
        "pattern": "^[0-9a-f]{40}$",
    }
    assert source["properties"]["dirty"] == {"const": False}
    assert artifact["properties"]["sha256"] == {
        "type": "string",
        "pattern": "^[0-9a-f]{64}$",
    }


def test_candidate_artifact_v1_evidence_vocabularies_are_closed() -> None:
    schema = load_schema()
    tests = schema["properties"]["tests"]
    acceptance = schema["properties"]["acceptance"]

    assert tests["additionalProperties"] is False
    assert tests["properties"]["overall"]["enum"] == [
        "NOT_RUN",
        "PASS",
        "FAIL",
        "UNKNOWN",
        "BLOCKED",
    ]
    assert acceptance["additionalProperties"] is False
    assert acceptance["properties"]["claim"]["enum"] == [
        "NONE",
        "PENDING",
        "PASS_REFERENCED",
        "FAIL_REFERENCED",
        "UNKNOWN",
    ]
    assert "ACCEPTED" not in acceptance["properties"]["claim"]["enum"]


def test_verify_valid_candidate_returns_exact_identity(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path)
    module = load_candidate_module()

    result = module.verify_candidate(candidate)

    assert result["valid"] is True
    assert result["source"] == {
        "commitSha": "1" * 40,
        "treeSha": "2" * 40,
        "branch": "test/fixture",
        "dirty": False,
    }
    assert result["artifact"]["sha256"] == sha256(candidate / "ovms.exe")
    assert result["artifact"]["sizeBytes"] == (candidate / "ovms.exe").stat().st_size
    assert result["tests"] == {"overall": "NOT_RUN"}
    assert result["acceptance"] == {"claim": "NONE", "evidenceRefs": []}


def test_missing_manifest_is_not_a_candidate(tmp_path: Path) -> None:
    module = load_candidate_module()
    assert_error_code(module, "NOT_A_CANDIDATE", tmp_path)


def test_malformed_manifest_is_not_silently_treated_as_missing(tmp_path: Path) -> None:
    (tmp_path / "candidate.manifest.json").write_text("{not-json\n", encoding="utf-8")
    module = load_candidate_module()
    assert_error_code(module, "MALFORMED", tmp_path)


@pytest.mark.parametrize("field", ["commitSha", "treeSha"])
def test_malformed_source_identity_fails_closed(tmp_path: Path, field: str) -> None:
    candidate = write_candidate(tmp_path)
    manifest = read_manifest(candidate)
    manifest["source"][field] = "f" * 39
    write_manifest(candidate, manifest)
    module = load_candidate_module()
    assert_error_code(module, "SOURCE_IDENTITY_MISMATCH", candidate)


def test_dirty_source_is_unsupported_in_v1(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path)
    manifest = read_manifest(candidate)
    manifest["source"]["dirty"] = True
    write_manifest(candidate, manifest)
    module = load_candidate_module()
    assert_error_code(module, "DIRTY_SOURCE_UNSUPPORTED", candidate)


def test_missing_artifact_is_missing_evidence_not_test_failure(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path)
    (candidate / "ovms.exe").unlink()
    module = load_candidate_module()
    assert_error_code(module, "MISSING", candidate)


def test_artifact_size_mismatch_fails_closed(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path)
    manifest = read_manifest(candidate)
    manifest["artifact"]["sizeBytes"] += 1
    write_manifest(candidate, manifest)
    module = load_candidate_module()
    assert_error_code(module, "SIZE_MISMATCH", candidate)


def test_artifact_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path)
    (candidate / "ovms.exe").write_bytes(b"changed-candidate-bytes")
    module = load_candidate_module()
    assert_error_code(module, "SIZE_MISMATCH", candidate)

    manifest = read_manifest(candidate)
    manifest["artifact"]["sizeBytes"] = (candidate / "ovms.exe").stat().st_size
    write_manifest(candidate, manifest)
    assert_error_code(module, "HASH_MISMATCH", candidate)


def test_parent_traversal_artifact_path_fails_closed(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path / "candidate")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside-bytes")
    point_artifact_at(candidate, "../outside.bin", outside)
    module = load_candidate_module()
    assert_error_code(module, "PATH_ESCAPE", candidate)


def test_absolute_artifact_path_fails_closed(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path / "candidate")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside-bytes")
    point_artifact_at(candidate, str(outside.resolve()), outside)
    module = load_candidate_module()
    assert_error_code(module, "PATH_ESCAPE", candidate)


def test_symlink_artifact_escape_fails_closed(tmp_path: Path) -> None:
    candidate = write_candidate(tmp_path / "candidate")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside-bytes")
    link = candidate / "escape.bin"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this platform")
    point_artifact_at(candidate, "escape.bin", outside)
    module = load_candidate_module()
    assert_error_code(module, "PATH_ESCAPE", candidate)
