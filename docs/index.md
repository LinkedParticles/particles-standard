<!--
  The landing page of https://linkedparticles.org — the standard's front door.
  See CONTRIBUTING.md for how changes to this page reach the repository.

  Audience: a curious technical generalist — someone who knows what an LLM is
  and has watched one be confidently wrong, but who may never have heard of
  RAG, Cyc, or bitemporality. The landing stays short and plain; the argument
  lives on why.md, the demos on walkthrough.md. Keep it that way: new detail
  goes on those pages, not here.
-->
# Particles

**A git-like ledger for what an AI system believes.**

Every piece of knowledge is one claim: sourced, dated, and confidence-scored.
As in a git history, nothing is overwritten: a correction *supersedes* the old
claim, a withdrawal *retracts* it, and a disagreement is recorded as a
disagreement — never quietly resolved. The full history of what was believed,
and when, is always there. Trust, doubt, and staleness are applied when you
*read*, never written into the stored claim. And the thing reading and writing
beliefs doesn't have to be an AI: the same store works as a sourced, dated
second brain for a person.

[Why Particles?](why.md){ .md-button .md-button--primary }
[See it work](walkthrough.md){ .md-button }
[Get started](https://docs.linkedparticles.org/user-guide/getting-started/){ .md-button }

## What makes it different

<div class="grid cards" markdown>

-   **Every claim has a source**

    ---

    A particle names the exact document snapshot it came from, so every answer
    is traceable to the evidence it was built from — claim by claim, not
    "sources at the bottom."

-   **Nothing is overwritten**

    ---

    A corrected claim *supersedes* the old one; a withdrawn claim is
    *retracted*, not deleted. Ask the store what it believes now — or what it
    believed on any past date.

-   **Trust is applied when you read**

    ---

    Each claim's stored confidence never changes. Source trust, extractor
    trust, and recency are composed at query time into the confidence used for
    ranking — so you can change your trust policy without rewriting a single
    record.

-   **Disagreements are kept, not resolved silently**

    ---

    When two sources conflict, the conflict itself becomes a visible record to
    review. Your rulings accumulate into a reusable source-trust policy.

</div>

No other memory system we know of ships all four —
[see how it compares](why.md#how-it-compares).

## Take your agent's memory out of its hands

A coding agent remembers by appending lines to a file it writes itself.
Nothing there records where a line came from, whether it is still true, or
that two lines disagree — and the agent decides what is worth keeping.

One command points that memory at a Particles store instead:

```bash
particles init claude-code
```

Remembering stops being the agent's job. Each session *ends* by **harvesting**
what happened into the corpus, so nothing depends on the agent choosing to
save it. Each session *starts* with the store's current view pushed into the
context window — ranked by effective confidence, contradictions flagged
rather than hidden. And on first run it audits the memory you already have:

```text
Audited 23 memory files → 212 beliefs about 58 subjects.

  4 potential contradictions        (2 cross-file, 2 contested at extract time)
  11 likely-duplicate belief pairs  (unjudged similarity candidates; --judge to verify)
  7 probably-stale facts            (5 aged past their source's decay horizon, 2 expired)

  Also: 3 cited sources never captured · 6 beliefs have no resolvable subject
```

Those are questions a text file cannot answer about itself.
[Claude Code memory →](https://docs.linkedparticles.org/user-guide/claude-code/)

## Watch a belief get replaced

In 2006 the IAU demoted Pluto. Below is a real Particles store that learned
*"Pluto is the ninth planet"* in 1996 and the reclassification in 2006. Both
claims are still there: the old one keeps its source, its confidence, and its
dates, and gains a pointer to what replaced it — so the store can answer with
what it believes now, or with what it believed in 2000.

<figure markdown="span">
  <iframe src="demo/pluto-belief-history.html" data-themed
          title="A Particles belief graph: the Pluto supersession chain, with a history toggle"
          loading="lazy"
          style="width: 100%; height: 30rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: var(--p-page);"></iframe>
  <figcaption>
    Click a link between <strong>Pluto</strong> and <strong>Solar
    System</strong> to read the claim behind it. The dashed edge is the retired
    belief; the panel names what replaced it and when. Uncheck
    <em>show history</em> to drop it from view —
    <a href="demo/pluto-belief-history.html">open it full-page</a>.
  </figcaption>
</figure>

The full loop — getting sources in, extracting claims, querying with evidence,
and time-traveling with `--as-of` — is on [See it work](walkthrough.md).

## Measured, not just argued

On LongMemEval, a long-term conversational-memory benchmark, an answering
model given ten retrieved particles (~2,000 characters) scores **92% of what
the same model scores when handed the entire conversation history** — from
under 2% of the tokens — and at that same context budget it answers **1.9×**
as many questions correctly as LLM-written session notes and **2.5×** as many
as retrieval over the raw transcript.
[The numbers, and their caveats →](why.md#measured-not-just-argued)

## Where to go next

<div class="grid cards" markdown>

-   **Use it**

    ---

    Install the SDK and run the deposit → extract → query loop against your
    own sources in a few minutes.

    [Getting started →](https://docs.linkedparticles.org/user-guide/getting-started/)

-   **Read the argument**

    ---

    Why knowledge systems keep failing in the same two ways, what a particle
    is, and the tradeoff this design accepts on purpose.

    [Why Particles? →](why.md)

-   **Read the standard**

    ---

    The whitepaper, the technical specification, the conformance profile, and
    the machine-readable schemas — independent of any one implementation.

    [The standard →](spec/whitepaper.md)

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

## Reference

- [SDK documentation](https://docs.linkedparticles.org/) — user, operator, and
  plugin-author guides, the CLI reference, and the HTTP API contract
- [Security and trust](https://github.com/LinkedParticles/particles-engine-py/blob/main/SECURITY.md)
  — the reporting policy and the disclosed caveats
- [Contributing](https://github.com/LinkedParticles/particles-standard/blob/main/CONTRIBUTING.md)
  — how changes to the standard are proposed and land
