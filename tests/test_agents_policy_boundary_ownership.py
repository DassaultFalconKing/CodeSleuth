from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
from codesleuth_project.agents_policy import (  # noqa: E402
    POLICY_BEGIN,
    POLICY_END,
    canonical_policy_text,
    ensure_agents_rules,
    remove_agents_rules,
)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


@pytest.mark.parametrize(
    "original",
    [
        b"# no final newline",
        b"   ",
        b"\n\n",
        b"\r\n\r\n",
        b"",
    ],
)
def test_existing_agents_round_trips_exact_bytes(original: bytes, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    agents = repo / "AGENTS.md"
    agents.write_bytes(original)

    ensure_agents_rules(repo, canonical_policy_text())
    installed = agents.read_bytes()
    assert POLICY_BEGIN.encode() in installed
    assert POLICY_END.encode() in installed

    remove_agents_rules(repo)
    assert agents.is_file(), "pre-existing AGENTS.md must never be deleted"
    assert agents.read_bytes() == original


def test_boundary_ownership_is_explicit_and_anchored(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    agents = repo / "AGENTS.md"
    agents.write_bytes(b"user text")

    ensure_agents_rules(repo, canonical_policy_text())
    state = json.loads((repo / ".opencode" / "state" / "agents-policy.json").read_text(encoding="utf-8"))
    assert state["schemaVersion"] == 3
    assert state["createdByCodesleuth"] is False
    assert state["ownedPrefix"] == "\n"
    assert state["ownedSuffix"] == "\n"
    assert state["prefixAnchorHash"]
    assert state["suffixAnchorHash"]

    remove_agents_rules(repo)
    assert agents.read_bytes() == b"user text"


def test_lost_state_never_guesses_boundary_ownership_or_deletes_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    agents = repo / "AGENTS.md"
    agents.write_bytes(b"user text")

    ensure_agents_rules(repo, canonical_policy_text())
    (repo / ".opencode" / "state" / "agents-policy.json").unlink()
    remove_agents_rules(repo)

    assert agents.is_file()
    remaining = agents.read_bytes()
    assert b"user text" in remaining
    assert POLICY_BEGIN.encode() not in remaining
    assert POLICY_END.encode() not in remaining


def test_user_edit_to_owned_prefix_revokes_separator_removal(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    agents = repo / "AGENTS.md"
    agents.write_bytes(b"user text")
    ensure_agents_rules(repo, canonical_policy_text())

    text = agents.read_text(encoding="utf-8")
    text = text.replace("user text\n" + POLICY_BEGIN, "user text\r\n" + POLICY_BEGIN, 1)
    agents.write_text(text, encoding="utf-8", newline="")

    remove_agents_rules(repo)
    assert agents.is_file()
    assert agents.read_bytes().startswith(b"user text\r\n")


def test_user_insert_after_block_is_never_mistaken_for_owned_suffix(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    agents = repo / "AGENTS.md"
    agents.write_bytes(b"user text\n")
    ensure_agents_rules(repo, canonical_policy_text())

    text = agents.read_text(encoding="utf-8")
    end = text.index(POLICY_END) + len(POLICY_END)
    user_tail = "\n\n# user section after managed block\n"
    agents.write_text(text[:end] + user_tail + text[end:], encoding="utf-8", newline="")

    remove_agents_rules(repo)
    restored = agents.read_text(encoding="utf-8")
    assert restored.startswith("user text\n")
    assert user_tail in restored
    assert POLICY_BEGIN not in restored
    assert POLICY_END not in restored
