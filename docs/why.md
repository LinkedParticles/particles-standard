<!--
  https://linkedparticles.org/why/ — the argument page.
  Authored in the private development upstream under publish/overlays/; laid
  into the exported tree by the release export. Edit it there.

  This page carries the full pitch: the failure modes, the definition, the
  comparison with other memory systems, the benchmark numbers, and the
  tradeoff. The landing (index.md) stays short and links here.

  The comparison matrix is compiled from each product's public documentation
  and repositories, dated in its caption. Re-verify the cells against current
  public materials before each release export — competitors move fast, and an
  ✗ only ever means "not documented in their public materials at that date."
-->
# Why Particles?

When you ask an AI system a question, you want to know: *Where did this come
from? Is it still true? What does the system actually believe — and what
happens when two of its sources disagree?*

Most AI systems cannot answer any of those questions, because their memory
has no concept of a claim, a source, or a correction. Particles is a memory
built out of exactly those things.

## Two ways to build a knowledge system

At the extremes, machine knowledge has been built in two ways, and each
gives up on half of the problem.

- **Formalize everything.** Projects like Cyc — a forty-year effort to
  hand-write common sense as formal logic — and the hand-built ontologies of
  the early semantic web bet that machines could reason over knowledge once
  every fact was encoded by hand. The reasoning worked; the economics didn't:
  they stalled on the cost of formalizing the world one rule at a time.
- **Formalize nothing.** Most of today's AI systems do the opposite: store
  raw text, cut it into chunks, and retrieve whatever looks similar to the
  question (the technique behind "retrieval-augmented generation"). Fast to
  build — but a chunk of text has no notion of a claim, a source's
  trustworthiness, or a belief that was later corrected.

Plenty of systems live between the extremes — knowledge graphs, entity
extraction, temporal databases. What none of them keep is the *epistemic
record*: which claim, from which source, believed how strongly, corrected by
what. Particles is built around exactly that record. An LLM does the
structuring — it
extracts each claim as a plain sentence, bundled with confidence, provenance,
and canonical **subjects** into a **particle**: the smallest self-contained
unit of knowledge, its uncertainty expressed in the terms of
[PSUM](https://www.omg.org/spec/PSUM/), the OMG's standard for representing
uncertainty. Truth is scoped, not
absolute; contested claims stay visible under an auditable trust policy. A
system's knowledge becomes something you can query, audit, and revise one
belief at a time. Extraction runs on whichever LLM you configure — hosted or
local; adding a provider is configuration, not code — and the store itself is
a local database that never leaves your machine unless you export it.

## Not only for AI

Nothing in the design cares whether the thing reading and writing beliefs is
an AI agent or a person. Deposit articles from your phone's share sheet, keep
a journal, pull in repositories and feeds — then query your own accumulated
knowledge and get answers that cite the exact source each claim came from.
The store exports to [Obsidian, Logseq, and Anki](https://docs.linkedparticles.org/user-guide/exporting/),
so it can sit underneath the tools a "second brain" already lives in — with
the provenance, confidence, and history those tools don't track.

## How it compares

The systems closest to Particles are the agent-memory platforms: Zep (built
on its open-source Graphiti temporal knowledge-graph engine), mem0, Letta,
Supermemory, and Hindsight. Credit where due: Graphiti got temporal
knowledge graphs right early — its edges carry validity intervals, and new
information invalidates old edges instead of deleting them, which enables
genuine point-in-time queries. If you need a hosted temporal graph for agent
state, it is a serious system.

What none of these systems have is the *epistemic* layer: per-claim
provenance back to a source snapshot, a stored confidence that never mutates,
trust applied at read time under a policy you can change, and contradictions
kept as first-class records for a human to rule on. Where a conflict is
handled at all in these systems, it is resolved silently by the model —
"the graph updated itself" — with no record that the disagreement existed and
no way for your judgment of the sources to accumulate. And none of them
publishes an implementation-independent specification: there is no schema or
interchange format that outlives the vendor's own code. (For database people:
the storage discipline underneath is bitemporal — append-only assertions with
as-of reads, in the Datomic/XTDB lineage. The epistemic layer on top is the
new part.)

Compiled August 2026 from each product's public documentation and
repositories. **✗ means "not documented in the product's public materials at
that date" — never a verified absence**; ◐ is a partial mechanism; – means we
could not determine it either way.

| | Particles | Zep / Graphiti | mem0 | Letta | Supermemory | Hindsight |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Claim-granularity memory units | ✓ | ✓ | ✓ | ✗ | ◐ | ✓ |
| Per-claim source provenance | ✓ | – | ✗ | ✗ | ✗ | ◐ |
| Point-in-time ("as-of") queries | ✓ | ✓ | ✗ | ✗ | ✗ | ◐ |
| Corrections preserved as history | ✓ | ✓ | ✗ | ✗ | ✗ | ◐ |
| Per-claim confidence | ✓ | ✗ | ✗ | ✗ | ✗ | ◐ |
| Trust applied at read time, policy changeable | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Contradictions surfaced for human review | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Source-trust policy built from your rulings | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Open, implementation-independent spec + interchange format | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Self-hostable, open source | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ |

Corrections are welcome —
[open an issue](https://github.com/LinkedParticles/particles-standard/issues).
Notes: Graphiti is Apache-2.0 and self-hostable; Zep's hosted product builds
on it. mem0's write path accumulates memories rather than overwriting them,
but records no supersession: contradictory memories coexist, and which one an
agent sees is a ranking outcome. Hindsight's confidence is a single blended
score per opinion; Particles separates the stored value from read-time trust.

## Measured, not just argued

Particles publishes its results on **LongMemEval** (Wu et al., ICLR 2025), a benchmark of 500
questions asked against months of chat history — run against the pipeline the
SDK actually ships, under default configuration, with the baseline that must
not be buried published beside it.

On a 150-question stratified subset, the store's top-10 retrieved claims
cover the labeled evidence **94%** of the time. An answering model given only
those ten claims — about 2,000 characters — answers **73.3%** of questions
correctly, against **79.3%** for the same model handed the *entire*
conversation history: **92% of full-context accuracy from under 2% of the
tokens**. And at that same ~2,000-character read budget, the two standard
alternatives collapse:

| Memory, at the same read-time context budget | Answer accuracy |
|---|---:|
| **Particles** (top-10 claims) | **73.3%** |
| LLM-written session notes | 39.3% |
| Retrieval over the raw transcript | 29.3% |
| *Entire history in context (no budget — the ceiling)* | *79.3%* |

The honest reading, published with the numbers: given an *unlimited* read
budget, whole-session notes recover what claim extraction paraphrases away
and edge ahead — Particles' advantage is **information density**, the most
answer per token, which is exactly what an agent with a context budget needs.
Where the answer must be assembled across many sessions, Particles wins at
any budget.

Vendor-published memory-benchmark numbers are mostly not comparable with each
other — different judge models, different dataset variants, and retrieval
recall is routinely marketed as answer accuracy — so this page does not put
our number beside theirs. Every comparison above holds the dataset, the
judge, the answering model, and the budget fixed, and changes only the
memory.

## The tradeoff

Choosing LLM extraction over hand-formalization has real costs, and they are
part of the design, not fine print.

- **No provable inference.** A formal knowledge base can *derive* new facts
  by rule and prove them correct. Particles can't: its claims are sentences,
  so combining them at query time is the LLM's job, with an LLM's
  fallibility.
- **Extraction noise.** An extractor will sometimes split a claim wrongly,
  drop a hedge, or lose the context that scoped it. The benchmark above
  quantifies one form of this honestly: on single-session lookup questions, a
  verbatim transcript chunk can beat a paraphrased claim.
- **Curation is ongoing.** A belief store accumulates contradictions and
  stale claims the way a codebase accumulates technical debt.

The third cost is also where the design pays off. `lint` surfaces
contradictions, staleness, and gaps as they accumulate; `review` turns each
source disagreement into a ruling; and rulings compound into a reusable
source-trust policy — so the judgment you invest doesn't evaporate into a
one-off edit, it becomes policy that re-ranks every future answer. That
accumulation of *your* judgment over the machine's knowledge is the thing a
pile of text chunks cannot do.

Ready to see the loop run? [See it work →](walkthrough.md)
