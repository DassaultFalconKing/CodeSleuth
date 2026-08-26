#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

META_NAME = "review-pack.json"
RESTART_MARKER = Path(".opencode") / "state" / "tui-restart-request.json"
APPLIED_MESSAGE = "REVIEW PACK UPDATE APPLIED"


def run(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, **kwargs)


def load_meta(repo: Path):
    path = repo / ".opencode" / META_NAME
    if not path.is_file():
        raise SystemExit(f"missing {path}; this repository is not a managed CodeSleuth installation")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_source(meta, args):
    src = dict(meta.get("source") or {})
    if args.source_remote:
        src["remote"] = args.source_remote
    if args.source_ref:
        src["ref"] = args.source_ref
    if args.source_subdir is not None:
        src["subdir"] = args.source_subdir
    remote, ref = src.get("remote"), src.get("ref")
    if not remote or not ref:
        raise SystemExit(
            "installation has no updateable source remote/ref; rerun the pack installer with --source-remote and "
            "--source-ref, or update from a local pack checkout using install.sh <repo> --update"
        )
    src.setdefault("subdir", "")
    return src


def remote_head(remote: str, ref: str):
    for full_ref in (f"refs/heads/{ref}", f"refs/tags/{ref}"):
        p = run(["git", "ls-remote", remote, full_ref])
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.split()[0]
    raise SystemExit(f"cannot resolve {ref!r} at {remote!r}")


def verify_installation(repo: Path) -> None:
    smoke = repo / ".opencode" / "bin" / "review-pack-smoke.py"
    if not smoke.is_file():
        raise SystemExit(f"updated CodeSleuth is missing Verify entrypoint: {smoke}")
    result = subprocess.run(
        [sys.executable, str(smoke), str(repo)],
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(f"updated CodeSleuth failed Verify (exit {result.returncode}); refusing automatic restart")


def request_tui_restart(repo: Path, source_commit: str) -> Path:
    marker = repo / RESTART_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": 1,
        "sourceCommit": source_commit,
        "nonce": time.time_ns(),
    }
    temp = marker.with_suffix(marker.suffix + ".tmp")
    temp.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(marker)
    return marker


def restart_tui(repo: Path) -> None:
    bootstrap = repo / ".opencode" / "bin" / "review_pack_tui_bootstrap.py"
    if not bootstrap.is_file():
        raise SystemExit(f"updated CodeSleuth is missing TUI bootstrap: {bootstrap}")
    os.environ["REVIEW_PACK_TARGET_ROOT"] = str(repo)
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, str(bootstrap), "--target", str(repo)])


def finalize_update(repo: Path, source_commit: str, *, restart: bool) -> None:
    verify_installation(repo)
    marker = request_tui_restart(repo, source_commit)
    print(APPLIED_MESSAGE)
    print("restart request:", marker)
    if restart:
        restart_tui(repo)


def main():
    ap = argparse.ArgumentParser(
        description="Check for and apply floating CodeSleuth updates from an explicit Git source ref."
    )
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--check", action="store_true", help="only compare installed source commit with the remote source")
    ap.add_argument(
        "--restart",
        action="store_true",
        help="after a successful update and Verify, replace this CLI process with the updated CodeSleuth TUI",
    )
    ap.add_argument("--source-remote", help="override recorded Git remote for this run")
    ap.add_argument("--source-ref", help="override recorded branch/tag for this run")
    ap.add_argument("--source-subdir", help="override pack subdirectory inside the source repository")
    ap.add_argument("--force-pack-files", action="store_true", help="replace locally modified managed files")
    args = ap.parse_args()
    if args.check and args.restart:
        ap.error("--check and --restart are mutually exclusive")

    repo = Path(args.repo).resolve()
    meta = load_meta(repo)
    source = resolve_source(meta, args)
    head = remote_head(source["remote"], source["ref"])
    installed_commit = source.get("commit")
    print("installed version:", meta.get("version", "unknown"))
    print("installed source:", installed_commit or "unknown")
    print("remote source:", head)
    if installed_commit == head:
        print("REVIEW PACK CURRENT")
        return
    print("REVIEW PACK UPDATE AVAILABLE")
    if args.check:
        return

    with tempfile.TemporaryDirectory(prefix="opencode-review-pack-update-") as td:
        clone = Path(td) / "source"
        p = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", source["ref"], source["remote"], str(clone)]
        )
        if p.returncode != 0:
            raise SystemExit(p.returncode)
        pack_root = clone / source.get("subdir", "")
        installer = pack_root / "install.py"
        if not installer.is_file():
            raise SystemExit(
                f"latest source does not contain {installer.relative_to(clone)}; "
                "recorded source metadata is stale or points at the wrong repository"
            )
        cmd = [
            sys.executable,
            str(installer),
            str(repo),
            "--update",
            "--source-remote",
            source["remote"],
            "--source-ref",
            source["ref"],
            "--source-subdir",
            source.get("subdir", ""),
            "--source-commit",
            head,
        ]
        if args.force_pack_files:
            cmd.append("--force-pack-files")
        code = subprocess.run(cmd).returncode
        if code:
            raise SystemExit(code)

    finalize_update(repo, head, restart=args.restart)


if __name__ == "__main__":
    main()
