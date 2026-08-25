#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


# Robust front-matter parsing shared by smoke and tests.
# Accepts CRLF, leading BOM, leading/trailing whitespace, and extra spacing around ':'.

_FRONTMATTER_RE = re.compile(r"^[ \t]*---[ \t]*\r?\n(.*?)\r?\n[ \t]*---[ \t]*\r?\n", re.S | re.M)


def parse_frontmatter_field_from_text(text: str, key: str) -> str | None:
    # Strip BOM if present
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if not text.lstrip().startswith("---"):
        return None
    match = _FRONTMATTER_RE.search(text)
    if match:
        inner = match.group(1)
    else:
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None
        inner = parts[1]
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.*?)\s*$")
    for line in inner.splitlines():
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return None


def parse_frontmatter_field(path: Path, key: str) -> str | None:
    text = path.read_text(encoding="utf-8")
    return parse_frontmatter_field_from_text(text, key)


# Helpers for install merge logic re-export for tests without importing install side-effects.
def merge_missing_for_test(dst: dict, src: dict, prefix: str = "") -> dict:
    import sys

    ROOT = Path(__file__).resolve().parents[2]
    # import install as module via spec to avoid side effects of ROOT detection
    import importlib.util

    spec = importlib.util.spec_from_file_location("codesleuth_install_for_test", ROOT / "install.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Prevent install.py from inserting PACK/bin again or running main
    saved_path = sys.path[:]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved_path
    # Use a copy to avoid mutating caller
    import copy

    dst_copy = copy.deepcopy(dst)
    return mod.merge_missing(dst_copy, src, prefix)


def three_way_defaults_for_test(current: dict, old: dict, new: dict, prefix: str = "") -> dict:
    import sys
    import importlib.util

    ROOT = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("codesleuth_install_for_test2", ROOT / "install.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    saved_path = sys.path[:]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved_path
    return mod.three_way_defaults(current, old, new, prefix)


def tracked_codesleuth_files(repo: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z", "--", ".codesleuth"],
        capture_output=True,
        check=True,
    )
    return [x for x in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if x]


def would_be_ignored(repo: Path, rel_path: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "-q", "--", rel_path],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0
