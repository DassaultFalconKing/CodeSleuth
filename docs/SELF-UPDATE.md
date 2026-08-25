# CodeSleuth self-update and restart

CodeSleuth supports a bounded self-update lifecycle for floating installations and for the CodeSleuth source checkout itself. This is lifecycle management only: it does not restart the operating system and it does not take ownership of an OpenCode model/session.

## Operator flow

A floating installed CodeSleuth instance can check without changing files:

```bash
.opencode/bin/review-pack-update --check
```

If an update is available, apply it and leave the current CLI process alone:

```bash
.opencode/bin/review-pack-update
```

To apply the update, run Verify, and replace the current CLI process with the updated CodeSleuth TUI after verification succeeds:

```bash
.opencode/bin/review-pack-update --restart
```

`--check` and `--restart` are intentionally mutually exclusive. A check never mutates the installation or restarts anything.

## TUI behavior

On the **Tools** surface:

1. **Check Updates** resolves the recorded floating source and reports whether a newer source commit exists.
2. **Update** fetches the selected source, applies the existing conflict-safe installer/update path, and runs the updated `review-pack-smoke.py` Verify gate.
3. Only after Verify succeeds, the updater atomically writes a local restart request under `.opencode/state/`.
4. The CodeSleuth bootstrap notices the new request, exits the current Textual application cleanly, and re-executes the updated bootstrap with the same target arguments.
5. The updated CodeSleuth instance starts against the same repository.

The restart request is local runtime state and is already covered by the `.opencode/state/` ignore policy. The bootstrap snapshots the marker that existed when it started, so an old request cannot cause a restart loop.

If Verify fails after the installer has applied files, CodeSleuth reports the failure and does **not** request an automatic restart. The updated files remain available for diagnosis or rollback instead of silently launching a runtime that failed its own integrity gate.

### First adoption from an older CodeSleuth

A CodeSleuth process started from a version that predates this restart supervisor cannot retroactively gain the watcher while it is already running. Therefore the first update **into** a version containing this feature requires one ordinary manual CodeSleuth restart after the update completes. Once the new bootstrap is running, later TUI updates perform the verified restart automatically.

This is a one-time compatibility boundary, not a persistent update mode.

## Source-checkout mode

When CodeSleuth is running against its own source checkout, the existing source-update contract remains authoritative:

- fetch `origin/main` explicitly;
- do not trust stale local branch-tracking metadata;
- require local branch `main`;
- refuse tracked local changes;
- update only by fast-forward to the fetched `origin/main`.

The bootstrap records the running distribution checkout's `HEAD`. After that guarded fast-forward changes the source `HEAD`, the current CodeSleuth control shell exits and re-executes the bootstrap from the updated checkout.

## Pinned projects

A project that binds CodeSleuth as the exact `tools/codesleuth` Git dependency remains deliberately pinned. TUI target-local Check Updates/Update stay disabled in that mode. Advance or revert the gitlink explicitly, materialize the accepted checkout, then run that checkout's installer/update path.

Automatic floating self-update must never silently move an exact project dependency.

## Ownership boundary

A CodeSleuth restart means only the CodeSleuth lifecycle/TUI process is reloaded. It does not:

- reboot Windows, Linux, macOS, WSL, or the host machine;
- restart an active OpenCode review session;
- create a second model/controller runtime;
- change the rule that OpenCode owns model execution, agents, tools, commands, Skills, and review orchestration.

This feature is `CORE-HARDENING`: it closes the update lifecycle already owned by CodeSleuth rather than adding a new analysis or execution subsystem.
