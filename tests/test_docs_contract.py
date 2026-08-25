from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_completed_production_handoff_is_archived() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    archived = (ROOT / "docs" / "archive" / "CURSOR-PRODUCTION-HANDOFF.md").read_text(encoding="utf-8")

    assert "Completed implementation packets" in index
    assert "historical evidence only" in index
    assert "Completed historical packet" in archived
    assert "Do not execute this file as a current task" in archived
    assert not (ROOT / "docs" / "CURSOR-PRODUCTION-HANDOFF.md").exists()


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def test_public_introduction_preserves_opencode_execution_ownership() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "USER-GUIDE.md").read_text(encoding="utf-8")
    blurb = _strip_html_comments(
        (ROOT / "docs" / "_includes" / "build-controller-blurb.md").read_text(encoding="utf-8")
    ).strip()

    assert "control panel" in readme
    assert "without replacing OpenCode's models, agents, tools, commands" in readme
    assert "OpenCode remains responsible for models, agents, tools, commands, Skills, and review execution" in guide
    assert "## OpenCode `build` controller" in readme
    assert "OpenCode's primary controller is `build`" in readme
    assert blurb in readme
    assert ".codesleuth/reports/" in readme
    assert ".codesleuth/reports/" in guide


def test_build_controller_docs_link_instead_of_repeating_the_blurb() -> None:
    anchor = "../README.md#opencode-build-controller"
    diagram = "native provider-specific controller prompt"
    docs = [
        ROOT / "docs" / "USER-GUIDE.md",
        ROOT / "docs" / "CODESLEUTH-PRODUCT-CONTRACT.md",
        ROOT / "docs" / "CODESLEUTH-BRANDING.md",
        ROOT / "docs" / "MAINTAINER-SUBREPO.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert anchor in text, f"{path.name} must link to the README controller section"
        assert diagram not in text, f"{path.name} must not copy the controller diagram"


def test_commands_stay_on_opencode_build_and_agents_are_subagents() -> None:
    pack = ROOT / "pack" / ".opencode"
    for name in (
        "repo-review.md",
        "repo-docs.md",
        "repo-review-resume.md",
        "repo-profile.md",
        "repo-prompts.md",
        "repo-report.md",
    ):
        text = (pack / "commands" / name).read_text(encoding="utf-8")
        assert "agent: build" in text
        assert "agent: repo-reviewer" not in text
    for name in (
        "repo-reviewer.md",
        "repo-documenter.md",
        "repo-profile-architect.md",
        "repo-prompt-advisor.md",
        "repo-scout.md",
    ):
        text = (pack / "agents" / name).read_text(encoding="utf-8")
        assert "mode: subagent" in text
        assert "mode: primary" not in text
    cfg = json.loads((pack / "opencode.json").read_text(encoding="utf-8"))
    agent = cfg.get("agent")
    if isinstance(agent, dict):
        build = agent.get("build")
        if isinstance(build, dict):
            assert not str(build.get("prompt") or "").strip()
    reports = (pack / "CODESLEUTH-REPORTS.md").read_text(encoding="utf-8")
    assert ".codesleuth/reports/" in reports
    assert "agent: build" in (pack / "commands" / "repo-report.md").read_text(encoding="utf-8")


def test_bun_smoke_dependency_is_exactly_pinned() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = (ROOT / "bun.lock").read_text(encoding="utf-8")

    assert package["private"] is True
    assert package["devDependencies"]["@opencode-ai/plugin"] == "1.14.48"
    assert "@opencode-ai/plugin" in lock
    assert "1.14.48" in lock


def test_internal_markdown_links_resolve() -> None:
    docs = [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]
    missing: list[str] = []
    for document in docs:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                missing.append(f"{document.relative_to(ROOT)} -> {target}")
    assert not missing, "broken documentation links:\n" + "\n".join(missing)
