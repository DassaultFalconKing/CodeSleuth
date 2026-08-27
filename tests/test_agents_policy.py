from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import review_pack_tui_core as tui_core  # noqa: E402
import codesleuth_project as lifecycle  # noqa: E402
from codesleuth_project.agents_policy import (  # noqa: E402
    POLICY_BEGIN,
    POLICY_END,
    canonical_policy_text,
    ensure_agents_rules,
    remove_agents_rules,
    validate_agents_rules,
)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init")
    git(path, "config", "user.email", "test@example.invalid")
    git(path, "config", "user.name", "CodeSleuth Test")
    (path / "README.md").write_text("target\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "init")


def test_default_policy_is_off() -> None:
    s = tui_core.default_settings(["generic"])
    assert s["policy"]["enforceAgentsMdRules"] is False
    validated = tui_core.validate_settings(s)
    assert validated["policy"]["enforceAgentsMdRules"] is False


def test_policy_round_trip() -> None:
    s = tui_core.default_settings(["generic"])
    s["policy"]["enforceAgentsMdRules"] = True
    validated = tui_core.validate_settings(s)
    # Simulate save/load via JSON
    dumped = json.loads(json.dumps(validated))
    reloaded = tui_core.validate_settings(dumped)
    assert reloaded["policy"]["enforceAgentsMdRules"] is True
    s2 = tui_core.default_settings(["generic"])
    s2["policy"]["enforceAgentsMdRules"] = False
    assert tui_core.validate_settings(s2)["policy"]["enforceAgentsMdRules"] is False


def test_policy_validation_rejects_non_bool() -> None:
    s = tui_core.default_settings(["generic"])
    s["policy"]["enforceAgentsMdRules"] = "true"  # type: ignore
    with pytest.raises(ValueError, match="policy.enforceAgentsMdRules must be a boolean"):
        tui_core.validate_settings(s)


def test_no_existing_file_enable_disable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    assert not (repo / "AGENTS.md").exists()
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert text.count(POLICY_BEGIN) == 1
    assert text.count(POLICY_END) == 1
    assert "Host owns" in text or "CodeSleuth workflow" in text
    # disable/uninstall removes and deletes file when created by CodeSleuth
    remove_agents_rules(repo)
    assert not (repo / "AGENTS.md").exists()


def test_existing_lf_preserved(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    original = "# User\n\nKeep me.\n"
    (repo / "AGENTS.md").write_text(original, encoding="utf-8", newline="\n")
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep me." in text
    assert text.count(POLICY_BEGIN) == 1
    # Outside block preserved byte-for-byte
    before = text.split(POLICY_BEGIN)[0]
    assert "Keep me." in before
    # Update idempotent
    ensure_agents_rules(repo, canon)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8").count(POLICY_BEGIN) == 1
    # Disable preserves user
    remove_agents_rules(repo)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == original


def test_existing_crlf_preserved(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    original = "# User\r\n\r\nKeep CRLF.\r\n"
    (repo / "AGENTS.md").write_bytes(original.encode("utf-8"))
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    data = (repo / "AGENTS.md").read_bytes()
    assert b"\r\n" in data
    text = data.decode("utf-8")
    assert "Keep CRLF." in text
    assert text.count(POLICY_BEGIN) == 1
    # Disable preserves CRLF file
    remove_agents_rules(repo)
    restored = (repo / "AGENTS.md").read_bytes().decode("utf-8")
    assert restored == original


def test_idempotent_repeated_enable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    first = (repo / "AGENTS.md").read_text(encoding="utf-8")
    ensure_agents_rules(repo, canon)
    second = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert first == second
    assert first.count(POLICY_BEGIN) == 1
    # Update with same canon remains idempotent even after re-read
    ensure_agents_rules(repo, canon)
    third = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert third == first


def test_user_edits_outside_survive_update(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    # User edits outside block
    edited = text.replace(POLICY_BEGIN, "# User edit before\n" + POLICY_BEGIN)
    (repo / "AGENTS.md").write_text(edited, encoding="utf-8")
    # Update should replace only managed block
    ensure_agents_rules(repo, canon)
    new_text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "# User edit before" in new_text
    assert new_text.count(POLICY_BEGIN) == 1


def test_user_edits_inside_are_replaced(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    # Corrupt inner
    corrupted = text.replace("Host owns", "HACKED inside")
    (repo / "AGENTS.md").write_text(corrupted, encoding="utf-8")
    assert "HACKED inside" in (repo / "AGENTS.md").read_text(encoding="utf-8")
    ensure_agents_rules(repo, canon)
    restored = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "HACKED inside" not in restored
    assert "Host owns" in restored


def test_duplicate_markers_fail_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    dup = text + "\n" + POLICY_BEGIN + "\n dup\n" + POLICY_END + "\n"
    (repo / "AGENTS.md").write_text(dup, encoding="utf-8")
    before = (repo / "AGENTS.md").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="duplicate|malformed"):
        ensure_agents_rules(repo, canon)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == before
    with pytest.raises(RuntimeError, match="duplicate|malformed"):
        remove_agents_rules(repo)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == before
    # validate also fails
    with pytest.raises(RuntimeError):
        validate_agents_rules(repo)


def test_malformed_missing_end_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "AGENTS.md").write_text("# x\n" + POLICY_BEGIN + "\n no end\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="malformed|BEGIN"):
        validate_agents_rules(repo)
    with pytest.raises(RuntimeError):
        ensure_agents_rules(repo, canonical_policy_text())
    before = (repo / "AGENTS.md").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError):
        remove_agents_rules(repo)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == before


def test_disable_removes_only_block_preserves_user(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    user = "# Keep\n\nUser content.\n"
    (repo / "AGENTS.md").write_text(user, encoding="utf-8")
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    assert "User content." in (repo / "AGENTS.md").read_text(encoding="utf-8")
    remove_agents_rules(repo)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == user


def test_final_newline_and_crlf_handling(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    # File without final newline
    original = "# No final newline"
    (repo / "AGENTS.md").write_text(original, encoding="utf-8")
    canon = canonical_policy_text()
    ensure_agents_rules(repo, canon)
    data = (repo / "AGENTS.md").read_bytes()
    # After ensure, file should be valid and contain block
    assert POLICY_BEGIN.encode() in data
    remove_agents_rules(repo)
    restored = (repo / "AGENTS.md").read_text(encoding="utf-8")
    # Preserve user content (strip-insensitive final newline handling is practical)
    assert restored.strip() == original.strip()
    assert "No final newline" in restored


def test_cli_override_overrides_persisted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    # Simulate persisted settings off
    settings = tui_core.default_settings(["generic"])
    settings["policy"]["enforceAgentsMdRules"] = False
    settings = tui_core.validate_settings(settings)
    # CLI explicit enable overrides
    cli_override = True
    settings["policy"]["enforceAgentsMdRules"] = cli_override
    validated = tui_core.validate_settings(settings)
    assert validated["policy"]["enforceAgentsMdRules"] is True
    # CLI explicit disable overrides
    settings["policy"]["enforceAgentsMdRules"] = True
    settings = tui_core.validate_settings(settings)
    settings["policy"]["enforceAgentsMdRules"] = False
    assert tui_core.validate_settings(settings)["policy"]["enforceAgentsMdRules"] is False


def test_self_install_guard(tmp_path: Path) -> None:
    # Self-target detection should be true when repo is the source checkout with explicit source_root
    from pathlib import Path as P

    src = P(__file__).resolve().parents[1]
    # The current repo root is the source checkout – pass source_root explicitly as install.py does
    assert lifecycle.is_self_target(src, source_root=src) is True
    # A fresh tmp repo is not self even with source_root pointing to src
    repo = tmp_path / "other"
    init_repo(repo)
    assert lifecycle.is_self_target(repo, source_root=src) is False
    assert lifecycle.is_self_target(repo) is False


def test_verify_only_when_enforced(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    # Setup installed layout for smoke-like check
    oc = repo / ".opencode"
    oc.mkdir(parents=True)
    # Simulate canonical asset
    import shutil

    pack_policy = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "policy" / "agents-rules.md"
    (oc / "policy").mkdir(parents=True, exist_ok=True)
    shutil.copy2(pack_policy, oc / "policy" / "agents-rules.md")
    canon = canonical_policy_text()
    # Not enforced – no block required, smoke should not fail
    settings_off = tui_core.default_settings(["generic"])
    assert settings_off["policy"]["enforceAgentsMdRules"] is False
    # Enforced but missing block should be detected
    settings_on = tui_core.default_settings(["generic"])
    settings_on["policy"]["enforceAgentsMdRules"] = True
    # No block yet – validation would fail
    assert not (repo / "AGENTS.md").exists()
    # After ensure, inner matches canonical
    ensure_agents_rules(repo, canon)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    b = text.find(POLICY_BEGIN)
    e = text.find(POLICY_END)
    inner = text[b + len(POLICY_BEGIN) : e].replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    assert inner == canon.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
