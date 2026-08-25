#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "codesleuth-naming.json"


def load_naming(path: Path | None = None) -> dict[str, Any]:
    manifest = path or MANIFEST_PATH
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise RuntimeError("unsupported CodeSleuth naming schema")
    for section in ("product", "canonical", "legacy", "migration"):
        if not isinstance(data.get(section), dict):
            raise RuntimeError(f"missing CodeSleuth naming section: {section}")
    return data
