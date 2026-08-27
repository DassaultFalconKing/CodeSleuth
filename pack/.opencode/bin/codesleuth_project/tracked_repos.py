"""Host-local registry of repositories tracked by CodeSleuth."""
from __future__ import annotations

import json
import os
import subprocess
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


def _git_output(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def short_remote(url: str | None) -> str | None:
    """Return a compact remote identity such as ``owner/repo`` or a directory name."""
    if not url:
        return None
    original = str(url).strip()
    cleaned = original.rstrip("/").replace("\\", "/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    if "://" not in cleaned and ":" in cleaned.split("/")[0]:
        cleaned = cleaned.split(":", 1)[-1]
    parts = [part for part in cleaned.split("/") if part]
    if not parts:
        return None
    hostish = original.lower()
    if len(parts) >= 2 and any(host in hostish for host in ("github.com", "gitlab.com", "bitbucket.org")):
        return "/".join(parts[-2:])
    return parts[-1]


def source_label(source: Any) -> str:
    """Return a compact CodeSleuth source label, or ``no source`` when unknown."""
    if not isinstance(source, dict):
        return "no source"
    remote = source.get("remote")
    short = short_remote(str(remote) if remote else None)
    if not short:
        return "no source"
    ref = str(source.get("ref") or "").strip()
    return f"{short}@{ref}" if ref else short


def format_tracked_label(entry: dict[str, Any]) -> str:
    """Return the operator-visible catalog line for a tracked repository."""
    path = str(entry.get("path") or "")
    name = str(entry.get("name") or Path(path).name or "unnamed")
    version = str(entry.get("version") or "n/a")
    mark = "" if entry.get("reachable", True) else " (missing)"
    return f"{name} · {source_label(entry.get('source'))} · {version}{mark}"


def _installed_metadata(path: Path) -> dict[str, Any] | None:
    try:
        from codesleuth_naming import resolve_state_file

        meta_path = resolve_state_file(path / ".opencode", "metadata", fail_on_conflict=False)
    except Exception:
        return None
    if meta_path is None or not meta_path.is_file():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _source_from_metadata(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    source = payload.get("source")
    if not isinstance(source, dict):
        return None
    remote = source.get("remote")
    ref = source.get("ref")
    commit = source.get("commit")
    if not remote and not ref and not commit:
        return None
    return {
        "remote": remote,
        "ref": ref,
        "subdir": source.get("subdir") or "",
        "commit": commit,
    }


def _probe_entry(path_str: str) -> dict[str, Any]:
    """Build a registry entry from the current on-disk lifecycle, when available."""
    from . import dependency_status, lifecycle_state  # local import avoids cycle at module load

    path = Path(path_str)
    folder_name = path.name or path_str
    entry: dict[str, Any] = {
        "path": path_str,
        "exists": path.is_dir(),
        "name": folder_name,
        "origin": None,
        "source": None,
        "lifecycle": None,
        "version": None,
        "dependencyBound": None,
        "reachable": False,
    }
    if not path.is_dir():
        return entry
    origin = _git_output(path, "remote", "get-url", "origin")
    entry["origin"] = origin
    entry["name"] = short_remote(origin) or folder_name
    try:
        entry["lifecycle"] = lifecycle_state(path)
        entry["dependencyBound"] = bool(dependency_status(path).get("bound"))
        entry["reachable"] = True
    except Exception:
        return entry
    payload = _installed_metadata(path)
    if payload:
        entry["version"] = payload.get("version")
        entry["source"] = _source_from_metadata(payload)
    return entry


def _stored_entry(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source")
    return {
        "path": item["path"],
        "addedAt": item.get("addedAt"),
        "lastSeenAt": item.get("lastSeenAt"),
        "name": item.get("name"),
        "origin": item.get("origin"),
        "source": source if isinstance(source, dict) else None,
        "lifecycle": item.get("lifecycle"),
        "version": item.get("version"),
        "dependencyBound": item.get("dependencyBound"),
    }


def list_tracked_repositories(*, refresh: bool = True, prune_missing: bool | None = None) -> list[dict[str, Any]]:
    """Return tracked repositories, optionally refreshing live identity fields.

    Refresh drops paths that no longer exist so the operator catalog cannot keep
    stale version-only rows from deleted test/install targets.
    """
    if prune_missing is None:
        prune_missing = refresh
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
            if prune_missing and not live.get("reachable"):
                changed = True
                continue
            if live.get("reachable"):
                entry.update(live)
                entry["path"] = path_str
            else:
                entry["exists"] = False
                entry["reachable"] = False
            entry["lastSeenAt"] = utc_iso()
            changed = True
        results.append(entry)
    results.sort(key=lambda item: str(item.get("lastSeenAt") or item.get("addedAt") or ""), reverse=True)
    if changed:
        data["repositories"] = [_stored_entry(item) for item in results]
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
            updated = _stored_entry(
                {
                    **live,
                    "path": path_str,
                    "addedAt": raw.get("addedAt") or now,
                    "lastSeenAt": now,
                }
            )
            repos.append(updated)
        else:
            repos.append(_stored_entry({**raw, "path": existing_path}))
    if updated is None:
        updated = _stored_entry({**live, "path": path_str, "addedAt": now, "lastSeenAt": now})
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
