from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eha_candidate_status.py"


def load_candidate_status():
    spec = importlib.util.spec_from_file_location("eha_candidate_status", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def disposable_candidate(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    repo = tmp_path / "candidate"
    repo.mkdir()
    git(repo, "init")
    (repo / "tracked.txt").write_text("candidate\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(
        repo,
        "-c",
        "user.name=CodeSleuth Test",
        "-c",
        "user.email=codesleuth@example.invalid",
        "commit",
        "-m",
        "candidate",
    )
    sha = git(repo, "rev-parse", "HEAD")
    branch = "dev/release-0.4.0"
    git(repo, "update-ref", f"refs/remotes/origin/{branch}", sha)
    git(repo, "checkout", "--detach", sha)
    env = {
        "CODESLEUTH_EHA_PREVERIFIED": "1",
        "CODESLEUTH_EHA_RELEASE_BRANCH": branch,
        "CODESLEUTH_EHA_EXPECTED_SHA": sha,
    }
    return repo, sha, env


def test_candidate_status_reverifies_real_detached_git_identity(tmp_path: Path) -> None:
    module = load_candidate_status()
    repo, sha, env = disposable_candidate(tmp_path)

    result = module.candidate_status(repo, env)

    assert result == {
        "schemaVersion": 1,
        "releaseBranch": "dev/release-0.4.0",
        "remoteRef": "refs/remotes/origin/dev/release-0.4.0",
        "selectedSha": sha,
        "checkoutSha": sha,
        "remoteHeadSha": sha,
        "branch": "DETACHED",
        "dirty": False,
        "selectionProvenance": "github-eha-bridge-preverified",
    }


def test_candidate_status_fails_closed_for_dirty_or_moved_identity(tmp_path: Path) -> None:
    module = load_candidate_status()
    repo, _, env = disposable_candidate(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(module.CandidateError, match="not clean"):
        module.candidate_status(repo, env)

    (repo / "untracked.txt").unlink()
    env["CODESLEUTH_EHA_EXPECTED_SHA"] = "f" * 40
    with pytest.raises(module.CandidateError, match="exact candidate mismatch"):
        module.candidate_status(repo, env)


def test_candidate_status_rejects_unbridged_use(tmp_path: Path) -> None:
    module = load_candidate_status()

    with pytest.raises(module.CandidateError, match="trusted EHA bridge"):
        module.candidate_status(tmp_path, {})
