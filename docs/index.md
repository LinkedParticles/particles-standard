---
title: Version control for what your AI knows
description: "Your agent's memory still says what was true last month. Particles keeps sourced, dated claims: when a source changes, the old claim is superseded, not erased."
hide:
  - navigation
  - toc
---
<!--
  The landing page of https://linkedparticles.org, the standard's front door.
  See CONTRIBUTING.md for how changes to this page reach the repository.

  Audience: a curious technical generalist, someone who knows what an LLM is
  and has watched one be confidently wrong, but who may never have heard of
  RAG, Cyc, or bitemporality. The landing stays short and plain; the argument
  lives on why.md, the demos on walkthrough.md. Keep it that way: new detail
  goes on those pages, not here.

  The README demo below is built from real records, never hand-written: a
  scratch store that deposited and extracted a README, then deposited and
  extracted it again after its Deploying section was edited. Every claim, id,
  status pair and event line is copied from that store, and the collapsed
  block shows every command that built it. The query block, folded under the
  demo, is that store's answer to one question, also captured, not written.
  Re-capture all of it together if the CLI's output or the claim text changes.
  Raw terminal output stays folded: a visitor reads the demo and the
  sentences, and opens the output only to check them. Its styles are the .p-demo rules
  in stylesheets/particles.css; it needs no script.

  Both sidebars are hidden here (front matter `hide`) so the hero and the demo
  get the full width; every other page keeps the documentation layout.
-->
<div class="p-hero" markdown>

# Your agent still believes what used to be true

Particles gives your agent a memory you can inspect and correct: see where a
remembered claim came from, what changed, and what replaced it.
{ .p-hero-sub }

</div>

An agent that remembers by writing to a notes file keeps the line and loses
the rest: where it came from, when it stopped being true, what replaced it.

[Connect Claude Code](https://docs.linkedparticles.org/user-guide/claude-code/){ .md-button .md-button--primary }
[See it work](walkthrough.md){ .md-button }

## Watch a README change

A team moves its deploys from a shell script to GitHub Actions and edits the
README. Below is what a real Particles store recorded, in three steps.

<div class="p-demo">
<input class="p-demo__radio" type="radio" name="p-demo-stage" id="p-demo-s1" aria-label="Step 1: old memory">
<input class="p-demo__radio" type="radio" name="p-demo-stage" id="p-demo-s2" aria-label="Step 2: the README changes">
<input class="p-demo__radio" type="radio" name="p-demo-stage" id="p-demo-s3" aria-label="Step 3: the old claim is superseded" checked>
<div class="p-demo__steps" aria-hidden="true">
<label for="p-demo-s1"><span class="p-demo__n">1</span> Old memory</label>
<label for="p-demo-s2"><span class="p-demo__n">2</span> README changes</label>
<label for="p-demo-s3"><span class="p-demo__n">3</span> Old claim superseded</label>
</div>
<div class="p-demo__panel p-demo__panel--1">
<p class="p-demo__lede">The store reads <code>README.md</code> and keeps a snapshot of it. These are the claims it took from the Deploying section.</p>
<div class="p-demo__source"><div class="p-demo__file">README.md <span>snapshot bbf9e423</span></div><pre>## Deploying

Deploy to production by running `./deploy.sh` from a clean checkout of `main`.
The script builds the container image, pushes it to the registry, and restarts
the service on the production host.</pre></div>
<ul class="p-demo__claims">
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">Active</span><p>Tally is deployed to production by running <code>./deploy.sh</code> from a clean checkout of <code>main</code>.</p><div class="p-demo__meta">from README.md, snapshot bbf9e423</div></li>
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">Active</span><p>The <code>./deploy.sh</code> script builds the container image, pushes it to the registry, and restarts the service on the production host.</p><div class="p-demo__meta">from README.md, snapshot bbf9e423</div></li>
</ul>
</div>
<div class="p-demo__panel p-demo__panel--2">
<p class="p-demo__lede">The README is deposited again. It is the same corpus entry with a new snapshot, and the old snapshot is kept, byte for byte.</p>
<div class="p-demo__source"><div class="p-demo__file">README.md <span>snapshot 1f37d56d</span></div><pre>## Deploying

<del>Deploy to production by running `./deploy.sh` from a clean checkout of `main`.</del><del>The script builds the container image, pushes it to the registry, and restarts</del><del>the service on the production host.</del><ins>Production deploys run through the `deploy` GitHub Actions workflow, which</ins><ins>starts on every merge to `main`. Do not deploy from your own machine;</ins><ins>`deploy.sh` is retired.</ins></pre></div>
</div>
<div class="p-demo__panel p-demo__panel--3">
<p class="p-demo__lede">Extracting the new snapshot replaces the old claim. The old one is kept, with its source and its dates, and points to what replaced it.</p>
<ul class="p-demo__claims">
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">Current</span><p>Tally's production deploys run through the <code>deploy</code> GitHub Actions workflow.</p><div class="p-demo__meta">from README.md, snapshot 1f37d56d</div></li>
<li class="p-demo__claim p-demo__claim--retired"><span class="p-demo__chip p-demo__chip--superseded">Replaced</span><p>Tally is deployed to production by running <code>./deploy.sh</code> from a clean checkout of <code>main</code>.</p><div class="p-demo__meta">from README.md, snapshot bbf9e423 · replaced by the claim above</div></li>
</ul>
<details class="p-demo__more">
<summary>Inspect all five records</summary>
<ul class="p-demo__claims">
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">Current</span><p>Tally's production deploys run through the <code>deploy</code> GitHub Actions workflow.</p><div class="p-demo__meta">61e4292b · ACTIVE · confidence 0.93 · supersedes f1213149</div></li>
<li class="p-demo__claim p-demo__claim--retired"><span class="p-demo__chip p-demo__chip--superseded">Replaced</span><p>Tally is deployed to production by running <code>./deploy.sh</code> from a clean checkout of <code>main</code>.</p><div class="p-demo__meta">f1213149 · PROVENANCE_STALE / SUPERSEDED_BY_UPDATE · confidence 0.90 · a newer claim from the same source replaced it</div></li>
<li class="p-demo__claim p-demo__claim--retired"><span class="p-demo__chip p-demo__chip--superseded">Retired</span><p>The <code>./deploy.sh</code> script builds the container image, pushes it to the registry, and restarts the service on the production host.</p><div class="p-demo__meta">1b5f283a · PROVENANCE_STALE / RETRACTED_DEPENDENCY · confidence 0.90 · no current snapshot of the README states it</div></li>
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">New</span><p>The <code>deploy</code> GitHub Actions workflow starts on every merge to <code>main</code>.</p><div class="p-demo__meta">cacede90 · ACTIVE · confidence 0.93</div></li>
<li class="p-demo__claim"><span class="p-demo__chip p-demo__chip--active">New</span><p><code>deploy.sh</code> is retired.</p><div class="p-demo__meta">de299c9a · ACTIVE · confidence 0.93</div></li>
</ul>
</details>
</div>
</div>

Ask the store how to deploy and it answers from the current claim only. The
replaced one stays on record and is no longer offered. This works when the
store can match the changed line to an earlier claim from the same document.
A change stated in a *separate* document is not caught this way yet: the old
claim and the new one both stay active.

??? example "The store's answer, as captured"

    ``` { .console .p-wrap }
    $ particles query "How do we deploy Tally?" --show-particles
     CONF    EFF     AGE  EXTRACTOR                     CONTENT
    ----------------------------------------------------------------------------------------------------
     0.93   0.65      1d  general-extractor             Tally's production deploys run through the `deploy` GitHub A
     0.88   0.62      1d  general-extractor             Running `make dev` makes Tally available locally at http://l
     0.93   0.65      1d  general-extractor             Tally is a small web app for splitting shared expenses.
     0.93   0.65      1d  general-extractor             `deploy.sh` is retired.
     0.93   0.65      1d  general-extractor             The `deploy` GitHub Actions workflow starts on every merge t

    Tally's production deploys run through the `deploy` GitHub Actions workflow. That workflow starts on every merge to `main`, so merging to `main` is what triggers a production deploy. The old `deploy.sh` script is retired and should no longer be used.

    For local use, running `make dev` makes Tally available at http://localhost:3000. That is for local development, not production deployment.

    The knowledge base doesn't cover other details, such as manual triggers, approval steps, or rollback procedures. Some of these particles are also uncalibrated, so the answer may be incomplete.
    ```

    `CONF` is the confidence stored with each claim, which never changes.
    `EFF` is the value the answer was ranked with: the stored one after
    extractor trust, source trust and age are applied at read time. An
    extractor starts at a trust weight of 0.7, so every row reads lower than
    it was stored. The answer's last sentence says the same thing: these
    confidences are the extractor's own, not yet calibrated against labelled
    data.

??? example "Every command that built the store, with real output"

    ```console
    $ particles db init
    Database tables created.
    $ particles deposit README.md --mutability MUTABLE
    entry_id:    4ff05a50-4f5d-400e-98a4-d806aab6aef7
    snapshot_id: bbf9e423-018d-4fff-b9a8-a37a598795f6
    $ particles extract --all-pending
    Extracting 1 pending snapshot(s)…
      4ff05a50…/bbf9e423…  4 particles
    $ # Edit README.md: the Deploying section now names the GitHub Actions workflow.
    $ particles deposit README.md --mutability MUTABLE
    entry_id:    4ff05a50-4f5d-400e-98a4-d806aab6aef7
    snapshot_id: 1f37d56d-01d6-493f-a062-d1fe575b2bd3
    $ particles extract --all-pending
    Extracting 1 pending snapshot(s)…
      4ff05a50…/1f37d56d…  4 particles (1 duplicate(s) suppressed)
    $ particles events list
    2026-10-30 20:09  4cc50774…  EXTRACT_RUN  by cli:extract
    2026-10-30 20:09  aa4e86b4…  CLAIMS_RETIRED  by extract
        reason: generation cascade: no current snapshot of the entry states the claim
        refs:   corpus_entry:4ff05a50…, particle:1b5f283a…, particle:808d4b03…
    2026-10-30 20:09  2c28bedd…  UPDATE_SUPERSESSION  by extract-pipeline
        reason: Rung 2.5 (ladder): f1213149 superseded by 61e4292b
        refs:   particle:61e4292b…, particle:f1213149…
    2026-10-30 20:08  c82ebbf8…  EXTRACT_RUN  by cli:extract
    ```

    Each `extract` also printed its cost estimate and token usage, left out
    here; the two runs together cost about seven US cents. The README's
    other two sections produced claims too. The `make dev` line was read
    again in new wording, so its first reading (`808d4b03`) retired beside
    `1b5f283a`.

## 92% of full-history accuracy from 1.3% of the tokens

<div class="p-stats">
<div class="p-stat">
<span class="p-stat__name">Particles: the claims it retrieves</span>
<span class="p-stat__figure"><span class="p-stat__value">2,149</span> tokens read</span>
<span class="p-stat__meter" aria-hidden="true"><span style="width: 1.3%"></span></span>
<span class="p-stat__figure"><span class="p-stat__value">80.4%</span> answered correctly</span>
<span class="p-stat__meter" aria-hidden="true"><span style="width: 80.4%"></span></span>
</div>
<div class="p-stat">
<span class="p-stat__name">The entire conversation history</span>
<span class="p-stat__figure"><span class="p-stat__value">166,725</span> tokens read</span>
<span class="p-stat__meter" aria-hidden="true"><span style="width: 100%"></span></span>
<span class="p-stat__figure"><span class="p-stat__value">87.8%</span> answered correctly</span>
<span class="p-stat__meter" aria-hidden="true"><span style="width: 87.8%"></span></span>
</div>
</div>

The same model answered the same questions both ways, on a stratified
150-question sample of LongMemEval, a long-term conversational-memory
benchmark (the full-history run was scored over 148 of the 150). Given
Particles' token budget, session notes answer **70.0%** and transcript
retrieval **60.0%**. With no budget at all, session notes come out ahead.
[The numbers and their caveats →](why.md#measured-not-just-argued)

Whether a memory keeps up as facts change is measured separately, in
[trip versus move](https://docs.linkedparticles.org/benchmarks/trip-vs-move/)
and [memory rot](https://docs.linkedparticles.org/benchmarks/rot/).

## Take your agent's memory out of its hands

One command moves Claude Code's memory out of its notes file and into a
Particles store:

```bash
pip install linkedparticles
particles init claude-code
```

Each session *ends* by harvesting what happened into the store, so nothing
depends on the agent choosing to save it. Each session *starts* with a small
ranked digest of the store's standing beliefs, contradictions flagged rather
than hidden. On first run, it also audits the memory you already have:

```text
Audited 23 memory files → 212 beliefs about 58 subjects.

  4 potential contradictions        (2 across files, 2 contested at extract time)
  11 likely-duplicate belief pairs  (unjudged similarity candidates; --judge to verify)
  7 probably-stale facts            (5 aged past their source's decay horizon, 2 expired)

  Also: 3 cited sources never captured · 6 beliefs have no resolvable subject
```

It needs Python 3.11 or later and a model to read sources with: an Anthropic
API key, or any OpenAI-compatible endpoint, local models included. The audit
prints its cost estimate before it spends anything; measured on the default
hosted model, it came to about five US cents a memory file
([what a run costs](https://docs.linkedparticles.org/benchmarks/cost/)). The
store is a file on your machine, and the same one serves
[Codex](https://docs.linkedparticles.org/user-guide/codex/) and
[Cursor and other MCP clients](https://docs.linkedparticles.org/user-guide/coding-agents/).
[Claude Code memory →](https://docs.linkedparticles.org/user-guide/claude-code/)

## What makes it different

<div class="grid cards" markdown>

-   **Every claim has a source**

    ---

    A claim names the exact snapshot of the document it came from, so every
    answer traces back to its evidence, claim by claim.

-   **Nothing is overwritten**

    ---

    A replaced claim is *superseded* and a withdrawn one *retracted*, never
    deleted. Ask what the store believes now, or what it believed on any past
    date.

-   **Trust is applied when you read**

    ---

    A claim's stored confidence never changes. Source trust and recency are
    applied at query time, so a new trust policy rewrites no records.

-   **Disagreements stay visible**

    ---

    When two sources conflict, the conflict becomes a record for you to
    review, and your rulings become a reusable source-trust policy.

</div>

In our August 2026 survey of the leading memory systems (Zep/Graphiti,
mem0, Letta, Supermemory, Hindsight), none documented all four.
[See the comparison](why.md#how-it-compares). The same store works for a
person, too, as a sourced, dated second brain.

## Where to go next

- **Use it:** [Getting started](https://docs.linkedparticles.org/user-guide/getting-started/)
  runs the deposit, extract and query loop on your own sources. The reference
  implementation lives in
  [`particles-engine-py`](https://github.com/LinkedParticles/particles-engine-py),
  the repository to star, watch, and file issues against.
- **Read the argument:** [Why Particles?](why.md) covers why knowledge systems
  keep failing in the same two ways, and the tradeoff this design accepts on
  purpose.
- **See it work:** [the walkthrough](walkthrough.md) follows one store end to
  end, including a store asked what it believed in 2000.
- **Read the specification:** [the specification](specification.md) holds the
  whitepaper, the technical specification, the conformance profile and the
  machine-readable schemas, independent of any one implementation.
