# World Intelligence roadmap status — 2026-08-06

The canonical current domain roadmap is [`../ROADMAP.md`](../ROADMAP.md). This dated file preserves
the detailed World-side packet status and evidence history that led to it; it is not the current
dispatch surface.

## Status by packet

| Packet | Status | Evidence |
|---|---|---|
| P2A — inert pack and compiler falsification | **Verified 2026-08-06** | [`docs/audits/world-intelligence-p2a-2026-08-06.md`](audits/world-intelligence-p2a-2026-08-06.md); `pack_ir:683de57a71669814e507d07d65a109db`; 7 conformance tests |
| P2B — prepared epistemic scenario | **Interpreter replay, immutable Case closure, governed Case-bound Brief, per-statement epistemic status, derivation-family independence, and supersession impact all verified 2026-08-07** | [`docs/audits/world-intelligence-p2b-case-brief-2026-08-07.md`](audits/world-intelligence-p2b-case-brief-2026-08-07.md); [`docs/audits/world-intelligence-p2b-status-case-brief-2026-08-07.md`](audits/world-intelligence-p2b-status-case-brief-2026-08-07.md); [`docs/audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md`](audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md); [`docs/audits/world-intelligence-p2b-supersession-impact-2026-08-07.md`](audits/world-intelligence-p2b-supersession-impact-2026-08-07.md); 8 Observations, 5 Shifts, 4 Signals, 1 Case, 1 governed Brief over 26 closure resources; all seven statuses bound per statement; corroboration proven independent; correction impact projected; `70 passed, 0 xfailed` at the time of writing, superseded by `81 passed` for the complete suite once P2C landed (re-measured 2026-08-08) |
| P2C — governed LIVE official-source proof | **Governed admission, exact replay, restart replay, and artifact binding verified 2026-08-07; reviewed network transport remains separate** | [`docs/audits/world-intelligence-p2c-federal-register-live-2026-08-07.md`](audits/world-intelligence-p2c-federal-register-live-2026-08-07.md); additive pack `pack_ir:1847032fc5301bba9b6f85d3d091400d`; adapter wheel SHA-256 `6b794c47…9b1f97`; one capture, 5 atomic LIVE records, zero downstream intelligence/action |
| P2C2 — official-record Reality Brief into reviewed action | **Released in World Intelligence 0.9.0 on 2026-08-10** | Two exact FCC records; stable LIVE entity; Shift; Signal; routed attention; six-claim/two-citation LIVE Brief; governed Decision; exact review; create-only export; verification; promotion; no second reasoning/effect on replay. Fresh public-artifact environment: 83 World + 26 connector + 2 focused tests passed without a Core checkout; public World wheel clean-install verified. See [`docs/audits/world-intelligence-p2c2-governed-reality-brief-2026-08-10.md`](audits/world-intelligence-p2c2-governed-reality-brief-2026-08-10.md). |
| P2D — multi-source conflict and correction | Partially pre-staged: the P2B fixtures already model multi-family conflict and append-only correction; runtime proof not started | — |

## P2B deliverable inventory

- Frozen 72-hour synthetic scenario `meridia_reservoir_release_72h` (fictional Republic of
  Meridia; no real actor, institution, or current controversy).
- Pinned expected graph, provenance families, claim transitions, supersessions, shifts, signals,
  and the exact seven-status Reality Brief.
- Nine fail-closed negative vectors, including false independent corroboration, history rewrite,
  persona-dependent status, stale closure, and divergent replay.
- The frozen packet recorded four consumer contract requests (`WI-CR-001` … `WI-CR-004`).
  `WI-CR-001` is now satisfied by ACE's generic detection `v1alpha2` contract and a World-owned
  compile proof covering the event, record-correction, and claim-support transitions. The three
  remaining requests stay quarantined. No private detector, graph, store, reasoning path,
  authority system, source-independence engine, or feedback loop exists in this repository.
- The additive PREPARED interpreter replay now exercises all five frozen Shifts and all intended
  Signals. ACE's generic resource-set admission preserves the corroboration Shift without a
  Signal. ACE's public immutable Case freezes four routed Signals plus that non-routed Shift and
  transitively binds all 28 scenario resources.
- The additive Case-bound packet closes `WI-CR-005`: ACE's public `CaseBriefSynthesisService`
  binds that exact Case, validates its complete 26-resource member closure and the four exact
  routed attention receipts, derives one compatible template and persona scope, and emits one
  governed Brief `brief:8fb3173069eca502652b1c9c004c92e6` with Case lineage. Nothing is aggregated
  privately in this repository and no World semantics were added to ACE.

## Gate status against the P2 acceptance gate

| Gate item | Status |
|---|---|
| 1. Compile/activate/upgrade/rollback through unchanged ACE | Compile and activation-bound replay proven; committed lifecycle/rollback proof remains open |
| 2. Installed-artifact identity reproduction | Proven through the public World 0.9.0 wheel with public Core 0.5.0; the monitor pack resolves from `site-packages` and the optional executable source adapter remains absent. |
| 3. Seven-status golden Brief without unsupported promotion | Verified end to end. WI-CR-002 and WI-CR-005 are closed: every statement carries one pack-declared status validated by ACE against its exact supports, while Core's separate grounding kind remains unchanged. |
| 4. Source-family lineage vs. repetition | Verified at runtime; WI-CR-003 is closed through the domain-neutral derivation-family closure and negative repetition vectors. |
| 5. Corrections append without rewriting history | Verified at runtime; WI-CR-004 is closed through immutable supersession-impact projections over both frozen corrections. |
| 6. Market + World simultaneous isolation | Proven at install/compile level (P2A); runtime co-activation pending |
| 7. Fail-closed negative cases | 5 compiler vectors (P2A) + 9 scenario vectors (P2B); generic categorical declarations now compile through ACE `v1alpha2` |
| 8. No World/political nouns in Core or Intelligence | Continuously asserted by the leak test; still green |

## P2B-SB1 — per-statement epistemic status (2026-08-07)

`WI-CR-002` is **closed**. The seven World statuses are declared in the inert Pack module
`modules/epistemic_status.json` (`ace.intelligence.epistemic-status/v1alpha1`) and bound to exact
claim IDs by ACE's public `CaseBriefStatusSynthesisService`, then persisted as a durable
`brief_epistemic_status_projection` record in the same atomic transaction as the Brief and its
synthesis receipt.

ACE learned no World vocabulary: `ClaimGroundingKind` remains `{cited, inference}`. The old
strict-xfail that would have closed `WI-CR-002` by adding `attributed` to that enum was the wrong
close condition and has been replaced.

New exact identities (additive pack `world_intelligence` 0.3.0,
`pack_ir:36cccb917b1420bf85e8c79f0dd9c579`):

- `case:bc28c76926d733c0ce0fe03b9c9222db`
- `brief:7adb24b596cac21d7aa4e5476bc8733c`
- `case_brief_synthesis_receipt:e79d934e0300901e18e0fe4af1064ba2`
- `brief_epistemic_status_projection:fca9062883e92e2e632388c0069c310e`

The frozen WI-CR-005 identities `case:2ee200c03f2576307b0bc43e6e128f30` and
`brief:8fb3173069eca502652b1c9c004c92e6` are unchanged. Declaring a Pack module necessarily
re-keys resources admitted under it, so this packet activates a separate additive revision
rather than mutating the frozen one.

`WI-CR-003` and `WI-CR-004` remain **open**. The declared `corroborated` status enforces a
minimum admitted-Observation support count and a closed support-kind set; it does not prove
independent source families, and the platform pins
`proves_source_family_independence` to `False` so no Pack can overclaim it.

### Next dispatch

`WI-CR-003` — a public, domain-neutral source/derivation-family predicate over Observation
lineage, so a `corroborated`-style status can require *independent* families rather than only a
support count. That is the single remaining blocker to a fully load-bearing corroboration label.

## P2B-IB1 — derivation-family independence (2026-08-07)

`WI-CR-003` is **closed**. ACE now exposes a public, domain-neutral derivation-family closure
over admitted Observation lineage (`observation_lineage_root_closure/v1alpha1`), and a Domain Pack
opts in by declaring `min_distinct_derivation_families` on a status through the sibling module
contract `ace.intelligence.epistemic-status/v1alpha2`.

World's `corroborated` now requires two distinct families. The Ledger report and the Basin
hydrology dataset corroborate; the Coastal Wire syndication and the Harborview reprint both
collapse into the Ledger root and cannot corroborate anything it asserts — not individually, and
not as a pair, despite being two different publishers. All three repetition vectors are rejected
at runtime with no durable residue.

New exact identities (additive pack `world_intelligence` 0.4.0,
`pack_ir:c6f8dd96892e51cac7e9ea5a27480f56`):

- `case:412426eee708d56f6bda931ccf9e5d8b`
- `brief:25d8232c9bfa27050bdcb160fb75f06c`
- `case_brief_synthesis_receipt:0016875ed9869be69714b5a9c8cefb4f`
- `brief_derivation_family_status_projection:3500889a2d75af7a5484a681afbee34c`

The WI-CR-005 and WI-CR-002 packets are byte-identical and unchanged. This packet brings the
syndicated copies into its own Case closure — a deliberate, approved consequence — so its
`unreferenced_admitted_records` is `0` and the negative vectors fail on the independence
predicate rather than on the pre-existing unknown-support guard.

Honest limit: independence is only as strong as the admitted lineage. Two Observations that share
an origin without declaring lineage between them still count as two families. ACE never treats
publisher count or textual variation as independence.

`WI-CR-004` is now **closed** by P2B-SI1 below.

### Next dispatch

`WI-CR-004` — a public projection enumerating the downstream resources affected by an admitted
correction or supersession, so a Brief can disclose what a correction invalidates.

## P2B-SI1 — supersession impact (2026-08-07)

`WI-CR-004` is **closed**, and the World consumer contract-request backlog is now empty. ACE
exposes a public, domain-neutral traversal that enumerates what depended on a superseded record,
appended as one additive immutable record under governed authorization. No Pack module was needed,
so this packet **reuses the WI-CR-003 activation unchanged** and reproduces
`case:412426eee708d56f6bda931ccf9e5d8b` and `brief:25d8232c9bfa27050bdcb160fb75f06c` byte-for-byte.

Both frozen corrections are exercised with genuinely different blast radii:

| Supersession | Impacted | Unaffected | Impacted claims |
|---|---|---|---|
| `correction_114` over `ledger_report_1088` | 11 | 16 | 9 (3 full) |
| `order_47` over `mwa_bulletin_214` | 7 | 20 | 5 (0 full) |

New exact identities:

- `supersession_impact_projection:f3723de8e9ac5c4390c5c46137f3765e`
- `supersession_impact_projection:61e8fb0eae42019e7344e97210638a54`

The prior Brief stays immutable: unchanged identity, byte-identical replay, no new reasoning, and
a cutoff that precedes the correction. Impact is **dependency, not falsehood** — the projection
discloses the unaffected set and the exact path behind every in-scope resource rather than issuing
a verdict.

### Next dispatch

No platform contract request remains open. The presentation packet is now implemented as
`scripts/public_demo.py`: one command runs the accepted independence and supersession-impact
harnesses and renders a deterministic, self-contained visual proof plus its machine-readable data.

P2C is now implemented as an additive activation pack plus a separately versioned, read-only
Federal Register adapter. The original World pack hashes remain frozen. The accepted transport is
recorded and network-free.

P2C2 now carries that official-record path through public ACE Core 0.5.0:
two recorded official snapshots become a configured categorical Shift and routed Signal, then one
Core-governed LIVE Reality Brief. A human Decision authorizes the exact action type; a separate
review binds the effect-free plan before Core admits execution; verification and promotion remain
separate after the create-only workspace export. The Domain Pack remains JSON-only and never owns
action authority. The same journey now passes with Core installed from PyPI and the reference
adapter installed from the Core `v0.5.0` GitHub release, with no Core checkout.

The next bounded dispatch is a separately reviewed opt-in network transport and P2D LIVE
multi-source conflict/correction. Visible
PREPARED/LIVE separation and the prohibition on autonomous publishing remain invariant.
