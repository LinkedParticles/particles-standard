<!--
  The landing page of https://linkedparticles.org — the standard's front door.
  See CONTRIBUTING.md for how changes to this page reach the repository.
-->
# Particles

**A git-like ledger for what an AI system believes.**

Every piece of knowledge is one claim: sourced, dated, and confidence-scored.
As in a git history, nothing is overwritten: a correction *supersedes* the old
claim, a withdrawal *retracts* it, and a disagreement stays *disputed* in the
open, so the full history of what was believed, and when, is always there.
Trust, doubt, and staleness are applied as a lens at *query time*, never baked
into the stored claim.

[Read the whitepaper](spec/whitepaper.md){ .md-button .md-button--primary }
[Install the SDK](https://github.com/LinkedParticles/particles-engine-py#install){ .md-button }

## Why Particles?

Ask an AI system a question and you want to know: *Where did this come from?
Is it still true? What does it actually believe, and what happens when two of
its sources disagree?* Two established approaches each give up on half of that.

- **Formalize everything.** Cyc and the semantic web bet that machines could
  reason over knowledge once it was formalized. They stalled on the cost of
  formalizing it by hand.
- **Formalize nothing.** Retrieval-augmented systems store raw text chunks and
  return whatever looks similar. Fast to build, but a chunk has no notion of a
  claim, a source's trustworthiness, or a belief that was later corrected.

Particles takes the path between them. An LLM extracts each claim as a plain
sentence, bundled with confidence, provenance, and canonical **subjects** into
a **particle**: the smallest self-contained unit of knowledge, its uncertainty
grounded in the [PSUM](https://www.omg.org/spec/PSUM/) standard. Truth is
scoped, not absolute; contested claims stay visible under an auditable trust
policy. An agent's knowledge becomes something you can query, audit, and revise
one belief at a time.

## Three ideas carry the design

<div class="grid cards" markdown>

-   **Nothing is overwritten**

    ---

    A corrected claim *supersedes* the old one; retractions cascade as status
    changes; every lifecycle transition is validated and auditable. Version
    control for beliefs.

-   **Trust is a read-time lens**

    ---

    A particle's stored confidence is immutable. At query time it's modulated
    by extractor trust, source trust, and recency decay into an *effective*
    confidence used for ranking. Change your trust policy and nothing gets
    rewritten.

-   **Contradictions are first-class**

    ---

    When two sources disagree, the conflict becomes a visible inconsistency
    record to review, never a silent overwrite. Your rulings accumulate into a
    reusable source-trust policy.

</div>

## See it in action

```bash
uv sync
export ANTHROPIC_API_KEY=sk-ant-...
uv run particles db init

# Deposit a source (file or URL): append-only, SHA-256 snapshotted
uv run particles deposit https://en.wikipedia.org/wiki/Douglas_Lenat

# Extract claim-granularity particles, then ask, showing the evidence
uv run particles extract --all-pending
uv run particles query "What is Cyc, and what was Lenat's role in building it?" \
  --show-particles
```

```text
 CONF   EFF   EXTRACTOR          CONTENT
 1.00   0.49  general-extractor  Lenat worked on the Cyc program at MCC.
 1.00   0.49  general-extractor  Douglas Lenat was the founder and CEO of Cycorp, Inc. …
 1.00   0.49  general-extractor  In 1986, Lenat estimated the effort to complete Cyc …
 1.00   0.49  general-extractor  Lenat became principal scientist of MCC from 1984 to 1994.
 …

## What is Cyc, and What Was Lenat's Role in Building It?

Cyc is a large-scale AI project aimed at building a comprehensive common
sense knowledge base. Douglas Lenat was the central figure behind it,
driving the work across two institutional phases: principal scientist at
MCC (1984-1994) and founder and CEO of Cycorp from 1994 onward …
```

`--show-particles` prints the retrieved claims ranked by **effective
confidence** (the `EFF` column: each particle's immutable stored `CONF`
modulated by source trust and recency *at read time*) above the synthesized
answer, so every answer is traceable to the exact particles it was built
from.

Full walkthrough:
[the SDK's getting-started guide](https://github.com/LinkedParticles/particles-engine-py/blob/main/docs/user-guide/getting-started.md).

## And what did it believe in 2000?

That demo shows the loop. This one shows what makes it different. Because
nothing is overwritten, a store can be asked what it *used to* hold — and be
made to show its own revisions.

Below is a real store, exported to a single self-contained page. Two claims
about Pluto were written into it: *"Pluto is the ninth planet of the Solar
System"*, learned in 1996, and the IAU's 2006 reclassification that replaced
it. Both are still there.

<figure markdown="span">
  <iframe src="demo/pluto-belief-history.html"
          title="A Particles belief graph: the Pluto supersession chain, with a history toggle"
          loading="lazy"
          style="width: 100%; height: 30rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: var(--p-page);"></iframe>
  <figcaption>
    Click either link between <strong>Pluto</strong> and <strong>Solar
    System</strong> to read the claim behind it. The dashed one is the retired
    belief; the panel names what replaced it and when. Uncheck
    <em>show history</em> to drop it from view —
    <a href="demo/pluto-belief-history.html">open it full-page</a>.
  </figcaption>
</figure>

The retired claim is not deleted and not edited. It keeps its source, its
confidence, and its dates, and it gains one thing: a pointer to the claim that
replaced it, stamped with the day that happened. So the store can answer a
question two ways — with what it holds now, or with what it held on a given
date:

```bash
particles query "How many planets are in the Solar System?" --as-of 2000-01-01
# → the planet belief, and one note line: now SUPERSEDED, retired 2006-08-24,
#   superseded by "Pluto is a dwarf planet (IAU 2006 reclassification)."

particles query "How many planets are in the Solar System?"
# → the dwarf-planet belief
```

One flag, and the same question answers from the beliefs held at that instant,
each retired hit naming what replaced it and when.

!!! note "What this does and does not claim"

    `--as-of` is an **assertion-time** lens: *what did this store believe at
    that instant, and when did it stop?* It is not a claim about the world.
    Pluto did not change in 2006 — the belief about it did, and this is the
    record of that revision.

Full walkthrough:
[as-of time travel](https://github.com/LinkedParticles/particles-engine-py/blob/main/docs/user-guide/as-of.md).

## The honest tradeoff

No free lunch. Choosing extraction over hand-formalization means **no provable
inference, some extraction noise, and ongoing curation**. Particles doesn't
hide that cost; it makes it visible and manageable: `lint` surfaces
contradictions and staleness as they accumulate, and `review` turns source
disagreements into a reusable trust policy.

## The three repositories

<div class="grid cards" markdown>

-   **The standard**

    ---

    The whitepaper, the technical specification, the normative schema and
    SHACL artifacts, and the conformance fixtures — independent of any one
    implementation. This site is built from it.

    [particles-standard →](https://github.com/LinkedParticles/particles-standard)

-   **The engine**

    ---

    The reference implementation's state-holding half: corpus, extraction
    pipeline, belief store, the query/lint/review operations, and the API,
    CLI, MCP and web surfaces.

    [particles-engine-py →](https://github.com/LinkedParticles/particles-engine-py)

-   **The client library**

    ---

    The store-free half: schema models with their confidence invariants,
    candidate extraction, conformance validation, and the interchange codec.
    Depend on this to produce or validate particles.

    [particles-core-py →](https://github.com/LinkedParticles/particles-core-py)

</div>

## The standard

- [Whitepaper](spec/whitepaper.md) — the motivation and the design argument
- [Technical specification](spec/technical-specification.md) — the formal
  schema, the operations, and the conformance contract
- [Conformance profile](spec/conformance-profile.md) — what a conforming
  implementation must do
- [Vocabulary](vocab.md) — every term, at the identifier it resolves to

The machine-readable artifacts are served at the identifiers published data
carries, byte-identical to the copies in the repository:

- [`/schemas/particle.schema.json`](https://linkedparticles.org/schemas/particle.schema.json)
- [`/schemas/context.jsonld`](https://linkedparticles.org/schemas/context.jsonld)
- [`/schemas/trust_lens.schema.json`](https://linkedparticles.org/schemas/trust_lens.schema.json)
- [`/schemas/interchange.schema.json`](https://linkedparticles.org/schemas/interchange.schema.json)
- the five SHACL shapes under
  [`/schemas/shacl/`](https://linkedparticles.org/schemas/shacl/ParticleShape.ttl)

## Reference

- [Security and trust](https://github.com/LinkedParticles/particles-engine-py/blob/main/SECURITY.md)
  — the reporting policy and the disclosed caveats
- [Contributing](https://github.com/LinkedParticles/particles-standard/blob/main/CONTRIBUTING.md)
  — how changes to the standard are proposed and land
