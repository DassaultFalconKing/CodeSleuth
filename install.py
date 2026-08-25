#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACK = ROOT / "pack" / ".opencode"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
META_NAME = "review-pack.json"
SETTINGS_NAME = "review-pack-user.json"
sys.path.insert(0, str(PACK / "bin"))
import review_pack_tui_core as tui_core  # noqa: E402


def run_git(args, cwd=None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def git_files(repo: Path):
    p = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, check=True)
    return [x for x in p.stdout.decode("utf-8", "surrogateescape").split("\0") if x]


def detect(files):
    names = set(files)
    profiles = ["generic"]
    if "Cargo.toml" in names or any(x.endswith(".rs") for x in files): profiles.append("rust")
    if any(x in names for x in ("pyproject.toml", "requirements.txt", "setup.py")) or any(x.endswith(".py") for x in files): profiles.append("python")
    if "package.json" in names: profiles.append("node")
    if any(Path(x).name.startswith("tsconfig") and x.endswith(".json") for x in files) or any(x.endswith((".ts", ".tsx")) for x in files): profiles.append("typescript")
    return profiles


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return sha256_file(dst)


def merge_missing(dst, src, prefix=""):
    for key, value in src.items():
        here = f"{prefix}.{key}" if prefix else key
        if key not in dst: dst[key] = value
        elif isinstance(dst[key], dict) and isinstance(value, dict): merge_missing(dst[key], value, here)
        elif dst[key] != value: print(f"preserve existing config conflict: {here}", file=sys.stderr)
    return dst


_MISSING = object()


def three_way_defaults(current, old, new, prefix=""):
    if not isinstance(current, dict) or not isinstance(old, dict) or not isinstance(new, dict):
        return new if current == old else current
    out = dict(current)
    for key in set(old) | set(new):
        here = f"{prefix}.{key}" if prefix else key
        cur = out.get(key, _MISSING); before = old.get(key, _MISSING); after = new.get(key, _MISSING)
        if after is _MISSING:
            if cur is not _MISSING and before is not _MISSING and cur == before:
                del out[key]; print(f"removed retired pack default: {here}")
            continue
        if cur is _MISSING:
            out[key] = after; print(f"added pack default: {here}"); continue
        if before is _MISSING:
            if cur != after: print(f"preserve existing config value: {here}", file=sys.stderr)
            continue
        if isinstance(cur, dict) and isinstance(before, dict) and isinstance(after, dict):
            out[key] = three_way_defaults(cur, before, after, here)
        elif cur == before:
            out[key] = after
            if before != after: print(f"updated pack default: {here}")
        elif cur != after: print(f"preserve user config override: {here}", file=sys.stderr)
    return out


def source_metadata(args):
    remote, ref, subdir, commit = args.source_remote, args.source_ref, args.source_subdir, args.source_commit
    try:
        top = Path(run_git(["rev-parse", "--show-toplevel"], cwd=ROOT).stdout.strip()).resolve()
        if remote is None:
            p = run_git(["remote", "get-url", "origin"], cwd=top, check=False)
            if p.returncode == 0: remote = p.stdout.strip() or None
        if ref is None:
            p = run_git(["branch", "--show-current"], cwd=top, check=False)
            if p.returncode == 0: ref = p.stdout.strip() or None
        if ref is None:
            p = run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=top, check=False)
            if p.returncode == 0 and p.stdout.strip().startswith("origin/"):
                ref = p.stdout.strip().split("/", 1)[1]
        if subdir is None: subdir = "" if ROOT == top else ROOT.relative_to(top).as_posix()
        if commit is None:
            p = run_git(["rev-parse", "HEAD"], cwd=top, check=False)
            if p.returncode == 0: commit = p.stdout.strip() or None
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
        if not src.is_file() or src.name == "opencode.json" or "__pycache__" in src.parts: continue
        rel = src.relative_to(PACK); rel_key = rel.as_posix(); seen.add(rel_key)
        dst = target / rel; incoming_hash = sha256_file(src)
        if not dst.exists():
            new_managed[rel_key] = copy_file(src, dst); print(f"installed: {rel_key}"); continue
        if adopt_existing and not update:
            backup = legacy_backup_path(target, stamp, rel); copy_file(dst, backup)
            new_managed[rel_key] = copy_file(src, dst); print(f"adopted legacy pack file with backup: {rel_key}"); continue
        if force:
            new_managed[rel_key] = copy_file(src, dst); print(f"forced: {rel_key}"); continue
        if not update:
            if sha256_file(dst) == incoming_hash:
                new_managed[rel_key] = incoming_hash; print(f"adopt existing identical pack file: {rel_key}")
            else: print(f"preserve existing unmanaged file: {rel_key}")
            continue
        old_hash = old_files.get(rel_key); current_hash = sha256_file(dst)
        if old_hash and current_hash == old_hash:
            new_managed[rel_key] = copy_file(src, dst)
            print(f"updated: {rel_key}" if current_hash != incoming_hash else f"unchanged: {rel_key}")
        elif old_hash and current_hash == incoming_hash:
            new_managed[rel_key] = current_hash; print(f"already current: {rel_key}")
        else:
            incoming = conflict_path(target, stamp, rel); copy_file(src, incoming)
            conflicts.append({"path": rel_key, "reason": "locally modified managed file" if old_hash else "pre-existing unmanaged file", "incoming": incoming.relative_to(target).as_posix()})
            if old_hash: new_managed[rel_key] = old_hash
            print(f"CONFLICT preserve local file: {rel_key}", file=sys.stderr)
    if update:
        for rel_key, old_hash in old_files.items():
            if rel_key in seen: continue
            dst = target / rel_key
            if not dst.exists(): continue
            if sha256_file(dst) == old_hash:
                dst.unlink(); print(f"removed retired pack file: {rel_key}")
            else:
                conflicts.append({"path": rel_key, "reason": "retired pack file was locally modified", "incoming": None})
                new_managed[rel_key] = old_hash; print(f"CONFLICT preserve retired modified file: {rel_key}", file=sys.stderr)
    return new_managed, conflicts


def update_config(target: Path, old_meta, update: bool):
    base = json.loads((PACK / "opencode.json").read_text(encoding="utf-8"))
    cfg_path = target / "opencode.json"; backup = target / "state" / "installer-backups"; backup.mkdir(parents=True, exist_ok=True)
    if cfg_path.exists():
        shutil.copy2(cfg_path, backup / "opencode.json.before-pack")
        current = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg = three_way_defaults(current, old_meta["baseConfig"], base) if update and old_meta and isinstance(old_meta.get("baseConfig"), dict) else merge_missing(current, base)
    else: cfg = base
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
            settings = tui_core.settings_from_config(cfg, profiles); settings["profiles"] = profiles; settings["profilesMode"] = "manual" if args.profile else "auto"
            return tui_core.validate_settings(settings)
        except Exception: pass
    settings = tui_core.default_settings(profiles); settings["profilesMode"] = "manual" if args.profile else "auto"
    return tui_core.validate_settings(settings)


def preserve_merged_config_settings(repo: Path, settings: dict, profiles: list[str]):
    """Persist user metadata after a passive update without rewriting the three-way merged config."""
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
        "exaLaunchDefault": "OPENCODE_ENABLE_EXA=1" if settings["runtime"]["exaEnabled"] else "disabled by review-pack-user.json",
    }, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Install or safely update the OpenCode repository review pack.")
    ap.add_argument("--version", action="version", version=VERSION)
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--profile", action="append", choices=["generic", "rust", "python", "node", "typescript"])
    ap.add_argument("--settings-file", help="validated review-pack-user.json payload, normally produced by the TUI")
    ap.add_argument("--force-pack-files", action="store_true", help="overwrite pack-owned files, including locally modified ones")
    ap.add_argument("--update", action="store_true", help="update an existing versioned installation")
    ap.add_argument("--adopt-existing-pack", action="store_true", help="one-time migration for an older unversioned installation: back up and replace known pack-owned files, then create managed metadata")
    ap.add_argument("--source-remote"); ap.add_argument("--source-ref"); ap.add_argument("--source-subdir"); ap.add_argument("--source-commit")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, check=True)
    target = repo / ".opencode"; target.mkdir(exist_ok=True); meta_path = target / META_NAME
    old_meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else None
    if args.update and not old_meta: raise SystemExit("cannot --update: .opencode/review-pack.json is missing; for an older pack installation run once with --adopt-existing-pack")
    if args.adopt_existing_pack and old_meta: raise SystemExit("installation is already versioned; use --update instead of --adopt-existing-pack")
    if args.adopt_existing_pack and args.update: raise SystemExit("--adopt-existing-pack and --update are mutually exclusive")

    profiles = args.profile or detect(git_files(repo))
    if "generic" not in profiles: profiles.insert(0, "generic")
    profiles = list(dict.fromkeys(profiles)); settings = resolve_settings(args, repo, profiles); profiles = settings["profiles"]
    managed, conflicts = install_files(target, old_meta, args.update, args.force_pack_files, args.adopt_existing_pack)
    base_config = update_config(target, old_meta, args.update)
    if args.update and not args.settings_file:
        preserve_merged_config_settings(repo, settings, profiles)
    else:
        tui_core.apply_settings_to_target(repo, settings)
    meta = {"schemaVersion": 1, "version": VERSION, "complete": not conflicts, "installedAt": datetime.now(timezone.utc).isoformat(), "managedFiles": managed, "baseConfig": base_config, "source": source_metadata(args), "conflicts": conflicts, "adoptedLegacy": bool(args.adopt_existing_pack)}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print("profiles:", ", ".join(profiles)); print(("updated" if args.update else "installed"), f"review pack {VERSION} into", repo)
    if args.adopt_existing_pack: print("legacy installation adopted; backups are under .opencode/state/installer-backups/legacy-adoption")
    if conflicts: print(f"update completed with {len(conflicts)} conflict(s); inspect .opencode/state/update-conflicts", file=sys.stderr)
    print("control TUI: .opencode/bin/review-pack"); print("smoke: python3 .opencode/bin/review-pack-smoke.py .")
    print("POSIX launch: .opencode/bin/opencode-review"); print("PowerShell launch: .opencode/bin/opencode-review.ps1")
    print("update check: .opencode/bin/review-pack-update --check"); print("inside OpenCode run: /repo-prompts")


if __name__ == "__main__": main()
