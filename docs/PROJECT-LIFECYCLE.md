# CodeSleuth project lifecycle

This document defines the target-project contract for installing CodeSleuth as a reversible development tool.

## States

- **unbound**: CodeSleuth may be installed into `.opencode`, but the project does not track the CodeSleuth source repository.
- **bound**: the project tracks an exact CodeSleuth commit as `tools/codesleuth` Git submodule/gitlink.
- **uninstalled-preserved**: the active CodeSleuth runtime is removed, pre-install project config is restored, and known CodeSleuth traces are archived locally under `.codesleuth/archive`.
- **uninstalled-purged**: the active runtime, bound dependency, CodeSleuth backups and known local traces are removed after restoring the pre-install project config.

## First-install backup

CodeSleuth creates one durable pre-install snapshot before it first modifies project OpenCode configuration. Repeated updates reuse that original snapshot rather than redefining "before CodeSleuth" on every update.

The snapshot includes the target root `.gitignore` and `.gitmodules` for forensic recovery plus non-ephemeral files under `.opencode`. It excludes caches, logs, sessions, state, dependency directories and bytecode.

For an older target that already has review-pack metadata when 0.3 first sees it, the manifest records `pre-0.3-upgrade` rather than pretending the snapshot predates the historical installation.

Automatic uninstall restores backed-up `.opencode` files. The target root `.gitignore` and `.gitmodules` are not blindly replaced, because doing so could erase unrelated changes made after installation; CodeSleuth manages only its marked ignore block and its own submodule section/gitlink.

## Ignore policy

During installation CodeSleuth adds a marked root `.gitignore` block for local-only data:

```text
.codesleuth/
.opencode/state/
.opencode/cache/
.opencode/logs/
.opencode/sessions/
.opencode/snapshots/
.opencode/node_modules/
```

The dependency path `tools/codesleuth` is never added to that block. If an existing project rule ignores the proposed submodule path, binding fails closed rather than silently rewriting project ignore policy.

## Dependency binding

Binding uses normal Git submodule semantics:

```text
.gitmodules               -> where CodeSleuth is obtained
tools/codesleuth gitlink  -> exact CodeSleuth commit expected by this project
```

CodeSleuth stages those Git changes but does not create a target-project commit or push it.

Detached dependency checkouts are expected. Exact commit identity is authoritative; CodeSleuth does not infer a floating branch from `origin/HEAD`.

## Removal

`git submodule deinit` removes only a local checkout. A project-level dependency removal uses Git's tracked submodule removal (`git rm <submodule-path>`), which removes the superproject gitlink and the corresponding `.gitmodules` section. CodeSleuth refuses to discard a dirty CodeSleuth worktree.

Git may keep the nested object database under the superproject's `.git/modules`; this is normal Git behavior and permits historical checkouts without re-fetching.

## Sensitive evidence

Preserved review state can contain credentials, API responses, source excerpts, or test diagnostics. The archive is gitignored by default. Users who intentionally version or publish audit reports are responsible for reviewing/sanitizing them first.

CodeSleuth does not guess at user-authored report locations outside its managed state. Such project files are never automatically deleted by uninstall.
