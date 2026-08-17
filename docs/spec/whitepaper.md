# Particles

**An Open Standard for Structured Agent Knowledge**

| Field | Value |
|---|---|
| Document Type | Whitepaper |
| Version | 2.4 — Draft |
| Status | For Review |
| Date | Updated July 2026 |
| Classification | Public / Open Standard |

---

## Reader's Guide

This document is the **whitepaper** — Part I of the Particles
publication. The Technical Specification (Part II) is a separate
document for implementers. A companion Implementation Status report
catalogues what the reference SDK actually ships against the design
described here.

| Document | Contents | Intended Reader |
|---|---|---|
| Whitepaper (this document) | Motivation, key architectural shift, design principles, primary use cases, known risks, why incremental alternatives are insufficient. Written to invite feedback. | Researchers, framework authors, potential collaborators, practitioners evaluating the approach. |
| Technical Specification (`spec/technical-specification.md`) | Formal particle schema, source corpus model, operation definitions, storage model, serialization, success metrics. | AI engineers implementing the standard, including automated code generation tools. |
| Roadmap (`roadmap.md`) | Per-milestone gate tables of RFC 2119-classified work items (MUST / SHOULD / MAY / SHOULD NOT / MUST NOT) with stable IDs for cross-reference — the done column (`done · ADR · version`) is the implementation-status record — plus the forward queue of what ships next. Item rationale lives in the ADR or PDR each row names. | Anyone evaluating the project's maturity. |

Appendices in the techspec provide a comparison table, standards
alignment map, implementation discoveries, and full
references. Readers already familiar with the motivation may go
directly to the techspec.

---

## What Particles Is

**The standard.** Particles is an open standard and reference SDK for
storing AI agent knowledge as *claim-granularity particles* —
natural-language sentences paired with structured metadata for
confidence, provenance, and uncertainty. The standard defines the
particle schema, the source-corpus model, the extraction protocol, and
a small set of operations (deposit, extract, query, lint, review,
reindex).

**What kind of standard.** Particles is a *minimal interoperable
substrate* for claim-granularity agent knowledge — narrower than a
*formal-ontology* knowledge graph (RDF / SPARQL), more structured
than augmented markdown, and optimised for LLM-native extraction
and synthesis. Structurally it is a sparse property graph over
prose claims; the §6 comparison table elaborates the relationship
to RDF / context-graph / LLM-Wiki stacks. It is not a universal
knowledge representation, not a replacement for vector search, and
not a multi-agent operating system. It is the smallest schema and
protocol that makes provenance, confidence, and lifecycle
inspectable per claim. Adjacent context-graph products
(Palantir-Foundry, Procedural Knowledge Ontology) model
*organisational decision-making* rather than *source-derived
claims with provenance* — complementary primitives at different
layers of the knowledge stack, not competing approaches to the
same problem.

**Terminology.** A *claim* is a single falsifiable assertion in
natural language — *"Acme acquired Widget"*, *"the half-life of
caesium-137 is 30.17 years"*. A *particle* is a claim plus its
metadata envelope: confidence, calibration source, provenance,
uncertainty classification, subjects, lifecycle status, and the
extractor that produced it. The whitepaper uses *particle* when the
metadata matters and *claim* when discussing the underlying
assertion. *Assertion* is avoided as a term of art.

**The problem it solves.** Existing approaches (classic RAG, LLM-Wiki)
store synthesised knowledge as prose. Prose cannot carry the signals —
confidence, provenance, validity conditions — needed for reliable
consistency checking, retraction propagation, or audience-tailored
rendering. Particles preserves those signals by inverting the
architecture: claims are stored with their structured metadata; prose
is generated at query time, tailored to the question and audience.

**The epistemic stance.** Particles is built on a single unifying
premise: there is no fundamental distinction between a fact and an
opinion — only *claims that are true for a group of observers, for a
period of time*. *"The 1932 quarter weighs 6.25 g"* and *"the 1932
quarter is the most beautiful US coin"* differ not in kind but in
observer scope: the first holds for very nearly every observer; the
second holds for some observers, and its holders can be named. And
even the plainest facts carry temporal scope: *"Pluto is a planet"*
was true for every observer for seventy-six years, until the 2006 IAU
reclassification changed what was true without changing Pluto. A
knowledge system that forces an early fact-or-opinion classification
discards exactly the information — who asserts this, on what
evidence, valid until when — that a reader needs to decide what the
claim is worth *to them*. Particles therefore stores every claim the
same way — a natural-language assertion wrapped in attribution
(`asserted_by`), provenance, confidence with calibration provenance,
and temporal scope (`asserted_at`, `valid_until`) — and computes what
is "true enough to render" at read time, through the reader's own
trust policy.

**Two scopes, two mechanisms — facts on the particle, judgments in
the lens.** The particle carries temporal *facts*: when the claim was
asserted, when its source published it, and any validity the source
itself asserted (`valid_until` expires time-bounded claims lazily,
§3.7); the snapshot-anchored corpus pins every claim to the moment
its source was captured. How those facts should *weigh* on belief is
judgment, and judgment is observer scope, applied at read time and
never stored: trust in sources and authors (techspec §6.4), trust in
extractors, and recency decay — how fast a forum thread's evidential
value fades is an opinion about the world, not a property of the
claim. (Today the decay policy is operator-level; folding it into the
shareable lens, scoped down to individual communities, is the natural
completion — deferred.) Observer scope is deliberately
*not* carried on the particle. It emerges at read time from the trust
layer — though today that layer expresses graduated *distrust* only;
the positive half, recording who *holds* a claim, is the endorsement
layer (deferred). Stamping *"true for group G"* onto stored
claims would fragment the substrate and reproduce, one level down,
the edit wars this design is meant to dissolve;
keeping the substrate shared and the perspectives separate is the
load-bearing choice (the *substrate-plus-lens* invariant;
shareable trust lenses). The substrate is observer-neutral;
perspective is a lens applied at query time, never a property burned
into the stored claim.

**The lineage, and the missing enabler.** The premise is not new —
what was missing was a way to act on it. Cyc's *microtheories*
conceded in the 1980s that a usable knowledge base must hold mutually
inconsistent assertions, each true within a context. Wikidata's data
model calls its statements *claims* — ranked, referenced, and
deliberately never adjudicated as true. Nanopublications have
published more than ten million claim-granularity assertions with
formal provenance since 2010. Each solved part of the problem; none
had an economical way to populate its formalism from prose, and none
made the observer dimension — *whose* claim, weighted by *whose*
trust — a first-class runtime quantity. LLMs supply the populator;
the Particles trust model supplies the observer scope. That
conjunction is the standard's reason to exist now, when both prior
attempts at it stalled.

**What this does not mean.** Treating facts and opinions uniformly
does not flatten them into relativism. The distinction is *recovered
as a measurement* rather than imposed as a label: a claim whose
effective confidence is invariant across every credible trust policy
behaves as a fact; a claim whose effective confidence varies sharply
across policies is visibly contested, with the holders of each
position attributed and cited. The system does not adjudicate; it
renders disagreement inspectable. This per-claim *contestedness*
signal is the max−min spread of effective confidence across the
viewer's policy set (the local policy plus each adopted lens),
computed at read time and surfaced in query responses, prose
exporters, and lint — disclosure, never a discount on confidence
(§6.9 of the technical specification).

**The frame.** Particles is not anti-markdown. It is anti-*markdown
as the source of truth*. The particle store is the canonical
structured substrate; the per-Subject wiki articles
(`particles export wiki`, `particles export obsidian`,
`particles export logseq`) are a compiled, cached, citation-validated
read-view *over* the substrate, rebuildable at any time from
inspectable claims. Read-heavy workloads serve the compiled view; the
particle store is consulted when the view doesn't exist yet, when a
hash change invalidates it, or when an operation cannot work from
prose (lint, conflict detection, retraction propagation). §2.2
elaborates this trade-off.

**Primary use cases.** The first-party use case is the substrate
itself: a git-like ledger for what an AI system believes — every
piece of knowledge a single sourced, dated, confidence-scored claim
that is never edited or deleted, only superseded, retracted, or
disputed in the open, with trust, doubt, and staleness applied as a
lens at query time, never baked into the record. Two products
surface that ledger for humans: a *linter* for AI engineers that
detects contradictions, stale claims, and broken provenance in
existing knowledge bases, and *wiki article views* for everyone
else — per-Subject prose synthesised from particles, with every
claim cited back to its source and confidence visible per claim.

**Design vs. implementation.** This whitepaper describes the
standard's *design*. The reference SDK at this writing
implements the core loop end-to-end and most of the capabilities
described here; the specific gaps that remain are catalogued in
`roadmap.md`. Where this whitepaper describes a capability, the
standard requires it; not every capability is shipped today.

**Stability at 1.0.0.** The 1.0.0 release establishes the
standard's compatibility contract. Four commitments:

- **Namespace-frozen at 1.0:** the *names* of schema fields, the
  `RelationType` enum kinds, the operation set (`deposit` /
  `extract` / `query` / `lint` / `review` / `reindex`), and the HTTP
  endpoint paths and response shapes. Renames or removals require a
  major-version bump.
- **Behavior-additive at minor versions:** new optional schema
  fields, new RESERVED → ACTIVE transitions of existing enum kinds,
  new exporter formats, new domain-specific extractors, new lint
  checks. A particle stored by a 1.x SDK MUST read cleanly under any
  1.y SDK where `y > x` without re-extraction. The reverse direction —
  a particle stored by a 1.y SDK read by a 1.x SDK — applies the
  conventional unknown-fields-ignored rule: unknown enum values surface
  as warnings rather than read failures, and unknown optional fields
  are dropped. Forward-only compat is the guarantee; graceful read
  on slightly-newer data is the conventional courtesy.
- **Extension via ADR amendment:** the documented extension seams
  (the `ParticleType` enum the `RelationType` registry
  the `properties` prefix registry) are
  the supported paths for additions. Each new entry lands as an ADR
  amendment specifying the emitter, consumer surface, and
  interoperability rationale before any code can emit the value.
- **Corpus durability:** the corpus archive (raw sources +
  SHA-256-addressed blobs + snapshot metadata) survives every
  upgrade, including major versions. The particle store is a derived
  view that can be rebuilt from the corpus by re-running extractors;
  the corpus is the durable record.

Implementation-status detail — including the pre-1.0
scrap-and-re-extract migration path documented and the
`particles db init --force` upgrade command — lives in `roadmap.md`
and the ADR archive. The compatibility contract above is what
adopters can rely on; the operational mechanics are documented
separately.

---

# Part I: Thesis

## The Case for Structured Agent Knowledge

---

# 1. Motivation

Structuring an agent's knowledge so that a machine can reason about it
reliably is not a new problem. Frame-based expert systems, RDF and the
broader semantic web, property graphs, and modern Retrieval-Augmented
Generation all attempt it with different trade-offs. Each leaves a
characteristic failure mode behind: rigid ontologies that LLMs cannot
populate consistently (RDF/property graphs); knowledge that does not
persist between queries (classic RAG); prose stores that drift from
their sources (LLM-Wiki). The claim-granularity unit itself has a
longer lineage than any of these: Cyc's *microtheories* partitioned a
knowledge base into contexts whose assertions could disagree;
nanopublications have published single assertions wrapped in formal
provenance since 2010 ([Groth, Gibson & Velterop
2010](https://content.iospress.com/articles/information-services-and-use/isu613));
micropublications extended that model to evidence and argument
structure ([Clark, Ciccarese & Goble
2014](https://jbiomedsem.biomedcentral.com/articles/10.1186/2041-1480-5-28)).
Particles inherits the unit from this lineage; what it adds is an
economical populator (LLM extraction) and a runtime lifecycle, as §6
elaborates. §6 catalogues the trade-offs in detail. This
section examines the most recent and most rapidly adopted of these
attempts — the LLM-Wiki pattern — because it is the closest in spirit
to the Particles thesis and the limits of its prose-based storage are
the limits Particles directly addresses.

## 1.1 The LLM-Wiki Pattern

On April 4, 2026, Andrej Karpathy published a design pattern for
persistent agent knowledge bases ([GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)).
The core observation is that most Retrieval-Augmented Generation (RAG)
systems re-derive knowledge from scratch on every query. LLM-Wiki
proposes instead that the language model incrementally compile sources
into a persistent, interlinked wiki of markdown files — so synthesis
happens once at ingest time and is available immediately at query time.

The architecture has three layers: raw sources (immutable originals),
the wiki (LLM-generated and maintained markdown), and the schema (a
configuration document describing wiki structure and conventions). The
three operations are:

- **Ingest**: a new source is read, key information is extracted, and
  relevant wiki pages are created or updated.
- **Query**: relevant wiki pages are retrieved and synthesized into a
  natural language answer.
- **Lint**: periodic health checks for contradictions, stale claims,
  orphan pages, and missing cross-references.

This is a genuine improvement over naive RAG. The wiki is a persistent,
compounding artifact; cross-references are pre-built; the model handles
the bookkeeping that causes humans to abandon wikis.

> **Dogfooding the source.** The Particles reference SDK ships a
> GitHub-gist extractor that ingests Karpathy's gist directly as a
> representative test fixture, producing structured particles from
> the original text and from each commenter's substantive technical
> discussion (author attribution back to the commenter on every
> claim). This is dogfooding, not validation — it demonstrates the
> pipeline runs against the motivating source without inflating
> what that demonstrates. See the techspec §14.4 reference-
> extractors table and the companion `roadmap.md`.

## 1.2 The Core Limitation: Natural Language as the Intermediate Representation

LLM-Wiki uses natural language markdown as the storage format for
synthesized knowledge. This choice is pragmatic — it is human-readable
and LLMs work with it natively. But it introduces a structural problem
that the LLM-Wiki pattern has no solution for.

> **Failure mode.** In a comment on Karpathy's Gist, a production
> practitioner reported: the LLM summarized documents and stored those
> summaries as wiki pages. The summaries were slightly lossy — a
> specific number here, a condition there. Health checks passed
> because they only verified that summaries agreed with each other,
> not whether they still matched the original documents. By the time
> the drift was caught, the knowledge base had been confidently wrong
> for months.

The structural cause: natural language markdown cannot carry:

- **Confidence values** — how certain is the agent about this synthesized claim?
- **Uncertainty classification** — is this uncertainty reducible (more evidence could help) or irreducible (inherent to the domain)?
- **Formal provenance** — which source document gave rise to this claim. (Passage-level provenance — byte-range or character-span references inside a source — is specified as Extension B; corpus-entry-level provenance is required at Core.)
- **Validity scope** — temporal qualifiers (`valid_until`) are first-class; richer assumption scoping (under what context or assumptions does this claim hold) is specified as Extension E.
- **Retraction semantics** — if a source is superseded or its author becomes unreliable, which derived claims are now stale? The standard distinguishes *source-trust* (the author or feed is unreliable, so every claim sourced from them is suspect) from *claim-status* (this specific claim is wrong even though the source is otherwise reliable).

Without these, linting is limited to surface checks. It cannot detect
the failure mode that matters most: a synthesized claim that has
silently diverged from its source.

The trade-off Particles makes is precise: it does not eliminate the
need for an LLM (or other semantic-equivalence layer) to judge when
two claims agree, disagree, or are independent — see §3.6 for the
honest version of this constraint. What it does is *constrain* the
inputs that the judging layer sees: structured claim-granularity
particles with explicit confidence, provenance, and lifecycle status,
rather than unstructured prose paragraphs whose interpretation has
already drifted. Bounding the judge's input is what makes the
remaining drift inspectable; it does not make the drift go away.

## 1.3 Why Incremental Alternatives Are Insufficient

An incremental path exists: augment markdown with the above rather
than replace it. Examples include YAML frontmatter for metadata,
inline tags for provenance, and hybrid graph-plus-document stores.
This is a legitimate evolution of LLM-Wiki and is already emerging in
practice.

Particles does not dismiss this path. The Markdown Exporters (see §3.5)
are designed explicitly as an incremental adoption layer for teams
already invested in markdown-native tools. However, augmented markdown
has a fundamental ceiling: once the canonical representation is text,
every downstream consumer that reads it loses the structure. Metadata
embedded in frontmatter is not enforced — any writer can omit it.
Provenance tags inline are conventions, not constraints.

The distinction is between a format where the signals — confidence,
provenance, validity — are *optional decoration* of prose, and a
format where those signals are the *canonical layer surrounding* a
prose claim. Particles takes the second position: the claim itself
remains a natural-language sentence; the structure surrounds it as
machine-readable metadata, not as an optional annotation a downstream
consumer may discard. Natural language renderings are generated from
particles as a view, not stored as particles as a source.

A commenter on the original Karpathy gist framed the distinction
precisely: when the language model is a librarian who writes new books
and shelves them next to the originals, you eventually cannot tell the
difference. When it writes index cards pointing at the originals, you
always can. Particles is the index card layer.

---

# 2. The Architectural Inversion

The central architectural shift Particles proposes:

| LLM-Wiki (current) | Particles (proposed) |
|---|---|
| **Ingest time**: convert source to natural language markdown. Store the prose synthesis. | **Ingest time**: deposit source into the immutable corpus (trivial cost). Asynchronously extract structured particles — claims with confidence, uncertainty, and provenance. |
| **Query time**: retrieve relevant markdown pages and read them. | **Query time**: retrieve relevant particles and generate natural language from them, tailored to the specific question and audience. |

This inversion has four important consequences:

1. **Fidelity is preserved.** Claims are extracted from sources in a single, provenance-preserving pass — not paraphrased repeatedly through intermediate prose layers as in LLM-Wiki, where a wiki page first summarises a source and a query response then summarises the wiki page. Confidence and provenance track what is known versus inferred.
2. **Consistency checking becomes more reliable.** Contradictions between particles can be detected via graph traversal and semantic comparison — more inspectable and more automatable than asking an LLM to re-read prose, though not fully deterministic (see §3.6).
3. **Query-time rendering is flexible.** The same particle store can answer differently for a domain expert versus a layperson, at different confidence thresholds. A query specifies an audience tier (`EXPERT`, `GENERAL`, `REGULATORY`) and a minimum confidence threshold; the response synthesis layer surfaces particles whose effective confidence clears the threshold and renders them at a vocabulary appropriate to the audience.
4. **Retraction propagates traceably.** When a source is superseded, every particle whose provenance traces to it can be identified and flagged automatically. *Traceably*, not *correctly*: the mechanical propagation is deterministic, but whether a downstream claim is actually invalidated by an upstream change requires semantic judgment that may need operator review.

> **Thesis.** Particles relates to LLM-Wiki the way structured records
> relate to freeform summaries: both contain the same information, but
> only one preserves machine-inspectable provenance and lifecycle
> metadata alongside the prose.

> **Two paths through the inversion.** Once the architecture is in
> place, downstream value flows along two distinct paths that the
> rest of the document is organised around. **Structural operations**
> — retraction propagation, contradiction detection, calibrated
> confidence, the relation graph — *cannot work on prose at all* and
> consume the particle store directly. **Presentation operations** —
> per-claim citations, audience-tier rendering, confidence disclosure
> — *work better with structured input but produce prose for human
> consumption*; they read from the particle store and write to the
> compiled wiki view. §4 names the two corresponding front doors:
> the agent-memory audit-and-harvest loop (a structural-operation
> surface for engineers and their agents) and the cited projections
> — wiki articles, vaults — (a presentation-operation surface for
> everyone else). The single architectural inversion enables both —
> without it, neither the audit loop nor the wiki has a substrate to
> operate on.

## 2.1 A Worked Example

To make the inversion concrete, here is the full round-trip for a
single source.

**Source** (a news article, deposited verbatim into the corpus):

> *"Acme Corp announced today that it has acquired Widget Inc for an
> undisclosed sum. The deal is expected to close in Q3 2026, pending
> regulatory approval."*
> — `https://example.com/news/2026/05/15/acme-widget`, fetched
> 2026-05-15T14:30Z, SHA-256 `7f3c…`.

**Extraction produces two particles** (fields abbreviated for clarity):

```yaml
- id: p-a91f2c…
  content: "Acme Corp acquired Widget Inc."
  subjects: [Q-Acme-Corp, Q-Widget-Inc]
  confidence:
    value: 0.92
    calibration_source: EXTRACTOR_DIRECT
  uncertainty_nature: EPISTEMIC
  provenance:
    corpus_entry: ce:8b14a…
    extractor_ref: general-extractor@0.3.0
  status: ACTIVE

- id: p-c2d8e3…
  content: "The Acme–Widget acquisition is expected to close in Q3 2026."
  subjects: [Q-Acme-Widget-acquisition]
  confidence:
    value: 0.65
    calibration_source: EXTRACTOR_DIRECT
  uncertainty_nature: ALEATORY
  valid_until: 2026-09-30
  provenance:
    corpus_entry: ce:8b14a…
    extractor_ref: general-extractor@0.3.0
  status: ACTIVE
```

The first particle is a factual claim with high confidence and
epistemic uncertainty (the fact is known to the source). The second
is a forward-looking statement: lower confidence, aleatory uncertainty
(the outcome is genuinely undetermined), and a `valid_until` after
which the claim expires lazily (§3.7).

**Query** (`particles query "Who acquired Widget Inc?"`):

The query embeds the question, retrieves matching particles via
semantic search, and synthesises a response that cites the
contributing particles:

> Acme Corp acquired Widget Inc [^p-a91f2c]. The deal is expected to
> close in Q3 2026, pending regulatory approval [^p-c2d8e3].
>
> [^p-a91f2c]: https://example.com/news/2026/05/15/acme-widget
>     (confidence 0.92; extractor general-extractor 0.3.0; 2026-05-15)
> [^p-c2d8e3]: https://example.com/news/2026/05/15/acme-widget
>     (confidence 0.65; forward-looking; valid until 2026-09-30)

**What changes downstream.** If a follow-up source on 2026-08-12
reports the acquisition closed, the lint operation detects that
`p-c2d8e3` should now be marked SUPERSEDED rather than expired; the
new claim is extracted as a separate particle with its own provenance.
If the original article is updated and the SHA-256 changes, re-extraction
runs against the new snapshot and any divergent particles are flagged.
If a second outlet reports the same acquisition, the lint operation
proposes a co-evidential link (§3.4.1) rather than treating the two
particles as independent evidence.

The same information stored as LLM-Wiki prose would carry none of
these signals: no per-claim confidence, no lifecycle status, no
provenance graph, no mechanical path from a source update to a claim
update.

## 2.2 Trade-offs of the Inversion

The inversion is not free. Three architectural tensions are
load-bearing and acknowledged here rather than buried in later
sections:

1. **Granularity vs reliability.** Finer-grained claims (§3.4)
   improve provenance precision and retraction targetability, but
   they also increase extraction ambiguity, semantic duplication
   (§3.4.1), and the surface area for spurious contradictions. The
   standard's claim grammar tries to land near the optimum; whether
   it does is an empirical question, not a settled one.
2. **Natural-language claims vs machine reasoning.** Storing claims
   as prose keeps them legible to LLMs and humans, but it imports
   probabilistic semantics into every operation that compares
   claims — contradiction detection, co-evidential grouping, trust
   merging. The standard does not escape ontology alignment; it
   keeps the alignment *soft, probabilistic, and inspectable* rather
   than enforced by a formal ontology (§3.4.1, §3.6).
3. **Ingest cost vs query cost.** Asynchronous extraction at deposit
   time pays an LLM-call cost up front. Query-time synthesis pays a
   second LLM-call cost on every read. Particles shifts complexity
   from ingest to query rather than eliminating it (Risk #9); the
   wiki article exporter (§4.2) is the primary mitigation, caching
   synthesis as a static artefact for the common-case read path.
4. **Subject-density vs query-time context limits.** A heavily-
   documented Subject can accumulate thousands of particles; vector
   similarity narrows that to a top-k slice at query time, but the
   slice still has to fit the synthesis LLM's context window. Highly
   documented entities (a major company, a recurring news subject,
   a long-lived technical project) can therefore exceed the synthesis
   budget without preprocessing. The pre-rendered per-Subject wiki
   article (§3.5, §4.2) is the architectural mitigation — it caches
   one synthesis pass per Subject and serves it as a static read —
   but interactive queries against very dense Subjects may need
   intermediate clustering or summary-of-summaries strategies that
   the standard does not yet specify.

These tensions are mitigated by specific design choices in §3 and
risk mitigations in §5, but the trade-offs themselves remain.

---

# 3. Design Principles

## 3.1 High-Fidelity Extraction

The architectural inversion only delivers on its promise if particle
extraction is high-fidelity. Inaccurate extraction moves the drift
problem upstream rather than solving it. Worse, the false precision of
structured metadata masks the resulting semantic errors from
downstream validation — confidence and provenance look authoritative
even when the underlying claim is wrong. (Extraction fragility is
catalogued as Known Risk #1 in §5.)

Extraction is harder than it may appear for four specific reasons:

1. **Claims are not objectively defined units.** Different extractors will segment the same text differently. *"One falsifiable claim (one that could in principle be shown false)"* is not operationally precise without domain-specific guidance.
2. **Context loss is subtle and systematic.** Conditions, scope, and qualifiers are often implicit. Extractors will systematically mishandle negation, exceptions, temporal qualifiers, and domain assumptions.
3. **LLM confidence is not epistemic confidence.** A model's self-reported confidence reflects its training distribution, not the strength of the underlying evidence. Confidence values must be calibrated against evidence, not taken from the extractor directly.
4. **Granularity creates combinatorial surface area.** More granular particles mean more edges in the provenance graph, more potential conflicts, and more failure modes at scale.

> **Empirical baseline.** The fidelity claims in this section are
> *design commitments*, not yet broad empirical results. The reference
> SDK's benchmark harness (§3.1.3) reports precision / recall / ECE
> against three seed suites in three domains — one structured-catalog
> (Numista coins) and two UGC (Reddit, Hacker News), with calibration
> results in §3.7. That is a working measurement framework, not a broad
> matrix: read every "high-fidelity" claim below as the operational
> hypothesis the architecture is designed against — substantiated for a
> handful of domains and in active expansion.

### 3.1.1 Original mitigations

- **Particles err toward granular and source-faithful.** When in doubt, extract narrower particles rather than fewer broader ones. Narrow particles are easier to retract precisely.
- **Extraction quality is measured and surfaced like any other operational metric** (latency, error rate) — not buried as an internal implementation detail. The benchmark suite includes extraction fidelity tests with recall and precision targets; see the techspec's success-metrics section.
- **The source corpus is always preserved.** Because every particle carries a provenance reference back into the immutable corpus, a failed extraction can be re-run against the original source without data loss. The corpus is the ground truth; the particle store is always a derived view.

### 3.1.2 Engineering mitigations from implementation experience

Implementation experience surfaced four additional extraction
principles, now considered baseline:

- **Extraction is chunked at structural boundaries.** Sources whose rendered text exceeds the single-call budget (long PDFs, heavily-commented gists, multi-page HTML, 100-page technical specs) are split on paragraph boundaries — falling back to line breaks inside long paragraphs and to a hard cut at chunk size for pathological one-line inputs. Chunking applies to every text-shaped non-PDF source, not only HTML; PDFs are paged separately.
- **Re-extraction uses content-hash carry-forward.** Each chunk's SHA-256 is recorded on the particles it produced; on re-extraction (whether triggered by an extractor upgrade or by a source mutation), chunks whose hash matches a prior particle's `chunk_hash` skip the LLM call entirely. Incremental source updates therefore re-extract only the changed regions, not the whole source.
- **Synthesised outputs are citation-validated**, so that an LLM cannot invent a provenance link the underlying particles don't support.
- **Per-source attribution heuristics are applied**, so that author identity carried in the source content (rather than in surrounding metadata) is correctly captured for UGC sources.

The techspec's "Implementation Discoveries" appendix documents the
concrete patterns.

### 3.1.3 Measurement

A benchmark harness measuring extraction fidelity — precision, recall,
and calibration error against curated gold-standard particles, broken
down by source type, claim category, and extractor — is part of the
standard's scope. The reference SDK ships the runner as
`particles extractor benchmark <extractor-id>`. It consumes
the frozen `BenchmarkSuite` schema documented in techspec §13.3, so
community-curated suites and the reference SDK's suites use the same
machinery.

**Measured baseline.** The bundled suite library covers three suites in
three domains — the structured Numista catalog plus two UGC sources
(Reddit, Hacker News). On the Numista fixture the reference coin
extractor scores precision 1.00, recall 1.00, and Expected Calibration
Error ≈ 0.05; the calibration results across all three suites are
reported in §3.7. These numbers establish that the harness works
end-to-end and say something real about the bundled extractors; they do
*not* establish that the standard meets its overall fidelity targets.
Current per-suite numbers as they accumulate are in `roadmap.md`.

## 3.2 Extraction as a Product Subsystem

High-quality extraction requires more than a general-purpose LLM prompt
over source documents. The general extractor (see §3.8) provides a
functional baseline for all deployments — no configuration required.
For operators who need higher fidelity in specific domains, extraction
quality can be improved through:

- **Domain-specific extractors** that encode the claim grammar for a particular subject area, registered via the extractor ecosystem (§3.8, techspec §6.8). These are optional enhancements, not requirements.
- **Confidence calibration strategies.** Methods that convert an LLM's raw self-reported confidence — which is often poorly calibrated — into a probability estimate grounded in evidence (agreement across multiple extractors, comparison against gold standards, or human review).
- **Re-extraction as extractors improve.** The `reindex` operation re-runs extraction against the source corpus when an extractor is upgraded or a previously-failed snapshot becomes processable, surfacing higher-fidelity particles without re-fetching the original source.
- **Human-in-the-loop correction** for low-confidence extractions and edge cases in high-stakes deployments.

> **Scope note.** The general extractor is the mandatory baseline —
> every conformant implementation ships with one, and it works without
> configuration. Domain-specific extractors improve on that baseline
> for operators who need it. The particle schema is domain-agnostic;
> extraction quality is domain-specific and improves incrementally as
> the extractor ecosystem matures.

## 3.3 Subjects: The Knowledge Graph Backbone

Every claim is *about something*. The Subject store is the standard's
catalogue of those somethings — canonical real-world entities against
which particles are indexed and which together form a sparse
knowledge graph: Subjects are nodes, single-subject particles are
properties of a node, and multi-subject particles are edges between
nodes.

A Subject is a record identified by canonical name, optional aliases,
optional external identifiers (Wikidata QIDs, Numista numbers, GitHub
login URIs), and an optional canonical class. A particle's
`subject_ids` field is the set of Subjects the claim involves. *"The
1969 quarter weighs 5.67 g"* is a property of one Subject; *"Acme
acquired Widget"* is an edge between two. The query layer uses
`subject_ids` as a hard filter alongside the vector-similarity match
on `content` — both axes contribute to retrieval (§3.11).

Two design choices distinguish the Subject store from a hand-curated
ontology:

- **Subjects are LLM-resolved against an external ontology, not
  hand-curated.** At extraction time the resolver looks up each
  subject name against Wikidata (general entities), Numista (coins),
  GitHub (code repositories), and falls back to creating a bare
  local Subject only when no external match exists. The mechanic
  is concrete: an extractor parsing *"Anthropic"* in a news article
  calls the Wikidata search API, takes the top result (`Q108587961
  — Anthropic, AI safety company`), and pins that QID onto the
  Subject record. Subsequent particles about *"Anthropic"* from any
  source — a Reddit thread, a SEC filing, a GitHub commit message —
  link to the same Subject because they resolve to the same QID.
  This keeps subject identity stable across operators and across
  extractors. The lookup is cached, rate-limited, and runs
  asynchronously to extraction.
- **Subjects carry a canonical class when one is known.** When the
  resolver retrieves an external record that exposes a class (e.g.
  Wikidata's `P31 instance of`, Numista's denomination/material
  metadata), the class is stored on the Subject
  (`nmo:NumismaticObject`, `wd:Q5 (human)`, …). The class drives
  rendering decisions (coins render with a numismatic property
  table; people render as generic notes) without requiring extractors
  to coordinate on rendering conventions.
- **Identity is *contractual*, not solved.** Name collisions
  (*"Anthropic"* the company vs *"Anthropic"* the product line),
  top-result brittleness, ontology disagreements (Wikidata says one
  thing, the domain KB says another), and concept drift over time
  are the hard cases — and exactly where knowledge-graph systems
  historically fail. The standard's posture is explicit on three
  points: (1) the resolver is **deterministic given a fixed resolver
  version, snapshot of the external KB, and input string**, so two
  operators running the same SDK version against the same Wikidata
  dump get the same QID for the same string; (2) every resolution
  result is **operator-overridable** via the shipped operator surface —
  `particles subjects merge` (combine two Subjects), `particles subjects
  split` (separate a misjoined Subject; the resolver re-canonicalises
  the new Subject against external KBs), and
  `particles subjects pin` (confirm an external-reference binding);
  (3) the resolution event itself is **provenance-tracked** —
  ``asserted_by`` and ``asserted_at`` on the Subject record carry
  the resolver identity and the resolution time, so audit and
  re-resolution are first-class. Identity is something operators
  inspect, correct, and version; the resolver provides a strong
  default, not an oracle.

Subjects are the surface where prose claims become *queryable
structure* without imposing a closed ontology. The schema is
domain-agnostic; subject resolution is domain-specific and improves
incrementally as the resolver gains adapters for new identifier
systems.

## 3.4 Claim Granularity

The granularity of a particle is the most consequential design decision
in the schema. Two failure modes bound the acceptable range:

- **Too coarse — paragraph-level particles**: provenance is imprecise, confidence is a blend of multiple claims, contradictions are hard to detect at sub-paragraph granularity.
- **Too fine — triple-level particles (Subject–Predicate–Object)**: the particle store grows combinatorially, retrieval becomes complex, and the context required to interpret a triple is spread across many particles.

The recommended granularity unit is the **claim**: a single falsifiable
assertion (one that could in principle be shown false) that can be
independently evaluated as true, false, or uncertain. Practical
guidance for extractors:

- One particle per independently verifiable assertion.
- Conditional claims preserve their conditions: *"X is true when Y"* is one particle, not two.
- Quantified claims preserve their quantification: *"Most X are Y"* is not the same particle as *"All X are Y."*
- Temporal qualifiers are preserved as part of content or in the `valid_until` field, not discarded.

In practice the claim boundary is set by the extractor's claim
grammar and is not guaranteed to be reproducible across extractors of
different domains: a numismatic extractor and a generic extractor
will segment the same paragraph differently. This is a known surface
of ambiguity, not a solved problem. Two SDK tools partially measure
its consequences: the extractor conformance validator
(`particles extractor conform`) checks
whether extractors populate the schema fields they should, and the
benchmark harness (`particles extractor benchmark`) measures precision and recall against gold-standard claims.
Direct measurement of claim-boundary stability across extractors — the
overlap between two extractors' segmentations of the same paragraph —
is a separate, deferred benchmark category not yet shipped.

> **Particles store prose, not triples.** A common misreading of
> "structured representation" is that Particles must store knowledge
> as RDF-style Subject–Predicate–Object triples. It does not. A
> particle's *content* field is a natural-language claim — a single
> sentence in prose. The *structure* is the metadata surrounding it:
> confidence with calibration source, uncertainty nature, provenance
> references back to the corpus, the canonical subjects the claim is
> about, and lifecycle status. This is a deliberately accessible
> representation: the LLM that produces a particle does not need to
> align it to an ontology, and a human reading a particle sees a
> sentence they understand. Particles is closer to Karpathy's
> original instinct (compose markdown claims with structure) than to
> a triplestore. The structured metadata is what makes machine
> reasoning more inspectable and easier to validate than prose-only
> representations; the prose content is what keeps the system humane.

### 3.4.1 Claim Identity and the Relation Graph

Claim granularity creates a second-order question: when two sources
assert the same underlying claim in slightly different words, are
those one claim or two? The standard's answer is that each source's
claim is its own particle — source-faithfulness is preserved — but
the particles are linked by typed relations that let downstream
operations (query synthesis, wiki rendering, contradiction checking,
trust-weighted confidence merging) treat the group with appropriate
semantics.

**The relation-kind registry.** Relations between particles are typed
via a closed registry rather than a free-form string column.
Three kinds are ACTIVE — the SDK ships an emitter and a downstream
consumer for each:

| Kind | Symmetry | Meaning |
|---|---|---|
| `CO_EVIDENTIAL` | symmetric | Two particles assert the same underlying claim from different sources; emitted by the `L-IDX-01` lint check, consumed by the trust-weighted confidence merge. |
| `PART_OF` | asymmetric | A constituent particle belongs to a narrative; the narrative exists only as the subgraph its `PART_OF` / `SEQUENCE_IN` edges induce. |
| `SEQUENCE_IN` | asymmetric | Orders a narrative's constituents (predecessor → successor); v1 sequences are linear. |

A further set of kinds — `CONTRADICTS`, `BOOSTS`, `QUOTES`,
`REPLIES_TO`, `MENTIONS` — is **RESERVED**: the names are held against
the multi-extractor interoperability contract (extractors MUST NOT
repurpose them) but no emitter ships yet. Reserving now is deliberate,
because the expensive coordination problem is activation, not naming:
once one public extractor emits `BOOSTS` under one definition and
another emits it under a different one, the standard has fragmented,
whereas *activating* a reserved kind later requires only an ADR naming
its emitter, consumer surface, and symmetry — landing in one commit.
Symmetric kinds canonicalise to `(min(a, b), max(a, b))` on write so
duplicate insertions collide at the unique constraint; asymmetric kinds
preserve direction because the direction carries meaning. The full
mechanism is in the techspec (records the co-evidential
rationale; the registry itself).

This is the point at which to be explicit about a critique that
applies to Particles as a whole: storing claims as prose does not
escape the need for semantic alignment. Contradiction detection
(§3.6), co-evidential grouping, and trust-weighted confidence
merging all require *some* notion of when two claims mean the same
thing or disagree. Particles does not avoid this work — it keeps
the alignment *soft, probabilistic, and inspectable* (embeddings,
LLM-mediated equivalence judgments, operator review through the
lint workflow) rather than enforced by a formal ontology. The
trade-off is honesty: the system is not a triplestore, but it is
also not free of the hard problems triplestores were built to
solve.

## 3.5 Markdown Exporters

Particles does not require teams to abandon existing tooling. The
Markdown Exporters are a *family* of renderings that present particles
in markdown-native formats, sized to the use case:

> **Adoption strategy.** A *"Particle-flavoured Markdown"* rendering —
> compatible with Obsidian callout blocks — allows operators to view
> particle metadata (confidence, provenance, uncertainty
> classification) directly in existing markdown tools. The particle
> store remains the canonical representation; markdown is a read-only
> view layer for human inspection.

Three concrete exporter renderings, in increasing scope:

1. **Per-particle annotation** (the original spec sense): each particle is rendered as a markdown blockquote with its metadata inline. Used by the Obsidian exporter for individual claims.
2. **Per-Subject vault**: one markdown file per Subject, listing every particle about that subject with citation and confidence inline. Shipped today as `particles export obsidian` (Obsidian-flavoured callouts) and `particles export logseq` (Logseq's native bullet-outline format with `((block-id))` cross-page citation). Both are optimised for graph navigation inside the operator's markdown-native tool of choice.
3. **Per-Subject wiki article** (`particles export wiki`): the LLM synthesises a prose article *about* a subject from its particles, with every claim cited back to its particle ID and footnote-linked to its source URL. The synthesised body passes two validation layers — Layer A (regex-based ID-membership) catches invented citations deterministically; Layer B (per-sentence LLM-judge alignment) catches real citations that have been laundered onto unsupported claims. On validation failure the exporter falls back to a deterministic structured-listing render so the operator always gets a fully cited article. Optimised for sharing with a reader who is not running the SDK — the wiki articles are the primary *demo artefact* of the system.

**Shared synthesis cache.** The wiki, Obsidian (via
`--with-synthesis`), and Logseq exporters all consult the same
content-addressed synthesis cache keyed on `(subject_id,
input_hash, prompt_version)`. An
operator who exports the same store via two or three markdown
formats pays the LLM synthesis cost once per Subject — not once
per exporter. This is what makes the multi-exporter strategy
operationally viable rather than a tax.

The reverse direction — onboarding an existing markdown knowledge
base — is the retrospective import path
(`particles import vault`): the SDK walks an existing Obsidian
vault or any directory of markdown notes, deposits each note
unmodified into the corpus as a source, and the standard
extraction pass converts the notes into particles. The lint tool
then runs against the existing knowledge base without the operator
rebuilding it by hand; the notes themselves are never modified.

## 3.6 Consistency Checking: Reliable, Not Deterministic

Graph traversal alone cannot detect semantic contradiction. Full
consistency checking requires semantic equivalence detection, ontology
alignment, unit normalization, and temporal alignment.

What Particles provides is a *more reliable and more inspectable*
consistency checking substrate than prose. Structural checks (provenance
overlap, confidence interval conflict, status flags) are deterministic
and fast. Semantic checks require LLM or symbolic reasoning layers, but
those layers operate on structured inputs rather than unstructured
prose, making them more precise and their failures more visible.

Consistency checking in Particles is probabilistic and inspectable,
relying on semantic equivalence layers over structured inputs rather
than on strict deterministic graph constraints. Any references in this
document to "deterministic" contradiction detection should be read
against that baseline.

**What "more reliable" looks like concretely.** Two cases the lint
workflow handles today, both deliberately small enough to fit on the
page:

* **Near-duplicate claims, two sources.** Two particles with
  high embedding similarity, the same canonical Subject set, and
  non-contradictory `valid_until` windows — e.g., one news article
  and one SEC filing each asserting *"Acme acquired Widget"*. The
  `L-IDX-01` lint check surfaces the pair as a candidate
  `CO_EVIDENTIAL` link; the operator confirms (or rejects); the
  trust-weighted confidence merge then treats the pair as one
  corroborated claim rather than two independent ones, removing the
  apparent double-evidence from query-time synthesis.
* **Conflicting numeric values for the same property.** Two
  particles attaching different `nmo:hasWeight` values to the same
  Numista subject — e.g., 0.75 g and 0.70 g for the same 1948 GDR
  Pfennig. The lint check flags the pair, surfaces both
  particles' provenance side-by-side, and emits a
  `[!warning]` Obsidian callout so the operator sees the conflict in
  the rendered vault. The merge logic does not silently pick one;
  the disagreement stays visible until reviewed.

Neither case is deterministic — the embedding threshold for "near-
duplicate" is tunable, and the numeric-conflict check assumes the
property semantics align. What they demonstrate is that *operating
on structured claim-granularity particles makes both kinds of
disagreement queryable*. The same two news + SEC documents stored
as LLM-Wiki prose would either silently agree (and miss the
acquisition-vs-rumour distinction) or silently contradict (and the
contradiction would sit in two paragraphs of unrelated wiki pages
that no lint pass would think to compare).

## 3.7 Calibrated Confidence

Structured metadata creates a specific failure mode absent from prose
systems: epistemic overconfidence — operators calibrating their trust
to the formalism rather than to the underlying reliability of the
extraction. (This is catalogued as Known Risk #3 in §5.) Four
principles in the standard's design contain the risk:

- **Extraction quality dashboards are mandatory, not optional.** Operators must be able to see extraction fidelity metrics for their particle stores.
- **Confidence values carry calibration provenance.** The `calibration_source` field records how the confidence value was derived — from the extractor directly (`EXTRACTOR_DIRECT`, lower trust), from a fitted calibration over a benchmark suite (`CALIBRATED_BENCHMARK`, higher trust), or from human review (`HUMAN_REVIEW`, highest trust).
- **The calibration pipeline is shipped infrastructure; quality demonstration depends on suite coverage.** The reference SDK implements temperature scaling. The reference SDK fits a one-parameter temperature scaler against the benchmark harness's gold-standard particles, stores the parameter on the extractor record, and applies it to every extracted confidence at extraction time. Operators run `particles extractor calibrate <extractor-id>` against a curated suite; subsequent extractions stamp `CALIBRATED_BENCHMARK` automatically. The lifecycle — `EXTRACTOR_DIRECT` → operator-fitted → `CALIBRATED_BENCHMARK` — runs end-to-end. Whether the result is a quality *improvement* depends on the extractor and the suite, and is published as data.

> **Worked example — three extractors, three runs.** Each of the
> three reference benchmark suites bundled with the SDK produces the
> following calibration result:
>
> | Extractor | Type | N | ECE raw | ECE calibrated | T fit | Reduction |
> |---|---|---|---|---|---|---|
> | `numista-coin-extractor` | structured | 7 | 0.0471 | 0.0953 | 10.0 (ceiling) | -102 % |
> | `reddit-extractor` | LLM-driven | 18 | 0.6389 | 0.0914 | 10.0 (ceiling) | -86 % |
> | `hackernews-extractor` | LLM-driven | 15 | 0.8024 | 0.0910 | 10.0 (ceiling) | -89 % |
>
> Three observations the data supports:
>
> 1. **Calibration substantially helps the common case.** For
>    LLM-driven extractors whose raw confidence is systematically
>    over-stated — the modal pattern, since the underlying language
>    model treats fluent prose as confident even when the supporting
>    evidence is weak — temperature scaling reduces Expected
>    Calibration Error by ~85-89 % across two independent UGC
>    extractors over two independent gold-standard suites.
> 2. **For already-well-calibrated extractors, the bounded fit can
>    be net negative.** The Numista coin extractor's raw confidence
>    clusters at 0.95–1.00 because the source is a structured
>    catalog. The scaler tries to dampen those values; on a small
>    sample the per-bin reliability tilts the wrong way; net ECE
>    rises. The result is not a refutation of temperature scaling —
>    it's evidence that operators should run calibration *and check
>    the result*, not blindly accept it.
> 3. **The T = 10.0 ceiling is the binding constraint in every
>    run.** The bounded optimiser's `[0.01, 10.0]` interval is
>    saturated in all three cases — the scaler wants more headroom
>    everywhere. This is a real R1.1 improvement lever (raise the
>    upper bound, possibly with regularisation against overconfident
>    T fits on small samples) and is recorded as a roadmap item.
>
> What the table *does not* claim: that calibration is a solved
> problem, that two LLM-driven extractors generalise to every
> extractor type, or that a calibrated ECE of 0.09 is a target
> rather than a floor of what bounded temperature scaling currently
> achieves on these suites. What it *does* claim: the pipeline
> ships, runs end-to-end, produces results that say something
> useful about whether to trust extractor confidences, and the
> standard's evidence story scales as the suite library grows.
- **Query-time rendering surfaces uncertainty.** Systems must not generate confident-sounding prose from low-confidence particles without disclosure.
- **Temporal validity is filtered lazily.** A particle's `valid_until` timestamp is enforced at query time: expired particles are filtered out of the candidate set without active retraction. Active retraction is reserved for source-driven invalidation (the source has been superseded or its author downgraded); time-bound claims simply expire.

## 3.8 The Extractor Ecosystem

Extraction quality is not solely an engineering problem — it is a
community coordination problem. No single general-purpose extractor will
achieve high fidelity across all domains. The standard therefore
defines an extractor ecosystem: a framework in which the community can
develop, share, evaluate, and compose extractors, with the general
extractor as a universal fallback.

### General extractor as fallback

Every conformant Particles implementation MUST provide a general-purpose
extractor. The general extractor requires no configuration, applies to
any `source_type`, and produces `EXTRACTOR_DIRECT` confidence particles.
It is the floor of extraction quality — always available, immediately
functional, and gradually superseded by domain-specific extractors as
they become available for a given domain.

The extraction pipeline selects extractors by specificity: the most
specific registered extractor whose applicability specification matches
the source is preferred; the general extractor is used if and only if
no domain-specific extractor applies. Multiple extractors may be
applied in parallel for cross-validation; their outputs are merged using
the trust-weighted confidence model (see techspec §6.9).

> **Extractor ecosystem.** Machine-checkable applicability scopes,
> deterministic conflict resolution between competing extractors, and
> a shared public archive of extractor outputs are Extension A
> features; the protocol mechanics are specified in techspec §14. A
> Core-conformant implementation needs only the general extractor.

The standard permits independently-developed extractors with explicit
trust and applicability metadata, allowing operators to compose
extraction pipelines without central coordination. The reference SDK
ships domain-specific extractors as evidence the architecture supports
diverse sources; the current set is catalogued in the techspec §14.4
reference-extractors table, and open extractor work items are tracked
in `roadmap.md`. The primary ecosystem challenge is
establishing the incentive structures and validation pipelines that
let the community contribute and maintain extractors across the long
tail of sources.

## 3.9 Link-Shaped Sources Preserve Curation Signal

The Source Corpus is more than a passive archive. Many high-value
sources today are *link-shaped*: a small envelope of platform
metadata that points at the URL where the substance lives. A Reddit
link post is one sentence and a URL; a Hacker News story is a title
and a URL; a Mastodon post with a link card is a sentence and a URL.
The substance of what the author wanted to share is the linked
page; the platform envelope records that they chose to share it on
that date with that framing.

**The non-goal** is worth stating up front, because the term
"intent" overpromises: Particles does **not** model *why* a user
shared a link — we make no claim about endorsement, satire, dunking,
spam, or any other social-dynamic signal. Particles records the
*curation* fact (this person, on this date, chose to amplify this
URL) and lets downstream consumers decide what to do with it. That's
a smaller and more defensible commitment than "modelling editorial
intent".

The deposit pipeline treats curation as first-class structure: an
importer for a link-shaped source stores the platform envelope as one
corpus entry, follows the post's primary URL, deposits that target as a
separate corpus entry (a depth-1 cap — followed entries do not
themselves trigger further follows), and records a typed `POST_LINK`
edge tying envelope to target.

**Envelope-vs-target attribution is preserved.** Claims extracted from
the *envelope* (the Reddit post body, the HN title) carry the poster as
their `asserted_by`; claims from the *target* (the linked article)
carry the target's own author. The follow-edge ties the two together
without conflating them — a reader who sees only the target's claims
can still ask "who shared this, and when," and the poster is *not*
treated as an author of the target's claims, even when they shared it
approvingly. That judgment belongs in higher-level reasoning over the
curation signal, not in attribution metadata.

**The depth-1 cap is principled, not arbitrary.** Multi-hop following
collides with graph cycles, attribution dilution (a 4-hop chain makes
the curator's role tenuous), and operator surprise (a single deposit
fetching an unbounded citation tree). One hop captures the curator →
target relationship; beyond that, operators deposit additional sources
explicitly. The follow edges are queryable rather than write-only, so
an operator running a wiki of policy debates can ask "who shared this
SEC filing and when" and get the answer directly. The shape is
normative: importers opt in by defining `primary_url()` on their
importer plugin, with per-source-type defaults shipping for Reddit,
Hacker News, and Mastodon.

---

# Part II: Implications

## 3.10 Privacy Boundary

Particles provides composable privacy primitives; operators set the
policy that combines them. The standard separates *mechanism* (what
the schema makes possible) from *policy* (which combinations are
required in a given jurisdiction or deployment), and commits to the
mechanism side. The following primitives are designed to support
privacy-sensitive use cases without prescribing how operators apply them:

- **`EPHEMERAL` mutability class** (techspec §7.4): corpus entries that MUST NOT be archived locally or shared; provenance references are retained but content is not.
- **ODRL rights metadata** (techspec §10.2): may be attached to corpus entries to record usage rights, redistribution restrictions, and deletion obligations.
- **Author identity scoping** (techspec §6.5): `author_id` is optional and may be omitted or pseudonymised for privacy-sensitive UGC sources.
- **Operator-controlled allowlists** (techspec §6.9): operators control which extractors may process which corpus entries, enabling data minimisation policies.

Personal data, sensitive data, and regulated data (HIPAA, GDPR, CCPA)
are within the intended use envelope of Particles. Operators are
responsible for determining which corpus entries require `EPHEMERAL`
handling, which particles may be shared in multi-agent contexts, and
which provenance chains must be expunged on deletion requests. The spec
provides the primitives; the compliance policy is the operator's
responsibility.

> **Privacy note.** The spec is compatible with privacy-preserving
> deployments but is not opinionated about them. A future Extension F
> (Privacy and Consent) may specify normative privacy controls for
> regulated deployments. This is acknowledged as a gap for production
> use cases involving personal health, financial, or identity data.

## 3.11 Navigation by embedding, not by traversal

A common critique of ontology and knowledge-graph approaches is that
even a well-modelled structure becomes unusable at runtime: agents
must either stuff the whole graph into their context window (token
explosion) or traverse it dynamically (latency nightmare). Smart
knowledge representation is necessary but not sufficient; the
*navigation engine* matters as much as the graph.

Particles addresses this by architectural choice rather than by
solving the traversal problem head-on. Three properties keep
navigation cheap:

1. **Shallow structure.** The graph is two hops deep: Subjects link
   to particles; particles link to corpus entries. There is no
   multi-level class hierarchy to crawl. The unit a query operates on
   is a flat set of claim-granularity particles, not a class lattice.
2. **Vector similarity as the primary navigation primitive.** Query
   embeds the question, retrieves top-k particles by cosine similarity
   against particle embeddings, and applies Subject and confidence
   filters as cheap secondary constraints. There is no symbolic graph
   walk on the read path. *"The agent knows which door to open"* is
   implemented in vector space, not in ontology.
3. **Pre-rendered synthesis for the common case.** The wiki article
   exporter (§4.2) caches per-Subject prose articles with input-hash
   invalidation, so the hot read path is reading a static markdown
   file, not running an LLM. Risk #9 catalogues this as the
   load-bearing performance choice.

This is a deliberate trade against expressive ontological reasoning.
Particles cannot answer queries that require multi-step symbolic
inference across a class hierarchy (*"every animal that is a mammal
that lives in water"*). It can answer queries that require finding
relevant claims about a subject and synthesising them with provenance
intact — which is the agent-knowledge problem in practice, not the
classical-AI reasoning problem the Semantic Web targeted.

## Use cases, risks, comparisons, and future directions

---

# 4. Primary Use Cases: AI Memory You Can Audit and Trust

The launch wedge is one sentence: **AI memory you can audit and
trust.** Capture and recall — persisting what an agent saw and
retrieving it later — is a well-served, heavily-invested problem.
What practitioners describe wanting, in their own words, is the layer
above it: claim-level identity with effective dates and version
relationships ("clause IDs"); an append-only *reconciled ledger*
rather than a memory note rewritten in place with its history pruned;
and memory that lives *outside the agent's control*, because agents
observably fail to write, half-write, or write the wrong thing. That
layer — supersession, provenance, calibrated confidence, decay, audit
— is what the substrate of §§2–3 was built to provide, and it is
where Particles stands.

This section is organised as **two front doors over one substrate**.
Door one (§4.1) is for AI engineers and their agents: the
audit-and-harvest loop that makes an agent's memory managed,
inspected, and consolidated outside the agent's control. Door two
(§4.2) is for everyone else: deposit sources, extract claims, query
with citations, and project the store outward as cited prose — a
wiki, an Obsidian vault, a flashcard deck. The bridge between the
doors is the architecture narrative beneath the wedge: **one
epistemic store serves both the human operator's second brain and the
AI agent's memory.** By serving both goals with one system, the
consensual memory benefits both — a claim the agent learned in last
night's session is citable in the wiki the human reads, and a
correction the human makes at the source is in the agent's context at
the next session start.

"Consensual" is mechanized, not metaphorical. Three mechanisms make a
memory shared between principals who do not fully trust each other
workable. **Write-authority boundaries:** every claim carries its
asserting principal (`asserted_by`); agent-originated writes ride a
server-bound identity whose trust rank is seeded below
operator-asserted claims, and one principal cannot supersede or
retract another's claims unless the operator explicitly enables it.
**Open reconciliation:** when two sources or two principals disagree,
the conflict-resolution ladder (techspec §6.6) surfaces an
`INCONSISTENCY` record for review instead of silently overwriting
either side. **Read-time lenses:** trust weighting, recency decay,
and the as-of instant are applied per observer at query time, never
baked into the stored record — different observers can rank the same
immutable claims differently without rewriting anyone's history.

## 4.1 The audit-and-harvest loop (for AI engineers and their agents)

Two failure modes shape this door's design, both observed in the
field rather than hypothesised. Agents forget to pull: a second brain
behind a pull-only retrieval tool goes unconsulted, while a memory
file that is already in the context window gets used. And agents
forget to write — or half-write, or write the wrong thing — so any
memory whose quality depends on the agent remembering to remember
degrades with prompt discipline. The loop resolves both the same way:
the read side is *pushed* into context, the write side is *harvested*
from what the session already produced, and the agent takes no action
to be remembered.

**One command installs the loop.** `particles init claude-code`
 merges a pair of lifecycle hooks into the harness's
settings. At session start, the store's standing knowledge is pushed
into the agent's context as a compiled digest — one line per ACTIVE
belief, ranked by effective confidence, contested beliefs flagged.
At session end, the hook harvests: the session transcript is
distilled deterministically (no LLM; tool payloads elided; a
credential-redaction pass), and it plus any changed memory files are
deposited into the append-only corpus. Deposits are idempotent by
content hash; a catch-up sweep covers sessions that crashed before
their hook fired; and every failure path degrades to an empty digest,
never a broken session. Everything is local by default — transcripts
are never shipped off-machine without an explicit opt-in.

**The memory file becomes a cited projection.** The harness's
always-loaded `MEMORY.md` gains a machine-owned region regenerated
deterministically from the store: the
top-ranked-by-effective-confidence beliefs as terse bullets, each
carrying a short particle id — the drill-down handle to full
provenance — with contested beliefs rendered flagged rather than
silently omitted. Forgetting becomes a computation instead of an
erasure: a belief that decays or is superseded drops out of the
projection but remains in the store with its provenance — the view
forgets, the store remembers. A drift gate protects the round trip:
edits made inside the machine-owned region are detected and routed
back through harvest and reconciliation, never overwritten.

**The first-run audit is the activation moment.** An earlier revision
of this section stated the linter's ambition as reporting *"your
agent's knowledge base is 12% self-contradictory, here are the
specific conflicts"* against a knowledge base it has never seen
before. That ambition shipped as `particles audit`: point
it at an existing agent-memory directory and it harvests, extracts,
and renders one census — *"Audited 23 memory files → 212 beliefs
about 58 subjects: 4 potential contradictions, 11 likely-duplicate
belief pairs, 7 probably-stale facts."* The hedged labels are
deliberate: these are counts of findings, not of verified defects,
and confidence on this genre is disclosed as self-reported and capped
at read time rather than benchmark-calibrated. The contradiction
check compares claims *across* sources — note A and note B silently
disagreeing, which is the common case in a real knowledge base — by
gating candidate pairs on embedding similarity before the LLM
comparison, so the cost stays bounded as the store grows.
(Staleness that *reads* like a contradiction — a once-true claim a
later source has overtaken — is a recency problem the staleness and
decay checks own, not the contradiction gate.) Every report class
ends with the verb that works it down, and the audited store becomes
the initial store the rest of the loop maintains. `particles lint`
remains the exhaustive diagnostic underneath: staleness, retraction
cascades, corpus link gaps, candidate co-evidential duplicates, and
the semantic contradiction findings the audit counts.

**Consolidation runs itself.** `particles memory consolidate`
 is the nightly dream cycle, scheduled by the operating
system's own scheduler (cron / launchd), running the maintenance
passes in a fixed order: re-check mutable local sources against the
files on disk, so an edited `AGENTS.md` or memory file yields a new
snapshot whose re-extraction retires the prior generation's claims
; extract the deposit backlog; sweep cross-entry document
supersession; run the contradiction and duplicate census scoped to
the *delta* since the previous run, so a quiet night is nearly free;
mine harvested transcripts for usefulness signal, so beliefs the
agent demonstrably acted on gain projection rank; and
re-render the `MEMORY.md` projection. Each run writes a persistent
run record and reports deltas — *"contradictions 4 (+2 since last
run)"* — and a run without an API key degrades to a disclosed
structural-only pass: its contradiction line reads "not probed this
run", never a silent "0".

**Time-travel is a query flag.** `particles query "…" --as-of
2000-01-01` answers the question every audit ultimately
asks: what did the store believe at instant T, and why did it stop
believing it? Each hit that has since been retired carries its
supersession crossing — what replaced it, when, and the evidentiary
basis for that timestamp. Retirement instants are recorded going
forward and reconstructed from supersession pointers, the operator
event log, and validity expiry for history; where an instant is
genuinely unreconstructible the claim is excluded and the exclusion
is counted and disclosed. The lens never manufactures history.

**Switching is one edit.** For agents already running the reference
MCP memory server, `particles memory serve` is a drop-in
compatibility façade: the same nine tools, argument shapes, and
response shapes, so an existing setup and system prompt keep working
unmodified. Underneath, every observation becomes a
provenance-carrying particle attributed to its asserting principal,
and every delete becomes a retraction with an audit trail rather than
a destruction — the deviations from reference behaviour are disclosed
in the tool descriptions themselves.

## 4.2 Cited projections outward (for everyone else)

The second door needs no agent at all. The core loop is three verbs:
`particles deposit <url-or-file>` writes the source into the
append-only corpus; `particles extract --all-pending` turns it into
claim-granularity particles with resolved subjects; `particles query
"question"` answers with effective-confidence-ranked claims and a
cited natural-language response. Everything else in this door is a
projection of that store outward.

A static directory of markdown articles, one per Subject, where every
claim is cited back to its source and confidence is visible per claim,
is the artefact that demonstrates Particles' differentiators without
requiring the reader to install anything, understand the schema, or
even know what a particle is. The wiki articles are the intended
practical demonstration of how provenance-aware synthesis differs from
prose-only approaches. Engineering reviewers can read the article *and*
follow the citations to the corpus to see how the system supports each
claim — making the implementation legible alongside the output.
Shipped in v0.20.0 as `particles export wiki ./output-dir`;
running the exporter against the reference SDK's bundled Numista
corpus produces a small wiki vault you can browse or share without
further setup.

The wiki is one exporter among several: the same store
projects to an Obsidian vault, a Logseq graph, an Anki flashcard
deck, or a Notion database. The Obsidian vault pairs with a companion
plugin that renders lint findings as callouts inside the
vault itself — with link, confirm, and retract write-back — so the
audit surface meets the reader where the notes already live.

For knowledge bases that already exist as markdown, the retrospective
import path (`particles import vault`, shipped in v0.31.1) deposits
the notes unmodified as corpus sources and converts them into
particles through the standard extraction pass — before any workflow
has been rebuilt around structured claims, and without the operator
rebuilding the knowledge base by hand. A simpler onboarding mechanism
— a deterministic parser treating raw markdown sentences as
low-confidence particles with implicit provenance, bypassing
extraction — was considered and rejected. Sentence-split prose yields
context-dependent fragments ("he then moved there two years later")
rather than the self-contained claims the consistency machinery
reasons over, and a uniform confidence value that nobody computed,
stamped on a "claim" that nobody extracted, is precisely the
metadata-theater failure mode Risk #11 (§5) names. Extraction is the
honest path from prose to claims; the retrospective import path makes
it a one-command onboarding step rather than a rebuild.

The two doors share one store, and that is the point. The vault a
human reads and the digest an agent recalls are projections of the
same reconciled substrate: a belief harvested from an agent session
is citable in the wiki, an imported note the human curated ranks in
the agent's next digest, and a contradiction between the two surfaces
as an `INCONSISTENCY` for review instead of whichever writer got
there last winning silently.

## 4.3 An operator's week

§4.1 and §4.2 name the two front doors; this section walks
through what *operating* a Particles store looks like across a
typical week, so the architecture has an operational shape and
not just an architectural one.

* **Continuous (zero-touch).** Deposits trickle in via
  `particles deposit URL` (or iOS Shortcut → inbox watch). Each
  deposit is cheap (a corpus write; extraction happens on the
  store's schedule); operators don't intervene. Agent sessions
  tend themselves: the hooks push the digest at every
  session start and harvest the transcript and memory files at
  every session end, with no operator action and no agent
  cooperation required.
* **Nightly (scheduled).** `particles memory consolidate --if-due`
  runs from launchd / cron: mutable-source refresh, extraction
  catch-up, the supersession sweep, the delta-scoped contradiction
  and duplicate census, utility mining, and the projection
  re-render (§4.1). The morning report is a delta against the
  previous run plus the top of the curation queue — findings the
  operator can work down, not a wall of re-announced state. A
  night without connectivity or a key runs the structural passes
  and says which passes it skipped.
* **Weekly (or before sharing).** A `particles curate` bus-stop
  session works the leverage-ranked queue down a few findings at a
  time; `particles review` resolves `INCONSISTENCY` particles into
  reusable `SourceTrustStatement` policy; `particles export
  <format>` re-renders the vault / wiki. The synthesis cache
   means most subjects skip the LLM; only subjects whose
  particle set changed since the last run pay LLM cost.
* **Quarterly (or on extractor upgrade).** `particles reindex
  --extractor-id <id>` re-runs extraction when an extractor ships
  a new version. The chunk-hash carry-forward skips
  LLM calls on unchanged regions, so the cost is *only* the
  changed-content slice. `particles extractor calibrate <id>`
  refits the temperature scaler when the benchmark suite has
  grown.
* **Annually (or on `SCHEMA_VERSION` bump).** Cross a 1.x → 2.0
  boundary by running `particles db init --force`: the corpus
  survives; the particle store is rebuilt from current extractors
  per the upgrade policy. No re-deposit, no LLM cost beyond what re-extraction
  pays anyway.

The shape is intentional: deposit is cheap and continuous, harvest
is automatic, consolidation is nightly and priced by the day's
delta rather than the store's size, synthesis is cached and only
expensive on change, calibration is opt-in and on operator
timescales, and schema migrations are rare events with a
documented path. Every operation that spends LLM budget unattended
is capped, and every cap, skip, and degradation is disclosed in
its report. Operators who arrive expecting "every operation pays
LLM cost on every read" should plan for the inverse — the read
path is the compiled projection, served from cache.

---

# 5. Known Risks and Failure Modes

The following risks are acknowledged explicitly. They do not invalidate
the proposal but must be managed actively. Each risk is paired with the
design principles (§3) and primary use cases (§4) that mitigate it.

| Rank | Risk | Consequence if unmitigated | Mitigation |
|---|---|---|---|
| 1 | **Extraction fragility** | Drift moved upstream, not eliminated. False precision makes errors harder to detect. | High-fidelity extraction principles (§3.1); benchmark harness (`particles extractor benchmark`) producing precision / recall / calibration-error per extractor against gold-standard suites; extraction as product subsystem (§3.2); re-extraction via source corpus (techspec §7); chunked extraction with carry-forward (§3.1.2). |
| 2 | **Adoption friction** | Teams reject the standard as too heavy relative to augmented markdown. The standard is *correct* but doesn't get tried. | Markdown Exporters (§3.5) including per-Subject wiki articles; one-command integration and the first-run memory audit (§4.1) as the day-one use case; retrospective vault import (§4.2); trivial-cost Deposit operation (techspec §9.1). |
| 3 | **Epistemic overconfidence** | Operators trust the system more than warranted because it looks formal. Errors have higher impact. | Calibrated confidence principles (§3.7): mandatory extraction quality dashboards; confidence calibration provenance; query-time uncertainty disclosure. |
| 4 | **Scale and performance** | Graph traversal, query-time synthesis, and provenance chain depth become expensive at production scale. Highly-documented Subjects can accumulate enough particles to exceed the synthesis LLM's context window even after top-k narrowing (§2.2 trade-off #4). | Explicit scale targets in storage model (techspec §8.4); lazy propagation for retraction; indexing strategy specified in spec. Pre-rendered per-Subject wiki articles (§3.5, §4.2) cache synthesis as a static read-view, bounding the per-query budget; cross-exporter synthesis cache amortises the cost across formats. Intermediate clustering / summary-of-summaries strategies for ultra-dense Subjects are deferred. |
| 5 | **Ontology drift across agents** | Different agents interpret claims differently; schema compliance does not guarantee semantic alignment. | Context fingerprinting for a shared baseline; trust and adversarial model in the multi-agent protocol (§7). |
| 6 | **Source link rot** | Original URLs become unavailable, breaking provenance chains. | Local archive in source corpus (techspec §7); Memento Protocol (RFC 7089) for URI-M references; revisit records for unchanged content. |
| 7 | **Extractor trust misconfiguration** | Untrusted or poorly-calibrated extractors produce particles that receive unwarranted confidence at query time. | Extractor trust weights and allowlists (techspec §6.9); mandatory `extractor_ref` on particles (techspec §6.2); extraction quality dashboards (§3.7). |
| 8 | **Extractor ecosystem monoculture** | Without community incentive to build domain-specific extractors, the ecosystem remains a general-extractor monoculture with uniformly low extraction fidelity across specialised domains. | `extractor_ref` enables usage attribution; calibration_history creates a public quality signal; registries provide community coordination. Current reference extractors are catalogued in the techspec §14.4 reference-extractors table. |
| 9 | **Query-time synthesis cost** | LLM-based synthesis from many particles on every read makes interactive queries slow and expensive at scale. | Pre-rendered per-Subject wiki articles (§3.5, §4.2) as the primary read path for the common case; per-Subject input-hash caching of synthesised output; audience-tier-aware query budgets; the linter and other batch operations bypass synthesis entirely. |
| 10 | **Claim proliferation / cross-source duplication** | Independently extracting the same claim from N sources produces N near-duplicate particles, inflating apparent evidence, cluttering wiki articles, and triggering spurious contradiction lint findings. | Claim identity primitive (§3.4.1) with co-evidential links; lint surfaces candidate near-duplicates for operator review; trust-weighted confidence merging operates over the co-evidential group, not over the raw count. |
| 11 | **Metadata theater** | Operators populate `confidence`, `provenance`, and `uncertainty_nature` fields mechanically — arbitrary numbers, perfunctory source links, default enum values — producing a system that looks rigorous without being calibrated. The structured metadata becomes a costume, not a control surface. | `calibration_source` field surfaces the *origin* of a confidence value (`EXTRACTOR_DIRECT` vs `BENCHMARK` vs `HUMAN_REVIEW`), making low-effort values visible as such; mandatory extraction quality dashboards (§3.7); benchmark suite measuring operator-set values against gold standards; conformance validator flags extractors that populate fields uniformly without variance, a signature of mechanical filling. |
| 12 | **Governance fragmentation** | Independently-developed extractors diverge on confidence semantics, trust-weight scales, uncertainty enums, or subject-resolution conventions. Particles from different extractors look interoperable but cannot be merged or compared without lossy translation. | Conformance contract defines required-vs-recommended-vs-optional field semantics; machine-checkable applicability scopes (§3.8) prevent silent overlap; shared calibration baselines via the benchmark suite; the general extractor is a universal lingua franca that operators can always fall back to. |

---

# 6. Why Existing Approaches Are Insufficient

> **A note on the KG and Nanopublications columns.** The Knowledge
> Graph column is a compressed summary of a tradition with
> substantial variation in practice. Production triplestores do
> carry provenance (named graphs, PROV-O reification) and confidence
> (custom predicates, nanopublications) — the "No" / "Partial"
> entries below mean *not in a minimal LLM-friendly substrate*, not
> *impossible*. The distinction Particles draws against KG stacks is
> therefore one of centre-of-gravity (LLM-native claim extraction vs
> formal ontology engineering), not one of capability per se. A
> reviewer from the KG world should read this table as "Particles
> makes choices that are awkward or expensive in RDF stacks", not
> "RDF stacks cannot do these things." The same fairness applies to
> the Nanopublications column — the closest prior art to the
> particle unit itself. Production nanopublication datasets do carry
> confidence values (e.g. gene–disease association scores published
> as nanopub attributes), so the differentiator is not confidence
> per se: it is *standardized calibration provenance*
> (`calibration_source` as a first-class field) plus *runtime trust
> weighting* of those values at query time, neither of which the
> nanopub model specifies.

| Capability | Classic RAG | LLM-Wiki | Knowledge Graph (RDF/SPARQL) | Nanopublications | Context Graph (Palantir / PKO) | Particles |
|---|---|---|---|---|---|---|
| Primary modelled unit | Document chunk | Wiki page | Class + relationship | Single assertion + provenance (named graphs) | Procedure + execution + decision | Claim + metadata envelope |
| Persistent knowledge accumulation | No | Yes — compiled wiki | Yes — triple store | Yes — published immutable archives | Yes — context graph | Yes — particle store |
| Formal confidence values | No | No | No (reification is awkward; no standard predicate) | Ad-hoc — per-dataset scores; no calibration provenance | Partial — platform-dependent | Yes |
| Uncertainty classification | No | No | No | No | No | Yes (Aleatory/Epistemic) |
| Formal provenance chain | Partial (chunk source) | No | Partial (named graphs, PROV-O) | Yes — assertion / provenance / publication-info graphs | Yes — decision traces with actor/authority | Yes — claim-level (passage-level as Extension B) |
| Reliable contradiction detection | No | Shallow — LLM reads prose | Yes if ontology covers the domain; brittle otherwise | No — published artefacts; no runtime lint loop | Partial — within the modelled process | More reliable — structured inputs to semantic checks |
| Automatic retraction propagation | Manual | Manual | Partial — depends on reasoner | Partial — retraction nanopubs by convention; no store-level cascade | No | Yes — via provenance graph |
| Audience-aware query rendering | No | No | No | No | No | Yes — query-time generation (`EXPERT`/`GENERAL`/`REGULATORY` tiers) |
| Human-readable output | Yes | Yes (always) | No — tabular query results | Partial — viewer tooling (Nanodash) renders the graphs; the stored assertion is triples | Partial — platform UI | Yes (at query time + Markdown Exporters, including wiki articles) |
| Immutable source archive | No | Partial (raw sources layer) | No | No — the assertion is the artefact; the source is a citation | Platform-dependent | Yes — Source Corpus (techspec §7) |
| Re-extractable from source | No | No | No — extraction is lossy and one-way | No | N/A — source is organisational behaviour | Yes — corpus is ground truth; chunked carry-forward for incremental re-extraction |
| Live source monitoring | No | No | No | No | No | Yes — lazy fetch with Memento alignment (techspec §7) |
| Multi-agent interoperability | No | No | Yes — RDF is the interchange | Yes — RDF interchange, content-addressed identifiers | No — typically proprietary | Yes (future extension; §7) |
| Extractor ecosystem with trust model | No | No | No | No | No — typically manual modelling | Yes — registry, machine-checkable applicability, trust chains |
| Shared public archiving | No | No | Partial — Linked Open Data cloud | Yes — decentralised public server network | No — proprietary | Yes — content-addressed shared archive (techspec §3.11, §7.3) |
| LLM-populatable from prose sources | Yes (chunking + embedding) | Yes (LLM synthesises wiki) | No — extraction to triples is notoriously hard | No — RDF assertion graphs require ontology alignment | No — requires manual knowledge engineering | Yes — extraction targets natural-language claims, not strict triples |
| Runtime navigation primitive | Vector similarity | Page link traversal | Graph traversal (SPARQL) | SPARQL / nanopub-index lookup | Graph traversal (constrained by procedure model) | Vector similarity + Subject filter + cached synthesis (§3.11) |
| Time to first useful store | Days (embed and index) | Days (let the LLM compile) | Years (formal ontology + knowledge engineering) | Months (per-domain ontology alignment + curation pipeline) | Years (process elicitation + ontology) | Hours (run extractors) |

> **Adjacent agent-memory systems.** A team evaluating Particles
> today is at least as likely to be comparing it against commercial
> agent-memory layers — Zep/Graphiti, Letta, mem0 — as against the
> research traditions above. Those systems persist agent memories
> across sessions — often as temporal knowledge graphs with
> episode-level references and validity intervals on their edges —
> and they are good at what they optimise for: recall continuity for
> a single agent. What they do not carry is the substance of this
> table's rows: provenance into an immutable, content-addressed
> source corpus, calibration provenance on confidence values, or
> re-extraction that lets the knowledge be rebuilt when extractors
> improve.
> They are omitted as a column because they occupy a different layer
> (session memory vs auditable knowledge substrate), not because they
> are not competitors for adoption.

---

# 7. Future Directions

The single-agent particle store described in Parts I and II is the
foundation. Several extensions are in scope for future versions of the
standard; they are sketched here so readers can see the trajectory.

## 7.1 Multi-Agent Knowledge Exchange

Complex operational workflows are increasingly built from multiple
specialised agents rather than a single monolithic model. Particles
provides the interchange protocol that lets these agents exchange
structured beliefs — with formal confidence, uncertainty, and
provenance — without the lossy translation through natural language
that current multi-agent systems rely on. An agent whose knowledge is
already stored as particles can hand particles directly to another
agent; trust-weighted confidence merging (see §3.4.1 and techspec
§6.9) gives the receiving agent a principled way to combine the
incoming claims with its own store.

Parts of this trajectory have since shipped in the reference SDK: a
round-trippable particle interchange and store-export format, federated cross-store query, and shareable trust
lenses that let one operator adopt another's trust policy with local
overrides. The full multi-agent protocol — including
adversarial behaviour and ontology-drift mitigations across agents —
remains in scope for a future major version and is summarised in the
techspec §12. Risk #5 (ontology drift across agents) catalogues the
known hard problems.

## 7.2 Other extensions

Passage-level provenance (Extension B), richer validity scope
(Extension E), and normative privacy controls (a possible Extension
F) are specified at varying degrees of detail in the techspec and the
companion `roadmap.md`. They extend the schema without
changing its centre of gravity.
