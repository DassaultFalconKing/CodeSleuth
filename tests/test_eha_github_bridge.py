from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eha_github_bridge.py"
WORKFLOW = ROOT / ".github" / "workflows" / "eha.yml"
DOC = ROOT / "docs" / "GITHUB-EHA-BRIDGE.md"


def load_bridge():
    spec = importlib.util.spec_from_file_location("eha_github_bridge", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_owner_issue_command_requires_literal_release_head_and_full_sha() -> None:
    bridge = load_bridge()
    sha = "a" * 40
    branch, parsed_sha, scope = bridge.parse_issue_request(
        f"/eha-test dev/release-0.4.0 {sha} release candidate EHA"
    )
    assert branch == "dev/release-0.4.0"
    assert parsed_sha == sha
    assert scope == "release candidate EHA"

    with pytest.raises(bridge.BridgeError):
        bridge.parse_issue_request(f"/eha-test main {sha}")
    with pytest.raises(bridge.BridgeError):
        bridge.parse_issue_request("/eha-test dev/release-0.4.0 deadbeef")
    with pytest.raises(bridge.BridgeError):
        bridge.parse_issue_request(f"please /eha-test dev/release-0.4.0 {sha}")


def test_bridge_detects_failed_sha_across_review_ledgers(tmp_path: Path) -> None:
    bridge = load_bridge()
    target = "b" * 40
    review_a = tmp_path / "state" / "reviews" / "review-a"
    review_b = tmp_path / "state" / "reviews" / "review-b"
    review_a.mkdir(parents=True)
    review_b.mkdir(parents=True)
    (review_a / "eha.ndjson").write_text(
        json.dumps(
            {
                "type": "verdict",
                "campaignId": "EHA-old",
                "targetSha": target,
                "level": "SIB1",
                "verdict": "FAIL",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (review_b / "eha.ndjson").write_text(
        json.dumps(
            {
                "type": "campaign_started",
                "campaignId": "EHA-other",
                "targetSha": "c" * 40,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert bridge.prior_failed_sha(tmp_path / "state", target) == ("review-a", "EHA-old")
    assert bridge.prior_failed_sha(tmp_path / "state", "d" * 40) is None


def test_bridge_derives_only_the_new_exact_target_campaign(tmp_path: Path) -> None:
    bridge = load_bridge()
    target = "d" * 40
    review = tmp_path / "state" / "reviews" / "review-new"
    review.mkdir(parents=True)
    ledger = review / "eha.ndjson"
    ledger.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {
                    "type": "campaign_started",
                    "campaignId": "EHA-new",
                    "targetSha": target,
                    "recordedAt": "2026-08-27T16:00:00+00:00",
                },
                {
                    "type": "verdict",
                    "campaignId": "EHA-new",
                    "targetSha": target,
                    "level": "SIB0",
                    "verdict": "PASS",
                },
                {
                    "type": "verdict",
                    "campaignId": "EHA-new",
                    "targetSha": target,
                    "level": "SIB1",
                    "verdict": "PASS",
                },
                {
                    "type": "verdict",
                    "campaignId": "EHA-new",
                    "targetSha": target,
                    "level": "SIB2",
                    "verdict": "PASS",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    started = bridge.datetime.fromisoformat("2026-08-27T15:59:59+00:00")
    found = bridge.latest_new_campaign(tmp_path / "state", target, started)
    assert found is not None
    review_id, campaign, events = found
    assert review_id == "review-new"
    assert campaign["campaignId"] == "EHA-new"
    assert bridge.verdict_summary(campaign, events) == {
        "SIB0": "PASS",
        "SIB1": "PASS",
        "SIB2": "PASS",
    }


def test_persistence_root_must_live_outside_disposable_checkout(tmp_path: Path) -> None:
    bridge = load_bridge()
    worktree = tmp_path / "repo"
    worktree.mkdir()
    with pytest.raises(bridge.BridgeError):
        bridge.ensure_external(worktree, worktree / ".opencode" / "state")
    external = bridge.ensure_external(worktree, tmp_path / "durable-eha")
    assert external == (tmp_path / "durable-eha").resolve()
    assert external.is_dir()


def test_private_transcript_is_host_local_unique_and_not_public_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = load_bridge()
    persist_root = tmp_path / "eha"
    persist_root.mkdir()
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")

    path = bridge.private_transcript_path(persist_root)
    assert path == persist_root / "bridge-logs" / "12345-attempt-2.log"
    assert path.exists()
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(bridge.BridgeError):
        bridge.private_transcript_path(persist_root)


def test_headless_opencode_permission_denies_git_mutation() -> None:
    bridge = load_bridge()
    permissions = json.loads(bridge.opencode_environment(ROOT)["OPENCODE_PERMISSION"])
    assert permissions["edit"]["*"] == "deny"
    assert permissions["edit"][".codesleuth/reports/**"] == "allow"
    assert permissions["bash"]["*"] == "allow"
    for pattern in (
        "git add*",
        "git checkout*",
        "git clean*",
        "git commit*",
        "git merge*",
        "git push*",
        "git rebase*",
        "git reset*",
        "git restore*",
        "git switch*",
        "git tag*",
        "git update-ref*",
        "git worktree*",
    ):
        assert permissions["bash"][pattern] == "deny"


def test_workflow_is_a_delegating_owner_gated_self_hosted_bridge() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "issue_comment:" in text
    assert "github.actor == github.repository_owner" in text
    assert "startsWith(github.event.comment.body, '/eha-test ')" in text
    assert "runs-on: [self-hosted, codesleuth-eha]" in text
    assert "cancel-in-progress: false" in text
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text
    assert "scripts/eha_github_bridge.py" in text

    assert '"run", "--command", "eha-test", "--format", "json"' in script
    assert "OPENCODE_CONFIG_DIR" in script
    assert "OPENCODE_DISABLE_AUTOUPDATE" in script
    assert "literal release-stream head" in script
    assert "refs/remotes/origin/" in script
    assert "prior_failed_sha" in script
    assert "post-EHA exact-target check" in script
    assert "state/reviews/<reviewId>/eha.ndjson" in script
    assert "stdout=transcript" in script
    assert "stderr=subprocess.STDOUT" in script
    assert "PRIVATE EHA TRANSCRIPT AND BRIDGE STATUS RECORDED ON TRUSTED HOST" in script


def test_bridge_document_is_discoverable_from_docs_index() -> None:
    assert DOC.exists()
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "GITHUB-EHA-BRIDGE.md" in index
