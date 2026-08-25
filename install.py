#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK = ROOT / "pack" / ".opencode"
sys.path.insert(0, str(PACK / "bin"))
from codesleuth_naming import load_naming  # noqa: E402
from codesleuth_version import source_version  # noqa: E402
import codesleuth_project as project_lifecycle  # noqa: E402
import codesleuth_tui_core as tui_core  # noqa: E402

NAMING = load_naming(PACK / "codesleuth-naming.json")
CANONICAL = NAMING["canonical"]
LEGACY = NAMING["legacy"]
META_NAME = CANONICAL["state"]["metadata"]
SETTINGS_NAME = CANONICAL["state"]["settings"]
LEGACY_META_NAME = LEGACY["state"]["metadata"]
LEGACY_SETTINGS_NAME = LEGACY["state"]["settings"]

VERSION = source_version(ROOT)


def run_git(args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


MIN_GIT_VERSION = (2, 35, 0)


def parse_git_version(raw: str) -> tuple[int, int, int]:
    """Parse ``git --version`` output into an (major, minor, patch) tuple."""
    match = re.search(r"git version\s+(\d+)\.(\d+)\.(\d+)", raw)
    if not match:
        raise ValueError(f"unrecognized git version: {raw!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def require_git_version() -> tuple[int, int, int]:
    """Require Git >= MIN_GIT_VERSION; return the parsed version tuple."""
    try:
        proc = subprocess.run(
            ["git", "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SystemExit(f"git --version failed: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
        raise SystemExit(f"git --version failed: {detail}")
    raw = (proc.stdout or proc.stderr or "").strip()
    try:
        version = parse_git_version(raw)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if version < MIN_GIT_VERSION:
        raise SystemExit(
            f"CodeSleuth requires Git {MIN_GIT_VERSION[0]}.{MIN_GIT_VERSION[1]}.{MIN_GIT_VERSION[2]} "
            f"or newer (found {version[0]}.{version[1]}.{version[2]})"
        )
    return version


def git_files(repo: Path):
    proc = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, check=True)
    return [x for x in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if x]


def detect(files):
    names = set(files)
    profiles = ["generic"]
    if "Cargo.toml" in names or any(x.endswith(".rs") for x in files):
        profiles.append("rust")
    if any(x in names for x in ("pyproject.toml", "requirements.txt", "setup.py")) or any(x.endswith(".py") for x in files):
        profiles.append("python")
    if "package.json" in names:
        profiles.append("node")
    if any(Path(x).name.startswith("tsconfig") and x.endswith(".json") for x in files) or any(x.endswith((".ts", ".tsx")) for x in files):
        profiles.append("typescript")
    return profiles


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return sha256_file(dst)


def merge_missing(dst, src, prefix=""):
    for key, value in src.items():
        here = f"{prefix}.{key}" if prefix else key
        if key not in dst:
            dst[key] = value
        elif isinstance(dst[key], dict) and isinstance(value, dict):
            merge_missing(dst[key], value, here)
        elif dst[key] != value:
            print(f"preserve existing config conflict: {here}", file=sys.stderr)
    return dst


_MISSING = object()


def three_way_defaults(current, old, new, prefix=""):
    if not isinstance(current, dict) or not isinstance(old, dict) or not isinstance(new, dict):
        return new if current == old else current
    out = dict(current)
    for key in set(old) | set(new):
        here = f"{prefix}.{key}" if prefix else key
        cur = out.get(key, _MISSING)
        before = old.get(key, _MISSING)
        after = new.get(key, _MISSING)
        if after is _MISSING:
            if cur is not _MISSING and before is not _MISSING and cur == before:
                del out[key]
                print(f"removed retired pack default: {here}")
            continue
        if cur is _MISSING:
            out[key] = after
            print(f"added pack default: {here}")
            continue
        if before is _MISSING:
            if cur != after:
                print(f"preserve existing config value: {here}", file=sys.stderr)
            continue
        if isinstance(cur, dict) and isinstance(before, dict) and isinstance(after, dict):
            out[key] = three_way_defaults(cur, before, after, here)
        elif cur == before:
            out[key] = after
            if before != after:
                print(f"updated pack default: {here}")
        elif cur != after:
            print(f"preserve user config override: {here}", file=sys.stderr)
    return out


def source_metadata(args):
    remote, ref, subdir, commit = args.source_remote, args.source_ref, args.source_subdir, args.source_commit
    try:
        top = Path(run_git(["rev-parse", "--show-toplevel"], cwd=ROOT).stdout.strip()).resolve()
        if remote is None:
            proc = run_git(["remote", "get-url", "origin"], cwd=top, check=False)
            if proc.returncode == 0:
                remote = proc.stdout.strip() or None
        if ref is None:
            proc = run_git(["branch", "--show-current"], cwd=top, check=False)
            if proc.returncode == 0:
                ref = proc.stdout.strip() or None
        # Detached HEAD deliberately records no floating branch. Exact commit is authority.
        if subdir is None:
            subdir = "" if ROOT == top else ROOT.relative_to(top).as_posix()
        if commit is None:
            proc = run_git(["rev-parse", "HEAD"], cwd=top, check=False)
            if proc.returncode == 0:
                commit = proc.stdout.strip() or None
    except Exception:
        pass
    return {"remote": remote, "ref": ref, "subdir": subdir or "", "commit": commit}


def conflict_path(target: Path, stamp: str, rel: Path):
    return target / "state" / "update-conflicts" / stamp / Path(str(rel) + ".incoming")


def legacy_backup_path(target: Path, stamp: str, rel: Path):
    return target / "state" / "installer-backups" / "legacy-adoption" / stamp / rel


def install_files(target: Path, old_meta, update: bool, force: bool, adopt_existing: bool):
    old_files = (old_meta or {}).get("managedFiles", {})
    new_managed, conflicts, seen = {}, [], set()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for src in sorted(PACK.rglob("*")):
        if not src.is_file() or src.name == "opencode.json" or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(PACK)
        rel_key = rel.as_posix()
        seen.add(rel_key)
        dst = target / rel
        incoming_hash = sha256_file(src)
        if not dst.exists():
            new_managed[rel_key] = copy_file(src, dst)
            print(f"installed: {rel_key}")
            continue
        if adopt_existing and not update:
            backup = legacy_backup_path(target, stamp, rel)
            copy_file(dst, backup)
            new_managed[rel_key] = copy_file(src, dst)
            print(f"adopted legacy pack file with backup: {rel_key}")
            continue
        if force:
            new_managed[rel_key] = copy_file(src, dst)
            print(f"forced: {rel_key}")
            continue
        if not update:
            if sha256_file(dst) == incoming_hash:
                new_managed[rel_key] = incoming_hash
                print(f"adopt existing identical pack file: {rel_key}")
            else:
                print(f"preserve existing unmanaged file: {rel_key}")
            continue
        old_hash = old_files.get(rel_key)
        current_hash = sha256_file(dst)
        if old_hash and current_hash == old_hash:
            new_managed[rel_key] = copy_file(src, dst)
            print(f"updated: {rel_key}" if current_hash != incoming_hash else f"unchanged: {rel_key}")
        elif old_hash and current_hash == incoming_hash:
            new_managed[rel_key] = current_hash
            print(f"already current: {rel_key}")
        else:
            incoming = conflict_path(target, stamp, rel)
            copy_file(src, incoming)
            conflicts.append({
                "path": rel_key,
                "reason": "locally modified managed file" if old_hash else "pre-existing unmanaged file",
                "incoming": incoming.relative_to(target).as_posix(),
            })
            if old_hash:
                new_managed[rel_key] = old_hash
            print(f"CONFLICT preserve local file: {rel_key}", file=sys.stderr)
    if update:
        for rel_key, old_hash in old_files.items():
            if rel_key in seen:
                continue
            dst = target / rel_key
            if not dst.exists():
                continue
            if sha256_file(dst) == old_hash:
                dst.unlink()
                print(f"removed retired pack file: {rel_key}")
            else:
                conflicts.append({"path": rel_key, "reason": "retired pack file was locally modified", "incoming": None})
                new_managed[rel_key] = old_hash
                print(f"CONFLICT preserve retired modified file: {rel_key}", file=sys.stderr)
    return new_managed, conflicts


def update_config(target: Path, old_meta, update: bool):
    base = json.loads((PACK / "opencode.json").read_text(encoding="utf-8"))
    cfg_path = target / "opencode.json"
    backup = target / "state" / "installer-backups"
    backup.mkdir(parents=True, exist_ok=True)
    if cfg_path.exists():
        shutil.copy2(cfg_path, backup / "opencode.json.before-pack")
        current = json.loads(cfg_path.read_text(encoding="utf-8"))
        if update and old_meta and isinstance(old_meta.get("baseConfig"), dict):
            cfg = three_way_defaults(current, old_meta["baseConfig"], base)
        else:
            cfg = merge_missing(current, base)
    else:
        cfg = base
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return base


def resolve_settings(args, repo: Path, profiles: list[str]):
    target = repo / ".opencode"
    if args.settings_file:
        return tui_core.validate_settings(json.loads(Path(args.settings_file).read_text(encoding="utf-8")))
    existing_settings = target / SETTINGS_NAME
    if existing_settings.is_file():
        return tui_core.validate_settings(json.loads(existing_settings.read_text(encoding="utf-8")))
    existing_config = target / "opencode.json"
    if existing_config.is_file():
        try:
            cfg = json.loads(existing_config.read_text(encoding="utf-8"))
            settings = tui_core.settings_from_config(cfg, profiles)
            settings["profiles"] = profiles
            settings["profilesMode"] = "manual" if args.profile else "auto"
            return tui_core.validate_settings(settings)
        except Exception:
            pass
    settings = tui_core.default_settings(profiles)
    settings["profilesMode"] = "manual" if args.profile else "auto"
    return tui_core.validate_settings(settings)


def preserve_merged_config_settings(repo: Path, settings: dict, profiles: list[str]):
    cfg = json.loads((repo / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    compaction = cfg.get("compaction")
    if isinstance(compaction, dict) and isinstance(compaction.get("reserved"), int):
        settings["runtime"]["compactionReserved"] = compaction["reserved"]
    settings["profiles"] = profiles
    settings = tui_core.validate_settings(settings)
    tui_core.save_settings(repo, settings)
    detected = repo / ".opencode" / "profiles" / "detected.json"
    detected.parent.mkdir(parents=True, exist_ok=True)
    detected.write_text(json.dumps({
        "profiles": settings["profiles"],
        "detectedFromTrackedFiles": settings.get("profilesMode") == "auto",
        "exaLaunchDefault": "OPENCODE_ENABLE_EXA=1" if settings["runtime"]["exaEnabled"] else "disabled by CodeSleuth project settings",
    }, indent=2) + "\n", encoding="utf-8")



def _atomic_write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _read_state_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid CodeSleuth persistent state at {path}: expected a JSON object")
    return value


def _resolve_named_state(target: Path, canonical_name: str, legacy_name: str) -> tuple[dict | None, bool]:
    canonical = target / canonical_name
    legacy = target / legacy_name
    canonical_exists = canonical.is_file()
    legacy_exists = legacy.is_file()
    if not canonical_exists and not legacy_exists:
        return None, False
    canonical_value = _read_state_json(canonical) if canonical_exists else None
    legacy_value = _read_state_json(legacy) if legacy_exists else None
    if canonical_exists and legacy_exists:
        if canonical_value != legacy_value:
            raise RuntimeError(
                f"conflicting CodeSleuth persistent state: {canonical} and {legacy} differ; refusing to guess authority"
            )
        legacy.unlink()
        return canonical_value, True
    if canonical_exists:
        return canonical_value, False
    assert legacy_value is not None
    _atomic_write_json(canonical, legacy_value)
    legacy.unlink()
    return legacy_value, True


def _materialize_legacy_update_bridges(target: Path) -> None:
    bin_dir = target / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bridges = set(NAMING["migration"]["bridgeEntrypoints"])
    legacy_env = LEGACY["environment"]
    canonical_env = CANONICAL["environment"]
    legacy_verify = LEGACY["entrypoints"]["verify"]
    legacy_bootstrap = LEGACY["python"]["tuiBootstrap"]
    if legacy_verify in bridges:
        verify = target / legacy_verify
        verify.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "here = Path(__file__).resolve().parent\n"
            f"os.execv(sys.executable, [sys.executable, str(here / {CANONICAL['entrypoints']['verify'].split('/')[-1]!r}), *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        verify.chmod(0o755)
    if legacy_bootstrap in bridges:
        bootstrap = target / legacy_bootstrap
        bootstrap.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            f"old_target = {legacy_env['targetRoot']!r}\n"
            f"new_target = {canonical_env['targetRoot']!r}\n"
            f"old_distribution = {legacy_env['distributionRoot']!r}\n"
            f"new_distribution = {canonical_env['distributionRoot']!r}\n"
            "if old_target in os.environ and new_target not in os.environ:\n    os.environ[new_target] = os.environ[old_target]\n"
            "if old_distribution in os.environ and new_distribution not in os.environ:\n    os.environ[new_distribution] = os.environ[old_distribution]\n"
            "here = Path(__file__).resolve().parent\n"
            f"os.execv(sys.executable, [sys.executable, str(here / {CANONICAL['python']['tuiBootstrap'].split('/')[-1]!r}), *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        bootstrap.chmod(0o755)


def parse_args():
    parser = argparse.ArgumentParser(description="Install, update, bind, or uninstall CodeSleuth for a Git repository.")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--profile", action="append", choices=["generic", "rust", "python", "node", "typescript"])
    parser.add_argument("--settings-file", help="validated CodeSleuth project-settings payload, normally produced by the TUI")
    parser.add_argument("--force-codesleuth-files", dest="force_managed_files", action="store_true", help="overwrite CodeSleuth-owned files, including locally modified ones")
    parser.add_argument(LEGACY["cliOptions"]["forceManagedFiles"], dest="force_managed_files", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--update", action="store_true", help="update an existing versioned installation")
    parser.add_argument("--adopt-existing-codesleuth", dest="adopt_existing", action="store_true", help="adopt an older unversioned CodeSleuth installation with backups")
    parser.add_argument(LEGACY["cliOptions"]["adoptExisting"], dest="adopt_existing", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--bind-dependency", action="store_true", help="pin this exact CodeSleuth commit as tools/codesleuth Git submodule")
    parser.add_argument("--dependency-path", default=project_lifecycle.DEFAULT_DEPENDENCY_PATH)
    parser.add_argument("--uninstall", action="store_true", help="restore pre-CodeSleuth configuration and remove CodeSleuth runtime")
    parser.add_argument("--purge-traces", action="store_true", help="with --uninstall, delete CodeSleuth reports/settings/backups instead of archiving them")
    parser.add_argument("--keep-dependency", action="store_true", help="with --uninstall, keep the CodeSleuth submodule/gitlink")
    parser.add_argument("--source-remote")
    parser.add_argument("--source-ref")
    parser.add_argument("--source-subdir")
    parser.add_argument("--source-commit")
    return parser.parse_args()


def main():
    args = parse_args()
    repo = project_lifecycle.git_root(Path(args.repo))

    if args.uninstall:
        if args.update or args.adopt_existing or args.bind_dependency:
            raise SystemExit("--uninstall is mutually exclusive with install/update/bind operations")
        result = project_lifecycle.uninstall_project(
            repo,
            preserve_traces=not args.purge_traces,
            remove_bound_dependency=not args.keep_dependency,
            dependency_path=args.dependency_path,
        )
        print(json.dumps(result, indent=2))
        print("CodeSleuth uninstalled. Review staged Git changes before committing.")
        return

    if args.adopt_existing and args.update:
        raise SystemExit("--adopt-existing-codesleuth and --update are mutually exclusive")

    project_lifecycle.create_preinstall_snapshot(repo)
    project_lifecycle.ensure_local_gitignore(repo)

    target = repo / ".opencode"
    target.mkdir(exist_ok=True)
    meta_path = target / META_NAME
    legacy_runtime = (target / LEGACY_META_NAME).is_file() or (target / LEGACY_SETTINGS_NAME).is_file()
    try:
        old_meta, migrated_meta = _resolve_named_state(target, META_NAME, LEGACY_META_NAME)
        _, migrated_settings = _resolve_named_state(target, SETTINGS_NAME, LEGACY_SETTINGS_NAME)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    legacy_runtime = legacy_runtime or migrated_meta or migrated_settings
    if args.update and not old_meta:
        raise SystemExit("cannot --update: .opencode/codesleuth.json is missing; use --adopt-existing-codesleuth for an older unversioned installation")
    if args.adopt_existing and old_meta:
        raise SystemExit("installation is already versioned; use --update")

    profiles = args.profile or detect(git_files(repo))
    if "generic" not in profiles:
        profiles.insert(0, "generic")
    profiles = list(dict.fromkeys(profiles))
    settings = resolve_settings(args, repo, profiles)
    profiles = settings["profiles"]

    managed, conflicts = install_files(target, old_meta, args.update, args.force_managed_files, args.adopt_existing)
    if args.update and legacy_runtime:
        _materialize_legacy_update_bridges(target)
    base_config = update_config(target, old_meta, args.update)
    if args.update and not args.settings_file:
        preserve_merged_config_settings(repo, settings, profiles)
    else:
        tui_core.apply_settings_to_target(repo, settings)

    source = source_metadata(args)
    dependency = (old_meta or {}).get("dependency")
    meta = {
        "schemaVersion": 2,
        "version": VERSION,
        "complete": not conflicts,
        "installedAt": datetime.now(timezone.utc).isoformat(),
        "managedFiles": managed,
        "baseConfig": base_config,
        "source": source,
        "dependency": dependency,
        "preInstallBackup": f"{project_lifecycle.LOCAL_ROOT}/preinstall.json",
        "conflicts": conflicts,
        "adoptedLegacy": bool(args.adopt_existing),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if args.bind_dependency:
        dependency = project_lifecycle.bind_dependency(
            repo,
            source_root=ROOT,
            source_metadata=source,
            dependency_path=args.dependency_path,
        )
        meta["dependency"] = dependency
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    project_lifecycle.record_postinstall_snapshot(repo)
    project_lifecycle.ensure_reports_workspace(repo)
    project_lifecycle.ensure_agents_reports_pointer(repo)

    print("profiles:", ", ".join(profiles))
    print(("updated" if args.update else "installed"), f"CodeSleuth {VERSION} into", repo)
    if args.adopt_existing:
        print("legacy installation adopted; backups are under .opencode/state/installer-backups/legacy-adoption")
    if conflicts:
        print(f"update completed with {len(conflicts)} conflict(s); inspect .opencode/state/update-conflicts", file=sys.stderr)
    if dependency and dependency.get("bound"):
        print(f"dependency: {dependency['path']} @ {dependency.get('commit') or dependency.get('requestedCommit')}")
    print("pre-install backup: .codesleuth/backups/pre-install/")
    print("analytical reports: .codesleuth/reports/ (INDEX.md + markdown; OpenCode build writes them)")
    print("control TUI: .opencode/bin/codesleuth")
    print("verify: python3 .opencode/bin/codesleuth-verify.py .")
    print("uninstall preserving traces: .opencode/bin/codesleuth-project --uninstall .")
    print("SECURITY: review evidence may contain development credentials; local reports/state are gitignored by default.")


if __name__ == "__main__":
    main()
