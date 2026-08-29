from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402
from codesleuth_report_metadata import (  # noqa: E402
    ReportMetadataError,
    parse_report_metadata,
    relate_to_head,
)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    git(path, "config", "core.autocrlf", "false")
    (path / "README.md").write_text("target\n", encoding="utf-8", newline="\n")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


def commit(repo: Path, name: str, message: str) -> str:
    (repo / name).write_text(f"{message}\n", encoding="utf-8", newline="\n")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def structured_report(
    *,
    report_type: str = "eha",
    target_sha: str,
    provenance: str = "anon",
    extra: dict[str, str] | None = None,
    body: str = "# EHA\n\nbody\n",
) -> str:
    lines = [
        "---",
        f"reportType: {report_type}",
        f"targetSha: {target_sha}",
        f"provenance: {provenance}",
    ]
    for key, value in (extra or {}).items():
        lines.append(f"{key}: {value}")
    lines.extend(["---", "", body])
    return "\n".join(lines)


def write_report(repo: Path, name: str, text: str) -> Path:
    reports = repo / ".codesleuth" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    path = reports / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_legacy_report_without_front_matter_is_unknown() -> None:
    meta = parse_report_metadata("# Title\n\n- targetSha: " + ("a" * 40) + "\n")
    assert meta.kind == "legacy"
    assert meta.target_sha is None


def test_malformed_sha_fail_closed() -> None:
    with pytest.raises(ReportMetadataError, match="malformed SHA"):
        parse_report_metadata(structured_report(target_sha="not-a-sha"))


def test_duplicate_identity_fields_fail_closed() -> None:
    sha = "a" * 40
    text = structured_report(target_sha=sha, extra={"targetSha": "b" * 40})
    with pytest.raises(ReportMetadataError, match="duplicate|conflicting"):
        parse_report_metadata(text)


def test_ambiguous_target_and_base_fail_closed() -> None:
    sha = "a" * 40
    with pytest.raises(ReportMetadataError, match="ambiguous"):
        parse_report_metadata(structured_report(target_sha=sha, extra={"baseSha": sha}))


def test_invalid_lifecycle_reference_fail_closed() -> None:
    sha = "a" * 40
    with pytest.raises(ReportMetadataError, match="lifecycle"):
        parse_report_metadata(structured_report(target_sha=sha, extra={"supersedes": "../secret.md"}))


def test_ghost_index_entry_is_dropped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    reports = lifecycle.ensure_reports_workspace(repo)
    keep = write_report(repo, "20260828T010000Z-keep.md", "# Keep\n")
    lifecycle.update_reports_index(repo, add=keep)
    index = reports / "INDEX.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "- `20260828T020000Z-ghost.md` — ghost\n",
        encoding="utf-8",
    )
    lifecycle.update_reports_index(repo)
    text = index.read_text(encoding="utf-8")
    assert "`20260828T020000Z-ghost.md`" not in text
    assert "`20260828T010000Z-keep.md`" in text
    assert "- `README.md`" not in text
    assert "- `INDEX.md`" not in text


def test_physical_report_appears_in_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    lifecycle.ensure_reports_workspace(repo)
    write_report(repo, "20260828T030000Z-new.md", "# New\n")
    lifecycle.update_reports_index(repo)
    text = (repo / ".codesleuth" / "reports" / "INDEX.md").read_text(encoding="utf-8")
    assert "`20260828T030000Z-new.md`" in text
    assert "legacy" in text


def test_relationships_and_pass_not_transferred(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    root = git(repo, "rev-parse", "HEAD")
    current = git(repo, "branch", "--show-current") or "master"
    git(repo, "checkout", "-b", "topic")
    topic = commit(repo, "topic.txt", "topic")
    git(repo, "checkout", current)
    main_head = commit(repo, "main.txt", "main")
    unknown = "f" * 40

    assert relate_to_head(repo, main_head, main_head) == "EXACT"
    assert relate_to_head(repo, root, main_head) == "ANCESTOR"
    assert relate_to_head(repo, topic, root) == "DESCENDANT"
    assert relate_to_head(repo, topic, main_head) == "DIVERGED"
    assert relate_to_head(repo, unknown, main_head) == "UNKNOWN"

    write_report(
        repo,
        "20260828T040000Z-eha.md",
        structured_report(
            target_sha=root,
            extra={
                "verdict": "PASS",
                "reviewId": "rev-1",
                "ehaCampaignId": "EHA-1",
                "supersedes": "20260827T010000Z-old.md",
                "closedBySha": main_head,
                "regressionTest": "tests/test_reports_index.py::test_ghost_index_entry_is_dropped",
            },
        ),
    )
    write_report(
        repo,
        "20260828T040500Z-topic.md",
        structured_report(target_sha=topic, extra={"verdict": "FAIL"}),
    )
    lifecycle.update_reports_index(repo, current_head=main_head)
    text = (repo / ".codesleuth" / "reports" / "INDEX.md").read_text(encoding="utf-8")
    assert "eha" in text
    assert root in text
    assert "ANCESTOR" in text
    assert "DIVERGED" in text
    assert "PASS on exact" in text
    assert "acceptance not transferred" in text
    assert f"PASS on exact {main_head}" not in text
    assert "supersedes 20260827T010000Z-old.md" in text
    assert "closedBy" in text


def test_index_shows_descendant_relationship(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    root = git(repo, "rev-parse", "HEAD")
    child = commit(repo, "child.txt", "child")
    write_report(
        repo,
        "20260828T041000Z-future.md",
        structured_report(target_sha=child, extra={"verdict": "PENDING"}),
    )
    lifecycle.update_reports_index(repo, current_head=root)
    text = (repo / ".codesleuth" / "reports" / "INDEX.md").read_text(encoding="utf-8")
    assert "DESCENDANT" in text
    assert child in text


def test_exact_pass_stays_pass_on_matching_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    head = git(repo, "rev-parse", "HEAD")
    write_report(
        repo,
        "20260828T050000Z-eha.md",
        structured_report(target_sha=head, extra={"verdict": "PASS"}),
    )
    lifecycle.update_reports_index(repo)
    text = (repo / ".codesleuth" / "reports" / "INDEX.md").read_text(encoding="utf-8")
    assert "EXACT" in text
    assert "acceptance not transferred" not in text
    assert "PASS" in text


def test_index_does_not_touch_review_ledgers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    ledger = repo / ".opencode" / "state" / "reviews" / "rid" / "eha.ndjson"
    ledger.parent.mkdir(parents=True)
    payload = '{"keep":true}\n'
    ledger.write_text(payload, encoding="utf-8")
    write_report(repo, "20260828T060000Z-note.md", "# Note\n")
    lifecycle.update_reports_index(repo)
    assert ledger.read_text(encoding="utf-8") == payload
    assert list(ledger.parent.iterdir()) == [ledger]
