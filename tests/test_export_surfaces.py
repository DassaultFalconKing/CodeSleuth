from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPORT_MODULE = ROOT / "pack" / ".opencode" / "bin" / "codesleuth_export.py"


def load_export_module():
    spec = importlib.util.spec_from_file_location("codesleuth_export_contract", EXPORT_MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeApp:
    def export_screenshot(self, *, title: str, simplify: bool) -> str:
        assert title
        assert simplify is True
        return '<svg xmlns="http://www.w3.org/2000/svg"><text>CodeSleuth export</text></svg>'


def test_tui_svg_export_is_retained_but_non_authoritative(tmp_path: Path) -> None:
    module = load_export_module()
    manifest = module.export_tui_svg(FakeApp(), tmp_path, "home-wide")

    export_dir = tmp_path / manifest["outputDirectory"]
    svg = (export_dir / "screen.svg").read_bytes()
    stored = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
    assert stored["kind"] == "codesleuth-ui-export"
    assert stored["exportAuthority"] == "none"
    assert stored["retainedArtifactOnly"] is True
    assert stored["artifacts"]["screen"]["sha256"] == hashlib.sha256(svg).hexdigest()
    assert b"<svg" in svg.lower()

    with pytest.raises(FileExistsError):
        module.export_tui_svg(FakeApp(), tmp_path, "home-wide")


@pytest.mark.parametrize("name", ["../escape", "", ".", "..", "with/slash"])
def test_tui_export_name_fails_closed(tmp_path: Path, name: str) -> None:
    module = load_export_module()
    with pytest.raises(ValueError):
        module.export_tui_svg(FakeApp(), tmp_path, name)


def test_tui_export_rejects_symlinked_export_root(tmp_path: Path) -> None:
    module = load_export_module()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / ".codesleuth"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted on this platform")
    with pytest.raises(RuntimeError, match="real directory"):
        module.export_tui_svg(FakeApp(), tmp_path, "home-wide")
    assert not (outside / "exports" / "ui" / "home-wide").exists()


def test_graph_export_routing_preserves_authority_boundaries() -> None:
    tool_source = (ROOT / "pack" / ".opencode" / "tools" / "codesleuth_export.ts").read_text(encoding="utf-8")
    bundle_source = (ROOT / "pack" / ".opencode" / "tools" / "export_bundle.ts").read_text(encoding="utf-8")

    assert 'get as contextGet' in tool_source
    assert 'includeMermaid: true' in tool_source
    assert 'query as protectedQuery' in tool_source
    assert 'load as ehaLoad' in tool_source
    assert 'assertProtectedSnapshot(machinePayload, envelope)' in tool_source
    assert 'assertEhaSnapshot(machinePayload, envelope)' in tool_source
    assert 'machine.contentSha256 !== presentation.contentSha256' in tool_source
    assert 'machinePayload?.eventCount !== provenance.eventCount' in tool_source
    assert 'from "./graphify' not in tool_source
    assert 'exportAuthority: "none"' in bundle_source
    assert 'retainedArtifactOnly: true' in bundle_source
    assert 'derivedPresentationOnly: true' in bundle_source
    assert '.codesleuth", "exports", "graphs"' in bundle_source
    assert 'refusing to export Mermaid without derivedPresentationOnly=true' in bundle_source
    assert 'isSymbolicLink()' in bundle_source
    assert 'export path component resolves through a link' in bundle_source


def test_svg_renderer_is_explicit_and_exact_pinned() -> None:
    source = EXPORT_MODULE.read_text(encoding="utf-8")
    assert 'PINNED_MERMAID_CLI_VERSION = "11.16.0"' in source
    assert 'securityLevel": "strict"' in source
    assert 'host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost' in source
    assert 'CODESLEUTH_MERMAID_CLI' in source
    assert 'CODESLEUTH_MERMAID_BROWSER' in source
    assert 'CODESLEUTH_MERMAID_NODE' in source
    assert 'executable identity must be explicitly configured' in source
    assert 'CODESLEUTH_MERMAID_CLI must be an absolute path' in source
    assert 'CODESLEUTH_MERMAID_RUNTIME must be an absolute path' in source
    assert '"python": {"path": str(Path(sys.executable).resolve())' in source
    assert 'retained": True' in source
