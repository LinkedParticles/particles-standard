# Review request: Particles whitepaper v2.2 (Draft)

> Paste this as the opening user message in a Gemini or ChatGPT session
> and attach `docs/spec/whitepaper.md`. Drives the v2.2 → 1.0.0
> external review pass per the roadmap.

## Context

You are reviewing the **whitepaper for the Particles standard** — an open
standard and reference SDK for storing AI agent knowledge as
*claim-granularity particles* (natural-language sentences paired with
structured metadata for confidence, provenance, uncertainty, and
lifecycle status). The whitepaper is Part I of a two-document publication;
the Technical Specification (Part II) is a separate document for
implementers and is **not under review here**.

We are preparing for a 1.0.0 release of the reference SDK. The whitepaper
is the product's public face — the document a researcher, framework
author, or potential collaborator reads first to evaluate whether the
approach is worth their time. We need it to hold up to a cold reading.

The v2.1 → v2.2 revision incorporated seven conceptual shifts that
landed in the reference SDK since v2.1 was published. They are summarised
in the "v2.2 revision summary" block at the top of the document. We
want substantive feedback before we cut 1.0.

Prior reviewers (Gemini and ChatGPT) each provided substantive feedback
on the v2.0 → v2.1 revision that drove ~20 commits of follow-up work.
We expect this round to be similarly substantive.

## What kind of feedback we want

### Highest value

1. **Sections that read as overstated** relative to what the document
   actually argues. "You claim X but only show Y" — call out the gap
   and propose either a sharper framing or a scope narrowing.
2. **Conceptual gaps a thoughtful researcher would call out.** Things
   a reader would email about — concepts referenced but not defined,
   comparisons that beg the obvious counter-example, claims that need
   a citation or a worked example.
3. **Framing issues** — places where the doc is technically correct
   but the argument doesn't quite land. Particularly: section openers
   that bury the lede, transitions that feel abrupt, glossary-style
   sentences that don't connect to the surrounding argument.
4. **Internal inconsistency** — places where two sections describe
   the same thing differently, or where one section's framing
   undermines another's.

### Specific call-outs we want your reaction on

- **§3.3 Subjects: The Knowledge Graph Backbone** (new section).
  Does it integrate cleanly with the surrounding §3.2 (extraction
  as product subsystem) → §3.4 (claim granularity) flow? Is the
  "LLM-resolved against external ontology, not hand-curated"
  framing convincing, or does it sound hand-wavy without an
  example?
- **§3.4.1 Claim Identity and the Relation Graph.** Expanded from
  co-evidential-only to a closed registry of six kinds (one ACTIVE,
  five RESERVED). Does the Status column read as honest, or as
  "shipping in name only"? Is the closed-enum + SemVer-lockdown
  story credible to you?
- **§3.9 Link-Shaped Sources Preserve Curation Signal** (new
  section). Reframes the deposit pipeline as treating Reddit / HN /
  Mastodon link-post structure as first-class curation signal — who
  amplified what, when — while explicitly disclaiming any modelling
  of *why* (intent, endorsement, satire). Does the "curation
  signal" framing earn its weight, or feel like over-engineering
  for a niche case?
- **§3.7 Calibrated Confidence — the "mechanical, not aspirational"
  claim.** We argue that temperature-scaling calibration ships as
  a working pipeline. Is the evidence in §3.1.3 (Measurement)
  sufficient backing for that claim, or do we need to say more?
- **The 1.0.0 stability commitment** (paragraph under "Design vs.
  implementation"). Does this read as a credible governance
  commitment, or as a defensive disclaimer? Specifically: does
  the schema-freeze + ADR-0028 / ADR-0079 extension-seam framing
  feel like a real contract or like hedging?

### Out of scope

Please do *not* spend effort on:

- **Implementation details of the reference SDK.** The whitepaper is
  about the standard's design, not the SDK's code. The roadmap and
  ADR archive cover implementation specifics.
- **The Technical Specification.** It's a separate document with
  its own review pass coming next.
- **Anything marked as Extension / RESERVED / post-1.0** (Extension F
  Privacy, Narrative Particles, reserved RelationType kinds).
  Those are deliberate deferrals, not gaps.
- **Copy-editing nits** (typos, comma placement, sentence length).
  We'll do that pass separately. Save attention for substance.

## Output format

Please structure your review as:

```
## Substantive feedback (highest priority)
1. {section reference}: {what's the issue, what would you change, why}
2. ...

## Sectioned reactions (one paragraph per specific call-out)
- §3.3 Subjects: ...
- §3.4.1 Relation Graph: ...
- §3.9 Deposits / Editorial Intent: ...
- §3.7 Calibrated Confidence: ...
- 1.0.0 stability commitment: ...

## Anything else you'd flag
- Gaps, comparisons, missing context, conflicts with adjacent
  literature, framing issues we should think about
```

Aim for substance over comprehensiveness. We'd rather receive 5
sharp critiques than 25 surface observations.
