# Particles conformance artifacts

This directory holds the **behavioural / quantitative** conformance surface of
the Particles standard — the ground truth a second implementation must match to
reproduce our numbers and decisions, complementing the **structural** artifacts
under `artifacts/schemas/` (JSON Schema, JSON-LD `@context`, SHACL shapes).

| File | Role | Governing ADR |
|---|---|---|
| `profile.yaml` | The **Conformance Profile** companion: constants, formulas, decay table, float tolerance, embedding profile, and deterministic test vectors. The single machine-readable source of truth for `docs/spec/conformance-profile.md`. | Profile |
| `similarity_vectors.json` | The frozen **embedding-similarity** test-vector set (band + top-k membership cases) — the portability instrument for the similarity substrate. | Profile |

The reference SDK self-certifies against both with `particles conformance check`
(L2 over `profile.yaml`'s vectors; L3 over `similarity_vectors.json`).

---

## `profile.yaml` — the Conformance Profile companion

Mirrors `docs/spec/conformance-profile.md`:

- **Constants** (§2) mostly carry a `config_path` — the dotted attribute on the
  SDK's `get_config()` they restate. A drift-guard test
  (`tests/test_conformance_profile.py`) asserts every published `value` still
  equals the live default at that path, so the artifact never silently lags
  `particles/config.py`. A few are **code-level** (`config_path: null`) — module
  constants rather than config knobs, notably the §2.6 / §13.3 benchmark
  match-semantics constants; those are drift-checked against the live
  code default directly rather than via `config_path`.
- **Formulas** (§4) — `effective_confidence`, `recency_factor`, the calibration
  apply transform, and the §6.9 noisy-OR co-evidential merge.
- **`embedding_profile`** — the reference `{model, dim, normalization}`, and a
  `similarity_vectors_ref` pointer to the file below.
- **`test_vectors`** — the canonical input → expected cases the L2 runner
  recomputes, covering both the §4 formulas and the §5 deterministic algorithms.

`profile_version` carries the artifact's own stamp; bump it when a default is
re-tuned. The loader/validator is `particles/conformance/profile.py`; the runner
is `particles/conformance/runner.py`.

### The `test_vectors` block

Seven families, in two kinds. The **numeric** families are the §4 formulas and
conform within `float_tolerance` (`1e-9` absolute); the **categorical** families
are the §5 algorithms, whose outputs are a verdict, a digest, a boolean and a
count — those must match *exactly*, since there is nothing to round.

| Family | Pins | Comparison |
|---|---|---|
| `effective_confidence` | §4 read-time product, incl. the `> 1.0` clamp | `float_tolerance` |
| `recency_factor` | §2.3 decay, incl. the floor and the `age ≤ 0` case | `float_tolerance` |
| `calibration_apply` | §4 `clamp(raw/T, 0, 1)`, incl. `T < 1` saturation | `float_tolerance` |
| `noisy_or_merge` | §6.9 co-evidential merge with the `1/k` within-source discount | `float_tolerance` |
| `conflict_ladder` | §6.4 **rung ordering** | exact |
| `context_fingerprint` | §16.1 procedure | exact |
| `cascade_gate` / `cascade_cap` | §15.1 policy gate (N ≥ 3) and per-run cap | exact |

**Every vector input is plain data** — scalars, strings, and flat records, never
a serialized SDK object. That is the portability contract: the ladder and
fingerprint families take *structured* inputs, so each one publishes only the
fields the algorithm actually reads, and a second implementation materialises
its own types from them.

- `conflict_ladder` carries two particle stubs of exactly two fields —
  `assertion_modality` (the §1.7 truth-apt gate; truth-apt iff `FALSIFIABLE`)
  and `uncertainty_nature` (the §1 `ALEATORY` exclusion) — plus the
  caller-resolved inputs (the replacement signal, the two supersession
  directions, both trust scores, the differential threshold, and whether the
  store has a single trust order). Omitted keys take the documented defaults.
  Because the family is about *ordering*, the vectors deliberately set up rungs
  to compete: an `ALEATORY` pair with both a supersession edge and a decisive
  trust gap must still come out `INCONSISTENT`.
- `context_fingerprint` carries `(id, status)` rows rather than a bare id list,
  so all three steps are pinned: the ACTIVE-only filter (step 1), the
  lexicographic sort (step 2 — one vector supplies its ids out of order), and
  the delimiter-free SHA-256 (step 3). The ids are fixed literals; the expected
  digest is a function of those exact strings, so they must be ported verbatim.

Boundary vectors state inclusive comparisons (`N ≥ 3`, `|Δ| ≥ threshold`, a
batch exactly at the cap). Where such a boundary would otherwise hinge on
decimal-to-binary rounding, the vector overrides the input to exactly
representable values and says so in a comment — the case is about the
comparison operator, not about float representation.

---

## `similarity_vectors.json` — embedding-similarity vectors

The frozen test-vector set that is the portability instrument for the standard's
similarity substrate. It is the concrete, language-agnostic answer to "does a
second implementation reproduce our similarity behaviour?" — the question
this Profile makes answerable.

### What is pinned

Per the technical specification (§8.5, *Embedding & Similarity Contract*):

- **Similarity** is **cosine over L2-normalized embedding vectors, clamped to
  `[0, 1]`** (negatives → 0). Every similarity threshold in the standard is
  expressed on this normalized scale.
- An implementation records a structured **`embedding_profile = {model, dim,
  normalization}`** in store metadata. A profile change requires re-embedding.
- The **reference profile** is
  `{model: all-MiniLM-L6-v2, dim: 384, normalization: l2}` — declared in the
  `profile` block of `similarity_vectors.json`.

### File format

```jsonc
{
  "profile":  { "model": "...", "dim": 384, "normalization": "l2" },
  "pairs": [
    { "id": "equiv-01", "category": "clear-equivalent",
      "text_a": "...", "text_b": "...", "band": [lo, hi] }
  ],
  "topk": [
    { "id": "topk-01", "query": "...",
      "corpus": [ { "id": "c1", "text": "..." }, ... ],
      "k": 2, "expected_topk": ["c1", "c3"] }
  ]
}
```

### Bands are the conformance semantics

Each `pairs` entry declares a closed band `[lo, hi]`. A backend is
**profile-conformant** on that vector when, embedding `text_a` and `text_b`
under the declared profile and applying the pinned metric, the resulting
similarity lands in `[lo, hi]` **inclusive**.

Bands — **not** an `|Δ| ≤ ε` tolerance against a recorded float — are the
contract (resolved open question 2). They are chosen to *comfortably
bracket* the reference model's score with margin on both sides, so the band is a
real cross-implementation contract rather than an overfit to one backend's
floating-point output. A different conformant encoder may legitimately score
anywhere inside the band.

The `category` field is descriptive only (it documents what each pair probes:
`clear-equivalent`, `clear-unrelated`, `near-threshold`, `cross-domain`); the
band is what is asserted.

### Top-k cases are membership, not ordering

Each `topk` entry asserts that, ranking `corpus` by similarity to `query`, the
top `k` results **contain** every id in `expected_topk` (set membership, ⊇).
This is the deliberately weaker guarantee that layer 4 establishes: exact
top-k *ordering* across profiles is implementation-defined and **non-normative**.
The cases pin the strong, reproducible part (the clearly-relevant documents make
the cut) without over-claiming a total order.

### Running the vectors as a conformance check

The reference SDK exercises this file in
`tests/test_conformance_similarity_vectors.py` (marked
`@pytest.mark.integration`, since it needs the real embedding model) and via the
L3 path of `particles conformance check`. Both load the JSON, encode every pair
with the reference encoder, and assert each score falls in its band and each
top-k membership holds. A second implementation runs the equivalent check in its
own language against this same frozen file.

---

## Maintenance

Both files are **frozen** contracts. Changing a band, a constant, a formula, or
the reference profile alters the conformance contract — it rides an ADR or an
explicit spec revision, never a silent edit. When a config default is re-tuned,
update `profile.yaml`'s matching constant in the same change (the drift-guard
test enforces this). When the *reference embedding profile* changes, re-author
the `similarity_vectors.json` bands against the new model and update its
`profile` block in the same change.
