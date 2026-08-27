from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "contributor_antipatterns.py"
SPEC = importlib.util.spec_from_file_location("codesleuth_contributor_antipatterns", SCRIPT)
assert SPEC and SPEC.loader
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


def _runtime_tree(root: Path) -> None:
    (root / "pack" / ".opencode" / "tools").mkdir(parents=True)
    (root / "pack" / ".opencode" / "bin").mkdir(parents=True)
    (root / "codesleuth_mcp").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)


def test_orphaned_bun_smoke_is_blocking(tmp_path: Path) -> None:
    _runtime_tree(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "bun tests/base_smoke.ts",
                    "test:base": "bun tests/base_smoke.ts",
                    "test:new": "bun tests/new_smoke.ts",
                }
            }
        ),
        encoding="utf-8",
    )
    findings = SCANNER.scan_repository(tmp_path)
    assert any(item.rule_id == "AP-CI-001" and item.blocking for item in findings)


def test_registered_bun_smoke_is_not_flagged(tmp_path: Path) -> None:
    _runtime_tree(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "bun tests/base_smoke.ts && bun tests/new_smoke.ts",
                    "test:base": "bun tests/base_smoke.ts",
                    "test:new": "bun tests/new_smoke.ts",
                }
            }
        ),
        encoding="utf-8",
    )
    findings = SCANNER.scan_repository(tmp_path)
    assert not any(item.rule_id == "AP-CI-001" for item in findings)


def test_ambient_python_spawn_is_blocking(tmp_path: Path) -> None:
    _runtime_tree(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "bun tests/base_smoke.ts", "test:base": "bun tests/base_smoke.ts"}}),
        encoding="utf-8",
    )
    tool = tmp_path / "pack" / ".opencode" / "tools" / "provider.ts"
    tool.write_text('const proc = Bun.spawn(["python", "adapter.py"])\n', encoding="utf-8")
    findings = SCANNER.scan_repository(tmp_path)
    assert any(item.rule_id == "AP-RUN-001" and item.blocking for item in findings)


def test_explicit_python_interpreter_is_not_flagged(tmp_path: Path) -> None:
    _runtime_tree(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "bun tests/base_smoke.ts", "test:base": "bun tests/base_smoke.ts"}}),
        encoding="utf-8",
    )
    runtime = tmp_path / "pack" / ".opencode" / "bin" / "runner.py"
    runtime.write_text(
        "import subprocess\nimport sys\nsubprocess.run([sys.executable, 'worker.py'], check=True)\n",
        encoding="utf-8",
    )
    findings = SCANNER.scan_repository(tmp_path)
    assert not any(item.rule_id == "AP-RUN-001" for item in findings)


def test_runtime_dependent_skip_is_visible_warning(tmp_path: Path) -> None:
    _runtime_tree(tmp_path)
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "bun tests/base_smoke.ts", "test:base": "bun tests/base_smoke.ts"}}),
        encoding="utf-8",
    )
    test_file = tmp_path / "tests" / "test_provider.py"
    test_file.write_text(
        "import pytest\n\ndef test_provider():\n    pytest.skip('optional runtime not installed')\n",
        encoding="utf-8",
    )
    findings = SCANNER.scan_repository(tmp_path)
    assert any(item.rule_id == "AP-CI-002" and item.severity == "WARN" for item in findings)


def test_repository_gate_has_no_blocking_mechanical_findings() -> None:
    findings = SCANNER.scan_repository(ROOT)
    blocking = [item for item in findings if item.blocking]
    assert blocking == [], "\n".join(
        f"{item.rule_id} {item.path}:{item.line} {item.message}" for item in blocking
    )


def test_prewrite_discipline_is_wired_into_contributor_and_agent_surfaces() -> None:
    command = "python scripts/contributor_antipatterns.py prewrite"
    contributor = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    cursor = (ROOT / ".cursor" / "rules" / "contributor-antipattern-preflight.mdc").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "acceptance.yml").read_text(encoding="utf-8")
    guidance = (ROOT / "docs" / "CONTRIBUTOR-ERROR-PATTERNS.md").read_text(encoding="utf-8")

    assert command in contributor
    assert command in agents
    assert command in cursor
    assert "python scripts/contributor_antipatterns.py scan --strict" in workflow
    assert "EP-01" in guidance and "EP-10" in guidance
    assert "alwaysApply: true" in cursor
