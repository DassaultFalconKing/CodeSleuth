#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

PINNED_MERMAID_CLI_VERSION = "11.16.0"
MAX_MERMAID_BYTES = 1_000_000
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _resolve_executable(explicit: str | None, label: str) -> Path:
    if not explicit:
        raise RuntimeError(f"{label} executable identity must be explicitly configured")
    candidate = Path(explicit)
    if not candidate.is_absolute():
        raise RuntimeError(f"{label} executable path must be absolute: {explicit}")
    resolved_path = candidate.resolve(strict=True)
    if not resolved_path.is_file() or not os.access(resolved_path, os.X_OK):
        raise RuntimeError(f"{label} is not executable: {resolved_path}")
    return resolved_path


def _version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    text = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if completed.returncode != 0 or not text:
        raise RuntimeError(f"{executable} --version failed with exit {completed.returncode}: {text}")
    return text[:1_000]


def _source_repo_root() -> Path:
    # pack/.opencode/bin/codesleuth_export.py -> repository root
    return Path(__file__).resolve().parents[3]


def _resolve_mermaid_cli() -> tuple[Path, Path, str]:
    explicit_cli = os.environ.get("CODESLEUTH_MERMAID_CLI")
    explicit_runtime = os.environ.get("CODESLEUTH_MERMAID_RUNTIME")
    if explicit_cli:
        configured_cli = Path(explicit_cli)
        if not configured_cli.is_absolute():
            raise RuntimeError("CODESLEUTH_MERMAID_CLI must be an absolute path")
        cli = configured_cli.resolve(strict=True)
        package_json = cli.parent.parent / "package.json"
    else:
        if explicit_runtime:
            configured_runtime = Path(explicit_runtime)
            if not configured_runtime.is_absolute():
                raise RuntimeError("CODESLEUTH_MERMAID_RUNTIME must be an absolute path")
            runtime = configured_runtime.resolve(strict=True)
        else:
            runtime = _source_repo_root() / "tools" / "mermaid-qa"
        package_root = runtime / "node_modules" / "@mermaid-js" / "mermaid-cli"
        cli = package_root / "src" / "cli.js"
        package_json = package_root / "package.json"
    if not cli.is_file() or not package_json.is_file():
        raise RuntimeError(
            "Mermaid export runtime is unavailable; install the exact-pinned tools/mermaid-qa runtime or set CODESLEUTH_MERMAID_CLI"
        )
    package = json.loads(package_json.read_text(encoding="utf-8"))
    version = str(package.get("version") or "")
    if version != PINNED_MERMAID_CLI_VERSION:
        raise RuntimeError(
            f"Mermaid export requires @mermaid-js/mermaid-cli {PINNED_MERMAID_CLI_VERSION}, found {version or 'unknown'}"
        )
    return cli.resolve(), package_json.resolve(), version


def render_mermaid_svg(source: bytes, output: Path, *, timeout_seconds: int = 30) -> dict[str, Any]:
    if not source.strip():
        raise RuntimeError("Mermaid source is empty")
    if len(source) > MAX_MERMAID_BYTES:
        raise RuntimeError(f"Mermaid source exceeds {MAX_MERMAID_BYTES} bytes")

    cli, package_json, cli_version = _resolve_mermaid_cli()
    node = _resolve_executable(os.environ.get("CODESLEUTH_MERMAID_NODE"), "Node")
    browser = _resolve_executable(os.environ.get("CODESLEUTH_MERMAID_BROWSER"), "Chromium")

    with tempfile.TemporaryDirectory(prefix="codesleuth-mermaid-export-") as temporary:
        temp = Path(temporary)
        source_path = temp / "input.mmd"
        rendered_path = temp / "output.svg"
        mermaid_config = temp / "mermaid.json"
        puppeteer_config = temp / "puppeteer.json"
        source_path.write_bytes(source)
        mermaid_config.write_text(json.dumps({"securityLevel": "strict"}), encoding="utf-8")
        puppeteer_config.write_text(
            json.dumps(
                {
                    "headless": True,
                    "executablePath": str(browser),
                    "args": [
                        "--disable-background-networking",
                        "--disable-component-update",
                        "--disable-domain-reliability",
                        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
                        "--no-first-run",
                    ],
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                str(node),
                str(cli),
                "--input",
                str(source_path),
                "--output",
                str(rendered_path),
                "--configFile",
                str(mermaid_config),
                "--puppeteerConfigFile",
                str(puppeteer_config),
                "--quiet",
            ],
            cwd=temp,
            env={
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "TEMP": os.environ.get("TEMP", str(temp)),
                "TMP": os.environ.get("TMP", str(temp)),
                "NO_PROXY": "*",
                "no_proxy": "*",
            },
            capture_output=True,
            text=True,
            timeout=max(1, timeout_seconds),
            check=False,
        )
        diagnostics = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        if completed.returncode != 0 or not rendered_path.is_file():
            raise RuntimeError(diagnostics or f"mmdc exited {completed.returncode} without SVG output")
        svg = rendered_path.read_bytes()
        if b"<svg" not in svg[:2_000].lower():
            raise RuntimeError("renderer output is not recognizable SVG")
        _atomic_write(output, svg)

    return {
        "schemaVersion": 1,
        "status": "pass",
        "retained": True,
        "format": "svg",
        "output": str(output),
        "bytes": len(svg),
        "sha256": _sha256(svg),
        "sourceSha256": _sha256(source),
        "renderer": {
            "package": "@mermaid-js/mermaid-cli",
            "version": cli_version,
            "packageJson": str(package_json),
            "python": {"path": str(Path(sys.executable).resolve()), "version": sys.version.splitlines()[0]},
            "node": {"path": str(node), "version": _version(node)},
            "browser": {"path": str(browser), "version": _version(browser)},
            "networkPolicy": "host resolution disabled; Mermaid securityLevel strict",
        },
        "diagnostics": diagnostics[:8_000],
    }


def _ensure_export_parent(root: Path, *parts: str) -> Path:
    current = root.resolve(strict=True)
    for part in parts:
        candidate = current / part
        try:
            status = candidate.lstat()
        except FileNotFoundError:
            candidate.mkdir()
            status = candidate.lstat()
        if candidate.is_symlink() or not stat.S_ISDIR(status.st_mode):
            raise RuntimeError(f"export path component must be a real directory, not a link or file: {candidate}")
        resolved = candidate.resolve(strict=True)
        if resolved != candidate:
            raise RuntimeError(f"export path component resolves through a link: {candidate} -> {resolved}")
        current = candidate
    return current


def export_tui_svg(app: Any, repo_root: Path, name: str, *, title: str | None = None) -> dict[str, Any]:
    if not SAFE_NAME_RE.fullmatch(name) or name in {".", ".."}:
        raise ValueError("TUI export name must be 1..120 safe filename characters")
    root = repo_root.resolve(strict=True)
    export_parent = _ensure_export_parent(root, ".codesleuth", "exports", "ui")
    export_dir = export_parent / name
    if export_dir.exists() or export_dir.is_symlink():
        raise FileExistsError(f"TUI export already exists: {export_dir}")
    export_dir.mkdir(parents=False, exist_ok=False)
    try:
        svg_text = app.export_screenshot(title=title or f"CodeSleuth TUI export: {name}", simplify=True)
        svg = svg_text.encode("utf-8")
        if b"<svg" not in svg[:2_000].lower():
            raise RuntimeError("Textual export_screenshot did not return recognizable SVG")
        _atomic_write(export_dir / "screen.svg", svg)
        manifest = {
            "schemaVersion": 1,
            "kind": "codesleuth-ui-export",
            "exportAuthority": "none",
            "retainedArtifactOnly": True,
            "surface": "tui",
            "artifacts": {
                "screen": {
                    "path": "screen.svg",
                    "format": "svg",
                    "bytes": len(svg),
                    "sha256": _sha256(svg),
                }
            },
            "reminder": "UI exports are presentation artifacts, not repository or acceptance evidence",
        }
        _atomic_write(
            export_dir / "manifest.json",
            (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )
        return {**manifest, "outputDirectory": export_dir.relative_to(root).as_posix()}
    except BaseException:
        shutil.rmtree(export_dir, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeSleuth retained export helpers")
    sub = parser.add_subparsers(dest="command", required=True)
    mermaid = sub.add_parser("mermaid-svg", help="Render Mermaid source to a retained SVG with pinned runtime identity")
    mermaid.add_argument("source", nargs="?", type=Path, help="Mermaid source file; stdin when omitted")
    mermaid.add_argument("--output", required=True, type=Path)
    mermaid.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    if args.command == "mermaid-svg":
        source = args.source.read_bytes() if args.source else sys.stdin.buffer.read(MAX_MERMAID_BYTES + 1)
        try:
            result = render_mermaid_svg(source, args.output, timeout_seconds=args.timeout)
        except Exception as error:
            print(json.dumps({"schemaVersion": 1, "status": "unavailable_or_failed", "error": str(error)}, indent=2))
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
