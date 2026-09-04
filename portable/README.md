# Portable CodeSleuth machinery

This directory is the vendorable entry point for project-neutral CodeSleuth primitives.

Start with [`docs/PORTABLE-TOOLS.md`](../docs/PORTABLE-TOOLS.md) for classification, blockers, and the licensing boundary.

## READY now

- `ebca-graph-readside/` — bounded generic graph reader (Rust 1.88 library + JSON CLI)
- provenance watermark algorithm inside that crate (`src/watermark.rs`), requiring an explicit domain separator

## Not in this directory

CodeSleuth adapters, persistence, Git freshness, evidence ledgers, OpenCode tools, and Mermaid/MCP runtimes stay in the main repository. They may call these primitives; they are not themselves portable cores.

## License

CodeSleuth is AGPL-3.0-or-later. Technical portability is not permission to relicense. Do not copy this tree into Aleph_Rugent, Pii_Parcer, or another product without a separate license-compatible decision.
