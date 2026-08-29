"""Canonical Skill publication routes. Delegates Git writes to the bounded reports publisher."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codesleuth_report_metadata import SHA_RE, is_report_filename, parse_report_metadata
from codesleuth_reports import publish_shared_report

ROUTES_NAME = "publication-routes.json"
ALLOWED_STATES = ("NOT_REQUESTED", "PASS", "FAILED")
REVIEWS_PREFIX = ".opencode/state/reviews/"


class PublicationError(ValueError):
    """Fail-closed publication-route or artifact contract violation."""


def _routes_path() -> Path:
    return Path(__file__).resolve().parents[1] / ROUTES_NAME


def load_publication_routes() -> dict[str, dict[str, str]]:
    payload = json.loads(_routes_path().read_text(encoding="utf-8"))
    routes = payload.get("routes")
    if not isinstance(routes, dict) or "reports" not in routes:
        raise PublicationError("canonical publication route registry is missing reports")
    return {key: dict(value) for key, value in routes.items()}


def resolve_publication_route(route: str) -> dict[str, str]:
    if not route or route != route.strip() or "/" in route or ":" in route:
        raise PublicationError(f"unknown publication route: {route!r}")
    routes = load_publication_routes()
    spec = routes.get(route)
    if spec is None:
        raise PublicationError(f"unknown publication route: {route!r}")
    if spec.get("publisher") != "codesleuth_reports" or spec.get("branch") != "reports":
        raise PublicationError(f"publication route {route!r} is not bound to the reports publisher")
    return spec


def skill_publication_route(skill_path: Path) -> str | None:
    """Return the declared route from Skill front matter. Reject a free-form branch field."""
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    closer = text.find("\n---", 3)
    if closer < 0:
        raise PublicationError(f"malformed Skill front matter: {skill_path}")
    block = text[4:closer]
    route: str | None = None
    for raw in block.splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "branch":
            raise PublicationError("Skill must not declare a free-form branch field")
        if key == "publicationRoute":
            if route is not None:
                raise PublicationError("duplicate publicationRoute declaration")
            route = value
    if route:
        resolve_publication_route(route)
    return route


def playbook_publication_route(playbook_dir: Path) -> str | None:
    manifest = json.loads((playbook_dir / "playbook.json").read_text(encoding="utf-8"))
    if "branch" in manifest:
        raise PublicationError("Playbook must not declare a free-form branch field")
    route = manifest.get("publication_route")
    if route is None:
        return None
    if not isinstance(route, str):
        raise PublicationError("malformed publication_route")
    return resolve_publication_route(route)["id"]


def _require_sha(field: str, value: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise PublicationError(f"exact {field} is required")
    return value


def _artifact_front_matter(
    *,
    skill_id: str,
    target_sha: str,
    codesleuth_source_sha: str,
    repository_identity: str,
    provenance: str,
    created_at: str,
    review_id: str | None,
) -> str:
    lines = [
        "---",
        "reportType: skill-result",
        f"targetSha: {target_sha}",
        f"provenance: {provenance}",
        f"skillId: {skill_id}",
        f"codesleuthSourceSha: {codesleuth_source_sha}",
        f"repositoryIdentity: {repository_identity}",
        f"createdAt: {created_at}",
    ]
    if review_id:
        lines.append(f"reviewId: {review_id}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def publish_skill_result(
    repo: Path,
    *,
    route: str,
    publish: bool,
    skill_id: str,
    body: str,
    target_sha: str,
    codesleuth_source_sha: str,
    repository_identity: str,
    provenance: str,
    review_id: str | None = None,
    created_at: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Publish one Skill artifact through a declared route, or record NOT_REQUESTED.

    Analysis is assumed already PASS when this is called. Publication failure does
    not rewrite that analysis, but it forbids a remote-success claim.
    """
    if branch is not None:
        raise PublicationError("model-supplied branch names are rejected")
    target_sha = _require_sha("targetSha", target_sha)
    codesleuth_source_sha = _require_sha("codesleuthSourceSha", codesleuth_source_sha)
    if not publish:
        return {
            "analysis": "PASS",
            "publication": "NOT_REQUESTED",
            "route": None,
            "applicationHead": None,
        }
    spec = resolve_publication_route(route)
    created = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = _artifact_front_matter(
        skill_id=skill_id,
        target_sha=target_sha,
        codesleuth_source_sha=codesleuth_source_sha,
        repository_identity=repository_identity,
        provenance=provenance,
        created_at=created,
        review_id=review_id,
    ) + body.lstrip("\n")
    parse_report_metadata(text)
    reports = repo / ".codesleuth" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{skill_id}.md"
    if not is_report_filename(name):
        raise PublicationError(f"skill id cannot form a timestamped report name: {skill_id}")
    path = reports / name
    if REVIEWS_PREFIX in path.as_posix():
        raise PublicationError("review/EHA ledgers cannot be published")
    path.write_text(text, encoding="utf-8", newline="\n")
    try:
        result = publish_shared_report(repo, path)
    except Exception as exc:
        return {
            "analysis": "PASS",
            "publication": "FAILED",
            "route": spec["id"],
            "error": str(exc),
            "report": path.relative_to(repo).as_posix() if path.is_file() else None,
        }
    return {
        "analysis": "PASS",
        "publication": "PASS",
        "route": spec["id"],
        "report": result.get("report"),
        "commit": result.get("commit"),
        "publishedRemote": result.get("publishedRemote"),
        "applicationHead": result.get("applicationHead"),
    }
