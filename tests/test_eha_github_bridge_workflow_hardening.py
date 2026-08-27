from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "eha.yml"
SCRIPT = ROOT / "scripts" / "eha_github_bridge.py"


def test_remote_eha_controller_is_immutable_and_manual_dispatch_is_main_only() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert "ref: ${{ github.sha }}" in workflow
    assert "ref: main" not in workflow


def test_remote_eha_does_not_stream_opencode_transcript_to_public_actions_log() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    assert "private_transcript_path" in script
    assert "stdout=transcript" in script
    assert "stderr=subprocess.STDOUT" in script
    assert "transcriptRecord" in script
    assert "PRIVATE EHA TRANSCRIPT AND BRIDGE STATUS RECORDED ON TRUSTED HOST" in script
