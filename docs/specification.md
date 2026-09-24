---
description: The Particles specification: whitepaper, technical specification, conformance profile, vocabulary, and the machine-readable schema artifacts, served at the identifiers published data carries.
---
<!--
  https://linkedparticles.org/specification/, the specification hub.
  Authored in the private development upstream under publish/overlays/; laid
  into the exported tree by the release export. Edit it there.

  Carries what used to close the landing page: the document list, the
  machine-readable artifact URLs, the repository cards, and the reference
  links, so the landing can stay short. "Specification", not "standard":
  the claim we make is an open spec built for independent implementation;
  "standard" waits for a second implementation.
-->
# The specification

Particles is an **open specification, built for independent implementation**:
the schema, the operations semantics, the conformance contract, and the
machine-readable artifacts are published independently of the reference
implementation, so a second implementation has something precise to conform
to. Today there is one implementation, the
[reference engine](https://github.com/LinkedParticles/particles-engine-py),
and the specification is a working draft; we'll call it a standard when
someone else has implemented it too.

**Status:** whitepaper and technical specification **v2.2 (draft)** ·
conformance profile **1.1** · reference implementation on
[PyPI](https://pypi.org/project/linkedparticles/).

## The documents

- [Whitepaper](spec/whitepaper.md): the motivation and the design argument
- [Technical specification](spec/technical-specification.md): the formal
  schema, the operations, and the conformance contract
- [Conformance profile](spec/conformance-profile.md): what a conforming
  implementation must do
- [Vocabulary](vocab.md): every term, at the identifier it resolves to

## The machine-readable artifacts

Served at the identifiers published data carries, byte-identical to the
copies in the repository (a deploy-time check re-verifies this daily):

- [`/schemas/particle.schema.json`](https://linkedparticles.org/schemas/particle.schema.json)
- [`/schemas/context.jsonld`](https://linkedparticles.org/schemas/context.jsonld)
- [`/schemas/trust_lens.schema.json`](https://linkedparticles.org/schemas/trust_lens.schema.json)
- [`/schemas/interchange.schema.json`](https://linkedparticles.org/schemas/interchange.schema.json)
- the five SHACL shapes:
  [`ParticleShape`](https://linkedparticles.org/schemas/shacl/ParticleShape.ttl) ·
  [`SubjectShape`](https://linkedparticles.org/schemas/shacl/SubjectShape.ttl) ·
  [`ProvenanceChainShape`](https://linkedparticles.org/schemas/shacl/ProvenanceChainShape.ttl) ·
  [`CorpusSnapshotShape`](https://linkedparticles.org/schemas/shacl/CorpusSnapshotShape.ttl) ·
  [`TrustStatementShape`](https://linkedparticles.org/schemas/shacl/TrustStatementShape.ttl)

## The three repositories

<div class="grid cards" markdown>

-   **The specification**

    ---

    The whitepaper, the technical specification, the normative schema and
    SHACL artifacts, and the conformance fixtures, independent of any one
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

- [SDK documentation](https://docs.linkedparticles.org/): user, operator, and
  plugin-author guides, the CLI reference, and the HTTP API contract
- [Security and trust](https://github.com/LinkedParticles/particles-engine-py/blob/main/SECURITY.md):
  the reporting policy and the disclosed caveats
- [Contributing](https://github.com/LinkedParticles/particles-standard/blob/main/CONTRIBUTING.md):
  how changes to the specification are proposed and land
