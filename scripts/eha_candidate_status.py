#!/usr/bin/env python3
"""Emit one bounded, fail-closed candidate identity for a bridged EHA run."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_BRANCH_RE = re.compile(r"^dev/release-[0-9]+\.[0-9]+\.[0-9]+$")


class CandidateError(RuntimeError):
    """Fail-closed candidate identity error."""


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def candidate_status(root: Path, env: dict[str, str]) -> dict[str, object]:
    if env.get("CODESLEUTH_EHA_PREVERIFIED") != "1":
        raise CandidateError("candidate identity is available only through the trusted EHA bridge")
    branch = env.get("CODESLEUTH_EHA_RELEASE_BRANCH", "").strip()
    expected = env.get("CODESLEUTH_EHA_EXPECTED_SHA", "").strip().lower()
    if not RELEASE_BRANCH_RE.fullmatch(branch):
        raise CandidateError("bridge release branch is missing or invalid")
    if not SHA_RE.fullmatch(expected):
        raise CandidateError("bridge expected SHA is missing or invalid")

    remote_ref = f"refs/remotes/origin/{branch}"
    checkout = git(root, "rev-parse", "HEAD").lower()
    remote_head = git(root, "rev-parse", remote_ref).lower()
    dirty_lines = git(root, "status", "--porcelain=v1").splitlines()
    if checkout != expected or remote_head != expected:
        raise CandidateError(
            "exact candidate mismatch: "
            f"expected={expected} checkout={checkout} remoteHead={remote_head}"
        )
    if dirty_lines:
        raise CandidateError("candidate checkout is not clean")
    return {
        "schemaVersion": 1,
        "releaseBranch": branch,
        "remoteRef": remote_ref,
        "selectedSha": expected,
        "checkoutSha": checkout,
        "remoteHeadSha": remote_head,
        "branch": "DETACHED",
        "dirty": False,
        "selectionProvenance": "github-eha-bridge-preverified",
    }


def main() -> int:
    try:
        result = candidate_status(Path.cwd().resolve(), dict(os.environ))
    except (CandidateError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"EHA CANDIDATE ERROR: {detail}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
