# Contributing to the Particles Standard

Thanks for your interest. This repository is the specification — the single
public source of truth for the design of Particles. Changes here are changes to
the standard, so they get more scrutiny than an implementation detail would.

## How this repository is maintained

This public repository is a **published view of a private development
upstream**. Releases are exported to it as scrubbed, per-release snapshots, and
pull requests are **landed by import**, not by pressing the green merge button.

1. **Your PR is reviewed here, on GitHub, as normal.**
2. **When accepted, your commits are imported and replayed individually** —
   `Author` and `Signed-off-by` preserved verbatim, so you appear in the public
   history under your own name and email.
3. **The PR is then closed with a note** pointing at the public commit and the
   release it shipped in; GitHub will not show the "merged" badge. This is
   expected.
4. **Expect your attributed commit within the next release export.**
5. **Always branch from the latest release** so your change applies to a
   freshly-exported baseline.

## What belongs here vs. an implementation

- **Here:** anything a second implementation would need to agree on — schema
  fields and enums, operation semantics, the conformance contract,
  serialization/interchange, confidence math, the status machine. The operating
  test: *could a conforming implementation choose differently and still pass the
  conformance suite and round-trip interchange?* If **no**, it is spec-worthy.
- **In an implementation repo:** anything a second implementation could choose
  differently — package layout, storage choices, plugin shapes, CLI ergonomics.

If a conforming implementation cannot be built without reading a specific
implementation's source, that is a **specification bug** to fix here.

## Signing off your work (DCO)

Every commit must carry a **Developer Certificate of Origin** sign-off — a
`Signed-off-by` trailer certifying you have the right to submit the change under
the applicable license. The full text is in the [DCO](DCO) file. There is **no
CLA**. Add it with `git commit -s`. A red DCO check means the PR is never
imported.

Sign-offs use your **real name and a working email** matching the commit
author. Anonymous contributions, or pseudonymous ones with an unreachable
email, are declined — the certification only means something coming from an
accountable identity.

## Tool-assisted contributions

Contributions produced with AI or agent assistance are welcome on the same
terms as any other. The **human who signs off** certifies the DCO for the
whole change, regardless of what tooling helped produce it. `Co-Authored-By`
trailers naming tools are permitted and carry no legal weight. A sign-off by a
tool — or by a signer who cannot stand behind the certification — is declined.

## Licensing of contributions

By contributing you agree your contribution is licensed under the same terms as
the file you change: the prose under `docs/spec/` is CC-BY-4.0; the
machine-readable artifacts and fixtures are Apache-2.0.

## Normative substance lands in the artifacts

The prose *describes*; the machine-readable artifacts *define*. A contribution
that introduces normative substance — schema fields, enums, constraints,
conformance behavior — must land that substance in the Apache-2.0 artifact
tier (the JSON Schema, the JSON-LD context, the SHACL shapes, the conformance
fixtures), not only in the CC-BY prose. This is what gives every implementer
an express patent license (Apache-2.0 §3) covering everything an
implementation must conform to.

A PR whose normative core exists only in prose will be asked to reshape — so
the normative substance lands in an artifact — before it is imported.
