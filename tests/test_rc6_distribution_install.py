from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RC6_SURFACES = {
    "commands/repo-contract-bootstrap.md",
    "commands/repo-contract-adjudicate.md",
    "commands/repo-continue.md",
    "skills/contract-archaeology/SKILL.md",
    "skills/development-authority-discovery/SKILL.md",
    "playbooks/repository-contract-bootstrap/PLAYBOOK.md",
    "playbooks/repository-contract-bootstrap/playbook.json",
    "playbooks/repository-development-continuation/PLAYBOOK.md",
    "playbooks/repository-development-continuation/playbook.json",
    "tools/change_surface_state.ts",
    "tools/contract_bootstrap_state.ts",
    "tools/development_authority_state.ts",
    "tools/development_continuation_state.ts",
    "tools/native_gate_state.ts",
    "tools/external_evidence_state.ts",
}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True)


def test_clean_install_materializes_and_manages_every_rc6_surface(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "CodeSleuth Test")
    (repo / "README.md").write_text("target\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")

    subprocess.run([sys.executable, str(ROOT / "install.py"), str(repo)], check=True)

    oc = repo / ".opencode"
    meta = json.loads((oc / "review-pack.json").read_text(encoding="utf-8"))
    managed = set(meta["managedFiles"])
    assert RC6_SURFACES <= managed
    for rel in RC6_SURFACES:
        assert (oc / rel).is_file(), rel

    subprocess.run([sys.executable, str(oc / "bin" / "review-pack-smoke.py"), str(repo)], check=True)
