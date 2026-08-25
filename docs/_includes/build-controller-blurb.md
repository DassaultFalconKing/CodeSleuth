<!-- Canonical blurb. Public copy: ../README.md#opencode-build-controller. Include as {% include build-controller-blurb.md %} if a Jekyll/docs processor is wired. -->

OpenCode's primary controller is `build`. CodeSleuth does not add a second supervisor. Agent profile (Open-weight / Codex / Claude) selects a model so OpenCode's native provider prompt is used; it does not inject a CodeSleuth system prompt.

```text
CodeSleuth TUI
    ↓
profile / skill / command / model / permissions
    ↓
OpenCode primary build
    ↓
native provider-specific controller prompt
    ↓
Task → explore / general / CodeSleuth skills and subagents
```
