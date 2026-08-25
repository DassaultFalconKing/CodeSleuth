# CodeSleuth project lifecycle

This document defines the target-project contract for installing CodeSleuth as a reversible development tool.

## Independent runtime and dependency states

Runtime installation and source dependency are independent axes:

- **unbound-inactive**: neither installed runtime nor tracked dependency;
- **unbound-active**: runtime installed in `.opencode`, without a tracked CodeSleuth dependency;
- **bound-active**: runtime installed and exact CodeSleuth commit tracked at `tools/codesleuth`;
- **dependency-only** (bound-inactive): exact dependency retained while the installed runtime is absent, for example after `--uninstall --keep-dependency`;
- **uninstalled-preserved**: the active CodeSleuth runtime is removed, pre-install project config is restored, and known CodeSleuth traces are archived locally under `.codesleuth/archive`.
- **uninstalled-purged**: the active runtime, bound dependency, CodeSleuth backups and known local traces are removed after a conflict-safe restore. Restore-conflict evidence is retained when needed.

## First-install backup

CodeSleuth creates one durable pre-install snapshot before it first modifies project OpenCode configuration. Repeated updates reuse that original snapshot rather than redefining "before CodeSleuth" on every update.

The snapshot includes the target root `.gitignore` and `.gitmodules` for forensic recovery plus non-ephemeral files under `.opencode`. It excludes caches, logs, sessions, state, dependency directories and bytecode.

For an older target that already has review-pack metadata when 0.3 first sees it, the manifest records `pre-0.3-upgrade` rather than pretending the snapshot predates the historical installation.

Automatic uninstall compares each pre-existing file's pre-install, post-install, and current hashes. An unchanged installed file can be restored automatically. If a pre-existing file changed again after installation, its current worktree version is never overwritten: CodeSleuth retains baseline/current copies plus an explicit manifest under `.codesleuth/restore-conflicts/`. This recovery evidence survives purge. The target root `.gitignore` and `.gitmodules` are not blindly replaced. Current CodeSleuth installs do not write an ignore block to the root `.gitignore`; uninstall can still remove the exact managed block left by older CodeSleuth versions. CodeSleuth manages only its own submodule section/gitlink in `.gitmodules`.

## Ignore policy

During installation CodeSleuth adds a marked block to the repository-local Git exclude file returned by:

```bash
git rev-parse --git-path info/exclude
```

For an ordinary checkout this is `.git/info/exclude`. The managed patterns are:

```text
.codesleuth/*
!.codesleuth/reports/
.codesleuth/reports/*
!.codesleuth/reports/README.md
.opencode/state/
.opencode/cache/
.opencode/logs/
.opencode/sessions/
.opencode/snapshots/
.opencode/node_modules/
.opencode/**/__pycache__/
.opencode/**/*.pyc
```

The purpose is to keep CodeSleuth/OpenCode runtime noise local without silently dirtying or changing a tracked project `.gitignore`.

`.codesleuth/reports/` is the OpenCode-written analytical report store. Report bodies and `INDEX.md` stay locally excluded by default because they may contain secrets. `README.md` in that folder may be intentionally tracked so maintainers can share the convention. Format: `.opencode/CODESLEUTH-REPORTS.md`. Discovery pointer: a managed block in root `AGENTS.md` created/updated in the installed worktree.

Reports and the installer-created `AGENTS.md` pointer are worktree-local unless a maintainer intentionally commits sanitized material or repository guidance. Fresh clones therefore do not inherit local evidence by accident.

The dependency path `tools/codesleuth` is never added to that block. If an existing project rule ignores the proposed submodule path, binding fails closed rather than silently rewriting project ignore policy.

## Dependency binding

Binding uses normal Git submodule semantics:

```text
.gitmodules               -> where CodeSleuth is obtained
tools/codesleuth gitlink  -> exact CodeSleuth commit expected by this project
```

CodeSleuth stages those Git changes but does not create a target-project commit or push it.

Detached dependency checkouts are expected. Exact commit identity is authoritative; CodeSleuth does not infer a floating branch from `origin/HEAD`.

Binding and unbinding do not imply runtime install/uninstall. Use `codesleuth-project --unbind .` to remove only the dependency, or `--uninstall --keep-dependency` to remove only the runtime.

## Removal

`git submodule deinit` removes only a local checkout. A project-level dependency removal uses Git's tracked submodule removal (`git rm <submodule-path>`), which removes the superproject gitlink and the corresponding `.gitmodules` section. CodeSleuth refuses to discard a dirty worktree. It also compares the checked-out submodule HEAD with the superproject gitlink and fails closed when a clean detached checkout contains a different local/unpushed commit.

Git may keep the nested object database under the superproject's `.git/modules`; this is normal Git behavior and permits historical checkouts without re-fetching.

## Sensitive evidence

Preserved review state can contain credentials, API responses, source excerpts, or test diagnostics. The archive is locally excluded from Git by default. Users who intentionally version or publish audit reports are responsible for reviewing/sanitizing them first.

CodeSleuth does not guess at user-authored report locations outside its managed state. Such project files are never automatically deleted by uninstall.
