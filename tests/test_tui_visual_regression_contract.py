from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENCODE = ROOT / "pack" / ".opencode"

MOJIBAKE_MARKERS = ("ÔÇ", "┬À", "ï»¿")

PACKET_B_TEXT_SURFACES = (
    ROOT / "tests" / "test_tui_visual_regression.py",
    ROOT / "docs" / "DURABLE-EVIDENCE-STORE.md",
    ROOT / "docs" / "TUI-VISUAL-REGRESSION.md",
    ROOT / "docs" / "EHA-OPERATING-PLAYBOOK.md",
    OPENCODE / "playbooks" / "eha-sib-acceptance" / "steps" / "05-sib2-profile.md",
    OPENCODE / "skills" / "eha-campaign-evidence" / "SKILL.md",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_visual_regression_suite_captures_screens_logs_and_event_trace() -> None:
    suite = text(ROOT / "tests" / "test_tui_visual_regression.py")
    for token in (
        "export_screenshot",
        "screen.svg",
        "ui.log",
        "events.log",
        "analysis.json",
        "Home · Evidence Console",
        "Verify started",
        "Update started",
        "left-nav-collapsed",
        "right-help-collapsed",
    ):
        assert token in suite


def test_acceptance_has_dedicated_tui_visual_regression_job_and_artifact_upload() -> None:
    workflow = text(ROOT / ".github" / "workflows" / "acceptance.yml")
    for token in (
        "TUI visual regression / Ubuntu",
        "CODESLEUTH_UI_VISUAL_REGRESSION",
        "CODESLEUTH_UI_ARTIFACT_DIR",
        "TEXTUAL_LOG",
        "tests/test_tui_visual_regression.py",
        "actions/upload-artifact@v4",
        "tui-visual-regression",
        "integration/**",
    ):
        assert token in workflow
    assert "ref: ${{ env.CODESLEUTH_ACCEPTANCE_SHA }}" in workflow
    assert "Verify exact checked-out commit" in workflow


def test_sib2_playbook_step_requires_tui_visual_regression() -> None:
    step = text(
        OPENCODE / "playbooks" / "eha-sib-acceptance" / "steps" / "05-sib2-profile.md"
    )
    assert "required `TUI visual regression / Ubuntu` job" in step
    assert "when applicable" not in step


def test_visual_regression_contract_is_documented_as_sib2_evidence() -> None:
    contract = text(ROOT / "docs" / "TUI-VISUAL-REGRESSION.md")
    campaign_skill = text(OPENCODE / "skills" / "eha-campaign-evidence" / "SKILL.md")
    for token in (
        "screen.svg",
        "ui.log",
        "events.log",
        "analysis.json",
        "exact tested SHA",
        "SIB2",
        "EHA repair loop",
    ):
        assert token in contract
    assert "TUI visual regression / Ubuntu" in campaign_skill
    assert "screen.svg" in campaign_skill
    assert "required" in campaign_skill and "SIB2" in campaign_skill


def test_packet_b_text_surfaces_have_no_known_mojibake_markers() -> None:
    for path in PACKET_B_TEXT_SURFACES:
        content = path.read_text(encoding="utf-8")
        assert "\ufeff" not in content, path
        for marker in MOJIBAKE_MARKERS:
            assert marker not in content, f"{marker!r} found in {path}"


def test_visual_regression_tools_label_matches_tui_source() -> None:
    canonical = "Tools · OpenCode-native capabilities"
    tui = text(ROOT / "pack" / ".opencode" / "bin" / "codesleuth_tui.py")
    suite = text(ROOT / "tests" / "test_tui_visual_regression.py")
    assert canonical in tui
    assert canonical in suite
    assert "Tools ┬À OpenCode-native capabilities" not in suite
