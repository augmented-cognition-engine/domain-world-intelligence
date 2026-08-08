# World Intelligence P2B golden-scenario audit

**Date:** 2026-08-06  
**Result:** passed for the frozen hermetic scenario packet, coherence suite, negative boundary, and installed-artifact replay  
**Not claimed:** runtime Observation admission, live detection or routing, governed Brief synthesis execution, user Decision/Outcome capture, LIVE sources, delivery, external action, or political analysis

## Outcome

The golden 72-hour public-issue scenario is frozen as a synthetic, hermetic, redistributable
conformance packet. Every actor, institution, publisher, jurisdiction, record, and measurement is
fictional (`meridia_reservoir_release_72h`). The packet pins the expected entity/relation graph,
provenance families, claim-support transitions, supersessions, material shifts, routed and blocked
signals, and an exact seven-status Reality Brief. The compiled pack is byte-identical to P2A:
adding the packet changed no pack module and no platform contract.

## Exact packet

- Pack (unchanged): `world_intelligence` `0.1.0`, `pack_ir:683de57a71669814e507d07d65a109db`
- Packet identity: `sha256:9efb3e53f7a8b8b8b3fadb2ecede62cf7d6d7550b37ec74912c0efaa1ecadf73`
- Scenario window: `2026-03-10T06:00:00Z` → `2026-03-13T06:00:00Z` (exactly 72 hours)
- Source records: `8`, each preserving event-effective, publication, observation, ingestion, and
  (for syndication) derivation time
- Provenance families: `4`; the Ledger family holds the original report, two syndicated copies,
  and the publisher correction, and counts once in every corroboration judgment
- Entities: `19` across all nine types; relations: `16` instances exercising all eleven types
- Claim transitions: supply-restoration `attributed_claim → disputed`; farm-allocation
  `attributed_claim → corroborated` (independent families: hydrology datasets + ledger reporting)
- Official status change: Order 47 moves event and policy `announced/in_effect → suspended`
- Supersessions: `2`, both append-only with the superseded record still admitted
- Shifts: `1` numeric (`-12.2977 %` storage, threshold `5.0`, runtime-supported) plus `4`
  categorical (event status, record correction, two claim-support), blocked by `WI-CR-001`
- Signals: `1` runtime-routable (`public_indicator_move` via `route_public_indicator_move` to both
  personas) plus `3` blocked (`breaking_development`, `material_correction`, `claim_conflict`)
- Brief: `reality_change_brief`, 11 ordered sections, 17 statements, status counts
  observed `8`, attributed claim `2`, corroborated `1`, disputed `1`, inferred `2`, unknown `2`,
  scenario `1` — all seven epistemic statuses present, persona-invariant

Artifacts (SHA-256 pinned in `p2b_manifest.json`): `p2b_scenario.json`, `p2b_expected.json`,
`p2b_negative_cases.json`, `p2b_contract_requests.json`, `scripts/p2b_scenario_acceptance.py`.

## Negative boundary

Nine mutations fail closed with distinct first violations:

| Case | Violation |
|---|---|
| missing_attribution | `missing_claim_attribution` |
| false_independent_corroboration | `false_independent_corroboration` |
| history_rewrite | `historical_record_rewritten` |
| inference_as_observation | `inference_presented_as_observation` |
| scenario_as_prediction | `scenario_presented_as_prediction` |
| persona_dependent_evidence_status | `persona_dependent_evidence_status` |
| unsupported_claim | `unsupported_material_statement` |
| stale_closure | `stale_closure` |
| divergent_replay | `divergent_replay_identity` |

## Consumer contract requests

Current ACE cannot express four expected results. Each is recorded as an open, domain-neutral
request in `p2b_contract_requests.json` with a quarantined `strict` expected-failure test that
flips loudly when the platform capability lands. Nothing is implemented privately in this
repository and no runtime success is simulated.

| Request | Gap | Quarantined test |
|---|---|---|
| WI-CR-001 | Detection contract is numeric-only; categorical state-change rules inexpressible | `test_platform_gap_categorical_state_change_detection` |
| WI-CR-002 | Claim grounding is `cited`/`inference` only; no generic epistemic-status projection | `test_platform_gap_epistemic_status_projection` |
| WI-CR-003 | No derivation-family closure or source-independence predicate over lineage | `test_platform_gap_source_independence_closure` |
| WI-CR-004 | `supersedes` lineage exists but no affected-resource impact projection | `test_platform_gap_supersession_impact_projection` |

Each request carries a Market-compatibility requirement: the Market pack must compile unchanged
and its suite stay green before World depends on the capability. The semantic
`position_or_narrative_shift` detector is deliberately deferred, not requested.

## Verification

| Check | Result |
|---|---:|
| World suite (P2A + P2B) | 19 passed, 4 xfailed (quarantined gaps) |
| P2A conformance subset | 7 passed, unchanged |
| `ruff check` / acceptance script format | passed |
| Pack recompiled through unchanged ACE | `pack_ir:683de57a71669814e507d07d65a109db` |
| Negative vectors | 9/9 fail closed |
| Installed-artifact replay | identical packet identity from the wheel |

Artifact pins:

- World `ace_ext_world_intelligence-0.2.0-py3-none-any.whl`:
  `1a82e547e20f3c2c0f552639da236e9b29dbb69b30a234f3f3e1944ff024fa7d`
- The wheel contains the inert manifest, five unchanged JSON modules, four P2A and five P2B
  conformance artifacts, and package metadata — no tests and no executable adapter code.
- Isolated probe: fresh Python 3.14 venv with only the World wheel installed reproduced
  `sha256:9efb3e53f7a8b8b8b3fadb2ecede62cf7d6d7550b37ec74912c0efaa1ecadf73` with zero violations
  and all nine negative vectors failing closed.

Falsification finding: for namespace packages, `importlib.resources.files()` returns a
`MultiplexedPath`, so the P2A-era `Path(str(...))` resolution silently fell back to the checkout.
The P2B acceptance script resolves the installed pack through the Traversable API; the pinned P2A
script is left untouched and its audit stands as recorded.

## Next gate

P2B runtime integration, in order:

1. ACE lands WI-CR-001 (categorical detection) generically with Market compatibility proven; the
   four blocked shifts and three blocked signals then move from `contract_blocked` to routed
   runtime expectations and the quarantined test flips.
2. ACE lands WI-CR-002/003/004 or negotiates alternative generic shapes; the packet's epistemic
   statuses, independence enforcement, and correction impact become runtime-checked rather than
   fixture-checked.
3. The frozen packet is carried through admitted PREPARED Observations, entity state, detection,
   routing, and governed Brief synthesis via public contracts only, followed by user
   correction/no-action, usefulness Outcome, and governed PREPARED feedback.
4. P2C then binds one separately installed, least-authorized LIVE official-source adapter.

## Post-freeze platform integration update — 2026-08-07

ACE has now satisfied `WI-CR-001` with the domain-neutral
`ace.intelligence.detection/v1alpha2` contract. The World consumer probe compiles an additive
upgrade over the frozen pack containing exact categorical transitions for event suspension,
record correction, claim dispute, and claim corroboration. The probe changes no frozen P2B
artifact and does not move the default `0.1.0` pack identity.

Compatibility and consumer results:

- ACE focused categorical/LIVE dispatch suite: `22 passed`;
- complete ACE Intelligence suite: `277 passed`;
- unchanged Market domain conformance suite: `88 passed, 1 skipped`;
- World P2A + P2B suite: `20 passed, 3 xfailed`;
- `WI-CR-002`, `WI-CR-003`, and `WI-CR-004` remain explicit quarantined gaps.

The installed-artifact probe used newly built `ace-core==0.3.0` and
`ace-ext-world-intelligence==0.2.0` wheels in a fresh environment outside both source checkouts.
It reproduced the frozen base pack as `pack_ir:683de57a71669814e507d07d65a109db` and compiled the
additive categorical revision as `pack_ir:65cc0d2ac4ca0ab2646394a3500d3c27`, with exactly
`claim_support_change`, `event_status_change`, and `record_correction` declared.

This closes the compiler-contract portion of the first P2B runtime-integration gate. Materializing
the frozen scenario as activation-bound PREPARED snapshots and replaying its categorical Shifts,
Signals, and Brief through public runtime APIs remains the next World-owned task.
