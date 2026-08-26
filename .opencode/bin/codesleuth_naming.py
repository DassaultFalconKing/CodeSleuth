#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "codesleuth-naming.json"


class NamingStateConflict(RuntimeError):
    """Raised when canonical and legacy persistent state both exist and differ."""


def load_naming(path: Path | None = None) -> dict[str, Any]:
    manifest = path or MANIFEST_PATH
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise RuntimeError("unsupported CodeSleuth naming schema")
    for section in ("product", "canonical", "legacy", "migration"):
        if not isinstance(data.get(section), dict):
            raise RuntimeError(f"missing CodeSleuth naming section: {section}")
    return data


def state_filenames(kind: str, naming: dict[str, Any] | None = None) -> tuple[str, str]:
    data = naming or load_naming()
    if kind not in {"metadata", "settings"}:
        raise ValueError(f"unsupported CodeSleuth state kind: {kind}")
    return data["canonical"]["state"][kind], data["legacy"]["state"][kind]


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: expected a JSON object")
    return value


def resolve_state_file(opencode: Path, kind: str, *, fail_on_conflict: bool = True) -> Path | None:
    """Return the persistent-state path to read, preferring canonical when both agree."""
    canonical_name, legacy_name = state_filenames(kind)
    canonical = opencode / canonical_name
    legacy = opencode / legacy_name
    canonical_exists = canonical.is_file()
    legacy_exists = legacy.is_file()
    if not canonical_exists and not legacy_exists:
        return None
    if canonical_exists and legacy_exists:
        if _read_object(canonical) != _read_object(legacy):
            if fail_on_conflict:
                raise NamingStateConflict(
                    f"conflicting CodeSleuth persistent state: {canonical} and {legacy} differ; "
                    "refusing to guess authority"
                )
        return canonical
    return canonical if canonical_exists else legacy


def runtime_metadata_present(repo: Path) -> bool:
    opencode = repo / ".opencode"
    canonical_name, legacy_name = state_filenames("metadata")
    return (opencode / canonical_name).is_file() or (opencode / legacy_name).is_file()
