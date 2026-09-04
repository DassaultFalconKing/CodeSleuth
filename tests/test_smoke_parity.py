from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _required_paths(script: Path) -> set[str]:
    module = ast.parse(script.read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "required" for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            return set(value)
    raise AssertionError(f"required list not found in {script}")


def test_source_and_installed_verify_require_all_advertised_rc6_surfaces() -> None:
    source = _required_paths(ROOT / "smoke.py")
    installed = _required_paths(ROOT / "pack" / ".opencode" / "bin" / "review-pack-smoke.py")
    required = {
        "commands/repo-map.md",
        "commands/repo-contracts.md",
        "commands/repo-contract-bootstrap.md",
        "commands/repo-contract-adjudicate.md",
        "commands/repo-continue.md",
        "commands/eha-test.md",
        "commands/eha-status.md",
        "skills/contract-archaeology/SKILL.md",
        "skills/development-authority-discovery/SKILL.md",
        "playbooks/repository-map/playbook.json",
        "playbooks/protected-capability-assessment/playbook.json",
        "playbooks/repository-contract-bootstrap/playbook.json",
        "playbooks/repository-development-continuation/playbook.json",
        "playbooks/eha-sib-acceptance/playbook.json",
        "tools/repo_context_graph.ts",
        "tools/eha_state.ts",
        "tools/protected_capability_graph.ts",
        "tools/repo_context_provider.ts",
        "tools/change_surface_state.ts",
        "tools/contract_bootstrap_state.ts",
        "tools/development_authority_state.ts",
        "tools/development_continuation_state.ts",
        "tools/native_gate_state.ts",
        "tools/external_evidence_state.ts",
        "bin/codesleuth_project/graphify_adapter.py",
    }
    assert required <= source
    assert required <= installed
    assert source == installed
