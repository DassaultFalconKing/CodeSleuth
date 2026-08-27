"""CodeSleuth project lifecycle: install snapshots, bind, and uninstall.

Path/workspace helpers live in ``codesleuth_project.paths`` and are re-exported
here for backward compatibility (``import codesleuth_project as lifecycle``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codesleuth_naming import resolve_state_file, runtime_metadata_present, state_filenames

from .paths import (
    AGENTS_BEGIN,
    AGENTS_END,
    AGENTS_POINTER,
    IGNORE_BEGIN,
    IGNORE_END,
    IGNORE_LINES,
    LOCAL_ROOT,
    REPORTS_DIR,
    REPORTS_INDEX,
    REPORTS_INDEX_HEADER,
    REPORTS_INDEX_PLACEHOLDER,
    REPORTS_README,
    ensure_agents_reports_pointer,
    ensure_local_gitignore,
    ensure_reports_workspace,
    remove_agents_reports_pointer,
    remove_local_gitignore_block,
    report_timestamp_key,
    update_reports_index,
    validate_agents_pointer,
)
from .tracked_repos import (
    forget_tracked_repository,
    format_tracked_label,
    host_state_dir,
    list_tracked_repositories,
    record_tracked_repository,
    registry_path,
    short_remote,
    source_label,
)

DEFAULT_DEPENDENCY_PATH = "tools/codesleuth"

SKIP_SNAPSHOT_DIRS = {
    ".cache",
    "cache",
    "logs",
    "sessions",
    "snapshots",
    "state",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run ``git`` in *repo* with *args* and return the completed process."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def utc_stamp() -> str:
    """Return a compact UTC timestamp string for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_rel(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"dependency path must stay inside the target repository: {value}")
    return path


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _path_state(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.is_dir():
        return "directory"
    if not path.exists():
        return "absent"
    return "other"


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _snapshot_candidates(repo: Path) -> list[Path]:
    candidates: list[Path] = []
    for root_name in (".gitignore", ".gitmodules"):
        root_file = repo / root_name
        if root_file.is_file():
            candidates.append(root_file)
    opencode = repo / ".opencode"
    if not opencode.is_dir():
        return candidates
    for path in sorted(opencode.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(opencode)
        if any(part in SKIP_SNAPSHOT_DIRS for part in rel.parts):
            continue
        if path.suffix in {".pyc", ".log", ".tmp"}:
            continue
        candidates.append(path)
    return candidates


def create_preinstall_snapshot(repo: Path) -> dict[str, Any]:
    """Snapshot pre-existing OpenCode/project state before install."""
    repo = repo.resolve()
    root = repo / LOCAL_ROOT
    pointer = root / "preinstall.json"
    if pointer.is_file():
        data = json.loads(pointer.read_text(encoding="utf-8"))
        manifest_path = repo / data["manifest"]
        if manifest_path.is_file():
            return data

    stamp = utc_stamp()
    snapshot = root / "backups" / "pre-install" / stamp
    files_root = snapshot / "files"
    entries: list[dict[str, str]] = []
    for source in _snapshot_candidates(repo):
        rel = source.relative_to(repo)
        target = files_root / rel
        _copy_file(source, target)
        entries.append({"path": rel.as_posix(), "sha256": sha256_file(source)})

    manifest = {
        "schemaVersion": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "opencodeExisted": (repo / ".opencode").exists(),
        "gitignoreExisted": (repo / ".gitignore").exists(),
        "gitmodulesExisted": (repo / ".gitmodules").exists(),
        "baselineKind": "pre-0.3-upgrade" if runtime_metadata_present(repo) else "pre-install",
        "files": entries,
    }
    manifest_path = snapshot / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer_data = {
        "schemaVersion": 1,
        "manifest": manifest_path.relative_to(repo).as_posix(),
    }
    _write_json(pointer, pointer_data)
    ensure_local_gitignore(repo)
    return pointer_data


def _load_snapshot(repo: Path) -> tuple[dict[str, Any] | None, Path | None]:
    pointer = repo / LOCAL_ROOT / "preinstall.json"
    if not pointer.is_file():
        return None, None
    pointer_data = json.loads(pointer.read_text(encoding="utf-8"))
    manifest_path = repo / str(pointer_data.get("manifest", ""))
    if not manifest_path.is_file():
        return None, None
    return json.loads(manifest_path.read_text(encoding="utf-8")), manifest_path.parent


def git_root(path: Path) -> Path:
    """Return the Git repository root containing *path*."""
    resolved = path.expanduser().resolve()
    result = run_git(resolved, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def record_postinstall_snapshot(repo: Path) -> None:
    """Record the installed side of the restore three-way comparison."""
    repo = git_root(repo)
    manifest, snapshot_dir = _load_snapshot(repo)
    if not manifest or not snapshot_dir:
        return
    changed = False
    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        if rel.as_posix() in {".gitignore", ".gitmodules"}:
            continue
        current = repo / rel
        installed_state = _path_state(current)
        installed_hash = sha256_file(current) if installed_state == "file" else None
        if "installedSha256" not in entry:
            entry["installedSha256"] = installed_hash
            entry["installedState"] = installed_state
            changed = True
    if changed:
        _write_json(snapshot_dir / "manifest.json", manifest)


def dependency_status(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
    """Return binding status for the optional CodeSleuth git dependency."""
    repo = git_root(repo)
    rel = _safe_rel(dependency_path).as_posix()
    staged = run_git(repo, ["ls-files", "--stage", "--", rel], check=False)
    mode = None
    commit = None
    if staged.returncode == 0 and staged.stdout.strip():
        fields = staged.stdout.split()
        if len(fields) >= 2:
            mode, commit = fields[0], fields[1]
    worktree = repo / rel
    return {
        "path": rel,
        "bound": mode == "160000",
        "commit": commit if mode == "160000" else None,
        "worktreePresent": worktree.exists(),
    }


def lifecycle_state(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> str:
    """Classify the repository lifecycle state for install/update/uninstall."""
    repo = git_root(repo)
    runtime = runtime_metadata_present(repo)
    bound = dependency_status(repo, dependency_path)["bound"]
    if runtime and bound:
        return "bound-active"
    if bound:
        return "dependency-only"
    if runtime:
        return "unbound-active"
    return "unbound-inactive"


def _guard_submodule_head(repo: Path, status: dict[str, Any], *, requested_commit: str | None = None) -> None:
    worktree = repo / status["path"]
    if not worktree.exists():
        return
    dirty = run_git(worktree, ["status", "--porcelain"], check=False)
    if dirty.returncode != 0:
        raise RuntimeError(f"cannot inspect CodeSleuth submodule: {status['path']}")
    if dirty.stdout.strip():
        raise RuntimeError(f"refusing to discard dirty CodeSleuth submodule: {status['path']}")
    head = run_git(worktree, ["rev-parse", "HEAD"], check=False)
    if head.returncode != 0:
        raise RuntimeError(f"cannot resolve CodeSleuth submodule HEAD: {status['path']}")
    actual = head.stdout.strip()
    recorded = status.get("commit")
    if actual != recorded and actual != requested_commit:
        raise RuntimeError(
            f"refusing to discard local CodeSleuth commit {actual}; "
            f"superproject records {recorded}. Preserve/push the commit or intentionally advance the pin first"
        )


def _source_from_checkout(source_root: Path | None, metadata: dict[str, Any] | None) -> tuple[str, str]:
    remote = None
    commit = None
    if source_root is not None and source_root.exists():
        remote_result = run_git(source_root, ["remote", "get-url", "origin"], check=False)
        if remote_result.returncode == 0:
            remote = remote_result.stdout.strip() or None
        commit_result = run_git(source_root, ["rev-parse", "HEAD"], check=False)
        if commit_result.returncode == 0:
            commit = commit_result.stdout.strip() or None
    if metadata:
        remote = remote or metadata.get("remote")
        commit = commit or metadata.get("commit")
    if not remote or not commit:
        raise RuntimeError("CodeSleuth dependency binding requires an exact source remote and commit")
    return str(remote), str(commit)


def is_self_target(repo: Path, source_root: Path | None = None, source_metadata: dict[str, Any] | None = None) -> bool:
    """Return True when the source checkout and target repo resolve to the same Git root."""
    target_root = git_root(repo)
    candidate_roots: list[Path] = []
    if source_root is not None and source_root.exists():
        try:
            candidate_roots.append(git_root(source_root))
        except subprocess.CalledProcessError:
            pass
    source_subdir = ""
    if source_metadata:
        source_subdir = str(source_metadata.get("subdir") or "")
    if not candidate_roots and source_metadata:
        source_commit = source_metadata.get("commit")
        source_remote = source_metadata.get("remote")
        try:
            target_commit = run_git(target_root, ["rev-parse", "HEAD"], check=False)
        except subprocess.CalledProcessError:
            target_commit = None
        try:
            target_remote = run_git(target_root, ["remote", "get-url", "origin"], check=False)
        except subprocess.CalledProcessError:
            target_remote = None
        if (
            source_commit
            and source_remote
            and target_commit
            and target_commit.returncode == 0
            and target_commit.stdout.strip() == source_commit
            and target_remote
            and target_remote.returncode == 0
            and target_remote.stdout.strip() == source_remote
        ):
            candidate_roots.append(target_root)
    for candidate in candidate_roots:
        if candidate == target_root and source_subdir in {"", "."}:
            return True
    return False


def bind_dependency(
    repo: Path,
    *,
    source_root: Path | None = None,
    source_metadata: dict[str, Any] | None = None,
    dependency_path: str = DEFAULT_DEPENDENCY_PATH,
) -> dict[str, Any]:
    """Bind CodeSleuth as a pinned Git submodule dependency."""
    repo = repo.resolve()
    rel = _safe_rel(dependency_path).as_posix()
    current = dependency_status(repo, rel)
    remote, commit = _source_from_checkout(source_root, source_metadata)
    if is_self_target(repo, source_root=source_root, source_metadata=source_metadata):
        raise RuntimeError(
            "cannot bind CodeSleuth as a dependency of its own source repository; "
            "self-install is supported, recursive self-submodule binding is not"
        )

    if current["bound"]:
        worktree = repo / rel
        if worktree.exists():
            _guard_submodule_head(repo, current, requested_commit=commit)
            run_git(worktree, ["fetch", "origin", commit], check=False)
            run_git(worktree, ["checkout", "--detach", commit])
            run_git(repo, ["add", "--", rel])
        return {**dependency_status(repo, rel), "remote": remote, "requestedCommit": commit}

    ignored = run_git(repo, ["check-ignore", "-q", "--", rel], check=False)
    if ignored.returncode == 0:
        raise RuntimeError(
            f"dependency path {rel} is ignored by the target repository; CodeSleuth will not override project ignore policy"
        )
    target = repo / rel
    if target.exists() and any(target.iterdir() if target.is_dir() else [target]):
        raise RuntimeError(f"dependency path already exists and is not a CodeSleuth gitlink: {rel}")
    target.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-C",
            str(repo),
            "submodule",
            "add",
            "--name",
            "codesleuth",
            "--",
            remote,
            rel,
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    worktree = repo / rel
    run_git(worktree, ["fetch", "origin", commit], check=False)
    run_git(worktree, ["checkout", "--detach", commit])
    run_git(repo, ["add", ".gitmodules", rel])
    return {**dependency_status(repo, rel), "remote": remote, "requestedCommit": commit}


def archive_traces(repo: Path) -> Path:
    """Archive managed CodeSleuth traces under ``.codesleuth/archive``."""
    stamp = utc_stamp()
    archive = repo / LOCAL_ROOT / "archive" / stamp
    meta_name, legacy_meta_name = state_filenames("metadata")
    settings_name, legacy_settings_name = state_filenames("settings")
    candidates = [
        repo / ".opencode" / meta_name,
        repo / ".opencode" / settings_name,
        repo / ".opencode" / legacy_meta_name,
        repo / ".opencode" / legacy_settings_name,
        repo / ".opencode" / "opencode.json",
        repo / ".opencode" / "profiles",
        repo / ".opencode" / "state" / "reviews",
        repo / ".opencode" / "state" / "tui",
        repo / LOCAL_ROOT / "reports",
    ]
    copied: list[str] = []
    for source in candidates:
        if not source.exists():
            continue
        rel = source.relative_to(repo)
        target = archive / "files" / rel
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
            copied.extend(p.relative_to(repo).as_posix() for p in source.rglob("*") if p.is_file())
        else:
            _copy_file(source, target)
            copied.append(rel.as_posix())
    _write_json(
        archive / "manifest.json",
        {
            "schemaVersion": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "files": sorted(set(copied)),
            "warning": "Archived review evidence may contain development credentials or other secrets. Inspect before sharing or force-adding to Git.",
        },
    )
    return archive


def _remove_codesleuth_files(
    repo: Path,
    metadata: dict[str, Any] | None,
    snapshot_paths: set[str],
    preserve_paths: set[str],
) -> None:
    target = repo / ".opencode"
    managed = (metadata or {}).get("managedFiles", {})
    remove_rel = set(managed)
    meta_name, legacy_meta_name = state_filenames("metadata")
    settings_name, legacy_settings_name = state_filenames("settings")
    remove_rel.update({meta_name, settings_name, legacy_meta_name, legacy_settings_name, "profiles/detected.json"})
    if ".opencode/opencode.json" not in snapshot_paths:
        remove_rel.add("opencode.json")
    for rel in sorted(remove_rel, reverse=True):
        full_rel = (Path(".opencode") / rel).as_posix()
        if full_rel in preserve_paths:
            continue
        path = target / rel
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    if target.exists():
        for directory in sorted((p for p in target.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass


def restore_preinstall_snapshot(repo: Path) -> dict[str, Any]:
    """Restore pre-install OpenCode files using the three-way comparison."""
    repo = git_root(repo)
    meta_path = resolve_state_file(repo / ".opencode", "metadata", fail_on_conflict=False)
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path is not None else None
    manifest, snapshot_dir = _load_snapshot(repo)
    snapshot_paths = {entry["path"] for entry in (manifest or {}).get("files", [])}

    if not manifest or not snapshot_dir:
        _remove_codesleuth_files(repo, metadata, snapshot_paths, set())
        return {"restored": False, "reason": "no pre-install snapshot; CodeSleuth-owned files removed without guessing prior config"}

    conflicts: list[dict[str, Any]] = []
    preserve_paths: set[str] = set()
    stamp = utc_stamp()
    conflict_root = repo / LOCAL_ROOT / "restore-conflicts" / stamp
    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        rel_key = rel.as_posix()
        if rel_key in {".gitignore", ".gitmodules"}:
            continue
        current = repo / rel
        current_state = _path_state(current)
        baseline_hash = entry["sha256"]
        installed_hash = entry.get("installedSha256")
        installed_state = entry.get("installedState", "file" if installed_hash is not None else "absent")
        current_hash = sha256_file(current) if current_state == "file" else None
        if current_hash == baseline_hash or (current_state == installed_state and current_hash == installed_hash):
            continue
        preserve_paths.add(rel_key)
        baseline_copy = conflict_root / "baseline" / rel
        _copy_file(snapshot_dir / "files" / rel, baseline_copy)
        current_copy = conflict_root / "current" / rel if current_state == "file" else None
        if current_copy is not None:
            _copy_file(current, current_copy)
        conflicts.append(
            {
                "path": rel_key,
                "reason": "pre-install file changed after CodeSleuth installation",
                "baseline": baseline_copy.relative_to(repo).as_posix(),
                "current": current_copy.relative_to(repo).as_posix() if current_copy else None,
                "currentState": current_state,
                "currentLinkTarget": str(current.readlink()) if current_state == "symlink" else None,
                "worktreePreserved": True,
            }
        )
    for managed_rel, installed_hash in (metadata or {}).get("managedFiles", {}).items():
        rel = Path(".opencode") / managed_rel
        rel_key = rel.as_posix()
        current = repo / rel
        if rel_key in snapshot_paths or not current.is_file() or sha256_file(current) == installed_hash:
            continue
        preserve_paths.add(rel_key)
        current_copy = conflict_root / "current" / rel
        _copy_file(current, current_copy)
        conflicts.append(
            {
                "path": rel_key,
                "reason": "CodeSleuth-managed file was locally modified after installation",
                "baseline": None,
                "current": current_copy.relative_to(repo).as_posix(),
                "worktreePreserved": True,
            }
        )
    if conflicts:
        _write_json(
            conflict_root / "manifest.json",
            {
                "schemaVersion": 1,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "policy": "divergent current files remain in the worktree; baseline and current copies are retained",
                "conflicts": conflicts,
            },
        )

    _remove_codesleuth_files(repo, metadata, snapshot_paths, preserve_paths)

    for entry in manifest.get("files", []):
        rel = Path(entry["path"])
        if rel.as_posix() in {".gitignore", ".gitmodules"}:
            # Root Git control files are backed up for recovery, but uninstall removes
            # only CodeSleuth-owned blocks/sections to preserve later user changes.
            continue
        if rel.as_posix() in preserve_paths:
            continue
        source = snapshot_dir / "files" / rel
        if source.is_file():
            _remove_path(repo / rel)
            _copy_file(source, repo / rel)
    return {
        "restored": True,
        "manifest": (snapshot_dir / "manifest.json").relative_to(repo).as_posix(),
        "conflicts": conflicts,
        "conflictManifest": (conflict_root / "manifest.json").relative_to(repo).as_posix() if conflicts else None,
    }


def remove_dependency(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
    """Remove the bound CodeSleuth submodule/gitlink when safe."""
    repo = git_root(repo)
    rel = _safe_rel(dependency_path).as_posix()
    status = dependency_status(repo, rel)
    if not status["bound"]:
        return {**status, "removed": False}
    worktree = repo / rel
    if worktree.exists():
        _guard_submodule_head(repo, status)
    run_git(repo, ["submodule", "deinit", "-f", "--", rel], check=False)
    run_git(repo, ["rm", "-f", "--", rel])
    return {"path": rel, "bound": False, "removed": True}


def uninstall_project(
    repo: Path,
    *,
    preserve_traces: bool = True,
    remove_bound_dependency: bool = True,
    dependency_path: str = DEFAULT_DEPENDENCY_PATH,
    source_root: Path | None = None,
) -> dict[str, Any]:
    """Uninstall CodeSleuth from *repo* (runtime and optional dependency)."""
    repo = git_root(repo)
    archive = archive_traces(repo) if preserve_traces else None
    skip_maintainer = is_self_target(repo, source_root=source_root)
    if not skip_maintainer:
        meta_path = repo / ".opencode" / "review-pack.json"
        if meta_path.is_file():
            try:
                skip_maintainer = bool(json.loads(meta_path.read_text(encoding="utf-8")).get("selfInstall"))
            except json.JSONDecodeError:
                skip_maintainer = False
    try:
        from .agents_policy import remove_agents_rules
    except ImportError:
        pass
    else:
        if not skip_maintainer:
            remove_agents_rules(repo)
    remove_agents_reports_pointer(repo)
    restored = restore_preinstall_snapshot(repo)
    dependency = (
        remove_dependency(repo, dependency_path)
        if remove_bound_dependency
        else {**dependency_status(repo, dependency_path), "removed": False}
    )
    if preserve_traces:
        ensure_local_gitignore(repo, preserve_archive_only=True)
    else:
        conflict_dir = repo / LOCAL_ROOT / "restore-conflicts"
        root = repo / LOCAL_ROOT
        if root.exists():
            for child in root.iterdir():
                if child == conflict_dir:
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        if restored.get("conflicts"):
            ensure_local_gitignore(repo, preserve_archive_only=True)
        else:
            remove_local_gitignore_block(repo)
            shutil.rmtree(root, ignore_errors=True)
    return {
        "preserveTraces": preserve_traces,
        "archive": archive.relative_to(repo).as_posix() if archive else None,
        "restore": restored,
        "dependency": dependency,
    }


def _metadata_source(repo: Path) -> dict[str, Any] | None:
    meta = resolve_state_file(repo / ".opencode", "metadata", fail_on_conflict=False)
    if meta is None:
        return None
    return json.loads(meta.read_text(encoding="utf-8")).get("source")


def main() -> int:
    """CLI entrypoint for project lifecycle operations."""
    parser = argparse.ArgumentParser(
        description="Manage CodeSleuth as a project-local dependency and reversible installation.",
        epilog=(
            "Self-install: install CodeSleuth into its own source checkout with "
            "`install.py . --self-install` (never with --bind-dependency). "
            "Host registry: --list shows reachable repositories recorded on this machine "
            "(name, CodeSleuth source, version). Missing paths are dropped on refresh. "
            "Use --forget PATH to remove a still-reachable catalog entry."
        ),
    )
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--dependency-path", default=DEFAULT_DEPENDENCY_PATH)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--list", action="store_true", help="list host-tracked CodeSleuth repositories")
    actions.add_argument("--forget", action="store_true", help="remove a path from the host-tracked repository catalog")
    actions.add_argument("--bind", action="store_true", help="pin CodeSleuth as a Git submodule")
    actions.add_argument("--unbind", action="store_true", help="remove the CodeSleuth dependency while keeping the installed runtime")
    actions.add_argument("--uninstall", action="store_true", help="restore pre-CodeSleuth config and remove CodeSleuth")
    parser.add_argument("--purge-traces", action="store_true", help="delete CodeSleuth reports/settings/backups instead of archiving them")
    parser.add_argument("--keep-dependency", action="store_true", help="uninstall the runtime but leave the CodeSleuth gitlink")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(list_tracked_repositories(refresh=True), indent=2))
        return 0
    if args.forget:
        target = Path(args.repo).expanduser()
        # --forget uses registry normalization and does not require lifecycle probe
        removed = forget_tracked_repository(target)
        # normalize for output consistency
        try:
            canon = str(target.resolve())
        except Exception:
            canon = str(target)
        print(json.dumps({"forgotten": removed, "path": canon}, indent=2))
        return 0 if removed else 1
    repo = git_root(Path(args.repo))
    if args.bind:
        result = bind_dependency(repo, source_metadata=_metadata_source(repo), dependency_path=args.dependency_path)
        record_tracked_repository(repo)
    elif args.unbind:
        result = remove_dependency(repo, args.dependency_path)
        record_tracked_repository(repo)
    else:
        result = uninstall_project(
            repo,
            preserve_traces=not args.purge_traces,
            remove_bound_dependency=not args.keep_dependency,
            dependency_path=args.dependency_path,
        )
        record_tracked_repository(repo)
    print(json.dumps(result, indent=2))
    return 0


__all__ = [
    "AGENTS_BEGIN",
    "AGENTS_END",
    "AGENTS_POINTER",
    "DEFAULT_DEPENDENCY_PATH",
    "IGNORE_BEGIN",
    "IGNORE_END",
    "IGNORE_LINES",
    "LOCAL_ROOT",
    "REPORTS_DIR",
    "REPORTS_INDEX",
    "REPORTS_INDEX_HEADER",
    "REPORTS_INDEX_PLACEHOLDER",
    "REPORTS_README",
    "archive_traces",
    "bind_dependency",
    "create_preinstall_snapshot",
    "dependency_status",
    "ensure_agents_reports_pointer",
    "ensure_local_gitignore",
    "ensure_reports_workspace",
    "forget_tracked_repository",
    "format_tracked_label",
    "git_root",
    "host_state_dir",
    "is_self_target",
    "lifecycle_state",
    "list_tracked_repositories",
    "main",
    "record_postinstall_snapshot",
    "record_tracked_repository",
    "registry_path",
    "remove_agents_reports_pointer",
    "remove_dependency",
    "remove_local_gitignore_block",
    "report_timestamp_key",
    "restore_preinstall_snapshot",
    "run_git",
    "sha256_file",
    "short_remote",
    "source_label",
    "uninstall_project",
    "update_reports_index",
    "utc_stamp",
    "validate_agents_pointer",
]
