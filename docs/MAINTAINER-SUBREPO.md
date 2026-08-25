# CodeSleuth Maintainer Guide

CodeSleuth is now the standalone source authority for the repository auditor originally extracted from Aleph_Rugent. Consumer projects should not carry editable copies of CodeSleuth source.

## Ownership model

```text
DassaultFalconKing/CodeSleuth
        ↓ exact Git submodule/gitlink
consumer/tools/codesleuth
        ↓ materialized project runtime
consumer/.opencode
```

The standalone repository owns auditor implementation, tests, generic profiles and release semantics. A consumer project owns only:

- the exact CodeSleuth commit it pins;
- its `.opencode` policy/profile/runtime contract;
- its local ignored state/backups.

Project-specific modifications must not be made inside the submodule checkout. Dirty worktrees and clean detached HEADs that differ from the recorded gitlink are both treated as local CodeSleuth source work; removal fails closed rather than discarding either form.

## Import provenance

The first standalone import was derived from:

```text
DassaultFalconKing/Aleph_Rugent
commit b00f83b81d50b2ac804fd24c83df0db86fe01c00
subtree opencode-repo-review-pack/
```

The initial imported tree was exactly:

```text
0037ea6c33584bc280dfc9152d623125d35f2f15
```

Do not recreate a second canonical copy in Aleph or another consumer.

## Release gates

Before tagging a CodeSleuth release, run at least:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
ruff check .
python3 tests/test_lifecycle.py
bun install --frozen-lockfile
bun tests/review_state_smoke.ts
```

Also exercise the pinned `textual==8.2.8` app in headless mode. `ReviewPackApp` remains a compatibility class name, but it must never override Textual `App.log`.

A release that advertises cross-platform support should execute PowerShell/Windows launcher coverage as well as Linux/Ubuntu coverage.

## Project dependency contract

`git submodule add` creates the submodule configuration and stages the superproject gitlink. The gitlink is the exact CodeSleuth commit required by that consumer. CodeSleuth does not commit or push the consumer repository automatically.

For normal development repositories, prefer a pinned dependency over a floating updater. Detached submodule HEAD is expected and must not be converted into an inferred `main`/`origin/HEAD` update channel.

Fresh clones must initialize the dependency explicitly:

```bash
git clone --recurse-submodules <consumer-url>
# or, after an ordinary clone:
git submodule update --init --recursive
```

## Update workflow for a consumer

1. accept/test a CodeSleuth release or SHA in this repository;
2. move the consumer's `tools/codesleuth` checkout to that exact SHA;
3. run the pinned checkout's `install.sh . --update`;
4. inspect `.opencode` materialization and local smoke output;
5. commit the gitlink and intended project contract together.

This creates a reproducible relationship between application source, auditor source, and auditor policy.

To revert a pin, checkout an earlier accepted SHA in `tools/codesleuth`, run that checkout's installer with `--update`, inspect the materialized diff, and commit the reverted gitlink plus intended `.opencode` changes together. Target-local `review-pack-update*` compatibility scripts are a floating-source path only when metadata contains an explicit `remote + ref`; they are not the advancement mechanism for a detached pin.

## Reversible installation

CodeSleuth 0.3+ creates a pre-install baseline under `.codesleuth/backups/pre-install/`. It backs up non-ephemeral `.opencode` configuration plus root `.gitignore`/`.gitmodules` for recovery evidence.

Uninstall uses pre-install/post-install/current hashes. A post-install edit to a pre-existing `.opencode` file remains in the worktree, with baseline/current recovery copies and a conflict manifest under ignored `.codesleuth/restore-conflicts/`. Purge removes ordinary backups and traces but retains required conflict evidence. Root Git control files are never blindly restored.

For an older installation first seen after upgrading to 0.3, the snapshot is marked `pre-0.3-upgrade`; do not misrepresent it as a historical pre-CodeSleuth snapshot.

## Sensitive evidence policy

CodeSleuth can inspect/run developer-authorized application workflows. Those workflows may use credentials. Local review state and archives are ignored by default, but maintainers must not claim universal secret redaction.

Never publish generated reports or preserved traces without inspecting them for secrets. CodeSleuth deliberately avoids deleting arbitrary user-authored report files outside its managed namespaces.

## Permission boundary

Built-in profiles are permission-neutral. They may describe stack detection, verification commands, review focus, compaction or watcher hints, but they must not silently turn `deny`/`ask` into `allow` for web, edit, shell or external-directory access.

The TUI/project policy layer is the only owner of those explicit permission choices.

## Compatibility surface

The following historical names remain during migration:

```text
review-pack
review-pack.json
review-pack-user.json
ReviewPackApp
```

New product-facing entrypoints are named `codesleuth`. Compatibility removal should be a separately versioned change after downstream projects have migrated.

## Watchdog follow-up

The current OpenCode keepalive watchdog stays functional. The stronger watchdog/recovery design from Aleph_Rugent should be integrated as a dedicated runtime feature after the project lifecycle is accepted. Do not couple watchdog failure handling to Git dependency mutation or backup/restore semantics.
