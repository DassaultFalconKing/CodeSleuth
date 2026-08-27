#!/usr/bin/env python3
"""Bounded, opt-in Mermaid parser/render QA using an isolated exact-pinned CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME = ROOT / "tools" / "mermaid-qa"
PINNED_PACKAGE = "@mermaid-js/mermaid-cli"
PINNED_VERSION = "11.16.0"
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 30


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _result(
    *,
    status: str,
    source: bytes,
    runtime: Path,
    diagnostics: str,
    version: str | None = None,
    svg: bytes | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "qa": "mermaid_cli_parse_render",
        "status": status,
        "passed": status == "pass",
        "sourceSha256": _sha256(source),
        "sourceBytes": len(source),
        "runtime": {
            "package": PINNED_PACKAGE,
            "expectedVersion": PINNED_VERSION,
            "resolvedVersion": version,
            "root": str(runtime.resolve()),
            "isolated": True,
        },
        "networkPolicy": "chromium host resolution disabled; Mermaid securityLevel strict",
        "diagnostics": diagnostics[:8_000],
    }
    if svg is not None:
        result["renderedArtifact"] = {
            "format": "svg",
            "bytes": len(svg),
            "sha256": _sha256(svg),
            "retained": False,
        }
    return result


def validate_mermaid(
    source: bytes,
    *,
    runtime: Path = DEFAULT_RUNTIME,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if len(source) > max_bytes:
        return _result(
            status="rejected",
            source=source,
            runtime=runtime,
            diagnostics=f"Mermaid source exceeds {max_bytes} byte bound",
        )
    if not source.strip():
        return _result(status="rejected", source=source, runtime=runtime, diagnostics="Mermaid source is empty")

    package_json = runtime / "node_modules" / "@mermaid-js" / "mermaid-cli" / "package.json"
    cli = runtime / "node_modules" / "@mermaid-js" / "mermaid-cli" / "src" / "cli.js"
    if not package_json.is_file() or not cli.is_file():
        return _result(
            status="unavailable",
            source=source,
            runtime=runtime,
            diagnostics=(
                "optional Mermaid QA runtime is not installed; run "
                "bun install --cwd tools/mermaid-qa --frozen-lockfile explicitly"
            ),
        )

    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return _result(status="unavailable", source=source, runtime=runtime, diagnostics=str(error))
    version = package.get("version")
    if version != PINNED_VERSION:
        return _result(
            status="version_mismatch",
            source=source,
            runtime=runtime,
            version=str(version) if version is not None else None,
            diagnostics=f"expected exact {PINNED_PACKAGE} {PINNED_VERSION}, found {version!r}",
        )

    with tempfile.TemporaryDirectory(prefix="codesleuth-mermaid-qa-") as temporary:
        temp = Path(temporary)
        source_path = temp / "input.mmd"
        output_path = temp / "output.svg"
        mermaid_config = temp / "mermaid.json"
        puppeteer_config = temp / "puppeteer.json"
        source_path.write_bytes(source)
        mermaid_config.write_text(json.dumps({"securityLevel": "strict"}), encoding="utf-8")
        puppeteer_config.write_text(
            json.dumps(
                {
                    "headless": True,
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
        command = [
            "node",
            str(cli),
            "--input",
            str(source_path),
            "--output",
            str(output_path),
            "--configFile",
            str(mermaid_config),
            "--puppeteerConfigFile",
            str(puppeteer_config),
            "--quiet",
        ]
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", str(temp)),
            "TMP": os.environ.get("TMP", str(temp)),
            "NO_PROXY": "*",
            "no_proxy": "*",
        }
        try:
            completed = subprocess.run(
                command,
                cwd=temp,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return _result(
                status="error",
                source=source,
                runtime=runtime,
                version=version,
                diagnostics=str(error),
            )
        diagnostics = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        if completed.returncode != 0 or not output_path.is_file():
            return _result(
                status="fail",
                source=source,
                runtime=runtime,
                version=version,
                diagnostics=diagnostics or f"mmdc exited {completed.returncode} without SVG output",
            )
        svg = output_path.read_bytes()
        if b"<svg" not in svg[:2_000].lower():
            return _result(
                status="fail",
                source=source,
                runtime=runtime,
                version=version,
                svg=svg,
                diagnostics="renderer output is not recognizable SVG",
            )
        return _result(
            status="pass",
            source=source,
            runtime=runtime,
            version=version,
            svg=svg,
            diagnostics=diagnostics,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, help="Mermaid source file; stdin is used when omitted")
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()
    source = args.source.read_bytes() if args.source else sys.stdin.buffer.read(args.max_bytes + 1)
    result = validate_mermaid(
        source,
        runtime=args.runtime,
        max_bytes=max(1, args.max_bytes),
        timeout_seconds=max(1, args.timeout),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
