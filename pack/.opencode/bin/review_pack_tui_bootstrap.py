#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
import venv
from pathlib import Path

TEXTUAL_VERSION = "8.2.8"
HERE = Path(__file__).resolve().parent
APP = HERE / "codesleuth_tui.py"
REQ = HERE / "requirements-tui.txt"


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


def ensure_runtime() -> Path:
    root = runtime_root()
    python = venv_python(root)
    marker = root / ".textual-version"
    if python.is_file() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == TEXTUAL_VERSION:
        return python
    root.mkdir(parents=True, exist_ok=True)
    print(f"Preparing isolated CodeSleuth TUI runtime in {root}", file=sys.stderr)
    venv.EnvBuilder(with_pip=True, clear=python.exists()).create(root)
    python = venv_python(root)
    subprocess.run([
        str(python), "-m", "pip", "install",
        "--disable-pip-version-check",
        "--requirement", str(REQ),
    ], check=True)
    marker.write_text(TEXTUAL_VERSION + "\n", encoding="utf-8")
    return python


def main() -> int:
    if sys.version_info < (3, 9):
        print("CodeSleuth TUI requires Python 3.9+", file=sys.stderr)
        return 2
    if usable_current_python():
        python = Path(sys.executable)
    else:
        try:
            python = ensure_runtime()
        except Exception as exc:
            print(f"Unable to prepare the isolated CodeSleuth Textual runtime: {exc}", file=sys.stderr)
            print("Install textual==8.2.8 in an isolated environment or retry with network access.", file=sys.stderr)
            return 2
    return subprocess.call([str(python), str(APP), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
