from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
MANIFEST = ROOT / "pack/.opencode/codesleuth-naming.json"
sys.path.insert(0, str(BIN))

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
