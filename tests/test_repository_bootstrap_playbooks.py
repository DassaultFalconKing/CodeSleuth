from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))

from playbook_catalog import pack_playbook_ids, validate_playbook_dir  # noqa: E402

BOOTSTRAP_SHA256 = "cfdfb0b1fba6978088a256682ec935a7b4e2cc0ed9342eee1f3825c8a0834ab8"
TASK_SESSION_SHA256 = "b9b0d48f5bc41ed898db97082baf18c795060a898532c0381deb470aa697df7b"


def _sha256_git_blob(path: Path) -> str:
    relative_path = path.relative_to(ROOT).as_posix()
    content = subprocess.check_output(["git", "show", f"HEAD:{relative_path}"], cwd=ROOT)
    return hashlib.sha256(content).hexdigest()


def test_repository_bootstrap_playbooks_are_builtin_and_valid() -> None:
    ids = pack_playbook_ids(ROOT, ROOT)
    assert "repository-bootstrap" in ids
    assert "repository-task-session" in ids

    for playbook_id in ("repository-bootstrap", "repository-task-session"):
        report = validate_playbook_dir(ROOT / "pack" / ".opencode" / "playbooks" / playbook_id)
        assert report.ok, report.errors


def test_repository_bootstrap_prompts_are_verbatim() -> None:
    playbooks = ROOT / "pack" / ".opencode" / "playbooks"
    bootstrap_prompt = playbooks / "repository-bootstrap" / "PROMPT.verbatim.md"
    task_prompt = playbooks / "repository-task-session" / "steps" / "01-task-specific-session.md"

    assert _sha256_git_blob(bootstrap_prompt) == BOOTSTRAP_SHA256
    assert _sha256_git_blob(task_prompt) == TASK_SESSION_SHA256
