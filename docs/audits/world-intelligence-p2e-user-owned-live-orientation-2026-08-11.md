# World Intelligence P2E user-owned LIVE orientation audit — 2026-08-11

## Result

P2E freezes the next consumer boundary over the accepted P2D NASA/ESA packet. Public
`ace-core==0.5.0` already supports exact inert Monitor, PersonaBinding, and Subscription contracts;
World now constructs and pins those three contracts without adding a domain-private runtime.

Owner-enforced pause/resume/revoke lifecycle and bounded sensing-window dispositions are not public
ACE 0.5.0 capabilities. They remain explicit contract requests `WI-CR-007` and `WI-CR-008`. No
runtime Monitor lifecycle, scheduler, source acquisition loop, or Subscription delivery is claimed.

## Exact static intent

| Resource | Accepted identity |
|---|---|
| Planetary-defense pack | `pack_ir:bb400cc0652622b43c01504e651110e0` |
| Activation revision | `activation_revision:385d00a35e8bf7a39ec07c630ac36eec` |
| Monitor | `monitor:bbb0e5ab246c6d1f08f7669226db6873` |
| Principal/persona binding | `persona_binding:1349e5c7f78270dd5c8e267b582a1399` |
| Record-only Subscription | `subscription:3bb149effa91c5fdd224780ae0a455ee` |
| P2E packet | `sha256:5690d6c1f6e9361e93eea558f9bb2f06dd2491f5b29b59836100a23a92850df8` |

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

These are frozen consumer expectations, not executed time-based windows. Every request time is
explicit. The cadence preference grants no scheduler or autonomous execution.

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
- P2E materializes no new LIVE or PREPARED runtime records while its two contracts are open.
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
| Focused P2E suite | `11 passed` |
| Complete World domain suite | `101 passed` |
| Complete connector suite | `80 passed` |
| Release-contract suite | `7 passed` |
| Ruff lint and format | passed |
| Candidate wheel JSON payload | exactly 59 resources |
| Planetary-defense wheel payload | exactly 13 resources, including four P2E conformance files |
| Executable wheel payload | none |
| Isolated public-artifact probe | World 0.9.0 + public ACE Core 0.5.0; all three intent identities reproduced; no checkout import |

Build artifacts from this working-tree verification:

- wheel SHA-256: `d77a12211356c808cfc44d90f3a87c202be653cd8953ffc6a43fac622ba894c4`;
- source-distribution SHA-256: `f60496946c6881da34a3dce8b4e6b014e6bea633f74219dad26eeb6531cdf4db`.

These are local candidate hashes, not published release identities.
