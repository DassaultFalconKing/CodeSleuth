from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "pack/.opencode/codesleuth-naming.json"


def test_naming_manifest_is_authoritative_and_complete():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["product"] == {"displayName": "CodeSleuth", "slug": "codesleuth"}
    assert data["canonical"]["state"] == {"metadata": "codesleuth.json", "settings": "codesleuth-user.json"}
    assert data["canonical"]["entrypoints"]["verify"] == "bin/codesleuth-verify.py"
    assert data["canonical"]["python"]["tuiBootstrap"] == "bin/codesleuth_tui_bootstrap.py"
    assert data["migration"]["freshInstallMaterializesLegacy"] is False
    assert data["migration"]["bridgeManaged"] is False


def test_static_legacy_entrypoints_are_absent():
    for rel in (
        "review-pack",
        "review-pack.ps1",
        "pack/.opencode/bin/review-pack",
        "pack/.opencode/bin/review-pack.ps1",
        "pack/.opencode/bin/review-pack-update",
        "pack/.opencode/bin/review-pack-update.ps1",
        "pack/.opencode/bin/review-pack-update.py",
        "pack/.opencode/bin/review-pack-smoke.py",
        "pack/.opencode/bin/review_pack_tui.py",
        "pack/.opencode/bin/review_pack_tui_core.py",
        "pack/.opencode/bin/review_pack_tui_bootstrap.py",
    ):
        assert not (ROOT / rel).exists(), rel


def test_canonical_entrypoints_are_present():
    for rel in (
        "codesleuth",
        "codesleuth.ps1",
        "pack/.opencode/bin/codesleuth",
        "pack/.opencode/bin/codesleuth.ps1",
        "pack/.opencode/bin/codesleuth-update",
        "pack/.opencode/bin/codesleuth-update.ps1",
        "pack/.opencode/bin/codesleuth_update.py",
        "pack/.opencode/bin/codesleuth-verify.py",
        "pack/.opencode/bin/codesleuth_tui_base.py",
        "pack/.opencode/bin/codesleuth_tui_core.py",
        "pack/.opencode/bin/codesleuth_tui_bootstrap.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_legacy_product_literals_are_bounded():
    needles = ("review-pack", "review_pack", "REVIEW_PACK")
    allowed = {
        "pack/.opencode/codesleuth-naming.json",
        "docs/CODESLEUTH-NAMING-CUTOVER.md",
        "tests/test_naming_cutover.py",
    }
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in allowed or rel.startswith("docs/archive/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(needle in text for needle in needles):
            offenders.append(rel)
    assert offenders == []


def test_installer_conflicting_persistent_state_fails_closed(tmp_path):
    spec = importlib.util.spec_from_file_location("codesleuth_installer", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    target = tmp_path / ".opencode"
    target.mkdir()
    (target / module.META_NAME).write_text('{"schemaVersion": 2, "version": "new"}\n', encoding="utf-8")
    (target / module.LEGACY_META_NAME).write_text('{"schemaVersion": 2, "version": "old"}\n', encoding="utf-8")
    try:
        module._resolve_named_state(target, module.META_NAME, module.LEGACY_META_NAME)
    except RuntimeError as exc:
        assert "conflicting CodeSleuth persistent state" in str(exc)
    else:
        raise AssertionError("conflicting persistent state must fail closed")


def test_installer_migrates_identical_or_legacy_only_state(tmp_path):
    spec = importlib.util.spec_from_file_location("codesleuth_installer_migrate", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    target = tmp_path / ".opencode"
    target.mkdir()
    legacy = target / module.LEGACY_META_NAME
    legacy.write_text('{"schemaVersion": 2, "version": "dev"}\n', encoding="utf-8")
    value, migrated = module._resolve_named_state(target, module.META_NAME, module.LEGACY_META_NAME)
    assert migrated is True
    assert value["version"] == "dev"
    assert (target / module.META_NAME).is_file()
    assert not legacy.exists()
