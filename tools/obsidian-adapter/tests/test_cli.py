from pathlib import Path
import json
from codesleuth_obsidian_adapter.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_renders_json_and_validates(tmp_path):
    source = tmp_path / "objects.json"
    source.write_text(json.dumps([{"schemaId":"Finding","findingId":"F-9"}]))
    vault = tmp_path / "vault"
    assert main(["render", "--input", str(source), "--profile", str(ROOT / "profiles" / "codesleuth.json"), "--output", str(vault)]) == 0
    assert main(["validate", "--vault", str(vault)]) == 0


def test_cli_reads_ndjson(tmp_path):
    source = tmp_path / "objects.ndjson"
    source.write_text('{"schemaId":"Contract","contractId":"C-9"}\n{"schemaId":"Finding","findingId":"F-9","contractIds":["C-9"]}\n')
    vault = tmp_path / "vault"
    assert main(["render", "--input", str(source), "--profile", str(ROOT / "profiles" / "codesleuth.json"), "--output", str(vault)]) == 0
    assert (vault / "objects" / "contracts" / "C-9.md").exists()
