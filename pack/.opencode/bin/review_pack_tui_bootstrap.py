#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.metadata
import os
import subprocess
import sys
import threading
import time
import venv
from dataclasses import dataclass
from pathlib import Path

from codesleuth_version import VersionMetadataError, resolve_version

TEXTUAL_VERSION = "8.2.8"
HERE = Path(__file__).resolve().parent
REQ = HERE / "requirements-tui.txt"
RESTART_MARKER = Path(".opencode") / "state" / "tui-restart-request.json"
WATCH_POLL_SECONDS = 0.20
SOURCE_PROBE_SECONDS = 1.0


@dataclass
class RuntimeWatch:
    target_root: Path
    marker: Path
    marker_token: str | None
    source_root: Path | None
    source_head: str | None
    last_source_probe: float = 0.0


def usable_current_python() -> bool:
    try:
        return importlib.metadata.version("textual") == TEXTUAL_VERSION
    except importlib.metadata.PackageNotFoundError:
        return False


def runtime_root() -> Path:
    distribution = os.environ.get("REVIEW_PACK_DISTRIBUTION_ROOT")
    if distribution:
        return Path(distribution).resolve() / ".runtime" / "tui"
    target = Path(os.environ.get("REVIEW_PACK_TARGET_ROOT", HERE.parents[2])).resolve()
    return target / ".opencode" / "state" / "tui-runtime"


def venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_runtime(version: str) -> Path:
    root = runtime_root()
    python = venv_python(root)
    marker = root / ".textual-version"
    if python.is_file() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == TEXTUAL_VERSION:
        return python
    root.mkdir(parents=True, exist_ok=True)
    print(f"Preparing isolated CodeSleuth {version} TUI runtime in {root}", file=sys.stderr)
    venv.EnvBuilder(with_pip=True, clear=python.exists()).create(root)
    python = venv_python(root)
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--requirement",
            str(REQ),
        ],
        check=True,
    )
    marker.write_text(TEXTUAL_VERSION + "\n", encoding="utf-8")
    return python


def git_output(repo: Path, *args: str) -> str | None:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return text or None


def git_root(path: Path) -> Path | None:
    value = git_output(path, "rev-parse", "--show-toplevel")
    return Path(value).resolve() if value else None


def read_marker_token(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def capture_runtime_watch(target: Path, distribution_root: Path | None) -> RuntimeWatch:
    target_root = git_root(target) or target.resolve()
    marker = target_root / RESTART_MARKER
    source_root = git_root(distribution_root) if distribution_root else None
    if source_root != target_root:
        source_root = None
    source_head = git_output(source_root, "rev-parse", "HEAD") if source_root else None
    return RuntimeWatch(
        target_root=target_root,
        marker=marker,
        marker_token=read_marker_token(marker),
        source_root=source_root,
        source_head=source_head,
        last_source_probe=time.monotonic(),
    )


def restart_requested(watch: RuntimeWatch) -> bool:
    token = read_marker_token(watch.marker)
    if token is not None and token != watch.marker_token:
        return True

    if watch.source_root is None or watch.source_head is None:
        return False
    now = time.monotonic()
    if now - watch.last_source_probe < SOURCE_PROBE_SECONDS:
        return False
    watch.last_source_probe = now
    current_head = git_output(watch.source_root, "rev-parse", "HEAD")
    return current_head is not None and current_head != watch.source_head


def parse_app_args(argv: list[str]) -> tuple[Path, Path | None]:
    parser = argparse.ArgumentParser(description="CodeSleuth Evidence Console for repository review and runtime control")
    parser.add_argument("repo", nargs="?", help="target Git repository")
    parser.add_argument("--target", help="target Git repository (same as positional repo)")
    args = parser.parse_args(argv)
    distribution = os.environ.get("REVIEW_PACK_DISTRIBUTION_ROOT")
    target = args.target or args.repo or os.environ.get("REVIEW_PACK_TARGET_ROOT") or "."
    return Path(target), Path(distribution) if distribution else None


def ensure_textual_runtime(argv: list[str], version: str) -> int | None:
    if sys.version_info < (3, 10):
        print("CodeSleuth requires Python 3.10+", file=sys.stderr)
        return 2
    if usable_current_python():
        return None
    try:
        python = ensure_runtime(version)
    except Exception as exc:
        print(f"Unable to prepare the isolated CodeSleuth {version} Textual runtime: {exc}", file=sys.stderr)
        print(
            f"Install textual=={TEXTUAL_VERSION} in an isolated environment or retry with network access.",
            file=sys.stderr,
        )
        return 2
    if python.resolve() != Path(sys.executable).resolve():
        sys.stdout.flush()
        sys.stderr.flush()
        os.execv(str(python), [str(python), str(Path(__file__).resolve()), *argv])
    return None


def reexec_bootstrap(argv: list[str]) -> None:
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), *argv])


def supervise_app(target: Path, distribution_root: Path | None, argv: list[str]) -> int:
    from codesleuth_tui_runtime import CodeSleuthApp, launch_opencode

    app = CodeSleuthApp(target, distribution_root)
    watch = capture_runtime_watch(target, distribution_root)
    restart_event = threading.Event()
    stop_event = threading.Event()

    def watch_loop() -> None:
        while not stop_event.wait(WATCH_POLL_SECONDS):
            if not restart_requested(watch):
                continue
            restart_event.set()
            try:
                app.call_from_thread(app.exit, ("restart", watch.target_root))
            except RuntimeError:
                pass
            return

    watcher = threading.Thread(target=watch_loop, name="codesleuth-update-watch", daemon=True)
    watcher.start()
    try:
        result = app.run()
    finally:
        stop_event.set()
        watcher.join(timeout=1.0)

    if restart_event.is_set() or (result and result[0] == "restart"):
        reexec_bootstrap(argv)
    if result and result[0] == "launch":
        return launch_opencode(result[1])
    return 0


def main() -> int:
    argv = sys.argv[1:]
    try:
        version = resolve_version()
    except VersionMetadataError as exc:
        print(f"Unable to resolve CodeSleuth version metadata: {exc}", file=sys.stderr)
        return 2

    if argv == ["--version"]:
        print(version)
        return 0

    runtime_error = ensure_textual_runtime(argv, version)
    if runtime_error is not None:
        return runtime_error
    target, distribution_root = parse_app_args(argv)
    return supervise_app(target, distribution_root, argv)


if __name__ == "__main__":
    raise SystemExit(main())
