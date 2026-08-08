# World Intelligence — P2B-IB1 independence-aware Reality Brief (2026-08-07)

Closes **WI-CR-003**. Keeps **WI-CR-004** open.

## Result

`corroborated` now means **two genuinely independent derivation families**, not
two records. The frozen `meridia_reservoir_release_72h` scenario proves it
through public ACE APIs and Pack IR only.

| Vector | Supports | Families | Outcome |
|---|---|---|---|
| `independent_roots` | Ledger report + Basin gauge | 2 | **accepted** |
| `ledger_plus_coastal_wire_syndication` | Ledger report + Coastal Wire copy | 1 | rejected, no residue |
| `ledger_plus_harborview_reprint` | Ledger report + Harborview reprint | 1 | rejected, no residue |
| `two_publishers_one_origin` | Coastal Wire + Harborview | 1 | rejected, no residue |

Every rejection raises `CaseBriefFamilyStatusSynthesisError`, names the
derivation-family requirement, and leaves `durable_brief_count == 0`.

The last row is the sharpest: **two different publishers, zero independence**,
because both declare `derived_from` the Ledger report.

## Exact new identities (P2B-IB1, pack `world_intelligence` 0.4.0)

| Artifact | Identity |
|---|---|
| Independence pack IR | `pack_ir:c6f8dd96892e51cac7e9ea5a27480f56` |
| Case | `case:412426eee708d56f6bda931ccf9e5d8b` |
| Brief | `brief:25d8232c9bfa27050bdcb160fb75f06c` |
| Synthesis receipt | `case_brief_synthesis_receipt:0016875ed9869be69714b5a9c8cefb4f` |
| Status projection | `brief_derivation_family_status_projection:3500889a2d75af7a5484a681afbee34c` |

## Prior packets are untouched

Declaring a Pack module *and* admitting Observation lineage both change
canonical payloads, so this packet necessarily re-keys its own resources. It
therefore builds a **third** additive activation and leaves both earlier
harnesses byte-identical:

- WI-CR-005: `case:2ee200c03f2576307b0bc43e6e128f30`, `brief:8fb3173069eca502652b1c9c004c92e6`
- WI-CR-002: `case:bc28c76926d733c0ce0fe03b9c9222db`, `brief:7adb24b596cac21d7aa4e5476bc8733c`

`test_earlier_packets_are_untouched_by_this_additive_packet` asserts all four.

## The approved consequence: no unreferenced records

The syndicated copies had to enter the exact Case closure. Otherwise a negative
vector would have been rejected by the pre-existing "unknown support" guard
rather than by the independence predicate — a test passing for the wrong reason.
Widening the corroborated claim's basis brings both copies in, so this packet's
closure is 28 resources and `unreferenced_admitted_records` is **0** (the frozen
packet keeps its 2). `test_the_syndicated_copies_join_the_closure_in_this_packet_only`
pins both sides.

## How independence is decided

A family is the transitive root of an Observation's admitted lineage, following
`derived_from` and `supersedes` only. The scenario yields **5 families** across the
8 admitted Observations, disclosed as exact membership rather than bare roots:
the Ledger reporting family with **4 members** (report + wire + reprint +
correction) and four single-member roots. Membership is total and
non-overlapping — every admitted Observation belongs to exactly one family.

`test_syndication_and_reprints_collapse_and_cannot_corroborate` asserts that
Coastal Wire and Harborview are **exact members of the Ledger root family**, not
merely that they are not roots themselves.

ACE never consults publisher identity, `source_ref`, payload text, or
acquisition path. The durable projection discloses
`derivation_family_policy = observation_lineage_root_closure/v1alpha1`, the exact
`collapsing_relations`, the full closure family assignment, and per claim the
exact roots, the count, and the requirement applied.

## Honest limit

**Independence is only as strong as the admitted lineage.** If two Observations
share an origin but declare no lineage between them, ACE counts them as two
families. This predicate collapses *declared* derivation structure; it does not
discover undeclared common origin. The P2B golden fixture's
`independent_family_ids` remains a fixture assertion and was not promoted into a
runtime guarantee beyond what the lineage supports.

**WI-CR-004 stays open.** No public projection enumerates the resources affected
by the admitted record correction.

## Boundary invariants

World added no private graph, persistence, authority, reasoning runtime, status
projector, **source-independence engine**, or imperative Pack code. The
vocabulary is a declarative JSON module (`modules/epistemic_status_v2.json`);
everything else is a public ACE call. `ClaimGroundingKind` remains
`{cited, inference}` and ACE learns no World label.

Market is unaffected: it stays on `epistemic-status/v1alpha1`, and a `v1alpha2`
Pack that leaves `min_distinct_derivation_families` at `1` behaves exactly as
before.

## Verification

```
domain_packs/tests    55 passed, 1 xfailed   (baseline 42 passed, 2 xfailed)
ruff check scripts/ domain_packs/            All checks passed
git diff --check                             clean
wheel probe   ace_ext_world_intelligence-0.6.0 packages the v1alpha2 module and manifest
```

Marketing regression control (source unchanged): `88 passed, 1 skipped`,
identical to baseline.
