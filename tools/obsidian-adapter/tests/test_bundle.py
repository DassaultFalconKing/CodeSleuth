from pathlib import Path
import json
from codesleuth_obsidian_adapter.profile import ProjectionProfile
from codesleuth_obsidian_adapter.render import render_projection

ROOT = Path(__file__).resolve().parents[1]


def fixture_records():
    return [
        {"schemaId":"Contract","contractId":"C-1","contradictionCount":1},
        {"schemaId":"Finding","findingId":"F-1","contractIds":["C-1"],"repairIds":["R-1"]},
        {"schemaId":"RepairCaseV1","repairCaseId":"RC-1","status":"open","findingIds":["F-1"],"repairPacketId":"RP-1","contractIds":["C-1"],"ehaCampaignId":"EHA-OLD"},
        {"schemaId":"RepairPacketV1","repairPacketId":"RP-1","repairCaseId":"RC-1","regressionWitnessIds":["W-1"],"candidateId":"SHA-NEW"},
        {"schemaId":"RegressionWitness","witnessId":"W-1","repairIds":["R-1"],"candidateSha":"SHA-NEW","forbidden":True},
        {"schemaId":"EHACampaign","campaignId":"EHA-OLD","targetId":"SHA-OLD","repairCaseId":"RC-1","result":"FAIL"},
        {"schemaId":"RepairLearningRecordV1","learningRecordId":"L-1","repairCaseId":"RC-1","capabilityIds":["CAP-1"]},
    ]


def test_bundle_has_six_bases_two_canvases_and_digest_manifest(tmp_path):
    profile = ProjectionProfile.load(ROOT / "profiles" / "codesleuth.json")
    manifest = render_projection(fixture_records(), profile, tmp_path)
    assert len(list((tmp_path / "views").glob("*.base"))) == 6
    canvases = list((tmp_path / "graphs").glob("*.canvas"))
    assert {p.name for p in canvases} == {"contract-traceability.canvas", "repair-lineage.canvas"}
    repair = json.loads((tmp_path / "graphs" / "repair-lineage.canvas").read_text())
    assert repair["edges"]
    assert all("id" in edge and edge.get("label") for edge in repair["edges"])
    doc = json.loads((tmp_path / "manifest.json").read_text())
    assert doc["roundTripCapability"] == "RENDER_ONLY"
    assert doc["projectionAuthority"] == "none"
    assert doc["outputs"]
    assert all(item["sha256"] for item in doc["outputs"])
    assert manifest["rendererId"] == "obsidian-vault"


def test_duplicate_object_ids_fail_closed(tmp_path):
    profile = ProjectionProfile.load(ROOT / "profiles" / "codesleuth.json")
    records = [
        {"schemaId":"Finding","findingId":"DUP"},
        {"schemaId":"Contract","contractId":"DUP"},
    ]
    import pytest
    with pytest.raises(ValueError, match="duplicate object id"):
        render_projection(records, profile, tmp_path)


def test_regeneration_removes_only_previous_generated_outputs(tmp_path):
    profile = ProjectionProfile.load(ROOT / "profiles" / "codesleuth.json")
    render_projection([
        {"schemaId":"Finding","findingId":"F-OLD"},
        {"schemaId":"Finding","findingId":"F-KEEP"},
    ], profile, tmp_path)
    user_note = tmp_path / "user-note.md"
    user_note.write_text("keep me")
    render_projection([
        {"schemaId":"Finding","findingId":"F-KEEP"},
    ], profile, tmp_path)
    assert not (tmp_path / "objects" / "findings" / "F-OLD.md").exists()
    assert (tmp_path / "objects" / "findings" / "F-KEEP.md").exists()
    assert user_note.read_text() == "keep me"
