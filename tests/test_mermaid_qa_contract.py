from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mermaid_qa.py"
SPEC = importlib.util.spec_from_file_location("codesleuth_mermaid_qa", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_runtime_is_exact_pinned_and_isolated_from_main_package() -> None:
    package = (ROOT / "tools" / "mermaid-qa" / "package.json").read_text(encoding="utf-8")
    main_package = (ROOT / "package.json").read_text(encoding="utf-8")
    assert '"@mermaid-js/mermaid-cli": "11.16.0"' in package
    assert "@mermaid-js/mermaid-cli" not in main_package


def test_missing_runtime_is_unavailable_not_pass(tmp_path: Path) -> None:
    result = MODULE.validate_mermaid(b"flowchart LR\n  A --> B\n", runtime=tmp_path)
    assert result["status"] == "unavailable"
    assert result["passed"] is False
    assert "renderedArtifact" not in result


def test_empty_and_over_bound_sources_fail_closed(tmp_path: Path) -> None:
    empty = MODULE.validate_mermaid(b"", runtime=tmp_path)
    oversized = MODULE.validate_mermaid(b"x" * 11, runtime=tmp_path, max_bytes=10)
    assert empty["status"] == "rejected" and empty["passed"] is False
    assert oversized["status"] == "rejected" and oversized["passed"] is False


def test_contract_reports_digest_runtime_and_network_policy(tmp_path: Path) -> None:
    result = MODULE.validate_mermaid(b"flowchart TD\n  A\n", runtime=tmp_path)
    assert len(result["sourceSha256"]) == 64
    assert result["runtime"]["expectedVersion"] == "11.16.0"
    assert result["runtime"]["isolated"] is True
    assert "disabled" in result["networkPolicy"]
