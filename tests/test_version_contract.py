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

from codesleuth_version import (  # noqa: E402
    VersionMetadataError,
    installed_version,
    source_version,
)


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


def test_installer_uses_version_metadata_without_literal_fallback() -> None:
    installer = (ROOT / "install.py").read_text(encoding="utf-8")
    assert "VERSION = source_version(ROOT)" in installer
    assert 'else "0.3.0"' not in installer
    assert 'else "0.4.0"' not in installer
