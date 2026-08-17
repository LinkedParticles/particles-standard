# Particles Whitepaper — Revision History

The per-round change log formerly appended to `whitepaper.md`, relocated here
so the whitepaper stays focused on the standard. These notes serve reviewers
diffing one revision against another; first-time readers can ignore them.

---

# Appendix: Revision History

Each whitepaper revision corresponds to a round of internal and / or
external review. Round summaries are recorded here so reviewers
diffing against a prior revision can see what changed and why
without scrolling through unrelated front-matter.

## v2.2 (Draft, May 2026)

Initial v2.2 substantive pass — added §3.3 "Subjects: The Knowledge
Graph Backbone" introducing the canonical-entity catalogue and the
LLM-resolved external-ontology alignment that had been load-bearing
since v0.4 but unstated in the whitepaper. Expanded §3.4.1 from
co-evidential-only to the full relation-kind registry
(CO_EVIDENTIAL active; CONTRADICTS, BOOSTS, QUOTES, REPLIES_TO,
MENTIONS reserved). Added §3.9 "Link-Shaped Sources Preserve
Curation Signal" documenting link-shaped-post follow
pipeline. Updated §3.1.2 (paragraph-bounded structural chunking), §3.5 (Logseq exporter + cross-exporter synthesis cache
), and §3.7 (calibration shipped mechanically
). Added the 1.0.0 stability commitment to the
front-matter governance framing. §3 expanded from 10 design
principles to 11 — readers comparing against v2.1 should expect a
one-section drift from §3.4 onward.

## v2.2 r2 — Gemini pre-review pass

Softened §1.2's framing of consistency checking from "solves" to
"bounds"; hoisted §3.1.3's single-fixture baseline caveat earlier;
added a combinatorial-context-limit trade-off to §2.2 and Risk #4;
added a concrete Wikidata example to §3.3; clarified §3.7's
pipeline-versus-data-coverage distinction; sharpened the §2.2 /
Risk #9 framing of pre-rendered wiki articles as a compiled
read-view over the particle store.

## v2.2 r3 — ChatGPT pre-review pass

Added a §3.3 "identity is contractual, not solved" paragraph
naming the disambiguation failure modes (name collisions,
top-result brittleness, ontology drift) and the standard's posture
(deterministic / overridable / provenance-tracked); restructured
§3.4.1's prose to split governance (the registry's interop
guarantee) from shipped functionality (CO_EVIDENTIAL only),
removing the "shipping in name only" reading; reframed §3.9 from
"editorial intent" to "curation signal" with an explicit non-goal
disclaiming intent modelling and a paragraph on envelope-vs-target
attribution; added §3.6 worked examples (near-duplicate news +
SEC, conflicting numismatic weights); added a §6 KG-column caveat
acknowledging that production triplestores carry provenance /
confidence in practice; restructured the 1.0.0 stability paragraph
into four explicit commitments and moved CLI migration mechanics
out of the front-matter; hoisted the compiled-read-view framing
into "What Particles Is"; added a §3.7 worked example reporting
the real calibration run on the v0.21.0 Numista seed (ECE 0.0471 →
0.0953 at T = 10.0 ceiling).

## v2.2 r4 — Claude pre-review pass + new code anchors

Restructured the §3.7 calibration vignette around three benchmark
suites (Numista, Reddit, HN) rather than one, replacing the
single-fixture caveat narrative with a three-row table that
demonstrates calibration delivers ~85–89 % ECE reduction on
LLM-driven extractors while admitting the bounded-fit ceiling is
the binding constraint across all three runs. Anchored §3.3's
"identity is contractual, operator-overridable" claim to the
shipped `particles subjects split` verb (v0.43.0)
rather than to a deferred R1.1 roadmap item. Anchored §3.9's
curation-signal principle to the shipped `particles corpus links
list` audit verb (v0.42.5) — the first downstream consumer of
`corpus_follow_edges`, converting §3.9 from architecture-only to
architecture-with-payoff. Clarified "What Particles Is" as
"narrower than a *formal-ontology* knowledge graph" so the §3.3
sparse-property-graph framing doesn't read as self-contradictory.
Added a §3.4.1 sentence explaining symmetric/asymmetric as the
*storage-invariant* axis. Acknowledged the §3.9 depth-1 cap as
shape-blind (a Reddit-to-Reddit follow is one hop just like a
Reddit-to-news follow). Renamed the 1.0.0 stability axes to
"namespace-frozen at 1.0" / "behavior-additive at minor" so the
two senses of "frozen" no longer overload; added the
unknown-fields-ignored backward-read story. Added a §4.3 "An
operator's week" walkthrough so the architecture has an
operational shape and not just an architectural one. Named the
two-paths architecture (structural ops vs presentation ops)
explicitly under §2 so readers don't have to assemble it across
§3.6 / §3.7 / §4. Reframed the §1.1 Karpathy gist callout from
"circular validation" to "dogfooding" — the SDK ingesting its
motivating source is not evidence the SDK is correct. Moved the
revision-history blocks to this appendix so the front-matter no
longer competes with the substantive content for a cold reader's
attention.

## v2.2 r5 — Retrospective-parser truth sync (2026-06 review F1.1)

Synced §3.5 and §4.1 with the shipped reality the 2026-06 external
review's F1.1 flagged: the retrospective onboarding path shipped in
v0.31.1 as `particles import vault`, but both sections still
described it as "not yet built." Both now describe the shipped
mechanism (deposit existing notes unmodified, convert via the
standard extraction pass). Retired the "treat markdown content as
low-confidence particles with implicit provenance" mechanism promise
from §4.1 and recorded why it was rejected rather than built:
sentence-split prose yields context-dependent fragments instead of
self-contained claims, and uniform stamped confidence is the Risk #11
metadata-theater failure mode. No design change — the sections now
describe what the SDK does.

## v2.3 (June 2026) — epistemic-stance thesis + prior-art pass (2026-06 review F1.1 / F1.2)

Added the four-paragraph epistemic-stance block to "What Particles
Is": the founding premise (no fundamental fact/opinion distinction —
only claims true for a group of observers, for a period of time); the
two-scopes split (temporal scope carried on the particle, observer
scope computed at read time through the trust layer, per the
substrate-plus-lens invariant and the shareable lenses of
the trust layer; the Cyc / Wikidata / nanopublications lineage with LLM
extraction plus the trust model as the missing enabler; and the
anti-relativism framing — the fact/opinion distinction recovered as a
measurement, with the per-claim contestedness signal deferred as
future work. Added the closest prior art the 2026-06 external review
flagged as missing (F1.2): a Nanopublications column in the §6
comparison table, an extension of the fairness caveat (production
nanopub datasets do carry confidence scores; the differentiator is
standardized calibration provenance plus runtime trust weighting), a
note on adjacent commercial agent-memory systems (Zep/Graphiti,
Letta, mem0), the claim-granularity lineage (Cyc microtheories,
nanopublications, micropublications) in §1, and the two corresponding
entries in the techspec reference list. Reframed §4.1 to lead with
the shipped linter surface and gave the "12 % self-contradictory"
hook its scope caveat — same-source contradiction detection ships,
cross-source detection is open work — re-ordering the
honesty without deleting the vision (F1.1). Refreshed stale anchors:
v0.2 → v0.61 implementation framing, one-suite → three-suite
benchmark coverage (§3.1, §3.1.3, §3.7), the §3.4.1 registry as-of,
and the §7.1 future-work hedge updated only where reality changed
(interchange, federated query, and trust lenses have shipped; the adversarial multi-agent protocol has not).
Stepped the document version to v2.3 rather than another r-pass
because the thesis block is a substantive addition, not a
review-response edit.

## v2.3 r2 (June 2026) — roadmap-pointer sync

Editorial truth-sync, no design content changed. The change restructured
the companion `roadmap.md` from RFC 2119-keyword prose sections into
per-milestone gate tables plus a forward queue. The Reader's Guide row
for the roadmap now describes that shape (tables with a lint-checked
done column as the status record, plus the forward queue) instead of
the retired section organisation. Two pointers claiming the reference
extractors are "catalogued in `roadmap.md`" (§3.2 and Risk #8) now
point at the techspec §14.4 reference-extractors table — the actual
catalogue — since the roadmap only ever carried a handful of extractor
work items, and post-restructure carries rows only.

## v2.3 r2 — final owner review (June 2026)

The owner's final read before the 1.0.0 cut, closing the milestone gate.
Reframed the thesis block's second paragraph around the
facts-on-the-particle / judgments-in-the-lens line: the particle
carries temporal *facts*; recency decay is a read-time *judgment*
(operator-level today; lens migration deferred), and the
trust layer's distrust-only scope is disclosed in place (the positive
endorsement half is a later decision's child). Led the
use-cases paragraph with the belief-ledger framing the README and
docs index adopted, naming the first-party use — the AI system's own
belief substrate — ahead of the linter and wiki surfaces. Simplified
§4.1 to describe what is built and what is intended, dropping
doc-history narration per the standing editorial rule that this
appendix is the only home for draft history. Relabelled the §6 cost
row to "Time to first useful store" (the old label priced Particles'
ingestion against competitors' modelling). §6 fairness fixes: the
nanopublication human-readable cell softened to Partial (viewer
tooling on both sides; the substrate difference stated in-cell), and
the agent-memory note now concedes episode-level references and
validity intervals, narrowing the differentiator to the immutable
content-addressed corpus, calibration provenance, and re-extraction.
P1-1 (the thesis resting on the deferred contestedness instrument)
was resolved by prioritizing the instrument rather than softening the
claim — promoted to a proposed ADR.

## v2.3 r3 (June 2026) — relation-registry + version-anchor truth-sync

Editorial truth-sync, no design content changed. Replaced the stale
reference-SDK version anchors (v0.61) with version-free phrasing in
the §1 design-vs-implementation note, the §3.4.1 registry guarantee,
and the §3.7 calibration vignette — the implementation has since
moved past that release, so the prose no longer pins a specific SDK
version. The v0.43.0 "since" / "measured at" anchors stay: they
record fixed historical milestones, not an as-of-now state, and the
earlier v0.2 → v0.61 mention in this appendix is itself history, left
verbatim. Integrated the narrative relation kinds into
§3.4.1, which had predated them: the registry table gains `PART_OF` /
`SEQUENCE_IN` rows (both asymmetric, ACTIVE) and the end-to-end
guarantee now names all three ACTIVE kinds instead of describing
`CO_EVIDENTIAL` as the only shipped one.

## v2.3 r4 (June 2026) — contestedness instrument shipped (P1-1 closure)

Replaced the thesis block's "(Surfacing this per claim — a
*contestedness* signal — is deferred work.)" parenthetical
with a pointer to the now-shipped mechanism: contestedness is the
max−min spread of effective confidence across the viewer's policy set
(local policy + each adopted lens, each evaluated standalone),
computed at read time and surfaced in query responses, prose
exporters, and lint — disclosure, never a discount (
techspec §6.9). This closes 2026-06 review P1-1 by delivering the
instrument the thesis promised rather than softening the claim: the
fact/opinion distinction is now recovered as a per-statement
measurement, the sibling of stance distribution. No design
content otherwise changed.

## v2.4 (July 2026) — §4 rewritten for the agent-memory arc (R1.14–R1.16)

Rewrote §4 "Primary Use Cases" end to end. The section predated the
R1.14–R1.16 agent-memory arc and still described the product as
"Linter for Engineers, Wiki for Everyone"; it now leads with the
launch wedge — **AI memory you can audit and trust** — organised as
two front doors over one substrate, with the shared-store bridge
("one epistemic store serves both the human operator's second brain
and the AI agent's memory") as the architecture narrative beneath the
wedge and the consent mechanisms (write-authority boundaries via
`asserted_by`, open §6.6 reconciliation, read-time lenses) stated
explicitly. §4.1 became the audit-and-harvest loop: the
`particles init claude-code` lifecycle hooks, the
drift-gated `MEMORY.md` projection, the first-run
`particles audit` census as the activation moment, the
nightly `particles memory consolidate` dream cycle with
the mutable local-source refresh and utility rank-lift
, the `--as-of` bitemporal read lens, and the
reference memory-server compatibility façade. §4.2 became
the cited-projections door, absorbing the former wiki-view section
plus the exporter family, the Obsidian lint-callout plugin
, and the retrospective vault import with its
rejected-parser rationale carried forward. §4.3 "An operator's week"
was updated to the shipped cadence: continuous zero-touch harvest,
nightly scheduled consolidation, weekly curate/review/export. The §2
"two paths through the inversion" callout and Risk #2's mitigation
column were synced to the new door names.
