# Changelog

All notable changes to `ace-domain-world-intelligence` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries describe the Domain Pack distribution. The Federal Register connector,
`ace-ext-world-federal-register-source`, is a separate distribution on its own version line and is
noted here only where the boundary between them changes.

## Unreleased

### Added

- **P2E user-owned LIVE-orientation consumer packet.** Public ACE 0.5.0 Monitor,
  PersonaBinding, and record-only Subscription contracts now bind the accepted planetary-defense
  pack, exact activation, one fixture principal, and the pack persona with pinned identities.
- **Repeated-window ownership and suppression runtime.** Six explicit owner-requested windows append
  and exactly replay initial orientation, exact no-change suppression, two always-visible
  corrections, zero acquisition while paused, resume, and zero acquisition after Subscription
  revocation. Eleven negative mutations fail closed.
- **Closed narrow platform requests.** Merged Core #94 closes `WI-CR-007` with owner-authorized
  append-only lifecycle and closes `WI-CR-008` with bounded sensing-window route-or-suppression
  receipts. World consumes the generic public seams and adds no private implementation.
- **Composed captured LIVE lineage.** The four NASA/ESA Observations remain linked through three
  Shifts, three Signals, two Cases, and the original 2-citation and 4-citation Reality Briefs.

- **P2D LIVE conflict and correction.** Four exact NASA/ESA planetary-defense publications become
  LIVE Observations, one dated cross-source divergence and two same-source downward-revision Shifts,
  three routed Signals, immutable historical and corrected Cases, and cited Reality Briefs with
  family-aware per-claim epistemic status.
- **Additive LIVE supersession impact.** Two explicit same-source supersession assertions append
  exact dependency projections over the historical closure. Each reaches five resources and seven
  Brief claims, discloses two unaffected resources, and leaves the historical Brief byte-identical.
- **Exact official-source connector profiles.** The separately packaged connector now validates the
  four reviewed NASA/ESA canonical pages under recorded, network-free transport. Eighteen focused
  adapter cases cover accepted material and fail-closed boundary violations.

### Boundaries

- P2E appends five lifecycle transitions and six sensing receipts without a network request,
  scheduler, autonomous loop, delivery, publication, or external action. Its P2D prerequisite
  remains 44 LIVE records; the composed ledger is 62 LIVE records and zero PREPARED records.
- The new six-module pack is inert JSON only. The P2D proof contains 44 LIVE records and zero
  PREPARED records, performs no network request, and creates no action, delivery, publication,
  persuasion, monitor, or schedule.
- NASA and ESA are independent claimant publication roots, not proven independent measurements.
  Same-lineage supersessions collapse to their predecessor and do not manufacture corroboration.

### Repository consistency

- Added the full Apache-2.0 license, NOTICE, security policy, contribution guide, Code of Conduct,
  and a root domain roadmap.
- Aligned the README and package project links with the Market Intelligence sibling while
  preserving World-specific proof, connector, and guardrail language.
- Added conformance assertions for the public repository identity and community baseline.

## [0.9.0] — 2026-08-10

Public release. The
[`v0.9.0` GitHub Release](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.9.0)
and [`ace-domain-world-intelligence` 0.9.0](https://pypi.org/project/ace-domain-world-intelligence/0.9.0/)
are public; the wheel was published at 2026-08-10T18:46:16Z.

### Added

- **P2C2 official-record Reality Brief journey.** Two exact Federal Register records become LIVE
  Observations and stable entity snapshots, one configured Shift and routed Signal, and a governed
  six-claim/two-citation Reality Brief.
- **Reasoning into reviewed action.** A named human Decision authorizes an effect-free plan; a
  second exact review gates a create-only workspace export; verification and promotion remain
  separate; replay performs no second reasoning call or file effect.
- **Public-artifact reproduction.** A fresh Python 3.12 environment installed `ace-core==0.5.0`
  from PyPI and `ace-reference-workspace-action==0.1.0` from the Core `v0.5.0` GitHub release,
  then passed the complete World suite (`83 passed`), connector suite (`26 passed`), and focused
  P2C2 proof (`2 passed`) without a Core checkout.

### Changed

- Raised the root Domain Pack compatibility window to `ace-core>=0.5.0,<0.6` and bumped the inert
  root distribution to 0.9.0.
- Bumped the separately packaged Federal Register source adapter to 0.2.0 with the same Core 0.5
  compatibility window. It remains outside the root wheel and runtime dependency closure. Its
  unchanged `0.1.0` implementation identity preserves the accepted source receipts; 0.2.0 is the
  distribution version for the new dependency boundary.

### Not included

No continuous network monitoring, autonomous publishing, political persuasion, voter targeting,
or legal/policy-impact inference is claimed. The accepted source transport is exact, recorded, and
network-free; the only effect is a reviewed create-only local export.

## [0.8.0] — 2026-08-09

Public release. The `v0.8.0` tag exists, the
[GitHub Release](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.8.0)
is published, and
[`ace-domain-world-intelligence` 0.8.0](https://pypi.org/project/ace-domain-world-intelligence/0.8.0/)
was published to PyPI at 2026-08-09T18:33:44Z. Scope and evidence are recorded in
[`docs/releases/world-intelligence-p2c-v0.8.0.md`](docs/releases/world-intelligence-p2c-v0.8.0.md).

### Added

- **P2C governed official-source sensing.** A second, JSON-only activation pack,
  `domain_packs/world_intelligence_federal_register/` (ontology plus source mapping), maps one exact
  Federal Register document and compiles to `pack_ir:1847032fc5301bba9b6f85d3d091400d`. One capture
  admits an acquisition receipt, a canonical source snapshot, a visibly LIVE Observation, an
  exact-lineage LIVE Entity Snapshot, and a LIVE admission receipt as a single atomic transaction.
  Exact replay and fresh-service restart replay reopen the same records without invoking the adapter
  or transport a second time.
- **Separately packaged connector.** `adapters/federal_register_source/` builds as its own
  distribution, `ace-ext-world-federal-register-source` 0.1.0. It holds all executable code, contains
  no network client, accepts only an injected reviewed transport, and builds reproducibly under
  `SOURCE_DATE_EPOCH=1735689600`.
- **Release-contract suite** (`tests/test_release_contract.py`) pinning the published identity: exact
  name and version, `>=3.12,<3.13`, a single `ace-core>=0.4.1,<0.5` runtime requirement, data-only
  and inert packaging, and the guarantee that no runtime dependency or extra pulls in the connector.
- **CI and publish workflows.** CI builds the root sdist and wheel, checks metadata with
  `twine --strict`, inspects the exact wheel contents, and proves an isolated install against public
  `ace-core` 0.4.1 with the connector absent. The publish workflow verifies the tag against the root
  project version and uploads the root distribution only, via PyPI trusted publishing.

### Changed

- Renamed the root distribution from `ace-ext-world-intelligence` to
  `ace-domain-world-intelligence` under the `ace-domain-*` / `ace-ext-*` convention, and bumped it to
  0.8.0.
- Renamed the connector distribution from `ace-world-federal-register-source` to
  `ace-ext-world-federal-register-source`, and made its build reproducible. Because the exact artifact
  identity is bound into the governed capture, the P2C acquisition receipt, source snapshot, LIVE
  Observation, LIVE Entity Snapshot, admission receipt, and activation revision re-keyed. The
  acceptance failed closed until the pin was regenerated. The captured canonical payload digest, the
  `domain_activation` ID, and the transaction ID are unchanged.
- Raised the required ACE compatibility window to `ace-core>=0.4.1,<0.5`.

### Unchanged

- The P2A/P2B files under `domain_packs/world_intelligence/` remain byte-identical, so the frozen
  PREPARED identities — including `case:412426eee708d56f6bda931ccf9e5d8b` and
  `brief:25d8232c9bfa27050bdcb160fb75f06c` — are not re-keyed by this release.

### Verification

- Complete World suite: **81 passed**.
- Connector fail-closed unit suite: **24 passed**.
- Public publication verified: a clean install from PyPI on Python 3.12 resolved
  `ace-domain-world-intelligence==0.8.0` and `ace-core==0.4.1`; the installed wheel contains
  exactly 32 JSON Domain Pack resources and no `.py`, `.pyc`, or `.so` resource, and the connector
  import package is absent.

### Not included

No Signal, Shift, Brief, Decision, Outcome, feedback, learning event, monitor, schedule, delivery,
publishing, persuasion, or other external action is derived from the LIVE capture. There is no
network transport in this release, and no continuous or autonomous monitoring of any source.

## [0.7.0-rc1] — developer preview

Developer-preview release candidate, released under the former distribution name
`ace-ext-world-intelligence`, covering the public proof surface, recorded in
[`docs/releases/world-intelligence-public-demo-v0.7.0.md`](docs/releases/world-intelligence-public-demo-v0.7.0.md).

### Added

- **Public demo command** (`scripts/public_demo.py`) rendering a self-contained visual Reality Brief
  and its exact machine-readable backing data to `artifacts/public-demo/`, with no external web
  assets. It runs the accepted derivation-family and supersession-impact harnesses and refuses to
  render if release-critical identities or counts drift. Both artifacts are byte-identical across
  runs.
- **Per-statement epistemic status** (`WI-CR-002`) and **derivation-family independence**
  (`WI-CR-003`), closed through public, domain-neutral ACE contracts. World declares the seven-label
  vocabulary; ACE validates each statement against its exact supports and proves that `corroborated`
  spans at least two admitted derivation families. Projection:
  `brief_derivation_family_status_projection:3500889a2d75af7a5484a681afbee34c`.
- **Supersession-impact enumeration** (`WI-CR-004`). Admitting a correction appends an immutable
  impact projection —
  `supersession_impact_projection:f3723de8e9ac5c4390c5c46137f3765e` — that enumerates direct and
  transitive dependants and discloses the resources it found unaffected. The prior Brief keeps its
  exact identity and replays byte-identically.
- **Governed Case-bound Brief synthesis** (`WI-CR-005`) over ACE's public
  `CaseBriefSynthesisService`, emitting `brief:8fb3173069eca502652b1c9c004c92e6`.

### Notes

With `WI-CR-002` through `WI-CR-005` closed, no public-platform contract request remained open at
0.7.0.

## Earlier work

P2A (`pack_ir:683de57a71669814e507d07d65a109db`, seven conformance tests) and the frozen P2B
`meridia_reservoir_release_72h` scenario predate this changelog. Their exact identities, negative
cases, and artifact proofs are recorded in the dated audits under
[`docs/audits/`](docs/audits/); the earliest are
[`world-intelligence-p2a-2026-08-06.md`](docs/audits/world-intelligence-p2a-2026-08-06.md) and
[`world-intelligence-p2b-2026-08-06.md`](docs/audits/world-intelligence-p2b-2026-08-06.md).
