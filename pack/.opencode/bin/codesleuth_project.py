#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCAL_ROOT = ".codesleuth"
DEFAULT_DEPENDENCY_PATH = "tools/codesleuth"
IGNORE_BEGIN = "# BEGIN CodeSleuth local-only data"
IGNORE_END = "# END CodeSleuth local-only data"
IGNORE_LINES = (
    ".codesleuth/",
    ".opencode/state/",
    ".opencode/cache/",
    ".opencode/logs/",
    ".opencode/sessions/",
    ".opencode/snapshots/",
    ".opencode/node_modules/",
    ".opencode/**/__pycache__/",
    ".opencode/**/*.pyc",
)
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
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
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


def ensure_local_gitignore(repo: Path, *, preserve_archive_only: bool = False) -> Path:
    path = repo / ".gitignore"
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    before, marker, tail = original.partition(IGNORE_BEGIN)
    if marker:
        _, end_marker, after = tail.partition(IGNORE_END)
        if not end_marker:
            raise RuntimeError("malformed CodeSleuth block in .gitignore")
        original = before.rstrip("\n") + ("\n" if before else "") + after.lstrip("\n")
    lines = [".codesleuth/"] if preserve_archive_only else list(IGNORE_LINES)
    block = "\n".join([IGNORE_BEGIN, *lines, IGNORE_END])
    body = original.rstrip("\n")
    new_content = f"{body}\n\n{block}\n" if body else f"{block}\n"
    path.write_text(new_content, encoding="utf-8")
    return path


def remove_local_gitignore_block(repo: Path) -> None:
    path = repo / ".gitignore"
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8")
    before, marker, tail = original.partition(IGNORE_BEGIN)
    if not marker:
        return
    _, end_marker, after = tail.partition(IGNORE_END)
    if not end_marker:
        raise RuntimeError("malformed CodeSleuth block in .gitignore")
    body = (before.rstrip("\n") + "\n" + after.lstrip("\n")).strip("\n")
    if body:
        path.write_text(body + "\n", encoding="utf-8")
    else:
        path.unlink()


def create_preinstall_snapshot(repo: Path) -> dict[str, Any]:
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
        "baselineKind": "pre-0.3-upgrade" if (repo / ".opencode" / "review-pack.json").is_file() else "pre-install",
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
        installed_hash = sha256_file(current) if current.is_file() else None
        if "installedSha256" not in entry:
            entry["installedSha256"] = installed_hash
            changed = True
    if changed:
        _write_json(snapshot_dir / "manifest.json", manifest)


def dependency_status(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
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
    repo = git_root(repo)
    runtime = (repo / ".opencode" / "review-pack.json").is_file()
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


def bind_dependency(
    repo: Path,
    *,
    source_root: Path | None = None,
    source_metadata: dict[str, Any] | None = None,
    dependency_path: str = DEFAULT_DEPENDENCY_PATH,
) -> dict[str, Any]:
    repo = repo.resolve()
    rel = _safe_rel(dependency_path).as_posix()
    current = dependency_status(repo, rel)
    remote, commit = _source_from_checkout(source_root, source_metadata)

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
    stamp = utc_stamp()
    archive = repo / LOCAL_ROOT / "archive" / stamp
    candidates = [
        repo / ".opencode" / "review-pack.json",
        repo / ".opencode" / "review-pack-user.json",
        repo / ".opencode" / "opencode.json",
        repo / ".opencode" / "profiles",
        repo / ".opencode" / "state" / "reviews",
        repo / ".opencode" / "state" / "tui",
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
    remove_rel.update({"review-pack.json", "review-pack-user.json", "profiles/detected.json"})
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
    repo = git_root(repo)
    meta_path = repo / ".opencode" / "review-pack.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else None
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
        if not current.is_file():
            continue
        current_hash = sha256_file(current)
        baseline_hash = entry["sha256"]
        installed_hash = entry.get("installedSha256")
        if current_hash == baseline_hash or (installed_hash is not None and current_hash == installed_hash):
            continue
        preserve_paths.add(rel_key)
        baseline_copy = conflict_root / "baseline" / rel
        current_copy = conflict_root / "current" / rel
        _copy_file(snapshot_dir / "files" / rel, baseline_copy)
        _copy_file(current, current_copy)
        conflicts.append(
            {
                "path": rel_key,
                "reason": "pre-install file changed after CodeSleuth installation",
                "baseline": baseline_copy.relative_to(repo).as_posix(),
                "current": current_copy.relative_to(repo).as_posix(),
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
            _copy_file(source, repo / rel)
    return {
        "restored": True,
        "manifest": (snapshot_dir / "manifest.json").relative_to(repo).as_posix(),
        "conflicts": conflicts,
        "conflictManifest": (conflict_root / "manifest.json").relative_to(repo).as_posix() if conflicts else None,
    }


def remove_dependency(repo: Path, dependency_path: str = DEFAULT_DEPENDENCY_PATH) -> dict[str, Any]:
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
) -> dict[str, Any]:
    repo = git_root(repo)
    archive = archive_traces(repo) if preserve_traces else None
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
    meta = repo / ".opencode" / "review-pack.json"
    if not meta.is_file():
        return None
    return json.loads(meta.read_text(encoding="utf-8")).get("source")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage CodeSleuth as a project-local dependency and reversible installation.")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--dependency-path", default=DEFAULT_DEPENDENCY_PATH)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--bind", action="store_true", help="pin CodeSleuth as a Git submodule")
    actions.add_argument("--unbind", action="store_true", help="remove the CodeSleuth dependency while keeping the installed runtime")
    actions.add_argument("--uninstall", action="store_true", help="restore pre-CodeSleuth config and remove CodeSleuth")
    parser.add_argument("--purge-traces", action="store_true", help="delete CodeSleuth reports/settings/backups instead of archiving them")
    parser.add_argument("--keep-dependency", action="store_true", help="uninstall the runtime but leave the CodeSleuth gitlink")
    args = parser.parse_args()
    repo = git_root(Path(args.repo))
    if args.bind:
        result = bind_dependency(repo, source_metadata=_metadata_source(repo), dependency_path=args.dependency_path)
    elif args.unbind:
        result = remove_dependency(repo, args.dependency_path)
    else:
        result = uninstall_project(
            repo,
            preserve_traces=not args.purge_traces,
            remove_bound_dependency=not args.keep_dependency,
            dependency_path=args.dependency_path,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
