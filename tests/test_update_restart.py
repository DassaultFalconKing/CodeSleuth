from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(__file__).resolve().parents[1] / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import review_pack_tui_bootstrap as bootstrap  # noqa: E402


def load_updater():
    path = BIN / "review-pack-update.py"
    spec = importlib.util.spec_from_file_location("codesleuth_update_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "CodeSleuth Test"], check=True)
    (path / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "initial"], check=True, capture_output=True)


def write_smoke(repo: Path, *, exit_code: int = 0) -> None:
    smoke = repo / ".opencode" / "bin" / "review-pack-smoke.py"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text(
        f"print({'VERIFY OK'!r} if {exit_code} == 0 else {'VERIFY FAILED'!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )


def test_finalize_update_verifies_then_writes_atomic_restart_request(tmp_path: Path) -> None:
    updater = load_updater()
    repo = tmp_path / "target"
    write_smoke(repo)

    updater.finalize_update(repo, "a" * 40, restart=False)

    marker = repo / updater.RESTART_MARKER
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["sourceCommit"] == "a" * 40
    assert isinstance(payload["nonce"], int)
    assert not marker.with_suffix(marker.suffix + ".tmp").exists()


def test_failed_verify_refuses_restart_request(tmp_path: Path) -> None:
    updater = load_updater()
    repo = tmp_path / "target"
    write_smoke(repo, exit_code=7)

    with pytest.raises(SystemExit, match="failed Verify"):
        updater.finalize_update(repo, "b" * 40, restart=False)

    assert not (repo / updater.RESTART_MARKER).exists()


def test_restart_tui_uses_current_python_and_updated_bootstrap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    updater = load_updater()
    repo = tmp_path / "target"
    bootstrap_path = repo / ".opencode" / "bin" / "review_pack_tui_bootstrap.py"
    bootstrap_path.parent.mkdir(parents=True)
    bootstrap_path.write_text("# updated bootstrap\n", encoding="utf-8")
    observed: dict[str, object] = {}

    def fake_execv(executable: str, argv: list[str]) -> None:
        observed["executable"] = executable
        observed["argv"] = argv
        observed["target_root"] = updater.os.environ.get("REVIEW_PACK_TARGET_ROOT")
        raise RuntimeError("exec intercepted")

    monkeypatch.delenv("REVIEW_PACK_TARGET_ROOT", raising=False)
    monkeypatch.setattr(updater.os, "execv", fake_execv)
    with pytest.raises(RuntimeError, match="exec intercepted"):
        updater.restart_tui(repo)

    assert observed["executable"] == sys.executable
    assert observed["argv"] == [sys.executable, str(bootstrap_path), "--target", str(repo)]
    assert observed["target_root"] == str(repo)


def test_runtime_watch_ignores_stale_marker_and_detects_new_request(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    marker = target / bootstrap.RESTART_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text('{"nonce":1}\n', encoding="utf-8")

    watch = bootstrap.capture_runtime_watch(target, None)
    assert not bootstrap.restart_requested(watch)

    marker.write_text('{"nonce":2}\n', encoding="utf-8")
    assert bootstrap.restart_requested(watch)


def test_runtime_watch_detects_self_checkout_head_change(tmp_path: Path) -> None:
    source = tmp_path / "source"
    init_repo(source)
    watch = bootstrap.capture_runtime_watch(source, source)
    assert watch.source_root == source.resolve()
    assert watch.source_head

    (source / "README.md").write_text("updated\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "commit", "-am", "update"], check=True, capture_output=True)
    watch.last_source_probe = 0.0

    assert bootstrap.restart_requested(watch)


def test_runtime_watch_does_not_reload_distribution_for_other_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    init_repo(source)
    init_repo(target)

    watch = bootstrap.capture_runtime_watch(target, source)

    assert watch.target_root == target.resolve()
    assert watch.source_root is None
    assert watch.source_head is None


def test_reexec_bootstrap_preserves_cli_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_execv(executable: str, argv: list[str]) -> None:
        observed["executable"] = executable
        observed["argv"] = argv
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(bootstrap.os, "execv", fake_execv)
    with pytest.raises(RuntimeError, match="exec intercepted"):
        bootstrap.reexec_bootstrap(["--target", "/tmp/example"])

    assert observed["executable"] == sys.executable
    assert observed["argv"][0] == sys.executable
    assert observed["argv"][-2:] == ["--target", "/tmp/example"]
