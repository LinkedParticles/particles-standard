# The Particles Standard

> **Particles is shared memory for humans and AI agents.** Each particle is one
> claim, plus what you need to judge it: who said it, where, when, and how
> confident they were. Facts, opinions, and memories are all claims, recorded
> the same way as particles. Particles are not edited or deleted. Particles are
> superseded, retracted, or disputed in the open. How much to trust it is a
> perspective applied at query time, never baked into the record.

Particles is an open standard for structured, auditable knowledge in AI agent
systems: provenance-tracked, claim-granularity beliefs with calibrated
uncertainty. This repository is the **standard itself** — the single public
source of truth for the design. It is independent of any one implementation.

## What's here

| Path | Contents | License |
|---|---|---|
| `docs/spec/whitepaper.md` | The motivation and the model | CC-BY-4.0 |
| `docs/spec/technical-specification.md` | The formal, normative definition | CC-BY-4.0 |
| `artifacts/schemas/` | Normative JSON Schema, JSON-LD context, and trust-lens schema | Apache-2.0 |
| `artifacts/conformance/` | The conformance profile and its ground-truth vectors | Apache-2.0 |
| `tests/conformance/fixtures/` | Behavioral conformance fixtures | Apache-2.0 |

The prose is licensed CC-BY-4.0; the machine-readable artifacts and fixtures are
Apache-2.0. See [`docs/spec/LICENSE`](docs/spec/LICENSE).

## Implementations

The reference implementation is Python, split into two distributions:

| Repo | What it is |
|---|---|
| [`particles-core-py`](https://github.com/LinkedParticles/particles-core-py) | Client layer (`linkedparticles-core`) — store-free schema, extraction, interchange |
| [`particles-engine-py`](https://github.com/LinkedParticles/particles-engine-py) | Engine layer + surfaces (`linkedparticles`) |

An implementation is **conforming** when it passes the conformance suite in this
repository and round-trips interchange — not by virtue of its language or its
repository shape. A second-language implementation is welcome and is, by design,
a test of whether this specification stands on its own.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions are accepted under a
Developer Certificate of Origin sign-off — there is no CLA.
