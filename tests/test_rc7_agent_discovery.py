from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
COMMANDS = ROOT / "pack" / ".opencode" / "commands"
MANIFEST = ROOT / "pack" / ".opencode" / "codesleuth-naming.json"
sys.path.insert(0, str(BIN))

import codesleuth_project as lifecycle  # noqa: E402
import playbook_catalog as catalog  # noqa: E402
from codesleuth_naming import load_naming  # noqa: E402
from codesleuth_project.paths import AGENTS_BEGIN, AGENTS_END  # noqa: E402


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def init_repo(path: Path, *, agents_text: str | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    if agents_text is not None:
        (path / "AGENTS.md").write_text(agents_text, encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "init")


def run_installer(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "install.py"), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_normal_install_injects_codesleuth_discovery_map_even_when_workflow_rules_are_off(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    installed = run_installer(repo)
    assert installed.returncode == 0, installed.stderr + installed.stdout

    settings = json.loads((repo / ".opencode" / "review-pack-user.json").read_text(encoding="utf-8"))
    assert settings["policy"]["enforceAgentsMdRules"] is False

    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count(AGENTS_BEGIN) == 1
    assert agents.count(AGENTS_END) == 1
    for expected in (
        ".codesleuth/reports/",
        ".codesleuth/reports/INDEX.md",
        ".opencode/state/reviews/",
        ".opencode/state/context-graphs/",
        ".opencode/playbooks/",
        "/codesleuth/playbooks",
        "/codesleuth/playbook <id>",
        "codesleuth-*",
        "DassaultFalconKing/CodeSleuth",
    ):
        assert expected in agents
    assert "derived" in agents.lower()
    assert "source" in agents.lower()


def test_uninstall_removes_codesleuth_discovery_but_preserves_user_agents_content(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    user_text = "# Repository rules\n\nKeep this exact user guidance.\n"
    init_repo(repo, agents_text=user_text)
    installed = run_installer(repo)
    assert installed.returncode == 0, installed.stderr + installed.stdout
    installed_agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert AGENTS_BEGIN in installed_agents
    assert "/codesleuth/playbooks" in installed_agents

    lifecycle.uninstall_project(repo, preserve_traces=False, source_root=ROOT)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == user_text


def test_naming_authority_exposes_plural_playbook_browse_operation() -> None:
    invocation = load_naming(MANIFEST)["canonical"]["invocation"]
    operation = invocation["operations"]["playbooks"]
    assert operation["path"] == "/codesleuth/playbooks"
    assert operation["compatibilityAliases"] == ["/playbooks"]
    assert (COMMANDS / "codesleuth" / "playbooks.md").is_file()
    assert (COMMANDS / "playbooks.md").is_file()


def test_playbook_catalog_formats_real_records_deterministically(tmp_path: Path) -> None:
    assert hasattr(catalog, "format_playbook_catalog")
    records = catalog.discover_playbooks(tmp_path / "target", ROOT)
    rendered = catalog.format_playbook_catalog(records)
    assert rendered.startswith("CodeSleuth Playbooks\n")
    ids = [record.id for record in records]
    assert ids == sorted(ids)
    for record in records:
        assert f"{record.id} [{record.origin}]" in rendered
        assert f"/codesleuth/playbook {record.id}" in rendered
    first = catalog.format_playbook_catalog(records)
    second = catalog.format_playbook_catalog(list(reversed(records)))
    assert first == second


def test_singular_playbook_command_browses_when_id_is_missing() -> None:
    canonical = (COMMANDS / "codesleuth" / "playbook.md").read_text(encoding="utf-8")
    alias = (COMMANDS / "playbook.md").read_text(encoding="utf-8")
    for text in (canonical, alias):
        assert "If `$1` is empty" in text
        assert "/codesleuth/playbooks" in text
        assert "do not execute" in text.lower()
