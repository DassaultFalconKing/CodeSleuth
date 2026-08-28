# Graphify representative-corpus comparison

The M3 harness evaluates the isolated structural adapter over deterministic Python,
TypeScript, Rust, mixed-language, over-limit and odd-encoding fixtures, plus a bounded
selection from CodeSleuth itself. Separate contract tests cover dirty tracked files,
rename/delete drift, Windows-style paths, staged symlink/gitlink modes and hostile
provider labels.

Install the optional exact runtime described in `GRAPHIFY-PROVIDER.md`, then run:

```text
python -m pytest -q tests/test_graphify_corpus.py
python scripts/graphify_corpus_compare.py --fixtures tests/fixtures/graphify-corpus --check
```

To retain a machine-readable report, write it only below ignored local state:

```text
python scripts/graphify_corpus_compare.py --fixtures tests/fixtures/graphify-corpus --check --output .runtime/graphify-corpus/report.json
```

The harness reports wall time, Python `tracemalloc` peak, model-visible JSON bytes,
node/edge counts, truncation, unmapped relations, and ratios of candidates retaining
exact Git/blob promotion. Native parser allocations may not be included in the Python
memory peak. Fixture minima are a useful-structure recall proxy, not general semantic
recall. `modelVisibleBytes` is reported instead of claiming unmeasured model-token
savings.

The report is disposable evaluation evidence, not a context projection, finding,
provider cache or acceptance authority. The harness never writes to tracked source and
rejects a requested output path outside `.runtime/`.
