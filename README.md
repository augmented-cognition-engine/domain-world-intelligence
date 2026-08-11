# ACE World Intelligence

**Governed public-issue sensemaking on the shared ACE foundation.**

ACE World Intelligence is an independently versioned ACE domain product. Its installable package
is an inert, JSON-only Domain Pack for making sense of a changing public issue. It separates
admitted records, attributed claims, corroboration, disputes, ACE inference, unknowns, and
conditional scenarios instead of presenting one opaque summary as truth.

It supplies World vocabulary, source mappings, material-change policy, personas, synthesis policy,
connectors, fixtures, and product evidence. It does not implement a second reasoning runtime,
graph, state store, authority system, detector engine, or feedback loop.

[Install](#install) · [Architecture](#what-you-install-and-what-you-get) ·
[Proof](#what-the-public-world-proof-demonstrates) · [Roadmap](ROADMAP.md) ·
[Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

- **Distribution:** `ace-domain-world-intelligence` 0.9.0
- **Requires:** Python 3.12 and `ace-core>=0.5.0,<0.6`
- **Artifact boundary:** JSON-only, data-only, inert
- **Release:** public. The
  [`v0.9.0` GitHub Release](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.9.0)
  and [`0.9.0 PyPI distribution`](https://pypi.org/project/ace-domain-world-intelligence/0.9.0/)
  are public. See the [`0.9.0 release packet`](docs/releases/world-intelligence-p2c2-v0.9.0.md).

## What you install, and what you get

The product is split into three layers, and this repository owns only the third.

| Layer | Distribution | What it is |
|---|---|---|
| **ACE Core** | `ace-core` (public on PyPI, 0.5.0) | The runtime: identity, graph, immutable records, temporal validation, lineage, admission, replay, and governed bounded action. |
| **ACE Intelligence** | shipped with ACE Core | The domain-neutral contracts: the pack compiler, activation binding, detection, Case, Brief synthesis, and epistemic-status validation that packs are checked against. |
| **World Intelligence Domain Pack** | `ace-domain-world-intelligence` (this repository) | JSON declarations only — ontology, source mapping, detection, personas, synthesis, epistemic-status vocabulary, and frozen conformance fixtures. |

Installing the Domain Pack adds **data**, not behaviour. The wheel contains no `.py`, no entry
points, and no install hooks; nothing in it executes on install or import. ACE Core compiles those
JSON modules and does the reasoning. If you want to sense a live official source, you additionally
install a separately reviewed connector — see [Connector boundary](#connector-boundary).

### Install

0.9.0 is published on PyPI. Install it on Python 3.12 with either command below; a public clean
install resolves `ace-domain-world-intelligence==0.9.0` and `ace-core==0.5.0`.

With `uv`:

```bash
uv add "ace-domain-world-intelligence==0.9.0"
```

With `pip`:

```bash
pip install "ace-domain-world-intelligence==0.9.0"
```

Either command also brings in `ace-core>=0.5.0,<0.6`, which is already public. It does **not** bring
in the Federal Register connector; that is a deliberate boundary, not an omission.

Resolve the pack data from the installed distribution:

```python
import json
from importlib.resources import files

manifest = json.loads(files("domain_packs.world_intelligence").joinpath("manifest.json").read_text(encoding="utf-8"))
print(manifest["metadata"]["pack_id"])  # world_intelligence
```

### Develop from a source checkout

To develop the pack, or to run the acceptance harnesses and the P2C connector packet, work from a
checkout alongside an ACE Core checkout or installation:

```bash
# from the root of this checkout
export REPO="$PWD"
export ACE=/path/to/ace-core
export PYTHONPATH="$REPO:$REPO/adapters/federal_register_source/src:$ACE"
export PY="$ACE/.venv/bin/python"
```

`PYTHONPATH` above includes the connector source so that the P2C packet runs. Drop that middle entry
and the P2C modules skip rather than fail.

## Product loop

```text
authorized evidence → Observation → Entity Snapshot
                           ├────────→ Signal ──┐
                           └────────→ Shift ───┼→ Case / Brief → Decision → Outcome
                                               └→ governed feedback proposal
```

This is a typed DAG, not a forced pipeline. A Shift need not become a Signal, a Signal need not
become a Brief, and no downstream resource grants itself authority.

## Domain scope

World Intelligence is intended to cover public events, actors, institutions, issues, policies,
claims, commitments, actions, reactions, corrections, and source relationships. Its user-facing
products can include Reality Briefs, event summaries, standing investigations, material-change
alerts, and personal briefings. These are World-domain types and policies; shared graph,
detection, routing, synthesis, authority, and feedback machinery remains in ACE.

## Current milestone

P2A proved that a materially different, JSON-only World Intelligence pack compiles through the
unchanged ACE pack compiler (`pack_ir:683de57a71669814e507d07d65a109db`, seven conformance tests).

P2B freezes the golden 72-hour public-issue scenario: the synthetic, hermetic, redistributable
`meridia_reservoir_release_72h` packet. It pins eight timestamped source records across four
provenance families (including two syndicated copies and a publisher correction), a
nineteen-entity graph exercising all eleven relation types, an official status change, four
material categorical shifts plus one numeric shift, one runtime-routable signal, and an exact
Reality Brief whose seventeen statements carry all seven epistemic statuses. Nine negative
vectors fail closed, from missing attribution through divergent replay.

The additive P2B PREPARED replay now compiles and activation-binds detection `v1alpha2`, admits all
eight source records as PREPARED Observations, reproduces all five Shifts, emits only the intended
four Signals, and resolves all four persona routes. The claim-corroboration Shift is represented
through ACE's generic resource-set admission without inventing a Signal. The frozen scenario and
default `0.1.0` pack identities remain unchanged.

The replay also freezes those developments into ACE's public immutable Case contract. Four routed
Signals plus the non-routed corroboration Shift form one five-member Case that transitively binds
the complete 28-resource scenario closure. World supplies the case type and purpose; ACE owns the
identity, temporal validation, lineage resolution, admission, and replay.

An additive Case-bound packet now consumes ACE's public `CaseBriefSynthesisService` over that exact
Case. It admits the routed derivations through ACE's durable PREPARED ledger without duplicating any
source record, derives one compatible template and persona scope from the four exact attention
receipts, freezes all 26 closure resources as Core context, and emits one governed, grounded,
atomically persisted, deterministically replayable Reality Brief that carries the Case in lineage:
`brief:8fb3173069eca502652b1c9c004c92e6`. `WI-CR-005` is closed.

Per-statement epistemic status (`WI-CR-002`) and derivation-family independence (`WI-CR-003`) are
now closed through public, domain-neutral ACE contracts. World declares its seven-label vocabulary;
ACE validates each statement against its exact supports and proves that `corroborated` spans at least
two admitted derivation families. The Ledger report and the independent Basin gauge satisfy that
rule, while Coastal Wire and Harborview collapse into the Ledger root despite being different
publishers. The durable projection discloses the exact root-to-member partition used by the proof.
Supersession-impact enumeration (`WI-CR-004`) is now closed too, so **no public-platform contract
request remains open**. When a record is superseded, ACE enumerates exactly what depended on it,
directly and transitively, and appends that answer as an additive immutable record. Both frozen
corrections are exercised: the Ledger correction reaches 11 resources and 9 Brief claims, the Order
supersession reaches 7 resources and 5 claims, and each projection discloses the resources it found
**unaffected** so the boundary is visible rather than inferred. Impact means dependency, not
falsehood — the prior Brief keeps its exact identity, replays byte-identically, and is never
rewritten.

P2C adds the first official-source sensing proof without mutating that frozen pack. A separate,
JSON-only activation pack (`pack_ir:1847032fc5301bba9b6f85d3d091400d`) maps one exact Federal
Register document, while a separately versioned, transport-injected adapter validates the exact
source, artifact, URI, network attestations, and closed payload. ACE then admits one acquisition
receipt, source snapshot, visibly LIVE Observation, LIVE Entity Snapshot, and admission receipt as
one atomic transaction. Exact replay and fresh-service restart replay perform no second capture.

The conformance transport is a recorded, network-free response from the reviewed official API URI;
it proves the governed LIVE contract and deterministic admission, not that the test suite performed
a live network request. FederalRegister.gov is explicitly labeled as not the official legal edition,
and the corresponding `govinfo.gov` PDF is retained as the official-format verification reference.
No Signal, Shift, Brief, Decision, Outcome, feedback, delivery, publishing, persuasion, or external
action is created.

P2C2 completes that sensing path across the Core + Intelligence + Domain boundaries. A new
declarative monitor pack admits two exact FCC records — document `2026-15932` published August 6
and document `2026-16197` published August 7 — as successive LIVE snapshots of one stable monitor
entity. Its configured categorical detector produces an `official_publication_change` Shift, routes
an `official_publication` Signal, and invokes Core-governed reasoning to produce one LIVE Reality
Brief with six claims and two exact citations. A named human Decision then authorizes only a
create-only workspace export; a second exact human review precedes the effect, and separate
verification and promotion receipts follow it. Replay performs neither a second reasoning call nor
a second file effect.

This is a governed export proof, not autonomous publishing. The pack contains no executable code or
action authority; the export is provided by Core's separately packaged reference adapter. The two
source responses are exact official public records under recorded transport, so P2C2 proves the
complete deterministic product journey but still does not claim network freshness at test time.

P2C3 is a source-checkout candidate over that unchanged public journey. It compares two exact
reviewed exports of the cited Brief with two reviewed exports of a World-owned source-only control.
The frozen product measure is the fraction of the two required admitted Observation identities
preserved in each exported artifact: treatment scores `1.0, 1.0`; control scores `0.0, 0.0`. Under
the declared minimum of two matched pairs and useful-effect threshold of `0.5`, Core + Intelligence
classifies the exact result as `useful` and appends a `promote` proposal that is non-effective,
non-selectable, and requires separate human review. Historical replay performs no reauthorization.

That measure is structural citation coverage. It is not a human-benefit measure, causal estimate,
general Brief-quality score, or network-freshness proof. The proposal is not applied. P2C3 depends
on the unreleased Core candidate in [PR #88](https://github.com/augmented-cognition-engine/core/pull/88),
so World 0.9.0 and its `ace-core>=0.5.0,<0.6` release contract remain unchanged.

P2C4 submits that exact proposal to a separate governed review path. A named, authenticated World
reviewer records `reject` with `no_action`: the bounded `useful` classification and `promote`
proposal remain immutable, and no governed head changes. The rationale rejects broader promotion
because structural coverage does not establish citation correctness, general Brief quality, human
benefit, causality, or live freshness. Exact replay returns the historical Decision without new
authorization. This is explicit disposition, not reclassification or proposal application.

P2C5 adds a distinct product-owned outcome rather than broadening the structural score. The named
principal `principal:world-citation-correctness-reviewer` records an exact immutable review over
the Brief, its one cited claim, the exact two citation identities, and the two admitted official
Observation references. Each Core Outcome names that exact result. A matched negative control
retains both citation identities but swaps the two publication dates in the claim: treatment and
control both have `1.0` coverage, while correctness is `1.0` and `0.0` respectively across two
pairs. The domain-neutral evaluator classifies that bounded difference as useful and still emits
only a non-effective proposal requiring separate review.

This candidate establishes exact review provenance and sensitivity to one semantic corruption. It
does not establish reviewer infallibility, current network freshness, source independence, general
Brief quality, causal impact, or human benefit. Citation review vocabulary and policy remain in
World; Core and Intelligence receive only the exact immutable observed-result coordinate.

P2C6 adds an exact contradiction-attention outcome over the same recorded official sources. One
candidate states the admitted document/date facts exactly and one swaps the dates. Treatment
alerts only on the contradiction; an inverted-routing control alerts only on the valid comparator.
Both emit exactly one alert, so raw alert volume cannot explain the `1.0` treatment/control quality
difference. The independently recorded review exposes contradiction recall, false-alert rate, one
valid silence, confusion counts, exact Brief/Observation provenance, policy identity, and limits.

This source-checkout candidate demonstrates one frozen challenge, not a live observed public
conflict or a population false-alert rate. It does not establish autonomous discovery, network
freshness, correction quality, general Brief quality, causality, or human benefit. The resulting
proposal remains non-effective and unapplied.

P2C7 uses an actual explicit FCC correction pair under recorded replay. Document `2021-10670`
names and corrects `2020-28779`; treatment and delayed control preserve that same exact linkage,
corrected instruction, original immutable Observation, and reviewed workflow. Against a frozen
600-second World target, treatment delay is 300 seconds and control delay is 21600 seconds. Exact
independent reviews become Core Outcomes, and the bounded two-pair difference is useful while the
proposal remains non-effective and unapplied.

The recorded availability and detection instants are test coordinates. The suite performs no
network access and does not establish live monitoring, network-arrival latency, population delay
performance, legal truth, calibration, general Brief quality, causality, or human benefit.

P2C8 creates actual prior, treatment, and control `BriefV1Alpha1` records over that same source
pair. Both revisions remove the stale instruction claim, add the same exact correction claim,
retain three claims, and cite the same original/correction sources. Treatment preserves the exact
identities of both unaffected claims; the paraphrase-drift control preserves neither. Independent
reviews record every expected, preserved, drifted, and unexpected claim identity, producing scores
of `1.0` and `0.0` across two matched pairs and another non-effective proposal.

This freezes a World product rule over one recorded pair. It is not live revision, a general
semantic-equivalence engine, population stability, calibration, causality, or human benefit.

P2C9 freezes one exact probabilistic scoring boundary over that recorded correction. After the
original Observation is admitted but before the correction is available, treatment and control
record probabilities of `0.75` and `0.25` for the same explicit-correction event and complete the
same reviewed workflow. Only then is the exact correction Observation admitted. Independent
reviews derive the binary result and single-event Brier quality contributions of `0.9375` and
`0.4375`; the two-pair difference is useful and still emits only a non-effective proposal.

The forecast artifacts contain no correction identity or result material, and every reviewed
forecast Action completes before the result becomes available. The probabilities are declared
fixture inputs, not ACE outputs. This is exact forecast/result scoring, not a historically
contemporaneous forecast, model-skill finding, empirical calibration curve, population reliability
estimate, causal claim, or human-benefit finding.

P2C10 independently reproduces correction-quality measurement over the U.S. Bureau of Labor
Statistics public errata family. The recorded July 1, 2025 JOLTS release `USDL-25-1087` and BLS's
July 2 correction are admitted as distinct immutable Observations. Treatment and control preserve
both source identities, the exact correction link, two reviewed Actions each, and the same matched
conditions; treatment renders the required minus sign in `−39,000`, while control retains the
reported pre-correction form. Exact reviews score `1.0` and `0.0`, so the unchanged domain-neutral
contract classifies the bounded two-pair difference as useful and emits only a non-effective
proposal.

The historical wrong form is derived from BLS's explicit statement that the sentence required a
missing minus sign; the currently archived release is already corrected. This is recorded replay
over one correction, not live monitoring, statistical validation of JOLTS, population correction
performance, causality, or human benefit. No Domain Pack, connector, or Core contract changes.

## What the public World proof demonstrates

Generate a self-contained visual Reality Brief and its exact machine-readable backing data:

```bash
PYTHONPATH=/path/to/domain-world-intelligence:/path/to/ace-core \
  /path/to/ace-core/.venv/bin/python scripts/public_demo.py
```

The command writes `artifacts/public-demo/index.html` and `demo-data.json`. It runs the accepted
independence and correction-impact harnesses, refuses to render if the pinned release proof drifts,
and uses no external web assets.

It demonstrates four things, and only these:

1. **Two publishers are not two sources.** Coastal Wire and Harborview are different publishers, but
   both derive from the Ledger report and collapse into one derivation family. Only the Ledger +
   Basin pairing satisfies the Brief's two-family corroboration rule.
2. **Every statement carries its own epistemic status.** The seven-label World vocabulary is
   validated by ACE against each statement's exact supports, not asserted by the pack.
3. **Corrections append rather than rewrite.** Admitting the later Ledger correction produces a
   governed impact projection over 11 downstream resources and 9 Brief claims, and discloses the 16
   resources it found unaffected. Impact means dependency, not falsehood.
4. **The result is reproducible.** The prior Brief keeps its exact identity and replays
   byte-identically, and the two artifacts are byte-identical across runs.

Exact public identities reproduced by the demo:

- Case: `case:412426eee708d56f6bda931ccf9e5d8b`
- Brief: `brief:25d8232c9bfa27050bdcb160fb75f06c`

The page is explicitly a synthetic PREPARED / FROZEN scenario, **not a live news product**. It does
not monitor the news, and it takes no action of its own. See
[`docs/releases/world-intelligence-public-demo-v0.7.0.md`](docs/releases/world-intelligence-public-demo-v0.7.0.md)
for the 0.7.0 release boundary and full identity list.

## Connector boundary

This repository ships an **inert Domain Pack**. The Federal Register connector is a separately
versioned executable artifact, `ace-ext-world-federal-register-source` 0.2.0, with its own review
boundary:

- it is **not** a dependency of the Domain Pack, and no extra reintroduces it;
- installing `ace-domain-world-intelligence` never installs it;
- it is **not** published by this repository's release workflow, which builds and uploads the root
  sdist and wheel only;
- it contains no network client — it accepts only an injected, separately reviewed transport, and
  validates the exact artifact identity, source type, HTTPS URI, empty redirect chain, absence of
  credentials, exact HTTP 200 `application/json`, bounded strict JSON, globally routable address
  attestations, DNS-rebinding protection, and monotonic operation times;
- to exercise it, put it on the path explicitly. Omit it and the P2C modules skip rather than fail.

Rebuild the connector reproducibly:

```bash
cd adapters/federal_register_source
SOURCE_DATE_EPOCH=1735689600 uv build --wheel
```

A production host must supply and review a real transport that enforces address validation and
rebinding protection throughout use. The shipped conformance material does not do that for you.

## Verification

With `$REPO`, `$ACE`, `$PYTHONPATH`, and `$PY` exported as in
[Develop from a source checkout](#develop-from-a-source-checkout):

```bash
# Complete domain suite, including every frozen packet and the P2C2 product journey: 83 passed
export PYTHONPATH="$PYTHONPATH:$ACE/adapters/reference_workspace_action/src"
$PY -m pytest -q

# Connector fail-closed unit suite: 26 passed
$PY -m pytest adapters/federal_register_source/tests -q

# Individual acceptance harnesses
$PY scripts/p2a_compile_acceptance.py
$PY scripts/p2b_scenario_acceptance.py --negative
$PY scripts/p2b_prepared_replay.py
$PY scripts/p2b_case_brief.py
$PY scripts/p2b_status_case_brief.py
$PY scripts/p2b_independent_case_brief.py
$PY scripts/p2c_federal_register_live_acceptance.py

# Complete official-record -> Shift -> Signal -> Brief -> reviewed export journey
WORKSPACE=$(mktemp -d)
$PY -m scripts.p2c2_governed_reality_brief "$WORKSPACE"

# Candidate measured Outcome -> governed-feedback extension (requires Core PR #88 source)
$PY -m scripts.p2c3_measured_feedback "$WORKSPACE"

# Stacked candidate: explicit reject/no-action review of the exact proposal
$PY -m scripts.p2c4_reviewed_impact_disposition "$WORKSPACE"

# Stacked candidates: correctness, attention, correction delay, revision stability, and forecast scoring
$PY -m scripts.p2c5_citation_correctness_outcome "$WORKSPACE"
$PY -m scripts.p2c6_contradiction_attention_outcome "$WORKSPACE"
$PY -m scripts.p2c7_correction_detection_delay_outcome "$WORKSPACE"
$PY -m scripts.p2c8_correction_revision_stability_outcome "$WORKSPACE"
$PY -m scripts.p2c9_forecast_calibration_outcome "$WORKSPACE"
$PY -m scripts.p2c10_independent_correction_reproduction "$WORKSPACE"
```

The released 0.9.0 gates are reproducible through the locked environment, as CI does. The
P2C2 action test runs when the independently packaged Core reference adapter is installed:

```bash
uv sync --frozen --no-install-project
uv run --no-sync python -m pytest                         # released + candidate-compatible gates
uv run --no-sync python -m pytest tests/test_release_contract.py  # publishable-identity gate
uv run --no-sync python -m pytest adapters/federal_register_source/tests  # connector: 26 passed
```

Verified totals as of 2026-08-10 with public `ace-core==0.5.0` from PyPI and the independently
packaged reference adapter from the Core `v0.5.0` GitHub release: domain suite `83 passed`,
connector suite `26 passed`. The
public demo reproduces `case:412426eee708d56f6bda931ccf9e5d8b` and
`brief:25d8232c9bfa27050bdcb160fb75f06c`, and its two artifacts are byte-identical across runs.

The exact identities, negative cases, and artifact proofs are recorded in
[`docs/audits/world-intelligence-p2a-2026-08-06.md`](docs/audits/world-intelligence-p2a-2026-08-06.md)
and
[`docs/audits/world-intelligence-p2b-2026-08-06.md`](docs/audits/world-intelligence-p2b-2026-08-06.md),
with the interpreter and Case proof in
[`docs/audits/world-intelligence-p2b-prepared-replay-2026-08-07.md`](docs/audits/world-intelligence-p2b-prepared-replay-2026-08-07.md)
and the governed Case-bound Brief proof in
[`docs/audits/world-intelligence-p2b-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-case-brief-2026-08-07.md),
the per-statement status proof in
[`docs/audits/world-intelligence-p2b-status-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-status-case-brief-2026-08-07.md),
and the independent-corroboration proof in
[`docs/audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md).
The governed official-source admission proof is recorded in
[`docs/audits/world-intelligence-p2c-federal-register-live-2026-08-07.md`](docs/audits/world-intelligence-p2c-federal-register-live-2026-08-07.md).
The complete governed product-journey evidence is recorded in
[`docs/audits/world-intelligence-p2c2-governed-reality-brief-2026-08-10.md`](docs/audits/world-intelligence-p2c2-governed-reality-brief-2026-08-10.md).
The source-checkout measured-feedback candidate is recorded in
[`docs/audits/world-intelligence-p2c3-measured-feedback-2026-08-10.md`](docs/audits/world-intelligence-p2c3-measured-feedback-2026-08-10.md).
The latest independent-source correction candidate is recorded in
[`docs/audits/world-intelligence-p2c10-independent-correction-reproduction-2026-08-10.md`](docs/audits/world-intelligence-p2c10-independent-correction-reproduction-2026-08-10.md).
The bounded installed-Core artifact convergence packet is frozen in
[`docs/design/world-measured-intelligence-release-convergence-work-packet-v1.md`](docs/design/world-measured-intelligence-release-convergence-work-packet-v1.md).
It generates one canonical machine-readable P2C10 result without importing Core from a checkout;
it is candidate evidence, not a release or SI4 pass.
The point-in-time [convergence audit](docs/audits/world-measured-intelligence-release-convergence-2026-08-11.md)
binds the exact built-artifact hashes and byte-reproducible
[`convergence-v1.json`](artifacts/measured-intelligence/convergence-v1.json).

Release-level scope and evidence are recorded in
[`docs/releases/world-intelligence-p2c2-v0.9.0.md`](docs/releases/world-intelligence-p2c2-v0.9.0.md),
and version history in [`CHANGELOG.md`](CHANGELOG.md).

## Guardrails

- A publisher is not assigned a hidden universal truth score.
- Repetition and syndication are not independent corroboration.
- Claims retain attribution.
- Corrections append state rather than rewriting history.
- Inference and scenario material remain explicitly labeled.
- Persona routing never changes an evidence status.
- No political persuasion, voter targeting, or autonomous publishing.
- External effects require an exact Core-governed Decision, human review, post-effect
  verification, and promotion; the reference proof is limited to one create-only workspace file.

World Intelligence does not watch live news feeds, decide anything on its own, or publish or deliver
content autonomously. Every LIVE capture demonstrated here is one explicitly requested, governed,
read-only retrieval. P2C2's only effect is an explicitly authorized and reviewed create-only local
workspace export followed by separate verification and promotion.

## Roadmap and project status

The [World Intelligence roadmap](ROADMAP.md) owns current domain direction. Detailed packet history
remains in [`docs/world-intelligence-roadmap-status-2026-08-06.md`](docs/world-intelligence-roadmap-status-2026-08-06.md),
and release history is in [`CHANGELOG.md`](CHANGELOG.md). P2C4 demonstrates a separately
authorized reject/no-action disposition of the P2C3 proposal without effective state change. P2C5
adds an independently reviewed citation-correctness Outcome and a citation-preserving semantic
negative control. P2C6 adds exact contradiction recall, false-alert rate, equal alert-volume
control, and valid silence under one frozen recorded-source challenge. P2C7 adds exact handling of
one explicit recorded correction pair, preserves the prior record, and measures frozen-replay
detection delay against a product target. P2C8 measures exact unaffected-claim identity
preservation across real Brief contracts while holding correction semantics, source coverage, and
claim count constant. P2C9 adds an exact withheld-result forecast record and derives a single-event
Brier contribution while explicitly withholding any population-calibration or model-skill claim.
P2C10 reproduces correction-quality measurement over an independently sourced BLS erratum without
changing the shared contracts. The next bounded measurement work is independent Market
reproduction.
Separately reviewed opt-in network transport and P2D multi-source conflict/correction with LIVE
inputs remain independent work. None of these steps may add autonomous publishing, delivery,
persuasion, or action authority to a Domain Pack.

## Community and security

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Issues](https://github.com/augmented-cognition-engine/domain-world-intelligence/issues)

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Existing work is copyright Edwin
Amirian; contributors retain copyright in their contributions and license them under Apache-2.0.
