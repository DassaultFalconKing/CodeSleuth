from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
MANIFEST = ROOT / "pack/.opencode/codesleuth-naming.json"
COMMANDS = ROOT / "pack/.opencode/commands"
TOOLS = ROOT / "pack/.opencode/tools"
CATALOG = BIN / "playbook_catalog.py"
sys.path.insert(0, str(BIN))

import playbook_catalog  # noqa: E402
from codesleuth_naming import NamingStateConflict, load_naming, resolve_state_file, runtime_metadata_present  # noqa: E402
from codesleuth_version import VersionMetadataError, installed_version  # noqa: E402


def test_naming_manifest_is_authoritative_and_complete() -> None:
    data = load_naming(MANIFEST)
    assert data["schemaVersion"] == 1
    assert data["product"] == {"displayName": "CodeSleuth", "slug": "codesleuth"}
    assert data["canonical"]["state"] == {"metadata": "codesleuth.json", "settings": "codesleuth-user.json"}
    assert data["legacy"]["state"] == {"metadata": "review-pack.json", "settings": "review-pack-user.json"}
    assert data["canonical"]["entrypoints"]["verify"] == "bin/codesleuth-verify.py"
    assert data["legacy"]["entrypoints"]["verify"] == "bin/review-pack-smoke.py"
    assert data["migration"]["failOnConflictingPersistentState"] is True
    assert data["migration"]["release040PersistentState"] == "legacy"


def test_040_keeps_live_compatibility_filenames() -> None:
    assert (ROOT / "review-pack").is_file()
    assert (ROOT / "review-pack.ps1").is_file()
    assert (ROOT / "pack/.opencode/bin/review-pack-smoke.py").is_file()
    assert (ROOT / "pack/.opencode/bin/review-pack-update.py").is_file()
    assert (ROOT / "pack/.opencode/bin/review_pack_tui_bootstrap.py").is_file()
    assert not (ROOT / "pack/.opencode/bin/codesleuth-verify.py").exists()
    assert not (ROOT / "pack/.opencode/bin/codesleuth_update.py").exists()


def test_canonical_and_legacy_state_names_do_not_overlap() -> None:
    data = load_naming(MANIFEST)
    canonical = set(data["canonical"]["state"].values())
    legacy = set(data["legacy"]["state"].values())
    assert canonical.isdisjoint(legacy)


def test_legacy_only_metadata_is_readable(tmp_path: Path) -> None:
    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    (opencode / "review-pack.json").write_text(json.dumps({"version": "9.8.7"}) + "\n", encoding="utf-8")
    path = resolve_state_file(opencode, "metadata")
    assert path == opencode / "review-pack.json"
    assert installed_version(tmp_path) == "9.8.7"
    assert runtime_metadata_present(tmp_path) is True


def test_canonical_metadata_is_preferred_when_identical(tmp_path: Path) -> None:
    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    payload = json.dumps({"version": "4.5.6"}) + "\n"
    (opencode / "review-pack.json").write_text(payload, encoding="utf-8")
    (opencode / "codesleuth.json").write_text(payload, encoding="utf-8")
    path = resolve_state_file(opencode, "metadata")
    assert path == opencode / "codesleuth.json"
    assert installed_version(tmp_path) == "4.5.6"


def test_conflicting_persistent_state_fails_closed(tmp_path: Path) -> None:
    opencode = tmp_path / ".opencode"
    opencode.mkdir()
    (opencode / "review-pack.json").write_text(json.dumps({"version": "old"}) + "\n", encoding="utf-8")
    (opencode / "codesleuth.json").write_text(json.dumps({"version": "new"}) + "\n", encoding="utf-8")
    with pytest.raises(NamingStateConflict, match="conflicting CodeSleuth persistent state"):
        resolve_state_file(opencode, "metadata")
    with pytest.raises(VersionMetadataError, match="conflicting CodeSleuth persistent state"):
        installed_version(tmp_path)


def test_rc7_canonical_invocation_namespace_is_materialized_from_naming_authority() -> None:
    data = load_naming(MANIFEST)
    invocation = data["canonical"]["invocation"]

    assert invocation["namespace"] == "codesleuth"
    operations = invocation["operations"]
    assert operations["review"]["path"] == "/codesleuth/review"
    assert operations["eha-test"]["path"] == "/codesleuth/eha/test"
    assert operations["eha-status"]["path"] == "/codesleuth/eha/status"
    assert operations["eha-repair"]["path"] == "/codesleuth/eha/repair"
    assert operations["continue"]["path"] == "/codesleuth/continue"

    canonical_paths = {metadata["path"] for metadata in operations.values()}
    assert len(canonical_paths) == len(operations)
    assert all(path.startswith("/codesleuth/") for path in canonical_paths)

    legacy_root_aliases = {f"/{path.stem}" for path in COMMANDS.glob("*.md")}
    declared_compatibility_aliases = {
        alias
        for metadata in operations.values()
        for alias in metadata.get("compatibilityAliases", [])
    }
    assert legacy_root_aliases <= declared_compatibility_aliases

    for metadata in operations.values():
        canonical_file = COMMANDS / f"{metadata['path'].removeprefix('/')}.md"
        assert canonical_file.is_file(), f"missing canonical host-native command: {canonical_file.relative_to(ROOT)}"
        for alias in metadata.get("compatibilityAliases", []):
            alias_file = COMMANDS / f"{alias.removeprefix('/')}.md"
            assert alias_file.is_file(), f"missing required compatibility alias: {alias}"

    expected_playbook_commands = {
        metadata["playbookId"]: metadata["path"]
        for metadata in operations.values()
        if metadata.get("playbookId")
    }
    expected_playbook_aliases = {
        metadata["playbookId"]: metadata["compatibilityAliases"][0]
        for metadata in operations.values()
        if metadata.get("playbookId") and metadata.get("compatibilityAliases")
    }
    assert playbook_catalog.CANONICAL_COMMANDS == expected_playbook_commands
    assert playbook_catalog.COMMAND_ALIASES == expected_playbook_aliases

    records = {record.id: record for record in playbook_catalog.discover_playbooks(ROOT, ROOT)}
    for playbook_id, canonical_command in expected_playbook_commands.items():
        assert records[playbook_id].canonical_command == canonical_command
        assert records[playbook_id].command_alias == expected_playbook_aliases[playbook_id]

    catalog_source = CATALOG.read_text(encoding="utf-8")
    assert '"repository-deep-review": "/repo-review"' not in catalog_source
    assert '"eha-sib-acceptance": "/eha-test"' not in catalog_source
    assert "load_naming" in catalog_source

    direct_tool_sentinels = {
        "context_graph_read.ts",
        "eha_state.ts",
        "repo_profile.ts",
        "review_state.ts",
    }
    assert all((TOOLS / name).is_file() for name in direct_tool_sentinels)
    assert not (TOOLS / "codesleuth").exists()
