from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT = ROOT / "scripts" / "eha_campaign_bootstrap.py"
BRIDGE_SCRIPT = ROOT / "scripts" / "eha_github_bridge.py"
RC6_BRIDGE_SCRIPT = ROOT / "scripts" / "eha_github_bridge_rc6.py"
WORKFLOW = ROOT / ".github" / "workflows" / "eha.yml"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def fixture_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "ci@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "CI"], check=True)
    (root / "tracked.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
    return root, git(root, "rev-parse", "HEAD")


def test_trusted_bootstrap_creates_review_and_campaign_before_provider(tmp_path: Path) -> None:
    bootstrap = load_module("eha_campaign_bootstrap", BOOTSTRAP_SCRIPT)
    root, sha = fixture_repo(tmp_path)
    state_dir = tmp_path / "authority" / "state"
    now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    result = bootstrap.start_trusted_campaign(
        root,
        state_dir,
        target_sha=sha,
        target_branch="dev/release-0.4.0",
        scope="RC6 exact-head acceptance",
        controller_session="github-eha-test",
        now=now,
    )

    review_id = result["reviewId"]
    review_dir = state_dir / "reviews" / review_id
    state = json.loads((review_dir / "state.json").read_text(encoding="utf-8"))
    ledger = [json.loads(line) for line in (review_dir / "eha.ndjson").read_text(encoding="utf-8").splitlines()]

    assert state["schemaVersion"] == 2
    assert state["headSha"] == sha
    assert state["dirtyAtStart"] is False
    assert (state_dir / "reviews" / "latest.txt").read_text(encoding="utf-8").strip() == review_id
    assert len(ledger) == 1
    assert ledger[0]["type"] == "campaign_started"
    assert ledger[0]["targetSha"] == sha
    assert ledger[0]["targetBranch"] == "dev/release-0.4.0"
    assert ledger[0]["bootstrapAuthority"] == "trusted_github_bridge"
    assert ledger[0]["recordedHeadSha"] == sha


def test_trusted_bootstrap_rejects_dirty_or_moved_target(tmp_path: Path) -> None:
    bootstrap = load_module("eha_campaign_bootstrap_dirty", BOOTSTRAP_SCRIPT)
    root, sha = fixture_repo(tmp_path)
    state_dir = tmp_path / "authority" / "state"

    (root / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(bootstrap.BootstrapError, match="clean exact-target"):
        bootstrap.start_trusted_campaign(
            root,
            state_dir,
            target_sha=sha,
            target_branch="dev/release-0.4.0",
            scope="test",
            controller_session="bridge",
        )

    subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "move"], check=True, capture_output=True)
    with pytest.raises(bootstrap.BootstrapError, match="HEAD CHANGED"):
        bootstrap.start_trusted_campaign(
            root,
            state_dir,
            target_sha=sha,
            target_branch="dev/release-0.4.0",
            scope="test",
            controller_session="bridge",
        )


def test_prestarted_campaign_removes_campaign_start_watchdog_dependency(tmp_path: Path) -> None:
    bridge = load_module("eha_github_bridge_prestart", BRIDGE_SCRIPT)
    target = "a" * 40
    state_dir = tmp_path / "state"
    review = state_dir / "reviews" / "prestarted-review"
    review.mkdir(parents=True)
    started = datetime.now(timezone.utc)
    (review / "eha.ndjson").write_text(
        json.dumps(
            {
                "type": "campaign_started",
                "eventId": "E-prestarted",
                "campaignId": "EHA-prestarted",
                "targetSha": target,
                "targetBranch": "dev/release-0.4.0",
                "scope": "test",
                "recordedAt": started.isoformat(),
                "recordedHeadSha": target,
                "bootstrapAuthority": "trusted_github_bridge",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    transcript = tmp_path / "transcript.log"
    transcript.touch()

    result = bridge.run_monitored_process(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        cwd=tmp_path,
        env=dict(**__import__("os").environ),
        transcript_path=transcript,
        state_dir=state_dir,
        expected_sha=target,
        started_at=started,
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=0.15,
            campaign_start_seconds=0.25,
            idle_seconds=1.0,
            poll_seconds=0.02,
        ),
    )

    _, reason, first_response, campaign_observed, completion_observed, _, _ = result
    assert reason == "FIRST_RESPONSE_TIMEOUT"
    assert first_response is False
    assert campaign_observed is True
    assert completion_observed is False
    assert reason != "CAMPAIGN_START_TIMEOUT"


def test_workflow_and_rc6_prompt_use_prestarted_campaign() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    rc6 = RC6_BRIDGE_SCRIPT.read_text(encoding="utf-8")
    assert "python3 scripts/eha_github_bridge_rc6.py" in workflow
    assert "created the review checkpoint" in rc6
    assert "Do not create, restart, replace, or supersede that campaign" in rc6
    assert "bridge.invoke_opencode(" not in rc6
