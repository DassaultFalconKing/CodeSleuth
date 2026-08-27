from __future__ import annotations

import subprocess
from pathlib import Path
from typing import BinaryIO

import pytest

from codesleuth_mcp.server import MAX_FILE_BYTES, RepositoryEvidence


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_read_evidence_never_performs_an_unbounded_file_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "codesleuth@example.invalid")
    git(tmp_path, "config", "user.name", "CodeSleuth Test")
    target = tmp_path / "large.txt"
    target.write_bytes(b"x" * (MAX_FILE_BYTES + 2))
    git(tmp_path, "add", "large.txt")
    git(tmp_path, "commit", "-m", "large tracked evidence")

    original_open = Path.open
    observed_read_sizes: list[int] = []

    class GuardedReader:
        def __init__(self, stream: BinaryIO) -> None:
            self.stream = stream

        def __enter__(self) -> "GuardedReader":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            self.stream.close()

        def read(self, size: int = -1) -> bytes:
            observed_read_sizes.append(size)
            assert size == MAX_FILE_BYTES + 1, "read_evidence must bound the actual filesystem read"
            return self.stream.read(size)

    def guarded_open(self: Path, mode: str = "r", *args, **kwargs):
        stream = original_open(self, mode, *args, **kwargs)
        if self == target and mode == "rb":
            return GuardedReader(stream)
        return stream

    monkeypatch.setattr(Path, "open", guarded_open)

    with pytest.raises(ValueError, match=f"file is larger than {MAX_FILE_BYTES} bytes"):
        RepositoryEvidence(tmp_path).read_evidence("large.txt")

    assert observed_read_sizes == [MAX_FILE_BYTES + 1]
