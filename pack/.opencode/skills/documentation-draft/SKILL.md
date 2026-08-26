---
name: documentation-draft
description: Draft or update one documentation artifact from a bounded verified evidence packet without re-running repository discovery
slash: true
---

# Documentation draft

## Atomic contract

**Input:** one requested document/output path plus a bounded packet of verified code/config/test evidence and explicit unresolved contradictions.

**Objective:** draft or update that one documentation artifact so claims match the supplied current evidence and canonical authorities.

**Output:** proposed/applied document delta with provenance notes and unresolved items.

**Stop:** evidence is insufficient for a material claim, the requested edit would overwrite a stronger canonical authority without an explicit contract decision, or translation/parity obligations cannot be satisfied.

**Must not:** perform whole-repository discovery, invent architecture, silently resolve code/docs/test contradictions, or duplicate large canonical sections that should be linked.

Use source paths/symbols as provenance. Label inference. Mermaid may present verified relationships but never becomes authority.
