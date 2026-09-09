from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
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

    def fake_replace(argv: list[str]) -> None:
        observed["argv"] = argv
        observed["target_root"] = updater.os.environ.get("REVIEW_PACK_TARGET_ROOT")
        raise RuntimeError("replace intercepted")

    monkeypatch.delenv("REVIEW_PACK_TARGET_ROOT", raising=False)
    monkeypatch.setattr(updater, "replace_current_process", fake_replace)
    with pytest.raises(RuntimeError, match="replace intercepted"):
        updater.restart_tui(repo)

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

    def fake_replace(argv: list[str]) -> None:
        observed["argv"] = argv
        raise RuntimeError("replace intercepted")

    monkeypatch.setattr(bootstrap, "replace_current_process", fake_replace)
    with pytest.raises(RuntimeError, match="replace intercepted"):
        bootstrap.reexec_bootstrap(["--target", "/tmp/example"])

    assert observed["argv"][0] == sys.executable
    assert Path(observed["argv"][1]) == BIN / "review_pack_tui_bootstrap.py"
    assert observed["argv"][-2:] == ["--target", "/tmp/example"]


def test_windows_process_replace_waits_and_forwards_exit(tmp_path: Path) -> None:
    """Windows overlay-exec returns to the parent waiter immediately (exit 0).

    Isolated TUI launch and restart must keep that waiter attached until the
    replacement interpreter exits, otherwise PowerShell reclaims the console
    and the Textual app is left unresponsive.
    """

    child = tmp_path / "child.py"
    child.write_text("import sys, time\ntime.sleep(0.35)\nraise SystemExit(17)\n", encoding="utf-8")
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(BIN)!r})\n"
        "import review_pack_tui_bootstrap as bootstrap\n"
        f"bootstrap.replace_current_process([sys.executable, {str(child)!r}])\n",
        encoding="utf-8",
    )

    started_at = time.monotonic()
    result = subprocess.run([sys.executable, str(driver)], text=True, capture_output=True)
    elapsed = time.monotonic() - started_at

    assert result.returncode == 17, result.stderr
    assert elapsed >= 0.25


def test_windows_process_replace_does_not_use_overlay_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.os, "name", "nt")

    def forbid_execv(*_args, **_kwargs) -> None:
        raise AssertionError("os.execv overlay-exec detaches the Windows console waiter")

    monkeypatch.setattr(bootstrap.os, "execv", forbid_execv)

    observed: dict[str, object] = {}

    class Result:
        returncode = 11

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)
    with pytest.raises(SystemExit) as exc:
        bootstrap.replace_current_process([sys.executable, "app.py", "."])
    assert exc.value.code == 11
    assert observed["argv"] == [sys.executable, "app.py", "."]
    kwargs = observed["kwargs"]
    assert not kwargs.get("capture_output")
    assert kwargs.get("stdout") is None
    assert kwargs.get("stderr") is None
    assert kwargs.get("stdin") is None
    assert "creationflags" not in kwargs


def test_posix_process_replace_uses_exec_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.os, "name", "posix")
    observed: dict[str, object] = {}

    def fake_execv(executable: str, argv: list[str]) -> None:
        observed["executable"] = executable
        observed["argv"] = list(argv)
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(bootstrap.os, "execv", fake_execv)
    with pytest.raises(RuntimeError, match="exec intercepted"):
        bootstrap.replace_current_process(["/usr/bin/python", "app.py", "."])
    assert observed["executable"] == "/usr/bin/python"
    assert observed["argv"] == ["/usr/bin/python", "app.py", "."]


def test_ensure_textual_runtime_replaces_into_isolated_interpreter(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    isolated = tmp_path / "isolated-python"
    isolated.write_text("", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "usable_current_python", lambda: False)
    monkeypatch.setattr(bootstrap, "ensure_runtime", lambda _version: isolated)
    monkeypatch.setattr(bootstrap.sys, "executable", str(tmp_path / "host-python"))
    observed: dict[str, object] = {}

    def fake_replace(argv: list[str]) -> None:
        observed["argv"] = argv
        raise RuntimeError("replaced")

    monkeypatch.setattr(bootstrap, "replace_current_process", fake_replace)
    with pytest.raises(RuntimeError, match="replaced"):
        bootstrap.ensure_textual_runtime(["."], "0.4.0")
    assert Path(observed["argv"][0]) == isolated
    assert Path(observed["argv"][1]) == BIN / "review_pack_tui_bootstrap.py"
    assert observed["argv"][-1] == "."


def test_restart_tui_windows_waits_for_replacement(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    updater = load_updater()
    repo = tmp_path / "target"
    bootstrap_path = repo / ".opencode" / "bin" / "review_pack_tui_bootstrap.py"
    bootstrap_path.parent.mkdir(parents=True)
    bootstrap_path.write_text("# updated bootstrap\n", encoding="utf-8")
    observed: dict[str, object] = {}

    def forbid_execv(*_args, **_kwargs) -> None:
        raise AssertionError("os.execv overlay-exec detaches the Windows console waiter")

    class Result:
        returncode = 0

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr(updater.os, "name", "nt")
    monkeypatch.setattr(updater.os, "execv", forbid_execv)
    monkeypatch.setattr(updater.subprocess, "run", fake_run)
    monkeypatch.delenv("REVIEW_PACK_TARGET_ROOT", raising=False)
    with pytest.raises(SystemExit) as exc:
        updater.restart_tui(repo)
    assert exc.value.code == 0
    assert observed["argv"] == [sys.executable, str(bootstrap_path), "--target", str(repo)]
    assert updater.os.environ.get("REVIEW_PACK_TARGET_ROOT") == str(repo)
    assert not observed["kwargs"].get("capture_output")
