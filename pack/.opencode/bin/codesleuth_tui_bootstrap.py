#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
import venv
from pathlib import Path

from codesleuth_naming import load_naming
from codesleuth_version import VersionMetadataError, resolve_version

NAMING = load_naming()
ENV_DISTRIBUTION_ROOT = NAMING["canonical"]["environment"]["distributionRoot"]
ENV_TARGET_ROOT = NAMING["canonical"]["environment"]["targetRoot"]

TEXTUAL_VERSION = "8.2.8"
HERE = Path(__file__).resolve().parent
APP = HERE / "codesleuth_tui.py"
REQ = HERE / "requirements-tui.txt"


def usable_current_python() -> bool:
    try:
        return importlib.metadata.version("textual") == TEXTUAL_VERSION
    except importlib.metadata.PackageNotFoundError:
        return False


def target_root() -> Path:
    return Path(os.environ.get(ENV_TARGET_ROOT, HERE.parents[1])).resolve()


def runtime_root() -> Path:
    distribution = os.environ.get(ENV_DISTRIBUTION_ROOT)
    if distribution:
        return Path(distribution).resolve() / ".runtime" / "tui"
    return target_root() / ".opencode" / "state" / "tui-runtime"


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


def cleanup_transition_bridges(target: Path) -> None:
    if not NAMING["migration"].get("removeBridgeAfterCanonicalBootstrap", False):
        return
    opencode = target.resolve() / ".opencode"
    for rel in NAMING["migration"].get("bridgeEntrypoints", []):
        candidate = opencode / rel
        try:
            if candidate.is_file():
                candidate.unlink()
        except OSError:
            pass


def main() -> int:
    try:
        version = resolve_version()
    except VersionMetadataError as exc:
        print(f"Unable to resolve CodeSleuth version metadata: {exc}", file=sys.stderr)
        return 2

    if sys.argv[1:] == ["--version"]:
        print(version)
        return 0

    if sys.version_info < (3, 10):
        print("CodeSleuth requires Python 3.10+", file=sys.stderr)
        return 2
    if usable_current_python():
        python = Path(sys.executable)
    else:
        try:
            python = ensure_runtime(version)
        except Exception as exc:
            print(f"Unable to prepare the isolated CodeSleuth {version} Textual runtime: {exc}", file=sys.stderr)
            print(f"Install textual=={TEXTUAL_VERSION} in an isolated environment or retry with network access.", file=sys.stderr)
            return 2

    cleanup_transition_bridges(target_root())
    return subprocess.call([str(python), str(APP), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
