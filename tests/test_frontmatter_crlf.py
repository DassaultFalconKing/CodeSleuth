from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"


# helper from tests_util
sys.path.insert(0, str(ROOT / "pack" / ".opencode"))
from tests_util import parse_frontmatter_field_from_text  # noqa: E402

BIN_HELPER = BIN / "review-pack-smoke.py"


def load_smoke_parser():
    spec = importlib.util.spec_from_file_location("review_pack_smoke_for_test", BIN_HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._frontmatter_field


def test_frontmatter_accepts_crlf_line_endings(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    content = "---\r\nagent: build\r\n---\r\nbody\r\n"
    # via helper
    assert parse_frontmatter_field_from_text(content, "agent") == "build"
    assert parse_frontmatter_field_from_text(content, "mode") is None
    # via smoke implementation
    p = tmp_path / "cmd.md"
    p.write_text(content, encoding="utf-8")
    assert smoke_field(p, "agent") == "build"
    # mode file with CRLF
    content2 = "---\r\nmode: subagent\r\n---\r\n"
    p2 = tmp_path / "agent.md"
    p2.write_text(content2, encoding="utf-8")
    assert smoke_field(p2, "mode") == "subagent"
    assert parse_frontmatter_field_from_text(content2, "mode") == "subagent"


@pytest.mark.parametrize(
    "raw",
    [
        "---\nagent : build\n---\n",
        "---\nagent:    build\n---\n",
        "---\n  agent: build  \n---\n",
        "---\n\t agent \t : \t build \t\n---\n",
        "---\nagent :    build   \n---\n",
        "---\n   mode   :   subagent   \n---\n",
    ],
)
def test_frontmatter_accepts_extra_yaml_spacing(raw: str, tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    key = "agent" if "agent" in raw else "mode"
    expected = "build" if key == "agent" else "subagent"
    assert parse_frontmatter_field_from_text(raw, key) == expected
    p = tmp_path / "f.md"
    p.write_text(raw, encoding="utf-8")
    assert smoke_field(p, key) == expected


def test_frontmatter_accepts_crlf_and_spacing_combined(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    content = "---\r\n  agent  :  build  \r\n---\r\n"
    assert parse_frontmatter_field_from_text(content, "agent") == "build"
    p = tmp_path / "c.md"
    p.write_text(content, encoding="utf-8")
    assert smoke_field(p, "agent") == "build"
    content2 = "---\r\n\tmode\t:\tsubagent\t\r\n---\r\n"
    assert parse_frontmatter_field_from_text(content2, "mode") == "subagent"
    p2 = tmp_path / "a.md"
    p2.write_text(content2, encoding="utf-8")
    assert smoke_field(p2, "mode") == "subagent"


def test_frontmatter_accepts_mixed_crlf_and_lf(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    content = "---\nagent: build\r\n---\nbody"
    assert parse_frontmatter_field_from_text(content, "agent") == "build"
    p = tmp_path / "m.md"
    p.write_text(content, encoding="utf-8")
    assert smoke_field(p, "agent") == "build"


def test_frontmatter_preserves_other_keys_and_returns_none_for_missing(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    content = "---\nagent: build\ndescription: x\n---\n"
    assert parse_frontmatter_field_from_text(content, "agent") == "build"
    assert parse_frontmatter_field_from_text(content, "description") == "x"
    assert parse_frontmatter_field_from_text(content, "mode") is None
    p = tmp_path / "q.md"
    p.write_text(content, encoding="utf-8")
    assert smoke_field(p, "agent") == "build"
    assert smoke_field(p, "missing") is None


def test_frontmatter_all_command_and_agent_variants(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    for name, key, value in [
        ("repo-review.md", "agent", "build"),
        ("repo-docs.md", "agent", "build"),
        ("repo-reviewer.md", "mode", "subagent"),
        ("repo-scout.md", "mode", "subagent"),
    ]:
        for template in [
            "---\n{key}: {value}\n---\n",
            "---\r\n{key}: {value}\r\n---\r\n",
            "---\n  {key}  :  {value}  \n---\n",
            "---\r\n\t{key}\t:\t{value}\t\r\n---\r\n",
        ]:
            raw = template.format(key=key, value=value)
            assert parse_frontmatter_field_from_text(raw, key) == value
            p = tmp_path / name
            p.write_text(raw, encoding="utf-8")
            assert smoke_field(p, key) == value


def test_frontmatter_handles_bom_and_leading_whitespace(tmp_path: Path) -> None:
    smoke_field = load_smoke_parser()
    content = "\ufeff---\nagent: build\n---\n"
    assert parse_frontmatter_field_from_text(content, "agent") == "build"
    p = tmp_path / "bom.md"
    p.write_text(content, encoding="utf-8")
    assert smoke_field(p, "agent") == "build"
    content2 = "  \n---\nmode: subagent\n---\n"
    # lstrip should allow leading whitespace/newlines before ---
    assert parse_frontmatter_field_from_text(content2, "mode") == "subagent"
