# Particles — Technical Specification
**Version:** 2.2
**Document Type:** Technical Specification
**For:** Implementers and Claude Code
**Companion to:** `spec/whitepaper.md`, `roadmap.md`

> Particles v2.2 is the 2026-06 **prose-truth revision** of the v2
> draft: the document was re-verified against the implementation and
> the normative schema artifacts (which take precedence on conflict,
> §6.1) as of reference SDK v0.60.x. Status remains *Draft* until the
> working group reviews the document.
>
> **Spec currency is enforced per ADR from v2.2 onward:** every new
> ADR declares a `spec_impact` classification, and an ADR
> with `spec_impact: standard` must update the normative artifacts in
> its activation commit, with spec prose lagging at most until the
> next release — the v2.0/v2.1 staleness era this revision closes out
> is not expected to recur.

---

**PART II**

***Implementation Specification***

*Schema, Operations, Storage Model, Phasing, and Open Questions*

# 6. The Particle Schema

## 6.1 Definition

A **claim** is a single falsifiable assertion in natural language —
*"Acme acquired Widget"*, *"the half-life of caesium-137 is 30.17
years"*. A **particle** is a claim plus its metadata envelope:
confidence, calibration source, provenance, uncertainty
classification, subjects, lifecycle status, and the extractor that
produced it. The term *assertion* is avoided as a term of art; use
*claim* (for the underlying sentence) or *particle* (for the envelope)
to keep the published documents consistent.

The schema is grounded in the Precise Semantics for Uncertainty
Modeling (PSUM) standard (Object Management Group, OMG Document
formal/24-12-03, June 2025: [https://www.omg.org/spec/PSUM/1.0](https://www.omg.org/spec/PSUM/1.0)).
Particles extends PSUM's Belief and BeliefStatement classes with
serialization, transport, and lifecycle semantics appropriate for
runtime agent use.

| **STANDARDS LAYER SEPARATION** |
| --- |
| PSUM owns *semantics*: what a belief is, what uncertainty means, what constitutes evidence. W3C PROV-O owns *interchange provenance*: how the history of a particle's derivation is serialized and exchanged. **Particles itself owns the *aggregation math*** — the noisy-OR confidence merge (§6.9), the multiplicative trust-chain decay (§14.6), the recency factor (§6.3), and the source-independence penalty over co-evidential groups (§6.10). PSUM does not specify these mechanisms; they are Particles' contribution on top of PSUM's semantic foundation. These standards operate at different layers and do not compete. Where PSUM and PROV-O address the same concept (e.g. provenance of an assertion), PSUM governs the meaning and PROV-O governs the serialization form. Implementations must not conflate the three vocabularies. |

| **NORMATIVE MACHINE-READABLE ARTIFACTS** |
| --- |
| The following machine-readable artifacts are required deliverables and must be published on GitHub alongside the prose spec: (1) JSON Schema for Core particle and Subject fields (`artifacts/schemas/particle.schema.json`, including a `$defs/Subject` definition); (2) canonical JSON-LD @context document (`artifacts/schemas/context.jsonld`); (3) five normative SHACL shapes — ParticleShape, SubjectShape, CorpusSnapshotShape, ProvenanceChainShape, TrustStatementShape (`artifacts/schemas/shacl/*.ttl`). These artifacts are the ground truth for conformance testing. Where the prose spec and the artifacts conflict, the artifacts take precedence for implementation purposes. The current schema version is `1.0.0` (frozen; carried in the particle's `schema_version` field). |

## 6.2 Field Reference

The whitepaper's §2.1 worked example shows the literal field shapes
in YAML. The same fields as a reference table follow. Every field
carries a `(Core)` or `(Extension X)` label; Core fields are required
for a conformant Core implementation, Extension fields may be omitted.

| **Field** | **Type / Label** | **Description** |
| --- | --- | --- |
| `id` | string, UUID (Core) | Globally unique identifier for this particle. |
| `content` | string (Core) | The claim — a single falsifiable natural-language assertion. Carries an implicit or explicit language tag. See §3.3 of the whitepaper for the claim-granularity guidance and §6.7 below for the relationship to Subjects. |
| `confidence` | Confidence object (Core) | Stores `confidence.value` — the extractor's confidence as calibrated at creation time — plus calibration provenance. Shape: `{value: float [0,1], variance: float?, calibration_source: enum, calibration_method: string?, calibration_ref: string?}`. **Normative:** `confidence.value` is stored immutably and never modified after creation. One derived quantity — `effective_confidence` — is computed at query time and never stored. See §6.3. |
| `uncertainty_nature` | enum (Core) | `ALEATORY` (irreducible) or `EPISTEMIC` (reducible). Per PSUM `UncertaintyNature`. |
| `subject_ids` | string[] (Core) | UUIDs of the Subjects this particle is about. Particles with one subject are properties of that subject; particles with two or more subjects are edges in the subject graph. See §6.7. |
| `provenance` | ProvenanceRef[] (Core) | Ordered chain of sources, agents, and prior particles. Each ref: `{type: SOURCE│PARTICLE│AGENT, corpus_entry_id: string, snapshot_id: string?, chunk_hash: string?, location: string?}`. `chunk_hash` identifies the source chunk for incremental re-extraction. See §7.2. Compatible with W3C PROV-O. |
| `extractor_ref` | ExtractorRef \| null (Core) | `{name: string, version: string}` — semver reference to the extractor that produced this particle. Enables targeted re-extraction, quality attribution, and trust-weighted confidence merging (see §6.9, §14.3–14.4). Both members are REQUIRED when the ref is present: `name` alone cannot scope re-extraction (§9.5) and `version` alone cannot join the extractor registry (§14.3), so a half-ref serves neither operation the field exists for. `version` MUST be a semver string (§14.3 orders it to determine re-extraction eligibility). The member set is open — a registry MAY carry additional hints on the ref — but implementations MUST NOT rely on any member beyond these two. `null` only for particles asserted directly by an operator or an authorized agent (§9.1a). Modelled normatively — through SDK 1.109.x the type was an open untyped object and the two member names were stated in prose only. |
| `extraction_provider_model` | string \| null (Core) | The `"<provider>:<model>"` pairing that produced this particle — the completion provider and model the extractor invoked (§14.3). A **sibling** of `extractor_ref`, not a member of it: `extractor_ref` identifies the extractor *code*, this identifies the runtime substrate that code invoked, and one extractor version may run under many models. `null` means UNRECORDED — either no completion provider produced the particle (a deterministic extractor; an operator or agent assertion, §9.1a) or it predates the field. `null` MUST NOT be interpreted as a default pairing, and implementations MUST NOT backfill, default, or recompute the value: it records what was known at mint time, and absence is a legal permanent state. |
| `asserted_by` | string, agent ID (Core) | The PSUM `BeliefAgent` making this assertion. For extracted particles this is the extractor's agent identity; for directly-asserted particles it is the operator or the authorized agent's `platform:identifier` (§9.1a). |
| `asserted_at` | ISO 8601 timestamp (Core) | When the particle was created. |
| `status` | enum (Core) | `ACTIVE`, `SUPERSEDED`, `RETRACTED`, `PROVENANCE_STALE`, `INCONSISTENCY`. Set by system operations, not by the asserting agent at creation. See §6.6 for the normative status transition table. |
| `status_reason` | enum (Core) | The cause of the current status. Set alongside `status` by every operation that changes it. Values: `RETRACTED_DEPENDENCY`, `CORPUS_ENTRY_MISSING`, `TRUST_DEMOTED` (Ext B), `LOWER_TRUST_SOURCE` (Ext B — extract-time trust resolution), `SUPERSEDED_BY_REINDEX`, `VALIDITY_EXPIRED`, `CONFLICT_RESOLVED`, `CONFLICT_PENDING` (quarantined conflict loser awaiting Review; the only reason permitted on a born-`PROVENANCE_STALE` particle), `EXPLICIT_RETRACTION`, `SOURCE_RETRACTED`, `EXPLICIT_SUPERSESSION` (deliberate revision by the asserting principal via `particle_supersede`, §9.1a), `DUPLICATE_MERGED` (an identical-content redundant copy folded into its group's survivor by exact-duplicate auto-merge (§9.2 path 4's normalized key); deliberately distinct from `EXPLICIT_SUPERSESSION` so a revert can select precisely auto-merge's own writes). Omitted on initial ACTIVE status. |
| `schema_version` | string, semver (Core) | The Particles schema version under which this particle was created (currently `1.0.0`, frozen). Enables lint to flag version mismatches and supports schema migrations. |
| `valid_until` | timestamp (Core) | Expiry for time-bounded claims. Per PSUM `Belief.duration`. Enforced at query time as a lazy filter — see §9.3. Populated at extraction by the general extractor for genuinely date-bounded claims (§9.2), as well as operator-set. Distinct from active retraction, which is reserved for source-driven invalidation. |
| `supersedes` | particle UUID (Core) | Prior particle this one revises. The superseded particle is retained for audit with status `SUPERSEDED`. |
| `properties` | dict[str, object] (Extension A) | Ontology-keyed structured data emitted by domain extractors that map cleanly to a formal ontology (e.g. Nomisma for coins). Schema is extractor-defined; keys are ontology IRIs. See §6.8. Not used by Core operations; preserved for domain-tool interop. |
| `uncertainty_kind` | enum (Extension A) | `CONTENT`, `ENVIRONMENT`, `GEOGRAPHICAL_LOCATION`, `OCCURRENCE`, or `TIME`. Per PSUM `UncertaintyKind`. |
| `basis` | Basis object (Extension A) | Per PSUM `Basis` and `EvidenceType`. Subtypes: `EMPIRICAL_EVIDENCE`, `THEOREM_PROVING`, `INFERENCE_BASED_ON_EMPIRICAL_DATA`, `COMMON_KNOWLEDGE`. |
| `sequence_context` | particle UUID[] (Extension A) | Adjacent particle UUIDs from the same extraction pass providing narrative context. Populated by extractors that detect inter-particle dependencies; omitted when the particle is independently interpretable. |
| `particle_type` | enum (Extension A) | `CLAIM` (default); `REVIEW` — audit records written by the Review operation (§9.6) so that review annotations are excluded from CLAIM-targeted lint checks; `NARRATIVE` — prose-level structural connective tissue over claims, whose body is derived by traversing `PART_OF` / `SEQUENCE_IN` edges rather than stored. Reserved future types: `ACTION`, `ANNOTATION` (forward compatibility only). |
| `assertion_modality` | enum (Extension A) | Truth-aptness axis: `FALSIFIABLE` (default) is observer-independent and truth-apt; `EVALUATIVE` (value/preference judgement), `EXPERIENTIAL` (first-person inner-state report), and `CONSTITUTIVE` (a rule a document establishes) are not. The engine applies truth-semantics — §6.6 conflict resolution, L-SEM-01 contradiction lint, L-IDX-01 co-evidential clustering — **only** to `FALSIFIABLE` particles; non-falsifiable particles co-exist and are never contradiction-checked or trust-arbitrated. **Exception:** the §6.4 document-supersession prior (rung 1.5) is an *editorial* relation, not a truth-engine rung, so it runs above the truth-apt gate and retires a superseded non-`FALSIFIABLE` claim (e.g. a `CONSTITUTIVE` definition replaced by its superseding document). Orthogonal to the document-scope axis (`WORLD` / `DOCUMENT_META`, carried in `properties`). Additive and Optional: old particles default to `FALSIFIABLE`, so `SCHEMA_VERSION` is unchanged. |
| `contributors` | ContributorRef[] (Extension D/E) | Who extracted / curated / asserted this claim: `{id: string, role: string, at: ISO 8601}`. `id` shares the AUTHOR-scoped `SourceRef` namespace (`platform:identifier`, §6.5); `role` is an open vocabulary with recommended values (`author`, `extractor`, `curator`, `reviewer`, `importer`, `agent`). Additive and Optional; Core operations MUST NOT branch on it (`null` ≡ `[]`). **List semantics:** `contributors` is an **ordered, append-only attribution chain** — extraction appends the extractor (and, where a UGC `Snapshot.author_id` is known, the author); later curation, review, and import each append their own ref. Entries are never rewritten or reordered (sort on `at` when a timeline view is needed); duplicate `(id, role)` pairs SHOULD be coalesced. Contributor `id` is attribution provenance, **never part of claim identity or the dedup key** (like `asserted_by`), so multi-contributor claims do not wrongly collapse; appending a contributor never mutates `confidence.value` and never encodes agreement. Also present on `CorpusEntry` and `Subject`. Carried by the interchange format so attribution survives cross-store transfer. |
| `structured_claim` | StructuredClaim (Extension A) | A **derived, regenerable** subject-predicate-object rendering of `content`: `{subject, predicate, object: ClaimTerm, subject_id: UUID?, structurizer_id, structurizer_version, generated_at}`. A `ClaimTerm` is `{kind: URI \| TOKEN \| LITERAL, value, datatype?, language?}` — `TOKEN` records a lexical name no vocabulary resolved, so coverage is not restricted to ontology-aligned sources; a `LITERAL` is legal in object position only. The immutability invariant generalizes here: *the asserted form is immutable, the derived form is regenerable* — this annotation is produced by tooling from `content`, carries its own derivation stamp, and its fidelity is a property of the annotation, never evidence about the claim. It MUST NOT influence `confidence`, `status`, or conflict resolution. Generated in exactly two places (extraction, and the structured-claim backfill); an exporter MUST NOT generate one inline. **Absence is a legal permanent state** — prose with no honest triple is left unannotated, no operation degrades without it, and lint does not flag its absence. Additive and Optional: old particles default to `null`, so `SCHEMA_VERSION` is unchanged. |
| `canonical_form` | enum (Extension A) | Which of the prose/structured pair is the assertion. `PROSE` (default) — `content` is asserted and any `structured_claim` is the derived annotation; this is every particle the reference SDK produces today. `STRUCTURED` — the triple is asserted and `content` is a derived verbalization, the shape a structure-native source produces (an RDF deposit; a Wikibase entity reading); it requires `structured_claim` to be present. Additive and Optional: old particles default to `PROSE`, so `SCHEMA_VERSION` is unchanged. **`STRUCTURED` does not make `content` mutable.** The §6.2 immutability rule is unqualified for both members of the pair: "derived" states which artefact a regeneration pass may *produce*, not that a stored value may be rewritten in place. A conforming implementation regenerates a verbalization by re-extracting the snapshot under a new extractor version and reconciling through the §6.6 ladder — the same path every other particle takes — so `canonical_form` introduces no new mutation path. A derived `content` MUST still satisfy the non-empty constraint on `content`; a verbalization procedure is therefore required to terminate in a value that always exists (for RDF, the term's IRI). |
| `tags` | string[] (Extension C) | Operator-assigned folksonomy labels. May form hierarchical taxonomies defined in a `TaxonomyDefinition` (§16.2). See §16 for taxonomy-aware retrieval. |
| `context_fingerprint` | string, hash (Extension C) | A SHA-256 fingerprint over the UUIDs of **all particles that were `ACTIVE`** in the asserting store when this particle was created — the whole-store baseline the §16.1 algorithm defines. (A narrower dependency-subgraph fingerprint is anticipated future tightening; §16.1.) See §16.1. |

| **CORE / EXTENSION LABELLING** |
| --- |
| Every field above carries a label: `(Core)` or `(Extension X)`. Core fields are required for a Core-conformant implementation. Extension fields belong to the named extension and may be omitted without affecting Core conformance. The label is part of the field definition, not advisory. |

| **PARTICLE LITERAL — WORKED EXAMPLE** |
| --- |
| The whitepaper §2.1 worked example shows two particles in YAML form. The same shape applies here: Core fields are always present; Extension fields appear only when their extractor emits them. Where the prose spec and the worked example diverge on a field name or casing, the worked example is the ground truth and the spec is amended to match. |

## 6.3 Confidence Representation

The confidence system defines two distinct quantities with different ownership and lifecycle. This separation is normative — implementations that conflate them will produce inconsistent behaviour across extraction, query, and trust evaluation. Calibration is an *input-side* transformation with full audit provenance on the stored record, not a read-side recompute. ( which revises three-quantity framing.)

| **Quantity** | **Owner** | **Where it lives** | **How it is computed** |
| --- | --- | --- | --- |
| `confidence.value` | Extractor | Stored immutably on the particle at creation time. Never modified after creation. | The extractor's confidence **as calibrated at creation time**: the raw self-reported value (`calibration_source = EXTRACTOR_DIRECT`), the calibrated value when the extractor carries an active calibration (`CALIBRATED_BENCHMARK`, with `calibration_method` recording how and `calibration_ref` recording which benchmark run produced the calibration), a human-assigned value (`HUMAN_REVIEW`), or an uncalibrated agent self-report stored via the MCP write surface (`AGENT_ASSERTED`). |
| `effective_confidence` | Query layer | Computed at query time. NOT stored. Discarded after query response. | `confidence.value × extractor.trust_weight × source_trust_rank × recency_factor`. Used for ranking, filtering, and disclosure. Never written back to the particle store. Absence of trust policy is strictly neutral: with no applicable `SourceTrustStatement` or source-trust rule, `source_trust_rank` is 1.0 — the factor is an operator demotion signal, not a prior. See §6.9 for the merge formula across multiple extractors or co-evidential groups. |

Because calibration is applied at creation, recalibration propagates only through re-extraction: a particle keeps the calibration in force at its creation, with `calibration_ref` as the audit trail. `extractor.trust_weight` is the live read-side correction lever.

The numeric ground truth for this section — the exact `effective_confidence` and calibration formulas, the constant values they consume, and worked test vectors an implementation reproduces bit-for-bit — is pinned in the **Conformance Profile** (`docs/spec/conformance-profile.md` §4 and its companion `artifacts/conformance/profile.yaml`), the behavioural/quantitative counterpart to the structural schema/SHACL artifacts. These are the **L2 deterministic-compute** conformance surface; `particles conformance check` self-certifies against them.

The full Confidence object shape:

```yaml
confidence:
  value: 0.82
  variance: 0.05
  calibration_source: CALIBRATED_BENCHMARK
  calibration_method: temperature_scaling
  calibration_ref: extractor-bench-v1/run-2026-04-15
```

Field semantics:

- `calibration_source` (mandatory): how the **stored** `confidence.value` was derived. `EXTRACTOR_DIRECT` — taken directly from the model's output logits (lowest trust, no calibration applied); `AGENT_ASSERTED` — an uncalibrated direct agent self-report stored via the MCP write surface (lowest trust, no calibration applied); `CALIBRATED_BENCHMARK` — the stored value is the extractor's raw output passed through the calibration fitted against a labelled benchmark population, applied at creation time (medium trust); `HUMAN_REVIEW` — assigned or confirmed by a human reviewer (highest trust).
- `calibration_method` (mandatory for `CALIBRATED_BENCHMARK`): the statistical method used to produce a well-calibrated probability. Recommended value: `temperature_scaling` — in the reference SDK this is Guo et al. (2017) **logit-space** temperature scaling, `sigmoid(logit(raw) / T)`, with T fit by NLL minimization over `[0.01, 10]`. T = 1 is the identity, T > 1 pulls values toward 0.5, T < 1 pushes them toward the ends, and 0.0 / 1.0 are exact fixed points. **Pairs whose raw confidence is 0.0 or 1.0 are excluded from the fitting population**: they are exact fixed points of the transform, so including them lets evidence no temperature can act on determine the temperature. A fitted T is admissible only if the labels carry both outcomes, at least two distinct movable confidences are present, the value is off both optimizer bounds, and calibration error actually falls; a fit failing any of these is not stored, and the extractor keeps emitting `EXTRACTOR_DIRECT`. Through v1.114.x the reference SDK instead applied a scalar-domain approximation, `clamp(raw / T, 0, 1)`, which saturated for T < 1 (values above T collapsed onto 1.0, losing their order) and at high T degraded without bound; a stored calibration record now declares which form its temperature parameterises. Acceptable alternatives: `isotonic_regression`, `platt_scaling` (not implemented in the reference SDK). `EXTRACTOR_DIRECT`, `AGENT_ASSERTED`, and `HUMAN_REVIEW` particles may omit this field.
- `calibration_ref` (recommended): a reference to the specific benchmark run in the extractor's `calibration_history` that produced this confidence value. Makes the stated confidence fully traceable and auditable.

The purpose of `calibration_method` is cross-extractor confidence interoperability: a confidence value of 0.8 should mean an empirical accuracy of approximately 80% regardless of which model architecture or vendor produced the extractor. Without a standard calibration method, confidence values are internally consistent within an extractor but not comparable across extractors. Temperature Scaling is the recommended default because it is model-agnostic, cheap to apply, and well-validated in the literature.

### Recency factor (content age decay)

`effective_confidence` is additionally modulated by a `recency_factor` computed from the source's `content_published_at` timestamp (§7.2) and a per-`source_type` half-life and floor:

```
recency_factor = max(floor, 0.5 ^ (age_days / half_life_days))
```

For example, REDDIT_POST defaults to a 60-day half-life with a 0.10 floor: an 18-month-old Reddit comment retains at most 10% of its at-extraction effective confidence. Half-lives and floors are operator-configurable per `source_type` in `config.yaml`. STABLE sources (PDFs, published papers) typically have no decay (`recency_factor = 1.0`). The recency factor is applied at query time only; `confidence.value` itself is never modified.

### `valid_until` lazy filter

`valid_until` is enforced at query time as a lazy filter: expired particles are filtered out of the candidate set without active retraction. Active retraction (status transition to `RETRACTED`) is reserved for source-driven invalidation — the source has been superseded, or its author downgraded — not for the routine passage of time. The mechanism lives in §9.3; this section is the schema-side note.

| **CALIBRATION REQUIREMENT** |
| --- |
| Any extractor claiming `calibration_source = CALIBRATED_BENCHMARK` MUST document its `calibration_method`. The reference SDK ships a temperature-scaling calibration utility (`particles extractor calibrate <id>`) that consumes the benchmark harness's gold-standard particles to fit the scaler; once an extractor carries an active calibration, every subsequent extraction stores the scaled value stamped `CALIBRATED_BENCHMARK`. Extractor authors are encouraged to evaluate against the TruthfulQA and HaluEval benchmark suites once those are wrapped as `BenchmarkSuite` artefacts; the harness itself (`particles extractor benchmark <id>`, v0.21.0) accepts any conformant suite (§13.3). |

## 6.4 Source Trust Model

The Source Trust Model allows operators to specify how much weight to give to particles whose provenance traces to a particular source, source type, or author within a source. It is the counterpart to the Extractor Trust Model (§14.4): while extractor trust discounts confidence based on *how* particles were extracted, source trust discounts confidence based on *where* the underlying content came from. (.)

The conflict-resolution ladder's ordering and its threshold constants — the trust differential (`0.15`), the demotion/cascade caps, and the recency-decay table — are pinned as **L2** conformance requirements in the **Conformance Profile** (`docs/spec/conformance-profile.md` §2, §5; `artifacts/conformance/profile.yaml`), the single source of truth this spec cites for those values. The ladder ordering and the cascade gates are additionally **machine-checkable**: the Profile's `conflict_ladder`, `cascade_gate`, and `cascade_cap` test-vector families (§5.1) state, as plain data, which rung fires for a given pair and which batches the per-run cap truncates.

### SourceTrustStatement schema

A `SourceTrustStatement` is a durable, operator-defined policy record that scopes a trust rank to a domain and optionally to a specific author within a source. Trust statements are stored in the particle store as first-class records and consulted by conflict resolution and query operations.

```yaml
SourceTrustStatement:
  statement_id: string (UUID)
  domain: string                # e.g. 'biomedical', 'linux_kernel'
  source_ref: SourceRef         # what this statement applies to
  trust_rank: float [0, 1]      # operator-assigned trust within this domain
  policy_provenance: enum       # OPERATOR_DIRECT | REVIEWER_DERIVED | REGISTRY_ENDORSED
  asserted_by: string           # agent or operator ID
  asserted_at: ISO 8601
  basis: string?                # free text: why this rank was assigned
  review_id: string?            # UUID of the Review that produced this statement

SourceRef:
  type: SOURCE_TYPE | CORPUS_ENTRY | AUTHOR
  value: string
  # SOURCE_TYPE: e.g. 'academic_paper', 'blog', 'forum'
  # CORPUS_ENTRY: a specific corpus entry_id
  # AUTHOR: scopes trust to a specific author within a UGC source
```

| **`domain` SCOPING (NORMATIVE NOTE)** |
| --- |
| `domain` is an **operator-defined free string** — the standard deliberately does not define a domain vocabulary. Matching is **exact-string** within an operator's own store: a statement scoped to `'biomedical'` never applies to a particle whose derived domain is `'biomedicine'`. The domain a particle's source maps to is derived from its corpus entry's `source_type` via the extractor registry's MUST-clause applicability mapping (the same derivation §9.3 step 5 and the §6.6 conflict ladder use) — a source type with no MUST clause has no domain, and domain-scoped statements cannot apply to it. **Cross-operator domain alignment is out of scope**: two operators' `'biomedical'` strings are not asserted to mean the same thing. Where trust policy needs to travel between operators, the unit of exchange is the trust lens (below), which carries whole statements rather than aligning domain vocabularies. |

`policy_provenance` enum:

- `OPERATOR_DIRECT` — pre-configured by operator with domain knowledge (highest authority).
- `REVIEWER_DERIVED` — produced from a single Review session (medium authority); cascade requires N ≥ 3 confirmations.
- `REGISTRY_ENDORSED` — endorsed by a trusted registry (authority depends on registry trust weight).

Author-scoped trust statements are the correct model for user-generated content sources. It is not meaningful to say *"I trust GitHub more than Reddit"* — a project maintainer's comment on GitHub carries more weight than an anonymous bystander's, and a domain expert's Reddit comment outweighs a throwaway account. Author-scoped statements capture this:

```yaml
- domain: linux_kernel
  source_ref: { type: AUTHOR, value: "github:torvalds" }
  trust_rank: 0.95
- domain: amateur_radio
  source_ref: { type: AUTHOR, value: "reddit:u/w6xyz" }
  trust_rank: 0.85
- domain: biomedical
  source_ref: { type: SOURCE_TYPE, value: "academic_paper" }
  trust_rank: 0.90
- domain: biomedical
  source_ref: { type: SOURCE_TYPE, value: "blog" }
  trust_rank: 0.40
```

The `policy_provenance` field makes trust statements self-describing about their own epistemic quality. A single reviewer resolving one conflict (`REVIEWER_DERIVED`) produces a weaker policy claim than an operator with deep domain expertise pre-configuring their trust model (`OPERATOR_DIRECT`), which is weaker than a statement endorsed by a trusted registry (`REGISTRY_ENDORSED`). Consumers of trust statements MUST take `policy_provenance` into account when deciding how much weight to give a trust rank.

| **POLICY QUALITY IS EPISTEMIC QUALITY** |
| --- |
| Trust statements are themselves claims with provenance. The `policy_provenance` field is the trust statement's equivalent of a particle's `calibration_source`. Systems that treat a `REVIEWER_DERIVED` trust rank as equivalent to an `OPERATOR_DIRECT` rank are making the same mistake as systems that treat `EXTRACTOR_DIRECT` confidence as equivalent to `CALIBRATED_BENCHMARK` confidence. |

### Layered trust lookup

When evaluating a particle's source trust at query or conflict time, the engine consults `SourceTrustStatement` records in a four-tier cascade:

1. **CORPUS_ENTRY** — the most specific tier. If a statement exists for the particle's specific corpus entry, use it.
2. **AUTHOR** — if no entry-scoped statement, look up by `author_id` (§6.5).
3. **SOURCE_TYPE** — if no author-scoped statement, look up by source type.
4. **Fallback** — if no domain-scoped statement applies, use the source type's default trust weight from the standard's catalogue.

The first match wins; later tiers do not aggregate. This ordering ensures that more-specific policies dominate more-general ones.

### Conflict resolution with source trust

When two ACTIVE particles conflict and their provenance traces to different sources, the conflict resolution algorithm in §9.2 and §9.4 applies source trust statements before surfacing an `INCONSISTENCY`. The ladder is normative:

1. **ALEATORY check.** If either particle has `uncertainty_nature = ALEATORY`, surface `INCONSISTENCY` immediately. Source trust cannot resolve irreducible uncertainty.
1.5. **Document-supersession prior**. If one particle's provenance corpus entry **(transitively) supersedes** the other's — an authored, in-corpus editorial relation that *this document replaces that one* (e.g. an ADR's `supersedes:` frontmatter, captured at ingest by a genre adapter) — prefer the superseding claim: set the superseded particle `PROVENANCE_STALE` with `status_reason = DOCUMENT_SUPERSEDED` and surface **no** `INCONSISTENCY`. **This prior is made modality-independent and placed above the truth-apt gate (step 1.7):** an authored replacement is an *editorial* fact that does not depend on either claim's truth-aptness, so it MUST retire a superseded `CONSTITUTIVE` definition (a formula/rule the truth engine would otherwise never see). The replacement is confirmed by a conflict signal reframed for the non-truth-apt case ("does the superseding claim replace, not merely restate, the superseded one?"); absent that signal both claims are kept (default-safe). It fires **only on an actual conflict between two specific claims**: a still-true, non-conflicting claim from the superseded document never conflicts, so it is never demoted (the relation is document-level, but the prior is claim-level and conflict-gated). It sits *above* both the truth-apt gate and the trust rung but *below* the ALEATORY exclusion. Single-trust-order stores only (same gating as rung 2). Cross-entry stores never reconcile this at extract time (intra-entry only); a dedicated reconcile sweep runs it cross-entry over already-extracted particles.
1.7. **Truth-apt gate** (scope narrowed). If either particle is non-truth-apt (`assertion_modality ≠ FALSIFIABLE`), the truth engine — the contradiction probe, trust arbitration (step 2), and `INCONSISTENCY` manufacture (step 3) — has no shared truth to adjudicate; the two co-exist. This gate governs *only* the truth-engine rungs below it; the editorial supersession prior (step 1.5) is lifted above it.
2. **Source trust check** (Extension B only — see below). Evaluate via layered lookup. If `trust_rank` differential exceeds the configured threshold (default 0.15), set the lower-trust particle `PROVENANCE_STALE` with `status_reason = TRUST_DEMOTED`.
3. **Default.** Create an `INCONSISTENCY` particle referencing both and queue for human Review (§9.6).

For ALEATORY conflicts, source trust never resolves — the standard's ladder is explicit on this point; rung 1.5 likewise never fires on an ALEATORY pair (rung 1 — now lifted to the top of the ladder — wins above it). ALEATORY is the one exclusion that outranks the supersession prior: an irreducible disagreement is never retired by an editorial relation.

### Trust statements as review outputs

Human review of `INCONSISTENCY` particles (§9.6) is the primary mechanism for generating new `SourceTrustStatement` records. When a reviewer resolves a conflict by preferring one source over another, the Review operation creates a `SourceTrustStatement` with `policy_provenance = REVIEWER_DERIVED`. This statement is then available to resolve future conflicts in the same domain — subject to the cascade gating in Extension B — making the system progressively smarter without requiring upfront policy configuration.

| **DEMOTION-ONLY RULE (NORMATIVE)** |
| --- |
| `SourceTrustStatement` records may only *demote* confidence — they may never silently suppress conflict visibility. A statement that resolves a conflict MUST set the lower-trust particle to `PROVENANCE_STALE` (making the resolution visible and auditable) rather than omitting the lower-trust particle from query results. `INCONSISTENCY` particles created before a trust statement existed are retained in the audit log even after auto-resolution. This rule prevents trust statements from becoming an invisible suppression mechanism. Extension B (auto-cascade) never violates this invariant; it never promotes trust automatically. |

| **EXTENSION B — SHIPPED** |
| --- |
| `SourceTrustStatement` automatic cascade — the resolution of conflicts without human review using stored trust statements — is Extension B. It is implemented and shipped. The cascade gate is policy-aware: `OPERATOR_DIRECT` statements cascade unconditionally; `REVIEWER_DERIVED` statements require N ≥ 3 reviewer confirmations (operator-configurable) before they cascade. The auto-cascade is bounded by a `max_cascade` parameter (default 500) per statement to prevent runaway propagation. See §15 for the full Extension B specification. |

### Trust lenses — shareable policy bundles

A **`TrustLensDefinition`** is a named, versioned, depositable corpus
artifact (`source_type = TRUST_LENS_DEFINITION`, detected by its
`"kind": "TrustLensDefinition"` sentinel) bundling **portable** trust
policy across four layers: SOURCE_TYPE-scoped trust statements, URL trust
rules (domain baselines and pattern modifiers), extractor trust-weight
overrides, and — since — **content-age decay rules** (`decay_rules`:
per-`source_type` or per-URL-pattern recency half-life / floor, §6.3).
Since a lens MAY additionally carry **usefulness (utility) rules**
(`utility_rules`, §6.3) — the outcome-learning judgment of how strongly a
belief's demonstrated *use* should promote it on a projection / digest
ranking. `CORPUS_ENTRY`-scoped statements are excluded — they key on
store-local identifiers and do not travel. The normative document shape is
`artifacts/schemas/trust_lens.schema.json`. Versions are monotonic
integers; materialising a lens replaces a lower-versioned materialisation
of the same name, and a lower-or-equal version MUST be rejected.

The **`decay_rules`** layer composes most-skeptical-wins like the trust
layers, with two differences specific to decay: a rule is an
**absolute** `(half_life_days, floor)` pair (not an additive modifier — a
half-life is not meaningfully summed), and the **URL-pattern layer is more
specific than the source_type layer** (a per-subreddit rule overrides the
source-type default in either direction, so a lens can declare a source
*more* durable than the global default, which a plain minimum could not
express). The store's local `content_age_decay` config (§6.3) is the base
the lens decay rules overlay; a `source_type` / URL a lens is silent about
keeps the local config's curve (or no decay). With no decay-bearing lens
adopted the resolved decay is byte-for-byte the global config.

The **`utility_rules`** layer (composition) is the
usefulness analogue of decay, and observes the same two-quantity separation
the confidence math uses (§6.3): the per-belief utility *evidence* — a
recency-weighted count `R` of **utility events**, each recording that an agent
demonstrably *acted* on the belief in a harvested session — is store-local and
implementation-defined (how it is mined is not part of this standard), while
the portable *judgment* travels in the lens as a `(half_life_uses_days,
rank_lift)` rule per `default` / `source_type` / `url_pattern` scope.

At render time the evidence and judgment compose into an **additive rank
lift** on the projection ordering key:

```
rank_score(p) = effective_confidence(p) + λ · ln(1 + R(p))
```

where `λ` is the rule's `rank_lift`. Four normative constraints:

(a) `rank_score` is an **ordering score, not a confidence** — it is NOT
constrained to `[0, 1]`, and an implementation MUST NOT present it as a
confidence value nor store it. The stored `confidence.value` and the
read-time `effective_confidence` (§6.3) are never modified by utility.

(b) The lift is **promotion-only**: `λ ≥ 0` and `R ≥ 0`, so the term is
non-negative and a belief with no utility evidence receives exactly `+0` and
keeps its base position (cold-start neutrality) — a store with no evidence
and no utility-bearing lens ranks byte-for-byte as before.

(c) The lift MUST be applied **only** on a projection / digest ranking (the
"what stays important" consolidation decision) and MUST NOT enter
semantic-search retrieval ranking — utility governs which beliefs render,
never which are *retrieved*.

(d) Growth MUST be sublinear in `R` so that no single belief dominates by
reinforcement count alone; the logarithmic form above adds only `λ·ln 2` per
doubling of `R`. (originally bounded this with a saturating
multiplier and a hard `cap`; that form was superseded because
saturation discarded count magnitude entirely — every sufficiently-reinforced
belief pegged the cap and the ranking reverted to base confidence — and
because a multiplicative lift is *smaller in absolute terms* for exactly the
low-confidence, high-use beliefs the layer exists to promote.)

Across adopted lenses utility composes most-skeptical-wins (least promotion:
minimum of each parameter, so the smallest `λ` wins).

A store **adopts** lenses by name; adoption is store state, not
configuration. At query/render time the effective trust policy composes
as follows (normative):

1. The store's **local** statements and rules win per key over every
   adopted lens.
2. Across multiple adopted lenses, the **minimum** (most skeptical)
   rank/score per key applies; URL-pattern modifiers sum within a lens
   and the minimum of the per-lens sums applies across lenses.
3. A key neither local policy nor any adopted lens asserts contributes
   **no** factor (the §6.3 neutral default) — adopting a lens MUST NOT
   demote sources the lens does not name.

These rules preserve the demotion-only invariant: adopting an additional
lens can only lower trust, never raise it past another adopted lens's
demotion; an operator who disagrees overrides locally, which is itself
an auditable act. In federated queries the **viewer's** adopted lenses
apply to every store's candidates (§6.3).

## 6.5 Author Identity Scoping

For user-generated content (UGC) sources, the identity of the content creator is captured in the corpus snapshot metadata and propagated through to extracted particles via the `provenance.corpus_entry_id` → snapshot lookup chain. This enables source trust statements (§6.4) to be evaluated at query time and lets the wiki article exporter attribute each cited claim to its individual author.

```yaml
Snapshot:
  # ...other fields, see §7.2
  author_id: string?         # author identity within the source
                             # format: '{platform}:{identifier}'
                             # e.g. 'github:karpathy', 'reddit:u/gertylooker'
  author_role: string?       # role metadata if available
                             # e.g. 'maintainer', 'first-time-contributor',
                             #      'verified-account', 'op'
```

Extractors for UGC sources SHOULD populate `author_id` from platform metadata where available; the Reddit and GitHub extractors do so. `author_id` MAY be omitted or pseudonymised for privacy-sensitive UGC sources — the `EPHEMERAL` mutability class (§7.4) is the canonical way to opt out of author retention entirely.

`author_role` is an optional signal extractors may include as a confidence modifier (a verified maintainer's claim about their own project carries more weight than an anonymous comment) without requiring an operator-defined trust statement for every individual author.

| **AUTHOR_ID NORMALISATION** |
| --- |
| `author_id` values follow the format `{platform}:{identifier}`. Implementations MUST normalise platform-internal aliases to the canonical form before persisting: `github:karpathy` (not `gh/karpathy` or `@karpathy`), `reddit:u/jeff` (preserving the `u/` prefix that identifies a user vs. a subreddit). The general extractor performs this normalisation as a post-extraction pass (for the GitHub-specific normalisation rules). |

The Review operation (§9.6) surfaces `author_id` and `author_role` in its UI so a reviewer can quickly assess the source of conflicting claims and produce author-scoped trust statements (§6.4) when appropriate.

## 6.6 Normative Status Transition Table

The following table is the single authoritative source for particle status transitions. Every operation in §9 that changes particle status must conform to this table. Implementations that define additional transitions are non-conformant.

| **From status** | **To status** | **Triggering operation** | **Condition** | **status_reason** |
| --- | --- | --- | --- | --- |
| (new) | ACTIVE | Extract (§9.2) | Extraction produces a new particle with no conflicts. | (omitted on initial ACTIVE) |
| (new) | PROVENANCE_STALE | Extract (§9.2) — INCONSISTENT verdict | The losing candidate of an unresolved §6.4 conflict is persisted *quarantined* — full content, provenance, confidence, and subjects intact — invisible to Query/Lint by the existing status filters. **Condition: this birth is permitted only with `status_reason = CONFLICT_PENDING`**, enforced at the persistence seam. | CONFLICT_PENDING |
| ACTIVE | SUPERSEDED | Extract (§9.2) or agent REVISE | A new particle is created that sets supersedes = this particle's id. | SUPERSEDED_BY_REINDEX or (omitted for agent REVISE — reason is on the superseding particle) |
| ACTIVE | RETRACTED | Agent RETRACT or operator action | Explicit withdrawal. Lazy propagation sets dependents to PROVENANCE_STALE. | EXPLICIT_RETRACTION (single particle); SOURCE_RETRACTED for a bulk `corpus retract` — which also covers INCONSISTENCY → RETRACTED for the same reason |
| ACTIVE | PROVENANCE_STALE (retraction cascade) | Lint (§9.4) | A particle in the provenance chain was retracted or superseded. | RETRACTED_DEPENDENCY |
| ACTIVE | PROVENANCE_STALE (corpus missing) | Lint (§9.4) | The referenced corpus snapshot no longer exists. | CORPUS_ENTRY_MISSING |
| ACTIVE | PROVENANCE_STALE (expired) | Lint (§9.4) | valid_until timestamp has passed. | VALIDITY_EXPIRED |
| ACTIVE | PROVENANCE_STALE (trust demotion) | Extract (§9.2) or Lint (§9.4) — Extension B only | Source trust rank differential exceeds threshold; a higher-trust conflicting particle exists. | LOWER_TRUST_SOURCE when the §6.4 conflict-resolution ladder demotes at extract time; TRUST_DEMOTED when a Lint trust pass demotes |
| ACTIVE | PROVENANCE_STALE (document supersession) | Extract (§9.2) / reconciliation — §6.4 ladder rung 1.5 | The conflicting claim's provenance corpus entry is **(transitively) superseded** by the winning claim's — an authored in-corpus *"this document replaces that one"* relation. Fires only on an actual conflict; non-conflicting context from the superseded document is never touched. The superseded claim is demoted (and stays auditable — demotion-only); no `INCONSISTENCY` is surfaced. | DOCUMENT_SUPERSEDED |
| ACTIVE | INCONSISTENCY | Extract (§9.2) or Lint (§9.4) | A semantic conflict is detected with another ACTIVE particle and the conflict resolution ladder does not resolve it automatically. The INCONSISTENCY status is set on a new particle referencing both; the originals remain ACTIVE. | (set on the INCONSISTENCY particle, not the originals) |
| INCONSISTENCY | (resolved — see below) | Review (§9.6) | Human reviewer selects a resolution action. | — |
| INCONSISTENCY → loser | PROVENANCE_STALE | Review: PREFER SOURCE A or B | The non-preferred particle is demoted. A loser already quarantined (born `CONFLICT_PENDING`) keeps its `PROVENANCE_STALE` status; only its reason is updated — no status transition occurs. | CONFLICT_RESOLVED |
| INCONSISTENCY | RETRACTED | Review: PREFER A/B or BOTH VALID | **Wrapper-terminal rule:** every non-DEFER resolution retracts the INCONSISTENCY wrapper itself, removing it from the review queue. DEFER is the only action that leaves a wrapper open. | CONFLICT_RESOLVED |
| INCONSISTENCY → ACTIVE (aleatory) | ACTIVE (both) | Review: BOTH VALID | Both claims set uncertainty_nature = ALEATORY and remain queryable. A quarantined constituent is *promoted*: a new ACTIVE particle is minted (fresh id, `supersedes` → the quarantined row) — there is no `PROVENANCE_STALE → ACTIVE` transition. INCONSISTENCY particle retracted. | (no status_reason change; uncertainty_nature updated) |
| INCONSISTENCY | INCONSISTENCY (deferred) | Review: DEFER | Status unchanged. Reviewer note appended. Re-queued. | (no change) |
| PROVENANCE_STALE | SUPERSEDED | Reindex supersession of a stale particle; Review PREFER B / BOTH VALID or trust cascade over a quarantined loser | A new ACTIVE particle replaces the stale one. For a quarantined loser whose conflict resolved in its favour, the new particle is *minted from it* (fresh id, `supersedes` set, provenance and embedding carried over — the Reindex pattern) and the quarantined row is superseded. Promotion never reactivates a stale particle. | SUPERSEDED_BY_REINDEX (reindex) or CONFLICT_RESOLVED (quarantine promotion) |
| PROVENANCE_STALE | ACTIVE | Reindex (§9.5) — re-extraction | A Reindex pass produces a new extraction; the new particle is ACTIVE. | (omitted — new particle, fresh status) |
| PROVENANCE_STALE | RETRACTED | Operator action | Explicit cleanup. | EXPLICIT_RETRACTION |
| SUPERSEDED | ACTIVE | Unmerge — revert of a recorded exact-duplicate auto-merge | The **only** exit from a terminal state, and the only reversible transition in this table. **Condition: permitted only when the row's *current* `status_reason` is `DUPLICATE_MERGED`**, enforced at the persistence seam (the table is keyed on status alone, as with the `CONFLICT_PENDING` birth gate above). The governing rule is that a status transition is reversible only if it encoded no judgment: an auto-merge is a hash predicate over identical content (§9.2 path 4) — no model, no principal's opinion — so it qualifies. The retirement stamp is **cleared** with the transition (write-once is per *retirement*, not per row: a withdrawn retirement releases the stamp, while a later hop within a retirement still never overwrites it). | (cleared — the pre-merge row carried none, and the revert restores the row rather than tagging it; the audit lives in the operator event log) |
| SUPERSEDED | (terminal for every other reason) | — | Retained for audit. Terminal for `EXPLICIT_SUPERSESSION`, `SUPERSEDED_BY_REINDEX`, `LOWER_TRUST_SOURCE`, `DOCUMENT_SUPERSEDED`, and `CONFLICT_RESOLVED` — each of those records a judgment, and only the single reason-gated exception above is reversible. | (unchanged) |
| RETRACTED | (terminal) | — | Retained for audit. Retraction is always a principal's judgment, so it is **not** reversible; the `SUPERSEDED → ACTIVE` exception above does not generalise to it. | (unchanged) |

| **CONFLICT RESOLUTION LADDER** |
| --- |
| The full normative ladder lives in §6.4. Summary: (1) ALEATORY check — if either particle has `uncertainty_nature = ALEATORY`, surface INCONSISTENCY immediately. (1.5) Document-supersession prior — if one particle's provenance document (transitively) supersedes the other's and a replacement signal confirms the conflict, demote the superseded particle PROVENANCE_STALE / DOCUMENT_SUPERSEDED (no INCONSISTENCY); **modality-independent and above the truth-apt gate**, so it reaches superseded CONSTITUTIVE definitions; single-trust-order stores only. (1.7) Truth-apt gate — non-FALSIFIABLE particles co-exist; this gate governs only the truth-engine rungs below it. (2) Source trust check (Extension B) — apply layered trust lookup; if differential exceeds threshold, set lower-trust particle PROVENANCE_STALE. (3) Default — create INCONSISTENCY and queue for Review. Implementations MUST apply steps in order. Co-evidential paraphrase pairs (§6.10) are excluded from conflict candidacy at step 0, as are stance pairs except a same-holder reversal. |

## 6.7 Subject as First-Class Entity

A `Subject` is a canonical real-world entity that one or more
particles are *about*. Subjects are the knowledge-graph backbone of
the particle store: single-subject particles are properties of that
subject; multi-subject particles are edges between subjects.
(.)

```yaml
Subject:
  id: string (UUID)
  canonical_name: string         # the resolved name (e.g. "POET Technologies")
  description: string?           # short disambiguating description
  aliases: string[]              # operator- or extraction-time observed aliases
  external_ids: ExternalRef[]    # links to external ontologies (Wikidata, etc.) — §6.8
  subject_class: string?         # ontology class hint for exporters (e.g. "nmo:Material")
  created_at: ISO 8601
  asserted_by: string            # agent or resolver that created this subject
  contributors: ContributorRef[]?  # Extension D/E attribution
```

The particles that reference a subject are recorded in the
`particle_subjects` join table, not on the Subject record itself.

**Subject granularity.** A subject is an entity that would
warrant its own item in a general-purpose ontology such as Wikidata — a
coin type, a country, a person, an event. Attributes of an entity
(an issue period, a physical specification, a founding date) are
expressed as particles *about* the subject, never as subjects
themselves. Same-named entities across different eras, countries, or
domains are **distinct subjects** — multiple coins named "1 Pfennig"
across eras and issuers each get their own Subject — and external IDs
(a Wikidata QID, a Numista N-number) are what prevent namespace
collisions between them. This is the positive boundary; the
extraction-time non-entity gate below is the negative one.

Particles reference subjects via their `subject_ids` field (§6.2).
The cardinality of `subject_ids` is meaningful:

| `len(subject_ids)` | Semantic role |
|---|---|
| 0 | Discouraged. A CLAIM particle SHOULD be about at least one subject; a zero-subject claim is unreachable by subject-filtered query and subject-graph traversal, and lint flags it (`NO_SUBJECT`, L-STR-09). Zero is legitimate where no subject applies or none could be resolved: non-CLAIM particle types (REVIEW audit records carry no subjects by design), DOCUMENT_META claims (scoped to the document, not a subject), non-asserted claims (DECLINED / HYPOTHETICAL), claims whose subject the deployment deliberately withholds and which the extractor marks accordingly (`extraction:subject_scope = SELF`; today the author of a personal-journal entry, held behind the privacy gate), interchange units whose subject refs could not be resolved at import, and extractions where subject resolution produced nothing. Conformance places `subject_ids` in the **Required** tier (§14.5) at a 100 % floor, and applies it to exactly the particles this row says *should* carry a subject — the cases listed above are excluded from the measured denominator rather than counted as failures. One predicate serves both this exclusion and lint `L-STR-09`, so the two surfaces cannot answer the question differently. An extraction whose subject resolution simply produced nothing is **not** excluded: that is the gap both exist to surface. |
| 1 | The particle is a **property** of that subject (e.g. *"POET Technologies is headquartered in Toronto"* → property of `Q-POET`). |
| ≥ 2 | The particle is an **edge** in the subject graph (e.g. *"Acme acquired Widget"* → edge between `Q-Acme` and `Q-Widget`). |

### Subject resolution

When an extractor produces a particle, the subject resolver maps each
candidate subject name to a canonical `Subject` via the following
ladder:

1. **Local match.** Look up the candidate against the local Subject
   store's `canonical_name` and `aliases`. If found, reuse.
2. **External ontology lookup.** For supported ontologies (Wikidata
, Numista, Nomisma),
   resolve the candidate against the external API. If a high-
   confidence match is found, create a new local `Subject` with the
   external identifier recorded in `external_ids` and a link confidence
    computed from the cosine similarity between the
   ontology description and the particle content.
3. **Bare local.** If no external match is found, create a new local
   `Subject` with `canonical_name = candidate` and no `external_ids`.
   Future extraction of the same name will reuse this subject.

Per the Subject Authority Registry, the external-ontology
step is pluggable: each supported ontology is a registered
**Subject Authority** plugin (`particles/ingest/authorities/`)
declaring its namespace, lookup method, and match-scoring behaviour.
The ladder consults registered authorities in priority order; adding
support for a new external knowledge base is a plugin registration,
not a resolver change. The same registry backs external-ID lookup in
`particles subjects split --new-external-id` and federated
subject matching. The full design contract lives.

**Authorities MUST declare domain applicability.** A Subject
Authority carries the same RFC 2119 `ApplicabilityClause` list an
extractor does (§14.1) — `{keyword, domain_uri, domain_label,
source_types}` — and the resolver **filters candidate authorities by the
claim's derived domain** (the domain a source maps to via the §6.4 /
§14.1 mapping) before consulting them: a numismatics authority fires on a
coin-domain claim and is skipped on a physics claim, and a `MUST_NOT`
clause hard-excludes an authority from a domain exactly as it does for an
extractor. A **new authority MUST declare its domain applicability — no
unconditioned global recognizers.** This is the rule that keeps the
resolver ladder from degrading as authorities are added: every authority
scopes the claims it will attempt to recognise, so registering another one
adds precision without adding spurious cross-domain lookups. An authority
that is *deliberately* broad (the reference Wikidata authority is the
canonical case — a general-knowledge base with no domain restriction)
declares that breadth explicitly rather than by omission.

**Non-entity gate.** Before the ladder runs, candidate subject
names matching non-entity token classes SHOULD NOT be promoted to Subjects:
the producing implementation's own controlled vocabulary (enum / relation-kind
constants), reference and identifier codes (e.g. document IDs such as
`RFC 2119`), filenames, command-line strings, and code identifiers. A
`Subject` is a real-world entity (§6.7), and these tokens are artifacts of the
*source document* — its worked examples and self-referential apparatus — not
entities the document is about; example-rich and self-referential sources
otherwise pollute the subject graph with them. A candidate left with no
surviving subjects becomes a general (subjectless) claim. The exclusion is a
**precision-first** heuristic: an implementation MUST NOT suppress a name that
may denote a real-world entity, so ambiguous shapes (e.g. CamelCase product
names, lone common words) are deliberately left in. The reference SDK
implements this as a deterministic lexical classifier in the Client layer.

### Alias management

when the resolver produces multiple aliases that point
to the same canonical subject (e.g. *"POET Technologies"*, *"POET"*,
*"the company POET"*), the operator can consolidate them via the
review operation. Alias merges propagate to all particles' `subject_ids`
automatically; the merged subject's `aliases` list grows.

### Operator-correction surface

The operator-overridable identity contract (whitepaper §3.3) is
implemented through three CLI verbs that share the resolver path
with extraction-time Subject creation:

- **`particles subjects merge <source-id> <target-id>`** — combines
  two Subjects. Source's `canonical_name` and `aliases` become
  aliases on target; all `particle_subjects` rows pointing to source
  are re-pointed to target; source is deleted.
- **`particles subjects split <source-id> --particle <pid> […]
  (--new-name NAME | --new-external-id NS:ID) [--dry-run]`** —
  separates a misjoined Subject (v0.43.0). The resolver
  canonicalises the new Subject against the available external KBs
  the same way extraction does; `--new-external-id` is an
  authoritative override that pulls metadata directly from the
  identifier (sidestepping the search-then-take-top step that
  produced the wrong match in the first place). Multi-subject
  particles are partially moved (only the source binding migrates);
  the source Subject is preserved with its remaining particles
  even if every particle was moved off, for audit-trail continuity.
  New Subjects get `asserted_by = "subjects-split"`.
- **`particles subjects confirm <id> NAMESPACE:ID`** — pins an
  external-reference binding's confidence to 1.0 (treating it as
  operator-confirmed) and `particles subjects unlink <id>
  NAMESPACE:ID` drops a wrong external-reference binding.

All four verbs preserve particle confidence and content — they are
metadata corrections, not re-extractions.

### Subject-level lint

Two lint checks specifically target subject quality:

- `PHANTOM_SUBJECT` — a subject was created from an alias that has
  since been disambiguated as not-actually-an-entity (e.g. a common
  noun the LLM treated as a name).
- `WIKIDATA_LINK_MISMATCH` (L-SEM-03) — a particle's
  Wikidata link has low cosine similarity to the particle content,
  suggesting the wrong entity was matched. Surfaced as a WARNING.

## 6.8 Domain Extractors and `properties` / External References

Particles' centre of gravity is natural-language claim storage (§3.3
in the whitepaper). Some domain extractors, however, emit additional
structured data that maps cleanly onto a formal ontology — a coin's
denomination, year, mint, and catalogue number under the Nomisma
ontology, for example, or a Linked-Open-Data IRI for a
referenced concept. The schema accommodates this without
inflating Core.

### `properties: dict[str, object]`

Extension A field. Ontology-keyed structured data emitted by a
domain extractor when the source supports it. Keys are ontology IRIs
or short identifiers documented by the extractor; values are extractor-
defined types (typically primitives or short structured objects).

```yaml
# Example: a coin particle from the Numista extractor
content: "The 1924 Polish 1 grosz is denominated at 1 grosz."
subject_ids: [Q-Coin-Polish-1grosz-1924]
properties:
  "nmo:hasDenomination": { value: 1, currency: "grosz" }
  "nmo:hasManufactureDate": "1924"
  "nmo:hasObverse": "Eagle with crown"
extractor_ref: { name: "numista-coin-extractor", version: "0.2.0" }
```

Core operations (Query, Lint) do not interpret `properties`. The
field is preserved so domain tools — a numismatic catalogue browser,
a coin valuation engine — can consume the structured data without
re-parsing the natural-language `content`.

### Prefix registry

Property keys use a colon-separated `prefix:term` convention so
multi-extractor stores can disambiguate which extractor / ontology
contributed a given key (active in v0.31.0). Keys without
a `:` separator are accepted by the schema but surface a
`PROPERTIES_KEY_FORMAT` warning from the conformance validator (phase 1, report-only). Registered prefixes:

| Prefix | Status | Source | Coverage |
|---|---|---|---|
| `nmo:` | ACTIVE | Nomisma ontology | Numista coin metadata (denomination, material, dates, descriptions). |
| `nuds:` | ACTIVE | Numismatic Description Standard | Numista fields NUDS covers that the core Nomisma ontology does not (`nuds:references`, `nuds:demonetizationDate`). |
| `skos:` | ACTIVE | SKOS concept vocabulary | Nomisma concept metadata (`skos:definition`, `skos:exactMatch`, `skos:closeMatch`). |
| `geo:` | ACTIVE | WGS84 geo positioning | Nomisma mint coordinates (`geo:lat`, `geo:long`). |
| `numista:` | ACTIVE | Numista-specific | Catalog-only fields without a Nomisma equivalent (catalog refs, URL). |
| `mastodon:` | ACTIVE | Mastodon API | Per-status metadata (boost flags, account acct, reblogged status URI). |
| `social:` | ACTIVE | Cross-platform social | Generic dual-emission slot for social-network signals shared across platforms (`social:hasScore`, etc.). |
| `thread:` | ACTIVE | Threaded discussions | Reply structure (`thread:parentId`, `thread:depth`). |
| `content:` | ACTIVE | Content-shape metadata | URL referenced by the content, content language, etc. **Not publishable in `context.jsonld`** — see the collision note below. |
| `hn:` | ACTIVE | Hacker News API | Per-item metadata (`hn:hasPoints`, `hn:type`). |
| `extraction:` | ACTIVE | Engine-assigned annotation axes | Classifications the extraction layer computes about a claim at mint time (`extraction:source_modality`, `extraction:scope`, `extraction:polarity`). |
| `schema:` | RESERVED | schema.org | Reserved; not yet emitted. |
| `dc:` | RESERVED | Dublin Core | Reserved; not yet emitted. |
| `wdt:` | RESERVED | Wikidata property statements | Reserved; not yet emitted. |

**Prefix selection ladder.** When a producer needs a prefix
for a new key, it walks the ladder top-down and uses the first
applicable rung:

1. **Published ontology** — if the concept maps cleanly to a published
   ontology (Nomisma `nmo:`, schema.org, Dublin Core, Wikidata), use
   its conventional prefix.
2. **Source-platform prefix** — for platform-specific concepts no
   published ontology covers, a short lowercase prefix matching the
   source platform (`hn:`, `mastodon:`, `reddit:`, `github:`),
   registered when the platform extractor lands.
3. **Cross-platform prefix** — for concepts spanning platforms
   (`social:`, `content:`, `thread:`). A new cross-platform prefix is
   minted only when two or more source-platform prefixes carry the
   same concept under different names, and **MUST NOT collide with an
   existing term in `artifacts/schemas/context.jsonld`** (see the
   collision note below).
4. **`extraction:`** — for a signal the extraction layer **computes
   about** a claim at mint time, never for one it **reads from** a
   source (rungs 1–3 own sourced data).

Producers **SHOULD** emit cross-platform keys (`social:hasScore`) in
addition to any platform-specific equivalent they also emit (Hacker
News's score is both `hn:hasPoints` and `social:hasScore`); consumers
SHOULD prefer the cross-platform key for generic views. Dual-emission
keys are permitted; the registry exists to ensure each emitter names
its slots consistently rather than to enforce single-key-per-fact
discipline. **Registering a new prefix is a pull request against the
standard repository that amends this registry table** — adding the row
(prefix, status, source, coverage). Public registration keeps the
namespace collision-free without a central gatekeeper: the table in
this section is the authoritative list, and the PR that adds a row is
the registration act.

**Registry vs published context.** This registry governs `properties`
**keys**; `artifacts/schemas/context.jsonld` governs which CURIEs are
expandable, and it is the superset — the context additionally carries
namespaces that never appear as a `properties` key (entity-IRI
namespaces such as `wd:` and `nm:`, and the RDF plumbing vocabularies).
One registered prefix is deliberately **not** in the context:
`content:` — a JSON-LD term has exactly one definition and `content`
is already bound to the particle's `content` field, so publishing the
prefix would corrupt expansion. `content:`-prefixed keys therefore do
not expand to IRIs; this is harmless because `properties` is an opaque
`@json` payload that no conforming code path expands, but it is why
rung 3 of the ladder carries the no-collision constraint.

### External references — `ExternalRef` on the Subject record

Linked-Open-Data references live on the **`Subject` record** (§6.7),
not on the particle. An external ontology entity (a Wikidata Q-ID, a
Nomisma IRI, a Numista catalogue number) identifies a real-world
*entity*, and the Subject is the schema's canonical-entity record —
so that is where the link belongs. (An earlier draft of this spec
carried `external_refs` as a particle field; the implementation and
the normative artifacts resolved it to `Subject.external_ids`, and
the JSON Schema's `$defs/Subject` is the binding shape.)

```yaml
Subject.external_ids:
  - namespace: "wikidata"
    id: "Q49757"
    uri: "http://www.wikidata.org/entity/Q49757"
    confidence: 0.78
  - namespace: "nomisma"
    id: "grosz"
    uri: "http://nomisma.org/id/grosz"
    confidence: 0.94
```

`confidence` is the *link confidence* — how strongly the external
entity is the right match for the Subject. A value of
1.0 means the link was asserted by a structured extractor or pinned
by `particles subjects confirm`; values below 1.0 are scored from
the cosine similarity between the external entity's ontology
description and the particle content that introduced the Subject.
Operators can suppress low-confidence links from rendered outputs
via a configurable threshold.

Domain extractors participate by emitting *candidate* external
references alongside each candidate particle; the subject resolver
(§6.7) attaches them to the resolved Subject's `external_ids` via
the registered Subject Authorities.

| **EXTENSION SCOPE** |
| --- |
| `properties` is part of **Extension A** (Extractor Registry). A Core-only implementation MUST preserve the field when present (do not strip it on serialisation) but is not required to populate or consume it. `external_ids` is part of the Core Subject record but is never required to be non-empty (the bare-local resolution rung in §6.7 creates Subjects without external links). The Reference SDK ships extractors that populate both surfaces (Numista, Nomisma, Wikidata) as evidence the architecture supports it. |

## 6.9 Trust-Weighted Confidence Merging

Effective confidence is computed at query time as the product of
several modulating factors (§6.3). When multiple particles assert
the same underlying claim — either via Extension A's multi-extractor
fan-out, or via a co-evidential group (§6.10) — the engine merges
their effective confidences into a single rendered value. This
section defines the merge.

### Per-particle effective confidence

```
effective_confidence(p) = p.confidence.value
                        × extractor.trust_weight(p.extractor_ref)
                        × source_trust_rank(p.provenance)
                        × recency_factor(p.provenance.snapshot.content_published_at, source_type)
```

All four factors are in [0, 1]; the product is monotone and bounded
by `confidence.value`. (multiplicative decay).
`source_trust_rank` defaults to 1.0 in the absence of any applicable
trust policy — an operator's asserted rank applies unchanged, but the
engine MUST NOT substitute a synthetic no-information baseline (such as
the §6.6 conflict ladder's 0.50 differential baseline) into the
product; silence about a source is neutral, not distrust.

Effective confidence is always computed at read time, never stored
, and is therefore evaluated **at the reference instant**:
present-time queries use now, and an as-of query (§9.3)
computes the recency factor at the requested instant T while trust
weights remain the viewer's current policy.

### Merging across a group

For a group of particles G (all asserting the same claim, either
from independent extractors of the same source or from a co-evidential
link spanning multiple sources), the merged confidence is **not** a
simple max or average. The standard uses a *noisy-OR with trust-
weighted weights*, which gives weakly-corroborating sources additive
lift while preventing single-source dominance:

```
merged(G) = 1 - product over p in G of (1 - effective_confidence(p) * source_independence(p))
```

`source_independence(p)` is 1.0 for the first particle from a given
source and `1 / k` for the k-th particle from the same source within
the group — preventing a single chatty source from saturating the
merge. Implementations MAY use simpler max-based merging during
prototyping but MUST adopt the noisy-OR form before claiming
trust-weighted merge conformance.

### Where the merge runs

- **Query (§9.3).** Applied during the co-evidential collapse step.
  The merge result is rendered as the single citation's confidence
  in the synthesised response.
- **Wiki article exporter (§10.4).** Same as Query: footnote-collapse
  over a co-evidential group renders one merged confidence in the
  article body; individual particle confidences remain visible in
  the references section.
- **Lint (§9.4).** The `EXTRACTION_QUALITY_REPORT` check reports
  both per-particle and merged confidences for groups.
- **Storage.** Never stored. The merge is recomputed per operation;
  changes to source trust statements (§6.4) or extractor trust
  weights (§14.4) take effect on the next query.

| **MERGE PRECEDENCE** |
| --- |
| When a particle is in both an Extension A multi-extractor pool and a §6.10 co-evidential group, the merge is computed once over the full union; nested merging is incorrect. The cascade in §6.4 evaluates the merged group as a single unit when comparing against another conflicting group. |

### Per-claim contestedness (lens-divergence)

A claim's **contestedness** is a derived, read-time-only quantity (a
sibling of `effective_confidence`): the **spread — max − min —
of the claim's `effective_confidence` evaluated separately under each
policy in the viewer's policy set.**

**The policy set** is viewer-relative: (1) the store's **local** policy
(its own trust statements, URL rules, and extractor-weight overrides,
with **no lens overlay**) — a member even when empty; plus (2) **each
adopted lens, standalone** — its portable layers only, no local overlay
and no cross-lens min. Each member is a complete standalone policy
evaluated in full (source trust rank, URL rules, *and* extractor-weight
overrides). This deliberately differs from the single composed policy
ranking uses (§6.4 — local-wins, min-across-lenses):
composition would collapse the very spread being measured.

**The statistic** is the range, not variance/stdev: the set is a
complete, small population (typically 2–5 policies) whose extremes are
*nameable policies* (the surfacing attributes "local: 0.43;
acme-numismatics: 0.81"), and the thesis it measures — "invariant across
every credible trust policy" — is a sup-norm claim, not an
average-deviation one. `effective_confidence ∈ [0, 1]`, so the range is
already normalized.

**Per co-evidential group:** for each policy, apply the §6.9 noisy-OR
merge over the group first, then take the spread of the per-policy merged
values.

**Normative:**

- Contestedness **MUST NOT** feed `effective_confidence`, ranking,
  `min_confidence` filtering, or §6.6 conflict resolution. It is
  **disclosure, not discount** — a contested claim is not a
  less-confident claim.
- It **MUST** be computed at read time and **never stored** (the same
  rule as `effective_confidence`; substrate-plus-lens).
- With **fewer than two policies** in the set the metric **MUST be
  absent** (omitted / null), never `0.0` — absence of measurement is not
  measured invariance, and a one-policy store must not mint fact-like
  badges. Because the local policy is always a member, the metric lights
  up at the first lens adoption.

In the contestedness metric only source trust and extractor weights vary
per policy; calibrated confidence is policy-invariant, and although the
**recency factor** is made per-observer (a lens may carry `decay_rules`),
the contestedness metric still evaluates it from the *composed* decay policy
(i.e. policy-invariant for the spread) — folding per-policy decay divergence
into the metric is deferred.
Lens-divergence (this section) and the §6.10 stance distribution
 are the two instruments of one concept — *this claim is
contested* — one measuring rendered-confidence divergence (viewer-side),
the other declared positions (substrate-side).

### The composed contested badge

The read surfaces compose the contest signals into **one badge**: a
claim renders *contested* iff at least one of three named bases fires,
and the badge is a **basis-carrying disjunction** — a non-empty set of
fired basis labels, never a blended scalar:

| Basis | Gate |
|---|---|
| `stance` | the claim's query-time stance distribution (§6.10, over its CO_EVIDENTIAL group, dangling edges excluded) contains ≥ 1 `DISPUTES` position; endorsements alone never fire |
| `divergence` | the lens-divergence spread (this section) ≥ the same threshold that gates the prose callout — one threshold, one meaning |
| `inconsistency` | an open INCONSISTENCY particle references the claim (the §9.3 recall marker, subsumed as a basis) |

**Normative (§§1–4):**

- The badge **MUST** carry its fired bases wherever it renders; a bare
  "contested" with no basis is non-conforming. When the `stance` basis
  fires, the §6.10 unverified-holder caveat **MUST** accompany the
  badge.
- A basis that cannot be measured is **absent from the composition**,
  not a non-firing vote (divergence below two policies is absent, per
  this section's absence rule); a claim with no available basis fired
  carries **no badge** — never an explicit "uncontested" assertion.
- The badge inherits the invariants above: **MUST NOT** feed
  `effective_confidence`, ranking, `min_confidence` filtering, or §6.6
  conflict resolution; **MUST** be computed at read time and never
  stored. The per-basis quantities (distribution, readings, the
  INCONSISTENCY reference) remain the drill-down; the badge does not
  duplicate them.

## 6.10 Claim Identity and the Relation Graph

Particles can be linked to each other via typed relations stored in
`particle_relations`. The registry is a **closed enum** (
active in v0.37.0) — extractors and lint checks MUST NOT emit kinds
outside the registry, and renames or removals require a major-version
bump.

### Relation kinds

| Kind | Symmetry | Status | Meaning |
|---|---|---|---|
| `CO_EVIDENTIAL` | symmetric | ACTIVE | Two particles assert the same underlying claim from different sources; group-merged for trust-weighted confidence (§6.9). |
| `PART_OF` | asymmetric | ACTIVE | `particle_a` is a constituent of the `NARRATIVE` particle `particle_b` (child → parent); the membership edge of a narrative. |
| `SEQUENCE_IN` | asymmetric | ACTIVE | Within a narrative, `particle_a` immediately precedes `particle_b` (predecessor → successor); the linear-ordering edge of a narrative. |
| `ENDORSES` | asymmetric | ACTIVE | `particle_a` (a *stance* particle) asserts its holder's agreement with target `particle_b` (stance → target); the role marker of an endorsement stance. |
| `DISPUTES` | asymmetric | ACTIVE | `particle_a` (a *stance* particle) asserts its holder's disagreement with target `particle_b` (stance → target); the role marker of a dispute stance. |
| `CONTRADICTS` | symmetric | RESERVED | Two particles make incompatible claims about the same subject(s). Once activated, the lint workflow routes pairs into operator review. |
| `BOOSTS` | asymmetric | RESERVED | Endorse / amplify another particle (social-network repost semantics; the Mastodon extractor currently captures the reblog data as properties pending the activation ADR). |
| `QUOTES` | asymmetric | RESERVED | Paraphrase or restate another particle with attribution. |
| `REPLIES_TO` | asymmetric | RESERVED | Respond to another particle in a conversational thread. |
| `MENTIONS` | asymmetric | RESERVED | Reference another particle's subject(s) without making a claim about it. |

Symmetric vs asymmetric is the **storage-invariant axis**: symmetric
kinds canonicalise to `(min(a, b), max(a, b))` on write so duplicate
insertions collide at the unique constraint; asymmetric kinds preserve
direction because direction carries semantic information.

RESERVED kinds activate via per-kind ADRs that specify the emitter,
the consumer surface (query filter, CLI parser, lint integration),
and the symmetry-table entry — landing all three in one commit. The
namespace is reserved at 1.0 so a future Bluesky `BOOSTS` edge will
have the same shape and downstream semantics as a Mastodon `BOOSTS`
edge.

### `particle_relations` schema

```yaml
ParticleRelation:
  particle_a: string (particle UUID)
  particle_b: string (particle UUID)
  relation_type: enum               # see Relation kinds table above
  created_by: enum                  # AUTO_CLUSTER_v1 | HUMAN_REVIEW | EXTRACTOR_DIRECT
                                    #   | MANUAL_CLI | LLM_JUDGE | EXACT_DUPLICATE
  created_at: ISO 8601
  confidence: float [0, 1]          # how confident the link is
```

For symmetric kinds the ORM layer enforces `particle_a < particle_b`
on write so the same logical edge can only be stored once.

The relation is symmetric and transitive *in the in-memory
representation* but persisted only as pairwise edges (the transitive
closure is computed at query time, not stored). Storage cost is
O(group_size²) per group in the worst case, but real groups are
small (typically 2–5 members).

### Claim Identity — Co-Evidential as the active case

Each source's claim is its own particle: source-faithfulness is
preserved (§3.1 of the whitepaper). When two or more particles assert
the same underlying claim — *"Acme acquired Widget"* extracted from
five different news articles — they are linked by a `CO_EVIDENTIAL`
relation that lets downstream operations treat the group as a single
claim with multiple corroborating sources, without collapsing the
originals.

The mechanism is recorded (active in v0.17.0). The
decision weighed three options (deterministic semantic hashing,
query-time clustering, explicit co-evidential link); option (c),
explicit link, is the standard's approach.

### Re-observation is not a second claim

Source-faithfulness makes each *source's* claim its own particle. It does
not make each *observation* of one claim a new particle: re-reading a
source that still says what it said before is corroboration, not a second
belief. Where co-evidential links relate two particles that already exist,
this rule governs whether the second particle is created at all.

**Normative.** When a creation path (§9.2 Extract, or any write path that
reconciles through §6.6) produces a candidate whose

* normalized `content` — whitespace runs collapsed and sentence-final
  punctuation trimmed; case and wording preserved,
* resolved subject-id set, and
* `stance:holder` (§6.10)

are all equal to those of an existing `ACTIVE`, truth-apt,
asserted particle, implementations **SHOULD** suppress the
candidate rather than write it, and — when they do — **MUST** record the
candidate's provenance ref on the surviving particle. Dropping the
observation is a source-faithfulness violation: the second source's
evidence has to land somewhere.

Four constraints bind the suppression:

1. **Identity, never similarity.** The predicate **MUST** be exact
   (normalized) content equality. Implementations **MUST NOT** use an
   embedding-similarity threshold for this rung: below exact identity,
   cosine does not order duplicate-likelihood (measurement found
   a one-token false positive at 0.9951 and an outright contradiction at
   0.9272). Near-duplicates remain a matter for review, not for automatic
   collapse.
2. **The decay anchor does not move.** The recorded ref is *appended*; the
   earliest ref remains the one §6.3 recency decays against. Re-observing a
   claim **MUST NOT** silently refresh its age.
3. **`confidence.value` is unchanged** (§6.3). Corroboration raises
   certainty only through the query-time co-evidential merge (§6.9), and a
   suppressed candidate creates no group — so a suppressed re-observation
   does not raise confidence. This is a deliberate consequence, not an
   oversight.
4. **Identity, not authorship, is preserved.** `asserted_at` and
   `asserted_by` continue to record the first minting of the claim.

Suppression **MUST** be disclosed to the operator (a count in the
operation's result or quality notes); a pass that recognises forty
already-known claims must not be indistinguishable from one that found
nothing.

### Endorsement stances and the agreement distribution

A **stance** is an ordinary `FALSIFIABLE` particle asserting an attribution
fact — *"agent A endorses / disputes claim B"* — bound to its target by an
outbound `ENDORSES` / `DISPUTES` edge. The edge **is** the role marker: there
is no `STANCE` particle type. Two `stance:`-prefixed `properties` keys (the convention) carry the attribution: `stance:holder` (the holder's
`platform:identifier`, the same namespace as `SourceRef(type=AUTHOR)`) and the
optional `stance:magnitude` (a float [0, 1] strength; absent ⇒ unqualified).
The stance's own `confidence.value` means *how sure we are the holder holds the
attitude* — calibrated like any claim — distinct from the magnitude.

**Agreement is a query-time distribution, never confidence.** For a target
claim, the engine computes — at query time, stored nowhere (substrate-plus-lens) — the **stance distribution** over the `ENDORSES` / `DISPUTES` edges
into the target's `CO_EVIDENTIAL` group: the holders of each position, each with
citation, the stance particle's own effective confidence, and magnitude.
**Normative:** stance data and agreement aggregation **MUST NOT**
feed any term of `effective_confidence` (§6.9) — agreement is surfaced
*alongside* confidence, never multiplied into it — and the distribution **MUST
NOT** be stored as canonical truth (evictable materialized views are permitted).
Holders are grouped by the raw, unverified `stance:holder` key: a count of keys,
not of verified agents, and the rendered distribution carries that caveat.

**Engine treatment.** A stance never contradicts its target, and opposing
stances by *different* holders never contradict each other (disagreement is not
inconsistency); a stance is therefore excluded from §6.6 conflict candidacy
except against a *same-holder* stance (a same-holder reversal). Stance particles
are kept out of the factual query top-k (the role marker is the outbound edge),
and two stances are co-evidential only when they share the same `stance:holder`.
On target retraction the stance edge is preserved as a *dangling* edge rather
than hard-deleted, so a retracted target does not silently drop the holder from
the distribution.

### Graded, observer-relative equivalence

*"Are these the same claim"* is **never a stored boolean truth**.
Claim equivalence is graded and observer-relative — a
sibling of `effective_confidence`, computed at query time over an
observer-neutral substrate. The substrate is the `CO_EVIDENTIAL`
edge's `confidence` within a store; where no edge can exist (the
cross-store federation case — relations are store-local), the
substrate is computed at query time from embedding similarity. The
lens — `effective_equivalence(observer, pair)` — is never stored;
in the current SDK it is the identity function with a reserved
per-observer hook. Co-evidential collapse (§9.3 step 6) gates a pair
into the same group on `effective_equivalence ≥ θ`, where the default
threshold reproduces the prior binary behaviour; below θ both
particles surface as separate ranked results. The full design
contract — including cross-language equivalence as a
substrate-production concern — lives.

### Creation paths

1. **Extraction time.** A domain extractor that processes a source
   which itself aggregates multiple sources (a Wikipedia article
   citing five news reports) MAY emit `CO_EVIDENTIAL` links between
   the particles it creates. `created_by = EXTRACTOR_DIRECT`.
2. **Links-suggest curation operation.** The
   `links suggest` operation finds candidate near-duplicates within a
   Subject (cosine similarity above a configurable threshold; the
   conformance profile pins the reference `candidate_threshold`) and
   proposes links for review. Candidate proposal is deliberately
   **not** a lint check — lint is a pure diagnostic (§9.4) and emits
   no `CO_EVIDENTIAL_CANDIDATE` findings. The operation has three
   modes: **report** (default — list pairs above threshold; no LLM
   call, no mutation), **LLM-judge** (per-Subject candidate clusters
   are batched into a judge call returning a per-pair
   `PARAPHRASE` / `DISTINCT` / `UNSURE` verdict; no mutation), and
   **apply** (implies LLM-judge; links `PARAPHRASE` pairs with
   `created_by = LLM_JUDGE`; verdicts other than `PARAPHRASE` are
   reported but never auto-applied, and an implementation SHOULD
   require explicit confirmation above a configurable pair-count
   cap). Operator-accepted candidates are `created_by = HUMAN_REVIEW`.
3. **Manual.** CLI: `particles links add p:abc p:def --type co-evidential`.
4. **Exact-duplicate auto-merge** (widened). ACTIVE
   truth-apt particles whose `content` strings are **identical under the
   §6.10 normalized key** (whitespace runs collapsed, sentence-final
   punctuation trimmed, case and wording preserved) are one claim by
   construction; an implementation MAY elect a survivor
   deterministically, link it to each redundant copy with `created_by =
   EXACT_DUPLICATE`, and transition those copies to `SUPERSEDED` with
   `status_reason = DUPLICATE_MERGED`. Normatively: the predicate is exact
   (normalized) content equality — **never** an embedding-similarity
   threshold, which does not order duplicate-likelihood below identity — the
   survivor is never mutated, and no particle is ever deleted. The merge is
   therefore append-only and exactly revertible from its audit record.

   The key is **the same one §6.10 suppression uses**, and this is normative:
   an implementation whose cleanup pass keyed on raw bytes while its
   prevention rung normalized would make prevention strictly wider than
   cleanup — a pair differing only by a trailing period could never be minted
   twice, yet an already-minted such pair would be permanently unreachable,
   and the pass would report "0 groups" over a store that still holds them.

   **Subject scoping is an election preference, not a membership gate**
   . Copies sharing a Subject form one group; copies carrying **no**
   Subject are grouped too, joining the group's subject-linked members when the
   byte-identical bucket offers exactly one such group and forming their own
   otherwise. Copies whose Subjects *disagree* are never one group. The
   survivor election is therefore `(subject-linked before subject-less,
   earliest asserted_at, smallest id)` — an implementation MUST NOT elect a
   subject-less survivor over a subject-linked copy of the same content, since
   that would drop the claim out of subject-filtered query (§6.7) even though
   an indexed copy of it existed.

### Effects on Core operations

- **Query (§9.3).** After top-k retrieval, group particles linked
  `CO_EVIDENTIAL`. Render one representative per group in the
  synthesised response; cite all group members in the footnotes.
  Confidence shown is the merged value from §6.9.
- **Wiki article exporter (§10.4).** Same collapse — one sentence,
  multiple footnotes. All corroborating sources appear in the
  References section.
- **Lint (§9.4).** The semantic-contradiction check (`L-SEM-01`)
  skips pairs already linked `CO_EVIDENTIAL`. Candidate links not
  yet established are surfaced by the links-suggest curation
  operation (creation path 2), not by lint.
- **Status transitions (§6.6).** When a particle in a co-evidential
  group is `RETRACTED`, the group survives and the retracted
  particle leaves. The group is dissolved only when it falls to a
  single member.

### Scope and constraints

- Co-evidential links are scoped within at-least-one-shared-Subject.
  Cross-Subject claim identity is out of scope (see Subject aliasing, which handles the related entity-resolution case).
- Two particles from the *same* extraction call are not auto-linked.
  The source did not corroborate itself; the particles' shared
  provenance already encodes that.
- The standard does not store a `CONTRADICTS` relation type yet.
  Contradiction is surfaced as `INCONSISTENCY` particles (§6.6).
  Whether to also persist contradiction as a link is deferred — see
  Deferred section.

| **CO-EVIDENTIAL GROUPS AND TRUST** |
| --- |
| Trust-weighted confidence merging (§6.9) operates *over the co-evidential group as a whole*, with `source_independence` discounting multiple particles from the same source. This prevents a single chatty source from artificially inflating apparent corroboration. The cascade in §6.4 also evaluates co-evidential groups as single units. |

> §6 v2 ends here. §6.11 (Benchmark Suite Interface) from v1 has
> moved to §13.3 per the Phase 2 outline decision.

# 7. The Source Corpus

## 7.1 Overview and Two-Layer Architecture

The Source Corpus is the foundational layer of the Particles architecture. It is an append-only archive of all materials from which particles have been or may be extracted. The particle store is a derived view over the corpus; the corpus is the system of record.

This separation resolves the primary failure mode of single-stage ingest pipelines: once a source has been transformed into particles, the original is no longer accessible for re-extraction. With the corpus as a first-class component, extraction becomes a re-runnable derivation rather than a destructive transformation. Failed, incomplete, or outdated extractions can be corrected without data loss. (.)

```
Source Corpus      (append-only event log — the ground truth)
       │
       │  [Extract: async, incremental, re-runnable]
       │
       v
Particle Store     (derived DAG — a view over the corpus)
       │
       │  [Query / Lint / Multi-agent exchange]
       │
       v
Agent context / natural-language response
```

Ingest is split into two operations with very different cost profiles:

- **Deposit (§9.1)**: write a source to the corpus. Requires no extraction, no schema, no structure. Cost is near-zero. A file, URL, transcript, or data export is deposited with a timestamp and source tag.
- **Extract (§9.2)**: derive particles from a corpus entry or snapshot. Runs asynchronously, incrementally, and can be re-run as extractors improve. Triggered lazily when a corpus entry is referenced by a query, or eagerly by `particles extract`.

| **ARCHITECTURAL PRINCIPLE** |
| --- |
| The corpus is always preserved. The particle store is always rebuildable from the corpus. No information that enters the corpus is ever lost due to extraction error. |

## 7.2 Corpus Entry and Snapshot Schema

A `CorpusEntry` is the stable record of a source and its relationship to its origin. Each entry has one or more `Snapshot`s — timestamped, content-addressed captures of the source at a point in time.

```yaml
CorpusEntry:
  entry_id: string (UUID)        # stable internal handle
  uri_r: string?                 # origin URI — Memento URI-R
  source_type: string            # OPEN string set (not a closed enum); see the
                                 # registry of well-known values below —
                                 # WEB_PAGE, PDF, CSV, CONVERSATION, DATA_EXPORT,
                                 # LOCAL_FILE, REDDIT_POST, GITHUB_GIST,
                                 # NUMISTA_API_COIN, WIKIDATA_API, ...
  mutability: enum               # APPEND_ONLY | MUTABLE | STABLE | EPHEMERAL
  fetch_policy: enum             # LAZY | NEVER
  created_at: ISO 8601
  deposited_by: string           # agent ID
  tags: string[]                 # operator-assigned filtering tags
  snapshots: Snapshot[]          # ordered by captured_at

Snapshot:
  snapshot_id: string (UUID)
  captured_at: ISO 8601          # when this snapshot was fetched / written
  content_published_at: ISO 8601?  # when the SOURCE published the content
                                   # (drives content age decay, §6.3)
  content_hash: string           # SHA-256 of raw content body
  etag: string?                  # HTTP ETag if available
  last_modified: ISO 8601?       # HTTP Last-Modified if available
  warc_record_type: enum         # RESPONSE | REVISIT
  archive_path: string?          # local path; null for REVISIT records
  refers_to: snapshot_id?        # WARC-Refers-To for REVISIT records
  extraction_status: enum        # PENDING | IN_PROGRESS | COMPLETE | FAILED
  extraction_started_at: ISO 8601?  # when extraction last claimed this
                                    # snapshot (0.42.2); cleared on transition
                                    # away from IN_PROGRESS. Lets
                                    # `extract --all-pending` reset
                                    # rows stranded by SIGKILL whose
                                    # try/except cleanup didn't run.
  author_id: string?             # author identity within the source (§6.5)
                                 # format: '{platform}:{identifier}'
  author_role: string?           # author role metadata, if available (§6.5)
```

`captured_at` is *when the importer fetched the content*; `content_published_at` is *when the source originally published it* (e.g. a Reddit comment's `created_utc`). The two diverge for UGC sources where retroactive deposit is common. Only `content_published_at` drives the content age decay factor (§6.3); `captured_at` drives the Lazy Fetch revisit cadence (§7.5).

| **`source_type` IS AN OPEN STRING SET, NOT A CLOSED ENUM** |
| --- |
| `source_type` is a **string**, not a fixed enumeration. The standard publishes a **registry of well-known values** — `WEB_PAGE`, `PDF`, `CSV`, `CONVERSATION`, `DATA_EXPORT`, `LOCAL_FILE`, plus the importer-specific values the reference SDK mints (`REDDIT_POST`, `HACKERNEWS_THREAD`, `MASTODON_THREAD`, `GITHUB_REPO` / `GITHUB_GIST` / `GITHUB_PAGES`, `WIKIDATA_API`, `NOMISMA_API`, `NUMISTA_API_COIN` / `NUMISTA_API_ISSUER` / `NUMISTA_LISTING_HTML`, `RDF_GRAPH`, `JOURNAL`, …; §9.1, §14.4) — but a **new importer may mint a new `source_type` string**, and a corpus entry carrying an unregistered value is **conforming**. This is deliberate: `source_type` is the key trust statements are scoped against (§6.4) and the key domain applicability derives from (§14.1), and forcing every new source format through a central enum revision would make the extensibility the extractor/importer registries exist to provide impossible. Consumers MUST treat an unrecognised `source_type` as an opaque, well-formed value (route it to the general extractor, apply no source-type-specific policy), never as an error. |

The `ProvenanceRef` in the particle schema (§6.2) points into the corpus with snapshot-level precision and (when carry-forward is in use) chunk-level precision:

```yaml
ProvenanceRef:
  type: SOURCE | PARTICLE | AGENT
  corpus_entry_id: string (UUID)   # the stable entry
  snapshot_id: string (UUID)       # the specific snapshot extracted from
  chunk_hash: string?              # SHA-256 of the source chunk this particle
                                   # was extracted from
  location: string?                # byte range, paragraph number,
                                   # comment ID, etc.
```

`chunk_hash` is populated by the chunked-extraction pipeline and enables the reindex operation (§9.5) to skip chunks whose hashes are unchanged from the prior extraction.

The `type` field is the model-level (snake-case) name; the canonical wire / RDF predicate for it is **`refType`** (`particles:refType`) — the single name used consistently across the interchange codec, the JSON-LD `@context`, and the `ProvenanceChainShape` SHACL predicate. The shape constrains it to `SOURCE | PARTICLE | AGENT`.

### `corpus_follow_edges` schema

When an importer for a *link-shaped* source (Reddit / Hacker News /
Mastodon link cards) recognises its post format, the deposit
operation recursively deposits the URL the post primarily references
and records the relationship in `corpus_follow_edges`. The result
is that the substance of a discussion (the linked article) and the
curation envelope (the post that shared it) are both extracted as
their own particles, while the relationship between them is
machine-queryable.

```yaml
CorpusFollowEdge:
  via_entry_id: string (UUID)      # the envelope entry that linked
  target_entry_id: string (UUID)   # the entry it linked to
  link_type: enum                  # POST_LINK (active) | COMMENT_LINK (reserved)
  discovered_at: ISO 8601
```

Three normative properties:

1. **Depth-1 cap.** Followed entries do not themselves trigger
   further follows. The standard does not model multi-hop citation
   trees through the follow-edge mechanism — operators who want
   that depose additional sources explicitly.
2. **No foreign-key cascade.** The table has no FK constraints to
   `corpus_entries`; deleting either endpoint leaves a dangling
   edge. Operator-deliberate cleanup is a future concern.
3. **Shape-blind.** A Reddit post linking to another Reddit post
   is one hop, recorded identically to a Reddit post linking to a
   news article. Source-type filtering is a query-side concern.

Two further normative behaviours:

4. **Follow failure never fails the envelope deposit.** When the
   secondary fetch fails (paywall, 403, DNS, timeout), the primary
   deposit — the post envelope — is unaffected and its extraction
   still runs; the failure is logged and **no edge row is written**
   (there is no target to point at).
5. **Content-hash dedup still records the edge.** When the followed
   URL dedups by `content_hash` to an already-deposited entry, the
   edge row is written anyway, pointing at the existing entry —
   this is what preserves fan-in (the same article reached via
   Reddit, Hacker News, and several statuses accumulates one edge
   row per link source). Existing edge rows are never deleted or
   overwritten by a later dedup in either direction.

The follow edges are surfaced to operators via
`particles corpus links list [entry-id] [--direction {out,in,both}]`
(v0.42.5) — the first downstream consumer of the table. Without an
entry-id, lists every edge in deposit order; with one, shows
outgoing follows (this entry → linked) and / or incoming follows
(others → this entry). This is what makes the curation signal
queryable rather than just stored.

## 7.3 Shared Archive

A shared archive is a content-addressed mirror of corpus snapshots that multiple operators can read from. The same SHA-256 `content_hash` produced by one operator's deposit identifies the same content regardless of who fetched it, so a snapshot fetched once can be reused everywhere — reducing both bandwidth and the risk of source link rot (whitepaper Risk #6). (.)

The shared archive design is **content-addressed** and **distribution-agnostic**:

- The store key is the `content_hash` itself. There is no platform-specific identifier.
- The transport is unspecified at the standard level. Reference implementations may use BitTorrent magnet links, IPFS CIDs, S3-compatible object storage, an HTTP-fetchable directory, or any combination. The whitepaper §6 matrix presents this as *"content-addressed shared archive"* — that is the standard's commitment; the BitTorrent/IPFS specifics are reference-implementation choices.
- Per-snapshot rights metadata (ODRL — see §10.2) governs whether a snapshot may be redistributed via the shared archive. `EPHEMERAL` snapshots (§7.4) MUST NOT be shared.

The shared archive is an **Extension A** feature; Core implementations may operate entirely against local corpus storage. Cross-references:

- §14.2 — Shared Archiving for Public Sources (the Extension A spec for participating in a shared archive ecosystem).
- §6.4 — source trust statements apply equally to snapshots whose content was fetched from a shared archive vs. directly from the origin.

## 7.4 Mutability Classes

The `mutability` field drives extraction behavior when a new snapshot is created. Operators declare the nature of a source at deposit time; the system handles the consequences. (.)

| **Mutability** | **Semantics** | **Examples** | **Extraction behavior on new snapshot** |
| --- | --- | --- | --- |
| `APPEND_ONLY` | New content is additive. Prior content does not change. | Reddit threads, GitHub issues, email threads, forum posts | Extract particles only from the delta (new content since prior snapshot). Existing particles from prior snapshots remain `ACTIVE`. |
| `MUTABLE` | Content may change anywhere. Prior content may be revised or removed. | Wikipedia articles, documentation pages, news articles | Re-extract from the full new snapshot, **then** flag the particles still anchored to a prior snapshot as `PROVENANCE_STALE` — see the ordering note below. |
| `STABLE` | Content will not change after initial deposit. No re-fetch needed. | PDFs, published papers, exported CSVs, books | No re-fetch. Initial extraction is definitive. |
| `EPHEMERAL` | Content should not be archived. Origin reference only, or expiring archive. | Private conversations, sensitive personal data | No `archive_path`. Provenance reference is to `entry_id` only; snapshot content is not retained. May not be shared via the shared archive (§7.3). |

**Ordering of the `MUTABLE` demotion is normative**. The demotion runs **after** the new snapshot has been extracted, and it is scoped by *snapshot generation* rather than by semantic comparison:

1. Extract the new snapshot. Content-hash carry-forward (§9.2) keeps the particles whose source chunk is unchanged, which — because provenance is not mutated — leaves them pointing at the snapshot they were first extracted from.
2. Demote the entry's remaining `ACTIVE` particles whose provenance names a snapshot other than the newly-extracted one, excluding those carried forward, to `PROVENANCE_STALE`.

Demoting *before* extraction is non-conformant: carry-forward matches on `ACTIVE` particles, so a pre-demotion defeats it, re-extracts unchanged text, and produces duplicate particles for claims that never changed.

The demotion is deliberately **not** a semantic operation. The §6.4 conflict ladder compares individual claims and therefore cannot retire a claim the new version merely *deleted*, nor one that has been replaced by guidance that does not logically contradict it; only the document generation establishes which version is operative. Implementations MUST NOT substitute contradiction detection for this rule, and it requires no LLM.

| **EXTENSION F — PRIVACY AND CONSENT (DEFERRED)** |
| --- |
| The Core privacy primitives — `EPHEMERAL` mutability here in §7.4, ODRL rights metadata in §10.2, optional `author_id` and pseudonymisation in §6.5, and operator-controlled allowlists in §14.6 — give operators the building blocks for privacy-compliant deployments without prescribing a policy. A future **Extension F: Privacy and Consent** is reserved for normative privacy controls for regulated deployments (HIPAA / GDPR / CCPA), including mandatory `EPHEMERAL` handling rules for defined data categories, consent tracking as a first-class corpus entry field, deletion propagation through provenance chains, and audit-log expungement requirements. Extension F is deferred pending engagement with privacy and regulatory stakeholders; see Appendix A. Whitepaper §3.8 mentions Extension F as future work; this callout is the techspec's forward-reference. |

## 7.5 Lazy Fetch Protocol

Corpus entries with `fetch_policy = LAZY` are re-fetched when referenced by a query, subject to a minimum re-fetch interval. **Resolved** (was OQ-8 in v1): the re-fetch floor is *fixed*, operator-configurable per source type, not adaptive. Adaptive backoff is a deferred future feature (Appendix A). The shipped defaults:

| Source class | Default re-fetch floor |
|---|---|
| Web sources (HTML, news) | 1 hour |
| Data exports (CSV, JSON dumps) | 24 hours |
| Static documents (PDFs, archived papers) | 7 days |

All floors are tunable via `config.yaml`'s `refetch_floors` section. The fetch protocol follows a three-tier change detection hierarchy, over two transports — remote (HTTP) and local (`file://`):

1. **Tier 1 — Source signal (fast, advisory).** A signal obtained without reading the body. *Remote:* send `If-None-Match` (ETag) and `If-Modified-Since` (Last-Modified) HTTP headers from the prior snapshot; a `304 Not Modified` response creates a `REVISIT` snapshot with no content body, referencing the prior snapshot via `refers_to`. *Local:* compare the file's modification time against the prior snapshot's `last_modified`; if they are equal, no content is read and no snapshot is written. The local comparison is on **inequality, not recency** — a modification time that has moved *backwards* (a restore from backup, an archive extraction) MUST be treated as a possible change. Implementations MUST treat this tier as advisory for local sources: unlike a `304`, an unchanged modification time is an inference rather than an assertion by the source, so tier 3 remains the guarantee.
2. **Tier 2 — Content hashing (authoritative).** If the tier-1 signal is unavailable, untrusted, or indicates a possible change, read the full content body and compare its SHA-256 hash against the prior snapshot. If hashes match, create a `REVISIT` snapshot. If hashes differ, create a `RESPONSE` snapshot and trigger extraction according to the mutability class (§7.4). A `REVISIT` created here SHOULD record the tier-1 signal observed alongside the match (for a local source, the file's modification time), so the next check can short-circuit at tier 1. Change detection uses the same SHA-256 that identifies the snapshot; implementations MUST NOT substitute a non-cryptographic hash, because `content_hash` is also the content-addressed identity used by the shared archive (§7.3).
3. **Tier 3 — Manual override.** Operators may force re-fetch and re-extraction of any corpus entry at any time, regardless of `fetch_policy`, re-fetch interval, or tier-1 signal. CLI: `particles deposit <url> --force-refetch`; `particles corpus refresh --force` for local sources.

A local source that no longer exists or cannot be read yields no snapshot and MUST NOT, by that fact alone, cause its particles to be retracted or demoted: absence of a file is not falsification of the claims extracted from it.

| **MEMENTO ALIGNMENT** |
| --- |
| Corpus entries align with the Memento Protocol (RFC 7089). The entry's `uri_r` maps to a Memento URI-R (the original resource URI). Each snapshot maps to a URI-M (a memento — an archived version at a specific datetime). The ordered snapshot list constitutes a TimeMap. Implementations may optionally expose a Memento-compatible HTTP interface over the corpus to interoperate with existing web archival tooling. |

## 7.6 WARC and Memento Alignment — Extension D

Full WARC record type alignment (response/revisit) and Memento Protocol (RFC 7089) URI-R/URI-M/TimeMap integration are **Extension D** features. See §17. Core implementations use `content_hash` and `archive_path` directly without requiring WARC tooling interoperability.

# 8. Storage Model

## 8.1 Representation

A Particles deployment has two distinct storage subsystems:

- Source Corpus store: an append-only object store (local filesystem, S3-compatible, or content-addressed store). Corpus entry and snapshot metadata is stored in a relational or document database. Content bodies are stored as blobs addressed by content_hash.

- Particle store: a directed acyclic graph (DAG) where nodes are particles and edges are provenance relationships. Implementations may use any storage backend that supports the required query patterns; a property graph database (e.g., Neo4j, TigerGraph) or a document store with graph traversal support are the natural fits.

## 8.2 Required Query Patterns

All conformant implementations must support the following query patterns efficiently:

- Point query: retrieve particle by UUID — O(1)

- Semantic search: retrieve particles by content similarity — implementor-defined, O(log n) expected with vector index

- Provenance traversal: retrieve all particles in the provenance chain of a given particle — O(depth)

- Status filter: retrieve all ACTIVE particles, or all PROVENANCE_STALE particles — O(n) worst case, O(1) with status index

- Confidence filter: retrieve particles with confidence.value >= threshold — O(log n) with B-tree index on confidence

- Conflict detection: retrieve pairs of ACTIVE particles with overlapping provenance scope and conflicting content — O(n log n) with provenance index

- Corpus entry lookup: retrieve all particles derived from a given corpus entry or snapshot — O(k) where k is particle count for that entry

## 8.3 Corpus Storage Requirements

The source corpus must support:

- Append-only writes: no update or delete of deposited content

- Content-addressed retrieval: retrieve snapshot content by SHA-256 hash

- Entry and snapshot metadata queries: lookup by entry_id, uri_r, snapshot_id, captured_at range

- Extraction status tracking: update extraction_status on snapshots as extraction progresses

## 8.4 Scale Targets

Scale targets come in two tiers, and the distinction is **normative**:

- **Reference-SDK target (the conformance baseline).** What the reference SDK
  is built to meet and the floor a conformant implementation is expected to
  sustain. This is the column to design and test against today.
- **Architectural ceiling (informative, aspirational).** The scale the
  standard's data model is *intended* to reach with a production storage
  backend (a vector index in place of brute-force similarity, plus cached /
  columnar read projections). It is **not** a conformance requirement and is
  **not** met by the reference SDK, whose particle store loads and scans
  embeddings in process and is scoped to ≈10⁵ particles by design. Reaching
  it is tracked as future work and is explicitly post-1.0.

| **Parameter** | **Reference-SDK target (normative)** | **Architectural ceiling (informative)** |
| --- | --- | --- |
| Particle store size | Up to 10⁵ particles | 10⁷ particles |
| Corpus entry count | Up to 10⁴ entries | 10⁶ entries |
| Corpus storage | Up to 100 GB | 10 TB |
| Ingest throughput | 100 particles/second | 10,000 particles/second |
| Query latency (p95) | <500ms end-to-end including NL generation | <200ms end-to-end |
| Lint pass duration (10⁵ particles) | <60 seconds | <10 seconds |
| Provenance chain depth (max) | 20 hops | 100 hops |
| Fetch concurrency | 10 concurrent re-fetches | 1,000 concurrent re-fetches |

> Until the consensus-scale read path (vector index + per-viewer projections
> — future work) lands, conformance is measured against the reference-SDK column;
> the architectural-ceiling column is a design target, not a test gate.

## 8.5 Embedding and Similarity Contract

Many observable behaviours in this standard ride on the similarity between text
embeddings: query retrieval and ranking (§9.3), co-evidential grouping
(§6.10) and the confidence merge it feeds (§6.9), contradiction candidacy
(§9.2, §9.4 `L-SEM-01`), subject resolution against external authorities
(§6.7), and near-duplicate detection. For a standard whose value proposition is
cross-implementation epistemic interoperability, the similarity substrate cannot
be left implicit. This subsection pins what is portable and is explicit about
what is not. It is **normative**.

### Similarity metric and scale

Content similarity is **cosine similarity over L2-normalized embedding vectors,
clamped to `[0, 1]`** — a negative cosine MUST be clamped to `0`. This clamped
value is *the* similarity scale of the standard: **every similarity threshold in
this specification** (the §9.3 retrieval ranking, the co-evidential equivalence
threshold θ of §6.10, the §9.2 / §9.4 contradiction-candidacy gates, the §6.7
subject-resolution cutoffs) is expressed against this `[0, 1]` scale, and an
implementation MUST compute it the same way. The metric and scale are
**model-independent**: they remove the largest ambiguities a reimplementer faces
(raw-vs-normalized vectors, which metric, what range a threshold lives on)
without naming any particular encoder.

| **NEGATIVE-SIMILARITY CLAMP** |
| --- |
| The clamp affects only the `[-1, 0)` half of the raw cosine range — anti-correlated vectors. For the near-paraphrase text pairs the thresholds gate on, this region does not arise in practice, so clamping leaves every non-negative similarity (and therefore every threshold comparison expressed on the `[0, 1]` scale) unchanged. Its sole effect is to forbid an anti-correlated pair from sorting *below* an unrelated zero-similarity pair, which would otherwise corrupt ranking and candidate selection. |

### The recorded `embedding_profile`

An implementation MUST record, in its particle-store metadata, a structured
**`embedding_profile`** identifying the embedding space its stored vectors
occupy:

```jsonc
embedding_profile = {
  "model":         string,   // encoder identity, e.g. "all-MiniLM-L6-v2"
  "dim":           integer,  // output dimensionality, e.g. 384
  "normalization": string    // per-vector normalization, e.g. "l2"
}
```

The profile is a **structured object, not a free string**. Cosine similarity
across two different embedding spaces is meaningless, so a particle's stored
vector carries the `model` of the encoder that produced it (the reference SDK
persists this as the `embedding_model_id` marker; §6.6's stale-vector guard and
the Appendix C re-embedding rule build on it). **A profile change requires
re-embedding** every affected vector — comparing a vector from one profile
against a query embedded under another MUST NOT occur silently; an
implementation either re-embeds or excludes the mismatched vectors from
similarity search.

The standard does **not** mandate one specific encoder. Appendix C's guidance —
swap to a larger or cross-lingual model for production — is preserved: a swap is
simply a new declared profile. The reference profile published with this
standard is:

> **Reference profile:** `{ model: "all-MiniLM-L6-v2", dim: 384, normalization: "l2" }`

### Conformance: the frozen test-vector set

Similarity *behaviour* is made portable by a frozen, language-agnostic
**test-vector set** rather than by freezing an encoder. The set lives at
`artifacts/conformance/similarity_vectors.json` and contains text pairs each
annotated with an expected similarity **band** `[lo, hi]`, plus a small set of
`(query, corpus) → expected-top-k-membership` cases.

A backend is **profile-conformant** when, within a declared profile, each pair's
computed similarity lands inside its band (inclusive) and each top-k case's
expected members appear in the computed top-k. Expectations are stated as
**bands**, not as an `|Δ| ≤ ε` tolerance against a recorded float: a band is a
genuine cross-implementation contract that a *different* conformant encoder may
satisfy anywhere within, where an ε against one backend's output would not be.
The bands are authored to comfortably bracket the reference profile's scores
with margin on both sides. See `artifacts/conformance/README.md` for the file
format and the precise band semantics.

### What is normative, and what is implementation-defined

Conformance to similarity behaviour is asserted on two surfaces:

- **The deterministic, model-independent surface** — the schema, the §6.6 status
  machine, the §6.3 / §6.9 confidence math *given a fixed set of retrieved
  inputs*, serialization, and the deterministic lint checks. These reproduce
  exactly across conformant implementations.
- **Similarity behaviour within a declared profile that passes the test
  vectors** — the metric, the scale, and the bounded similarity scores above.

These two surfaces are the **L3 (profile-similarity)** and, together with the
§6.3/§6.9 math, **L2 (deterministic-compute)** tiers of the graded conformance
levels catalogued in the **Conformance Profile** (`docs/spec/conformance-profile.md`). The Profile is the normative home for the threshold table, the
similarity-vector reference, and the L1–L4 level definitions; `profile.yaml`
points at the same `artifacts/conformance/similarity_vectors.json` this section
mandates.

Two things are explicitly **implementation-defined (non-normative) across
profiles** and MUST be disclosed as such by any implementation that claims
conformance: (a) the exact **top-k ordering** returned by a query, and (b)
**borderline candidate selection** — which near-threshold pairs a profile admits
into co-evidential grouping or contradiction candidacy. Different profiles
legitimately rank and select differently at the margins; the test vectors bound
this drift but do not eliminate it. This is the same treatment §9.3 already
warrants for its natural-language synthesis: the confidence numbers become
reproducible *given the same retrieved inputs*, while *which* inputs are
retrieved is profile-relative, bounded by the test vectors, and disclosed.

# 9. Operations

Six operations make up the standard's runtime contract: **Deposit**, **Extract**, **Query**, **Lint**, **Reindex**, and **Review**. Each maps to a CLI subcommand and a `POST` API endpoint in the reference SDK. The two ingest operations (Deposit, Extract) are deliberately split — Deposit is cheap and structureless, Extract is asynchronous and re-runnable — so an operator can capture material faster than the extraction pipeline can process it without losing anything.

## 9.1 Deposit

Deposit writes a source to the corpus. It is intentionally trivial and carries no extraction cost. Any agent or operator can deposit at any time without schema knowledge.

### Importer plugin registry

An `ImporterRegistry` dispatches a deposit request to the appropriate importer plugin by matching the input URL or source descriptor against each registered importer's URL pattern. The dispatch is opaque to operators — `particles deposit <url>` works regardless of whether the URL is a GitHub gist, a Reddit thread, a Wikidata entity, or an arbitrary web page — but it is the documented Core conformance interface for source-format extensibility.

the plugin role formerly named `DepositorPlugin` is `ImporterPlugin`. The user-facing CLI verb `particles deposit` is unchanged: it describes the *operation* (writing into the corpus), independent of the plugin role that performs the fetch. The triplet `ImporterPlugin` / `ExtractorPlugin` / `ExporterPlugin` gives the SDK three complementary plugin roles with three distinct verbs.

The reference SDK ships six domain importers plus a generic-HTTP fallback. an analogous `ExporterRegistry` provides the symmetric output-side extensibility.

| **IMPORTER DISPATCH ≠ EXTRACTOR APPLICABILITY** |
| --- |
| The importer registry described here matches **URL patterns** to format-specific fetch logic (e.g. `gist.github.com/...` → `github-importer`). The *extractor* registry (§14.1) uses **RFC 2119 applicability clauses** over **claim domains** (e.g. *"biomedical literature"*, *"legal contract text"*) — a different mechanism operating on a different key. The two registries are independent: a single source can be imported by one URL-pattern importer and then processed by any extractor whose applicability matches the resulting `source_type` and claim domain. Do not conflate the two. |

| Importer | URL pattern (illustrative) | Notes |
|---|---|---|
| `github-importer` | `github.com/{owner}/{repo}`, `gist.github.com/...`, `{user}.github.io/...` | Three GitHub sub-types: REPO, GIST, PAGES. |
| `reddit-importer` | `reddit.com/r/{sub}/comments/...` | Curl-subprocess fetch to bypass Cloudflare TLS fingerprinting. |
| `numista-importer` | `numista.com/catalogue/pieces{id}.html`, REST API URLs | REST-API fetch. |
| `nomisma-importer` | `nomisma.org/id/...` | REST-API fetch. |
| `wikidata-importer` | `wikidata.org/wiki/Q{id}`, REST API URLs | REST-API fetch. |
| `generic-http` | any other `http(s)://` URL | Fallback. |

### Deposit algorithm

1. Receive source material (URL, file path, raw text, structured data, conversation transcript) and optional operator overrides.
2. The `ImporterRegistry` selects the most-specific matching importer; if none match, the generic-HTTP fallback is used. Operators may force an importer with `--importer <name>`.
3. Assign `entry_id` (UUID). If `uri_r` is provided, check for an existing corpus entry with matching `uri_r` — if found, add a snapshot to the existing entry rather than creating a new entry.
4. Detect `source_type` from the importer (e.g. `GITHUB_GIST`, `REDDIT_POST`, `NUMISTA`) or, for the generic-HTTP fallback, from content-type / file extension. Accept operator override.

| **RDF SOURCES ARE ONE SOURCE TYPE, NOT ONE PER SYNTAX** |
| --- |
| Turtle, N-Triples, TriG, N-Quads, JSON-LD and RDF/XML are serializations of a single data model, so a conforming implementation SHOULD detect them to **one** `source_type` (`RDF_GRAPH` in the reference SDK). The concrete syntax is a parse hint, not an epistemic property: `source_type` is the key trust statements are scoped against and the key the domain mapping is derived from, and neither should fork on whether the bytes used prefixes or angle brackets. Implementations SHOULD NOT infer an RDF source type from a generic `.json` extension by sniffing for `@context` — that slot is contended, and the interchange bundles of §12 carry an `@context` of their own. |
5. Accept operator-specified `mutability` and `fetch_policy`; apply defaults (`MUTABLE / LAZY` for web URLs; `STABLE / NEVER` for local files; `MUTABLE / LAZY` for Reddit/forum URLs — a thread accretes edits and later comments, so the reference importer treats it as mutable rather than strictly append-only).
6. Fetch content if not already available locally; compute `content_hash` (SHA-256). Populate `content_published_at` if the importer extracts it (e.g. Reddit `created_utc`).
7. Write `Snapshot` with `warc_record_type = RESPONSE`, `extraction_status = PENDING`, and any importer-supplied metadata (`author_id`, `author_role`).
8. **Follow the primary link of a link-shaped post.** If the importer defines a primary-URL accessor and post-link following is enabled (per-importer default, operator-overridable), recursively deposit that URL with following **disabled on the recursive call** (the depth-1 cap, §7.2) and record a `POST_LINK` row in `corpus_follow_edges`. A failed secondary fetch never fails this deposit and writes no edge row; a dedup'd target still gets its edge row (§7.2 properties 4–5). Importers with no primary-URL semantic never trigger a follow.
9. Write corpus entry metadata; return `entry_id` and `snapshot_id`.

| **ZERO EXTRACTION COST** |
| --- |
| Deposit has no dependency on the extraction pipeline. A corpus entry is useful immediately as an archival record even before extraction completes. This makes Deposit suitable for bulk ingestion workflows where extraction is deferred — `particles deposit <urls.txt>` is a valid pattern. |

## 9.1a Assertion pathway

*Normative for any implementation exposing a direct-assertion surface (e.g. the
read-write MCP write tools). Direct assertion is **not** a seventh
operation — it composes Deposit (§9.1) + Client-layer candidate production (the
asserter supplies one candidate particle) + the §6.6 insert seam — but its
semantics are normative. An implementation that ships only the wire shape
without the five guarantees below is non-conformant.*

A directly-asserted particle is a normal Core particle with `extractor_ref`
omitted (§6.2) and `confidence.calibration_source = AGENT_ASSERTED` (the honest
label for an uncalibrated agent self-report). A conformant assertion
pathway MUST:

1. **Construct the trust-/status-/identity-bearing fields server-side.** The
   caller supplies only content, subject names, a self-reported confidence, an
   optional `uncertainty_nature` / tags, and the source excerpt (or an existing
   corpus-entry reference). `extractor_ref` (omitted), `calibration_source`,
   `status` / `status_reason`, the asserting identity (`asserted_by` plus the
   excerpt snapshot's `author_id`), and `supersedes` are server-owned; the
   self-reported confidence is clamped to a configured ceiling. The asserting
   identity is server-bound, not a per-call argument.
2. **Carry deposit-excerpt provenance.** The assertion deposits the excerpt in
   which the belief was established as a `CONVERSATION` corpus entry
   (zero-extraction Deposit, §9.1); the particle's `ProvenanceRef` points at it.
   An assertion with no excerpt and no existing corpus reference is rejected —
   an unprovenanced belief is not admitted.
3. **Reconcile through §6.6 in consensus mode.** The candidate enters via the
   cross-entry §6.6 ladder (never bypassing it). The host store reconciles as a
   multi-contributor store: a confirmed contradiction surfaces as an
   `INCONSISTENCY` (the losing candidate quarantined `CONFLICT_PENDING`), never
   an auto-supersede of the existing belief; and when the contradiction probe
   cannot complete, the assertion fails closed (quarantine), never admitting two
   coexisting ACTIVE beliefs.
4. **Weight agent-asserted content at or below operator-asserted content.** The
   asserting identity resolves a source-trust rank ≤ the operator baseline at
   query / conflict time, so a self-reported confidence cannot lift agent
   content's effective confidence above operator-asserted content.
5. **Surface contested beliefs to recall.** When a returned ACTIVE belief is
   referenced by an open `INCONSISTENCY`, the read surface marks it contested,
   so a contradiction is visible to the reader, not only to operator Review.
   Since this marker is one basis of the **composed contested
   badge** (§6.9 "The composed contested badge"): the query response
   annotates each returned claim with the badge and its fired bases
   (`stance` / `divergence` / `inconsistency`), disclosure-only, computed
   at read time.

`EXPLICIT_SUPERSESSION` (§6.2) is set on the prior particle when a successor is
asserted with `supersedes` — the deliberate-revision ledger entry, distinct from
the system-driven supersession reasons.

## 9.2 Extract

Extract derives particles from a corpus snapshot. It is asynchronous, incremental, and re-runnable. Extraction is triggered lazily when a corpus entry's particles are needed by a query, or eagerly by `particles extract <entry-id>`.

### Extractor plugin registry and dispatch

an `ExtractorRegistry` selects an extractor for a given snapshot using a dispatch ladder driven by per-extractor `APPLICABILITY` clauses (see also §14.1):

1. **Most-specific match.** Each registered extractor declares an applicability over `source_type` (and optionally further constraints like URL pattern, content language, or `properties` keys present). The registry picks the most specific extractor whose applicability matches. RFC 2119 conflict tiebreaking (`MUST` > `SHOULD` > `MAY`) resolves overlapping claims.
2. **Multiple-extractor fan-out (Extension A).** If multiple extractors at the same applicability tier claim the snapshot, all of them run; their outputs are merged per §6.9 trust-weighted confidence.
3. **General-extractor fallback.** If no domain extractor matches, the general extractor runs. It accepts any source type and produces `EXTRACTOR_DIRECT` particles.

The reference SDK's current extractor catalogue is in §14.4.

### Chunked extraction and carry-forward

For sources whose rendered text exceeds the single-call context budget, the extractor pipeline chunks the input. Per-source-type chunkers:

- **PDF** — page-chunked.
- **HTML** — **character-budget chunking**: the decoded text is split into chunks bounded by a configured maximum character size, each cut **snapped to a line boundary** within the budget (falling back to a hard cut only for a pathological single unbroken line). This is a cheap, deterministic budget-and-snap pass, not a semantics-aware **structural** (DOM- / HTML-block-aware) chunker — that remains future work (Appendix A).
- **Long UGC** (Reddit threads, gist comment streams) — adaptive chunking.

Each chunk is identified by `chunk_hash` (SHA-256 of the chunk text). **re-extraction uses content-hash carry-forward**: a re-run skips chunks whose `chunk_hash` is unchanged from the prior extraction. Particles from carried-forward chunks remain `ACTIVE` without being re-extracted; only changed or new chunks invoke the LLM. This makes incremental updates cheap and is the dominant re-extraction pattern in practice.

### Extract algorithm

1. **Identify the snapshot set.** For `APPEND_ONLY` sources with prior extractions, compute the delta. For `MUTABLE` sources, extract from the full new snapshot. For `STABLE` sources, extract once.
2. **APPEND_ONLY with edits to prior content** (resolved OQ-9). Run a cheap text diff between prior and new snapshot. If the changed regions are limited to tail content (new additions), treat as `APPEND_ONLY` delta. If changed regions include non-tail content, fall back to `MUTABLE` handling for *this* snapshot: re-extract from the full new snapshot and set `PROVENANCE_STALE` on particles whose `provenance.location` falls within the changed regions. Full semantic diffing is deferred (Appendix A).
3. **Retrieve archived content** by `content_hash`.
4. **Chunk** if applicable (per above). For each chunk, check `chunk_hash` against the prior extraction; carry forward unchanged particles.
5. **Run the selected extractor(s).** Each candidate particle carries `calibration_source = EXTRACTOR_DIRECT`, the chunk's `chunk_hash` in its `provenance`, and the extractor's `extractor_ref`. Domain extractors additionally populate `properties` and emit candidate external references that subject resolution attaches to the Subject record's `external_ids` (§6.8).
5a. **Classify document scope**. The extractor tags each candidate with a scope, `WORLD` (default) or `DOCUMENT_META` — *the assertion is about the source document's own structure, sections, numbering, cross-references, or editorial apparatus, not about entities or events in the world*. The judgment is semantic and rides the extraction call itself (no second pass, no lexical pattern list); the label is recorded in `properties` (`extraction:scope`, §6.8) — absent means `WORLD` — and each `DOCUMENT_META` classification is disclosed in the extraction result's quality notes (no silent truncation). The default outcome mode is **label, not drop**: the particle stays `ACTIVE` and stored. `DOCUMENT_META` particles are **excluded from step 7's conflict resolution and from the semantic-contradiction lint** (L-SEM-01) — document-meta claims never meaningfully contradict one another, and running them through the truth engine only manufactures `INCONSISTENCY` noise — and are excluded from the default query surface (§9.3). **Confidence is never the scope lever**: a `DOCUMENT_META` claim may be perfectly true, so its `confidence.value` is untouched — scope governs visibility and engine participation, never the truth scalar. Operator-configurable alternative modes: `suppress` (drop `DOCUMENT_META` candidates before persisting; lossy) and `passthrough` (tag only, no behavioural effect). This axis is orthogonal to `assertion_modality` (§6.2): a document-meta claim is typically `FALSIFIABLE` yet still excluded — its defect is scope, not truth-aptness.
6. **Resolve subjects** for each candidate (§6.7 ladder): local match → external ontology → bare local.
6a. **Suppress exact duplicates**. Before conflict detection, test each candidate against the §6.10 re-observation rule: if an `ACTIVE`, truth-apt, asserted particle already holds the same normalized `content` with the same resolved subject-id set and the same `stance:holder`, do not write the candidate — append its provenance ref to that particle instead, and disclose the suppression in the operation's result. The predicate is exact content identity, never similarity, and it runs **above** step 7 deliberately: an exact duplicate that reaches the ladder finds no contradiction signal, resolves as corroboration, and would be written as a second `ACTIVE` particle. Implementations MUST exclude from the suppression target set any particle this run is about to supersede (step 8) — folding a candidate into a particle that is then retired would remove the claim from the `ACTIVE` surface entirely.
7. **Detect conflicts.** For each candidate, query the particle store for `ACTIVE` particles with overlapping subjects and content similarity above a threshold. Apply the conflict resolution ladder (§6.4):
   - Truth-aptness pre-gate → if either particle is non-`FALSIFIABLE` (`assertion_modality` of `EVALUATIVE` / `EXPERIENTIAL` / `CONSTITUTIVE`), the pair corroborates and both stay `ACTIVE`: there is no shared truth to adjudicate. Non-falsifiable particles are not even selected as comparison pairs.
   - ALEATORY check → surface `INCONSISTENCY` immediately.
   - Source trust check (Extension B) → set lower-trust particle `PROVENANCE_STALE` if differential exceeds threshold. When the *existing* particle wins, the candidate is dropped without persistence — but the drop is **audited**: a `CONFLICT_CANDIDATE_DROPPED` operator event (§9.7) records the candidate excerpt, the verdict, and the winning particle id.
   - Default → persist the losing candidate **quarantined** (born `PROVENANCE_STALE` with `status_reason = CONFLICT_PENDING`, full content/provenance/confidence/subjects/embedding), then create an `INCONSISTENCY` particle whose PARTICLE provenance refs point at the two persisted rows; queue for Review.
8. **Handle supersession.** If a candidate updates a prior claim from the same source, set `supersedes` and mark the prior `SUPERSEDED`. For `MUTABLE` re-extraction, set `PROVENANCE_STALE` on all prior particles from earlier snapshots of this entry.
9. **Write the particle** with `status = ACTIVE` (or as `INCONSISTENCY` per step 7).
10. **Update snapshot** `extraction_status = COMPLETE` (or `FAILED` with error detail; failed snapshots are picked up by Reindex auto-discovery, §9.5).

### Event-anchored validity boundaries

The general extractor MAY populate a candidate's `valid_until` (§6.2) for a
claim whose text carries a **genuine, resolvable, future-dated validity
boundary** — an arrangement or scheduled event that ceases to hold at a named
instant ("the contract runs through 2026", "the exam is tomorrow"). This is the
extraction-time producer of the field the §9.3 lazy filter and the §9.4
`L-STR-05` staleness lint (and, under the as-of read lens, the
`VALIDITY_EXPIRED` retirement instant) already consume; before the
field was operator-set only.

Emission is **normatively biased toward under-emission**, because a spurious
`valid_until` silently retires a durable fact (via the staleness lint) — the
strictly more dangerous direction than omitting a boundary (which merely leaves
the claim to recency decay). A conforming general extractor MUST NOT assign a
`valid_until` to a claim that merely *mentions* a date without being bounded by
it (a completed past event "signed in 1919", an origin "founded in 1998"); the
governing test is *does the claim stop being true after the date?* Concretely,
the reference SDK gates emission on three conjunctive conditions — an explicit
boundary cue, a self-assessed boundary-confidence at or above a configured floor
(`extraction_validity.min_boundary_confidence`; a quantity distinct from the
claim's own `confidence.value`, which is never the lever — §6.9a),
and a resolved date **in the future** relative to extraction time; a
born-expired boundary (`valid_until <= now`) is dropped, leaving the claim
undated. Relative expressions ("tomorrow") are resolved against the source's
publication instant where known, else the extraction instant. Whether a
conforming implementation reproduces this exact gate is implementation-defined;
the normative requirements are the mention-vs-boundary contract and the
under-emission bias. The behaviour is config-gated (`extraction_validity`) and,
disabled, reproduces the pre-ADR-0197 output.

### Cross-entry reconciliation

Step 7's conflict detection originated as a per-entry check.
Particle insertion on the import / contribution path
runs **cross-entry reconciliation**: the candidate set is bounded —
existing ACTIVE particles about the same Subject(s) and/or above an
embedding-similarity threshold, across *all* corpus entries (the
subject graph is the reconciliation index; all-pairs comparison is
never required). The §6.4 ladder runs unchanged over the wider set;
only the candidate scope widens. In a shared, multi-contributor
store, auto-supersession is replaced by surfacing an `INCONSISTENCY`
— **a contributor's claim is never dropped by someone else's trust
order**; disagreement is ranked per-viewer at query time, not resolved away at write time. A systematic reconciliation
pass for pairs that predate a contributor is deferred.
The full design contract lives.

| **EXTRACTION TAX** |
| --- |
| Extractor confidence values reflect model belief, not evidence strength. All particles created by an extractor carry `calibration_source = EXTRACTOR_DIRECT` and should be treated as provisional until validated against benchmarks (§13.3) or human review. Extraction quality dashboards (§3.6 of the whitepaper) must be available to operators. The conformance validator (active in v0.19.0) is the tool for flagging extractors that populate fields mechanically — the *metadata theater* failure mode (whitepaper Risk #11). |

## 9.3 Query

Query retrieves relevant particles and generates a natural-language response tailored to the question and audience. Query MUST NOT block on extraction of large corpus entries; coverage gaps are disclosed in the response rather than resolved synchronously. The hot read path for the common case is *not* Query but the pre-rendered wiki article (§10.4), which Query falls back to via the wiki cache where applicable.

### Navigation model

Per whitepaper §3.11, Query's navigation primitive is **vector similarity over particle embeddings, not graph traversal**. Three properties keep this cheap:

1. **Shallow graph structure.** Two hops deep: Subjects link to particles; particles link to corpus entries. There is no multi-level class hierarchy to crawl.
2. **Embedding-based retrieval.** The question is embedded; top-k particles are retrieved by cosine similarity (numpy-based embedding similarity over sqlite-vec). Subject and confidence filters are applied as cheap secondary constraints.
3. **Cached synthesis.** Per-Subject wiki articles (§10.4) cache synthesised prose with input-hash invalidation. When the read target is "an article about Subject X," Query routes through the cache; the LLM-synthesis path is reserved for unique questions.

This is the standard's answer to the *ontology-traversal* failure mode common to deep formal knowledge graphs.

### Query parameters

```yaml
QueryRequest:
  question: string              # the natural-language question
  subject_id: string?           # filter to a specific Subject
  min_confidence: float?        # default 0.0; filters effective_confidence
  uncertainty_nature: enum?     # ALEATORY | EPISTEMIC | null (any)
  recency_window_days: int?     # only particles whose snapshot.content_published_at
                                # is within this window
  audience: enum                # EXPERT | GENERAL | REGULATORY
  top_k: int                    # default 40; max 200
  collapse_co_evidential: bool  # default true (see §6.10)
  as_of: datetime?              # evaluate the store as of this past instant
                                # (assertion-time lens); a future
                                # instant MUST be rejected
```

### Query algorithm

1. **Validate** the request; reject particles whose `schema_version` is incompatible with the current store version (surface as `schema_mismatch` rather than including in results).
2. **Identify candidate corpus entries** via metadata + Subject store match. For entries with `extraction_status = PENDING` or `FAILED`, enqueue a background Extract job (do not block); record the entry as a `coverage_gap` in the response metadata.
3. **Embed the question** using the SDK's embedding model.
4. **Retrieve top-k particles.** Filter: `status = ACTIVE`; `subject_id` match if provided; `valid_until` is null or > now (lazy filter, §6.3); `recency_window_days` satisfied if provided; particles tagged `DOCUMENT_META` (`extraction:scope` in `properties`, §9.2 step 5a) are **excluded from the default factual surface** and returned only when the caller passes the explicit opt-in (`include_document_meta`) — they remain `ACTIVE`, stored, and auditable, just out of the default encyclopedia. Rank by the combined score `similarity_weight · cosine_similarity + confidence_weight · effective_confidence` (reference weights 0.6 / 0.4), where *cosine similarity* is the normalized, `[0, 1]`-clamped metric pinned in §8.5; only particles whose stored vector matches the store's `embedding_profile` are comparable (§8.5). Exact top-k ordering at the margins is profile-relative and non-normative (§8.5).
5. **Compute effective_confidence per particle** (§6.9): `confidence.value × extractor.trust_weight × source_trust_rank × recency_factor`. The domain for `SourceTrustStatement` applicability is derived from the particle's SOURCE corpus entry's `source_type` via the extractor registry's MUST-clause mapping — the same derivation the §6.6 conflict ladder uses; a source type with no MUST clause has no domain, and only URL-scoped trust rules can apply. Apply `min_confidence` filter post-computation (filtering on `effective_confidence`, not the raw `confidence.value`).
6. **Co-evidential collapse** (if `collapse_co_evidential` and such links exist). Group retrieved particles linked `CO_EVIDENTIAL`; render one representative per group. Confidence shown is the §6.9 merged value over the group; all member particles' provenance is preserved as co-citations.
7. **Generate the natural-language response.** Audience-driven template:
   - `EXPERT`: numeric confidence + uncertainty classification, full provenance chain inline.
   - `GENERAL`: hedged natural language ("according to X, …"), citations as footnotes.
   - `REGULATORY`: full provenance citations inline, no hedging; all retrieved particles included regardless of confidence; audit trail attached.
8. **Disclose coverage gaps** if any candidate entries had `PENDING` / `FAILED` extraction: *"Note: N corpus entries relevant to this query have not yet been extracted and may contain additional information."* In addition to this corpus-level signal, the response carries **subject-level coverage gaps**: when the request names a subject (the `subject_id` filter), the response distinguishes machine-readably *why* an answer may be incomplete — `NO_SUBJECT_MATCH` (the named subject is not in the registry), `SUBJECT_HAS_NO_PARTICLES` (the subject exists but has zero ACTIVE CLAIM particles — a phantom subject), or `SUBJECT_HAS_LOW_COVERAGE` (the subject has particles but fewer than a configurable threshold) — each gap carrying the subject id/name where known, the ACTIVE CLAIM `particle_count`, and a human-readable detail. The NL synthesis step SHOULD hedge on sparse subjects rather than answer with unwarranted authority. Subject inference from free-form query text is not required — the signal is populated under an explicit subject filter.
9. **Optionally** create a `QUERY` particle recording the question, retrieved particle IDs, coverage gaps, and generated response for audit trail.

| **OVERCONFIDENCE GUARD** |
| --- |
| If the mean `effective_confidence` of retrieved particles is below 0.6, or if any retrieved particle is uncalibrated — `calibration_source = EXTRACTOR_DIRECT` with no benchmark calibration record, or `calibration_source = AGENT_ASSERTED` (an uncalibrated agent self-report) — the query response MUST include a disclosure that the knowledge base has not been validated for this topic area. |

| **TOP-K TRUNCATION WARNING** |
| --- |
| when the candidate set exceeds `top_k`, the response MUST include a truncation warning if the bottom-ranked returned particle's similarity score is close to the next-rank-out particle's score (within a configurable margin). This prevents silent loss of relevant claims at the top-k boundary. |

| **SCHEMA VALIDATION AT QUERY TIME** |
| --- |
| The query layer MUST reject particles whose `schema_version` is incompatible with the current store version, surfacing them as `schema_mismatch` rather than including them in results. This prevents silently incorrect results from legacy particles after a schema migration. |

### As-of evaluation

When `as_of` is set to a past instant T, Query evaluates the store on
the **assertion-time axis** — *what did the store believe at T* — never
world-time validity. The normative changes relative to the algorithm
above:

1. **Visibility predicate.** Step 4's `status = ACTIVE` filter is
   replaced by: a particle is visible iff `asserted_at <= T` **and** it
   had not yet been retired at T — it is currently ACTIVE, or its
   retirement instant R satisfies `R > T`. `valid_until` is evaluated
   against T rather than now. Particles that were never believed
   (INCONSISTENCY records, quarantined conflict losers) are never
   visible.
2. **Retirement instants are stored facts, never guesses.** R is exact
   when computed from standard particle fields: a successor particle's
   `supersedes` pointer dates the predecessor's retirement at the
   successor's `asserted_at`, and a `VALIDITY_EXPIRED` retirement is
   dated by the stored `valid_until`. A conforming implementation MAY
   sharpen the remaining cases with whatever retirement records it
   keeps (this SDK stores a write-once `retired_at` and reads its
   operator event log); a retired particle whose retirement instant is
   unknown MUST be excluded (**fail-closed**) and the exclusion count
   MUST be disclosed in the response. An implementation MUST NOT
   fabricate or approximate retirement instants.
3. **Temporal quantities move to T; judgment quantities stay current.**
   The §6.9 recency factor and any recency-window filter are evaluated
   at reference instant T; the viewer's trust policy, adopted lenses,
   and contested-belief markers are evaluated as currently configured.
   Stored `confidence.value` is immutable (§6.3), so no historical
   value reconstruction is needed.
4. **The response carries the crossing.** For each returned particle
   since retired, the response annotates what replaced it and when
   (the supersession crossing), with the basis of the retirement
   instant, so the as-of answer is itself auditable. Under federation
   (below), the viewer's single `as_of` applies to every store's
   candidates. Unset `as_of` MUST preserve present-time behaviour
   unchanged.

### Federated cross-store query

The engine is store-parameterised: a **store** is one
database, named by an opaque `StoreHandle` resolved through a
config-driven registry, and every storage entry point takes an
optional `store` parameter whose default preserves single-store
behaviour unchanged. Two invariants are normative:

1. **Writes are single-store.** Deposit, Extract, status transitions,
   and §6.6 conflict resolution target exactly one store; there are no
   distributed transactions.
2. **Only reads federate.** A federated query fans out the §9.3
   retrieval across the selected stores, merges candidates by shared
   Subject external identity (`external_ids` under a registered
   authority — store-local UUIDs are never authoritative
   across stores), and reranks **per viewer**: the viewer's trust
   policy and adopted lenses apply to every
   store's candidates, so consensus is per-viewer trust at query time
   .

CLI surface: a repeatable `--store` option on `particles query` — the
first handle is the viewer whose trust policy ranks the merged
results; omitted, the default store is queried. The full design
contract lives.

## 9.4 Lint

Lint is a formal operation over the particle store and corpus. Structural checks are fast and require no LLM. Semantic checks use the LLM or symbolic-reasoning layers operating on structured inputs. Lint produces a machine-readable JSON-LD report and a human-readable Markdown rendering (via the Markdown Bridge, §10.3).

**Lint is read-only by default.** A plain lint invocation — on every surface (CLI, API, MCP) — reports findings and mutates nothing; the status transitions described by the fix-capable checks below (L-STR-01, L-STR-04, L-STR-05) are applied **only when the operator passes the explicit fix opt-in**. Where a check row says "set" or "persist" a status, read it as *the transition the check pairs with its finding*, applied under opt-in; the default run reports what would be transitioned. The MCP surface is read-only and never mutates regardless. All other checks are diagnostic-only on every run.

### Normative check set

Each check has an ID of the form `L-{CATEGORY}-{NN}` where category is `STR` (structural), `SEM` (semantic), or `IDX` (indexing).

| ID | Name | Category | Description |
|---|---|---|---|
| L-STR-01 | `PROVENANCE_STALE` cascade | structural | Find ACTIVE particles whose provenance chain includes a RETRACTED or SUPERSEDED particle. Set `PROVENANCE_STALE` with `status_reason = RETRACTED_DEPENDENCY`. Lazy propagation. |
| L-STR-02 | Subject coverage (`PHANTOM_SUBJECT` / `LOW_COVERAGE_SUBJECT`) | structural | two findings over the subject side of the graph, both computable without an LLM. `PHANTOM_SUBJECT` (severity WARNING): a Subject with **zero** ACTIVE CLAIM particles — a named entity the resolver created but the extractor produced no claims about; the subject-side complement of L-STR-08's orphan check. Remediation is operator triage (extract sources about it, or merge/delete if spurious); phantom subjects are flagged, never auto-deleted. `LOW_COVERAGE_SUBJECT` (severity INFO): a Subject with at least one but fewer than a configurable threshold of ACTIVE CLAIM particles; restricted to canonical subjects (those carrying `external_ids`), since bare author-handle subjects are expected to be sparse and would flood the finding set. |
| L-STR-03 | `EXTRACTION_QUALITY_REPORT` | structural | Report the distribution of `calibration_source` values across ACTIVE particles. Alert if `EXTRACTOR_DIRECT` fraction exceeds the configured threshold (default 50%). The mitigation for whitepaper Risk #11 (metadata theater). |
| L-STR-04 | Corpus link integrity | structural | Find particles whose provenance references a `snapshot_id` no longer in the corpus. Flag as `PROVENANCE_STALE` with `status_reason = CORPUS_ENTRY_MISSING`. |
| L-STR-05 | Staleness (`valid_until`) | structural | Find ACTIVE particles whose `valid_until` has passed. Set `PROVENANCE_STALE` with `status_reason = VALIDITY_EXPIRED`. (Query also filters lazily — §9.3. Lint persists the state transition under the fix opt-in.) |
| L-STR-06 | Pending extraction report | structural | Report corpus entries with `extraction_status = PENDING` or `FAILED`. Surface as gaps in knowledge base coverage. |
| L-STR-07 | Schema version audit | structural | Report distribution of `schema_version` values across ACTIVE particles. Flag particles whose `schema_version` is incompatible with the current store version as `schema_mismatch` candidates for migration. |
| L-STR-08 | Orphan detection | structural | Find ACTIVE CLAIM particles with zero provenance references. no-provenance means orphan — the particle is anchored to no corpus entry. Flag as pruning candidates. (Subject linkage is L-STR-09's concern.) |
| L-STR-09 | `NO_SUBJECT` | structural | Find ACTIVE CLAIM particles with empty `subject_ids`, excluding the §9 zero-subject populations: DOCUMENT_META claims, non-asserted claims, and claims marked `extraction:subject_scope = SELF`. §6.7: a claim SHOULD be about at least one subject; zero-subject claims are unreachable by subject-filtered query. The exclusion predicate is shared with §14.5's `subject_ids` measurement, so the lint and the conformance floor cannot disagree about which claims owe a subject. Severity: WARNING. |
| L-STR-10 | `COMPOUND_ASSERTION` | structural | Find ACTIVE agent-asserted particles (`asserted_by` = the MCP write surface's bound identity) whose `content` breaches the claim-granularity soft-gate the write surface applies at assert time (`mcp.write.max_assertion_chars` / `max_assertion_sentences`). Surfaces compound beliefs asserted before the gate existed for operator review. Read-only; severity WARNING. The deterministic size proxy is interim. |
| L-STR-11 | `STRUCTURED_CLAIM_SUBJECT_MISMATCH` | structural | find ACTIVE particles whose `structured_claim.subject_id` is set but is not among the particle's `subject_ids` — the triple makes a statement about an entity the claim is not about, the cheapest available signal that the structurizer hallucinated the subject. A `null` `subject_id` is **not** flagged: it honestly records that the subject term resolved to no Subject. The remedy is regeneration of the annotation, never a change to the claim. Severity: WARNING. |
| L-STR-12 | `BARE_PROPERTIES_KEY` | structural | Find ACTIVE particles carrying a `properties` key with no `prefix:` — §6.4 requires `prefix:LocalName` so a consumer can attribute a key to a namespace. The conformance validator asks the same question of *fresh extractor output* over a fixture (§14.5); this rule asks it of the store, which is the only surface that sees particles arriving by interchange import, from a third-party extractor, or from before a convention change. Advisory and read-only: the remedy is a data migration or a re-extraction, never a status transition, and the claim itself is unaffected. Severity: WARNING. |
| L-SEM-01 | Contradiction detection | semantic | Across ACTIVE truth-apt particles store-wide — including pairs from *different* corpus entries — generate candidate pairs by embedding cosine similarity at or above a configurable threshold (`lint.contradiction_candidate_threshold`), then use LLM comparison to evaluate semantic contradiction. The similarity gate bounds the candidate set so the check avoids an O(n²) LLM cost (only the cosine comparison is O(n²)). Apply the §6.4 conflict resolution ladder; surface remaining genuine `INCONSISTENCY` particles for Review (§9.6). Pairs already linked `CO_EVIDENTIAL` (§6.10) are excluded, as are non-`FALSIFIABLE` particles and different-holder stances. |
| L-SEM-02 | `GRANULARITY_VIOLATION_CANDIDATE` | semantic | Identify particles whose content appears to contain multiple independent claims. Flag for re-extraction. A structural pre-check (content length vs the extractor's median) reduces LLM calls. |
| L-SEM-03 | `WIKIDATA_LINK_MISMATCH` | semantic | find particles whose Wikidata external ref has low cosine similarity to the particle content, suggesting the wrong entity was matched. Severity: WARNING. |
| L-SEM-04 | *(retired)* | semantic | The former semantic phantom-subject check (common-noun / transient-phrase subjects) is superseded: prevention moved to the extraction-time non-entity gate (§6.7), and the `PHANTOM_SUBJECT` finding is the structural zero-coverage check under L-STR-02. The ID is retained so historical reports remain interpretable; a conforming implementation does not run a semantic phantom check. |
| L-IDX-01 | *(relocated)* Candidate co-evidential links | indexing | Candidate proposal is **not a lint check**: lint emits no `CO_EVIDENTIAL_CANDIDATE` findings. Near-duplicate candidates within a Subject are surfaced by the links-suggest curation operation — §6.10 "Creation paths" path 2 — which owns the report / LLM-judge / apply workflow. The mitigation for whitepaper Risk #10 (claim proliferation) lives there; the ID is retained for historical reports. |

### Lint output

```yaml
LintReport:
  ran_at: ISO 8601
  scope: string                   # 'full' | 'entries:[...]' | 'subjects:[...]'
  findings:
    - check_id: string            # e.g. 'L-SEM-01'
      severity: enum              # INFO | WARNING | ERROR
      particle_ids: string[]?     # particles implicated
      subject_ids: string[]?      # subjects implicated
      entry_ids: string[]?        # corpus entries implicated
      details: object             # check-specific data
      recommended_action: string? # human-readable
  summary:
    by_check: { check_id: count }
    by_severity: { severity: count }
```

The report is rendered to Markdown via the Markdown Bridge (§10.3) for human review.

| **DAY-ONE USAGE** |
| --- |
| The lint tool runs against existing LLM-Wiki and RAG knowledge bases via the retrospective import path, shipped in v0.31.1: `particles import vault <dir>` deposits every markdown note in an existing vault unmodified as a `LOCAL_MARKDOWN` corpus source (Obsidian YAML frontmatter is stripped before extraction), the standard extraction pass converts the notes into particles, and Lint runs normally. Lint is therefore useful on day one against an existing knowledge base without the operator rebuilding it by hand. An earlier revision of this callout promised a deterministic parser treating raw markdown as low-confidence particles with implicit provenance, bypassing extraction; that mechanism was rejected — sentence-split prose yields context-dependent fragments rather than self-contained claims, and uniform stamped confidence is metadata theater (whitepaper §5 Risk #11). Extraction is the conversion step. |

## 9.5 Reindex

Reindex re-extracts particles for a scoped set of corpus entries. It is the operation by which improved extractors propagate their improvements through the store, and by which previously-failed extractions are retried.

### Auto-discovery scope

By default, Reindex auto-discovers two scopes:

1. **Failed snapshots.** Snapshots with `extraction_status = FAILED`. The retry attempts re-extraction with the current extractor; if the failure was transient (rate limit, network), this resolves.
2. **Stale extractor version.** Particles whose `extractor_ref.version` is older than the currently-registered version for the same extractor name. These are candidates for re-extraction with the upgraded extractor.
3. **Extraction pairing.** Particles whose `extraction_provider_model` equals a requested `"<provider>:<model>"` pairing — the scope for re-extracting what one model produced, e.g. after an uncalibrated provider swap benchmarks badly. Matched by **exact equality**, never substring: pairings nest (`openai:gpt-5.6` is a prefix of `openai:gpt-5.6-luna`), so a substring match would select the sibling model the scope exists to distinguish. Particles with a `null` pairing never match. Note the scope unit is the snapshot, so a snapshot whose particles were produced by more than one model is re-extracted in full.

### Explicit scoping (CLI flags)

```bash
particles reindex                        # auto-discovery scope
particles reindex --entry-ids ce:a,ce:b  # explicit corpus entries
particles reindex --extractor-id general-extractor  # all entries from this extractor
particles reindex --source-type REDDIT_POST         # all entries of this source type
particles reindex --verbose                         # per-entry progress (0.14.5+)
```

`--extractor-id` is especially useful when an upstream change to the extractor's prompt (rather than a code version bump) warrants re-extraction across all of its outputs.

### Reindex algorithm

1. **Resolve scope** from CLI flags or auto-discovery. Compute the set of `(corpus_entry_id, snapshot_id)` tuples to re-extract.
2. **For each scoped entry,** query the particle store for all ACTIVE particles whose `provenance.snapshot_id` is in scope and whose `extractor_ref.version` is the prior version. These are candidates for supersession.
3. **Enqueue Extract jobs** (§9.2), rate-limited to prevent re-extraction storms. Default rate limit: 100 extractions per minute; operator-configurable.
4. **Chunk-hash carry-forward**: for each snapshot, identify chunks whose `chunk_hash` is unchanged from the prior extraction. Particles from carried-forward chunks are NOT superseded; only chunks that produce different particle outputs cause supersession. This is the dominant pattern — most re-extractions touch only a handful of chunks.
5. **As each Extract job completes:**
   - New particles whose `chunk_hash` matches a prior particle's chunk are diffed; if content is materially different, the new particle supersedes the prior (set `supersedes`, mark prior `SUPERSEDED` with `status_reason = SUPERSEDED_BY_REINDEX`).
   - Particles not covered by the new extraction (e.g. if the new extractor has narrower scope) are left ACTIVE — they are not retracted automatically.
6. **Surface progress** through the extraction quality dashboard. With `--verbose`, per-entry status is streamed.
7. **On completion,** run a Lint pass (§9.4) over the reindexed entries to detect any new inconsistencies introduced by the updated extractor.

| **RE-EXTRACTION STORM MITIGATION** |
| --- |
| When a high-trust domain-specific extractor is registered that covers a large number of existing corpus entries, the resulting Reindex scope may be very large. Rate limiting and chunk-hash carry-forward ensure the particle store remains queryable throughout. Operators should monitor the extraction quality dashboard during large Reindex jobs and review the post-Reindex Lint report before promoting the new extractor to `MUST` status in their registry. |

## 9.6 Review

Review is a human-in-the-loop operation for resolving `INCONSISTENCY` particles and generating durable `SourceTrustStatement` records from those resolutions. It is the mechanism by which operator judgment becomes reusable trust policy rather than one-time manual fixes.

### Review workflow

1. **Retrieve** `INCONSISTENCY` particles, ordered by domain and confidence impact (highest-impact first).
2. **For each `INCONSISTENCY`,** present the conflicting particles side by side:
   - Content
   - Provenance chain (corpus entries, snapshots, chunk hashes)
   - Source metadata: `author_id` and `author_role` for UGC sources (§6.5)
   - Confidence values (raw, calibrated, and effective)
   - Domain context (Subjects, related particles in the same Subject)
3. **Reviewer selects one of four resolution actions:**
   - `PREFER_A`: particle from source A is correct. Create a `SourceTrustStatement` preferring source A's source/author over source B's within this domain. Set particle from source B to `PROVENANCE_STALE` with `status_reason = CONFLICT_RESOLVED` — for a quarantined B (born `CONFLICT_PENDING`) this is a reason-only update, no status transition. Record `review_id` on the new statement.
   - `PREFER_B`: symmetric for the trust statement and A's demotion. A quarantined B is **promoted**: a new ACTIVE particle is minted from the quarantined row — fresh id, `supersedes` → the quarantined row, content/provenance/confidence/subjects/embedding carried over (the Reindex pattern) — and the quarantined row becomes `SUPERSEDED`. There is no `PROVENANCE_STALE → ACTIVE` transition.
   - `BOTH_VALID` (ALEATORY): the conflict is irreducible — both claims are correct in different contexts. Set `uncertainty_nature = ALEATORY` on both; a quarantined B is promoted as in `PREFER_B`, minted with `ALEATORY` nature, so both claims are queryable. Surface to future queries with both values and appropriate hedging.
   - `DEFER`: insufficient context to resolve. Leave `INCONSISTENCY` status. Add reviewer note. Re-queue after a configurable interval.

   **Wrapper-terminal rule.** Every non-DEFER resolution also retracts the `INCONSISTENCY` wrapper itself (`status_reason = CONFLICT_RESOLVED`), so a resolved conflict leaves the review queue and cannot be re-resolved; implementations MUST reject a resolution action against an already-resolved wrapper. `DEFER` is the only action that leaves the wrapper open.

   **Legacy wrappers.** `INCONSISTENCY` particles created before the quarantine rule may carry a dangling B ref (the losing candidate was never persisted; only the wrapper's content excerpt survives). Such wrappers remain resolvable — `PREFER_A` and `DEFER` behave normally with excerpt-only display for B; `PREFER_B` / `BOTH_VALID` cannot recover claim B's full content because it was never stored.
4. **On `PREFER_*` resolution:** write the new `SourceTrustStatement` with `policy_provenance = REVIEWER_DERIVED`. Record a `REVIEW` particle:

```yaml
REVIEW:
  review_id: string (UUID)
  inconsistency_particle_id: string
  resolution: enum                    # PREFER_A | PREFER_B | BOTH_VALID | DEFER
  reviewer_id: string
  reviewed_at: ISO 8601
  trust_statement_id: string?         # if a new statement was created
  notes: string?
```

5. **Co-evidential offer.** If the two conflicting particles turn out to be paraphrases of the same claim (rather than genuine contradiction), the reviewer may instead create a `CO_EVIDENTIAL` link (§6.10) and dismiss the `INCONSISTENCY`. The Review UI should surface this as a fifth implicit action: *"these aren't contradictory, they're the same claim."*

### UGC author trust

For UGC sources, when a reviewer chooses `PREFER_A`/`PREFER_B`, the Review UI offers to persist the resolution as an `AUTHOR`-scoped `SourceTrustStatement` for the domain (rather than just a one-time particle-level resolution). A reviewer who consistently prefers a GitHub project maintainer over anonymous commenters is implicitly building author-scoped trust policy; the offer makes that explicit and durable.

### Core vs Extension B behaviour

- **Core (annotation-only).** Each `INCONSISTENCY` requires its own Review action. The `PREFER_*` resolution sets the lower-trust particle `PROVENANCE_STALE` and records the `REVIEW` particle. The new `SourceTrustStatement` is stored but does *not* automatically cascade to other open `INCONSISTENCY` particles. Each conflict is resolved individually.
- **Extension B (auto-cascade — shipped).** After writing a new `SourceTrustStatement`, re-evaluate all open `INCONSISTENCY` particles in the same domain against the new statement. Particles that now resolve automatically are set `PROVENANCE_STALE`; their `REVIEW` particles record the auto-resolution and the triggering `statement_id`. The cascade is policy-gated: `OPERATOR_DIRECT` statements cascade unconditionally; `REVIEWER_DERIVED` statements require N ≥ 3 reviewer confirmations (operator-configurable) before they cascade. Auto-cascade is bounded by `max_cascade` (default 500) per statement.

| **TRUST MODEL BOOTSTRAPPING** |
| --- |
| A new deployment starts with no `SourceTrustStatement` records. The first round of Review sessions builds the initial trust policy organically from real conflicts in the operator's actual corpus. This is more reliable than asking operators to pre-configure trust ranks for hypothetical conflicts — the policy reflects the domain and sources the operator actually uses. |

| **DEMOTION-ONLY INVARIANT** |
| --- |
| `SourceTrustStatement` records may only *demote* confidence — never silently suppress conflict visibility. Extension B's auto-cascade never promotes trust automatically; it only resolves conflicts by demoting the lower-trust particle to `PROVENANCE_STALE`. `INCONSISTENCY` particles created before a trust statement existed are retained in the audit log even after auto-resolution. |

## 9.7 Operator Event Log

Every operator-initiated mutation — retraction,
subject merge / split, trust change, review resolution, lens adoption,
marking a belief useful — is recorded in an
**append-only operator event log**: an
`operator_events` header table (event type, timestamp, actor,
free-text `--reason`, structured payload) plus an
`operator_event_refs` index table mapping events to the particles,
subjects, corpus entries, and trust statements they touched, so
*"what operator actions touched record X?"* is an indexed lookup.
Rows are inserted, never updated or deleted by application code.

The write-helper lives in the operation / store layer, so events fire
regardless of which front-end triggered the mutation, and the read
surface (`particles events list` / `events show`) is exposed
identically across CLI, HTTP, and MCP. The `actor` column is reserved
to become the authenticated principal when multi-user authentication
lands. The event log is the audit complement to the particle-level
status machine (§6.6): status transitions record *what* changed in
the knowledge substrate; the event log records *which operator
decision* caused it and why. The full design contract lives.

One event kind is also a **system of record rather than an audit
echo**. `BELIEF_MARKED_USEFUL` records an operator's
explicit usefulness gesture, and the per-belief utility evidence it
credits is a *derived index* rebuilt from these events — so the log
is authoritative for that channel, not a parallel copy of it. The
event exists because the usefulness signal (mined from an
agent's tool-call actions) is structurally blind to prohibitions and
design stances: compliance with *"never do X"* is the **absence** of
an action, which no miner over actions can observe. The gesture is
operator-only and promotion-only, and it affects projection ranking
alone — never a particle's stored or effective confidence.

# 10. Serialization, Standards Alignment, and Exporters

§10 covers three closely-related surfaces: the on-wire serialization format (§10.1), the catalogue of external standards Particles aligns with (§10.2), and the renderings that turn particles into human-readable Markdown (§10.3 per-particle, §10.4 per-Subject). The exporter family is the user-facing layer that makes the standard's commitments visible to readers who do not run the SDK.

## 10.1 Serialization Format

Particles uses **JSON-LD** as the primary runtime serialization format — compact, self-describing via `@context`, natively compatible with RDF and PROV-O, and familiar to AI engineers. The canonical `@context` document is `artifacts/schemas/context.jsonld`; the JSON Schema for Core fields is `artifacts/schemas/particle.schema.json`. Both are normative per §6.1. The `@context` maps **every** key the interchange codec emits, so an exported unit expands fully to the `particles:` vocabulary with no dropped terms — the JSON-LD → RDF round-trip is a real, conformance-tested surface. A round-trip conformance test serializes a particle with provenance, expands it against the shipped `@context`, and validates the expanded graph against the SHACL shapes (including `ProvenanceChainShape`).

A companion XMI serialization provides full PSUM compliance for OMG ecosystem tooling. The XMI form is generated from the JSON-LD form on demand; the JSON-LD is the authoritative storage representation.

### Interchange and store export

Two store-level serialization surfaces build on the
same JSON-LD `@context`: **particle interchange** — a stream of
self-contained particle units for exchange between stores (the
federation transport) — and **store export** — a bundle
of an entire store for portability and backup. Unlike the one-way
exporters (§10.3–§10.5), interchange is round-trippable. CLI:
`particles interchange export` / `import`.

**The interchange unit (normative).** One unit = one particle as a
JSON-LD object carrying **only the immutable substrate**: `content`,
the stored `confidence` record (value + nature + kind + calibration
metadata), provenance, `asserted_by` / `asserted_at`, `status` +
`status_reason`, `valid_until`, `extractor_ref`,
`extraction_provider_model`, `properties`, `context_fingerprint`,
`schema_version`, `contributors`, and `assertion_modality` where
present. A unit **never** carries derived or per-observer quantities
(`effective_confidence`, ranks, lens outputs) — those are recomputed
on import; round-trip preserves the substrate exactly (the
recomputability contract). Units serialize one-per-line (JSONL) for
bulk exchange and MUST validate against `particle.schema.json` and
the SHACL shapes — the format inherits the three-layer conformance
validation of §6.1. The **unit envelope itself** — the JSON-LD wire
object's camelCase terms, its required/optional key set, and the
`@context` / `@type` / `formatVersion` framing — is pinned by a
dedicated normative artifact, `artifacts/schemas/interchange.schema.json`
. It describes both the **Particle unit** (`@type:
"Particle"`) and the standalone **Subject unit** (`@type: "Subject"`)
a store-export bundle carries; every emitted unit MUST validate against
it, and `particle.schema.json` additionally governs the Core field
semantics a Particle unit carries.

**Serializations (normative).** Two standard serializations carry the
interchange unit, both bound to the same JSON-LD `@context`:

- **JSON-LD / JSONL** is canonical and lossless — one unit per line,
  for streaming and machine-to-machine bulk exchange.
- **YAML-LD** is a human-editable convenience — a single YAML document
  holding the same sequence of units, the same terms, and the same
  `@context`. It **MUST round-trip** to the canonical JSON-LD: decoding
  a YAML-LD member and re-encoding it reproduces the identical document
  model (key order and concrete syntax may differ; semantics may not).

A conforming implementation MAY offer either serialization on its
export/import surface; the store-export bundle selects one per bundle
and the members' file extensions (`.jsonl` / `.yaml`) name the choice
.

**Cross-store identity (normative).** Store-local UUIDs (`id`,
`subject_ids`, provenance entry/snapshot ids) are not authoritative
across stores:

- **Subjects travel by external reference** — `(namespace, id)` under
  a registered authority, never by store-local UUID. The
  target store merges a subject only when it shares an external id
  under a registered authority; subjects with no shared authority —
  bare-local, or the same entity aligned to *different* authorities —
  **do not auto-merge** (cross-authority equivalence is out of
  scope). A bare-local subject travels as an inline descriptor
  (canonical name + aliases) and imports as a new subject.
- **Particle import identity is claim identity** — the content
  fingerprint plus §6.6 reconciliation in the **target** store: each
  imported unit is reconciled through the same conflict ladder a
  fresh extraction takes. The origin store handle and origin particle
  id ride along as **provenance metadata** (audit / back-reference),
  never as target identity.
- **Provenance travels as descriptors** — source URI + `content_hash`
  + location — so a receiving viewer can apply trust without the full
  corpus; raw corpus blobs are a store-export concern and travel by
  reference by default.

**The store-export bundle (normative).** A container (directory /
tar / zip) with a `manifest.json` envelope and newline-delimited
members. The envelope carries `format_version` — versioned
independently of Core `schema_version` (units carry
`schema_version`; the container can evolve without a Core schema
bump) — plus the source store handle, `exported_at`, and per-member
record counts. Members: a particles and a subjects member (the
knowledge-graph core), serialized either as JSONL (`particles.jsonl`)
or YAML-LD (`particles.yaml`) — one container per bundle, the member
extension naming the choice — with trust-statement, operator-event,
and corpus-manifest members defined by the format and emitted as the
reference implementation completes them. Import of a bundle is a
sequence of single-store writes (invariant — no
distributed transactions).

## 10.2 Standards Alignment Map

| **Standard** | **Full Name & Reference** | **Role in Particles** |
| --- | --- | --- |
| **PSUM** | Precise Semantics for Uncertainty Modeling. OMG formal/24-12-03, June 2025. https://www.omg.org/spec/PSUM/1.0 | Semantic foundation. Owns the meaning of belief, uncertainty, evidence, and epistemic degree. PSUM governs what particle fields mean; W3C PROV governs how they are serialized and exchanged. See §6.1 for the normative layer separation. |
| **W3C SHACL** | Shapes Constraint Language. W3C Recommendation, July 2017. https://www.w3.org/TR/shacl/ | Schema validation layer. The reference SDK ships SHACL shapes for the Particle schema (`artifacts/schemas/*.shacl.ttl`), enabling machine-checkable conformance testing. |
| **W3C PROV** | W3C Provenance Ontology. W3C Working Group Note, April 2013. https://www.w3.org/TR/prov-overview/ | Interchange provenance layer. Owns the serialization and exchange form of provenance chains. Particle `ProvenanceRef` structures are compatible with PROV-O Activity/Entity/Agent graphs. |
| **ODRL** | Open Digital Rights Language. W3C Recommendation, February 2018. https://www.w3.org/TR/odrl-model/ | Per-snapshot rights metadata. ODRL policies attached to corpus entries record usage rights, redistribution restrictions, and deletion obligations. Required for snapshots flowing through the shared archive (§7.3) when source rights are restrictive. Otherwise advisory. |
| **Wikidata** | Wikidata SPARQL Endpoint and REST API. https://www.wikidata.org/ | Primary external ontology for Subject canonicalisation (§6.7). The Wikidata extractor resolves candidate Subject names against Wikidata entities; the resulting Q-IDs are stored on `Subject.external_ids`. Link confidence is computed via cosine similarity between the Wikidata description and the particle content. |
| **Nomisma** | Nomisma.org Linked Open Data vocabulary for numismatic concepts. http://nomisma.org/ | Domain ontology used by Numista and Nomisma extractors. Property keys in `particles.properties` (§6.8) follow the Nomisma `nmo:` prefix for coin-related structured data. Demonstrates how domain extractors map onto formal ontologies without inflating Core. |
| **SACM** | Structured Assurance Case Metamodel. OMG version 2.3. https://www.omg.org/spec/SACM/2.3 | Argumentation and evidence chains for provenance. Relevant for regulated deployments. |
| **SMM** | Structured Metrics Metamodel. OMG version 1.2. https://www.omg.org/spec/SMM/1.2 | Quantification of confidence and uncertainty measurements. |
| **Memento** | The Memento Framework. RFC 7089. H. Van de Sompel et al., 2013. https://datatracker.ietf.org/doc/html/rfc7089 | Corpus entry URI-R / URI-M / TimeMap structure (§7.6). Enables interoperability with web archives. |
| **WARC** | Web ARChive Format. ISO 28500:2017. https://iipc.github.io/warc-specifications/ | Corpus snapshot record types (RESPONSE, REVISIT). Enables storage and tooling interoperability with Common Crawl, warcio, and archival pipelines. |
| **RFC 2119** | Key Words for use in RFCs to Indicate Requirement Levels. IETF BCP 14. S. Bradner, March 1997. https://datatracker.ietf.org/doc/html/rfc2119 | Extractor applicability specifications (§14.1) use RFC 2119 keywords (`MUST`, `SHOULD`, `MAY`, `MUST NOT`) to declare domain suitability and known failure modes. This is the formal mechanism behind the whitepaper's "machine-checkable applicability scopes." |
| **W3C VC** | W3C Verifiable Credentials Data Model 2.0. W3C Recommendation, 2024. https://www.w3.org/TR/vc-data-model-2.0/ | Recommended alignment for extractor record signatures (§14.3). Extractor author = issuer; particle store = holder; registry = verifier. Provides tamper-proof provenance chains for regulated deployments. |
| **BitTorrent / IPFS** | BitTorrent: https://www.bittorrent.org/beps/bep_0003.html · IPFS CID: https://docs.ipfs.tech/concepts/content-addressing/ | Optional shared-archive transports for public corpus snapshots (§7.3, §14.2). `content_hash` (SHA-256) serves as the content address compatible with both BitTorrent info-hashes and IPFS CIDs. The whitepaper presents this as *"content-addressed shared archive"*; these are the reference-implementation transports. |
| **MCP** | Model Context Protocol. Anthropic, 2024. https://www.anthropic.com/news/model-context-protocol | Transport layer for agent tool access. Particles can be carried over MCP; Particles adds the semantic knowledge layer above MCP's tool-call abstraction. |

## 10.3 Markdown Bridge — Per-Particle Annotation

The Markdown Bridge is the per-particle rendering primitive: it turns a single particle into a Markdown blockquote with its metadata as inline annotations. This is the lowest-level human-readable view of a particle and the building block from which higher-level exporters (the per-Subject vault, the wiki article exporter) are composed.

### Rendering format

A particle rendered via the Markdown Bridge appears as a Markdown blockquote with structured metadata in Obsidian-compatible callout syntax:

```markdown
> [!particle] `p-a91f2c…` — confidence 0.92 (EXTRACTOR_DIRECT)
> Acme Corp acquired Widget Inc.
>
> **Subjects:** [[Q-Acme-Corp|Acme Corp]], [[Q-Widget-Inc|Widget Inc]]
> **Source:** [example.com/news/2026/05/15/acme-widget](https://example.com/news/2026/05/15/acme-widget)
>   (snapshot `8b14a…`, fetched 2026-05-15)
> **Extractor:** general-extractor 0.3.0
> **Uncertainty:** epistemic
```

The rendering is generated by Jinja2 templates in `particles/exporters/markdown.py`. The template surface is operator-customisable for deployments that want different styling (color hints, different metadata fields surfaced, alternative callout type).

### Composition

The per-particle rendering is composed into two higher-level exporters by the exporter plugin registry:

- **Per-Subject vault** (`particles export obsidian`): one Markdown file per Subject, listing every particle about that Subject via the Markdown Bridge rendering. Optimised for graph navigation in markdown-native tools (Obsidian, Logseq, Foam).
- **Anki deck** (`particles export anki`): per-particle flashcards using the Markdown Bridge as the back-of-card content.

The wiki article exporter (§10.4) takes a different approach: rather than render each particle individually, it synthesises *prose* from the particle set and uses footnote citations to preserve provenance.

| **MARKDOWN BRIDGE IS A PRIMITIVE, NOT A USE CASE** |
| --- |
| The Markdown Bridge is not the answer to "how should I share a particle store with a non-technical reader." That role belongs to the wiki article exporter (§10.4). The Bridge is the building block: a stable, mechanical rendering of a single particle that higher-level exporters compose into views (per-Subject vaults, decks, articles). |

## 10.4 Wiki Article Exporter — Per-Subject Synthesis

The wiki article exporter is the primary read path for the common-case "show me what we know about Subject X" question. Where the Markdown Bridge (§10.3) renders particles individually, the wiki exporter *synthesises prose* from the particle set for a Subject, with every claim cited back to its particle ID and footnote-linked to the source URL. Per whitepaper §4.2, the wiki articles are the artefact that demonstrates Particles' differentiators without requiring the reader to install anything, understand the schema, or even know what a particle is.

This section pins the normative slot and the load-bearing invariants the implementation satisfies; beyond them, the reference exporter fixes non-normative detail a conformant implementation is free to vary — the exact synthesis-prompt structure, the article frontmatter shape, and the regeneration/overwrite semantics. Topic-level (multi-subject) articles, article versioning, operator-tunable synthesis prompts, and tag-aware articles (once folksonomy tagging, §16.2, is in use) are recognised extensions deliberately left to future work.

### Per-Subject scope and output shape

For each `Subject` with at least `min_particles` ACTIVE particles (default 3, configurable), the exporter generates one Markdown file `{subject_slug}.md`. A top-level `index.md` lists every generated article. Output is a static directory of Markdown files suitable for emailing, hosting via a static-site generator, or browsing locally.

### Synthesis with citation validation

The exporter loads the Subject's ACTIVE particles, renders them as a structured LLM prompt, and synthesises an article in which every claim cites a particle by its short ID (`[^p-abc12345]`). Synthesis is followed by a **citation-validation pass**: every footnote reference must point at a real particle in the input set. Articles with un-cited claims or invented citations are flagged and regenerated with a stricter prompt; persistent failures fall back to a structural listing rendering.

Validation runs in two layers. **Layer A** is deterministic ID membership: every cited footnote ID must exist in the input particle set. **Layer B** is a semantic-alignment judge auditing each *(claim, cited particle)* pair for the failure Layer A cannot catch — **citation laundering**, where a real particle is cited to make a hallucinated claim look sourced. The Layer B judge returns one of three verdicts per pair:

- **`supports`** — the particle is a necessary input to the claim; the claim may paraphrase, summarise, or combine it with other cited particles (encyclopedic prose is expected to do all three).
- **`unrelated`** — the particle is real but not a necessary input; the citation looks ornamental. A soft failure, tolerated up to a configured fraction of the article's citations.
- **`contradicts`** — the particle asserts something incompatible with the claim it backs. The hard failure — this is the laundering case.

The pass rule is deterministic given the verdicts: Layer B **passes** iff there are zero `contradicts` verdicts **and** `unrelated_count / total_citations` does not exceed the configured tolerance (the conformance profile pins the reference `layer_b_unrelated_tolerance` at 0.30); any `contradicts` verdict fails the article outright. Unknown or unparseable verdicts default to `unrelated`. Layer B is tri-state: it returns `passed = null` (neither pass nor fail) when it cannot run — no citations, judge unavailable, or unparseable judge output. A Layer B failure triggers regeneration with a Layer-B-specific strict prompt (naming the misaligned pairs), distinct from the Layer A invented-ID retry prompt.

This invariant — *every claim cited; citations validated post-synthesis* — is what distinguishes Particles' wiki articles from prose-only LLM-Wiki: the article cannot drift from its sources because the citation validation forbids any claim that is not traceable to a particle.

### Footnote collapse over co-evidential groups

When multiple particles in the input set are linked `CO_EVIDENTIAL` (§6.10), the synthesis collapses them into a single sentence with multiple footnotes — one sentence, N citations. This is the load-bearing mitigation for whitepaper Risk #10 (claim proliferation): five news articles reporting the same acquisition produce one synthesised sentence with five source citations, not five repetitive sentences.

Effective confidence shown for the collapsed sentence is the merged value from §6.9 (trust-weighted noisy-OR), not the max or the average of the individual particles.

### Incremental regeneration via input-hash caching

LLM-call cost dominates the wiki exporter. The exporter caches per-Subject article state via an `input_hash` (SHA-256 of the sorted-by-ID particle list that fed the article's generation). On re-run, articles whose input hash is unchanged are left untouched; only Subjects whose input set changed get re-rendered. The cache is bypassed with `--regenerate-all`.

This is the article-scope analogue of chunk-hash carry-forward and is the load-bearing mitigation for whitepaper Risk #9 (query-time synthesis cost): the hot read path for "what do we know about Subject X" is `cat wiki/Subject-X.md`, not running an LLM.

### Article synthesis as a cross-exporter capability

The article-rendering machinery (active in v0.22.0)
described above — synthesis prompt, citation validation (Layer A
regex + Layer B semantic-alignment LLM-judge), retry-then-fallback
ladder, frontmatter shape, input-hash cache key — lives in a shared
helper module `particles/exporters/article_synthesis.py` rather than
inside the wiki exporter itself. The wiki exporter (this section)
is one consumer; the **Obsidian exporter** (§10.3 family) is the
other, via the opt-in `particles export obsidian ./vault
--with-synthesis` flag, which splices the synthesised prose article
between the Obsidian per-subject note's H1 and its existing
structural particle listing (separated by a `## Source particles`
heading). The Logseq exporter (§10.5) is the third consumer.
All three share the per-subject `input_hash` through the
cross-exporter `synthesis_cache` table (§10.6) so an
operator who exports the same store via two or three formats pays
LLM cost once per Subject — not once per exporter.

### Cross-references

- Full design contract — synthesis prompt structure, frontmatter shape, regeneration semantics, deferred items like topic-level synthesis.
- Article-synthesis-as-shared-helper refactor; binding location for the helper module's API.
- §6.10 Claim Identity — co-evidential collapse semantics applied here.
- §6.9 Trust-Weighted Confidence Merging — merge formula applied per group.
- Whitepaper §4.2 — the use-case framing.
- Whitepaper Risks #9, #10 — the failure modes this exporter mitigates.

## 10.5 Logseq Exporter — Per-Subject Bullet Outline

The Logseq exporter is the third per-Subject-vault format (after
Obsidian and the wiki article exporter). Where Obsidian renders each
particle as a callout blockquote and the wiki exporter renders prose
articles, Logseq renders each particle as a *block* in Logseq's
native bullet-outline format — every line is a block, every block
has an `id::` property, and any block can be cited from any other
page via `((<block-id>))` syntax.

This section pins the normative slot and the cross-citation guarantee
below; beyond them, the reference exporter fixes non-normative
presentation detail a conformant implementation may vary — the exact
block-ID format, the per-page frontmatter shape, and the
particle-to-block rendering.

### Output shape

```
<output-dir>/
  pages/
    Subject-Name-1.md         # one outline page per Subject
    Subject-Name-2.md
    Contents.md                # top-level index
```

Each per-Subject page is a Logseq outline of blocks; the topmost
block carries the Subject's frontmatter metadata and `tags::`. Every
particle is a child block whose `id:: <particle-uuid>` makes it
addressable from any other page via `((<uuid>))`.

### Cross-citation guarantee

`((<particle-id>))` resolves natively in Logseq's UI to the cited
block. The exporter's choice to emit particle IDs (UUIDs) as block
IDs means every per-Subject vault becomes a graph in which any claim
can be cited from any other claim's discussion, mirroring the
provenance graph the particle store already encodes. This is the
core reason Logseq is in scope as a third exporter format
alongside Obsidian — its native data model (a graph of blocks with
addressable IDs) maps more cleanly onto the particle store than
Markdown wikilinks do.

### Synthesis integration

`particles export logseq <dir> --with-synthesis` splices the
synthesised prose article (via the shared `article_synthesis` helper)
above the structural particle outline, separated by a `## Source
particles` heading. The synthesis cache (§10.6) means re-running
this against the same store reuses synthesised articles produced by
`particles export obsidian` or `particles export wiki` against the
same Subject.

### Cross-references

- Full design contract — block-ID format, frontmatter
  shape, particle-to-block rendering).
- §10.4 Wiki Article Exporter — synthesis helper shared.
- §10.6 Shared Synthesis Cache — cross-exporter LLM amortisation.

## 10.6 Shared Synthesis Cache

The article-synthesis helper was specified to be shared
across exporters. The *cache*
side of that contract is realised (active in v0.41.0): per-Subject synthesised article bodies are
stored in a `synthesis_cache` table keyed on `(subject_id,
input_hash, prompt_version)`. Each prose exporter consults the table
before invoking the LLM, so running two or three exporters against
the same store pays LLM cost once per Subject — not once per
exporter.

```yaml
SynthesisCache:
  subject_id: string (UUID)         # primary key part
  input_hash: string                # primary key part — SHA-256 of
                                    # (sorted particle (id, status, conf))
  prompt_version: string            # primary key part — bump invalidates cache
  article_body: string              # full synthesised body
  generated_at: ISO 8601
  layer_b_verdict: string?          # last Layer-B alignment verdict
  quality_notes: string             # synthesis quality notes (JSON)
```

The primary key triple ensures:

- A particle set change (`input_hash` differs) misses the cache and
  re-synthesises.
- A prompt change (`prompt_version` bump) globally invalidates the
  cache without dropping the table — the next run regenerates every
  affected Subject's article.
- Two exporters consulting the cache for the same Subject + input
  + prompt see the same body.

Eviction:

- `particles export wiki|obsidian|logseq --regenerate-all` flushes
  the cache for the current run.
- `--invalidate-stale-links` drops the cache entry for
  any Subject whose article wikilinks reference a renamed Subject.
- Operators may delete rows directly via SQL for emergency
  invalidation.

The Obsidian exporter additionally backfills the cache from on-disk
note bodies when the per-note hash short-circuit fires and no DB row
exists yet — operators upgrading from pre-0.41 Obsidian vaults
populate the cache on the first export without paying LLM cost
twice.

### Cross-references

- Full design contract — eviction, backfill, prompt_version
  bump semantics).
- §10.4 Wiki Article Exporter — original synthesis consumer.
- §10.5 Logseq Exporter — third consumer.
- Whitepaper §3.5 — the cross-exporter framing.

# 11. Open Questions

§11 lists the **decisions v2 deliberately leaves open** — questions the working group has not (and should not yet) resolved, but which are tracked so that future versions can take them up. The 11 questions resolved between v1 and v2 have migrated into the relevant spec sections with ADR citations; only questions still open are retained here.

| **ID** | **Question** | **Current recommendation** | **Why still open** |
| --- | --- | --- | --- |
| OQ-7 | Standards body for v1.0 submission: OMG, W3C, or independent? | OMG preferred given PSUM/SACM/SMM alignment; W3C is an alternative if JSON-LD / Linked Data alignment is prioritised. Final decision deferred to the working group. | v1.0 milestone-blocking. Requires working-group consensus that the standard is ready for formal submission. Not a design decision; a coordination decision. |
| OQ-10 | What governance model applies to shared public archives (BitTorrent / IPFS swarms)? Who is responsible for a snapshot that was accurate at archival time but is now misleading? | Recommendation: shared archives are immutable historical records; governance responsibility lies with the depositing operator, not the archive infrastructure. The Memento datetime on each snapshot makes temporal scope explicit (per §7.6). | Legal/regulatory question rather than a technical one. Mirrors existing web archiving norms (Internet Archive policy). Liability in regulated domains requires per-deployment counsel; the spec should not attempt to resolve it. |
| OQ-12 | How should the `ACTION` particle_type be specified when introduced post-MVP? | Defer full specification to a post-v1.0 extension. Design constraint: `ACTION` particles must be able to reference epistemic `CLAIM` particles via provenance (enabling *"do X because of evidence Y"*). The `particle_type` field is reserved in v2 to ensure schema compatibility. GTD-style lifecycle states (`next_action`, `waiting`, `someday_maybe`, `done`) are the expected fields. | Conflating task management with epistemic knowledge in the Core schema would bloat the standard. The extensibility reservation is the right MVP posture. Operator demand will determine whether the full spec is worth writing. |

# 12. Multi-Agent Discourse Protocol — Extension E (Summary)

The multi-agent discourse protocol is **Extension E** of the standard, planned for a future major version and summarised in §18. Single-agent scope is the current Core target; multi-agent is deferred so single-user value lands first.

The first piece of multi-agent groundwork to land is **context fingerprinting** (active in v0.16.0; §16.1), which provides the shared-baseline mechanism that multi-agent exchange would build on. The multi-agent message types, trust model, and adversarial behaviour considerations are catalogued in §18 and in the whitepaper's §7 Future Directions.

| **CROSS-REFERENCE** |
| --- |
| Whitepaper §7.1 (Multi-Agent Knowledge Exchange) is the standard's user-facing vision statement for the multi-agent direction; §18 is the techspec-side message-type sketch. Risk #5 (whitepaper §5) catalogues ontology drift across agents as the known hard problem. |

# 13. Phasing, Success Metrics, and Benchmark Suite Interface

## 13.1 Phasing

The phasing table is a **live tracker** — status badges reflect the
current reference SDK release. For per-feature implementation status
(what is shipped, what is specified-but-not-built, what is deferred),
see the companion `roadmap.md`.

**Current release:** v0.61.1 of the reference SDK; spec at v2.2
(draft).

| **Version** | **Name** | **Status** | **Scope** |
| --- | --- | --- | --- |
| v0.1 | Schema Spec | ✅ Done | Particle schema; JSON Schema, JSON-LD @context, four normative SHACL shapes (a fifth, SubjectShape, followed in v0.52.1); PSUM/PROV alignment map. |
| v0.2 Core | Reference SDK — Core Loop | ✅ Done | Python SDK: Deposit / Extract / Query / Lint / Reindex / Review operations; general extractor; Markdown Bridge; coverage_gap disclosure; SHACL validation; CLI + FastAPI. v0.2 Core conformance achieved as of v0.15.1 (per Appendix B). |
| v0.2 Ext A | Extension A — Extractor Registry | ✅ Done | Importer + extractor plugin registries; RFC 2119 applicability; 11 domain extractors shipped, plus the mandatory general-extractor baseline (§14.4). |
| v0.2 Ext B | Extension B — Source Trust Automation | ✅ Done | Layered source trust cascade with policy gating; demotion-only invariant; content age decay; Wikidata link confidence. |
| v0.3 | Benchmarks + Wiki Articles + Claim Identity + Context Fingerprinting | ✅ Done | Context fingerprinting in v0.16.0; claim identity / co-evidential links in v0.17.0; extractor architecture decisions in v0.18.0; extractor conformance validator in v0.19.0; wiki article exporter in v0.20.0; benchmark harness (§13.3) in v0.21.0 with the seed numismatic suite as the first baseline; article-synthesis-as-shared-helper refactor in v0.22.0. Whitepaper v2.1 carries the baseline numbers (§3.1.3). |
| v0.4 | Taxonomy (Extension C part 2) | ✅ Done | Taxonomy and tag-aware query expansion shipped in v0.25.0. The v0.25–v0.5x releases also accumulated, among much else: extractor calibration, the Logseq exporter, the shared synthesis cache, subject split, and the operator event log; see `roadmap.md` and `CHANGELOG.md` for the full record. |
| v0.5x–v0.60 | Multi-user substrate + trust arc | ✅ Done | The multi-user architecture arc (0110): store-parameterised engine + federated query (§9.3); interchange / store export (§10.1); graded claim equivalence (§6.10); cross-entry reconciliation (§9.2); subject authority registry (§6.7); ContributorRef (§6.2); Client/Engine package carve. Capped by the trust arc: query-time source_trust_rank (§6.3/§6.9) and shareable trust lenses (§6.4), both active at v0.60.0. |
| Ext E | Multi-Agent (Extension E) | 🔮 Deferred | Multi-agent discourse protocol; agent trust model; merge semantics. Whitepaper §7.1 frames the direction; single-user and multi-user single-operator value lands first. |
| v1.0 | Standards Submission | 🔮 Deferred | Complete schema, protocol, SDK; conformance test suite; 3+ framework integrations; Memento HTTP interface over corpus; standards body submission (OQ-7 still open on which body). |

| **MVP RATIONALE** |
| --- |
| v0.2 Core is the MVP and shipped as of v0.15.1. The primary hook is the core loop: deposit a corpus, extract particles, query them, lint contradictions — demonstrating provenance fidelity on a real corpus. The secondary hook (lint runs against existing LLM-Wiki content) shipped in v0.31.1 as the retrospective import path (`particles import vault`; see §9.4). Extensions A, B, and C are shipped on top. v0.3 closes the benchmark-harness commitment that the whitepaper §3.1.3 publicly stated. |

### Extensions catalogue

| **Extension** | **Title** | **Depends on** | **Status** |
| --- | --- | --- | --- |
| A | Extractor Registry and Calibration | Core | ✅ Shipped |
| B | Source Trust Automation | Core + A | ✅ Shipped |
| C | Taxonomy and Context Fingerprinting | Core | ✅ Shipped — context fingerprinting in v0.16.0; taxonomy + tag-aware query expansion in v0.25.0 |
| D | Shared Archiving | Core | 🔮 Deferred |
| E | Multi-Agent Protocol | Core + A + B | 🔮 Deferred (v0.5+) |
| F | Privacy and Consent | Core | 🔮 Deferred (forward-reference in §7.4 callout; whitepaper §3.10) |

## 13.2 Success Metrics

Metrics are organised by dimension. The **Measured?** column is the
honest current state — most metrics are aspirational targets pending
the benchmark harness (§13.3); the few that are mechanically checked
in CI are marked accordingly. The whitepaper §3.1.3 quotes the
initial v0.21.0 baseline for the Numista coin extractor against the
bundled seed suite; growing suite + extractor coverage is the
ongoing work that this table tracks.

Conformance itself is graded **L1–L4** (Structural / Deterministic-compute /
Profile-similarity / Full) by the **Conformance Profile**
(`docs/spec/conformance-profile.md`); an implementation declares the
level it targets and self-certifies with `particles conformance check`. That is
the behavioural ground truth these success metrics measure progress *toward*,
distinct from the §13.3 BenchmarkSuite, which measures extraction fidelity.

### Adoption

| Target | Measured? |
|---|---|
| 3+ major agent frameworks with native Particles support within 18 months of v1.0 | Not yet |
| 10+ production agent deployments using Particles as knowledge store within 24 months | Not yet |
| 3+ independent implementations of the spec within 24 months | Not yet |

### Extraction fidelity *(harness shipped in v0.21.0; suite coverage growing)*

| Target | Measured? |
|---|---|
| Particle extractor recall: 90%+ of hand-labelled ground-truth claims on benchmark documents | Partial — Numista coin extractor scores 100% recall on the seed numismatic suite (one fixture); other extractors unbenchmarked. |
| Particle extractor precision: ≤ 10% of extracted particles are spurious or non-falsifiable | Partial — Numista coin extractor scores precision 1.00 on the seed suite (i.e. zero spurious particles). Other extractors unbenchmarked. |
| Calibration accuracy: `CALIBRATED_BENCHMARK` confidence within 0.05 absolute error of empirical accuracy on held-out test sets | Not yet — temperature-scaling calibration shipped (v0.33.0), but no extractor has yet graduated to a verified `CALIBRATED_BENCHMARK` accuracy target on held-out sets. |
| Cross-extractor confidence interoperability: two `CALIBRATED_BENCHMARK` extractors using temperature scaling on the same suite produce confidence within 0.05 of each other for equivalent claims | Not yet — calibration shipped; cross-extractor interoperability not yet verified on a shared suite. |
| General extractor recall: 70%+ on benchmark documents (floor) | Not yet — no general-extractor benchmark suite is published. |

### Correctness

| Target | Measured? |
|---|---|
| Retraction propagation: 100% of dependent particles identifiable via provenance traversal | ✅ Tested (conformance test suite) |
| Uncertainty fidelity: confidence values survive round-trip encode/decode with < 0.01 absolute error | ✅ Tested |
| Lint recall: 95%+ of injected contradictions detected without LLM assistance in structural benchmark tests | Not yet |

### Source corpus

| Target | Measured? |
|---|---|
| WARC round-trip fidelity: corpus content recoverable from WARC files with 100% content_hash match | Not yet (no WARC export implemented; deferred to Extension D) |
| Re-extraction correctness: particles re-extracted from unchanged corpus snapshot produce identical output with > 95% particle-level recall against the original extraction | Partial (chunk-hash carry-forward ensures byte-stable carry; recall across re-extraction not yet measured) |
| Fetch efficiency: > 80% of LAZY re-fetches for stable sources result in REVISIT records | Not yet |

### Risk-mitigation coverage

The whitepaper §5 risk table catalogues 12 risks. Each has a named
mitigation in the spec; this column tracks whether the mitigation is
shipped or pending.

| Risk | Mitigation | Status |
|---|---|---|
| #1 Extraction fragility | §3.1 design principles + §13.3 benchmark | Partial — benchmark harness shipped (v0.21.0); suite coverage limited to one numismatic fixture so far. |
| #2 Adoption friction | Markdown exporters (§10.3, §10.4); linter (§9.4) | Shipped — wiki exporter in v0.20.0; Obsidian `--with-synthesis` in v0.22.0. |
| #3 Epistemic overconfidence | §3.6 calibrated confidence; `calibration_source` field | Shipped |
| #4 Scale and performance | Storage scale targets (§8.4); top-k truncation | Partial |
| #5 Ontology drift (multi-agent) | Context fingerprinting | Shipped (v0.16.0) |
| #6 Source link rot | Local archive (§7); Memento alignment (§7.6) | Shipped |
| #7 Extractor trust misconfiguration | Trust weights + allowlists (§14.6); `extractor_ref` (§6.2) | Shipped |
| #8 Extractor ecosystem monoculture | `extractor_ref`, calibration_history, registries (§14) | Partial (registry shipped; community pending) |
| #9 Query-time synthesis cost | Wiki article exporter cache (§10.4); audience-tier budgets (§9.3) | Shipped (in v0.20.0; per-Subject input-hash cache makes the hot read path `cat wiki/Subject-X.md`, not an LLM call.) |
| #10 Claim proliferation / cross-source duplication | Co-evidential links (§6.10); L-IDX-01 lint (§9.4) | Shipped (in v0.17.0) |
| #11 Metadata theater | Extraction quality dashboards (§3.6); conformance validator (§14.5) | Shipped (in v0.19.0) |
| #12 Governance fragmentation | Conformance contract (§14.5); machine-checkable applicability (§14.1); shared calibration baselines (§13.3) | Shipped (applicability + conformance + benchmark harness all shipped by v0.21.0) |

### Source trust and review

| Target | Measured? |
|---|---|
| Conflict auto-resolution: > 60% of `INCONSISTENCY` particles in benchmark corpora with pre-configured trust statements resolved without human review | Not yet |
| Trust statement bootstrap: a deployment with zero pre-configured trust statements reaches > 50% auto-resolution after 20 human Review sessions in a single domain | Not yet |
| Review throughput: a domain-familiar reviewer resolves a single `INCONSISTENCY` in under 60 seconds | Not yet |
| Author trust propagation: `author_id` correctly extracted and surfaced in Review UI for 3+ UGC source types | ✅ Shipped (GitHub, Reddit) |

## 13.3 Benchmark Suite Interface

The standard does not prescribe specific benchmark datasets. Instead it defines a **BenchmarkSuite** schema that community contributors conform to when publishing benchmark suites. This lets the ecosystem develop domain-specific benchmarks without requiring the standard to anticipate every domain.

(This section was v1's §6.5 Benchmark Suite Interface. It moves here because a benchmark suite is a *testing* surface, not a particle-schema concept. The reference runner shipped in v0.21.0 — see § Status below. The whitepaper §3.1.3 quotes the initial baseline numbers it has produced.)

### BenchmarkSuite schema

```yaml
BenchmarkSuite:
  suite_id: string (UUID)
  name: string
  version: string (semver)
  domain: string                  # subject area this suite evaluates
  source_types: string[]          # corpus source types covered
  cases: BenchmarkCase[]
  metrics: RequiredMetric[]       # metrics all runners must report
  published_by: string
  published_at: ISO 8601

BenchmarkCase:
  case_id: string (UUID)
  source_snapshot: Snapshot       # the input to extraction
  expected: ExpectedParticle[]    # ground truth

ExpectedParticle:
  content: string                 # expected claim text
  confidence_min: float           # minimum acceptable confidence
  uncertainty_nature: enum        # expected ALEATORY | EPISTEMIC
  required: bool                  # if true, missing = recall failure

RequiredMetric:
  name: string                    # e.g. 'recall', 'precision', 'calibration_error'
  definition: string              # how it is computed
```

### Required metrics for all conformant benchmark runners

- **recall** — `matched_required / total_required`. Only `required: true` expected particles count toward the denominator; optional expected particles count toward precision but their absence is not a recall miss.
- **precision** — `matched_emitted / total_emitted`. Every emitted particle is either matched to an expected one or counted as spurious.
- **calibration_error** — **Expected Calibration Error (ECE)** over 10 equal-width confidence bins: for each bin *b*, empirical accuracy `acc_b = matched_in_bin / total_in_bin` and mean stated confidence `conf_b`; ECE = Σ over bins of `(|b| / N) · |acc_b − conf_b|`. Lower is better; 0.0 is perfect calibration. Two conformant runners MUST use the same binning so their reported numbers are comparable.

### Match semantics — when does an emitted particle match an expected one?

The three metrics are only comparable across runners if the claim-equivalence test is pinned:

- **Default (embedding judge):** embed all expected and emitted `content` strings with the store's embedding model (§8.5). For each expected particle, the highest-cosine emitted particle matches if similarity ≥ the equivalence threshold (reference default **0.80**, configurable). Assignment is **greedy one-to-one in similarity-descending order** — an emitted particle can match at most one expected particle, preventing double-counting.
- **LLM-judge mode (opt-in):** every `(expected, emitted)` pair scoring ≥ **0.65** cosine (a deliberately wider net) is evaluated by a batched LLM call for semantic match; the judge is the tiebreaker for pairs the embedding model finds plausible, and the cosine pre-filter bounds the LLM cost. Returns the same matched/unmatched split.
- **`confidence_min` demotion:** an emitted particle that matches an expected particle but whose stated confidence is below the expected `confidence_min` is demoted to a **partial match** — it counts toward neither precision nor recall and is surfaced in a separate `under_confidence` count. This catches the "right claim, but not confident enough to surface in operator workflows" failure mode.

Extractor authors report these metrics in their `calibration_history` entries (§14.3), referencing the `suite_id` of the benchmark used. The extractor conformance validator (§14.5) consumes the same benchmark output to compute conformance scores.

### Status

- **Specification:** frozen. The schema above is normative.
- **Reference runner:** shipped in v0.21.0 as `particles extractor benchmark <extractor-id>`. As of v0.43.0, three suites ship under `tests/benchmark/suites/`: `numismatic-seed-001` (structured catalog extraction; ECE 0.0471 raw), `reddit-seed-001` (UGC LLM-driven; ECE 0.6389 raw), `hackernews-seed-001` (UGC LLM-driven; ECE 0.8024 raw). The three suites produce the §3.7 calibration evidence table in the whitepaper. Community suites for additional domains are invited.
- **Community suites:** invited. TruthfulQA and HaluEval (cited in §6.3 and §10.2) are existing benchmark datasets that can be wrapped as `BenchmarkSuite` artefacts for Particles. Domain-specific suites for biomedical, legal, financial, and scientific content are explicitly invited.

| **CALIBRATION BASELINE** |
| --- |
| The reference SDK will ship a benchmark runner CLI that accepts any conformant `BenchmarkSuite` and produces a `CalibrationRecord` suitable for inclusion in an extractor's `calibration_history`. Temperature scaling (shipped in v0.33.0) is the recommended calibration method; the runner implements it as a one-shot post-processing step over the runner's raw outputs. |

# 14. Extension A: Extractor Registry and Calibration

Extension A defines the extractor registry, the applicability and pipeline-selection model, the shared-archive interop layer, the Extractor Record Schema, the reference extractor catalogue, the conformance validator, and the extractor trust model. It builds on the general extractor and the Core extraction pipeline (§9.2) and adds the community-ecosystem layer.

| **WHITEPAPER / TECHSPEC TERMINOLOGY** |
| --- |
| The whitepaper §3.8 uses accessible terms for two mechanisms specified in this section: *"machine-checkable applicability scopes"* and *"content-addressed shared archive"*. The techspec keeps the formal mechanism names — **RFC 2119 applicability clauses** (§14.1) and **content-addressed transports including BitTorrent info-hashes and IPFS CIDs** (§14.2) — because the techspec is where mechanism lives. Both registers refer to the same designs; a reader bouncing between whitepaper and techspec should not see them as different concepts. |

## 14.1 Applicability and Pipeline Selection

| **APPLICABILITY OPERATES ON CLAIM DOMAINS, NOT URLs** |
| --- |
| RFC 2119 applicability clauses describe the *semantic claim domain* an extractor is suited for (*"biomedical literature"*, *"legal contract text"*, *"general web content"*), not the URL pattern of the source. URL-pattern dispatch — *"this URL is a GitHub gist, hand it to the gist importer"* — is the importer registry (§9.1), a separate mechanism. The two work in series: importers fetch and normalise the source; extractors then process the normalised text according to their applicability. A single source can be imported by one URL-pattern importer and processed by any number of extractors whose applicability matches. |

### RFC 2119 applicability specifications

Extractor authors declare the scope and limitations of their extractor using RFC 2119 keywords (BCP 14, March 1997). The `applicability` field on an extractor record is a list of **`ApplicabilityClause`** objects. Each clause carries four fields:

| Field | Type | Meaning |
|---|---|---|
| `keyword` | `MUST` \| `SHOULD` \| `MAY` \| `MUST_NOT` | The RFC 2119 strength of the applicability statement. |
| `domain_uri` | string (IRI) | The **canonical, language-independent identity** of the claim domain — an IRI, conventionally a **Wikidata entity URI** (`http://www.wikidata.org/entity/Q…`; e.g. social media = `Q202833`), but any stable domain-identifying IRI is permitted where no clean Wikidata item exists (a platform's canonical URL, an ontology namespace). The IRI is the interop-stable key: two implementations naming the same domain agree on the IRI, not on a prose string. |
| `domain_label` | string | A short human-readable name for the same domain (e.g. `"social media"`, `"personal journal"`). This is the operator-facing label and the string the domain-derivation match (§6.4 / §9.2 dispatch) compares against. |
| `source_types` | string[] | The corpus `source_type` values (§7.2) this clause applies to. |

```yaml
applicability:
  - keyword: MUST
    domain_uri: "http://www.wikidata.org/entity/Q202833"   # social media
    domain_label: social media
    source_types: [REDDIT_POST]
  - keyword: MUST_NOT
    domain_uri: "http://www.wikidata.org/entity/Q8242"      # literature — figurative text
    domain_label: poetry and figurative language
    source_types: []
```

The **domain vocabulary is IRIs, conventionally Wikidata QIDs**: `domain_uri` is a Wikidata entity URI wherever a clean item exists, with `domain_label` as its human-readable companion. The standard does not mint its own domain ontology — it reuses Wikidata's where it can — so the domain a social-media extractor claims (`Q202833`) and the domain a physics extractor claims are globally distinct identities any implementation can dereference. `MUST_NOT` clauses are the canonical form for documenting known failure modes. The pipeline treats them as hard exclusions: an extractor with a `MUST_NOT` clause matching the source domain is never selected for that source, regardless of trust weight. This prevents systematic errors from being silently applied at scale.

(The **subject-authority registry** reuses this same `ApplicabilityClause` shape to scope which authorities fire on which claim domains; see §6.7.)

### Pipeline selection algorithm

1. `MUST` — highest priority. Extractor is authoritative for this domain; prefer exclusively if trust weight permits.
2. `SHOULD` — strong preference. Used when no `MUST` extractor applies.
3. `MAY` — acceptable fallback. Used when no `MUST` or `SHOULD` extractor applies.
4. `MUST_NOT` — hard exclusion. Never selected for this domain regardless of other factors.
5. No matching clause — treated as `MAY` for selection purposes; the general extractor remains the unconditional fallback.

### MUST-MUST conflict tiebreaking

When two registered extractors both carry `MUST` clauses matching the same source domain, the pipeline applies a tiebreaker in order of precedence:

1. **Higher precision** on the specific `source_type` of the current snapshot, as recorded in the most recent `calibration_history` entry (§14.3).
2. If precision is equal or unavailable, **more recent calibration_history entry**.
3. If calibration history is absent for both, **higher operator-assigned trust_weight** (§14.6).
4. If trust weights are equal, **run both** and merge their outputs via §6.9 trust-weighted noisy-OR; if the merge produces conflicting candidates, flag as `INCONSISTENCY` for Review (§9.6).

## 14.2 Shared Archiving for Public Sources

§7.3 documents the standard's commitment to a content-addressed shared archive. §14.2 documents the Extension A operator-side interop: how a snapshot fetched from a shared archive is verified, recorded, and made available to extraction.

For public, stable sources, the `content_hash` (SHA-256) functions as a content address compatible with BitTorrent info-hashes and IPFS CIDs. A snapshot whose `content_hash` is already present in a shared archive need not be fetched or stored locally — the implementation verifies the hash and records the `archive_location` reference.

```yaml
archive_location:
  - type: local
    path: "corpus/abc123/snap_001.warc.gz"
  - type: magnet
    uri: "magnet:?xt=urn:btih:..."
  - type: ipfs
    cid: "bafybeig..."
  - type: warc_url
    url: "https://web.archive.org/web/..."
```

`archive_location` is an ordered list tried in sequence — local first (fastest), then archive transports. Resolution is a `content_hash` verification: the bytes returned MUST hash to the recorded `content_hash` or the location is rejected and the next is tried.

| **SCOPE CONSTRAINT** |
| --- |
| Shared archiving applies only to `STABLE` and `APPEND_ONLY` public sources. `EPHEMERAL` sources MUST NOT be submitted to shared archives (§7.4). `MUTABLE` sources require per-snapshot governance decisions before sharing, since older snapshots may contain content the origin has since revised or retracted. Per-snapshot ODRL metadata (§10.2) governs whether a snapshot may be redistributed. |

## 14.3 Extractor Record Schema

An extractor is a registered artifact in the Particles ecosystem. The extractor record is the canonical description of an extractor's identity, domain coverage, applicability constraints, calibration history, and interface contract. It is the basis for pipeline selection (§14.1), trust evaluation (§14.6), and targeted re-extraction (§9.5).

### Extractor record fields

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `extractor_id` | string, UUID | Globally unique identifier for this extractor registration. |
| `name` | string | Human-readable name. Conventionally `org/name` (e.g. `acme/biomedical`). |
| `version` | string (semver) | Semantic version. A new version triggers re-extraction eligibility for all particles with `extractor_ref` pointing to prior versions (§9.5). The particle-side `extractor_ref.version` (§6.2) carries the same constraint normatively — the eligibility rule above is an *ordering* over versions, so a version that cannot be ordered breaks it rather than degrading it. |
| `source_types` | string[] | Source types this extractor handles. A subset of the corpus `source_type` values — an **open string set**, not a closed enum (§7.2); an extractor may name a value no prior extractor did. Empty list means any source type. |
| `applicability` | ApplicabilityClause[] | RFC 2119 domain applicability statements (§14.1). |
| `claim_grammar` | string (optional) | Human-readable description of the claim types this extractor produces (factual assertions, causal relationships, temporal claims, etc.). Informs pipeline composition decisions. |
| `interface` | ExtractorInterface | See Extractor Interface below. |
| `calibration_history` | CalibrationRecord[] | Ordered list of benchmark runs. Each record: `{benchmark_id, run_at, recall, precision, calibration_error, source_types_tested}`. |
| `calibration` | CalibrationParameters? | The currently-active calibration parameters applied to extracted confidences at extraction time (v0.33.0). Contains `{temperature: float, transform: string?, fitted_at: ISO 8601, suite_ids: string[], ece_raw: float, ece_calibrated: float, sample_n: int}`. Particles extracted while a calibration is set carry `calibration_source = CALIBRATED_BENCHMARK` and a stored confidence value scaled by `sigmoid(logit(raw) / temperature)`. `transform` names the functional form the temperature parameterises — `"logit"` for the above; a record omitting it predates that change and is not applied. `null` until the operator first runs `particles extractor calibrate <extractor-id>`. |
| `conformance` | ConformanceReport (optional) | The most recent extractor conformance validator output (§14.5). |
| `registered_by` | string | Agent or org ID. Used by trust chain resolution (§14.6). |
| `registered_at` | ISO 8601 | Registration timestamp. |
| `signature` | string (optional) | Cryptographic signature over the extractor record by `registered_by`. Enables PKI-style trust chain verification; W3C VC alignment is recommended (see §10.2). |

### Extractor interface

All registered extractors MUST implement the following interface. This standardisation makes extractors composable and portable across Particles implementations.

```yaml
ExtractorInterface:
  extract(snapshot: Snapshot,
          config: object,
          prior: Particle[])    # existing particles for delta/carry-forward
    -> ExtractionResult
  accepts(snapshot: Snapshot)
    -> { accepted: bool, reason: string? }

ExtractionResult:
  particles: CandidateParticle[]
  supersessions: SupersessionHint[]   # prior particle UUIDs this result supersedes
  co_evidential: CoEvidentialHint[]?  # within-extraction co-evidential links (§6.10)
  quality_notes: string[]             # extractor-generated warnings or caveats
```

`co_evidential` is new in v2: an extractor that processes an aggregating source (e.g. a Wikipedia article citing five news reports) MAY emit within-extraction `CO_EVIDENTIAL` links between the particles it creates. This is the extraction-time creation path.

| **GENERAL EXTRACTOR CONTRACT** |
| --- |
| the general extractor MUST implement `ExtractorInterface` and MUST accept any snapshot regardless of `source_type`. It MAY apply to all domains (no `MUST_NOT` clauses). Its `calibration_history` is maintained by the reference SDK and updated with each benchmark release (§13.3) using temperature scaling against TruthfulQA, HaluEval, and future Particles-specific benchmark suites. Domain-specific extractors override the general extractor when their applicability clauses match; the general extractor is the unconditional fallback. |

## 14.4 Reference Extractors

The reference SDK ships a catalogue of extractors as evidence that the Extension A architecture works across diverse sources. The table below documents the catalogue as of v1.126.2 — the `source_type` strings and default `trust_weight` values are the shipped ones; for the live status of each (shipped vs in-progress) and per-extractor configuration knobs, see `roadmap.md`.

| Extractor | `source_type` matched | Default `trust_weight` | ADR | Notes |
|---|---|---|---|---|
| `general-extractor` | * (fallback) | 0.70 | 0018 | Mandatory baseline. No configuration. Produces `EXTRACTOR_DIRECT` particles. |
| `numista-coin-extractor` | `NUMISTA_API_COIN` | 0.90 | 0042 | Coin catalogue entries; populates `properties` via Nomisma ontology (§6.8). |
| `numista-issuer-extractor` | `NUMISTA_API_ISSUER` | 0.85 | 0042 | Coin-issuing authority records. |
| `numista-listing-extractor` | `NUMISTA_LISTING_HTML` | 0.80 | 0042 | Catalogue listing-page HTML (lower trust — less curated than the API records). |
| `wikidata-extractor` | `WIKIDATA_API` | 0.90 | 0041 | General-knowledge entity descriptions. High trust due to Wikidata's curation model. |
| `nomisma-extractor` | `NOMISMA_API` | 0.95 | 0047 | Linked Open Data; ontology IRIs preserved as Subject `external_ids` (§6.8). Highest trust — formal ontology source. |
| `reddit-extractor` | `REDDIT_POST` | 0.40 | 0050 | UGC; lowest default trust. Populates `author_id`. Applicability: MUST social-media (Q202833). |
| `hackernews-extractor` | `HACKERNEWS_THREAD` | 0.50 | n/a | UGC; comparable trust to Reddit. Renders the story body + indented-DFS comment tree as prose for LLM extraction. |
| `mastodon-extractor` | `MASTODON_THREAD` | 0.50 | n/a | UGC; populates per-status metadata via `mastodon:` and `social:` properties. |
| `github-repo-extractor` | `GITHUB_REPO` | 0.75 | 0056 | Repository metadata + README. |
| `github-gist-extractor` | `GITHUB_GIST` | 0.65 | 0056 | Gist content + comments with author attribution. Used to ingest Karpathy's gist that motivated the project. |
| `github-pages-extractor` | `GITHUB_PAGES` | 0.70 | 0056 | Static-site content from `{user}.github.io`. |

The catalogue covers the design space — single-domain (Numista, Nomisma), general-knowledge (Wikidata), and multi-domain UGC (Reddit, GitHub gists with comments) — demonstrating that the architecture supports diverse extractor shapes without changes to Core.

## 14.5 Extractor Conformance

Whitepaper Risks #11 (metadata theater) and #12 (governance fragmentation) name the *conformance validator* as their primary mitigation. The validator's role is to make per-extractor field-population behaviour visible — uniformly populated fields vs missing fields vs mechanically filled fields — so operators can tell which extractors are taking the schema seriously and which are not.

The full design contract is an internal record (active in v0.19.0); this section pins the techspec slot.

### Conformance contract

Particle schema fields are categorised as **required**, **recommended**, or **optional** for the purposes of conformance:

- **Required** — every particle from a conformant extractor MUST populate this field, at a 100 % floor. The tier is **exhaustive**: `asserted_by`, `confidence.value`, `content`, `id`, `particle_type`, `provenance`, `schema_version`, `status`, `subject_ids`, `uncertainty_nature`. A conformance run that finds any extracted particle missing a required field reports the extractor as **non-conformant**.
- **Recommended** — every particle SHOULD populate this field where it applies; the conformance validator reports the population rate (`recommended_fill_rate`) and warns if below the configured threshold. The tier is **exhaustive**: `confidence.calibration_source`, `extractor_ref`, `provenance[].snapshot_id`.
- **Optional** — every other schema field: absence carries no quality signal, so the validator reports the rate without a threshold. Examples: `properties`, `sequence_context`, `tags`, `context_fingerprint`, `contributors`, `structured_claim`, `canonical_form`.

The two obligation-bearing tiers are enumerated here in full and are **normative** — an extractor's "conformance level" is determined against this contract, not against the validator implementation. The optional tier is the residue and is given by example only, because it grows with every schema addition and carries no obligation to grow with. The enumeration is machine-checked against `particles/conformance/contract.py` (`tests/test_conformance.py::TestSpecTierSync`) so that a reader of this section alone builds the same contract the reference implementation enforces; a field whose tier changes is a change to *this section*, not only to that file.

A `[]` token in a field path descends into list elements — `provenance[].snapshot_id` means "the `snapshot_id` of every `ProvenanceRef` in the chain", and counts as populated only when every element is.

**Measured population.** A field's rate is computed over every particle the run produced, *except* where the spec already says the field legitimately does not apply. Today that is one field: `subject_ids` is measured over the particles §9's subject-count table says should carry a subject, and the excluded particles are removed from the denominator rather than counted as failures. `FieldStat.excluded_count` reports how many were removed, so a rate is never read as wider than it is, and a field whose denominator collapses to zero reports **unevaluated** rather than 100 %. The exclusion is spec-derived, never extractor-declared: an extractor cannot widen its own exemption, and adding a class is a change to §9 and to the contract — the same distinction that made a self-declared extractor attribute an illegal key for conditional diversity application. Two reports are comparable only when their exclusion rules agree, which the contract version records.

### Validator output and gating

The validator produces a per-field report (one `FieldStat` per
contract entry, with rate / distinct-values / per-value counts /
pass-or-fail) plus top-level `failures` / `warnings` / `advisories`
subsets and a `passed` property. The full data shape, including the
**DIVERSITY** rule overlay that flags mechanically-filled fields (the
explicit countermeasure for whitepaper Risk #11 — the canonical
example is an extractor that always emits
`uncertainty_nature = EPISTEMIC`), is the `ConformanceReport` /
`FieldStat` / `DiversityRule` dataclass set in
`particles/conformance/types.py`. The design contract is recorded;
those dataclasses are the binding schema. The yaml sketch that
previously appeared in this section has been removed to avoid drift —
the implementation is the authoritative shape.

The report also names the `"<provider>:<model>"` pairing that produced
the particles it scored, in `extraction_provider_model` — the
same §6.2 key each particle carries. It is **null** when no scored
particle carries one, which at report scope means the extractor made no
completion call: a report covers only particles minted during its own
run, so unlike a particle's null (§6.2) it cannot mean
"predates the field". A conformant implementation may therefore read the
null as the deterministic-vs-model-derived discriminator, and must not
carry that reading over to a report computed against stored particles.

**Diversity severity.** Every `DiversityRule` declares a
`severity` — `FAIL` or `ADVISORY`, with no default, so a rule author
must state which. A `FAIL` violation joins `failures` and makes the run
non-conformant; an `ADVISORY` violation joins `advisories` and is
reported without affecting any field's verdict, `passed`, or the exit
code. The one rule shipped today — `uncertainty_nature` at
`min_distinct_values = 2` — is `ADVISORY`, because its outcome tracks
whether the extractor's *source vocabulary* carries a distinguishable
stochastic-quantity signal rather than whether the extractor is
complete: a parser over structured records has no honest basis to emit
`ALEATORY`, while prose extraction does but only by sampling. The
field's population tier is unaffected and remains `REQUIRED` at a
100 % floor. `FieldStat.value_counts` carries the per-value histogram
behind `distinct_values` for every enum-typed field, so a reader can
judge the margin behind a diversity result rather than only its
pass/fail.

**Gating policy.** Phase 1, the validator is
**report-only** in v0.19.0+: it produces a `ConformanceReport` and
exits non-zero only when invoked with `--fail-on error` (or `--fail-on
warn` for the stricter gate). Plain invocation never blocks anything.
Phase 2 — flipping CI to *block* PRs that introduce REQUIRED-field
failures — is deferred until the fixture corpus covers all built-in
extractors thoroughly; the threshold is a judgement call by the
maintainers. That deferral was conditioned on two prerequisites;
the first (the diversity rule) is now discharged, leaving fixture
coverage as the sole remaining one. Phase 3 — auto-discounting trust weights based on
conformance failures — is further deferred and would require a
separate ADR.

### CLI surface

```bash
particles extractor conform <extractor-id>                     # default fixture dir, table output
particles extractor conform <extractor-id> --fixtures ./fx     # override fixture directory
particles extractor conform <extractor-id> --format json       # JSON instead of table
particles extractor conform <extractor-id> --fail-on warn      # exit 1 on warnings too
particles extractor conform <extractor-id> --recommended-threshold 0.9
particles extractor conform <extractor-id> --all-accepted      # widen past routing (report-only)
```

**Which fixtures a run scores.** The default set is the fixtures the
production registry would *route* to the named extractor — the same
first-`accepts()`-wins ladder the extract pipeline uses, read back
through one helper. It is deliberately not "every fixture the
extractor accepts": the mandatory fallback extractor accepts every
source type by contract, so the accepts() predicate would report its
field-population rates over the whole corpus, including inputs no deployment
will ever route to it. `--all-accepted` restores the wide set for the
deliberate probe and is report-only — it never updates the stored conformance
verdict an implementation may feed to a trust lever.

The verb is `conform`, not `conformance`. `--all` is a shell loop
over `particles extractor list`; running all extractors at once is
not privileged as a first-class verb because conformance reports are
per-extractor decisions.

## 14.6 Extractor Trust Model

The extractor trust model controls how much an operator's particle store trusts the `confidence` values produced by each extractor. It is the per-extractor input to the merge formula in §6.9: `effective_confidence` is `confidence.value × extractor.trust_weight × source_trust_rank × recency_factor`.

§6.9 documents how the four factors combine into a per-particle and per-group `effective_confidence`. §14.6 documents the `trust_weight` factor specifically: how it is assigned, how it is propagated across registry endorsements, and how operators impose hard controls independent of trust weights.

### Trust weight

Every extractor registration in an operator's store carries a `trust_weight` scalar in [0, 1], operator-assigned. A weight of 1.0 means the extractor's stated confidence is accepted as-is; 0.5 means the operator believes the extractor overstates confidence by roughly half. The general extractor receives a default weight of 0.7 in the reference implementation; operators may override.

Trust weights affect confidence at query time, not storage. Low-trust extractor particles are stored and retained normally — they may be the only evidence available for a claim. The trust weight prevents them from misleading high-stakes queries, not from contributing to the knowledge base at all.

### Trust chains

In enterprise, academic, or regulated deployments, operators may not evaluate individual extractors directly. **Trust chains** allow an operator to delegate trust evaluation to a registry, which in turn vouches for individual extractors.

A trust chain is a sequence: `operator → registry → extractor`. Each link carries a trust weight. The effective extractor trust weight is the **product** of trust weights along the chain, with an operator-configurable floor:

```
# Simple chain (no decay)
effective_trust = operator_registry_trust × registry_extractor_trust

# Example: operator trusts registry at 0.9; registry endorses extractor at 0.85
effective_trust = 0.9 × 0.85 = 0.765

# Chains may be multi-hop; each hop multiplies. Operators impose a floor:
effective_trust = max(chain_product, floor)   # default floor 0.1
```

Trust chains mirror PKI certificate chains in structure. Registries are analogous to certificate authorities: they evaluate extractors against published criteria (calibration benchmarks, peer review, domain audits, conformance reports — §14.5) and issue endorsements. An operator who trusts a registry inherits its endorsements at the declared trust weight.

Chains deeper than 5 hops trigger a lint warning (per OQ-11 resolution): deep chains usually signal over-delegation or a misconfigured registry topology rather than a legitimate trust path.

### Allowlists and denylists

Operators may impose hard controls independent of trust weights:

- **Allowlist** — only extractors explicitly listed are permitted. Particles produced by unlisted extractors are rejected at ingest. The enterprise compliance case: a security team approves extractors before they may contribute to the knowledge base.
- **Denylist** — listed extractors are unconditionally excluded. Particles produced by denylisted extractors are flagged `PROVENANCE_STALE` regardless of stored confidence.

Allowlists and denylists are enforced at the operator level and do not propagate in multi-agent exchange (whitepaper §7.1). A receiving agent applies its own allowlist/denylist independently.

| **TRUST MODEL SCOPE** |
| --- |
| The trust model defined here applies to extractors. Agent-to-agent trust in multi-agent deployments is a related but distinct problem, deferred (whitepaper §7.1). The extractor trust model is intentionally simpler: extractors are registered artifacts with stable identities, not autonomous agents with dynamic behaviour. The chain-of-trust mechanism is designed to be sufficient for single-agent deployments and to compose cleanly with the agent trust model when it is specified. |

# 15. Extension B: Source Trust Automation

Extension B is **shipped** (implemented). It extends the Core Source Trust Model (§6.4) with automatic conflict cascade — re-evaluating open `INCONSISTENCY` particles against newly-written `SourceTrustStatement` records — and is enabled by default in the reference SDK. Extension B requires Extension A (for registry-endorsed trust statements).

## 15.1 Automatic Conflict Cascade

When Extension B is enabled, the conflict resolution ladder (§6.4) is extended: after a new `SourceTrustStatement` is written (by a Review session, by operator CLI, or by registry ingest), the system automatically re-evaluates all open `INCONSISTENCY` particles in the same domain against the new statement. Particles that now resolve are set `PROVENANCE_STALE` with `status_reason = CONFLICT_RESOLVED` (a quarantined loser gets the reason-only update, and a cascade resolving in the *quarantined* candidate's favour promotes it by minting a new ACTIVE particle, exactly as a `PREFER_B` review would); their `REVIEW` particles record the auto-resolution and the triggering `statement_id`.

The cascade is bounded by `max_cascade` (default 500 per statement, operator-configurable in `config.yaml`) to prevent runaway propagation when a high-impact statement is written. The trust-rank differential threshold (default 0.15) governs which conflicts resolve via cascade vs which remain for review.

### Policy gating

Extension B's cascade is **policy-gated** by `policy_provenance` (§6.4):

- `OPERATOR_DIRECT` statements cascade unconditionally — the operator's domain knowledge is treated as authoritative for the domain.
- `REVIEWER_DERIVED` statements require **N ≥ 3 independent reviewer confirmations** (operator-configurable) before they cascade. A single reviewer's judgment becomes durable policy only after enough independent confirmations to outweigh single-reviewer bias.
- `REGISTRY_ENDORSED` statements cascade according to the registry's own trust weight in the operator's trust chain (§14.6).

The policy gate is the load-bearing mitigation for the policy-poisoning threat: a single biased reviewer cannot manufacture a cascade-causing statement on their own.

| **WHAT "INDEPENDENT REVIEWER" MEANS** |
| --- |
| The N ≥ 3 rule's protection holds only if "independent" is operationally enforced. Particles defines independence as **distinct `asserted_by` identities** across the `REVIEW` particles that confirm the resolution. Implementations SHOULD use cryptographic reviewer identity (signed assertions, OAuth tokens, hardware-bound keys); a deployment that cannot enforce identity SHOULD raise the N threshold above 3 — or disable `REVIEWER_DERIVED` cascade entirely — rather than rely on honour-system distinctness. A single human operating three accounts under different `asserted_by` strings is not independent in any meaningful sense; the operator is responsible for ensuring the identity primitive matches the deployment's adversary model. |

## 15.2 Adversarial Threat Model

Extension B introduces attack surfaces not present in Core. The mitigations below are specified for the reference SDK and, where implemented, SHOULD be preserved in any conformant implementation (implementation status is noted per row; one — `L-SEC-01` — remains proposed and not yet specified):

- **Policy poisoning** — an adversary manufactures plausible conflicts from a controlled source, causing reviewers to encode a biased `SourceTrustStatement`. *Mitigation:* the N ≥ 3 confirmation requirement for `REVIEWER_DERIVED` cascade (above).
- **Author identity gaming** — sockpuppets, account resale, or cross-platform identity fragmentation corrupt `author_id`-scoped trust. *Mitigation:* require platform-verified author identity (e.g. GitHub OAuth, Reddit verified-account flag) before creating `AUTHOR`-scoped trust statements that will participate in cascade. Statements created without verification are stored but not cascade-eligible.
- **Threshold gaming** — adversary tunes source mixtures to stay just under the `trust_rank` differential threshold, preventing auto-resolution of legitimate conflicts. *Mitigation:* audit logs of `INCONSISTENCY` particles that repeatedly approach but do not exceed threshold are surfaced as a Lint signal (`L-SEC-01`, proposed; not yet specified).

| **DEMOTION-ONLY INVARIANT** |
| --- |
| Extension B's cascade *never promotes* trust automatically. It only resolves conflicts by demoting the lower-trust particle to `PROVENANCE_STALE`. `INCONSISTENCY` particles created before a trust statement existed are retained in the audit log even after auto-resolution. The cascade is auditable end-to-end: every auto-resolved particle's `REVIEW` record names the triggering statement, and every statement names its `policy_provenance`. |

| **BOOTSTRAP POSTURE** |
| --- |
| No `SourceTrustStatement` records are required at deployment time. The system functions with `INCONSISTENCY` surfacing as the default conflict behaviour. Trust statements accumulate organically through human Review; the cascade activates as the N ≥ 3 threshold is crossed for `REVIEWER_DERIVED` statements. Operators with strong domain knowledge may pre-configure `OPERATOR_DIRECT` statements that cascade immediately. |

# 16. Extension C: Taxonomy and Context Fingerprinting

Extension C defines two independent features that enhance retrieval and reproducibility without being required for the Core epistemic model: **TaxonomyDefinition** for user-defined folksonomy tagging, and **context fingerprinting** for delta compression and reproducibility in multi-agent deployments.

Extension C is **shipped**. Context fingerprinting is active in v0.16.0; taxonomy and tag-aware query expansion is active in v0.25.0. The spec text below is the standard-level statement of intent; implementation details belong to those records.

## 16.1 Context Fingerprinting

| **EXTENSION C — SHIPPED (v0.16.0)** |
| --- |
| Context fingerprinting is Extension C. A Core-conformant implementation is NOT required to compute or store `context_fingerprint` values. The `context_fingerprint` field on particles (§6.2) is optional and may be omitted. Implementations that do support it MUST follow the algorithm below exactly to ensure cross-agent fingerprint compatibility. for the implementation design. |

A context fingerprint is a **SHA-256 digest over the whole-store `ACTIVE` set** — the sorted UUIDs of every particle that was `ACTIVE` in the asserting agent's store at particle creation time (OQ-3 resolved). It is a flat fingerprint of that baseline set, not a Merkle tree, and it fingerprints the **entire** ACTIVE set rather than a per-particle dependency subgraph. It serves two purposes:

- **Delta compression** — two agents sharing a common fingerprint exchange only particles that differ from that baseline.
- **Reproducibility** — a particle can be re-evaluated in the context in which it was originally asserted.

*Anticipated future tightening.* Fingerprinting the narrower **dependency subgraph** actually reachable from a particle — rather than the whole ACTIVE set — would make the fingerprint more discriminating (two particles asserted against unrelated regions of a large store would no longer share a baseline). That refinement is deferred; the normative algorithm below is the whole-store form, and a conformant implementation MUST compute exactly that.

Fingerprint algorithm: (1) identify all `ACTIVE` particles in the asserting agent's store at the moment of assertion; (2) sort UUIDs lexicographically; (3) compute SHA-256 of the concatenated sorted UUIDs (no delimiter). The algorithm is deterministic and MUST be followed exactly to ensure cross-agent fingerprint compatibility. Incremental computation and storage strategies are documented. The procedure is machine-checkable: the Conformance Profile carries a `context_fingerprint` **L2 test-vector family** (`artifacts/conformance/profile.yaml`; `docs/spec/conformance-profile.md` §5.1) whose cases pin each of the three steps, and `particles conformance check --level L2` recomputes them.

## 16.2 Taxonomy Definition

| **EXTENSION C — SHIPPED (v0.25.0)** |
| --- |
| Taxonomy definitions and folksonomy tags are Extension C. A Core-conformant implementation is NOT required to support `TaxonomyDefinition` artefacts or the `tags` field on particles. The `tags` field (§6.2) is optional and may be omitted. Taxonomy-aware query expansion is an opt-in Extension C feature. for the implementation design. |

Folksonomies are user-defined tag hierarchies applied to particles. They coexist alongside the standard Particles schema without modifying Core fields. A `TaxonomyDefinition` is a depositable artefact that declares a set of tags, their parent-child relationships, and optional domain scope. Multiple taxonomies may be active in a particle store simultaneously.

```yaml
TaxonomyDefinition:
  taxonomy_id: string (UUID)
  name: string
  version: string (semver)
  author: string                 # agent or operator ID
  domain: string?                # scope hint
  tags: TagNode[]
  published_at: ISO 8601
  corpus_entry_id: string?       # if deposited into corpus for sharing

TagNode:
  tag: string                    # e.g. 'cycling/nutrition'
  parent: string?                # parent tag; null for root tags
  aliases: string[]?             # alternate labels mapping to this tag
  description: string?
```

**Taxonomy-aware retrieval.** When a query is evaluated, the query layer optionally expands tag filters using the active `TaxonomyDefinition` — a query for `cycling` returns particles tagged `cycling/nutrition`, `cycling/equipment`, and `cycling/training` without requiring the operator to enumerate subtags. Improves recall for queries that use the operator's personal vocabulary rather than the source vocabulary.

**Publishing and sharing.** A `TaxonomyDefinition` can be deposited into the corpus like any other source, assigned a stable `corpus_entry_id`, and shared via the content-addressed archive (§7.3, §14.2). Other operators can adopt a published taxonomy by depositing the same artefact and applying its tags. Shared taxonomies enable cross-operator query interoperability without schema changes.

| **FOLKSONOMY NOTE** |
| --- |
| Tags are deliberately operator-defined and informal. The standard does not mandate a vocabulary. Standard taxonomies (MeSH for biomedical, DDC for library classification, etc.) may be expressed as `TaxonomyDefinition` artefacts and shared via the corpus, but their adoption is always operator-voluntary. This preserves the expressiveness of personal knowledge organisation while enabling optional standardisation. |

# 17. Extension D: Shared Archiving

Extension D defines full **WARC** format alignment, **Memento Protocol** integration, and shared public archiving via content-addressed transports (BitTorrent / IPFS). It extends the Core corpus model (§7) with tooling interoperability for the web archival ecosystem and community-contributed shared archives for public stable sources.

§7.3 (Shared Archive) is the Core commitment; §14.2 is the Extension A operator-side interop layer. §17 documents the full Extension D scope: complete WARC interop, full Memento HTTP interface, and shared-swarm tooling. Extension D is **deferred** — Core ships content-addressed storage with `content_hash` and `archive_path` directly, without requiring WARC tooling interoperability.

## 17.1 WARC Alignment

The corpus snapshot format aligns with the WARC standard (ISO 28500:2017). The `warc_record_type` field maps directly to WARC record types:

- `RESPONSE` — a full archived copy of content. Equivalent to a WARC response record. The `archive_path` stores the content body.
- `REVISIT` — content has not changed since a prior snapshot. Equivalent to a WARC revisit record with `WARC-Refers-To` pointing to the prior snapshot. No content body is stored, eliminating redundant storage costs for unchanged sources.

Implementations may store corpus content in native WARC files, enabling interoperability with existing web archival tooling (Wayback Machine, warcio, Common Crawl pipelines). The corpus entry and snapshot metadata layer sits above WARC, adding Particles-specific fields (`mutability`, `extraction_status`, `entry_id`) that WARC does not carry.

## 17.2 Memento Protocol Alignment

Corpus entries align with the Memento Protocol (RFC 7089) as described in §7.6. Extension D additionally specifies a **Memento-compatible HTTP interface** over the corpus — endpoints for URI-R lookup, TimeMap retrieval, and URI-M dereferencing — enabling third-party Memento tooling to query a particle store's corpus as if it were a web archive.

| **MEMENTO HTTP INTERFACE** |
| --- |
| The Memento HTTP interface is Extension D, not Core. A Core-conformant implementation aligns its data shapes with Memento concepts (URI-R / URI-M / TimeMap) but is not required to expose them via HTTP. The interface is a v1.0 candidate deliverable per §13.1. |

## 17.3 Shared Public Archiving (BitTorrent / IPFS)

§14.2 documents the operator-side interop: `archive_location` schema, content_hash verification, ODRL gating. §17.3 documents the swarm-side tooling: contributing snapshots to a swarm, fetching from a swarm, governance for public stable sources.

| **SCOPE CONSTRAINT** |
| --- |
| Shared archiving applies only to `STABLE` and `APPEND_ONLY` public sources. `EPHEMERAL` sources MUST NOT be submitted to shared archives. `MUTABLE` sources require per-snapshot governance decisions before sharing. Archive governance for shared swarms is an implementation concern (OQ-10 still open); the spec defines the `archive_location` schema and the `content_hash` verification requirement only. |

# 18. Extension E: Multi-Agent Discourse Protocol

Extension E defines the multi-agent discourse protocol for exchanging particles between autonomous agents. It depends on Core, Extension A (extractor registry), and Extension B (source trust automation), and is **deferred** to a future major version (single-agent scope first).

Whitepaper §7.1 frames the user-facing vision; this section sketches the message-type catalogue so that any v2-conformant implementation that anticipates multi-agent use can preserve schema compatibility.

| **Message Type** | **Semantics** |
| --- | --- |
| `ASSERT` | Agent publishes a particle to the shared store or to a peer agent. |
| `CHALLENGE` | Agent requests justification for a particle, referencing specific uncertainty fields. The challenged agent must respond with `ASSERT` (updated evidence), `REVISE`, or `RETRACT`. |
| `REVISE` | Agent updates a prior particle. Sets `supersedes` on the new particle; marks prior `SUPERSEDED`. |
| `MERGE` | Agent proposes a reconciled particle from two `EPISTEMIC` particles with differing confidence. Merge semantics: trust-weighted noisy-OR per §6.9 (or Bayesian update treating each agent's confidence as evidence — to be decided when Extension E lands). |
| `ENDORSE` | Agent increases confidence in an existing particle based on corroborating evidence. Creates a new `ACTIVE` particle superseding the prior with updated confidence — or, when co-evidential links are active, adds a `CO_EVIDENTIAL` link instead of superseding (preserving each source). |
| `RETRACT` | Agent withdraws a prior particle. Sets status `RETRACTED`. Lazy propagation sets `PROVENANCE_STALE` on dependents per §6.6. |
| `CHECKPOINT` | Agent serialises the current shared epistemic state (particle set + context fingerprint per §16.1) for persistence or transmission to a new agent session. |

### Deferred work items

The following are catalogued in Appendix A and in whitepaper §7.1, listed here for traceability:

- Agent identity verification (cryptographic; aligns with §14.3 W3C VC signatures).
- Reputation tracking for agents (analogous to per-extractor `trust_weight` and `calibration_history`).
- Spam / adversarial particle detection (multi-agent extension of the threat model in §15.2).
- Incentive alignment for cooperative exchange in open systems.
- Ontology drift mitigations across agents (whitepaper Risk #5; partially addressed by context fingerprinting).

# Appendix A: Future Features

Features identified as potentially valuable but deferred beyond the current versioning horizon. Recorded here to preserve the ideas and ensure current design decisions do not foreclose them.

| **Feature** | **Description** | **Why deferred** |
| --- | --- | --- |
| Daily / scheduled Lint digest | A scheduled Lint pass producing a structured daily summary: new `INCONSISTENCY` count, `PROVENANCE_STALE` count, extraction quality trend, coverage gaps. Human-readable email/notification format alongside the JSON-LD report (§9.4). | Operational tooling. Lint is already designed for on-demand and programmatic use; digest format adds UI/notification infrastructure without changing core logic. |
| Adaptive re-fetch backoff | For `LAZY` corpus entries, exponential backoff on consecutive `REVISIT` streaks (no content change) to reduce fetch volume for stable sources. Floor bound prevents entries from becoming effectively frozen. | Complexity not justified at MVP scale. Fixed per-source-type re-fetch floor is sufficient (§7.5; resolved OQ-8). |
| `ACTION` particle type (GTD integration) | A `particle_type = ACTION` with GTD-compatible lifecycle states (`next_action`, `waiting`, `someday_maybe`, `done`), owner, due date, project reference. `ACTION` particles reference epistemic `CLAIM` particles via provenance to capture *"do X because of evidence Y"*. | Conflating task management with epistemic knowledge in Core would bloat the schema. `particle_type` is reserved in v2 for forward compatibility. See OQ-12 (§11). |
| Shared archive swarm tooling | CLI for contributing corpus snapshots to and retrieving from BitTorrent / IPFS swarms. Content_hash verification, governance policy enforcement for `STABLE` / `APPEND_ONLY` public sources. | Architecture is specified in §7.3, §14.2, §17. Tooling deferred — Extension D. |
| Spreading activation graph traversal | A query mode that follows provenance and `sequence_context` edges outward from a seed particle set, weighted by edge type and trust. Complementary to vector search; useful for *"blast radius"* and context-expansion queries. | Reference implementation deferred. The §9.3 navigation model favours embedding-based retrieval as the primary primitive; spreading activation is a secondary mode for advanced use cases. |
| Extension F: Privacy and Consent | Normative privacy controls for regulated deployments involving personal health, financial, or identity data. Would specify: mandatory `EPHEMERAL` handling rules for defined data categories; GDPR / CCPA deletion propagation through provenance chains; consent tracking as a first-class corpus entry metadata field; audit log retention and expungement requirements. | Acknowledged as a gap for production deployments involving personal data. Deferred pending engagement with privacy / regulatory stakeholders. The Core privacy primitives (`EPHEMERAL` in §7.4, ODRL in §10.2, `author_id` in §6.5, allowlists in §14.6) and the §7.4 Extension F callout are the current placeholder; whitepaper §3.10 mentions Extension F as future work. |
| Taxonomy-aware retrieval index | A dedicated index structure over `TaxonomyDefinition` tag hierarchies enabling efficient subtree expansion at query time. The §16.2 design is shipped (v0.25.0); the index optimisation is deferred. | Basic tag filtering is feasible without a dedicated index at MVP scale. Index becomes necessary at > 10⁵ tagged particles. |
| Multi-agent trust model | Full agent-to-agent trust specification: agent identity verification, reputation tracking, adversarial particle detection, incentive alignment. Extends the extractor trust model (§14.6) to autonomous agents in open multi-agent deployments. | Deferred with Extension E (§18). Whitepaper §7.1 frames the direction. |
| Operator-defined retrieval routing tables | User-defined navigation structures over the particle store that reflect the operator's mental model of their domain. Supplements semantic search with explicit conceptual hierarchy for improved recall on personal-vocabulary queries. | Conceptually related to `TaxonomyDefinition` (§16.2) but distinct: routing tables govern retrieval traversal order, not tag labelling. Deferred pending operator feedback on taxonomy-aware retrieval adoption. |
| `CONTRADICTS` link type | Counterpart to `CO_EVIDENTIAL` (§6.10). Persists semantic contradiction as a first-class link between particles, in addition to the existing `INCONSISTENCY` particle mechanism (§6.6). | Sketched as deferred. The `INCONSISTENCY` particle mechanism already provides the lifecycle hook; whether to also persist as a link is an open design question with no immediate operational driver. |
| Automatic co-evidential link creation at extraction time | An extension to the general extractor that automatically emits `CO_EVIDENTIAL` links (§6.10) across particles from different sources during a single batch extraction, rather than waiting for the `L-IDX-01` lint pass to surface candidates. | Sketched as deferred. The lint-based path is shipped first because it allows operator review of each link before persistence. |
| Cross-language co-evidence | Two particles asserting the same claim in different languages — e.g. English and German — are conceptually co-evidential. Embedding models that span languages support this; the threshold tuning needs separate work. | Sketched as deferred. Out of scope for the v1 claim-identity primitive; multilingual embedding evaluation is a research direction. |
| Compound trust predicates | Current `SourceRef` types in `SourceTrustStatement` are atomic — `SOURCE_TYPE` *or* `CORPUS_ENTRY` *or* `AUTHOR`. Operators are likely to want *compound* predicates that combine scopes, e.g. *"within this organisation's repositories, trust verified maintainers over anonymous contributors"* — a per-author rule scoped to a corpus subset. The current model expresses this only by writing one trust statement per (author × organisation) pair. | Out of scope for v0.3; reconsider when an operator surfaces a concrete need. Extends the existing trust model rather than rewriting it (likely a new `SourceRef` type like `AUTHOR_IN_CORPUS_SCOPE`, plus a small predicate language). |
| HTML / Wikipedia article chunk-hash carry-forward | Chunk-hash carry-forward is shipped for Reddit and GitHub via `extract_with_carry_forward()` — both have domain-specific chunk units (body + comment groups) where unchanged units hash identically across re-deposits. The general extractor's `WEB_PAGE` path (which handles Wikipedia, news articles, and arbitrary HTML via the generic-HTTP importer) does **not** route through `extract_with_carry_forward()`. Its `_extract_html_chunked()` splits on **line boundaries** at a character budget (~15K), not on paragraph or HTML-block boundaries; a minor edit anywhere in a Wikipedia article triggers full re-extraction of every chunk. | A fix requires three pieces: (1) a structural chunker that breaks on paragraph (`\n\n`) or HTML-block boundaries instead of line boundaries, so unchanged paragraphs produce stable chunks; (2) a normalisation pass before hashing to absorb cosmetic noise (Wikipedia `[edit]` markers, generation timestamps, link attribute drift) that otherwise causes spurious hash mismatches; (3) wiring `GeneralExtractor._extract_html_chunked()` to `extract_with_carry_forward()`. v0.4 candidate; would have the largest impact of any carry-forward extension because Wikipedia is the canonical large-stable-localised-edits source. |

# Appendix B: Core Implementation Checklist

A Core-conformant implementation must complete every item in this checklist and nothing more. Extension sections (§14–18) may be ignored entirely without affecting Core conformance. The checklist is normative.

| **v0.2 CORE CONFORMANCE ACHIEVED** |
| --- |
| As of reference SDK release **v0.15.1**, every item in this checklist is implemented and tested. The reference SDK is Core-conformant. Sections marked *Deferred deliverables* below are items originally scoped to v0.2 Core that have moved to v0.3; they are not blockers for Core conformance. |

| **THE PRESSURE TEST** |
| --- |
| A small team should be able to implement Core in a single quarter using only this checklist and the Core sections of the spec. If any item on this list requires reading an Extension section to understand, that is a spec defect to be corrected. |

### 1. Source Corpus

- Implement corpus Deposit operation (§9.1): accept any source material, assign entry_id, compute content_hash (SHA-256), write Snapshot with warc_record_type = RESPONSE and extraction_status = PENDING.

- Support corpus entry mutability classes: STABLE, MUTABLE, APPEND_ONLY, EPHEMERAL (§7.4). Apply correct extraction behaviour on new snapshots for each class.

- Implement lazy re-fetch for entries with fetch_policy = LAZY (§7.5): Tier 1 (ETag/Last-Modified) and Tier 2 (content hash comparison). Write REVISIT snapshots for unchanged content. Default re-fetch floor: 1 hour for WEB_PAGE, 24 hours for DATA_EXPORT, 7 days for STABLE (see OQ-8, resolved).

- Store corpus content as content-addressed blobs by SHA-256. Corpus entries and snapshot metadata stored in queryable form (relational or document store).

### 2. Particle Schema (Core fields only)

- Support all Core particle fields: id, content, confidence (with value, variance, calibration_source, calibration_method, calibration_ref), uncertainty_nature, provenance (ProvenanceRef array), extractor_ref (omitted only for operator-asserted particles), asserted_by, asserted_at, status, status_reason, schema_version. Particle_type defaults to CLAIM.

- Implement the two-quantity confidence separation (§6.3): store confidence.value immutably, as calibrated at creation time (when the extractor carries an active calibration, store the calibrated value stamped CALIBRATED_BENCHMARK with calibration_method and calibration_ref provenance); compute effective_confidence at query time. Never write derived quantities back to the particle store.

- Implement all status values and transitions per §6.6 normative table. Set status_reason on every status-changing operation.

### 3. Extraction

- Ship a general-purpose extractor that accepts any source_type, produces EXTRACTOR_DIRECT confidence particles, and implements the ExtractorInterface (§6.8): extract() and accepts() methods.

- Implement Extract operation (§9.2): retrieve corpus snapshot, call extractor, apply conflict resolution ladder (§6.6), write ACTIVE particles or INCONSISTENCY particles as appropriate.

- Apply calibration_source = EXTRACTOR_DIRECT to all general extractor outputs. Implement temperature scaling calibration utility for operators who want CALIBRATED_BENCHMARK particles.

### 4. Query

- Implement Query operation (§9.3): semantic search over ACTIVE particles; apply effective_confidence (confidence.value only for Core — extractor and source trust weights are Extension features); rank and return results; include coverage_gap disclosure for PENDING corpus entries; apply schema_version mismatch guard.

- Support min_confidence, uncertainty_nature, and recency_window filter parameters.

- Generate audience-appropriate natural language response with confidence disclosure.

### 5. Lint

- Implement all structural Lint checks (§9.4): staleness detection (valid_until), retraction propagation (PROVENANCE_STALE cascade), corpus link integrity, confidence decay flagging, orphan detection, extraction quality report, pending extraction report, schema version audit.

- Implement semantic Lint: contradiction detection using structured particle inputs; granularity violation detection.

- Produce machine-readable (JSON-LD) and human-readable (Markdown Bridge) lint report.

### 6. Review

- Implement Review operation (§9.6) in v0.2 annotation-only mode: present INCONSISTENCY particles; support four resolution actions (PREFER A, PREFER B, BOTH VALID, DEFER); write REVIEW particle recording outcome; write SourceTrustStatement on PREFER resolutions. No automatic cascade (Extension B).

- Surface author_id and author_role in Review UI for UGC corpus entries.

- SourceTrustStatements: implement schema including policy_provenance field (§6.5). Enforce demotion-only rule.

### 7. Reindex

- Implement Reindex operation (§9.5): identify scoped corpus entries, enqueue rate-limited Extract jobs, supersede prior particles from old extractor versions, run post-Reindex Lint pass.

### 8. Conformance

- Validate all particles against the five normative SHACL shapes (v0.1 deliverable + SubjectShape, 0.52.1): ParticleShape, SubjectShape, CorpusSnapshotShape, ProvenanceChainShape, TrustStatementShape.

- Implement schema validator: flag particles with missing Core fields, invalid status transitions, or schema_version mismatches.

- Publish extraction quality dashboard: calibration_source distribution, EXTRACTOR_DIRECT fraction, pending extraction count, lint findings summary.

- Implement Markdown Bridge renderer: render particle metadata as human-readable annotations in markdown output.

### What is explicitly NOT required for Core conformance

- Context fingerprinting (§16.1) — Extension C
- `TaxonomyDefinition` and tag-based retrieval (§16.2) — Extension C
- Extractor registry beyond a placeholder; trust weight machinery; RFC 2119 applicability selection (§14) — Extension A
- `SourceTrustStatement` automatic cascade (§15) — Extension B
- Shared-swarm tooling (§17.3) — Extension D
- Memento HTTP interface over the corpus (§17.2) — Extension D
- Multi-agent discourse protocol (§18) — Extension E
- Spreading activation graph traversal — Appendix A
- Adaptive re-fetch backoff — Appendix A

### Deferred deliverables (originally scoped to v0.2 Core; now v0.3)

These items appeared in the original v1-techspec Appendix B as v0.2 deliverables but have been intentionally re-prioritised to v0.3 to focus the Core release on the shipping core loop. None are blockers for Core conformance.

- **LangChain adapter.** The Core SDK exposes a clean Python API and a CLI; framework adapters are deferred until the v0.3 work surfaces.
- **BenchmarkSuite runner CLI.** Shipped in v0.21.0 as `particles extractor benchmark <extractor-id>` consuming the frozen §13.3 `BenchmarkSuite` schema. One numismatic seed suite is bundled in `tests/benchmark/suites/`; TruthfulQA and HaluEval wrappers are deferred to follow-up community work.
- **Retrospective LLM-Wiki parser.** Enables the §9.4 "lint runs on day one against existing markdown" workflow. Shipped in v0.31.1 as `particles import vault`: existing vaults are deposited unmodified as `LOCAL_MARKDOWN` corpus sources and converted to particles by the standard extraction pass. The originally-sketched deterministic treat-markdown-as-low-confidence-particles mode was rejected in favour of extraction; see the §9.4 callout for the rationale.
- **Per-Subject wiki article exporter** (§10.4). Shipped in v0.20.0. Refactored in v0.22.0 so the article-rendering machinery is now shared across exporters via `particles/exporters/article_synthesis.py`; the Obsidian exporter consumes it via `--with-synthesis`.

# Appendix C: Reference Implementation Guide

This appendix records technology preferences and implementation decisions for the **reference** Python SDK. It is not part of the standard — conformant implementations may use any technology stack. It is intended to orient contributors and to give Claude Code sufficient context to begin implementation without ambiguity.

Per the project's versioning policy (root `AGENTS.md`), the technology stack itself is governed by the reference implementation Python stack decision; operator configuration is governed by the consolidated YAML config decision. When the prose below disagrees with those records, the records are authoritative.

## C.1 Language and Runtime

| **Concern** | **Decision** | **ADR** | **Rationale** |
| --- | --- | --- | --- |
| Language | Python 3.11+ | 0030 | Type hints, match statements, `tomllib`, native async. |
| Package manager | uv | 0030 | Fast resolution; lockfile. Poetry / pip are acceptable alternatives. |
| Type checking | mypy in strict mode | 0030 | Schema has many optional / enum fields; strict typing prevents an error class early. |
| Testing | pytest + hypothesis | 0030 | pytest for unit/integration; hypothesis for property-based testing of schema round-trips and status-transition invariants. |
| Configuration | YAML via `particles/config.py` Pydantic models | 0055 | `config.yaml` (gitignored) overrides compiled defaults; env vars override `config.yaml`. Secrets remain env-var-only, read through the single `particles/secrets.py` seam (`ANTHROPIC_API_KEY`, `NUMISTA_API_KEY`, `GITHUB_API_KEY`, `NOTION_API_KEY`, `PARTICLES_API_KEY`, `PARTICLES_ENGINE_TOKEN`, `PARTICLES_LLM_API_KEY_<NAME>` per named completion provider (legacy `PARTICLES_LOCAL_LLM_API_KEY` honoured for `local`), `PARTICLES_OTEL_EXPORTER_HEADERS`). |

## C.2 Storage Backends

| **Subsystem** | **Default choice** | **Notes** |
| --- | --- | --- |
| Corpus content store | Local filesystem (content-addressed by SHA-256), with S3-compatible interface as an optional backend. | WARC files written to corpus/{entry_id}/{snapshot_id}.warc.gz. Content addressed: blobs stored at blobs/{sha256[:2]}/{sha256}. |
| Corpus metadata store | SQLite for development; PostgreSQL for production. | Snapshot metadata, extraction_status, fetch timestamps. SQLAlchemy ORM with Alembic migrations. |
| Particle store | SQLite + sqlite-vec for development; PostgreSQL + pgvector for production. | Graph edges (provenance, sequence_context, supersedes) as a self-referential adjacency table. Vector index on content embeddings for semantic search. |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 (local, no API dependency). | 384-dimensional embeddings — the standard's **reference profile** (§8.5). Swap to a larger model for production by declaring a new `embedding_profile`. The structured `embedding_profile = {model, dim, normalization}` MUST be recorded in particle-store metadata (§8.5, normative — not merely this non-normative appendix) — changing the profile requires re-embedding. |
| Trust policy store | Same database as particle store (separate table). | SourceTrustStatements are rows with all schema fields including policy_provenance. |

## C.3 Corpus Fetching

| **Concern** | **Decision** |
| --- | --- |
| HTTP client | httpx with async support. Respects ETag and Last-Modified headers automatically. |
| WARC writing | warcio library. Writes RESPONSE and REVISIT records per §7.6 specification. |
| Re-fetch scheduling | APScheduler for background re-fetch jobs. Default re-fetch floor: 1 hour for WEB_PAGE; 24 hours for DATA_EXPORT; 7 days for STABLE sources (see OQ-8). |
| Rate limiting | Configurable per-domain rate limit. Default: 1 request/second per domain. Robots.txt respected. |

## C.4 Extraction

| **Concern** | **Decision** |
| --- | --- |
| General extractor | LLM-based. Prompt instructs claim-granularity extraction with confidence self-assessment. Produces EXTRACTOR_DIRECT particles. Optionally emits `valid_until` for genuinely date-bounded claims, under-emission-biased (§9.2). |
| LLM provider port | Every chat/completion call routes through a `CompletionProvider` port (`particles/llm/`): a Protocol + registry with per-purpose provider/model selection from `config.llm` (purposes: extraction, semantic lint, query response, synthesis, benchmark). The Anthropic adapter is the default; no model string is hardcoded at a call site. Calibration records are keyed by (extractor, provider/model). |
| Extraction concurrency | asyncio with a semaphore limiting concurrent LLM calls. Default: 5 concurrent extractions. |
| Calibration utility | scipy.optimize for temperature scaling. Requires a calibration dataset; ships with a small general-domain calibration set for bootstrapping. |
| Extractor registry | JSON file on disk for v0.2 Core. Registry entries include extractor_id, version, applicability clauses, and calibration_history. Upgrade path to a hosted registry in v0.3. |

## C.5 Query and Lint

| **Concern** | **Decision** |
| --- | --- |
| Semantic search | pgvector cosine similarity (production) or numpy cosine similarity over in-memory vectors (development). The metric is the normalized, `[0, 1]`-clamped cosine pinned in §8.5; top-k retrieval with configurable k (exact ordering at the margins is profile-relative, §8.5). |
| LLM for semantic lint | Routed through the CompletionProvider port (`semantic_lint` purpose) for contradiction detection and granularity violation checks. Structural lint checks (staleness, retraction propagation, corpus integrity) run without LLM. |
| Markdown Bridge | Jinja2 templates rendering particle metadata as Obsidian-compatible callout blocks. |
| JSON-LD serialization | pyld library for JSON-LD processing. Canonical @context loaded from the v0.1 artifact once published. |
| SHACL validation | pyshacl library. Shapes loaded from the v0.1 artifact. Validation runs on write (optional, configurable) and on lint pass (always). |

## C.6 API Layer

| **Concern** | **Decision** |
| --- | --- |
| Framework | FastAPI with async endpoints. Automatic OpenAPI documentation. |
| Authentication | API key authentication for v0.2. OAuth2 / OIDC planned for multi-agent v0.3. |
| Endpoints (Core) | POST /corpus/deposit; GET /corpus/{entry_id}; POST /extract; POST /query; POST /lint; GET /lint/report; POST /review; POST /reindex; GET /health. |
| CLI | Typer-based CLI wrapping the same operations. Primary interface for local personal knowledge base deployments. |

## C.7 Project Structure

The directory tree this section used to carry described the v0.2
sketch and drifted badly as the SDK grew (the Client/Engine
carve split `extraction/` from `ingest/`; query, lint, and the
exporters became packages rather than single files; `bridge/` was
absorbed into `exporters/`). Rather than maintain a second copy, this
appendix defers to the canonical map: the **architecture overview in
the repository's root `AGENTS.md`**, which carries the current
per-package layout with one-line descriptions and the Client/Engine
boundary annotations, and is kept in lockstep with the code by the
repo's documentation-maintenance rules. Appendix C is non-normative;
the pointer is the contract.

## C.8 Implementation Order (Suggested)

The following order minimises rework and ensures each layer has a stable foundation before the next is built. Each phase produces a runnable, testable artifact.

- Phase 1 — Schema and storage: Pydantic models for all Core particle fields; status/status_reason enums; SQLAlchemy models for corpus metadata and particle store; status transition validator that enforces §6.6 normatively.

- Phase 2 — Corpus: Deposit operation; WARC writing with warcio; content-addressed blob store; lazy re-fetch with ETag and hash comparison; REVISIT record generation.

- Phase 3 — Extraction: General extractor (LLM prompt + response parsing); Extract operation with conflict resolution ladder; EXTRACTOR_DIRECT confidence assignment; temperature scaling calibration utility.

- Phase 4 — Query: Semantic search with embeddings; effective_confidence computation; coverage_gap disclosure; schema_version mismatch guard; natural language response generation with confidence disclosure.

- Phase 5 — Lint: All structural checks; semantic contradiction detection; granularity violation detection; JSON-LD and Markdown Bridge report output.

- Phase 6 — Review: INCONSISTENCY particle presentation; four resolution actions; REVIEW particle writing; SourceTrustStatement creation (annotation-only, no cascade).

- Phase 7 — Reindex: Scoped re-extraction jobs; rate limiting; post-Reindex Lint pass.

- Phase 8 — API and CLI: FastAPI endpoints; Typer CLI; SHACL validation on lint pass; extraction quality dashboard endpoint.

- Phase 9 — Conformance: SHACL shape validation against v0.1 artifacts once published; BenchmarkSuite runner CLI; conformance test suite.

# Appendix D: Implementation Discoveries

Things the original v1 spec did not know that the reference implementation surfaced. The most valuable thing a v2 spec can carry forward for the next implementer.

### D.1 Chunked extraction is unavoidable for UGC sources

Reddit threads and gist comments routinely exceed single-LLM-call context windows once you raise the comment cap. The adaptive chunking pattern is the dominant operational mode for any source with user-generated discussion. Don't try to extract the whole thread in one call — page through it.

### D.2 Subject canonicalisation is harder than it looks

Naive name matching produces phantom subjects, prefix-expansion false positives (`"POET"` collapsing with `"POET Technologies Inc."` correctly but also with `"POET"` the poetry term), and word-continuation false positives. The Subject resolver's ladder (§6.7) — local match → external ontology → bare local — was not initially obvious; v1 implicit. The `PHANTOM_SUBJECT` lint check (§9.4) and Wikidata link confidence (§6.3) emerged from these failure modes.

### D.3 `EXTRACTOR_DIRECT` dominates `calibration_source` in practice

`EXTRACTOR_DIRECT` is the dominant calibration source today; `CALIBRATED_BENCHMARK` is theoretical until the benchmark suite ships (§13.3). Operators should treat `effective_confidence` numbers from `EXTRACTOR_DIRECT` particles as ordinal (this is more confident than that) rather than calibrated absolute values. Whitepaper §3.1.3 makes this commitment publicly.

### D.4 The Karpathy gist comes full circle

The whitepaper's §1.1 motivating example is Karpathy's LLM-Wiki gist. The GitHub-gist extractor now ingests that very gist — including its comment section, which contains substantial practitioner critique — and produces particles from it. The standard is testable against the artefact that motivated it. This is the cleanest worked-example for demos.

### D.5 `gh/{login}` → `@{login}` content normalisation

The pattern of using a token-shaped prefix (`gh/karpathy`) to coax the LLM into emitting subject-eligible names, then rewriting to the canonical form (`@karpathy` or `github:karpathy`) in a post-extraction pass, is a discovered technique worth documenting. It generalises: pre-extraction normalisation that makes the LLM's job easier without forcing the operator's vocabulary into the particle content.

### D.6 Reddit threading is deeper than one level

The original Reddit extractor walked comment threads to depth 1. v0.15.x walks BFS to depth N with a configurable cap. The standard SHOULD NOT over-constrain extraction-depth choices for UGC sources; per-extractor configuration is the right surface.

### D.7 Reindex with chunk-hash carry-forward is the dominant re-extraction pattern

Full re-extraction (re-running the LLM on every chunk) is the fallback; chunk-hash carry-forward (§9.5) is the default. Most operational reindex runs touch only a handful of chunks. The chunk-hash surface (`provenance.chunk_hash` on each particle) was not in v1 — it was discovered as the only way to keep reindex tractable at scale.

### D.8 Operators want per-Subject prose, not just per-particle annotations

v1 §10 (Markdown Bridge) was framed as a per-particle annotation primitive. Operators consistently asked for *per-Subject prose synthesis* — *"give me an article about Subject X with every claim cited"* — which is a different artefact entirely. The Wiki Article Exporter (§10.4) was written in response. The Markdown Bridge remains the primitive; the wiki exporter is the user-facing read path (whitepaper §4.2).

### D.9 Operator review surfaces author identity, not just source identity

For UGC sources, the `INCONSISTENCY` resolution that operators want to encode is almost always *"trust this author"* or *"distrust this author"* rather than *"trust this source domain"*. The author-scoped `SourceTrustStatement` design (§6.4, §6.5) was a v1 sketch that the implementation pushed into production-grade. The Review UI's offer to persist author-scoped statements (§9.6) is the load-bearing UX detail.

### D.10 The whitepaper / techspec split is a sustained editorial discipline

the published split is whitepaper + techspec. The whitepaper has been through one major version transition (v1 → v2) plus three review-driven revision passes; each pass surfaced *some* status leakage from whitepaper into techspec territory and vice versa. The discipline is not "split once, done" — it's an ongoing editorial pass with every spec change.

---

# References

- **LLM-Wiki. **Andrej Karpathy. GitHub Gist, April 4, 2026. [https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

- **Precise Semantics for Uncertainty Modeling (PSUM), Version 1.0. **Object Management Group. OMG Document formal/24-12-03. June 2025. [https://www.omg.org/spec/PSUM/1.0](https://www.omg.org/spec/PSUM/1.0)

- **Structured Assurance Case Metamodel (SACM), Version 2.3. **Object Management Group. [https://www.omg.org/spec/SACM/2.3](https://www.omg.org/spec/SACM/2.3)

- **Structured Metrics Metamodel (SMM), Version 1.2. **Object Management Group. [https://www.omg.org/spec/SMM/1.2](https://www.omg.org/spec/SMM/1.2)

- **PROV-Overview: An Overview of the PROV Family of Documents. **W3C Working Group Note, April 2013. [https://www.w3.org/TR/prov-overview/](https://www.w3.org/TR/prov-overview/)

- **The Anatomy of a Nanopublication. **P. Groth, A. Gibson, J. Velterop. Information Services & Use, 30(1–2), 2010. DOI 10.3233/ISU-2010-0613. [https://content.iospress.com/articles/information-services-and-use/isu613](https://content.iospress.com/articles/information-services-and-use/isu613)

- **Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications. **T. Clark, P. N. Ciccarese, C. A. Goble. Journal of Biomedical Semantics, 5:28, 2014. DOI 10.1186/2041-1480-5-28. [https://jbiomedsem.biomedcentral.com/articles/10.1186/2041-1480-5-28](https://jbiomedsem.biomedcentral.com/articles/10.1186/2041-1480-5-28)

- **The Memento Framework (RFC 7089). **H. Van de Sompel, M. Nelson, R. Sanderson. IETF, December 2013. [https://datatracker.ietf.org/doc/html/rfc7089](https://datatracker.ietf.org/doc/html/rfc7089)

- **WARC File Format, Version 1.0 (ISO 28500:2017). **International Internet Preservation Consortium. [https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.0/](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.0/)

- **The Society of Mind. **Marvin Minsky. Simon & Schuster, 1986. ISBN 978-0-671-65713-0.

- **Model Context Protocol. **Anthropic, 2024. [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)

- **Key Words for use in RFCs to Indicate Requirement Levels (RFC 2119). **S. Bradner. IETF BCP 14, March 1997. [https://datatracker.ietf.org/doc/html/rfc2119](https://datatracker.ietf.org/doc/html/rfc2119)

- **BitTorrent Protocol Specification (BEP 3). **B. Cohen. BitTorrent.org, 2008. [https://www.bittorrent.org/beps/bep_0003.html](https://www.bittorrent.org/beps/bep_0003.html)

- **Verifiable Credentials Data Model 2.0. **W3C Recommendation, 2024. [https://www.w3.org/TR/vc-data-model-2.0/](https://www.w3.org/TR/vc-data-model-2.0/)

- **TruthfulQA: Measuring How Models Mimic Human Falsehoods. **S. Lin, J. Hilton, O. Evans. ACL 2022. [https://aclanthology.org/2022.acl-long.229/](https://aclanthology.org/2022.acl-long.229/)

- **HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models. **J. Li et al. EMNLP 2023. [https://aclanthology.org/2023.emnlp-main.397/](https://aclanthology.org/2023.emnlp-main.397/)

- **On Calibration of Modern Neural Networks. **C. Guo, G. Pleiss, Y. Sun, K. Q. Weinberger. ICML 2017. (Temperature Scaling reference.) [https://proceedings.mlr.press/v70/guo17a.html](https://proceedings.mlr.press/v70/guo17a.html)

- **Shapes Constraint Language (SHACL). **W3C Recommendation, July 2017. [https://www.w3.org/TR/shacl/](https://www.w3.org/TR/shacl/)

- **ODRL Information Model 2.2. **W3C Recommendation, February 2018. [https://www.w3.org/TR/odrl-model/](https://www.w3.org/TR/odrl-model/)
