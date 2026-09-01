#!/usr/bin/env python3
"""RC6 trusted EHA controller with deterministic pre-provider campaign bootstrap."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import eha_campaign_bootstrap
import eha_github_bridge as bridge


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
        bootstrap = eha_campaign_bootstrap.start_trusted_campaign(
            root,
            state_dir,
            target_sha=expected_sha,
            target_branch=release_branch,
            scope=scope,
            controller_session=f"github-eha-{bridge.bridge_run_key()}",
            now=started,
        )
        prestarted_campaign = bootstrap["campaign"]
        print(
            "EHA TRUSTED CAMPAIGN BOOTSTRAP "
            f"campaign={prestarted_campaign['campaignId']} review={bootstrap['reviewId']} "
            f"target={expected_sha}",
            flush=True,
        )

        execution = bridge.invoke_opencode(
            root,
            release_branch,
            expected_sha,
            scope,
            model,
            transcript_path,
            state_dir,
            started,
            watchdog,
        )
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
            campaign_observed=True,
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
