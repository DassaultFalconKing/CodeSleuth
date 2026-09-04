#!/usr/bin/env python3
"""RC6 trusted EHA controller with deterministic pre-provider campaign bootstrap."""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import eha_campaign_bootstrap
import eha_github_bridge_core as bridge


def invoke_opencode_rc6(
    root: Path,
    release_branch: str,
    expected_sha: str,
    scope: str,
    model: str,
    transcript_path: Path,
    state_dir: Path,
    started_at: datetime,
    watchdog: bridge.WatchdogConfig,
    *,
    review_id: str,
    campaign_id: str,
    provenance_watermark: str,
) -> bridge.OpenCodeExecution:
    """Invoke OpenCode only after trusted controller authority already exists."""
    binary = shutil.which("opencode")
    if not binary:
        raise bridge.BridgeError(
            "opencode is not installed on this runner; canonical EHA requires a trusted OpenCode host"
        )
    version = subprocess.run(
        [binary, "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout.strip()

    message = (
        "GitHub EHA bridge request. Treat this as normal future-SIB analysis on one already-started "
        "trusted campaign. "
        f"Release stream: {release_branch}. Expected literal release HEAD and checkout SHA: "
        f"{expected_sha}. Scope: {scope}. Trusted review: {review_id}. Trusted campaign: "
        f"{campaign_id}. Verified prebound provenance: {provenance_watermark}. The controller already "
        "verified the remote release ref, checked out the exact SHA detached, attached host-persistent "
        "canonical review/EHA state, bound immutable provenance through the canonical watermark "
        "implementation, and appended campaign_started BEFORE provider/model execution. Do not create, "
        "restart, replace, or supersede that campaign and do not rebind provenance. For Step 1 run only "
        "`python scripts/eha_candidate_status.py` and use its bounded JSON as candidate_identity; "
        "do not rediscover refs or enumerate the persistence root. Then load review_state, "
        "provenance_state and eha_state, verify the supplied exact campaign is fresh, incomplete, and "
        "bound to the same target SHA, and continue directly with its SIB profiles one Playbook Step "
        "at a time. The candidate checkout is read-only for this campaign: do not create, modify, "
        "rename, or delete any path inside it, including temporary or scratch files. If transient "
        "storage is unavoidable, use only the external CODESLEUTH_EHA_SCRATCH_DIR. Write analytical "
        "reports only through the bounded .codesleuth/reports route. Run the canonical "
        "eha-sib-acceptance Playbook only. After SIB0, SIB1 and SIB2 durable verdicts and report "
        "persistence, append the durable campaign_completed handshake for the supplied campaign; do "
        "not wait for a final provider frame after that marker."
    )
    command = bridge.opencode_wrapper_command(root)
    command.extend(["run", "--command", "eha-test", "--format", "json"])
    command.extend(["--model", model])
    command.append(message)
    print(f"OPENCODE VERSION {version}", flush=True)
    print(f"EHA MODEL {model}", flush=True)
    print(f"EHA EXACT TARGET {expected_sha} FROM {release_branch}", flush=True)
    scratch_dir = bridge.prepare_scratch_dir(root, transcript_path.parent.parent)
    env = bridge.opencode_environment(
        root,
        scratch_dir,
        release_branch=release_branch,
        expected_sha=expected_sha,
    )
    env["CODESLEUTH_EHA_REVIEW_ID"] = review_id
    env["CODESLEUTH_EHA_CAMPAIGN_ID"] = campaign_id
    env["CODESLEUTH_EHA_PROVENANCE"] = provenance_watermark
    (
        returncode,
        reason,
        first_response_observed,
        campaign_observed,
        completion_observed,
        last_activity_at,
        stalled_at,
    ) = bridge.run_monitored_process(
        command,
        cwd=root,
        env=env,
        transcript_path=transcript_path,
        state_dir=state_dir,
        expected_sha=expected_sha,
        started_at=started_at,
        watchdog=watchdog,
    )
    return bridge.OpenCodeExecution(
        returncode=returncode,
        version=version,
        model=model,
        transport_outcome="ERROR" if reason else "PASS",
        reason=reason,
        first_response_observed=first_response_observed,
        campaign_observed=campaign_observed,
        completion_observed=completion_observed,
        started_at=started_at,
        last_activity_at=last_activity_at,
        stalled_at=stalled_at,
    )


def bootstrap_then_invoke(
    root: Path,
    state_dir: Path,
    persist_root: Path,
    *,
    release_branch: str,
    expected_sha: str,
    scope: str,
    model: str,
    transcript_path: Path,
    started_at: datetime,
    watchdog: bridge.WatchdogConfig,
) -> tuple[dict[str, Any], bridge.OpenCodeExecution]:
    """Establish durable authority first; provider invocation is unreachable on bootstrap failure."""
    bootstrap = eha_campaign_bootstrap.start_trusted_campaign(
        root,
        state_dir,
        target_sha=expected_sha,
        target_branch=release_branch,
        scope=scope,
        controller_session=f"github-eha-{bridge.bridge_run_key()}",
        now=started_at,
    )
    campaign = bootstrap["campaign"]
    provenance = bootstrap["provenance"]
    review_id = str(bootstrap["reviewId"])
    campaign_id = str(campaign["campaignId"])
    watermark = str(provenance["watermark"])
    print(
        "EHA TRUSTED CAMPAIGN BOOTSTRAP "
        f"campaign={campaign_id} review={review_id} target={expected_sha} provenance={watermark}",
        flush=True,
    )
    execution = invoke_opencode_rc6(
        root,
        release_branch,
        expected_sha,
        scope,
        model,
        transcript_path,
        state_dir,
        started_at,
        watchdog,
        review_id=review_id,
        campaign_id=campaign_id,
        provenance_watermark=watermark,
    )
    return bootstrap, execution


def main(argv: list[str] | None = None) -> int:
    try:
        args = bridge.build_parser().parse_args(argv)
        model = bridge.validate_model(args.model)
        watchdog = bridge.WatchdogConfig(
            first_response_seconds=bridge.positive_seconds(
                args.first_response_timeout_seconds, "first-response timeout"
            ),
            campaign_start_seconds=bridge.positive_seconds(
                args.campaign_start_timeout_seconds, "campaign-start timeout"
            ),
            idle_seconds=bridge.positive_seconds(args.idle_timeout_seconds, "idle timeout"),
            poll_seconds=bridge.positive_seconds(
                args.watchdog_poll_seconds, "watchdog poll interval"
            ),
        )
        root = Path.cwd().resolve()
        if not (root / ".git").exists():
            raise bridge.BridgeError("run the EHA bridge from the repository root")
        release_branch, expected_sha, scope = bridge.resolve_request(args)
        persist_root = bridge.ensure_external(root, Path(args.persist_root))

        bridge.require_clean(root, "bridge entry")
        bridge.freeze_release_head(root, release_branch, expected_sha)
        state_dir, _ = bridge.wire_persistence(root, persist_root)

        prior_fail = bridge.prior_failed_sha(state_dir, expected_sha)
        if prior_fail:
            review_id, campaign_id = prior_fail
            raise bridge.BridgeError(
                "exact target already has a durable FAIL verdict in review "
                f"{review_id}, campaign {campaign_id}; failed SHAs are immutable, repair to a new SHA"
            )

        transcript_path = bridge.private_transcript_path(persist_root)
        started = datetime.now(timezone.utc)
        bootstrap, execution = bootstrap_then_invoke(
            root,
            state_dir,
            persist_root,
            release_branch=release_branch,
            expected_sha=expected_sha,
            scope=scope,
            model=model,
            transcript_path=transcript_path,
            started_at=started,
            watchdog=watchdog,
        )
        trusted_review_id = str(bootstrap["reviewId"])
        trusted_campaign_id = str(bootstrap["campaign"]["campaignId"])

        postcondition_error: str | None = None
        try:
            bridge.require_clean(root, "post-EHA exact-target check")
        except bridge.BridgeError as exc:
            postcondition_error = str(exc)

        found = bridge.latest_new_campaign(state_dir, expected_sha, started)
        review_id: str | None = None
        campaign_id: str | None = None
        completion: dict[str, Any] | None = None
        verdicts = {level: "PENDING" for level in bridge.LEVELS}
        if found:
            review_id, start, events = found
            verdicts = bridge.verdict_summary(start, events)
            campaign_id = str(start.get("campaignId"))
            completion = bridge.campaign_completion(start, events)
        if review_id != trusted_review_id or campaign_id != trusted_campaign_id:
            raise bridge.BridgeError(
                "trusted EHA campaign identity changed after provider execution; refusing ambiguous authority"
            )
        completion_observed = execution.completion_observed or completion is not None
        if "FAIL" in verdicts.values():
            outcome = "FAIL"
        elif found and all(verdicts[level] == "PASS" for level in bridge.LEVELS):
            outcome = "PASS"
        elif found:
            outcome = "INCOMPLETE"
        else:
            outcome = "NOT_RUN"

        transport_outcome = execution.transport_outcome
        reason = execution.reason
        if postcondition_error:
            transport_outcome = "ERROR"
            reason = "POSTCONDITION_DIRTY"
        elif execution.returncode != 0 and not completion_observed:
            transport_outcome = "ERROR"
            reason = reason or "OPENCODE_NONZERO_EXIT"
        elif not found:
            transport_outcome = "ERROR"
            reason = "NO_DURABLE_CAMPAIGN"
        elif outcome == "PASS" and not completion_observed:
            transport_outcome = "ERROR"
            reason = "NO_DURABLE_COMPLETION"

        bridge.write_bridge_status(
            persist_root,
            review_id=review_id,
            campaign_id=campaign_id,
            release_branch=release_branch,
            target_sha=expected_sha,
            verdicts=verdicts,
            outcome=outcome,
            transport_outcome=transport_outcome,
            reason=reason,
            model=execution.model,
            opencode_version=execution.version,
            opencode_returncode=execution.returncode,
            transcript_path=transcript_path,
            first_response_observed=execution.first_response_observed,
            campaign_observed=execution.campaign_observed or found is not None,
            durable_completion_observed=completion_observed,
            started_at=execution.started_at,
            last_activity_at=execution.last_activity_at,
            stalled_at=execution.stalled_at,
        )
        print(
            "EHA BRIDGE RESULT "
            f"campaign={campaign_id} review={review_id} target={expected_sha} "
            f"SIB0={verdicts['SIB0']} SIB1={verdicts['SIB1']} SIB2={verdicts['SIB2']} "
            f"completion={completion_observed} outcome={outcome} "
            f"transport={transport_outcome} reason={reason}",
            flush=True,
        )
        print("PRIVATE EHA TRANSCRIPT AND BRIDGE STATUS RECORDED ON TRUSTED HOST", flush=True)

        if postcondition_error:
            print(f"EHA BRIDGE ERROR: {postcondition_error}", file=sys.stderr)
            return 5
        if transport_outcome != "PASS":
            print(
                "OpenCode transport did not complete cleanly: "
                f"reason={reason} returncode={execution.returncode}; "
                "the prestarted durable campaign and any verdict ledger remain authoritative",
                file=sys.stderr,
            )
            return 7 if execution.reason else 4
        if outcome == "PASS":
            return 0
        if outcome == "FAIL":
            return 2
        return 3
    except (bridge.BridgeError, eha_campaign_bootstrap.BootstrapError) as exc:
        print(f"EHA BRIDGE ERROR: {exc}", file=sys.stderr)
        return 5
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        print(f"EHA BRIDGE ERROR: command failed ({exc.returncode}): {detail}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
