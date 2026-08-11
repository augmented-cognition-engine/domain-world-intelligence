# World Intelligence P2E user-owned LIVE orientation audit — 2026-08-11

## Result

P2E materializes the next consumer boundary over the accepted P2D NASA/ESA packet. Public
`ace-core==0.5.0` supplies the exact inert Monitor, PersonaBinding, and Subscription contracts. Core
PR [#94](https://github.com/augmented-cognition-engine/core/pull/94), merged as
`f0d2191ba7cf2d33ccfc3c821422786929be8349`, adds the domain-neutral owner lifecycle and bounded
sensing-window services. World consumes those public seams without adding a domain-private runtime.

`WI-CR-007` and `WI-CR-008` are closed for merged-source consumer acceptance. Five owner lifecycle
transitions and six sensing-window dispositions append immutably and replay through newly
constructed services. There is still no scheduler, autonomous source loop, delivery, publication,
or external action. Public-index Core reproduction remains pending a versioned Core release.

## Exact static intent

| Resource | Accepted identity |
|---|---|
| Planetary-defense pack | `pack_ir:bb400cc0652622b43c01504e651110e0` |
| Activation revision | `activation_revision:385d00a35e8bf7a39ec07c630ac36eec` |
| Monitor | `monitor:bbb0e5ab246c6d1f08f7669226db6873` |
| Principal/persona binding | `persona_binding:1349e5c7f78270dd5c8e267b582a1399` |
| Record-only Subscription | `subscription:3bb149effa91c5fdd224780ae0a455ee` |
| P2E packet | `sha256:e35f892af752db6dc4e6bf0cd6f6c5e9f7f4b74749f952ccb7effee701ad9d9e` |

The binding names one fixture principal and the `planetary_defense_researcher` pack persona. The
Subscription selects both accepted planetary-defense Signal types and the existing Reality Brief
template. Its delivery disposition is `record_only`; no delivery adapter or effect is present.

## Six frozen sensing windows

| Window | State | Material | Disposition | Acquisition requests |
|---|---|---|---|---:|
| `w1` | active | earlier NASA/ESA divergence | routed | 2 |
| `w2` | active | exact replay, no new material | `no_material_change` | 2 |
| `w3` | active | NASA same-lineage correction | routed and visible | 1 |
| `w4` | owner paused | none | `owner_paused` | 0 |
| `w5` | resumed | ESA same-lineage correction | routed and visible | 1 |
| `w6` | subscription revoked | none | `subscription_revoked` | 0 |

These windows are now executed as explicit requests over immutable completed evaluations. Every
request and interval is bounded and replayed exactly. The cadence preference still grants no
scheduler or autonomous execution.

## Captured LIVE lineage

The same recorded, network-free official-source adapters capture four dated publications under two
claimant roots. The resulting LIVE path is preserved exactly:

```text
4 source-linked Observations
→ 3 Shifts
→ 3 Signals
→ historical + corrected Cases
→ cited Reality Briefs (2 and 4 citations)
```

The Briefs remain `brief:c3549af0262b100ca65024ee19cbae6e` and
`brief:806d69d8e41f83f93ee3dc10f58f0d16`; P2E does not rewrite the P2D record graph.

## Fail-closed evidence

Eleven mutations fail with pinned first violations:

- missing owner and changed owner;
- PREPARED/LIVE mixing;
- acquisition while paused and after revocation;
- correction hidden as no material change;
- publication roots misrepresented as independent measurements;
- hidden delivery and autonomous scheduling;
- historical Brief rewriting; and
- divergent replay identity.

## Boundary

- The accepted P2D prerequisite remains 44 LIVE records and zero PREPARED records.
- P2E adds 18 LIVE monitoring records—five lifecycle transitions with their append-only anchor and
  revision material plus six sensing receipts—for 62 composed LIVE records and zero PREPARED
  records.
- NASA and ESA remain independent claimant publication roots only.
- Corrections are always material and visible; same-lineage revisions add no corroboration family.
- The Domain Pack remains JSON-only and requests only source-read authority.
- The packet performs no network access, scheduling, delivery, publication, persuasion, Decision,
  Outcome, or external action.

## Verification

| Check | Result |
|---|---:|
| P2E acceptance projection | zero violations; exact packet replay |
| P2E negative vectors | 11/11 fail closed with pinned first violations |
| Focused P2E + pack-pin suite | `14 passed` |
| Complete World domain suite | `102 passed` |
| Complete connector suite | `80 passed` |
| Release-contract suite | `7 passed` |
| Changed-file Ruff lint and format | passed |
| Candidate wheel JSON payload | exactly 59 resources |
| Planetary-defense wheel payload | exactly 13 resources, including four P2E conformance files |
| Executable wheel payload | none |
| Checkout-free merged-tree probe | World candidate + local Core wheel from the exact Core #94 tree; all lifecycle/window and LIVE lineage identities reproduced from `site-packages` |

Build artifacts from this working-tree verification:

- Core candidate wheel SHA-256:
  `82a0b365b83a79672685f6c2e71370a7f7218cf56e8c872064961e6e38985d7a`;
- World wheel SHA-256:
  `d256293ee16d9a641fa02b52a36322b85eb5c48960667649335ce313c5be2100`;
- World source-distribution SHA-256:
  `1005516d8d09e6b10720049b5da1e46d5ac6973483385ab38223d2912050e2e6`.

The World wheel reproduced byte-for-byte in two builds under the frozen source epoch. It contains
59 JSON resources, 13 under the planetary-defense pack, and zero Python payloads. The Core wheel's
source tree `9690d1e75f07b75d1e0bc1aab73b4d9ee145f2e1` is byte-identical to merged commit
`f0d2191ba7cf2d33ccfc3c821422786929be8349`. A checkout-free import loaded both Core and World from
`site-packages` and exposed both monitoring services.

These are local candidate hashes, not published release identities.
