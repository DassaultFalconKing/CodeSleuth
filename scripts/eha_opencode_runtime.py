#!/usr/bin/env python3
"""Prepare a per-run OpenCode config mirror outside an EHA candidate checkout.

The EHA bridge points OPENCODE_CONFIG at the exact tracked config file. OpenCode's
custom config directory is different: it is a runtime discovery/bootstrap surface
and may receive generated package metadata. This helper copies the exact target's
pack/.opencode tree to an external, unique per-run directory so that generated
runtime files cannot dirty the candidate worktree.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


class RuntimeConfigError(RuntimeError):
    """Fail-closed runtime-config preparation error."""


def prepare_runtime_config(source: Path, target: Path) -> Path:
    source = source.resolve()
    target = target.expanduser().resolve()

    if not source.is_dir():
        raise RuntimeConfigError(f"OpenCode config source does not exist: {source}")
    if not (source / "opencode.json").is_file():
        raise RuntimeConfigError(f"OpenCode config source is missing opencode.json: {source}")

    # Expected source shape is <repo>/pack/.opencode. Keep the writable mirror
    # outside the whole repository, not merely outside pack/.opencode.
    try:
        repo_root = source.parents[1]
    except IndexError as exc:
        raise RuntimeConfigError(f"cannot derive repository root from config source: {source}") from exc

    try:
        target.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise RuntimeConfigError(
            "OpenCode runtime config mirror must live outside the candidate repository"
        )

    if target.exists() or target.is_symlink():
        raise RuntimeConfigError(
            f"refusing to reuse existing OpenCode runtime config mirror: {target}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)

    if not (target / "opencode.json").is_file():
        raise RuntimeConfigError("runtime config mirror is incomplete after copy")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        target = prepare_runtime_config(Path(args.source), Path(args.target))
    except RuntimeConfigError as exc:
        print(f"EHA RUNTIME CONFIG ERROR: {exc}")
        return 2
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
