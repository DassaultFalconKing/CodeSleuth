from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from fnmatch import fnmatchcase
import sys
import time

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
    records = [
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
        {
            "type": "campaign_completed",
            "campaignId": "EHA-new",
            "targetSha": target,
            "reportPath": ".codesleuth/reports/eha-new.md",
        },
    ]
    ledger.write_text(
        "\n".join(json.dumps(event) for event in records) + "\n",
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
    assert bridge.campaign_completion(campaign, events)["reportPath"] == (
        ".codesleuth/reports/eha-new.md"
    )


def test_completion_requires_all_pass_and_exact_target() -> None:
    bridge = load_bridge()
    target = "a" * 40
    start = {"campaignId": "EHA-x", "targetSha": target}
    events = [
        start | {"type": "campaign_started"},
        {
            "type": "verdict",
            "campaignId": "EHA-x",
            "targetSha": target,
            "level": "SIB0",
            "verdict": "PASS",
        },
        {
            "type": "campaign_completed",
            "campaignId": "EHA-x",
            "targetSha": target,
            "reportPath": ".codesleuth/reports/x.md",
        },
    ]
    with pytest.raises(bridge.BridgeError, match="before all SIB verdicts are PASS"):
        bridge.campaign_completion(start, events)

    complete_events = [
        start | {"type": "campaign_started"},
        *[
            {
                "type": "verdict",
                "campaignId": "EHA-x",
                "targetSha": target,
                "level": level,
                "verdict": "PASS",
            }
            for level in bridge.LEVELS
        ],
        {
            "type": "campaign_completed",
            "campaignId": "EHA-x",
            "targetSha": "b" * 40,
            "reportPath": ".codesleuth/reports/x.md",
        },
    ]
    with pytest.raises(bridge.BridgeError, match="target mismatch"):
        bridge.campaign_completion(start, complete_events)


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


def test_headless_opencode_permission_is_fail_closed_for_repository_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = load_bridge()
    repo = tmp_path / "repo"
    repo.mkdir()
    persist = tmp_path / "persist"
    monkeypatch.setenv("GITHUB_RUN_ID", "rc5b-regression")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    scratch = bridge.prepare_scratch_dir(repo, persist)
    target = "a" * 40
    environment = bridge.opencode_environment(
        repo,
        scratch,
        release_branch="dev/release-0.4.0",
        expected_sha=target,
    )
    permissions = json.loads(environment["OPENCODE_PERMISSION"])

    assert permissions["edit"]["*"] == "deny"
    assert permissions["edit"][".codesleuth/reports/**"] == "allow"
    assert permissions["bash"]["*"] == "deny"
    assert permissions["bash"]["git status*"] == "allow"
    assert permissions["bash"]["python -m pytest*"] == "allow"
    assert permissions["bash"]["python scripts/eha_candidate_status.py*"] == "allow"
    assert permissions["bash"]["*Out-File*"] == "deny"
    assert permissions["bash"]["*Get-ChildItem*-Recurse*"] == "deny"
    assert permissions["bash"]["*>*"] == "deny"
    assert "python3 -c*" not in permissions["bash"]

    def decision(command: str) -> str:
        result = "ask"
        for pattern, action in permissions["bash"].items():
            if fnmatchcase(command, pattern):
                result = action
        return result

    assert decision('Get-Content ".codesleuth/reports/INDEX.md" -Raw') == "allow"
    assert decision("Out-File -Encoding utf8 temp.txt") == "deny"
    assert decision('Get-Content "VERSION" > temp.txt') == "deny"
    assert decision("python3 -c \"open('temp.txt', 'w').write('x')\"") == "deny"

    assert scratch == persist / "bridge-runtime" / "rc5b-regression-attempt-1" / "scratch"
    assert scratch.is_dir()
    assert not scratch.is_relative_to(repo)
    for key in ("CODESLEUTH_EHA_SCRATCH_DIR", "TEMP", "TMP", "TMPDIR"):
        assert environment[key] == str(scratch)
    assert environment["CODESLEUTH_EHA_PREVERIFIED"] == "1"
    assert environment["CODESLEUTH_EHA_RELEASE_BRANCH"] == "dev/release-0.4.0"
    assert environment["CODESLEUTH_EHA_EXPECTED_SHA"] == target

    with pytest.raises(bridge.BridgeError, match="refusing to reuse"):
        bridge.prepare_scratch_dir(repo, persist)


def test_bridge_requires_an_explicit_provider_model() -> None:
    bridge = load_bridge()

    assert bridge.validate_model("opencode/nemotron-3.5-lightning-free") == (
        "opencode/nemotron-3.5-lightning-free"
    )
    with pytest.raises(bridge.BridgeError, match="explicit host-qualified model"):
        bridge.validate_model(None)
    with pytest.raises(bridge.BridgeError, match="provider/model"):
        bridge.validate_model("ambient-default")


def test_root_watchdog_stops_a_provider_before_first_response(tmp_path: Path) -> None:
    bridge = load_bridge()
    transcript = tmp_path / "bridge.log"
    state = tmp_path / "state"
    state.mkdir()
    started = bridge.datetime.now(bridge.timezone.utc)
    before = time.monotonic()

    result = bridge.run_monitored_process(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        transcript_path=transcript,
        state_dir=state,
        expected_sha="b" * 40,
        started_at=started,
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=0.15,
            campaign_start_seconds=2,
            idle_seconds=2,
            poll_seconds=0.02,
        ),
    )

    returncode, reason, first_response, campaign, completion, _, stalled_at = result
    assert time.monotonic() - before < 5
    assert returncode != 0
    assert reason == "FIRST_RESPONSE_TIMEOUT"
    assert first_response is False
    assert campaign is False
    assert completion is False
    assert stalled_at is not None


def test_root_watchdog_stops_a_responsive_session_without_campaign(tmp_path: Path) -> None:
    bridge = load_bridge()
    transcript = tmp_path / "bridge.log"
    state = tmp_path / "state"
    state.mkdir()

    result = bridge.run_monitored_process(
        [sys.executable, "-c", "print('{}', flush=True); import time; time.sleep(30)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        transcript_path=transcript,
        state_dir=state,
        expected_sha="c" * 40,
        started_at=bridge.datetime.now(bridge.timezone.utc),
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=1,
            campaign_start_seconds=0.2,
            idle_seconds=2,
            poll_seconds=0.02,
        ),
    )

    returncode, reason, first_response, campaign, completion, _, _ = result
    assert returncode != 0
    assert reason == "CAMPAIGN_START_TIMEOUT"
    assert first_response is True
    assert campaign is False
    assert completion is False


def test_root_watchdog_preserves_a_started_campaign_as_incomplete_evidence(
    tmp_path: Path,
) -> None:
    bridge = load_bridge()
    transcript = tmp_path / "bridge.log"
    state = tmp_path / "state"
    review = state / "reviews" / "review-watchdog"
    review.mkdir(parents=True)
    target = "d" * 40
    recorded = bridge.datetime.now(bridge.timezone.utc).isoformat()
    event = json.dumps(
        {
            "type": "campaign_started",
            "campaignId": "EHA-watchdog",
            "targetSha": target,
            "recordedAt": recorded,
        }
    )
    child = (
        "from pathlib import Path; import time; "
        f"Path({str(review / 'eha.ndjson')!r}).write_text({(event + chr(10))!r}, encoding='utf-8'); "
        "print('{}', flush=True); time.sleep(30)"
    )
    started = bridge.datetime.fromisoformat(recorded) - bridge.timedelta(seconds=1)

    result = bridge.run_monitored_process(
        [sys.executable, "-c", child],
        cwd=tmp_path,
        env=os.environ.copy(),
        transcript_path=transcript,
        state_dir=state,
        expected_sha=target,
        started_at=started,
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=1,
            campaign_start_seconds=1,
            idle_seconds=0.2,
            poll_seconds=0.02,
        ),
    )

    returncode, reason, first_response, campaign, completion, _, _ = result
    assert returncode != 0
    assert reason == "NO_PROGRESS_TIMEOUT"
    assert first_response is True
    assert campaign is True
    assert completion is False
    found = bridge.latest_new_campaign(state, target, started)
    assert found is not None
    assert bridge.verdict_summary(found[1], found[2]) == {
        "SIB0": "PENDING",
        "SIB1": "PENDING",
        "SIB2": "PENDING",
    }


def test_root_monitor_terminates_provider_after_durable_completion(tmp_path: Path) -> None:
    bridge = load_bridge()
    transcript = tmp_path / "bridge.log"
    state = tmp_path / "state"
    review = state / "reviews" / "review-complete"
    review.mkdir(parents=True)
    target = "e" * 40
    recorded = bridge.datetime.now(bridge.timezone.utc).isoformat()
    campaign_id = "EHA-complete"
    records = [
        {
            "type": "campaign_started",
            "campaignId": campaign_id,
            "targetSha": target,
            "recordedAt": recorded,
        },
        *[
            {
                "type": "verdict",
                "campaignId": campaign_id,
                "targetSha": target,
                "level": level,
                "verdict": "PASS",
            }
            for level in bridge.LEVELS
        ],
        {
            "type": "campaign_completed",
            "campaignId": campaign_id,
            "targetSha": target,
            "reportPath": ".codesleuth/reports/eha-complete.md",
            "recordedAt": recorded,
        },
    ]
    payload = "\n".join(json.dumps(record) for record in records) + "\n"
    child = (
        "from pathlib import Path; import time; "
        "print('{}', flush=True); time.sleep(0.05); "
        f"Path({str(review / 'eha.ndjson')!r}).write_text({payload!r}, encoding='utf-8'); "
        "time.sleep(30)"
    )
    started = bridge.datetime.fromisoformat(recorded) - bridge.timedelta(seconds=1)
    before = time.monotonic()

    result = bridge.run_monitored_process(
        [sys.executable, "-c", child],
        cwd=tmp_path,
        env=os.environ.copy(),
        transcript_path=transcript,
        state_dir=state,
        expected_sha=target,
        started_at=started,
        watchdog=bridge.WatchdogConfig(
            first_response_seconds=1,
            campaign_start_seconds=1,
            idle_seconds=2,
            poll_seconds=0.02,
        ),
    )

    _, reason, first_response, campaign, completion, _, stalled_at = result
    assert time.monotonic() - before < 5
    assert reason is None
    assert first_response is True
    assert campaign is True
    assert completion is True
    assert stalled_at is None


def test_bridge_status_records_transport_error_without_inventing_eha_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = load_bridge()
    persist = tmp_path / "persist"
    transcript = persist / "bridge-logs" / "run-attempt-1.log"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_RUN_ID", "run")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    now = bridge.datetime.now(bridge.timezone.utc)

    path = bridge.write_bridge_status(
        persist,
        review_id=None,
        campaign_id=None,
        release_branch="dev/release-0.4.0",
        target_sha="e" * 40,
        verdicts={"SIB0": "PENDING", "SIB1": "PENDING", "SIB2": "PENDING"},
        outcome="NOT_RUN",
        transport_outcome="ERROR",
        reason="FIRST_RESPONSE_TIMEOUT",
        model="opencode/nemotron-3.5-lightning-free",
        opencode_version="1.18.25",
        opencode_returncode=1,
        transcript_path=transcript,
        first_response_observed=False,
        campaign_observed=False,
        durable_completion_observed=False,
        started_at=now,
        last_activity_at=now,
        stalled_at=now,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 3
    assert payload["outcome"] == "NOT_RUN"
    assert payload["transportOutcome"] == "ERROR"
    assert payload["reason"] == "FIRST_RESPONSE_TIMEOUT"
    assert payload["campaignId"] is None
    assert payload["durableCompletionObserved"] is False
    assert set(payload["verdicts"].values()) == {"PENDING"}


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
    assert "CODESLEUTH_EHA_MODEL: ${{ vars.CODESLEUTH_EHA_MODEL }}" in text
    assert '--model "$CODESLEUTH_EHA_MODEL"' in text

    assert '"run", "--command", "eha-test", "--format", "json"' in script
    assert "OPENCODE_CONFIG_DIR" in script
    assert "OPENCODE_DISABLE_AUTOUPDATE" in script
    assert "CODESLEUTH_EHA_SCRATCH_DIR" in script
    assert '"*": "deny"' in script
    assert "literal release-stream head" in script
    assert "refs/remotes/origin/" in script
    assert "prior_failed_sha" in script
    assert "post-EHA exact-target check" in script
    assert "state/reviews/<reviewId>/eha.ndjson" in script
    assert "stdout=transcript" in script
    assert "stderr=subprocess.STDOUT" in script
    assert "FIRST_RESPONSE_TIMEOUT" in script
    assert "CAMPAIGN_START_TIMEOUT" in script
    assert "NO_PROGRESS_TIMEOUT" in script
    assert "campaign_completed" in script
    assert "NO_DURABLE_COMPLETION" in script
    assert "PRIVATE EHA TRANSCRIPT AND BRIDGE STATUS RECORDED ON TRUSTED HOST" in script


def test_bridge_document_is_discoverable_from_docs_index() -> None:
    assert DOC.exists()
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "GITHUB-EHA-BRIDGE.md" in index
