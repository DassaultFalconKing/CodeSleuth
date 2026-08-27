#!/usr/bin/env python3
"""Development entry point for the installed CodeSleuth Graphify adapter."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pack" / ".opencode" / "bin"))

from codesleuth_project.graphify_adapter import *  # noqa: F403,E402
from codesleuth_project.graphify_adapter import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
