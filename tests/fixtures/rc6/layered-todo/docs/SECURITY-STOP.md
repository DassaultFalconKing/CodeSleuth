# Security containment stop-gate

Objective: close authorization containment before capacity work.
Allowed paths: `src/security/**` and `tests/security/**`.
Adjacent parallel track: `src/capacity/**`.
Required repository gate: `./verify.sh security`.
Live-only acceptance: Temporal poller smoke on a production-like host.
