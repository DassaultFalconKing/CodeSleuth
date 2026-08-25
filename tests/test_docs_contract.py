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


def test_public_introduction_preserves_opencode_execution_ownership() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "USER-GUIDE.md").read_text(encoding="utf-8")

    assert "control panel" in readme
    assert "without replacing OpenCode's models, agents, tools, commands" in readme
    assert "OpenCode remains responsible for models, agents, tools, commands, Skills, and review execution" in guide


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
