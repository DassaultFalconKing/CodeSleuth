#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import sys

ACTOR_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WATERMARK_RE = re.compile(r"^(?P<actor>[a-z0-9][a-z0-9._-]{1,31})-(?P<digest>[0-9a-f]{12})$")
DOMAIN = "codesleuth-provenance-v1"


def normalize_subject(subject: str) -> str:
    first = subject.splitlines()[0] if subject.splitlines() else ""
    return " ".join(first.strip().lower().split())


def validate_actor(actor: str) -> str:
    value = actor.strip().lower()
    if not ACTOR_RE.fullmatch(value):
        raise ValueError("actor must be 2-32 lowercase [a-z0-9._-] characters")
    return value


def validate_sha(sha: str) -> str:
    value = sha.strip().lower()
    if not SHA_RE.fullmatch(value):
        raise ValueError("SHA must be a full 40-character lowercase Git SHA")
    return value


def digest12(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def commit_watermark(actor: str, parent_sha: str, subject: str) -> str:
    actor = validate_actor(actor)
    parent_sha = validate_sha(parent_sha)
    normalized = normalize_subject(subject)
    if not normalized:
        raise ValueError("commit subject must not be empty")
    digest = digest12(f"{DOMAIN}|commit|{actor}|{parent_sha}|{normalized}")
    return f"{actor}-{digest}"


def historical_s56_v0(parent_sha: str, subject: str) -> str:
    parent_sha = validate_sha(parent_sha)
    normalized = normalize_subject(subject)
    if not normalized:
        raise ValueError("commit subject must not be empty")
    digest = digest12(f"codesleuth-sol56-v1|{parent_sha}|{normalized}")
    return f"s56-{digest}"


def session_watermark(actor: str, head_sha: str, session_id: str) -> str:
    actor = validate_actor(actor)
    head_sha = validate_sha(head_sha)
    session_id = session_id.strip()
    if not session_id:
        raise ValueError("session id must not be empty")
    digest = digest12(f"{DOMAIN}|session|{actor}|{head_sha}|{session_id}")
    return f"{actor}-{digest}"


def parse_watermark(value: str) -> tuple[str, str]:
    match = WATERMARK_RE.fullmatch(value.strip().lower())
    if not match:
        raise ValueError("watermark must be <actor>-<12 lowercase hex>")
    return match.group("actor"), match.group("digest")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute or verify CodeSleuth provenance watermarks")
    sub = parser.add_subparsers(dest="command", required=True)

    commit = sub.add_parser("commit", help="compute a commit Trace-Id watermark")
    commit.add_argument("--actor", required=True)
    commit.add_argument("--parent", required=True)
    commit.add_argument("--subject", required=True)

    session = sub.add_parser("session", help="compute a session/evidence watermark")
    session.add_argument("--actor", required=True)
    session.add_argument("--head", required=True)
    session.add_argument("--session-id", required=True)

    verify = sub.add_parser("verify-commit", help="verify a commit watermark")
    verify.add_argument("--watermark", required=True)
    verify.add_argument("--parent", required=True)
    verify.add_argument("--subject", required=True)
    verify.add_argument("--allow-historical-s56-v0", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "commit":
            print(commit_watermark(args.actor, args.parent, args.subject))
            return 0
        if args.command == "session":
            print(session_watermark(args.actor, args.head, args.session_id))
            return 0
        actor, _ = parse_watermark(args.watermark)
        expected = commit_watermark(actor, args.parent, args.subject)
        if args.watermark.strip().lower() == expected:
            print("PASS")
            return 0
        if args.allow_historical_s56_v0 and actor == "s56":
            if args.watermark.strip().lower() == historical_s56_v0(args.parent, args.subject):
                print("PASS historical-s56-v0")
                return 0
        print(f"FAIL expected {expected}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
