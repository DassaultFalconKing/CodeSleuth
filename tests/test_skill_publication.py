from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BIN))
import codesleuth_publication as publication  # noqa: E402
import codesleuth_reports as shared_reports  # noqa: E402
from codesleuth_publication import PublicationError  # noqa: E402


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=check,
    )


def init_remote(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "CodeSleuth Test")
    git(repo, "config", "core.autocrlf", "false")
    (repo / "README.md").write_text("application\n", encoding="utf-8", newline="\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "init")
    git(repo, "push", "origin", "HEAD:main")
    return remote, repo


def sha(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def publish_kwargs(repo: Path, skill_id: str, body: str, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "route": "reports",
        "publish": True,
        "skill_id": skill_id,
        "body": body,
        "target_sha": sha(repo),
        "codesleuth_source_sha": "a" * 40,
        "repository_identity": f"file://{repo.resolve().as_posix()}",
        "provenance": "anon",
        "created_at": "2026-08-28T12:00:00Z",
        "review_id": "rev-skill-1",
    }
    values.update(overrides)
    return values


def test_reports_route_is_canonical_and_unknown_rejected() -> None:
    spec = publication.resolve_publication_route("reports")
    assert spec["branch"] == "reports"
    assert spec["pathPrefix"] == ".codesleuth/reports/"
    with pytest.raises(PublicationError, match="unknown publication route"):
        publication.resolve_publication_route("foo")


def test_skill_declaration_uses_route_and_rejects_branch_field(tmp_path: Path) -> None:
    skill = ROOT / "pack" / ".opencode" / "skills" / "codesleuth-reports" / "SKILL.md"
    assert publication.skill_publication_route(skill) == "reports"
    rogue = tmp_path / "SKILL.md"
    rogue.write_text("---\nname: rogue\nbranch: whatever\nslash: true\n---\n", encoding="utf-8")
    with pytest.raises(PublicationError, match="branch"):
        publication.skill_publication_route(rogue)
    playbook = ROOT / "pack" / ".opencode" / "playbooks" / "repository-map"
    assert publication.playbook_publication_route(playbook) == "reports"


def test_model_supplied_branch_is_rejected(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    with pytest.raises(PublicationError, match="branch"):
        publication.publish_skill_result(repo, **publish_kwargs(repo, "alpha", "# A\n"), branch="evil")


def test_agent_policy_still_denies_arbitrary_git_push() -> None:
    config = json.loads((ROOT / "pack" / ".opencode" / "opencode.json").read_text(encoding="utf-8"))
    assert config["permission"]["bash"]["git push*"] == "deny"
    source = (ROOT / "pack" / ".opencode" / "bin" / "codesleuth_publication.py").read_text(encoding="utf-8")
    assert "git push" not in source
    assert "publish_shared_report" in source


def test_publish_reports_route_and_second_clone(tmp_path: Path) -> None:
    remote, first = init_remote(tmp_path)
    app_head = sha(first)
    result = publication.publish_skill_result(first, **publish_kwargs(first, "documentation-draft", "# Docs\nresult one\n"))
    assert result["analysis"] == "PASS"
    assert result["publication"] == "PASS"
    assert result["route"] == "reports"
    assert result["applicationHead"] == app_head
    assert git(first, "rev-parse", "HEAD").stdout.strip() == app_head
    report_text = (first / result["report"]).read_text(encoding="utf-8")
    assert "reportType: skill-result" in report_text
    assert f"targetSha: {app_head}" in report_text
    assert "codesleuthSourceSha: " + ("a" * 40) in report_text
    assert "skillId: documentation-draft" in report_text
    assert "createdAt: 2026-08-28T12:00:00Z" in report_text

    second_skill = publication.publish_skill_result(first, **publish_kwargs(first, "codesleuth-reports", "# Reports\nresult two\n"))
    assert second_skill["publication"] == "PASS"
    names = git(first, "ls-tree", "-r", "--name-only", "reports").stdout
    assert "documentation-draft.md" in names
    assert "codesleuth-reports.md" in names
    assert ".opencode/state/reviews" not in names

    second = tmp_path / "second"
    subprocess.run(["git", "clone", str(remote), str(second)], check=True, capture_output=True)
    git(second, "checkout", "main")
    synced = shared_reports.sync_shared_reports(second)
    assert synced["status"] == "synced"
    imported = list((second / ".codesleuth" / "reports").glob("*-documentation-draft.md"))
    assert imported
    assert "result one" in imported[0].read_text(encoding="utf-8")
    assert git(second, "rev-parse", "HEAD").stdout.strip() == app_head


def test_publication_not_requested_leaves_head_and_remote_untouched(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    app_head = sha(repo)
    kwargs = publish_kwargs(repo, "documentation-draft", "# Docs\n")
    kwargs["publish"] = False
    result = publication.publish_skill_result(repo, **kwargs)
    assert result == {
        "analysis": "PASS",
        "publication": "NOT_REQUESTED",
        "route": None,
        "applicationHead": None,
    }
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == app_head
    assert git(repo, "rev-parse", "--verify", "refs/heads/reports", check=False).returncode != 0


def test_publication_failure_keeps_analysis_pass(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    result = publication.publish_skill_result(
        repo,
        **publish_kwargs(repo, "documentation-draft", "Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345\n"),
    )
    assert result["analysis"] == "PASS"
    assert result["publication"] == "FAILED"
    assert "secret scanner" in (result.get("error") or "")


def test_collision_and_missing_provenance_fail_closed(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    first = publication.publish_skill_result(
        repo,
        **publish_kwargs(repo, "alpha", "# One\n", created_at="2026-08-28T12:00:00Z"),
    )
    assert first["publication"] == "PASS"
    path = repo / first["report"]
    path.write_text(path.read_text(encoding="utf-8").replace("result", "changed") if "result" in path.read_text(encoding="utf-8") else path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    with pytest.raises(Exception, match="collision"):
        shared_reports.publish_shared_report(repo, path)
    with pytest.raises(PublicationError, match="exact codesleuthSourceSha"):
        publication.publish_skill_result(repo, **publish_kwargs(repo, "beta", "# Two\n", codesleuth_source_sha="main"))


def test_contaminated_reports_branch_and_ledgers_are_not_published(tmp_path: Path) -> None:
    _, repo = init_remote(tmp_path)
    git(repo, "branch", "reports", "HEAD")
    result = publication.publish_skill_result(repo, **publish_kwargs(repo, "alpha", "# A\n"))
    assert result["analysis"] == "PASS"
    assert result["publication"] == "FAILED"
    assert "non-report paths" in (result.get("error") or "")
    ledger = repo / ".opencode" / "state" / "reviews" / "rid" / "eha.ndjson"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("keep\n", encoding="utf-8")
    clean = tmp_path / "clean"
    _remote, first = init_remote(clean)
    ledger2 = first / ".opencode" / "state" / "reviews" / "rid" / "eha.ndjson"
    ledger2.parent.mkdir(parents=True)
    ledger2.write_text("keep\n", encoding="utf-8")
    published = publication.publish_skill_result(first, **publish_kwargs(first, "alpha", "# A\n"))
    assert published["publication"] == "PASS"
    tree = git(first, "ls-tree", "-r", "--name-only", "reports").stdout
    assert ".opencode/state/reviews" not in tree
    assert ledger2.read_text(encoding="utf-8") == "keep\n"
