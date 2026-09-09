from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "pack/.opencode/contracts/candidate-artifact-v1.schema.json"


def load_schema() -> dict[str, object]:
    assert SCHEMA.is_file(), "CandidateArtifactV1 schema must be installed with the CodeSleuth pack"
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


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
