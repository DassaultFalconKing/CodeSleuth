# CodeSleuth integration

CodeSleuth uses Puppeteer indirectly through the exact-pinned
`@mermaid-js/mermaid-cli` runtime under `tools/mermaid-qa`. The purpose is to
prove that generated Mermaid source is parsed and rendered by a real browser,
not merely accepted by a string-level smoke test.

## Runtime contract

The current gate requires:

```text
bun install --cwd tools/mermaid-qa --frozen-lockfile
CODESLEUTH_MERMAID_NODE=<absolute Node executable>
CODESLEUTH_MERMAID_BROWSER=<absolute Chrome/Chromium executable>
bun run test
```

`scripts/mermaid_qa.py` then verifies:

- exact isolated Mermaid CLI version from its own `package.json`;
- absolute, existing, executable Node and browser paths;
- runtime-reported Node and browser versions;
- a bounded Mermaid input size and subprocess timeout;
- strict Mermaid security level;
- disabled external host resolution while allowing localhost;
- real SVG output and its hash;
- absence of sandbox-disabling flags.

The QA subprocess receives a deliberately small environment and writes source,
configuration, and rendered output to a unique temporary directory. The
rendered SVG is hashed for evidence and is not retained by default.

## Hosted Ubuntu binding

The acceptance workflow resolves `/usr/bin/google-chrome` and Node to literal
paths, launches the browser headlessly with a unique temporary profile to prove
the sandbox works, then exports those exact paths to the gate. This separates
browser identity/sandbox preflight from Mermaid rendering.

## Lessons for other agent tools

1. A browser-backed gate must verify the browser actually ran; dependency
   presence alone is insufficient.
2. An explicit executable path is evidence only when it identifies a dedicated
   automation browser. Pointing at a user's everyday browser is unsafe.
3. `--version` is not uniformly side-effect-free across browser distributions
   and Windows launch behavior. Prefer an isolated headless launch plus
   `browser.version()` for general-purpose agent tooling.
4. Missing browser identity is a fail-closed `unavailable` result, not a skip.
5. `No usable sandbox!` is a real hosted compatibility failure. Do not add
   `--no-sandbox`, skip the renderer, or replace browser proof with parsing.
6. Browser/profile cleanup must be scoped to the process and temporary path the
   current run owns.

See also:

- [`../MERMAID-QA.md`](../MERMAID-QA.md)
- [`../EXPORT-SURFACES.md`](../EXPORT-SURFACES.md)
- [acceptance workflow](../../.github/workflows/acceptance.yml)
- [Mermaid QA implementation](../../scripts/mermaid_qa.py)
