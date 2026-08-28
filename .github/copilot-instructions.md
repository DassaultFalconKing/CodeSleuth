# CodeSleuth coding-agent provenance

Before the first repository write, read `docs/PROVENANCE-WATERMARK.md` (or `.opencode/PROVENANCE-WATERMARK.md` in an installed CodeSleuth target).

Keep one stable opaque actor code for the logical coding/review session. Use `anon` when attribution is unavailable; do not infer model identity from Git author metadata.

When you control an agent-authored commit message, include the deterministic `Trace-Id: <actor>-<12 hex>` trailer defined by the provenance contract. For CodeSleuth reports or EHA/proof output, bind/load the session watermark through `provenance_state_*` and include the verified watermark in report metadata.

The watermark is attribution metadata only. It is not a cryptographic signature, authorization token, acceptance verdict, or substitute for exact-head evidence and canonical gates.
