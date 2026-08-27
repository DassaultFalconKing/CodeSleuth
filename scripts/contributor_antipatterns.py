#!/usr/bin/env python3
"""CodeSleuth contributor anti-pattern scanner and mandatory pre-write checklist."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_TS_ROOTS = (
    Path("pack/.opencode/tools"),
)
RUNTIME_PY_ROOTS = (
    Path("pack/.opencode/bin"),
    Path("codesleuth_mcp"),
)

SEMANTIC_CHECKLIST = (
    ("SC-01", "Exact target/base identity is known; mutable branch/ref names are not being used as acceptance/source identity."),
    ("SC-02", "Current issue/roadmap/contract authority permits the change; deferred/retired work has a new adoption decision."),
    ("SC-03", "Existing no-argument/default caller behavior is known and will remain compatible unless deliberately versioned/broken."),
    ("SC-04", "Missing/absent state is distinct from degraded, unreadable, conflicted, parse/probe/dependency failure."),
    ("SC-05", "Product-visible support is no broader than the enabled runtime/platform matrix actually exercised by canonical gates."),
    ("SC-06", "Every new critical test path is reached by the canonical umbrella/workflow and non-skipped in at least one evidence profile."),
    ("SC-07", "Interpreter/provider/subprocess identity is explicit wherever correctness depends on a particular runtime."),
    ("SC-08", "Docs/CHANGELOG/PR wording will not claim PASS/support/completion beyond the exact evidence actually executed."),
    ("SC-09", "External provider output remains candidate data until CodeSleuth re-verifies exact source/blob/range and semantic mapping."),
    ("SC-10", "Optional dependency lifecycle is complete from an installed target: absent status, install/activate, use, removal."),
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str

    @property
    def blocking(self) -> bool:
        return self.severity == "ERROR"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _iter_files(root: Path, relative_roots: Iterable[Path], suffixes: tuple[str, ...]) -> Iterable[Path]:
    for relative in relative_roots:
        base = root / relative
        if not base.exists():
            continue
        if base.is_file() and base.suffix in suffixes:
            yield base
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if any(part in {".git", ".runtime", ".venv", "node_modules", "__pycache__"} for part in path.parts):
                continue
            yield path


def check_bun_smoke_registration(root: Path) -> list[Finding]:
    package_path = root / "package.json"
    if not package_path.is_file():
        return []
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [Finding("AP-CI-001", "ERROR", "package.json", 1, "package.json is unreadable; cannot prove Bun smoke reachability")]
    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return []
    main = scripts.get("test")
    if not isinstance(main, str):
        return [Finding("AP-CI-001", "ERROR", "package.json", 1, "package scripts.test is missing; canonical Bun smoke reachability is undefined")]

    smoke_re = re.compile(r"\bbun\s+(tests/[A-Za-z0-9_./-]+_smoke\.ts)\b")
    main_smokes = set(smoke_re.findall(main))
    findings: list[Finding] = []
    for name, command in scripts.items():
        if name == "test" or not name.startswith("test:") or not isinstance(command, str):
            continue
        for smoke in smoke_re.findall(command):
            if smoke not in main_smokes:
                findings.append(
                    Finding(
                        "AP-CI-001",
                        "ERROR",
                        "package.json",
                        1,
                        f"{name} exposes {smoke}, but the default scripts.test umbrella does not execute it",
                    )
                )
    return findings


_TS_AMBIENT_PYTHON = re.compile(
    r"""Bun\.spawn(?:Sync)?\s*\(\s*\[\s*["']python(?:3(?:\.\d+)?)?["']""",
    re.MULTILINE,
)
_PY_AMBIENT_PYTHON = re.compile(
    r"""subprocess\.(?:run|Popen|check_output|check_call)\s*\(\s*\[\s*["']python(?:3(?:\.\d+)?)?["']""",
    re.MULTILINE,
)


def check_ambient_python_runtime(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, RUNTIME_TS_ROOTS, (".ts", ".js")):
        text = _read_text(path)
        for match in _TS_AMBIENT_PYTHON.finditer(text):
            findings.append(
                Finding(
                    "AP-RUN-001",
                    "ERROR",
                    path.relative_to(root).as_posix(),
                    _line_number(text, match.start()),
                    "runtime code launches ambient python/python3 from PATH; use an explicit interpreter/runtime contract",
                )
            )
    for path in _iter_files(root, RUNTIME_PY_ROOTS, (".py",)):
        text = _read_text(path)
        for match in _PY_AMBIENT_PYTHON.finditer(text):
            findings.append(
                Finding(
                    "AP-RUN-001",
                    "ERROR",
                    path.relative_to(root).as_posix(),
                    _line_number(text, match.start()),
                    "runtime code launches ambient python/python3 from PATH; normally use sys.executable or an explicit runtime path",
                )
            )
    return findings


_RUNTIME_SKIP_RE = re.compile(
    r"""pytest\.skip\s*\(\s*["'][^"']*(?:optional|runtime|provider|dependency|installed|unavailable)[^"']*["']""",
    re.IGNORECASE,
)


def check_green_by_skip(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    tests = root / "tests"
    if not tests.is_dir():
        return findings
    for path in tests.glob("test_*.py"):
        text = _read_text(path)
        for match in _RUNTIME_SKIP_RE.finditer(text):
            findings.append(
                Finding(
                    "AP-CI-002",
                    "WARN",
                    path.relative_to(root).as_posix(),
                    _line_number(text, match.start()),
                    "runtime/dependency-dependent skip can make CI green without executing the enabled feature path; require a non-skipped canonical profile",
                )
            )
    return findings


def _function_chunks(text: str) -> Iterable[tuple[int, str, str]]:
    starts = list(re.finditer(r"(?m)^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        yield match.start(), match.group(1), text[match.start():end]


def check_mutable_identity_labels(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, RUNTIME_PY_ROOTS, (".py",)):
        text = _read_text(path)
        for offset, name, chunk in _function_chunks(text):
            lower_name = name.lower()
            if not any(token in lower_name for token in ("source", "identity", "label")):
                continue
            reads_mutable = bool(re.search(r"""get\(\s*["'](?:ref|branch|remote)["']""", chunk))
            reads_exact = bool(re.search(r"""get\(\s*["'](?:commit|sha|blob|hash|digest)["']""", chunk))
            if reads_mutable and not reads_exact:
                findings.append(
                    Finding(
                        "AP-ID-001",
                        "WARN",
                        path.relative_to(root).as_posix(),
                        _line_number(text, offset),
                        f"{name} consumes mutable source/ref/remote identity without an obvious exact commit/hash field",
                    )
                )
    return findings


def check_failure_absence_collapse(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(root, RUNTIME_PY_ROOTS, (".py",)):
        text = _read_text(path)
        if "except Exception" not in text:
            continue
        if not re.search(r"\b(reachable|exists|missing|present)\b", text):
            continue
        if not re.search(r"\b(pop\s*\(|unlink\s*\(|rmtree\s*\(|del\s+)", text):
            continue
        offset = text.find("except Exception")
        findings.append(
            Finding(
                "AP-STATE-001",
                "WARN",
                path.relative_to(root).as_posix(),
                _line_number(text, max(0, offset)),
                "broad probe failure and destructive/pruning signals coexist; verify that failure cannot be collapsed into absence",
            )
        )
    return findings


def scan_repository(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    findings.extend(check_bun_smoke_registration(root))
    findings.extend(check_ambient_python_runtime(root))
    findings.extend(check_green_by_skip(root))
    findings.extend(check_mutable_identity_labels(root))
    findings.extend(check_failure_absence_collapse(root))
    return sorted(findings, key=lambda item: (item.severity != "ERROR", item.rule_id, item.path, item.line))


def git_identity(root: Path) -> dict[str, str | None]:
    def run(*args: str) -> str | None:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return None
        if completed.returncode != 0:
            return None
        value = completed.stdout.strip()
        return value or None

    return {
        "head": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "status": run("status", "--porcelain"),
    }


def render_text(findings: list[Finding], *, include_checklist: bool, identity: dict[str, str | None]) -> str:
    lines = [
        "CodeSleuth contributor anti-pattern gate",
        f"HEAD: {identity.get('head') or 'unknown'}",
        f"branch: {identity.get('branch') or '(detached/unknown)'}",
    ]
    if identity.get("status"):
        lines.append("worktree: dirty")
    else:
        lines.append("worktree: clean or unavailable")
    if findings:
        lines.append("")
        lines.append("Findings:")
        for finding in findings:
            lines.append(
                f"- {finding.severity} {finding.rule_id} {finding.path}:{finding.line} - {finding.message}"
            )
    else:
        lines.extend(["", "Mechanical scan: PASS"])
    if include_checklist:
        lines.extend(["", "Mandatory semantic pre-write review:"])
        for rule_id, message in SEMANTIC_CHECKLIST:
            lines.append(f"- {rule_id}: {message}")
        lines.extend(
            [
                "",
                "If any semantic item is unresolved, do not guess the contract. Record UNRESOLVED/DEFER/BLOCK before implementing that part.",
                "Normative guidance: docs/CONTRIBUTOR-ERROR-PATTERNS.md",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("prewrite", "scan"), default="scan")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", help="return non-zero when mechanical ERROR findings exist")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = scan_repository(root)
    identity = git_identity(root)
    blocking = [finding for finding in findings if finding.blocking]
    payload = {
        "schemaVersion": 1,
        "command": args.command,
        "root": str(root),
        "identity": identity,
        "findings": [asdict(finding) for finding in findings],
        "blockingCount": len(blocking),
        "warningCount": sum(finding.severity == "WARN" for finding in findings),
        "semanticChecklist": [
            {"id": rule_id, "review": message} for rule_id, message in SEMANTIC_CHECKLIST
        ],
        "passed": not blocking,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(findings, include_checklist=args.command == "prewrite", identity=identity))

    if args.strict and blocking:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
