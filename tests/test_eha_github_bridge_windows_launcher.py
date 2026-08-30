from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eha_github_bridge.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("eha_github_bridge_windows", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_posix_eha_bridge_uses_posix_opencode_wrapper(tmp_path: Path) -> None:
    bridge = load_bridge()
    wrapper = tmp_path / "pack" / ".opencode" / "bin" / "opencode-review"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    assert bridge.opencode_wrapper_command(tmp_path, platform_name="posix") == [str(wrapper)]


def test_windows_eha_bridge_uses_powershell_wrapper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = load_bridge()
    wrapper = tmp_path / "pack" / ".opencode" / "bin" / "opencode-review.ps1"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("& opencode @args\n", encoding="utf-8")
    pwsh = r"C:\Program Files\PowerShell\7\pwsh.exe"
    monkeypatch.setattr(bridge.shutil, "which", lambda name: pwsh if name == "pwsh" else None)

    command = bridge.opencode_wrapper_command(tmp_path, platform_name="nt")

    assert command == [
        pwsh,
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper),
    ]


def test_windows_eha_bridge_fails_closed_without_powershell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = load_bridge()
    wrapper = tmp_path / "pack" / ".opencode" / "bin" / "opencode-review.ps1"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("& opencode @args\n", encoding="utf-8")
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)

    with pytest.raises(bridge.BridgeError, match="PowerShell"):
        bridge.opencode_wrapper_command(tmp_path, platform_name="nt")
