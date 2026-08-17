# Particles Conformance Profile

| Field | Value |
|---|---|
| Document Type | Conformance Profile (behavioural / quantitative ground truth) |
| Version | 1.1 |
| Status | **Normative** (active 1.61.0) |
| Companion artifact | `artifacts/conformance/profile.yaml` |
| Self-certification | `particles conformance check` (runner) |

> **Status.** This document realizes the decision (active as of
> 1.61.0) and is **normative**. Every owner decision it depended on is resolved
> (see §8) and the companion artifact is shipped. The technical specification
> cites it as the behavioural / quantitative ground truth, the way it cites the
> schema/SHACL/`@context` artifacts for structure. Where this document and the
> companion `profile.yaml` disagree, the artifact takes precedence for
> implementation; where the spec prose and the resolved canonical value
> historically disagreed, the canonical value stated here governs.

The Particles standard pins **structure** through `particle.schema.json`, the
SHACL shapes, and the JSON-LD `@context`. This Profile pins **behaviour and
quantities**: the constants, formulas, decay tables, and similarity rules an
implementation must match. It is the single source of truth the technical
specification cites for behaviour, and it carries its own version stamp.

Operational parameters that do **not** affect epistemic outputs (network
timeouts, byte caps, rate limits, batch sizes, progress-bar toggles) are
explicitly **out of scope** — they may differ freely across implementations.

---

## 1. Conformance levels

An implementation **declares the highest level it targets**. Each level is a
superset of the ones below and is independently testable.

- **L1 — Structural.** Schema validity, the §6.6 status machine, JSON-LD
  serialization round-trip, and relation-graph canonicalization. Covered by the
  existing schema/SHACL/context artifacts. *Reproducible exactly.*
- **L2 — Deterministic-compute.** Every numeric/algorithmic output that is a
  pure function of stored inputs: `effective_confidence`, the noisy-OR
  confidence merge, the recency factor, calibration scaling, the
  conflict-resolution **ladder ordering**, the §16.1 fingerprint, and cascade
  gating. Given identical inputs, outputs MUST match within the float tolerance
  in §4. *Reproducible exactly, given inputs.*
- **L3 — Profile-similarity.** Similarity-driven behaviour — retrieval,
  co-evidential grouping, contradiction candidacy, subject-link scoring —
  **within a declared `embedding_profile`** that passes the §3 similarity test
  vectors. Cross-profile top-k *ordering* is implementation-defined and MUST be
  disclosed. *Reproducible within a profile; bounded by test vectors.*
- **L4 — Full.** End-to-end behaviour including LLM-driven judgments (extraction
  granularity, semantic-contradiction verdicts, NL synthesis). Conformance is on
  the **structured envelope and disclosure** (§6), never the prose. *Not
  bit-exact.*

A conformance claim names the level and the profile, e.g. *"L3-conformant under
`embedding_profile = minilm-l6-v2-384`."*

---

## 2. Normative constants & thresholds

The conformance-relevant constants, grouped by the decision each one drives.
**Value** is the reference SDK's current default; **Level** is the lowest
conformance level that observes it; **Spec** points to the governing section.

### 2.1 Confidence & calibration

| Constant | Value | Scale | Level | Spec | Notes |
|---|---|---|---|---|---|
| `max_asserted_confidence` | `0.90` | [0,1] | L2 | §9.1a | Cap on an agent-asserted particle's confidence. |
| calibration temperature bound | `[0.01, 10.0]` | T | L2 | §14.3 | Bounded NLL optimiser interval (`calibration.py`); confirmed. |
| `calibration_source` enum | `EXTRACTOR_DIRECT` / `CALIBRATED_BENCHMARK` / `HUMAN_REVIEW` | enum | L1 | §6.3 | Trust ordering low→high. |

### 2.2 Trust, demotion & cascade

| Constant | Value | Scale | Level | Spec | Notes |
|---|---|---|---|---|---|
| trust differential threshold | `0.15` | [0,1] | L2 | §6.4 rung 2 | **Resolved:** `0.15` canonical (`config.py`). The §6.4 / §9.4 prose was corrected from the stale "0.2" alongside the activation. |
| `cascade_max_per_run` | `500` | count | L2 | §15.1 | Extension B safety cap. |
| `cascade_min_reviewer_confirmations` | `3` | count | L2 | §15.1 | N≥3 to auto-cascade. |
| `reviewer_trust_rank` | `0.8` | [0,1] | L2 | §9.6 | Default reviewer trust. |
| `agent_trust_rank` | `0.8` | [0,1] | L2 | §9.1a | Default agent-assertion trust. |
| conformance trust-weight cap | `0.5` | [0,1] | L2 | Profile | Cap on a REQUIRED-failing extractor's trust weight. |
| authority status → confidence | `preferred 0.99` / `normal 0.85` / `deprecated 0.30` | [0,1] | L2 | §6.7 | Subject-authority link confidence by status. |

### 2.3 Recency decay

`recency_factor = max(floor, 0.5 ^ (age_days / half_life_days))`, per
`source_type`. **Resolved** from `config.py:597-601` (authoritative):

| source_type | half_life_days | floor | Level | Notes |
|---|---|---|---|---|
| `REDDIT_POST` | `60` | `0.10` | L2 | Floor is the `SourceDecayConfig` field default — stated explicitly here so it can't drift. |
| `GITHUB_REPO` | `365` | `0.40` | L2 | |
| `GITHUB_GIST` | `180` | `0.20` | L2 | |
| `GITHUB_PAGES` | `365` | `0.25` | L2 | |
| *(any other `source_type`)* | — | — | L2 | **No decay → `recency_factor = 1.0`.** The common case (WEB_PAGE, PDFs, papers, local files). |

`age_days = (now_utc − content_published_at_utc) / 86400`, **fractional**;
reference is `content_published_at` (not capture time); `None` or future-dated →
`1.0` (`core/decay.py:43-55`). **Scope:** this is the store-local
*base* — adopted trust lenses may overlay per-`source_type` / per-URL
`decay_rules`; the table above is the default policy with no decay-bearing lens
adopted.

### 2.4 Similarity thresholds (L3 — profile-relative)

These gate similarity-driven decisions and are meaningful only **on the §3
normalized cosine scale, within a declared profile**.

| Constant | Value | Purpose | Spec |
|---|---|---|---|
| `extraction.similarity_threshold` | `0.80` | Extract-time conflict candidacy | §9.2 step 7 |
| `query.equivalence_threshold` (θ) | `0.0` | Co-evidential grouping; `0.0` reproduces prior binary behaviour | §6.10 |
| `lint.contradiction_candidate_threshold` | `0.6` | `L-SEM-01` contradiction candidacy | §9.4 |
| `find_duplicates_similarity_threshold` | `0.88` | Near-duplicate detection | §9.4 |
| `wikidata_link_suppress_threshold` | `0.25` | Subject-link suppression (abstain below) | §6.7 |
| `external_link_abstain_threshold` | `0.15` | External-authority abstain cutoff | §6.7 |
| curation `candidate_threshold` | `0.92` | `links_suggest` co-evidential candidates | Profile |

### 2.5 Query ranking & lint (deterministic given retrieval)

| Constant | Value | Purpose | Level | Notes |
|---|---|---|---|---|
| `default_top_k` | `40` | Retrieval slice | L3 | Ordering non-normative across profiles. (Code default `40`; `config.yaml.sample` said `10` — sample corrected.) |
| `default_min_confidence` | `0.0` | Floor filter | L2 | |
| `similarity_weight` / `confidence_weight` | `0.6` / `0.4` | Rank blend | L3 | **Resolved:** ranking is the **weighted sum** `similarity_weight·cos + confidence_weight·eff_conf` (`operations/query/main.py`). The §9.3 prose was corrected from the erroneous "×" alongside the activation. |
| `lint.recency_decay_threshold` | `0.5` | Staleness flag on recency factor | L2 | |
| `lint.variance_threshold` | `0.15` | Confidence-decay lint flag | L2 | variance growth on a stale particle. |
| `contestedness.callout_threshold` | `0.2` | Contested-claim callout surfacing | L2 | max−min effective-confidence spread across the policy set. Draft labelled this `review.callout_threshold`; the canonical config path is `contestedness.callout_threshold`. |
| synthesis `layer_b_unrelated_tolerance` | `0.30` | Citation-validation Layer B | L4 | LLM-judge dependent. |

### 2.6 Benchmark match semantics — §13.3

These pin the claim-equivalence assignment and the ECE binning the §13.3
benchmark runner uses, so two conformant runners' precision / recall /
`calibration_error` are comparable numbers rather than artefacts of differing
match rules. They are **code-level constants** — module-level defaults in
`particles/benchmark/`, not config knobs — so they carry no `config_path`; the
drift guard checks them against the live benchmark defaults directly
(`tests/test_conformance_profile.py::test_benchmark_match_constants_match_live_code`).

| Constant | Value | Purpose | Level | Notes |
|---|---|---|---|---|
| `benchmark_equivalence_threshold` | `0.80` | Embedding judge: an emitted/expected pair matches when cosine ≥ this, assigned greedily one-to-one in similarity-descending order | L3 | On the §3 normalized cosine scale. |
| `benchmark_llm_prefilter` | `0.65` | LLM-judge mode: only pairs scoring ≥ this cosine are sent to the LLM judge (a wider net; the pre-filter bounds LLM cost) | L3 | On the §3 normalized cosine scale. |
| `benchmark_ece_bins` | `10` | Expected Calibration Error: number of equal-width confidence bins | L2 | Guo et al. 2017 convention; two runners MUST use the same binning. |

---

## 3. Embedding & similarity contract (L3)

Governed by the similarity-portability contract. Summary of the contract this Profile must carry:

- **Metric & scale.** Similarity is **cosine over L2-normalized embedding
  vectors**, clamped to `[0, 1]` (negatives → 0). All §2.4 thresholds are on
  this scale.
- **`embedding_profile`.** An implementation records `{model, dimensionality,
  pooling/normalization}` in store metadata; a profile change requires
  re-embedding. **Reference profile (ratified):** `all-MiniLM-L6-v2` @ 384-dim,
  L2 normalization.
- **Similarity test vectors.** A frozen set of `(text_a, text_b) → expected
  similarity band` and `(query, corpus) → expected top-k membership` cases. A
  backend is profile-conformant if it reproduces the **bands** (ratified
  tolerance methodology — bands, not `|Δ|≤ε`) and the top-k membership. The
  corpus is a small purpose-built set (~20–40 pairs + top-k cases).

The concrete vector file is shipped at
`artifacts/conformance/similarity_vectors.json`
(28 pairs + 4 top-k cases), with band semantics documented in
`artifacts/conformance/README.md`. The L3 check in `particles conformance check`
runs every vector against the live profile; the unit-tier regression guard is
`tests/test_conformance_similarity_vectors.py`. `profile.yaml` points at this
file by name (`similarity_vectors_ref`).

---

## 4. Confidence & calibration math (L2)

All formulas below are pure functions of stored inputs and MUST reproduce
exactly. **Float tolerance (resolved — §8 decision #6):** two L2 outputs are
conformant-equal iff `|a − b| ≤ 1e-9` — an **absolute** tolerance on the `[0, 1]`
scale. It is loose enough to absorb cross-language `pow` / `exp` rounding, tight
enough that a genuine formula divergence fails. The companion artifact carries
the same value as `float_tolerance`, and `particles conformance check` applies
it when comparing each computed result against its published vector.

**Effective confidence** (read-time, never stored):

```
effective_confidence = confidence.value
                     × extractor_trust_weight
                     × source_trust_rank
                     × recency_factor
```

**Recency factor** (§6.3):

```
recency_factor = max(floor, 0.5 ^ (age_days / half_life_days))
age_days       = (now_utc − content_published_at_utc) / 86400   # fractional days; None/future → factor 1.0
```

**Stored confidence (calibration at creation, immutable — §6.3 / §14.3):**

```
confidence.value = sigmoid(logit(raw) / T),   T ∈ [0.01, 10.0]
```
**Resolved:** the apply transform is **logit-space temperature scaling** — Guo
et al. (2017) as written — and `T` is fit by **NLL** minimization (not ECE) over
`[0.01, 10.0]` via `scipy.minimize_scalar(method="bounded")`. `T = 1` is the
identity; `T > 1` pulls every value toward `0.5`; `T < 1` pushes toward the ends;
`0.0` and `1.0` are exact fixed points. The stored enum
`calibration_method="temperature_scaling"` is unchanged and now literally
accurate.

**Amended.** This section previously resolved the transform as
`clamp(raw/T, 0, 1)` — *bounded reciprocal-temperature scaling of a `[0,1]`
scalar* — on the reasoning that extractors expose a confidence rather than
logits. That reasoning was wrong: a confidence *is* a probability, and `logit`
of a probability is defined. The approximation carried two defects the logit
form does not — a `T<1` saturation that collapsed every value above `T` onto
`1.0` (destroying order among them), and unbounded degradation at high `T`
(at the bound, every confidence divided by ten). A stored calibration now
declares its own transform; one that does not predates this decision and is not
applied.

**Co-evidential merge (noisy-OR, §6.9 — transcribed verbatim):** for a
co-evidential group `G` (the same claim asserted from independent extractors or
across co-evidential-linked sources), the merged confidence is **not** a max or
average but a trust-weighted noisy-OR:

```
merged(G) = 1 − ∏_{p ∈ G} (1 − effective_confidence(p) × source_independence(p))
```

- `effective_confidence(p)` is the per-particle product above (already clamped
  to `[0, 1]`).
- `source_independence(p)` is `1.0` for the **first** particle from a given
  source and `1/k` for the `k`-th particle from that same source within the
  group — the throttle that stops one chatty source from saturating the merge.
- **Within-source ranking is by descending `effective_confidence`** (the
  strongest claim from a source carries full weight; weaker repeats absorb the
  `1/k` discount). This makes the result independent of input order. An empty
  group merges to `0.0`; a singleton passes its value through unchanged.

This is the reference SDK's `merge_co_evidential_confidence`
(`particles/core/confidence.py`). The `source_key` that groups particles is
typically the first SOURCE provenance ref's `corpus_entry_id`, but may be a
domain or author for finer throttling — the merge math is identical.

**Worked example.** A group of three particles — two from source `A`, one from
source `B`:

| particle | source | effective_confidence | within-source rank `k` | `source_independence` | `1 − ec·si` |
|---|---|---|---|---|---|
| p1 | A | 0.70 | 1 | 1.0 | `1 − 0.70 = 0.30` |
| p2 | A | 0.50 | 2 | 0.5 | `1 − 0.25 = 0.75` |
| p3 | B | 0.60 | 1 | 1.0 | `1 − 0.60 = 0.40` |

`merged = 1 − (0.30 × 0.75 × 0.40) = 1 − 0.09 = `**`0.91`**. Note p2 — the
second voice from `A` — contributes `0.50 × 0.5 = 0.25`, not `0.50`: the
discount keeps a single source from counting twice at full strength. The same
three particles from three *distinct* sources would merge higher
(`1 − 0.30·0.50·0.40 = 0.94`); three identical `0.60` voices from *one* source
merge to `0.776`, not `0.936`.

### Worked vectors

These are the canonical L2 vectors **for the formula families above**, mirrored
verbatim in `profile.yaml`'s `test_vectors` block; `particles conformance check
--level L2` recomputes each via the SDK's own functions and asserts
`|computed − expected| ≤ 1e-9`. The §5 deterministic *algorithms* carry their
own vector families in the same block — see §5.1.

| # | Formula | Inputs | Expected |
|---|---|---|---|
| V1 | effective_confidence | value 0.80, ext_tw 1.0, src_rank 0.90, recency 1.0 | `0.72` |
| V2 | effective_confidence | value 0.50, ext_tw 0.8, src_rank 1.0, recency 0.5 | `0.20` |
| V3 | effective_confidence (clamp) | value 0.95, ext_tw 1.5, src_rank 1.0, recency 1.0 | `1.0` (product 1.425 clamped) |
| V4 | recency_factor | age 60d, half_life 60, floor 0.10 | `max(0.10, 0.5^1) = 0.5` |
| V5 | recency_factor (floor) | age 600d, half_life 60, floor 0.10 | `max(0.10, 0.5^10) = 0.1` |
| V6 | recency_factor (age≤0) | age 0d, half_life 60, floor 0.10 | `1.0` |
| V7 | calibration sigmoid(logit(raw)/T) | raw 0.97, T 10.0 | `0.5860378586300931` |
| V8 | calibration (T<1 sharpens, no saturation) | raw 0.80, T 0.5 | `16/17 = 0.9411764705882353` |
| V9 | noisy-OR merge | `[(0.6, A), (0.5, B)]` | `1 − 0.4·0.5 = 0.8` |
| V10 | noisy-OR (one chatty source) | `[(0.6, A), (0.6, A), (0.6, A)]` | `0.776` |
| V11 | noisy-OR (mixed) | `[(0.7, A), (0.5, A), (0.6, B)]` | `0.91` |

The machine-readable companion (§7) carries the authoritative vector set; an
implementation runs `particles conformance check` to self-certify L2 and L3.

---

## 5. Deterministic algorithms (L2)

Specified normatively elsewhere; the Profile pins them as L2 conformance
requirements and points to the governing text:

- **Status transitions** — the §6.6 transition table (exhaustive, normative).
- **Relation canonicalization** — symmetric kinds → `(min(a,b), max(a,b))` on
  write; asymmetric kinds preserve direction (§6.10).
- **Fingerprint** — the §16.1 Merkle/SHA-256 procedure ("MUST be followed
  exactly").
- **Conflict-resolution ladder ordering** — the §6.4 rungs in order:
  `1 ALEATORY → 1.5 document-supersession → 1.7 truth-apt gate → 2 trust
  differential → 3 INCONSISTENCY`. The **ordering** is L2-normative; the
  similarity *candidacy* that feeds it is L3.
- **Cascade gating** — N≥3 confirmations, `cascade_max_per_run` cap (§15).

### 5.1 Machine-checkable vectors for the algorithms

Three of the five above — the ladder ordering, the fingerprint, and cascade
gating — carry runnable `test_vectors` families in the companion artifact
alongside the §4 formula families, and `particles conformance check --level L2`
recomputes them with the rest. (Status transitions and relation
canonicalization remain pinned by prose + the L1 structural artifacts.)

The §4 families are numeric and conform within `float_tolerance`. These three
are **categorical** — a verdict, a hex digest, a boolean and a count — and MUST
match **exactly**; there is nothing to round.

| Family | Pins | Governing text |
|---|---|---|
| `conflict_ladder` | Which rung fires for a given pair, including the cases where an upper rung must beat a lower one that would decide differently | §6.4 |
| `context_fingerprint` | The ACTIVE-only filter, the lexicographic sort, and the delimiter-free SHA-256 | §16.1 |
| `cascade_gate`, `cascade_cap` | The policy gate (`OPERATOR_DIRECT` / `REGISTRY_ENDORSED` always; `REVIEWER_DERIVED` at N ≥ `cascade_min_reviewer_confirmations`) and the `cascade_max_per_run` truncation | §15.1 |

**Structured inputs stay plain data.** Unlike the §4 vectors, which take
scalars, these take structured inputs — but each vector publishes **only the
fields its algorithm actually reads**, as flat records, never a serialized
particle. A `conflict_ladder` vector's two particle stubs carry
`assertion_modality` and `uncertainty_nature` and nothing else; a
`context_fingerprint` vector carries `(id, status)` rows. This is what keeps
the set portable: a second implementation materialises its own types from those
fields rather than reproducing this SDK's object graph. An implementation that
adds fields to its particle type does not invalidate the vectors.

Because the ladder family is about **ordering** rather than any single rung's
logic, its vectors deliberately put rungs in competition — a vector sets up a
lower rung to decide one way and asserts that the higher rung overrides it. An
`ALEATORY` pair carrying both a document-supersession edge and a decisive trust
differential must still resolve to `INCONSISTENT`; that vector is what a
reordering of the ladder would break.

---

## 6. LLM-judgment boundary (L4 — non-deterministic)

The following are **LLM-driven and therefore not bit-reproducible**. The
standard's conformance contract around each is on the *deterministic envelope*,
not the model output:

| Behaviour | Non-deterministic part | Deterministic contract (what IS conformance) |
|---|---|---|
| Extraction | Claim segmentation, confidence self-assessment, subject names | Output schema validity (L1); calibration applied deterministically (L2); candidate-subject resolution scoring (L3) |
| Semantic lint (`L-SEM-*`) | The contradiction / equivalence *verdict* | Candidate *generation* is deterministic (similarity gate, §2.4) — conformance is on candidates, not verdicts |
| Synthesis (wiki/query NL) | The prose | Citation-validation Layers A/B must run; cited IDs MUST be members (L1/L4) |

An L4 implementation MUST **disclose** which outputs are LLM-driven.

---

## 7. Machine-readable companion & conformance runner

The companion artifact `artifacts/conformance/profile.yaml`
mirrors §2 (constants, each tagged with the `config_path` it restates), §3 (the
embedding profile + a `similarity_vectors_ref` pointer to the vector
file), §4 (formulas + the canonical `test_vectors`), and §5.1 (the algorithm
vector families). It carries its own `profile_version` (`1.1`), decoupled from
this document's and the spec's cadence — bump it when a default is re-tuned or
the vector set grows.

**Single source of truth, kept in sync.** premise is that the Profile
*restates* the config-derived constants as the published ground truth. The
reference SDK keeps the artifact and `particles/config.py` from drifting via a
drift-guard test (`tests/test_conformance_profile.py`): for every constant it
resolves the declared `config_path` off the live `get_config()` and asserts the
published `value` still matches. Re-tuning a default without updating the Profile
(or vice versa) fails the test — so the artifact never silently lags the code.
`config.py` remains the runtime source; the Profile is the published mirror the
test pins to it.

**Self-certification — `particles conformance check` (this milestone).** The
runner (`particles/conformance/runner.py`) loads `profile.yaml` and reports a
per-level verdict:

- **L2** recomputes every `test_vectors` entry via the SDK's own functions —
  `core.scoring.confidence.compute_effective_confidence` /
  `merge_co_evidential_confidence`, `core.scoring.decay.recency_factor_from_params`,
  `extraction.calibration.TemperatureScaler` for the §4 formulas (asserting
  `|computed − expected| ≤ float_tolerance`), and
  `core.conflict_resolution.resolve_conflict`,
  `core.fingerprint.context_fingerprint`, `core.cascade_gate` for the §5.1
  algorithms (asserting exact equality). Pure; runs anywhere.
- **L3** embeds the `similarity_vectors.json` pairs under the live embedding
  profile and checks band membership + top-k membership. **SKIPPED** (not failed)
  when the embedding model is unavailable, since L3 is a claim about the encoder
  backend.
- **L1** is delegated to the existing schema/SHACL/`@context` validators
  (`conformance/jsonschema.py`, `conformance/shacl.py`); the runner names it
  rather than re-deriving structural validity.

`particles conformance check --level {L2,L3,all}` exits non-zero on any FAIL and
takes `--json` for machine consumption; `particles conformance show` prints the
loaded constants and formulas. The runner is the reference SDK's
self-certification harness and the template a second implementation ports: the
artifact's formulas + vectors are language-agnostic, so an independent engine
runs the identical checks against its own functions to make the same L1–L4
claim.

---

## 8. Decisions

**Resolved (2026-06-25, owner-ratified after codebase investigation):**

1. **Trust differential** — **`0.15`** canonical (`config.py`). The
   §6.4 / §9.4 "0.2" prose was corrected in the truth-sync. (§2.2)
2. **Query ranking** — **weighted sum** `similarity_weight·cos +
   confidence_weight·eff_conf` (`operations/query/main.py`). The
   §9.3 "×" prose was corrected in the truth-sync. (§2.5)
3. **Recency decay** — frozen per §2.3 (four configured types; unlisted →
   `1.0`); `age_days` fractional UTC from `content_published_at`. (§2.3)
4. **Calibration** — `sigmoid(logit(raw)/T)`, `T` fit by NLL over `[0.01,10.0]`;
   logit-space which amended this section's original resolution of
   "bounded reciprocal-temperature scalar scaling"; enum string retained. (§4)
5. **Embedding reference / tolerance / corpus** —: reference
   `all-MiniLM-L6-v2 @ 384 / l2`; **band** tolerance; small purpose-built corpus
   in `artifacts/conformance/`. (§3)

Decisions 1–4 also imply small `technical-specification.md` prose corrections
(the `0.15` differential, the weighted-sum ranking, and the `default_top_k`
sample fix) — a docs truth-sync applied alongside the activation; this
document's activation additionally wires the spec to **cite** the Profile as the
behavioural ground truth (techspec §6.3 / §6.4 / §8.5 / §13.2, the way it
already cites the schema/SHACL artifacts for structure).

**Resolved at activation (2026-06-25, owner-ratified in session):**

6. **Float tolerance** for L2 equality — **`1e-9` absolute** on the `[0, 1]`
   scale (`|a − b| ≤ 1e-9`). Absorbs cross-language `pow`/`exp` rounding without
   admitting a real formula divergence. Carried as `float_tolerance` in
   `profile.yaml`. (§4)
7. **Companion artifact & runner** — the artifact ships at
   `artifacts/conformance/profile.yaml` (sibling of the `similarity_vectors.json`), shape per §7, parsed by
   `particles/conformance/profile.py`. A conformance-test **runner ships this
   milestone**: `particles conformance check` (L2 deterministic + L3 similarity;
   L1 delegated), backed by `particles/conformance/runner.py`, plus the
   config-sync drift guard. The remaining scope was deferred (
   `## Deferred`). (§7)

**Resolved since (2026-08-02):**

8. **Algorithm vector coverage** — the §5 deterministic algorithms named
   L2-normative but not previously machine-checkable now carry `test_vectors`
   families: the §6.4 conflict-ladder ordering, the §16.1 fingerprint, and
   §15.1 cascade gating. The vector schema grew to admit **structured** inputs
   while staying language-agnostic — each vector publishes only the fields its
   algorithm reads, as flat plain-data records (§5.1). Categorical outputs
   compare exactly rather than within `float_tolerance`. `profile_version` →
   `1.1`. The one still-open item from decision #7 is the formal
   *external*-submission protocol. (§5.1)
