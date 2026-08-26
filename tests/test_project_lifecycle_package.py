from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pack" / ".opencode" / "bin"
sys.path.insert(0, str(BIN))
import codesleuth_project as lifecycle  # noqa: E402


def test_lifecycle_import_resolves_package_and_extracted_paths() -> None:
    module_path = Path(lifecycle.__file__).resolve()
    assert module_path == (BIN / "codesleuth_project" / "__init__.py").resolve()
    assert lifecycle.ensure_local_gitignore.__module__ == "codesleuth_project.paths"
    assert lifecycle.update_reports_index.__module__ == "codesleuth_project.paths"
    assert (BIN / "codesleuth_project" / "paths.py").is_file()
    assert (BIN / "codesleuth_project" / "__main__.py").is_file()


def test_current_naming_contract_keeps_python_file_shim() -> None:
    manifest = json.loads((ROOT / "pack" / ".opencode" / "codesleuth-naming.json").read_text(encoding="utf-8"))
    assert manifest["canonical"]["python"]["project"] == "bin/codesleuth_project.py"
    shim = BIN / "codesleuth_project.py"
    assert shim.is_file()
    text = shim.read_text(encoding="utf-8")
    assert "from codesleuth_project import main" in text


def test_module_and_canonical_shim_entrypoints_are_executable() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(BIN) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    module = subprocess.run(
        [sys.executable, "-m", "codesleuth_project", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert module.returncode == 0, module.stderr
    assert "Manage CodeSleuth" in module.stdout

    shim = subprocess.run(
        [sys.executable, str(BIN / "codesleuth_project.py"), "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert shim.returncode == 0, shim.stderr
    assert "Manage CodeSleuth" in shim.stdout


def test_launchers_use_package_entrypoint() -> None:
    shell = (BIN / "codesleuth-project").read_text(encoding="utf-8")
    powershell = (BIN / "codesleuth-project.ps1").read_text(encoding="utf-8")
    assert "PYTHONPATH" in shell
    assert "python3 -m codesleuth_project" in shell
    assert "PYTHONPATH" in powershell
    assert "python -m codesleuth_project" in powershell
