from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import threading
from collections import Counter
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

from mcp.server.fastmcp import FastMCP


MAX_FILE_BYTES = 1_000_000
MAX_READ_LINES = 400
MAX_SEARCH_RESULTS = 200
MAX_SEARCH_BYTES = 2_000_000
MAX_DIFF_CHARS = 40_000
MAX_GIT_STDERR_BYTES = 64_000
REGULAR_FILE_MODES = frozenset({"100644", "100755"})


def _trace(message: str) -> None:
    if os.environ.get("CODESLEUTH_MCP_DEBUG"):
        print(f"codesleuth-mcp: {message}", file=sys.stderr, flush=True)


def _git_environment() -> dict[str, str]:
    """Return a non-interactive Git environment without caller-controlled repository redirects."""

    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    environment.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _search_records(raw: bytes, limit: int | None = None) -> list[dict[str, Any]]:
    """Parse complete ``git grep -n -z`` records, ignoring a partial trailing record."""

    parts = raw.split(b"\0")
    matches: list[dict[str, Any]] = []
    index = 0
    while index + 2 < len(parts) and (limit is None or len(matches) < limit):
        path_bytes, line_bytes, remainder = parts[index], parts[index + 1], parts[index + 2]
        if not path_bytes:
            break
        content, separator, tail = remainder.partition(b"\n")
        if not separator:
            break
        matches.append(
            {
                "path": path_bytes.decode("utf-8", errors="replace").replace("\\", "/"),
                "line": int(line_bytes.decode("ascii")),
                "text": content.decode("utf-8", errors="replace"),
            }
        )
        if tail:
            parts[index + 2] = tail
            index += 2
        else:
            index += 3
    return matches


class RepositoryEvidence:
    """Deterministic, bounded evidence captured from one Git worktree."""

    def __init__(self, requested_root: str | os.PathLike[str]) -> None:
        requested = Path(requested_root).resolve()
        self._git_env = _git_environment()
        completed = subprocess.run(
            self._command(requested, "rev-parse", "--show-toplevel"),
            check=False,
            env=self._git_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(message or f"not a Git worktree: {requested}")
        self.root = Path(completed.stdout.decode("utf-8", errors="strict").strip()).resolve()

    @staticmethod
    def _command(root: Path, *args: str) -> list[str]:
        # `core.fsmonitor=false` prevents both an external fsmonitor hook and Git's built-in daemon
        # from being started by an evidence probe. It is a command-scoped override so repository and
        # user configuration cannot widen this boundary.
        return ["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(root), *args]

    def _git_bytes(self, *args: str, allow_no_match: bool = False) -> bytes:
        _trace(f"git start: {' '.join(args)}")
        completed = subprocess.run(
            self._command(self.root, *args),
            check=False,
            # MCP stdio owns the process stdin. A child that inherits it can consume or hold the
            # JSON-RPC wire; on Windows even `git status` then left tools/list healthy while every
            # tools/call timed out. Repository probes are non-interactive by contract.
            stdin=subprocess.DEVNULL,
            env=self._git_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _trace(f"git complete ({completed.returncode}): {' '.join(args)}")
        if completed.returncode != 0 and not (allow_no_match and completed.returncode == 1):
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"git {' '.join(args)} failed with {completed.returncode}")
        return completed.stdout

    def _git_bytes_bounded(
        self,
        *args: str,
        max_bytes: int,
        stop_when: Callable[[bytes], bool] | None = None,
        allow_no_match: bool = False,
    ) -> tuple[bytes, bool]:
        """Stream Git output, terminating once a byte or semantic evidence budget is reached."""

        _trace(f"git bounded start: {' '.join(args)}")
        process = subprocess.Popen(
            self._command(self.root, *args),
            env=self._git_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if process.stdout is None or process.stderr is None:  # pragma: no cover - guaranteed by PIPE
            process.kill()
            raise RuntimeError("Git evidence process did not expose output pipes")

        stderr = bytearray()

        def drain_stderr() -> None:
            while chunk := process.stderr.read(8192):
                remaining = MAX_GIT_STDERR_BYTES - len(stderr)
                if remaining > 0:
                    stderr.extend(chunk[:remaining])

        stderr_thread = threading.Thread(target=drain_stderr, name="codesleuth-git-stderr", daemon=True)
        stderr_thread.start()

        stdout = bytearray()
        stopped = False
        try:
            while chunk := process.stdout.read1(65536):
                remaining = max_bytes + 1 - len(stdout)
                if remaining > 0:
                    stdout.extend(chunk[:remaining])
                if len(stdout) > max_bytes or (stop_when is not None and stop_when(bytes(stdout))):
                    stopped = True
                    if process.poll() is None:
                        try:
                            process.terminate()
                        except ProcessLookupError:
                            pass
                    break
            if stopped:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            else:
                process.wait()
        finally:
            process.stdout.close()
            stderr_thread.join(timeout=2)
            process.stderr.close()

        _trace(f"git bounded complete ({process.returncode}): {' '.join(args)}")
        if not stopped and process.returncode != 0 and not (allow_no_match and process.returncode == 1):
            message = bytes(stderr).decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"git {' '.join(args)} failed with {process.returncode}")
        return bytes(stdout[:max_bytes]), stopped

    def _git(self, *args: str, allow_no_match: bool = False) -> str:
        return self._git_bytes(*args, allow_no_match=allow_no_match).decode("utf-8", errors="replace")

    def _records(self) -> list[dict[str, str]]:
        raw = self._git_bytes("ls-files", "-s", "-z")
        records: list[dict[str, str]] = []
        for item in raw.split(b"\0"):
            if not item:
                continue
            metadata, separator, path_bytes = item.partition(b"\t")
            if not separator:
                raise RuntimeError("unexpected git ls-files record")
            fields = metadata.decode("ascii", errors="strict").split()
            records.append(
                {
                    "mode": fields[0],
                    "blob": fields[1],
                    "stage": fields[2],
                    "path": path_bytes.decode("utf-8", errors="replace").replace("\\", "/"),
                }
            )
        by_path: dict[str, list[dict[str, str]]] = {}
        for record in records:
            by_path.setdefault(record["path"], []).append(record)
        for path, path_records in by_path.items():
            if len(path_records) != 1 or path_records[0]["stage"] != "0":
                stages = ", ".join(record["stage"] for record in path_records)
                raise RuntimeError(f"unresolved index stages for {path}: {stages}")
        return records

    def _safe_tracked_path(self, raw_path: str) -> tuple[str, dict[str, str]]:
        normalized = raw_path.replace("\\", "/").removeprefix("./")
        candidate = PurePosixPath(normalized)
        if not normalized or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"path must name a tracked file inside the repository: {raw_path}")
        value = candidate.as_posix()
        record = next((item for item in self._records() if item["path"] == value), None)
        if record is None:
            raise ValueError(f"path is not a tracked file: {value}")
        if record["mode"] not in REGULAR_FILE_MODES:
            raise ValueError(f"path is not a regular tracked file: {value} (mode {record['mode']})")
        absolute = self.root / Path(*candidate.parts)
        try:
            working_mode = absolute.lstat().st_mode
        except FileNotFoundError as error:
            raise ValueError(f"tracked file is missing from the working tree: {value}") from error
        if not stat.S_ISREG(working_mode):
            raise ValueError(f"working path is not a regular file: {value}")
        resolved = absolute.resolve()
        if self.root != resolved and self.root not in resolved.parents:
            raise ValueError(f"path escapes repository: {raw_path}")
        return value, record

    def _working_blob(self, path: str) -> str:
        return self._git("hash-object", "--", path).strip()

    @staticmethod
    def _extension(path: str) -> str:
        suffix = PurePosixPath(path).suffix.lower()
        return suffix or "<none>"

    def overview(self) -> dict[str, Any]:
        records = self._records()
        paths = [record["path"] for record in records]
        status_lines = [line for line in self._git("status", "--porcelain=v1").splitlines() if line]
        top_level = Counter(path.split("/", 1)[0] if "/" in path else "<root>" for path in paths)
        extensions = Counter(self._extension(path) for path in paths)
        root_files = sorted(path for path in paths if "/" not in path)
        return {
            "repositoryRoot": str(self.root),
            "headSha": self._git("rev-parse", "HEAD").strip(),
            "branch": self._git("branch", "--show-current").strip() or None,
            "dirty": bool(status_lines),
            "status": status_lines[:100],
            "trackedFiles": len(records),
            "rootFiles": root_files[:100],
            "topLevel": [{"name": name, "count": count} for name, count in top_level.most_common(40)],
            "extensions": [{"name": name, "count": count} for name, count in extensions.most_common(40)],
        }

    def inventory(self, prefix: str = "", cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        normalized = prefix.replace("\\", "/").strip("/").removeprefix("./")
        if ".." in PurePosixPath(normalized).parts:
            raise ValueError("prefix must stay inside the repository")
        records = self._records()
        scoped = [
            record
            for record in records
            if not normalized or record["path"] == normalized or record["path"].startswith(normalized + "/")
        ]
        page = scoped[cursor : cursor + limit]
        next_cursor = cursor + len(page) if cursor + len(page) < len(scoped) else None
        return {
            "headSha": self._git("rev-parse", "HEAD").strip(),
            "scope": normalized or ".",
            "total": len(scoped),
            "cursor": cursor,
            "nextCursor": next_cursor,
            "files": page,
        }

    def read_evidence(self, path: str, start_line: int = 1, end_line: int = 200) -> dict[str, Any]:
        safe_path, record = self._safe_tracked_path(path)
        if start_line < 1 or end_line < start_line:
            raise ValueError("line range must be positive and ordered")
        if end_line - start_line + 1 > MAX_READ_LINES:
            raise ValueError(f"at most {MAX_READ_LINES} lines may be read at once")
        absolute = self.root / Path(*PurePosixPath(safe_path).parts)
        payload = absolute.read_bytes()
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError(f"file is larger than {MAX_FILE_BYTES} bytes")
        if b"\0" in payload:
            raise ValueError("binary files cannot be returned as source evidence")
        text = payload.decode("utf-8", errors="replace")
        lines = text.splitlines()
        selected = lines[start_line - 1 : end_line]
        numbered = [{"line": start_line + offset, "text": value} for offset, value in enumerate(selected)]
        return {
            "path": safe_path,
            "workingBlob": self._working_blob(safe_path),
            "indexBlob": record["blob"],
            "lineCount": len(lines),
            "startLine": start_line,
            "endLine": start_line + len(numbered) - 1 if numbered else start_line - 1,
            "lines": numbered,
        }

    def search(
        self,
        pattern: str,
        path_prefix: str = "",
        limit: int = 100,
        fixed_strings: bool = True,
    ) -> dict[str, Any]:
        if not pattern:
            raise ValueError("pattern must not be empty")
        if not 1 <= limit <= MAX_SEARCH_RESULTS:
            raise ValueError(f"limit must be between 1 and {MAX_SEARCH_RESULTS}")
        prefix = path_prefix.replace("\\", "/").strip("/").removeprefix("./")
        if ".." in PurePosixPath(prefix).parts:
            raise ValueError("path_prefix must stay inside the repository")
        args = ["grep", "-n", "-z", "-I"]
        if fixed_strings:
            args.append("-F")
        args.extend(["-e", pattern])
        if prefix:
            args.extend(["--", prefix])
        raw, stream_truncated = self._git_bytes_bounded(
            *args,
            max_bytes=MAX_SEARCH_BYTES,
            stop_when=lambda output: len(_search_records(output, limit + 1)) > limit,
            allow_no_match=True,
        )
        discovered = _search_records(raw, limit + 1)
        matches = discovered[:limit]
        return {
            "pattern": pattern,
            "fixedStrings": fixed_strings,
            "pathPrefix": prefix or ".",
            "matches": matches,
            "truncated": stream_truncated or len(discovered) > limit,
        }

    def test_map(self, cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        if cursor < 0 or not 1 <= limit <= 500:
            raise ValueError("cursor must be non-negative and limit must be between 1 and 500")
        markers = {
            "makefile.am",
            "makefile.in",
            "configure.ac",
            "configure",
            "meson.build",
            "cmakelists.txt",
            "package.json",
            "pyproject.toml",
            "cargo.toml",
        }
        candidates: list[dict[str, str]] = []
        for record in self._records():
            path = record["path"]
            lowered = path.lower()
            name = PurePosixPath(lowered).name
            parts = PurePosixPath(lowered).parts
            if (
                any(part in {"test", "tests", "testing", "spec", "specs"} for part in parts)
                or name.startswith("test_")
                or name.endswith(("_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))
                or name in markers
                or lowered.startswith(".github/workflows/")
            ):
                candidates.append({"path": path, "blob": record["blob"]})
        page = candidates[cursor : cursor + limit]
        next_cursor = cursor + len(page) if cursor + len(page) < len(candidates) else None
        return {
            "headSha": self._git("rev-parse", "HEAD").strip(),
            "totalCandidates": len(candidates),
            "cursor": cursor,
            "nextCursor": next_cursor,
            "candidates": page,
            "warning": "This maps likely test/build surfaces; it does not claim executed or measured coverage.",
        }

    def diff_evidence(self, staged: bool = False) -> dict[str, Any]:
        args = ["diff", "--no-ext-diff", "--no-textconv", "--unified=3"]
        if staged:
            args.append("--cached")
        raw, stream_truncated = self._git_bytes_bounded(*args, max_bytes=MAX_DIFF_CHARS * 4 + 4)
        text = raw.decode("utf-8", errors="replace")
        return {
            "headSha": self._git("rev-parse", "HEAD").strip(),
            "staged": staged,
            "diff": text[:MAX_DIFF_CHARS],
            "truncated": stream_truncated or len(text) > MAX_DIFF_CHARS,
        }


def create_server(repository: str | os.PathLike[str]) -> FastMCP:
    evidence = RepositoryEvidence(repository)
    server = FastMCP(
        "CodeSleuth",
        instructions=(
            "Evidence-first repository intelligence for one fixed Git worktree. "
            "Treat returned blob hashes and exact line ranges as evidence. Reopen exact source before material claims. "
            "A test map is not measured coverage, and a Mermaid or inferred relationship is never source authority."
        ),
        log_level="WARNING",
    )

    @server.tool(name="overview", structured_output=True)
    def overview() -> dict[str, Any]:
        """Return Git identity, dirty state, tracked-file counts, root files, and bounded shape summaries."""
        _trace("overview start")
        result = evidence.overview()
        _trace("overview complete")
        return result

    @server.tool(name="inventory", structured_output=True)
    def inventory(prefix: str = "", cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        """List tracked paths with exact index blob ids using a bounded, cursor-based Git inventory."""
        return evidence.inventory(prefix=prefix, cursor=cursor, limit=limit)

    @server.tool(name="read_evidence", structured_output=True)
    def read_evidence(path: str, start_line: int = 1, end_line: int = 200) -> dict[str, Any]:
        """Read a bounded line range from a tracked text file with current and index blob identities."""
        return evidence.read_evidence(path=path, start_line=start_line, end_line=end_line)

    @server.tool(name="search", structured_output=True)
    def search(
        pattern: str,
        path_prefix: str = "",
        limit: int = 100,
        fixed_strings: bool = True,
    ) -> dict[str, Any]:
        """Run bounded Git grep over tracked text, returning exact path, line, and matching text."""
        return evidence.search(
            pattern=pattern,
            path_prefix=path_prefix,
            limit=limit,
            fixed_strings=fixed_strings,
        )

    @server.tool(name="test_map", structured_output=True)
    def test_map(cursor: int = 0, limit: int = 100) -> dict[str, Any]:
        """Map likely test, build, and CI files without falsely claiming measured test coverage."""
        return evidence.test_map(cursor=cursor, limit=limit)

    @server.tool(name="diff_evidence", structured_output=True)
    def diff_evidence(staged: bool = False) -> dict[str, Any]:
        """Return a bounded working-tree or staged diff tied to the current HEAD."""
        return evidence.diff_evidence(staged=staged)

    @server.prompt(name="repository_review")
    def repository_review(objective: str = "Audit this repository") -> str:
        """Evidence-disciplined repository review workflow for any MCP-capable agent host."""
        return (
            f"Objective: {objective}\n"
            "1. Call overview and inventory before forming an architecture claim.\n"
            "2. Use test_map only to locate test/build surfaces; run relevant tests before claiming coverage.\n"
            "3. Use search to locate relationships, then read_evidence to verify exact source lines.\n"
            "4. Distinguish verified facts, inferences, and unverified questions.\n"
            "5. Cite every material finding as path:start-end plus workingBlob.\n"
            "6. Do not edit the repository unless the user separately authorizes implementation."
        )

    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve CodeSleuth repository evidence over MCP stdio.")
    parser.add_argument("--repo", required=True, help="Git worktree CodeSleuth is allowed to inspect")
    parser.add_argument("--describe", action="store_true", help="Print server binding as JSON and exit")
    args = parser.parse_args(argv)
    evidence = RepositoryEvidence(args.repo)
    if args.describe:
        print(json.dumps(evidence.overview(), indent=2))
        return 0
    create_server(str(evidence.root)).run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
