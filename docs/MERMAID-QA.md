# Optional Mermaid parser/render QA

CodeSleuth's runtime tools generate bounded Mermaid source. They do not require or
launch a browser. Development and release verification may explicitly install and run
the isolated parser/render QA profile in `tools/mermaid-qa`.

## Install the exact QA runtime

```text
bun install --cwd tools/mermaid-qa --frozen-lockfile
```

This installs `@mermaid-js/mermaid-cli==11.16.0` under the isolated directory only. It
does not modify the main package or make Chromium part of normal CodeSleuth operation.
The lockfile is committed; `node_modules/` remains ignored.

## Run QA

```text
python scripts/mermaid_qa.py diagram.mmd
Get-Content diagram.mmd | python scripts/mermaid_qa.py
bun run test:mermaid-qa
```

The command emits JSON containing the source SHA-256, source size, expected and
resolved runtime version, status, bounded diagnostics and disposable SVG metadata. It
never returns PASS merely because the optional runtime is absent: the status is
`unavailable` and the process exits non-zero. Oversized and empty sources are rejected
before launching Chromium.

Rendering uses Mermaid `securityLevel: strict` and Chromium flags that disable host
resolution/background networking. Input, configuration and SVG are created in a
temporary directory and removed before the command returns; only the SVG digest and
size are reported.

This QA proves that one source parses and renders with the pinned development runtime.
It does not make SVG an authoritative artifact, replace exact repository evidence, or
prove compatibility with every Mermaid host/version.
