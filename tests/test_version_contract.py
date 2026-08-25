from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from codesleuth_tui import CodeSleuthApp  # noqa: E402
from codesleuth_version import (  # noqa: E402
    VersionMetadataError,
    installed_version,
    source_version,
)
from textual.widgets import Static  # noqa: E402


def test_root_version_is_valid_canonical_metadata() -> None:
    version = source_version(ROOT)
    assert version == (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_missing_source_version_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(VersionMetadataError, match="missing CodeSleuth VERSION metadata"):
        source_version(tmp_path)


def test_installed_version_comes_from_review_pack_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / ".opencode" / "review-pack.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({"version": "9.8.7"}), encoding="utf-8")
    assert installed_version(tmp_path) == "9.8.7"


def test_source_cli_version_matches_root_metadata() -> None:
    env = dict(os.environ)
    env["REVIEW_PACK_DISTRIBUTION_ROOT"] = str(ROOT)
    env.pop("REVIEW_PACK_TARGET_ROOT", None)
    result = subprocess.run(
        [sys.executable, str(BIN / "review_pack_tui_bootstrap.py"), "--version"],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == source_version(ROOT)
    assert result.stderr == ""


def test_installed_cli_version_matches_installed_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / ".opencode" / "review-pack.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")
    env = dict(os.environ)
    env.pop("REVIEW_PACK_DISTRIBUTION_ROOT", None)
    env["REVIEW_PACK_TARGET_ROOT"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, str(BIN / "review_pack_tui_bootstrap.py"), "--version"],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "1.2.3"
    assert result.stderr == ""


@pytest.mark.asyncio
async def test_tui_status_uses_installed_metadata_version(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "CodeSleuth Test"], check=True)
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "fixture"], check=True, capture_output=True)

    metadata = tmp_path / ".opencode" / "review-pack.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text(
        json.dumps({"schemaVersion": 2, "version": "7.6.5", "complete": True, "source": {}}),
        encoding="utf-8",
    )

    app = CodeSleuthApp(tmp_path, None)
    async with app.run_test(size=(120, 35)) as pilot:
        await pilot.pause()
        status = str(app.query_one("#status", Static).render())
        assert "CodeSleuth 7.6.5" in status


def test_installer_uses_version_metadata_without_literal_fallback() -> None:
    installer = (ROOT / "install.py").read_text(encoding="utf-8")
    assert "VERSION = source_version(ROOT)" in installer
    assert 'else "0.3.0"' not in installer
    assert 'else "0.4.0"' not in installer
