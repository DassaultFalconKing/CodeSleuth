from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_application_tree_does_not_track_local_report_mirror() -> None:
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", ".codesleuth/reports"],
        check=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
    ).stdout.splitlines()

    assert tracked == [], (
        ".codesleuth/reports is an ignored local mirror whose shared Git transport is the orphan "
        f"reports branch; application history must not track it: {tracked}"
    )

    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".codesleuth/" in ignored
