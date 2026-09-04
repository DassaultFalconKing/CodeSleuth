from pathlib import Path
from codesleuth_obsidian_adapter.profile import ProjectionProfile
from codesleuth_obsidian_adapter.render import normalize_records, render_note

ROOT = Path(__file__).resolve().parents[1]


def test_note_is_non_authoritative_deterministic_and_linked():
    profile = ProjectionProfile.load(ROOT / "profiles" / "codesleuth.json")
    record = {
        "schemaId": "RepairCaseV1",
        "repairCaseId": "RC-008",
        "result": "FAIL",
        "subjectSha": "a" * 40,
        "profileDigest": "digest-1",
        "assumptions": ["A: B"],
        "limitations": ["none"],
        "contractIds": ["CONTRACT-1"],
    }
    obj = normalize_records([record], profile)[0]
    a = render_note(obj)
    b = render_note(obj)
    assert a == b
    assert "projectionAuthority: none" in a
    assert 'objectId: "RC-008"' in a
    assert 'schemaId: "RepairCaseV1"' in a
    assert "sourceDigest:" in a
    assert "[[CONTRACT-1]]" in a
    assert "violates" in a
    assert "A: B" in a
