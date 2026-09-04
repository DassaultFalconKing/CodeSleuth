from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSIX_WRAPPER = ROOT / "pack" / ".opencode" / "bin" / "opencode-review"
WINDOWS_WRAPPER = ROOT / "pack" / ".opencode" / "bin" / "opencode-review.ps1"
CONTINUE_COMMAND = ROOT / "pack" / ".opencode" / "commands" / "repo-continue.md"


def test_read_only_launchers_disable_target_project_config_discovery() -> None:
    posix = POSIX_WRAPPER.read_text(encoding="utf-8")
    windows = WINDOWS_WRAPPER.read_text(encoding="utf-8")

    assert "OPENCODE_DISABLE_PROJECT_CONFIG" in posix
    assert "OPENCODE_DISABLE_PROJECT_CONFIG" in windows
    assert 'OPENCODE_DISABLE_PROJECT_CONFIG="1"' in posix
    assert '$env:OPENCODE_DISABLE_PROJECT_CONFIG = "1"' in windows


def test_repo_continue_requires_durable_isolation_marker_before_parent_fallback() -> None:
    command = CONTINUE_COMMAND.read_text(encoding="utf-8")

    assert "development_continuation_state_record_isolation_unproven" in command
    assert "before executing that Step in the current session" in command
    assert "durable" in command.lower()
    assert "pathScopeAuthority = NOT_DECLARED" in command
    assert "SUPERSEDE_CONTRADICTION" in command
