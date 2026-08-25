#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


class VersionMetadataError(RuntimeError):
    """Raised when CodeSleuth version metadata is absent or malformed."""


def validate_version(value: str, source: str | Path) -> str:
    """Validate one version string read from an identified metadata source."""
    version = value.strip()
    if not version:
        raise VersionMetadataError(f"CodeSleuth version metadata is empty: {source}")
    if not _VERSION_RE.fullmatch(version):
        raise VersionMetadataError(f"invalid CodeSleuth version {version!r} in {source}")
    return version


def source_version(distribution_root: Path) -> str:
    """Read the source-distribution version from the canonical root VERSION file."""
    path = distribution_root.resolve() / "VERSION"
    if not path.is_file():
        raise VersionMetadataError(f"missing CodeSleuth VERSION metadata: {path}")
    return validate_version(path.read_text(encoding="utf-8"), path)


def installed_version(target_root: Path) -> str:
    """Read the installed version materialized into .opencode/codesleuth.json."""
    path = target_root.resolve() / ".opencode" / "codesleuth.json"
    if not path.is_file():
        raise VersionMetadataError(f"missing installed CodeSleuth metadata: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersionMetadataError(f"cannot read installed CodeSleuth metadata: {path}: {exc}") from exc
    value = payload.get("version")
    if not isinstance(value, str):
        raise VersionMetadataError(f"installed CodeSleuth metadata has no string version: {path}")
    return validate_version(value, path)


def resolve_version(
    distribution_root: Path | None = None,
    target_root: Path | None = None,
) -> str:
    """Resolve the version for the active CodeSleuth surface without a fallback constant."""
    if distribution_root is not None:
        return source_version(distribution_root)
    if target_root is not None:
        return installed_version(target_root)

    distribution_env = os.environ.get("CODESLEUTH_DISTRIBUTION_ROOT")
    if distribution_env:
        return source_version(Path(distribution_env))
    target_env = os.environ.get("CODESLEUTH_TARGET_ROOT")
    if target_env:
        return installed_version(Path(target_env))
    raise VersionMetadataError(
        "cannot resolve CodeSleuth version: set CODESLEUTH_DISTRIBUTION_ROOT or CODESLEUTH_TARGET_ROOT"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Print CodeSleuth version from canonical metadata")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--distribution", type=Path, help="CodeSleuth source checkout containing VERSION")
    source.add_argument("--target", type=Path, help="installed target containing .opencode/codesleuth.json")
    args = parser.parse_args()
    try:
        print(resolve_version(args.distribution, args.target))
    except VersionMetadataError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
