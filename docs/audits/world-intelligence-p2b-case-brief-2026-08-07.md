# World Intelligence P2B Case-bound governed Reality Brief audit

**Date:** 2026-08-07
**Result:** `WI-CR-005` closed — one governed Brief is synthesized from the exact frozen Case
**Not claimed:** seven-status epistemic projection, source-family independence, supersession impact, Decision, Outcome, feedback, LIVE sources, delivery, or external action

## Outcome

ACE now exposes an additive, domain-neutral Case-bound Brief synthesis path. This packet consumes
it end to end. The frozen `meridia_reservoir_release_72h` developments are admitted through ACE's
public durable PREPARED ledger, the pinned five-member orientation Case is frozen, and ACE's public
`CaseBriefSynthesisService` produces exactly one governed, grounded, atomically persisted, and
deterministically replayable Reality Brief bound to that Case.

No World semantics were added to ACE and no private aggregation was added to World. The template,
personas, closure, grounding, authorization, atomic append, and replay verification are all ACE's.
World supplies only the pack declarations, the scenario material, and a deterministic
structured-reasoning fixture standing in for a provider.

## Exact identities

| Material | Identity |
|---|---|
| Orientation Case | `case:2ee200c03f2576307b0bc43e6e128f30` |
| Case digest | `sha256:2ee200c03f2576307b0bc43e6e128f309e9de7efd3c11b1cad2ad1c250b4591f` |
| Governed Brief | `brief:8fb3173069eca502652b1c9c004c92e6` |
| Brief digest | `sha256:8fb3173069eca502652b1c9c004c92e6f5ef16b6ffecfcd7fc2e97daed594d81` |
| Case synthesis receipt | `case_brief_synthesis_receipt:3e122634e7f7a76390e6574dfc4f3e8d` |
| Receipt digest | `sha256:3e122634e7f7a76390e6574dfc4f3e8d07d2259d5f2e9d1b2ec9ac804be8875b` |
| Replay pack | `world_intelligence` `0.2.0`, `pack_ir:758974adc317ee67b2b244fb2dc4088a` |

The Case identity is byte-identical to the one pinned by the prepared-replay packet. Freezing the
orientation boundary and consuming it did not move it.

## Exact closure

| Material | Result |
|---|---:|
| Direct Case members | 5 |
| Routed Signal members with exact attention receipts | 4 |
| Non-routed Shift member preserved without attention | 1 |
| Brief lineage resources (transitive closure + the Case) | 26 |
| — Case | 1 |
| — Signals | 4 |
| — Shifts | 5 |
| — Entity Snapshots | 10 |
| — Observations | 6 |
| Selected frozen Core context items | 26 |
| Derived Brief template | `reality_change_brief` |
| Derived persona scope | `general_reader`, `public_researcher` |
| Brief sections | 11 |
| Grounded claims | 11 |
| Citations | 6 |
| Atomic records in the commit | 2 |
| Governed state preconditions on the commit | 4 |
| Provider invocations across synthesis + replay | 1 |
| Durable Briefs after replay | 1 |

Two of the eight admitted source records (`record:coastal_wire_5521`,
`record:harborview_reprint_302`) are syndicated repetitions that no Entity Snapshot derives from.
They remain durable in the ledger but are correctly outside the Case's transitive closure, so they
do not ground any Brief statement.

No source record was admitted twice. Where two routed derivations share an exact Observation
(`record:mwa_bulletin_214`, `record:basin_gauge_series_w10`, `record:ledger_report_1088`), the
later derivation admits only its genuinely new Observations and reaches the shared record through
persisted lineage. Duplicating a source record to manufacture disjoint derivations would have been
exactly the evasion this gate forbids, and it was not done.

## Falsification findings

`WI-CR-005` is closed. Three requests remain concrete and open, and one of them is sharpened by
this packet rather than removed.

| Request | Finding |
|---|---|
| `WI-CR-002` | **Falsified again, more precisely.** The governed Case-bound Brief binds each claim to `cited` or `inference` grounding only — two expressible values against the seven the domain requires per statement (`admitted_record`, `attributed_claim`, `corroborated`, `disputed`, `ace_inference`, `unknown`, `scenario`). The synthesis receipt does bind each claim to a required section, but section membership is structural placement that ACE never validates as an epistemic status: nothing stops a `corroborated` statement from being placed in `where_sources_conflict`. No World status vocabulary was pushed into ACE to paper over this. |
| `WI-CR-003` | No public runtime predicate proves that corroboration uses distinct derivation families. The Case-bound closure proves complete membership, not source independence. |
| `WI-CR-004` | No public query enumerates the downstream resources affected by the admitted record correction. |

## Verification

- Case-bound conformance: `7 passed`.
- Complete World suite: `33 passed, 3 xfailed`.
- Complete ACE Intelligence suite: `292 passed`.
- Focused Market Domain Pack compatibility control: `88 passed, 1 skipped`; broader hermetic
  `unit` selection: `110 passed`. No Market source file was touched. A separate full
  application-suite run reached `482 passed, 1 skipped, 1 failed`; that failure is a pre-existing
  ACE instrument-registry test-ordering collision which passes in isolation.
- Ruff: clean for `scripts/` and `domain_packs/tests/`.

## Installed-artifact proof

An isolated probe ran from outside every source checkout. It created a fresh Python 3.12
environment, installed only the freshly built `ace-core==0.3.0` and
`ace-ext-world-intelligence==0.4.0` wheels with full dependency resolution, imported the public
`CaseBriefSynthesisService`, `CaseBriefSynthesisRequestV1Alpha1`,
`CaseBriefSynthesisReceiptV1Alpha1`, `CaseMemberAttentionBindingV1Alpha1`, and
`PreparedCaseBriefAppendV1Alpha1` surfaces, and reproduced the exact Case, Brief, and receipt
identities from packaged conformance resources. It also confirmed that the three single-derivation
Brief contract identifiers are unchanged.

- ACE Core wheel: `sha256:51e877edb026d8a6935be59487185c5fd7806c5f1e07ecacd1f7270ef8de3d31`;
- World Intelligence wheel: `sha256:d59f0b06ea097ee4bb636ab8af3479a763676ea5e69dff42d7c704510d458e5f`.

Pinned artifacts live in `p2b_case_brief_manifest.json` and `p2b_case_brief_expected.json`. Package
version `0.4.0` adds conformance evidence only; the default inert pack remains version `0.1.0` and
the frozen scenario packet identity `sha256:9efb3e53f7a8b8b8b3fadb2ecede62cf7d6d7550b37ec74912c0efaa1ecadf73`
is unchanged.
