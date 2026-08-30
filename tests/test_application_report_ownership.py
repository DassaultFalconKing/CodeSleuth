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
        f"reports branch; the current application tree must not track it: {tracked}"
    )

    probe = ".codesleuth/reports/__ownership_probe__.md"
    ignored = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "--verbose", "--no-index", probe],
        check=False,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
    )
    assert ignored.returncode == 0, (
        ".codesleuth must remain effectively ignored for the local report mirror; "
        f"git check-ignore returned {ignored.returncode}: {ignored.stderr or ignored.stdout}"
    )
