#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, **kwargs):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kwargs)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def init_target(path: Path, files):
    path.mkdir()
    run(["git", "init", str(path)])
    for name, content in files.items():
        (path / name).write_text(content, encoding="utf-8")
    run(["git", "-C", str(path), "add", *files.keys()])


def main():
    with tempfile.TemporaryDirectory(prefix="review-pack-test-") as td:
        tmp = Path(td)

        target = tmp / "target"
        init_target(target, {
            "Cargo.toml": '[package]\nname="x"\nversion="0.1.0"\nedition="2021"\n',
            "tsconfig.json": '{"compilerOptions":{"strict":true}}\n',
        })

        run([sys.executable, str(ROOT / "install.py"), str(target)])
        oc = target / ".opencode"
        meta = load(oc / "review-pack.json")
        assert meta["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        assert meta["complete"] is True
        detected = load(oc / "profiles" / "detected.json")["profiles"]
        assert "rust" in detected and "typescript" in detected
        assert (oc / "bin" / "review-pack-update.py").is_file()

        cfg_path = oc / "opencode.json"
        cfg = load(cfg_path)
        cfg["compaction"]["reserved"] = 12345
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

        reviewer = oc / "agents" / "repo-reviewer.md"
        reviewer.write_text(reviewer.read_text(encoding="utf-8") + "\nLOCAL USER CHANGE\n", encoding="utf-8")

        next_pack = tmp / "next-pack"
        shutil.copytree(ROOT, next_pack, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        (next_pack / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        scout = next_pack / "pack" / ".opencode" / "agents" / "repo-scout.md"
        scout.write_text(scout.read_text(encoding="utf-8") + "\nPACK UPDATE MARKER\n", encoding="utf-8")
        next_cfg_path = next_pack / "pack" / ".opencode" / "opencode.json"
        next_cfg = load(next_cfg_path)
        next_cfg["compaction"]["reserved"] = 30000
        next_cfg_path.write_text(json.dumps(next_cfg, indent=2) + "\n", encoding="utf-8")

        run([sys.executable, str(next_pack / "install.py"), str(target), "--update"])
        assert "LOCAL USER CHANGE" in reviewer.read_text(encoding="utf-8")
        assert "PACK UPDATE MARKER" in (oc / "agents" / "repo-scout.md").read_text(encoding="utf-8")
        assert load(cfg_path)["compaction"]["reserved"] == 12345
        assert load(oc / "review-pack-user.json")["runtime"]["compactionReserved"] == 12345

        meta2 = load(oc / "review-pack.json")
        assert meta2["version"] == "9.9.9"
        assert meta2["complete"] is False
        assert any(x["path"] == "agents/repo-reviewer.md" for x in meta2["conflicts"])
        assert any((oc / "state" / "update-conflicts").rglob("repo-reviewer.md.incoming"))
        run([sys.executable, str(oc / "bin" / "review-pack-smoke.py"), str(target)])

        legacy = tmp / "legacy"
        init_target(legacy, {"README.md": "legacy target\n"})
        legacy_oc = legacy / ".opencode"
        legacy_agent = legacy_oc / "agents" / "repo-reviewer.md"
        legacy_agent.parent.mkdir(parents=True, exist_ok=True)
        legacy_agent.write_text("OLD PRE-VERSIONED REVIEWER\n", encoding="utf-8")
        legacy_cfg = legacy_oc / "opencode.json"
        legacy_cfg.write_text('{"compaction":{"reserved":7777}}\n', encoding="utf-8")

        run([sys.executable, str(ROOT / "install.py"), str(legacy), "--adopt-existing-pack"])
        legacy_meta = load(legacy_oc / "review-pack.json")
        assert legacy_meta["adoptedLegacy"] is True
        assert legacy_meta["complete"] is True
        assert "OLD PRE-VERSIONED REVIEWER" not in legacy_agent.read_text(encoding="utf-8")
        assert load(legacy_cfg)["compaction"]["reserved"] == 7777
        backups = legacy_oc / "state" / "installer-backups" / "legacy-adoption"
        assert any(backups.rglob("repo-reviewer.md"))
        run([sys.executable, str(legacy_oc / "bin" / "review-pack-smoke.py"), str(legacy)])

        assert "install.py" in (ROOT / "install.sh").read_text(encoding="utf-8")
        assert "install.py" in (ROOT / "install.ps1").read_text(encoding="utf-8")
        assert "review-pack-update.py" in (ROOT / "pack" / ".opencode" / "bin" / "review-pack-update").read_text(encoding="utf-8")
        assert "review-pack-update.py" in (ROOT / "pack" / ".opencode" / "bin" / "review-pack-update.ps1").read_text(encoding="utf-8")

        print("LIFECYCLE TEST PASS")


if __name__ == "__main__":
    main()
