<!--
  https://linkedparticles.org/walkthrough/, the demo page.
  Authored in the private development upstream under publish/overlays/; laid
  into the exported tree by the release export. Edit it there.

  Every output block on this page is captured from a real run against a real
  store, never hand-written. When the CLI's output format changes, re-run the
  commands and re-capture. The Pluto blocks come from the seed script's store
  (scripts/seed_pluto_demo.py in the engine repo's upstream); the quickstart
  blocks from a two-source store built with the commands shown.
-->
# See it work

One real store, end to end: put sources in, extract claims, ask a question
and get an answer that cites its evidence, then change your trust policy and
watch the ranking follow, without a single stored record changing.

## Deposit → extract → query

Point the store at two accounts of the same story: the Wikipedia article on
Douglas Lenat, and an independent essay on Cyc, the forty-year
formalize-everything project Lenat led. (Install first?
[Getting started](https://docs.linkedparticles.org/user-guide/getting-started/).)

```bash
# Deposit sources (files or URLs): append-only, SHA-256 snapshotted
particles deposit https://en.wikipedia.org/wiki/Douglas_Lenat
particles deposit https://yuxi-liu-wired.github.io/essays/posts/cyc/

# Extract claim-granularity particles from everything pending
particles extract --all-pending

# State how much you trust each source: policy, not data
particles trust set en.wikipedia.org 0.9
particles trust set yuxi-liu-wired.github.io 0.55

# Ask, showing the evidence
particles query "What is Cyc, and what was Lenat's role in building it?" \
  --show-particles
```

Real output, excerpted. The store extracted several hundred claims from the
two sources:

```text
 CONF    EFF   EXTRACTOR               CONTENT
 1.00   0.63   general-extractor       Lenat worked on Cyc at Cycorp since 1994.
 0.95   0.37   github-pages-extractor  Lenat started the Cyc project in 1984.
 1.00   0.63   general-extractor       Douglas Lenat was the founder and CEO of Cycorp, Inc. in Aus…
 0.90   0.35   github-pages-extractor  Lenat devoted 2000 person-years to the Cyc project.
 0.95   0.37   github-pages-extractor  Lenat left his post as a professor at Stanford to start the …
 0.80   0.31   github-pages-extractor  Lenat's approach to Cyc was the same as Minsky's Society of …
 ⋮

⚠ Note: The underlying knowledge base for this topic has relatively low
validation confidence, so some details below should be treated with caution.

**Lenat's Role**

Douglas Lenat was the founder and driving force behind Cyc. He launched the
project in **1984**, leaving his professorship at Stanford to begin work on
it at MCC … After the original MCC consortium wound down around 1995, Lenat
spun Cyc out into a for-profit company called **Cycorp**, based in Austin,
Texas, where he served as founder and CEO. …
```

Read the two left columns. `CONF` is the claim's **stored** confidence,
written once at extraction and never changed. `EFF` is its **effective**
confidence: the stored value composed with source trust and recency *at read
time*. The Wikipedia claims (`0.90` trust) and the essay claims (`0.55`)
rank differently not because their records differ, but because your trust
policy does. Change the policy and the same query re-ranks, with nothing
rewritten. Even the caution note is the trust lens at work: most of this
topic's evidence comes from the lower-trust source, and the answer says so.
Every line of the answer traces to the ranked claims above it, and each
claim to the exact snapshot of the source it came from.

## Ask what it used to believe

Because nothing is overwritten, a store can be asked what it *used to* hold.
Below is a real store that learned *"Pluto is the ninth planet"* in 1996 and
the IAU's 2006 reclassification when it happened. Both claims are still
there.

<figure markdown="span">
  <iframe src="../demo/pluto-belief-history.html" data-themed
          title="A Particles belief graph: the Pluto supersession chain, with a history toggle"
          loading="lazy"
          style="width: 100%; height: 30rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: var(--p-page);"></iframe>
  <figcaption>
    Click a link between <strong>Pluto</strong> and <strong>Solar
    System</strong> to read the claim behind it. The dashed edge is the
    retired belief; the panel names what replaced it and when.
    <a href="../demo/pluto-belief-history.html">Open it full-page</a>.
  </figcaption>
</figure>

The retired claim is not deleted and not edited. It keeps its source, its
confidence, and its dates, and it gains one thing: a pointer to the claim
that replaced it, stamped with the day that happened. That is what lets the
same question answer two ways: with what the store holds now, or with what it held on any
given date:

```bash
particles query "How many planets are in the Solar System?" --as-of 2000-01-01
```

```text
 CONF    EFF   EXTRACTOR   CONTENT
 0.90   0.90   …           Pluto is the ninth planet of the Solar System.

As of the reference date, the Solar System has **nine planets**: Mercury,
Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, and Pluto — with Pluto
recognized as the ninth planet.
↳ Pluto is the ninth planet of the Solar System. — now SUPERSEDED,
  retired 2006-08-24; superseded by 7aa3b9fc: Pluto is a dwarf planet
  (IAU 2006 reclassification).
```

The same question with no flag answers from present belief:

```bash
particles query "How many planets are in the Solar System?"
```

```text
 CONF    EFF   EXTRACTOR   CONTENT
 0.95   0.95   …           Pluto is a dwarf planet (IAU 2006 reclassification).

There are **8 planets** in the Solar System: Mercury, Venus, Earth, Mars,
Jupiter, Saturn, Uranus, and Neptune. This count reflects the IAU's 2006
reclassification, which formally designated Pluto as a *dwarf planet* rather
than a full planet — a status it retains today.
```

A date before the store knew anything answers honestly, too:

```bash
particles query "How many planets are in the Solar System?" --as-of 1980-01-01
```

```text
The store held no beliefs matching this question as of 1980-01-01T00:00:00+00:00.
```

!!! note "What this does and does not claim"

    `--as-of` is an **assertion-time** lens: *what did this store believe at
    that instant, and when did it stop?* It is not a claim about the world.
    Pluto did not change in 2006; the belief about it did, and this is the
    record of that revision.

Full guide:
[as-of time travel](https://docs.linkedparticles.org/user-guide/as-of/).

## Getting knowledge in

Everything enters through one door: `deposit`, which writes the raw source
into an append-only, SHA-256-snapshotted corpus before any claim is
extracted, so every particle can point back to the exact bytes it came from.
What you deposit is up to you:

- **Web pages and files.** `particles deposit <url-or-path>`, as above.
- **From your phone.** A share-sheet shortcut deposits whatever you're
  reading into an inbox for later extraction:
  [depositing from your phone](https://docs.linkedparticles.org/user-guide/inbox/).
- **From your agents.** AI agents read and write the store directly over
  MCP: memories an agent saves become sourced, dated claims instead of lines
  in a text file:
  [Claude Code memory](https://docs.linkedparticles.org/user-guide/claude-code/).
- **Structured sources.** Domain importers (GitHub repositories and gists,
  journals, and more) deposit with richer provenance:
  [the user guide](https://docs.linkedparticles.org/user-guide/).

## The operations, at a glance

Everything above is four of seven operations. Select one to see what it does,
step by step, and what comes out:

<figure markdown="span">
  <iframe src="../operations.html" data-themed
          title="The Particles operations: the core loop and the maintenance passes, step by step"
          loading="lazy"
          style="width: 100%; height: 36rem; border: 1px solid var(--p-border); border-radius: var(--p-radius-lg); background: var(--p-page);"></iframe>
</figure>

## Keeping it healthy

A belief store accumulates contradictions and staleness the way a codebase
accumulates technical debt, so the maintenance loop is part of the product,
not an afterthought:

```bash
particles lint            # surface contradictions, staleness, and gaps
particles review <id>     # rule on a conflict; the ruling becomes trust policy
particles query "..."     # every future answer re-ranks under your rulings
```

`lint` finds the problems; `review` turns each source disagreement into a
ruling; rulings accumulate into a reusable source-trust policy that re-ranks
every future answer. Your judgment compounds.
[Lint and review →](https://docs.linkedparticles.org/operator-guide/lint-and-review/)
