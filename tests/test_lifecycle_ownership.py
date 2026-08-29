from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str | Path) -> None:
    subprocess.run([str(arg) for arg in args], check=True, capture_output=True)


def init_repo(path: Path) -> None:
    path.mkdir()
    run("git", "init", "-b", "main", path)
    run("git", "-C", path, "config", "user.email", "lifecycle-ownership@example.invalid")
    run("git", "-C", path, "config", "user.name", "CodeSleuth Lifecycle Ownership")
    (path / "README.md").write_text("lifecycle ownership fixture\n", encoding="utf-8")
    run("git", "-C", path, "add", "README.md")
    run("git", "-C", path, "commit", "-m", "fixture")


def test_purge_removes_only_codesleuth_owned_runtime_residue(tmp_path: Path) -> None:
    target = tmp_path / "target"
    init_repo(target)

    foreign_cache = target / ".opencode" / "bin" / "__pycache__" / "foreign_plugin.cpython-312.pyc"
    foreign_cache.parent.mkdir(parents=True)
    foreign_cache.write_bytes(b"foreign bytecode that CodeSleuth does not own\n")

    foreign_tui_trace = target / ".opencode" / "state" / "tui-backups" / "user-owned.txt"
    foreign_tui_trace.parent.mkdir(parents=True)
    foreign_tui_trace.write_text("foreign TUI state\n", encoding="utf-8")

    run(sys.executable, ROOT / "install.py", target)
    run(sys.executable, target / ".opencode" / "bin" / "review-pack-smoke.py", target)

    managed_cache_files = [
        path
        for path in (target / ".opencode" / "bin" / "__pycache__").glob("*.pyc")
        if path != foreign_cache
    ]
    assert managed_cache_files, "Verify must generate at least one CodeSleuth bytecode witness"
    assert (target / ".opencode" / "state" / "tui-backups" / "opencode.json.before-tui").is_file()

    run(sys.executable, ROOT / "install.py", target, "--uninstall", "--purge-traces")

    assert foreign_cache.read_bytes() == b"foreign bytecode that CodeSleuth does not own\n"
    assert foreign_tui_trace.read_text(encoding="utf-8") == "foreign TUI state\n"
    assert not (target / ".opencode" / "review-pack.json").exists()
    assert not (target / ".opencode" / "state" / "tui-backups" / "opencode.json.before-tui").exists()
    assert all(not path.exists() for path in managed_cache_files)
