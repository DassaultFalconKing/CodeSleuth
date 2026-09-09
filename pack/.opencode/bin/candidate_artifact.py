#!/usr/bin/env python3
"""Verify one CandidateArtifactV1 identity envelope without creating acceptance authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class CandidateError(RuntimeError):
    """Fail-closed candidate identity error with a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _object(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CandidateError("MALFORMED", f"{field} must be an object")
    return value


def _string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CandidateError("MALFORMED", f"{field} must be a non-empty string")
    return value


def _integer(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CandidateError("MALFORMED", f"{field} must be a non-negative integer")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(candidate_dir: Path) -> dict[str, object]:
    path = candidate_dir / "candidate.manifest.json"
    if not path.is_file():
        raise CandidateError("NOT_A_CANDIDATE", "candidate.manifest.json is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError("MALFORMED", f"candidate manifest is unreadable: {exc}") from exc
    return _object(payload, field="manifest")


def _verify_source(manifest: dict[str, object]) -> dict[str, object]:
    source = _object(manifest.get("source"), field="source")
    commit_sha = _string(source.get("commitSha"), field="source.commitSha")
    tree_sha = _string(source.get("treeSha"), field="source.treeSha")
    if not HEX40_RE.fullmatch(commit_sha) or not HEX40_RE.fullmatch(tree_sha):
        raise CandidateError(
            "SOURCE_IDENTITY_MISMATCH",
            "source commitSha and treeSha must each be exactly 40 lowercase hex characters",
        )
    if source.get("dirty") is not False:
        raise CandidateError(
            "DIRTY_SOURCE_UNSUPPORTED",
            "CandidateArtifactV1 requires source.dirty=false",
        )

    result: dict[str, object] = {
        "commitSha": commit_sha,
        "treeSha": tree_sha,
        "dirty": False,
    }
    branch = source.get("branch")
    if branch is not None:
        result["branch"] = _string(branch, field="source.branch")
    return result


def _verify_artifact(candidate_dir: Path, manifest: dict[str, object]) -> dict[str, object]:
    artifact = _object(manifest.get("artifact"), field="artifact")
    relative_path = _string(artifact.get("path"), field="artifact.path")
    expected_sha = _string(artifact.get("sha256"), field="artifact.sha256")
    if not HEX64_RE.fullmatch(expected_sha):
        raise CandidateError("MALFORMED", "artifact.sha256 must be exactly 64 lowercase hex characters")
    expected_size = _integer(artifact.get("sizeBytes"), field="artifact.sizeBytes")

    path = candidate_dir / relative_path
    if not path.is_file():
        raise CandidateError("MISSING", f"artifact is missing: {relative_path}")
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise CandidateError(
            "SIZE_MISMATCH",
            f"artifact size mismatch: expected={expected_size} actual={actual_size}",
        )
    actual_sha = _sha256_file(path)
    if actual_sha != expected_sha:
        raise CandidateError(
            "HASH_MISMATCH",
            f"artifact SHA-256 mismatch: expected={expected_sha} actual={actual_sha}",
        )
    return {
        "path": relative_path,
        "sha256": actual_sha,
        "sizeBytes": actual_size,
    }


def verify_candidate(candidate_dir: Path) -> dict[str, object]:
    """Verify the exact source/artifact identity for one CandidateArtifactV1 directory."""

    candidate_dir = Path(candidate_dir)
    manifest = _read_manifest(candidate_dir)
    if manifest.get("schemaVersion") != 1:
        raise CandidateError("MALFORMED", "schemaVersion must equal 1")

    tests = _object(manifest.get("tests"), field="tests")
    acceptance = _object(manifest.get("acceptance"), field="acceptance")

    return {
        "valid": True,
        "source": _verify_source(manifest),
        "artifact": _verify_artifact(candidate_dir, manifest),
        "tests": dict(tests),
        "acceptance": dict(acceptance),
    }
