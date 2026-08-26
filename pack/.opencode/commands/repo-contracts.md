---
description: Query or maintain protected capability contracts and forbidden regressions
agent: build
---

Load the `protected-capability-registry` skill and follow it.

Requested contract query / diff / maintenance task:

$ARGUMENTS

Pin the exact repository HEAD before drawing conclusions. Treat `docs/protected-capabilities.json` as the machine-readable contract index and `docs/PROTECTED-CAPABILITY-CONTRACTS.md` as its normative semantics.

For ordinary queries, search the manifest with grep/ripgrep and bounded reads. If the registry is genuinely large and host-native BM25, embedding retrieval, or reranking is already available, use those only to retrieve candidates, then reopen the exact manifest entries and their code/docs/tests evidence before answering.

For a diff or PR, map changed paths to protected contracts, compute the reverse dependency closure, and inspect each matched contract's own `forbidden_regressions` registry. Do not stop at new-feature tests.

For contract maintenance, triangulate current code/config, normative/public documentation, and executable acceptance/regression tests. If they disagree, classify drift instead of inventing a compromise. Do not promote a capability to `protected` without explicit SIB1/SIB2 acceptance evidence.

In read-only review mode, report registry drift rather than editing source. Modify `docs/protected-capabilities.json` only when the requested task authorizes contract maintenance.
