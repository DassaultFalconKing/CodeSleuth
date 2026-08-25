from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location(
        "codesleuth_installer_git_gate", ROOT / "install.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("git version 2.35.0", (2, 35, 0)),
        ("git version 2.35.0.windows.1", (2, 35, 0)),
        ("git version 2.49.0", (2, 49, 0)),
        ("git version 2.30.2 (Apple Git-136)", (2, 30, 2)),
    ],
)
def test_parse_git_version(raw: str, expected: tuple[int, int, int]) -> None:
    installer = load_installer()
    assert installer.parse_git_version(raw) == expected


def test_parse_git_version_rejects_garbage() -> None:
    installer = load_installer()
    with pytest.raises(ValueError, match="unrecognized git version"):
        installer.parse_git_version("not a version")


def test_require_git_version_passes_current_git() -> None:
    installer = load_installer()
    version = installer.require_git_version()
    assert version >= installer.MIN_GIT_VERSION


def test_require_git_version_fails_closed_for_old_git(monkeypatch: pytest.MonkeyPatch) -> None:
    installer = load_installer()

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="git version 2.34.1\n", stderr="")

    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    with pytest.raises(SystemExit, match="requires Git 2.35.0"):
        installer.require_git_version()


def test_require_git_version_fails_when_git_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    installer = load_installer()

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="git: command not found")

    monkeypatch.setattr(installer.subprocess, "run", fake_run)
    with pytest.raises(SystemExit, match="git --version"):
        installer.require_git_version()
