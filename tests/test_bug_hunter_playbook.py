import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "pack" / ".opencode" / "playbooks" / "bug-hunter"
COMMAND = ROOT / "pack" / ".opencode" / "commands" / "bug-hunt.md"


def test_bug_hunter_manifest_has_read_only_audit_shape() -> None:
    manifest = json.loads((PLAYBOOK / "playbook.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "bug-hunter"
    assert manifest["steps"][0]["skill"] == "exact-target-identity"
    assert manifest["steps"][-1]["skill"] == "codesleuth-reports"
    assert [step["id"] for step in manifest["steps"]] == [
        "capture-target",
        "authority-and-scope",
        "pattern-hunt",
        "verify-and-ledger",
        "persist-report",
    ]


def test_bug_hunter_command_routes_to_playbook_and_forbids_repairs() -> None:
    text = COMMAND.read_text(encoding="utf-8")
    assert "bug-hunter" in text
    assert "read-only" in text
    assert "Do not fix findings" in text
    assert "exactly one Step" in text


def test_bug_hunter_hunts_every_contributor_error_class() -> None:
    text = (PLAYBOOK / "steps" / "03-pattern-hunt.md").read_text(encoding="utf-8")
    for number in range(1, 11):
        assert f"EP-{number:02d}" in text
    assert "whole repository" in text
    assert "Do not fix anything" in text


def test_bug_hunter_authority_step_runs_scanner_without_promoting_it() -> None:
    text = (PLAYBOOK / "steps" / "02-authority-and-scope.md").read_text(encoding="utf-8")
    for expected in (
        "AGENTS.md",
        "CONTRIBUTING.md",
        "docs/CONTRIBUTOR-ERROR-PATTERNS.md",
        ".github/workflows/acceptance.yml",
        "python scripts/contributor_antipatterns.py scan --strict",
        "not by itself a verified semantic finding",
    ):
        assert expected in text


def test_bug_hunter_verifies_witness_and_returns_merge_ledger() -> None:
    text = (PLAYBOOK / "steps" / "04-verify-and-ledger.md").read_text(encoding="utf-8")
    for expected in (
        "producer → transformation → consumer",
        "canonical-gate reachability",
        "INVESTIGATE",
        "PATTERN LEDGER",
        "CANONICAL-GATE GAPS",
        "SAFE-TO-MERGE",
        "STOP CONDITIONS",
        "Do not repair findings",
    ):
        assert expected in text
