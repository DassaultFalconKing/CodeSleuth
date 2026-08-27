from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
    installer = Path(__file__).resolve().parents[1] / "install.py"
    first = subprocess.run(
        [sys.executable, str(installer), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    settings_path = repo / ".opencode" / "review-pack-user.json"
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted["policy"]["enforceAgentsMdRules"] is False
    assert POLICY_BEGIN not in (repo / "AGENTS.md").read_text(encoding="utf-8")

    enabled = subprocess.run(
        [sys.executable, str(installer), str(repo), "--update", "--enforce-agents-md-rules"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert enabled.returncode == 0, enabled.stderr
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted["policy"]["enforceAgentsMdRules"] is True
    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count(POLICY_BEGIN) == 1

    disabled = subprocess.run(
        [sys.executable, str(installer), str(repo), "--update", "--no-enforce-agents-md-rules"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert disabled.returncode == 0, disabled.stderr
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert persisted["policy"]["enforceAgentsMdRules"] is False
    assert POLICY_BEGIN not in (repo / "AGENTS.md").read_text(encoding="utf-8")


def test_self_install_guard(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1]
    assert lifecycle.is_self_target(src, source_root=src) is True
    repo = tmp_path / "other"
    init_repo(repo)
    assert lifecycle.is_self_target(repo, source_root=src) is False
    assert lifecycle.is_self_target(repo) is False


def test_verify_only_when_enforced(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    installer = Path(__file__).resolve().parents[1] / "install.py"
    off = subprocess.run(
        [sys.executable, str(installer), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert off.returncode == 0, off.stderr
    smoke = repo / ".opencode" / "bin" / "review-pack-smoke.py"
    verify_off = subprocess.run(
        [sys.executable, str(smoke), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert verify_off.returncode == 0, verify_off.stderr + verify_off.stdout
    assert "PACK SMOKE PASS" in verify_off.stdout

    on = subprocess.run(
        [sys.executable, str(installer), str(repo), "--update", "--enforce-agents-md-rules"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert on.returncode == 0, on.stderr
    verify_on = subprocess.run(
        [sys.executable, str(smoke), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert verify_on.returncode == 0, verify_on.stderr + verify_on.stdout
    agents = repo / "AGENTS.md"
    tampered = agents.read_text(encoding="utf-8").replace("Host owns", "HACKED")
    agents.write_text(tampered, encoding="utf-8")
    stale = subprocess.run(
        [sys.executable, str(smoke), str(repo)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert stale.returncode != 0
    assert "does not match canonical" in (stale.stderr + stale.stdout)


def test_settings_file_cli_override_and_retain(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    installer = Path(__file__).resolve().parents[1] / "install.py"
    subprocess.run([sys.executable, str(installer), str(repo)], check=True, capture_output=True, text=True)
    settings_path = tmp_path / "settings.json"
    payload = tui_core.default_settings(["generic"])
    payload["policy"]["enforceAgentsMdRules"] = True
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    override = subprocess.run(
        [
            sys.executable,
            str(installer),
            str(repo),
            "--update",
            "--settings-file",
            str(settings_path),
            "--no-enforce-agents-md-rules",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert override.returncode == 0, override.stderr
    persisted = json.loads((repo / ".opencode" / "review-pack-user.json").read_text(encoding="utf-8"))
    assert persisted["policy"]["enforceAgentsMdRules"] is False
    assert POLICY_BEGIN not in (repo / "AGENTS.md").read_text(encoding="utf-8")


def test_apply_settings_transactional_on_malformed_markers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    installer = Path(__file__).resolve().parents[1] / "install.py"
    subprocess.run([sys.executable, str(installer), str(repo)], check=True, capture_output=True, text=True)
    settings_path = repo / ".opencode" / "review-pack-user.json"
    before_settings = settings_path.read_text(encoding="utf-8")
    before_cfg = (repo / ".opencode" / "opencode.json").read_text(encoding="utf-8")
    malformed = "# keep\n" + POLICY_BEGIN + "\nno end\n"
    (repo / "AGENTS.md").write_text(malformed, encoding="utf-8")
    settings = tui_core.validate_settings(json.loads(before_settings))
    settings["policy"]["enforceAgentsMdRules"] = True
    with pytest.raises(RuntimeError, match="malformed"):
        tui_core.apply_settings_to_target(repo, settings)
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == malformed
    assert settings_path.read_text(encoding="utf-8") == before_settings
    assert (repo / ".opencode" / "opencode.json").read_text(encoding="utf-8") == before_cfg
    assert json.loads(before_settings)["policy"]["enforceAgentsMdRules"] is False


def test_remove_without_positive_ownership_preserves_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    canon = canonical_policy_text()
    block = f"{POLICY_BEGIN}\n{canon.rstrip()}\n{POLICY_END}\n"
    (repo / "AGENTS.md").write_text(block, encoding="utf-8")
    assert not (repo / ".opencode" / "state" / "agents-policy.json").exists()
    remove_agents_rules(repo)
    assert (repo / "AGENTS.md").is_file()
    leftover = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert POLICY_BEGIN not in leftover
    assert leftover.strip() == ""


def test_remove_preserves_user_blank_lines_around_block(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    original = "# Before\n\n\nKeep blank lines.\n"
    (repo / "AGENTS.md").write_text(original, encoding="utf-8")
    ensure_agents_rules(repo, canonical_policy_text())
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    e = text.find(POLICY_END) + len(POLICY_END)
    expanded = text[:e] + "\n\n# After section\n" + text[e:]
    (repo / "AGENTS.md").write_text(expanded, encoding="utf-8")
    remove_agents_rules(repo)
    restored = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert restored.startswith("# Before\n\n\nKeep blank lines.\n")
    assert "# After section" in restored
    assert POLICY_BEGIN not in restored
    assert POLICY_END not in restored


def test_self_install_rejects_enforce_and_does_not_rewrite_agents(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1]
    dest = tmp_path / "codesleuth"

    def _ignore(directory: str, names: list[str]) -> set[str]:
        skipped = {"__pycache__"}
        if Path(directory).resolve() == src.resolve():
            skipped.update({".git", ".opencode", ".codesleuth", ".venv", "node_modules", ".pytest_cache", "artifacts", ".cursor"})
        return {name for name in names if name in skipped}

    shutil.copytree(src, dest, ignore=_ignore)
    git(dest, "init")
    git(dest, "config", "user.email", "test@example.invalid")
    git(dest, "config", "user.name", "CodeSleuth Test")
    git(dest, "add", ".")
    git(dest, "commit", "-m", "self")
    before = (dest / "AGENTS.md").read_bytes()
    rejected = subprocess.run(
        [sys.executable, str(dest / "install.py"), str(dest), "--self-install", "--enforce-agents-md-rules"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "not valid for a CodeSleuth self-install" in (rejected.stderr + rejected.stdout)
    assert (dest / "AGENTS.md").read_bytes() == before

    ok = subprocess.run(
        [sys.executable, str(dest / "install.py"), str(dest), "--self-install"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr
    after = (dest / "AGENTS.md").read_text(encoding="utf-8")
    assert POLICY_BEGIN not in after
    persisted = json.loads((dest / ".opencode" / "review-pack-user.json").read_text(encoding="utf-8"))
    assert persisted["policy"]["enforceAgentsMdRules"] is False
    smoke = subprocess.run(
        [sys.executable, str(dest / ".opencode" / "bin" / "review-pack-smoke.py"), str(dest)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert smoke.returncode == 0, smoke.stderr + smoke.stdout
