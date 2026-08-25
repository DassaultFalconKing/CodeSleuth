from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

from codesleuth_mcp.server import RepositoryEvidence, create_server  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "codesleuth@example.invalid")
    git(tmp_path, "config", "user.name", "CodeSleuth Test")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "hello.py").write_text("def hello():\n    return 'hello'\n", encoding="utf-8", newline="\n")
    (tmp_path / "tests" / "test_hello.py").write_text(
        "from src.hello import hello\n\ndef test_hello():\n    assert hello() == 'hello'\n",
        encoding="utf-8",
        newline="\n",
    )
    (tmp_path / "README.md").write_text("# fixture\n", encoding="utf-8", newline="\n")
    git(tmp_path, "add", "README.md", "src/hello.py", "tests/test_hello.py")
    git(tmp_path, "commit", "-m", "fixture")
    return tmp_path


def test_overview_and_inventory_are_bound_to_git(repository: Path) -> None:
    evidence = RepositoryEvidence(repository / "src")
    overview = evidence.overview()
    inventory = evidence.inventory(limit=2)
    assert evidence.root == repository.resolve()
    assert overview["trackedFiles"] == 3
    assert overview["dirty"] is False
    assert inventory["total"] == 3
    assert len(inventory["files"]) == 2
    assert inventory["nextCursor"] == 2
    assert all(len(item["blob"]) == 40 for item in inventory["files"])


def test_repository_binding_ignores_inherited_git_redirects(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    git(redirected, "init")
    git(redirected, "config", "user.email", "redirected@example.invalid")
    git(redirected, "config", "user.name", "Redirected Test")
    (redirected / "wrong.txt").write_text("wrong repository\n", encoding="utf-8")
    git(redirected, "add", "wrong.txt")
    git(redirected, "commit", "-m", "redirected")

    monkeypatch.setenv("GIT_DIR", str(redirected / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(redirected))
    evidence = RepositoryEvidence(repository)

    assert evidence.root == repository.resolve()
    assert {item["path"] for item in evidence.inventory(limit=100)["files"]} == {
        "README.md",
        "src/hello.py",
        "tests/test_hello.py",
    }


def test_overview_does_not_refresh_or_write_the_index(repository: Path) -> None:
    index = Path(git(repository, "rev-parse", "--git-path", "index").strip())
    if not index.is_absolute():
        index = repository / index
    before = index.read_bytes()
    tracked = repository / "README.md"
    stat = tracked.stat()
    os.utime(tracked, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))

    assert RepositoryEvidence(repository).overview()["dirty"] is False
    assert index.read_bytes() == before


def test_overview_does_not_invoke_configured_fsmonitor(repository: Path) -> None:
    marker = repository / "fsmonitor-invoked"
    hook = repository / "fsmonitor.sh"
    hook.write_text(
        f'#!/bin/sh\nprintf invoked > "{marker.as_posix()}"\nexit 1\n',
        encoding="utf-8",
        newline="\n",
    )
    hook.chmod(0o755)
    git(repository, "config", "core.fsmonitor", hook.as_posix())

    git(repository, "status", "--porcelain=v1")
    assert marker.exists(), "negative control: configured fsmonitor hook was not executable"
    marker.unlink()

    RepositoryEvidence(repository).overview()
    assert not marker.exists()


def test_exact_source_and_search_carry_line_evidence(repository: Path) -> None:
    evidence = RepositoryEvidence(repository)
    source = evidence.read_evidence("src/hello.py", 1, 2)
    matches = evidence.search("return 'hello'")
    assert source["workingBlob"] == source["indexBlob"]
    assert source["lines"] == [
        {"line": 1, "text": "def hello():"},
        {"line": 2, "text": "    return 'hello'"},
    ]
    assert matches["matches"] == [{"path": "src/hello.py", "line": 2, "text": "    return 'hello'"}]


def test_search_fetches_one_extra_match_before_reporting_truncation(repository: Path) -> None:
    target = repository / "src" / "matches.txt"
    target.write_text("EXACT_TOKEN one\nEXACT_TOKEN two\n", encoding="utf-8", newline="\n")
    git(repository, "add", "src/matches.txt")
    git(repository, "commit", "-m", "two matches")

    exact = RepositoryEvidence(repository).search("EXACT_TOKEN", limit=2)
    assert len(exact["matches"]) == 2
    assert exact["truncated"] is False

    target.write_text(
        "EXACT_TOKEN one\nEXACT_TOKEN two\nEXACT_TOKEN three\n",
        encoding="utf-8",
        newline="\n",
    )
    extra = RepositoryEvidence(repository).search("EXACT_TOKEN", limit=2)
    assert len(extra["matches"]) == 2
    assert extra["truncated"] is True


def test_path_escape_and_untracked_files_fail_closed(repository: Path) -> None:
    evidence = RepositoryEvidence(repository)
    (repository / "secret.txt").write_text("not tracked", encoding="utf-8")
    with pytest.raises(ValueError, match="tracked file"):
        evidence.read_evidence("secret.txt")
    with pytest.raises(ValueError, match="inside the repository"):
        evidence.read_evidence("../outside.txt")


def test_tracked_symlink_cannot_expose_untracked_target(repository: Path) -> None:
    secret = repository / "secret.txt"
    secret.write_text("UNTRACKED SECRET\n", encoding="utf-8", newline="\n")
    link = repository / "source-link.txt"
    try:
        link.symlink_to(secret.name)
        git(repository, "add", "source-link.txt")
    except OSError:
        link.write_text(secret.name, encoding="utf-8", newline="")
        blob = git(repository, "hash-object", "-w", "source-link.txt").strip()
        git(repository, "update-index", "--add", "--cacheinfo", f"120000,{blob},source-link.txt")
    git(repository, "commit", "-m", "tracked symlink")
    assert git(repository, "ls-files", "--stage", "source-link.txt").startswith("120000 ")

    with pytest.raises(ValueError, match=r"not a regular tracked file.*mode 120000") as captured:
        RepositoryEvidence(repository).read_evidence("source-link.txt")

    assert "UNTRACKED SECRET" not in str(captured.value)


def test_regular_index_entry_replaced_by_working_symlink_fails_closed(repository: Path) -> None:
    secret = repository / "secret.txt"
    secret.write_text("UNTRACKED SECRET\n", encoding="utf-8", newline="\n")
    tracked = repository / "README.md"
    tracked.unlink()
    try:
        tracked.symlink_to(secret.name)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    with pytest.raises(ValueError, match="working path is not a regular file") as captured:
        RepositoryEvidence(repository).read_evidence("README.md")

    assert "UNTRACKED SECRET" not in str(captured.value)


def test_gitlink_cannot_be_returned_as_source_evidence(repository: Path) -> None:
    head = git(repository, "rev-parse", "HEAD").strip()
    git(repository, "update-index", "--add", "--cacheinfo", f"160000,{head},vendor/dependency")
    assert git(repository, "ls-files", "--stage", "vendor/dependency").startswith("160000 ")

    with pytest.raises(ValueError, match=r"not a regular tracked file.*mode 160000"):
        RepositoryEvidence(repository).read_evidence("vendor/dependency")


def test_test_map_is_explicitly_not_coverage(repository: Path) -> None:
    result = RepositoryEvidence(repository).test_map()
    paths = {item["path"] for item in result["candidates"]}
    assert "tests/test_hello.py" in paths
    assert "coverage" in result["warning"]


def test_diff_is_bounded_and_tied_to_head(repository: Path) -> None:
    (repository / "README.md").write_text("# changed\n" + ("diff payload\n" * 20_000), encoding="utf-8", newline="\n")
    result = RepositoryEvidence(repository).diff_evidence()
    assert "README.md" in result["diff"]
    assert len(result["headSha"]) == 40
    assert len(result["diff"]) <= 40_000
    assert result["truncated"] is True


def test_diff_does_not_invoke_configured_textconv(repository: Path) -> None:
    marker = repository / "textconv-invoked"
    script = repository / "textconv.py"
    script.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        f"Path({str(marker)!r}).write_text('invoked', encoding='utf-8')\n"
        "sys.stdout.buffer.write(Path(sys.argv[1]).read_bytes())\n",
        encoding="utf-8",
        newline="\n",
    )
    (repository / ".gitattributes").write_text("*.txt diff=marker\n", encoding="utf-8", newline="\n")
    target = repository / "sample.txt"
    target.write_text("before\n", encoding="utf-8", newline="\n")
    git(repository, "add", ".gitattributes", "sample.txt")
    git(repository, "commit", "-m", "textconv fixture")
    textconv = f'"{Path(sys.executable).as_posix()}" "{script.as_posix()}"'
    git(repository, "config", "diff.marker.textconv", textconv)
    target.write_text("after\n", encoding="utf-8", newline="\n")

    git(repository, "diff", "--textconv")
    assert marker.exists(), "negative control: configured textconv command was not invoked"
    marker.unlink()

    RepositoryEvidence(repository).diff_evidence()
    assert not marker.exists()


def test_unresolved_merge_stages_fail_closed(repository: Path) -> None:
    base_branch = git(repository, "branch", "--show-current").strip()
    git(repository, "checkout", "-b", "conflicting-side")
    (repository / "README.md").write_text("# side\n", encoding="utf-8", newline="\n")
    git(repository, "commit", "-am", "side")
    git(repository, "checkout", base_branch)
    (repository / "README.md").write_text("# base\n", encoding="utf-8", newline="\n")
    git(repository, "commit", "-am", "base")
    merge = subprocess.run(
        ["git", "-C", str(repository), "merge", "conflicting-side"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert merge.returncode != 0

    with pytest.raises(RuntimeError, match=r"unresolved index stages for README\.md: 1, 2, 3"):
        RepositoryEvidence(repository).inventory()


def test_mcp_surface_has_only_bounded_repository_tools(repository: Path) -> None:
    server = create_server(repository)
    names = {tool.name for tool in server._tool_manager.list_tools()}
    assert names == {"overview", "inventory", "read_evidence", "search", "test_map", "diff_evidence"}


def test_stdio_tool_call_does_not_let_git_consume_the_mcp_wire(repository: Path) -> None:
    async def probe() -> None:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "codesleuth_mcp.server", "--repo", str(repository)],
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                result = await asyncio.wait_for(session.call_tool("overview", {}), timeout=10)
                assert result.isError is False
                assert result.structuredContent["trackedFiles"] == 3

    asyncio.run(probe())
