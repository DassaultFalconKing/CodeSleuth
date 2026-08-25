from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("codesleuth_installer_edit_test", ROOT / "install.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_merge_missing_preserves_nested_edit_and_adds_reports_allow() -> None:
    installer = load_installer()
    dst = {"permission": {"edit": {"*": "deny", "custom/**": "allow"}}}
    src = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}}
    out = installer.merge_missing(copy.deepcopy(dst), src)
    assert out["permission"]["edit"]["*"] == "deny"
    assert out["permission"]["edit"]["custom/**"] == "allow"
    assert out["permission"]["edit"][".codesleuth/reports/**"] == "allow"


def test_merge_missing_does_not_clobber_nested_edit_when_src_is_dict() -> None:
    installer = load_installer()
    dst = {"permission": {"edit": {"*": "ask", "already": "keep"}}}
    src = {
        "permission": {
            "edit": {"*": "ask", ".codesleuth/reports/**": "allow"},
            "bash": {"*": "ask"},
        }
    }
    out = installer.merge_missing(copy.deepcopy(dst), src)
    assert isinstance(out["permission"]["edit"], dict)
    assert out["permission"]["edit"]["already"] == "keep"
    assert out["permission"]["edit"][".codesleuth/reports/**"] == "allow"
    assert out["permission"]["bash"]["*"] == "ask"


def test_three_way_defaults_preserves_user_edit_override_on_pack_update() -> None:
    installer = load_installer()
    old_base = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}}
    new_base = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}}
    current = {"permission": {"edit": {"*": "deny", ".codesleuth/reports/**": "allow"}}}
    out = installer.three_way_defaults(current, old_base, new_base)
    assert out["permission"]["edit"]["*"] == "deny"
    assert out["permission"]["edit"][".codesleuth/reports/**"] == "allow"


def test_three_way_defaults_adds_new_pack_edit_key_when_user_unchanged() -> None:
    installer = load_installer()
    old_base = {"permission": {"edit": {"*": "ask"}}}
    new_base = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}}
    current = {"permission": {"edit": {"*": "ask"}}}
    out = installer.three_way_defaults(current, old_base, new_base)
    assert out["permission"]["edit"][".codesleuth/reports/**"] == "allow"
    assert out["permission"]["edit"]["*"] == "ask"


def test_update_config_merge_missing_adds_reports_edit_allow_without_clobbering_custom(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess_args = ["git", "-C", str(repo), "init"]
    import subprocess

    subprocess.run(subprocess_args, check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "CodeSleuth Test"], check=True)
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
    # create existing opencode.json with nested edit mapping
    oc = repo / ".opencode"
    oc.mkdir(parents=True)
    existing = {
        "permission": {"edit": {"*": "deny", "custom/path/**": "allow"}},
        "compaction": {"reserved": 12345},
    }
    (oc / "opencode.json").write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    installer = load_installer()
    # simulate non-update install path (merge_missing)
    base = json.loads((ROOT / "pack" / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    current = json.loads((oc / "opencode.json").read_text(encoding="utf-8"))
    merged = installer.merge_missing(copy.deepcopy(current), base)
    assert merged["permission"]["edit"]["*"] == "deny"
    assert merged["permission"]["edit"]["custom/path/**"] == "allow"
    assert merged["permission"]["edit"][".codesleuth/reports/**"] == "allow"
    # persisted result also preserves compaction
    assert merged["compaction"]["reserved"] == 12345
    # exercise actual update_config helper (non-update)
    installer.update_config(repo, old_meta=None, update=False)
    on_disk = json.loads((oc / "opencode.json").read_text(encoding="utf-8"))
    assert on_disk["permission"]["edit"]["custom/path/**"] == "allow"
    assert on_disk["permission"]["edit"][".codesleuth/reports/**"] == "allow"


def test_update_config_three_way_preserves_user_override(tmp_path: Path) -> None:
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    oc = repo / ".opencode"
    oc.mkdir(parents=True)
    base_old = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}, "compaction": {"reserved": 20000}}
    base_new = {"permission": {"edit": {"*": "ask", ".codesleuth/reports/**": "allow"}}, "compaction": {"reserved": 30000}}
    current = {"permission": {"edit": {"*": "deny", ".codesleuth/reports/**": "allow"}}, "compaction": {"reserved": 12345}}
    (oc / "opencode.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    installer = load_installer()
    old_meta = {"baseConfig": base_old}
    # monkeypatch PACK opencode.json read by temporarily swapping file content
    pack_cfg = ROOT / "pack" / ".opencode" / "opencode.json"
    orig = pack_cfg.read_text(encoding="utf-8")
    try:
        pack_cfg.write_text(json.dumps(base_new, indent=2) + "\n", encoding="utf-8")
        installer.update_config(repo, old_meta=old_meta, update=True)
    finally:
        pack_cfg.write_text(orig, encoding="utf-8")
    after = json.loads((oc / "opencode.json").read_text(encoding="utf-8"))
    assert after["permission"]["edit"]["*"] == "deny"
    assert after["permission"]["edit"][".codesleuth/reports/**"] == "allow"
