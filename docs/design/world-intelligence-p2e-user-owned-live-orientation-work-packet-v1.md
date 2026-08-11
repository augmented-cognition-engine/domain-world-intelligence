# P2E work packet — user-owned LIVE orientation

**Status:** merged-platform consumer candidate; public Core artifact replay pending

**Mode:** LIVE only; PREPARED material is excluded

**Runtime status:** six lifecycle-governed sensing windows materialized and exactly replayed

## Purpose

P2E turns the P2D one-shot planetary-defense proof into an explicit user-owned sensing intent
without moving universal lifecycle or sensing-window semantics into the World domain. The packet
now consumes the generic implementation merged in Core
[#94](https://github.com/augmented-cognition-engine/core/pull/94) at
`f0d2191ba7cf2d33ccfc3c821422786929be8349`.

Released `ace-core==0.5.0` exposes inert, domain-neutral `MonitorV1Alpha1`,
`PersonaBindingV1Alpha1`, and `SubscriptionV1Alpha1` contracts. Merged Core source adds the public
owner lifecycle and bounded sensing-window contracts and application services. P2E constructs,
materializes, and pins those resources against a checkout-free wheel whose source tree is identical
to the merged commit. The Subscription remains `record_only`, so the new receipts grant no delivery
effect. Public-index Core installation remains a later release receipt rather than a claim here.

The scenario reuses the exact P2D NASA/ESA publication lineages, pack activation, historical Brief,
corrected Brief, and correction semantics. It adds no new factual claim and performs no network
request. Six owner-requested sensing windows exercise active sensing, exact no-change suppression,
visible correction, pause, resume, and revocation.

## Frozen sequence

1. The owner creates one inert LIVE Monitor, one principal-to-persona binding, and one record-only
   Subscription bound to the accepted P2D pack through public ACE 0.5.0 contracts.
2. Window `w1` admits the two earlier NASA/ESA publications and surfaces the historical divergence.
3. Window `w2` sees the exact same admitted material and records `no_material_change`; it creates no
   new Shift, Signal, Case, Brief, or source record.
4. Window `w3` surfaces the NASA revision and its same-lineage supersession. A correction may never
   be hidden by duplicate or fatigue suppression.
5. The owner pauses the monitor. Window `w4` performs zero acquisition and records `owner_paused`.
6. The owner resumes the monitor. Window `w5` surfaces the ESA revision and the accepted corrected
   Reality Brief.
7. The owner revokes the subscription. Window `w6` performs zero acquisition and records
   `subscription_revoked`.

Every window is explicitly requested. The packet declares cadence preferences but grants no
scheduler, timer, daemon, delivery channel, publication, or external-action authority.

## Ownership boundary

- One stable `owner_ref` must bind the monitor, subscription, lifecycle events, and attention
  policy. Ownership cannot be inferred from a device, API credential, source, persona, or publisher.
- Only that owner may pause, resume, or revoke the intent in this packet.
- Paused or revoked state blocks acquisition before a source adapter or transport is invoked.
- Subscription revocation is terminal for later windows; replay may reopen the revocation but may
  not silently reactivate it.
- Attention remains an internal route-or-suppression disposition. P2E authorizes no delivery.

## Correction and independence boundary

- `no_material_change` applies only when the exact admitted source identities are unchanged.
- A newly admitted correction or supersession is material and must remain visible.
- NASA and ESA count as two claimant publication roots. The packet does not claim independent
  measurements, observation campaigns, models, or truth.
- Same-lineage before/after publications never manufacture corroboration.
- P2D historical artifacts remain immutable and reopen with the accepted identities.

## Closed public-platform contract requests

### WI-CR-007 — owner-enforced Monitor and Subscription lifecycle

Closed by Core #94. ACE Intelligence now has append-only lifecycle transitions for create, pause,
resume, and revoke. The application service authorizes transitions against the bound principal,
preserves a stable logical intent and append-once sequence, enforces terminal revocation, and
provides exact restart replay. World contributes only the subject, source requirements, persona,
and policy references.

### WI-CR-008 — bounded sensing-window disposition

Closed by Core #94. ACE Intelligence now has a domain-neutral, append-only sensing-window receipt
that records the authorizing Monitor/Subscription revisions, requested interval, source transaction
references, accepted new resources, and exactly one routed-or-suppressed disposition. P2E proves
paused and revoked windows contain zero acquisition and correction material cannot collapse into
`no_material_change`.

Neither implementation lives in the Domain Pack. World imports the generic contracts and services
without adding World vocabulary to Core. `WI-CR-007` and `WI-CR-008` are closed for merged-source
consumer acceptance; public-artifact reproduction remains explicitly pending.

## Fail-closed vectors

The conformance validator rejects missing or changed ownership, PREPARED/LIVE mixing, acquisition
while paused, acquisition after revocation, correction suppression, false measurement independence,
hidden delivery, autonomous scheduling, historical rewriting, and replay divergence.

## Acceptance

- The positive packet validates with zero violations and an exact replay identity.
- All ten negative vectors fail with their pinned first violation.
- The accepted P2D pack and Brief identities remain unchanged.
- The three static public contracts construct with exact pinned identities; five lifecycle
  transitions and six sensing-window receipts append exactly and replay after fresh service
  construction.
- Captured NASA/ESA LIVE Observations remain source-linked through three Shifts, three Signals, two
  Cases, and the original cited Reality Brief identities.
- The composed ledger contains 62 LIVE records—44 P2D records plus 18 monitoring records—and zero
  PREPARED records.
- The Domain Pack stays JSON-only and gains no authority request beyond source read.
- No network, scheduler, delivery, publication, persuasion, Decision, Outcome, or external action is
  executed or implied.
