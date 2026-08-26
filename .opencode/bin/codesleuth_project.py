#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical ``bin/codesleuth_project.py`` path.

The lifecycle implementation is package-based. The file remains because the current
CodeSleuth naming contract exposes this exact Python path and older installed callers
may still execute it directly.
"""
from __future__ import annotations

from codesleuth_project import main


if __name__ == "__main__":
    raise SystemExit(main())
