from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "pack" / ".opencode" / "tools" / "context_graph_read.ts"


def test_native_graph_read_rechecks_exact_projection_payload_snapshot() -> None:
    source = ADAPTER.read_text(encoding="utf-8")

    # projectionId intentionally excludes presentation/evidence-linkage payload
    # such as labels, notes and SourceRef details. A post-native-call check that
    # only compares projectionId + headSha therefore cannot detect every
    # concurrent projection-file mutation.
    assert 'import { createHash } from "node:crypto"' in source
    assert "function projectionPayloadDigest(raw: string): string" in source
    assert 'createHash("sha256").update(raw, "utf8").digest("hex")' in source
    assert "payloadDigest: projectionPayloadDigest(raw)" in source
    assert "expected.payloadDigest" in source
    assert "projectionPayloadDigest(raw) !== expected.payloadDigest" in source
    assert "projection payload changed during native graph read" in source
