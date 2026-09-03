from pathlib import Path
import pytest
from codesleuth_obsidian_adapter.profile import ProjectionProfile, unsafe_id

ROOT = Path(__file__).resolve().parents[1]


def test_codesleuth_profile_classifies_ids_and_relations():
    profile = ProjectionProfile.load(ROOT / "profiles" / "codesleuth.json")
    record = {
        "schemaId": "RepairCaseV1",
        "repairCaseId": "RC-008",
        "contractIds": ["CONTRACT-1"],
        "repairPacketId": "RP-008",
    }
    assert profile.classify(record) == "RepairCaseV1"
    assert profile.object_id("RepairCaseV1", record) == "RC-008"
    assert profile.folder("RepairCaseV1") == "repair-cases"
    assert profile.relations("RepairCaseV1", record) == [
        ("repairPacket", "RP-008"),
        ("violates", "CONTRACT-1"),
    ]


def test_unsafe_ids_fail_closed():
    for value in ["../escape", "a/b", "", ".", ".."]:
        with pytest.raises(ValueError):
            unsafe_id(value)
