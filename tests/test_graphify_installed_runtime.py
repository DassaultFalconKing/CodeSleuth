from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_disposable_install_carries_provider_tools_and_lifecycle(tmp_path: Path, monkeypatch) -> None:
    run("git", "init", "-q", str(tmp_path))
    run("git", "-C", str(tmp_path), "config", "user.email", "test@example.invalid")
    run("git", "-C", str(tmp_path), "config", "user.name", "CodeSleuth Test")
    (tmp_path / "README.md").write_text("# disposable target\n", encoding="utf-8")
    run("git", "-C", str(tmp_path), "add", "README.md")
    run("git", "-C", str(tmp_path), "commit", "-qm", "fixture")

    installed = run("python", str(ROOT / "install.py"), str(tmp_path))
    assert "installed CodeSleuth" in installed.stdout
    smoke = run("python", str(ROOT / "smoke.py"), str(tmp_path))
    assert "PACK SMOKE PASS" in smoke.stdout

    installed_tool = tmp_path / ".opencode" / "tools" / "repo_context_provider.ts"
    installed_helper = tmp_path / ".opencode" / "bin" / "codesleuth_project" / "graphify_adapter.py"
    assert digest(installed_tool) == digest(ROOT / "pack" / ".opencode" / "tools" / "repo_context_provider.ts")
    assert digest(installed_helper) == digest(
        ROOT / "pack" / ".opencode" / "bin" / "codesleuth_project" / "graphify_adapter.py"
    )
    installed_lock = tmp_path / ".opencode" / "deps" / "graphify" / "requirements-lock.txt"
    assert installed_lock.is_file() and "--hash=sha256:" in installed_lock.read_text(encoding="utf-8")

    status = run(
        "python",
        str(installed_helper),
        "--runtime",
        str(tmp_path / ".runtime" / "graphify-provider"),
        "--status",
    )
    payload = json.loads(status.stdout)
    assert payload["status"] == "unavailable"
    assert payload["installed"] is False and payload["compatible"] is False
    assert payload["defaultProvider"] is False

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(tmp_path / ".opencode" / "bin")
    command = [
        "python", "-m", "codesleuth_project", "--install-graphify-runtime", str(tmp_path)
    ]
    # Exercise the installed CLI contract without downloading in this unit test.
    fake_pip = tmp_path / "fake_pip.py"
    fake_pip.write_text(
        "import pathlib,sys\n"
        "target=pathlib.Path(sys.argv[sys.argv.index('--target')+1])\n"
        "(target/'graphify').mkdir(parents=True)\n"
        "(target/'graphify'/'__init__.py').write_text('')\n"
        "meta=target/'graphifyy-0.9.50.dist-info'; meta.mkdir()\n"
        "(meta/'METADATA').write_text('Name: graphifyy\\nVersion: 0.9.50\\n')\n",
        encoding="utf-8",
    )
    lifecycle_script = tmp_path / ".opencode" / "bin" / "codesleuth_project" / "__init__.py"
    lifecycle_text = lifecycle_script.read_text(encoding="utf-8")
    lifecycle_text = lifecycle_text.replace(
        "sys.executable,\n                \"-m\",\n                \"pip\",",
        f"sys.executable,\n                {str(fake_pip)!r},",
    )
    lifecycle_script.write_text(lifecycle_text, encoding="utf-8")
    installed_runtime = subprocess.run(command, capture_output=True, text=True, check=True, env=environment)
    install_payload = json.loads(installed_runtime.stdout)
    assert install_payload["installed"] is True and install_payload["hashesRequired"] is True

    runtime = tmp_path / ".runtime" / "graphify-provider"
    (runtime / "marker.txt").write_text("optional", encoding="utf-8")
    removed = subprocess.run(
        ["python", "-m", "codesleuth_project", "--remove-graphify-runtime", str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    removal = json.loads(removed.stdout)
    assert removal["removed"] is True and removal["path"] == ".runtime/graphify-provider"
    assert not runtime.exists()
