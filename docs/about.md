---
title: About
description: Who makes Particles, why it exists, and how to reach the person responsible for it.
---
<!--
  https://linkedparticles.org/about/, the accountability page.
  Authored in the private development upstream under publish/overlays/; laid
  into the exported tree by the release export. Edit it there.

  Purpose: a reader who is about to trust this system with what their agent
  knows can see a name, a reason, and a way to reach a person. Nothing more.
  No photo, no resume, no story arc. Keep it this short.

  House rule for public copy: no em-dashes and no double-hyphens. Use a
  comma, a colon, a period, or parentheses instead.

  The contact address below is mirrored into SECURITY.md and
  CODE_OF_CONDUCT.md. If it changes, change all three.
-->
# About

Particles is built by one person, **Jeff Gage**.

## Why it exists

I got tired of not being able to tell what my tools believed, or why.

A coding agent remembers by appending lines to a file it writes itself.
Nothing there records where a line came from, whether it is still true, or
that two lines disagree. The agent decides what is worth keeping. When one
of those tools was confidently wrong, there was nowhere to look.

Particles is the thing I wanted to look at: every piece of knowledge as one
claim, with its source, its date, and how sure the source was; nothing ever
overwritten; disagreements kept as disagreements rather than quietly
resolved. It is built so that when a system is wrong you can see exactly
why: which claim, from which source, superseded by what. Then you fix it at
the source.

That is also why the project publishes what it publishes: the benchmark
baseline that beats it, the price of the cheaper model it did not adopt, the
gaps in its own conformance. A memory you are supposed to trust should not
be marketed in a way its own ledger would flag.

## What you are looking at

- **An open standard and a reference implementation.** The
  [specification](specification.md) is independent of any one
  implementation and licensed CC-BY-4.0; the Python engine and client
  library are Apache-2.0.
- **Local-first, with no telemetry.** The store is a SQLite file on your
  machine. Nothing phones home. There is no hosted service and no company
  behind this today.
- **Developed in the open since 2026.** The code lives on GitHub, releases
  go to PyPI, and contributions land under the Developer Certificate of
  Origin.

## Reach me

- **Questions, ideas, and rough edges:**
  [GitHub Discussions](https://github.com/LinkedParticles/particles-engine-py/discussions)
  on the reference implementation. Public, so the next person with the same
  question can find the answer.
- **Bugs:** an issue on the relevant repository:
  [engine](https://github.com/LinkedParticles/particles-engine-py/issues),
  [client](https://github.com/LinkedParticles/particles-core-py/issues), or
  [standard](https://github.com/LinkedParticles/particles-standard/issues).
- **Security:** please don't open a public issue. Use the private advisory
  form described in each repository's `SECURITY.md`.
- **Anything else:** [jeff@gage.org](mailto:jeff@gage.org)

I read all of it. Replies can take a few days; it is one person.
