"""Strict derived-report metadata and HEAD-relationship read model.

Markdown reports and INDEX.md remain navigation/handoff material. Exact Git
source and structured review/EHA ledgers stay authority. This module never
reads or rewrites ``.opencode/state/reviews/**``.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPORT_NAME_RE = re.compile(
    r"^(?:\d{8}T\d{4}(?:\d{2})?Z|\d{4}-\d{2}-\d{2}T\d{4}Z)-"
    r"[a-z0-9][a-z0-9-]*\.md$"
)
REPORT_TYPE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
PROVENANCE_RE = re.compile(
    r"^(?:anon|unavailable|[a-z0-9][a-z0-9._-]{1,31}-[0-9a-f]{12})$"
)
REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
RELATIVE_PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:\\-]*$")
IDENTITY_KEYS = frozenset({"targetSha", "baseSha", "closedBySha"})
REQUIRED_KEYS = ("reportType", "targetSha", "provenance")
ALLOWED_KEYS = frozenset(
    {
        "reportType",
        "targetSha",
        "baseSha",
        "verdict",
        "reviewId",
        "ehaCampaignId",
        "provenance",
        "findingIds",
        "supersedes",
        "supersededBy",
        "closedBySha",
        "regressionTest",
        "skillId",
        "codesleuthSourceSha",
        "repositoryIdentity",
        "createdAt",
    }
)
SKILL_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FLOATING_IDENTITY = frozenset({"main", "master", "head", "origin/main", "origin/master", "sib"})
RELATIONSHIPS = ("EXACT", "ANCESTOR", "DESCENDANT", "DIVERGED", "UNKNOWN")


class ReportMetadataError(ValueError):
    """Fail-closed metadata contract violation."""


@dataclass(frozen=True)
class ReportMetadata:
    kind: str
    report_type: str | None = None
    target_sha: str | None = None
    base_sha: str | None = None
    verdict: str | None = None
    review_id: str | None = None
    eha_campaign_id: str | None = None
    provenance: str | None = None
    finding_ids: tuple[str, ...] = ()
    supersedes: str | None = None
    superseded_by: str | None = None
    closed_by_sha: str | None = None
    regression_test: str | None = None


LEGACY_METADATA = ReportMetadata(kind="legacy")


def is_report_filename(name: str) -> bool:
    return bool(REPORT_NAME_RE.fullmatch(name))


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=check,
    )


def _require_sha(field: str, value: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise ReportMetadataError(f"malformed SHA in {field}")
    return value


def _require_report_ref(field: str, value: str) -> str:
    if not is_report_filename(value):
        raise ReportMetadataError(f"invalid lifecycle reference in {field}: {value}")
    return value


def _require_relative_path(field: str, value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not RELATIVE_PATH_RE.fullmatch(value.replace("\\", "/")):
        raise ReportMetadataError(f"invalid lifecycle reference in {field}: {value}")
    return value.replace("\\", "/")


def split_front_matter(text: str) -> tuple[dict[str, str] | None, str]:
    """Return (parsed mapping or None, body). ``None`` means legacy/no block."""
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---"):
        return None, text
    rest = text[3:]
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    else:
        raise ReportMetadataError("malformed report metadata block")
    closer = re.search(r"\n---[ \t]*(?:\r?\n|$)", rest)
    if closer is None:
        raise ReportMetadataError("malformed report metadata block")
    raw = rest[: closer.start()]
    body = rest[closer.end() :]
    mapping: dict[str, str] = {}
    for line_no, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in raw_line:
            raise ReportMetadataError(f"malformed metadata line {line_no}")
        key, _, value = raw_line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ReportMetadataError(f"malformed metadata line {line_no}")
        if key in mapping:
            if mapping[key] != value:
                raise ReportMetadataError(f"conflicting duplicate key {key}")
            raise ReportMetadataError(f"duplicate identity field {key}")
        mapping[key] = value
    return mapping, body


def parse_report_metadata(text: str) -> ReportMetadata:
    """Parse machine-readable report metadata. Fail closed on a present but invalid block."""
    mapping, _body = split_front_matter(text)
    if mapping is None:
        return LEGACY_METADATA
    unknown = sorted(set(mapping) - ALLOWED_KEYS)
    if unknown:
        raise ReportMetadataError("unknown metadata keys: " + ", ".join(unknown))
    for required in REQUIRED_KEYS:
        if required not in mapping:
            raise ReportMetadataError(f"missing required metadata field {required}")
    identity_hits = [key for key in IDENTITY_KEYS if key in mapping]
    if len(identity_hits) > 1 and mapping.get("targetSha") == mapping.get("baseSha"):
        raise ReportMetadataError("ambiguous duplicate identity fields")
    if not REPORT_TYPE_RE.fullmatch(mapping["reportType"]):
        raise ReportMetadataError("malformed reportType")
    if not PROVENANCE_RE.fullmatch(mapping["provenance"]):
        raise ReportMetadataError("malformed provenance")
    finding_ids: tuple[str, ...] = ()
    if "findingIds" in mapping:
        parts = [item.strip() for item in mapping["findingIds"].split(",") if item.strip()]
        if not parts:
            raise ReportMetadataError("malformed findingIds")
        for item in parts:
            if not FINDING_ID_RE.fullmatch(item):
                raise ReportMetadataError(f"malformed findingIds value {item}")
        finding_ids = tuple(parts)
    for field in ("reviewId", "ehaCampaignId"):
        if field in mapping and not REVIEW_ID_RE.fullmatch(mapping[field]):
            raise ReportMetadataError(f"malformed {field}")
    if "verdict" in mapping and not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,31}", mapping["verdict"]):
        raise ReportMetadataError("malformed verdict")
    if "skillId" in mapping and not SKILL_ID_RE.fullmatch(mapping["skillId"]):
        raise ReportMetadataError("malformed skillId")
    if "codesleuthSourceSha" in mapping:
        _require_sha("codesleuthSourceSha", mapping["codesleuthSourceSha"])
    if "repositoryIdentity" in mapping:
        ident = mapping["repositoryIdentity"].strip()
        if not ident or ident.lower() in FLOATING_IDENTITY:
            raise ReportMetadataError("floating branch/ref cannot replace repository identity")
    if "createdAt" in mapping and not CREATED_AT_RE.fullmatch(mapping["createdAt"]):
        raise ReportMetadataError("malformed createdAt")
    if mapping["reportType"] == "skill-result":
        for required in ("skillId", "codesleuthSourceSha", "repositoryIdentity", "createdAt"):
            if required not in mapping:
                raise ReportMetadataError(f"missing required metadata field {required}")
    return ReportMetadata(
        kind="structured",
        report_type=mapping["reportType"],
        target_sha=_require_sha("targetSha", mapping["targetSha"]),
        base_sha=_require_sha("baseSha", mapping["baseSha"]) if "baseSha" in mapping else None,
        verdict=mapping.get("verdict"),
        review_id=mapping.get("reviewId"),
        eha_campaign_id=mapping.get("ehaCampaignId"),
        provenance=mapping["provenance"],
        finding_ids=finding_ids,
        supersedes=_require_report_ref("supersedes", mapping["supersedes"]) if "supersedes" in mapping else None,
        superseded_by=_require_report_ref("supersededBy", mapping["supersededBy"]) if "supersededBy" in mapping else None,
        closed_by_sha=_require_sha("closedBySha", mapping["closedBySha"]) if "closedBySha" in mapping else None,
        regression_test=_require_relative_path("regressionTest", mapping["regressionTest"])
        if "regressionTest" in mapping
        else None,
    )


def parse_report_file(path: Path) -> ReportMetadata:
    return parse_report_metadata(path.read_text(encoding="utf-8"))


def _object_state(repo: Path, sha: str) -> str:
    proc = _git(repo, "cat-file", "-e", sha, check=False)
    if proc.returncode == 0:
        return "present"
    err = f"{proc.stderr} {proc.stdout}".lower()
    if proc.returncode in {1, 128} and any(
        token in err for token in ("bad object", "not found", "does not exist", "exists", "invalid")
    ):
        return "missing"
    if proc.returncode in {1, 128}:
        return "missing"
    return "unreadable"


def relate_to_head(repo: Path, target_sha: str | None, current_head: str | None) -> str:
    """Derive EXACT/ANCESTOR/DESCENDANT/DIVERGED/UNKNOWN from Git ancestry."""
    if not target_sha or not current_head or not SHA_RE.fullmatch(target_sha) or not SHA_RE.fullmatch(current_head):
        return "UNKNOWN"
    if target_sha == current_head:
        return "EXACT"
    target_state = _object_state(repo, target_sha)
    head_state = _object_state(repo, current_head)
    if target_state == "unreadable" or head_state == "unreadable":
        return "UNKNOWN"
    if target_state != "present" or head_state != "present":
        return "UNKNOWN"
    ancestor = _git(repo, "merge-base", "--is-ancestor", target_sha, current_head, check=False)
    if ancestor.returncode == 0:
        return "ANCESTOR"
    if ancestor.returncode not in {0, 1}:
        return "UNKNOWN"
    descendant = _git(repo, "merge-base", "--is-ancestor", current_head, target_sha, check=False)
    if descendant.returncode == 0:
        return "DESCENDANT"
    if descendant.returncode not in {0, 1}:
        return "UNKNOWN"
    return "DIVERGED"


def acceptance_status(meta: ReportMetadata, relationship: str) -> str:
    """Render verdict without transferring PASS onto a non-exact HEAD."""
    if meta.kind != "structured":
        return "unknown"
    if not meta.verdict:
        return "unknown"
    if meta.verdict.upper() == "PASS" and relationship != "EXACT":
        short = (meta.target_sha or "")[:12]
        return f"PASS on exact {short}; {relationship} of current; acceptance not transferred"
    return meta.verdict


def lifecycle_navigation(meta: ReportMetadata) -> str:
    if meta.kind != "structured":
        return ""
    parts: list[str] = []
    if meta.supersedes:
        parts.append(f"supersedes {meta.supersedes}")
    if meta.superseded_by:
        parts.append(f"supersededBy {meta.superseded_by}")
    if meta.closed_by_sha:
        parts.append(f"closedBy {meta.closed_by_sha[:12]}")
    if meta.regression_test:
        parts.append(f"reg {meta.regression_test}")
    return "; ".join(parts)


def index_fields(meta: ReportMetadata, relationship: str) -> dict[str, str]:
    if meta.kind != "structured":
        return {
            "report_type": "legacy",
            "target_sha": "unknown",
            "status": "unknown",
            "relationship": "UNKNOWN",
            "lifecycle": "",
        }
    status = acceptance_status(meta, relationship)
    nav = lifecycle_navigation(meta)
    if nav:
        status = f"{status} ({nav})" if status else nav
    return {
        "report_type": meta.report_type or "legacy",
        "target_sha": meta.target_sha or "unknown",
        "status": status,
        "relationship": relationship,
        "lifecycle": nav,
    }


def verify_index_matches_files(reports: Path) -> None:
    """Fail closed if INDEX.md lists anything other than physical timestamped reports."""
    index = reports / "INDEX.md"
    if not index.is_file():
        raise RuntimeError("reports INDEX.md is missing")
    listed: set[str] = set()
    for line in index.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- `([^`]+)`", line.strip())
        if match and is_report_filename(match.group(1)):
            listed.add(match.group(1))
    physical = {path.name for path in reports.iterdir() if path.is_file() and is_report_filename(path.name)}
    if listed != physical:
        raise RuntimeError("reports INDEX does not match timestamped files on disk")


def resolve_current_head(repo: Path, current_head: str | None = None) -> str | None:
    if current_head:
        return current_head if SHA_RE.fullmatch(current_head) else None
    proc = _git(repo, "rev-parse", "HEAD", check=False)
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value if SHA_RE.fullmatch(value) else None
