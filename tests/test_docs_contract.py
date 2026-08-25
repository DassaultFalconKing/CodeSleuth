from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_TRANSLATIONS = (ROOT / "README.ru.md", ROOT / "README.uk.md")
AGENT_INSTRUCTIONS = ROOT / "AGENTS.md"
LLM_OPERATOR_GUIDE = ROOT / "docs" / "LLM-OPERATOR.md"
README_SOURCE_BLOB_RE = re.compile(r"<!-- README-SOURCE-BLOB: ([0-9a-f]{40}) -->")
README_SWITCH_TARGETS = ("README.md", "README.ru.md", "README.uk.md")


def _git_blob_sha(content: bytes) -> str:
    payload = f"blob {len(content)}\0".encode() + content
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def test_readme_translations_track_current_english_source() -> None:
    source_blob = _git_blob_sha((ROOT / "README.md").read_bytes())
    for path in README_TRANSLATIONS:
        text = path.read_text(encoding="utf-8")
        match = README_SOURCE_BLOB_RE.search(text)
        assert match, f"{path.name} must declare README-SOURCE-BLOB"
        assert match.group(1) == source_blob, (
            f"{path.name} is stale: translate README.md and refresh README-SOURCE-BLOB"
        )


def test_llm_operator_guide_tracks_current_english_source() -> None:
    source_blob = _git_blob_sha((ROOT / "README.md").read_bytes())
    text = LLM_OPERATOR_GUIDE.read_text(encoding="utf-8")
    match = README_SOURCE_BLOB_RE.search(text)
    assert match, "LLM-OPERATOR.md must declare README-SOURCE-BLOB"
    assert match.group(1) == source_blob, (
        "LLM-OPERATOR.md parity is stale: review agent-operational behavior against README.md "
        "and refresh README-SOURCE-BLOB"
    )


def test_agents_entry_point_routes_operator_tasks_to_detailed_guide() -> None:
    text = AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "docs/LLM-OPERATOR.md" in text
    assert "install, configure unattended, use, update, bind, unbind, remove" in text
    assert "second CodeSleuth runtime" in text


def test_llm_operator_guide_keeps_install_config_and_removal_contracts() -> None:
    text = LLM_OPERATOR_GUIDE.read_text(encoding="utf-8")
    required = (
        "--settings-file",
        "--bind-dependency",
        "--update",
        "--uninstall",
        "--purge-traces",
        "--keep-dependency",
        "permissions.managePolicy",
        "review-safe",
        "balanced",
        "autonomous",
        ".opencode/bin/review-pack-smoke.py",
        ".opencode/bin/codesleuth-project . --unbind",
        "second primary controller",
        "release-clean",
    )
    for token in required:
        assert token in text, f"LLM-OPERATOR.md lost required operator contract: {token}"


def test_readme_language_switchers_link_all_other_versions() -> None:
    readmes = (ROOT / "README.md", *README_TRANSLATIONS)
    for path in readmes:
        text = path.read_text(encoding="utf-8")
        assert '<p align="right">' in text, f"{path.name} must keep the top-right language switcher"
        for target in README_SWITCH_TARGETS:
            if target == path.name:
                continue
            assert f'href="./{target}"' in text, f"{path.name} must link to {target}"


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
    assert re.search(r"^#{2,6} OpenCode `build` controller$", readme, flags=re.M)
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
        "repo-map.md",
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
    docs = [AGENT_INSTRUCTIONS, *(ROOT.glob("README*.md")), *((ROOT / "docs").rglob("*.md"))]
    missing: list[str] = []
    for document in docs:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                missing.append(f"{document.relative_to(ROOT)} -> {target}")
    assert not missing, "broken documentation links:\n" + "\n".join(missing)
