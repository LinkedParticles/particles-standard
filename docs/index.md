---
title: Version control for what your AI knows
description: When an AI agent is confidently wrong, its memory gives you nowhere to look. Particles keeps that memory as sourced, dated claims, and nothing is overwritten.
---
<!--
  The landing page of https://linkedparticles.org, the standard's front door.
  See CONTRIBUTING.md for how changes to this page reach the repository.

  Audience: a curious technical generalist, someone who knows what an LLM is
  and has watched one be confidently wrong, but who may never have heard of
  RAG, Cyc, or bitemporality. The landing stays short and plain; the argument
  lives on why.md, the demos on walkthrough.md. Keep it that way: new detail
  goes on those pages, not here.
-->
<div class="p-hero" markdown>

# Version control for what your AI knows

An AI agent remembers by writing notes to itself, and nothing records where a
line came from, whether it is still true, or that two lines disagree.
{ .p-hero-sub }

</div>

When the agent is confidently wrong, there is nowhere to look. Particles
keeps that memory as a git-like ledger instead: every piece of knowledge is
one claim (sourced, dated, confidence-scored) and nothing is ever
overwritten. A correction *supersedes* the old claim, a withdrawal *retracts*
it, and a disagreement is recorded as a disagreement, never quietly resolved.
Trust, doubt, and staleness are applied when you *read*, never written into
the stored claim. The thing reading and writing beliefs doesn't have to be
an AI, either: the same store works as a sourced, dated second brain for a person.

[Get started](https://docs.linkedparticles.org/user-guide/getting-started/){ .md-button .md-button--primary }
[See it work](walkthrough.md){ .md-button }
[Why Particles?](why.md){ .md-button }

## What makes it different

<div class="grid cards" markdown>

-   **Every claim has a source**

    ---

    A particle names the exact document snapshot it came from, so every answer
    is traceable to the evidence it was built from: claim by claim, not
    "sources at the bottom."

-   **Nothing is overwritten**

    ---

    A corrected claim *supersedes* the old one; a withdrawn claim is
    *retracted*, not deleted. Ask the store what it believes now, or what it
    believed on any past date.

-   **Trust is applied when you read**

    ---

    Each claim's stored confidence never changes. Source trust, extractor
    trust, and recency are composed at query time into the confidence used for
    ranking, so you can change your trust policy without rewriting a single
    record.

-   **Disagreements are kept, not resolved silently**

    ---

    When two sources conflict, the conflict itself becomes a visible record to
    review. Your rulings accumulate into a reusable source-trust policy.

</div>

In our August 2026 survey of the leading memory systems (Zep/Graphiti,
mem0, Letta, Supermemory, Hindsight), none documented all four.
[See the comparison](why.md#how-it-compares).

## Take your agent's memory out of its hands

One command moves a coding agent's memory out of its notes file and into a
Particles store:

```bash
particles init claude-code
```

Remembering stops being the agent's job. Each session *ends* by **harvesting**
what happened into the corpus, so nothing depends on the agent choosing to
save it. Each session *starts* with a small ranked digest (the store's top
standing beliefs, a few thousand tokens at most, never the whole store)
pushed into the context window, contradictions flagged rather than hidden;
everything else stays out of the prompt, retrievable on demand. On first run,
it also audits the memory you already have:

```text
Audited 23 memory files → 212 beliefs about 58 subjects.

  4 potential contradictions        (2 cross-file, 2 contested at extract time)
  11 likely-duplicate belief pairs  (unjudged similarity candidates; --judge to verify)
  7 probably-stale facts            (5 aged past their source's decay horizon, 2 expired)

  Also: 3 cited sources never captured · 6 beliefs have no resolvable subject
```

Those are questions a text file cannot answer about itself. When your
agent gets something wrong, you can see exactly why (which claim, from which
source, superseded by what) and fix it at the source.
[Claude Code memory →](https://docs.linkedparticles.org/user-guide/claude-code/)

## Watch a belief get replaced

In 2006 the IAU demoted Pluto. Below is a real Particles store that learned
*"Pluto is the ninth planet"* in 1996 and the reclassification in 2006. Both
claims are still there: the old one keeps its source, its confidence, and its
dates, and gains a pointer to what replaced it, so the store can answer with
what it believes now, or with what it believed in 2000. (That lens is about
the store's own history: what it believed, and when that changed. Pluto
didn't change in 2006; the belief about it did.)

<figure markdown="span">
  <iframe src="demo/pluto-belief-history.html" data-themed
          title="A Particles belief graph: the Pluto supersession chain, with a history toggle"
          loading="lazy"
          style="width: 100%; height: 30rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: var(--p-page);"></iframe>
  <figcaption>
    Click a link between <strong>Pluto</strong> and <strong>Solar
    System</strong> to read the claim behind it. The dashed edge is the retired
    belief; the panel names what replaced it and when. Uncheck
    <em>show history</em> to drop it from view.
    <a href="demo/pluto-belief-history.html">Open it full-page</a>.
  </figcaption>
</figure>

The full loop (getting sources in, extracting claims, querying with evidence,
and time-traveling with `--as-of`) is on [See it work](walkthrough.md).

## Ask, and see the evidence

Here is the bundled web UI answering a question against that same Pluto store.
The answer is built only from stored claims, and every claim behind it is
listed with its stored confidence, the effective confidence it was ranked with
at read time, its dates, and whether it revises an earlier belief. At the end,
the same answer opens as a graph of the knowledge it consulted.

<figure markdown="span">
  <video src="assets/query-demo.mp4" autoplay loop muted playsinline
         title="The Particles web UI answering a question, with each cited belief's stored and effective confidence"
         style="width: 100%; max-width: 44rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: #f4f6fb;"></video>
  <figcaption>
    Asking <em>"Is Pluto still a planet?"</em> in the web UI that ships with
    the engine. The top-cited belief is the 2006 reclassification, marked
    <em>revises an earlier belief</em>, because the 1996 claim it replaced is
    still in the store.
  </figcaption>
</figure>

## Measured, not just argued

On a stratified 150-question run of LongMemEval, a long-term
conversational-memory benchmark, an answering model given the forty retrieved
particles the shipped default returns (a measured 2,149-token read budget)
answers **80.4%** of questions correctly, against **87.8%** for the same model
handed the *entire* conversation history (scored over 148 questions): **92% of
the ceiling from 1.3% of the tokens**. Give session notes or transcript
retrieval that same budget and they answer **70.0%** and **60.0%**; notes need
about half as much context again to draw level. Squeeze the budget to ten
particles, 542 tokens, and Particles still answers **80.0%**, twice what
either alternative manages there. Lift the budget entirely and session notes
win.
[The numbers, and their caveats →](why.md#measured-not-just-argued)

## Where to go next

<div class="grid cards" markdown>

-   **Use it**

    ---

    `pip install linkedparticles`, then run the deposit → extract → query
    loop against your own sources. The reference implementation lives in
    [`particles-engine-py`](https://github.com/LinkedParticles/particles-engine-py),
    the repository to star, watch, and file issues against.

    [Getting started →](https://docs.linkedparticles.org/user-guide/getting-started/)

-   **Read the argument**

    ---

    Why knowledge systems keep failing in the same two ways, what a particle
    is, and the tradeoff this design accepts on purpose.

    [Why Particles? →](why.md)

-   **Read the specification**

    ---

    The whitepaper, the technical specification, the conformance profile, and
    the machine-readable schemas, independent of any one implementation.

    [The specification →](specification.md)

</div>
