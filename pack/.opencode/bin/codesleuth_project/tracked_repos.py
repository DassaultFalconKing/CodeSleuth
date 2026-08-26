"""Host-local registry of repositories tracked by CodeSleuth."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_NAME = "tracked-repositories.json"
SCHEMA_VERSION = 1


def utc_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def host_state_dir() -> Path:
    """Return the host directory for CodeSleuth operator state.

    Override with ``CODESLEUTH_HOST_STATE_DIR`` (useful for tests and isolated hosts).
    Default: ``%LOCALAPPDATA%/CodeSleuth`` on Windows, else
    ``$XDG_DATA_HOME/codesleuth`` or ``~/.local/share/codesleuth``.
    """
    override = os.environ.get("CODESLEUTH_HOST_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return (base / "CodeSleuth").resolve()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return (Path(xdg).expanduser().resolve() / "codesleuth")
    return (Path.home() / ".local" / "share" / "codesleuth").resolve()


def registry_path() -> Path:
    """Return the JSON registry path on this host."""
    return host_state_dir() / REGISTRY_NAME


def _empty_registry() -> dict[str, Any]:
    return {"schemaVersion": SCHEMA_VERSION, "repositories": []}


def load_registry() -> dict[str, Any]:
    """Load the host registry, returning an empty schema when missing/corrupt."""
    path = registry_path()
    if not path.is_file():
        return _empty_registry()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_registry()
    if not isinstance(data, dict):
        return _empty_registry()
    repos = data.get("repositories")
    if not isinstance(repos, list):
        repos = []
    return {"schemaVersion": int(data.get("schemaVersion") or SCHEMA_VERSION), "repositories": repos}


def save_registry(data: dict[str, Any]) -> Path:
    """Persist the host registry and return its path."""
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": int(data.get("schemaVersion") or SCHEMA_VERSION),
        "repositories": list(data.get("repositories") or []),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _normalize_path(repo: Path) -> str:
    return str(Path(repo).expanduser().resolve())


def _probe_entry(path_str: str) -> dict[str, Any]:
    """Build a registry entry from the current on-disk lifecycle, when available."""
    from . import dependency_status, lifecycle_state  # local import avoids cycle at module load

    path = Path(path_str)
    entry: dict[str, Any] = {
        "path": path_str,
        "exists": path.is_dir(),
        "lifecycle": None,
        "version": None,
        "dependencyBound": None,
        "reachable": False,
    }
    if not path.is_dir():
        return entry
    try:
        entry["lifecycle"] = lifecycle_state(path)
        entry["dependencyBound"] = bool(dependency_status(path).get("bound"))
        entry["reachable"] = True
    except Exception:
        return entry
    meta = path / ".opencode" / "review-pack.json"
    if meta.is_file():
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
            entry["version"] = payload.get("version")
        except (OSError, json.JSONDecodeError):
            pass
    return entry


def list_tracked_repositories(*, refresh: bool = True) -> list[dict[str, Any]]:
    """Return tracked repositories, optionally refreshing live lifecycle fields."""
    data = load_registry()
    results: list[dict[str, Any]] = []
    changed = False
    for raw in data["repositories"]:
        if not isinstance(raw, dict) or not raw.get("path"):
            continue
        path_str = _normalize_path(Path(str(raw["path"])))
        entry = dict(raw)
        entry["path"] = path_str
        if refresh:
            live = _probe_entry(path_str)
            for key, value in live.items():
                if value is not None or key in {"exists", "reachable"}:
                    entry[key] = value
            entry["lastSeenAt"] = utc_iso()
            changed = True
        results.append(entry)
    results.sort(key=lambda item: str(item.get("lastSeenAt") or item.get("addedAt") or ""), reverse=True)
    if changed:
        data["repositories"] = [
            {
                "path": item["path"],
                "addedAt": item.get("addedAt"),
                "lastSeenAt": item.get("lastSeenAt"),
                "lifecycle": item.get("lifecycle"),
                "version": item.get("version"),
                "dependencyBound": item.get("dependencyBound"),
            }
            for item in results
        ]
        save_registry(data)
    return results


def record_tracked_repository(repo: Path) -> dict[str, Any]:
    """Upsert *repo* in the host registry and return the stored entry."""
    path_str = _normalize_path(repo)
    live = _probe_entry(path_str)
    data = load_registry()
    now = utc_iso()
    updated: dict[str, Any] | None = None
    repos: list[dict[str, Any]] = []
    for raw in data["repositories"]:
        if not isinstance(raw, dict) or not raw.get("path"):
            continue
        existing_path = _normalize_path(Path(str(raw["path"])))
        if existing_path == path_str:
            updated = {
                "path": path_str,
                "addedAt": raw.get("addedAt") or now,
                "lastSeenAt": now,
                "lifecycle": live.get("lifecycle"),
                "version": live.get("version"),
                "dependencyBound": live.get("dependencyBound"),
            }
            repos.append(updated)
        else:
            repos.append({**raw, "path": existing_path})
    if updated is None:
        updated = {
            "path": path_str,
            "addedAt": now,
            "lastSeenAt": now,
            "lifecycle": live.get("lifecycle"),
            "version": live.get("version"),
            "dependencyBound": live.get("dependencyBound"),
        }
        repos.append(updated)
    data["repositories"] = repos
    save_registry(data)
    return {**updated, "exists": live.get("exists"), "reachable": live.get("reachable")}


def forget_tracked_repository(repo: Path) -> bool:
    """Remove *repo* from the host registry. Return True when an entry was removed."""
    path_str = _normalize_path(repo)
    data = load_registry()
    kept = [
        raw
        for raw in data["repositories"]
        if isinstance(raw, dict) and raw.get("path") and _normalize_path(Path(str(raw["path"]))) != path_str
    ]
    removed = len(kept) != len(data["repositories"])
    if removed:
        data["repositories"] = kept
        save_registry(data)
    return removed
