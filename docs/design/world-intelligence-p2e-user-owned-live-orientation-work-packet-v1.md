# P2E work packet — user-owned LIVE orientation

**Status:** frozen consumer-acceptance packet

**Mode:** LIVE only; PREPARED material is excluded

**Runtime status:** partially materialized; lifecycle and sensing windows remain contract-blocked

## Purpose

P2E turns the P2D one-shot planetary-defense proof into an explicit user-owned sensing intent
without moving universal lifecycle or sensing-window semantics into the World domain. The packet
freezes the smallest acceptable platform boundary before implementation.

Released `ace-core==0.5.0` already exposes inert, domain-neutral `MonitorV1Alpha1`,
`PersonaBindingV1Alpha1`, and `SubscriptionV1Alpha1` contracts. P2E constructs and pins all three
through those public APIs. The Subscription selects `record_only`, so it grants no delivery effect.
The public contracts do not yet provide an owner-authorized pause/resume/revoke lifecycle or a
bounded sensing-window receipt; those narrower gaps remain explicit below.

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

## Public-platform contract requests

### WI-CR-007 — owner-enforced Monitor and Subscription lifecycle

ACE Intelligence already has domain-neutral immutable Monitor, PersonaBinding, and Subscription
resources. It still needs append-only lifecycle transitions for create, pause, resume, and revoke.
The platform must authorize transitions against the bound principal, preserve the stable logical
intent across revisions, enforce terminal revocation, and provide idempotent replay. World
contributes only the subject, source requirements, persona, and policy references.

### WI-CR-008 — bounded sensing-window disposition

ACE Intelligence needs a domain-neutral, append-only sensing-window receipt that records the
authorizing Monitor/Subscription revisions, requested interval, source transaction references,
accepted new resources, and exactly one disposition: routed material change or an explicit
suppression reason. Paused and revoked windows must prove zero acquisition. Correction material may
not be collapsed into `no_material_change`.

Neither remaining request belongs in a Domain Pack. Until public contracts close both requests,
P2E claims only the three inert public intent contracts—not lifecycle execution or sensing-window
runtime materialization.

## Fail-closed vectors

The conformance validator rejects missing or changed ownership, PREPARED/LIVE mixing, acquisition
while paused, acquisition after revocation, correction suppression, false measurement independence,
hidden delivery, autonomous scheduling, historical rewriting, and replay divergence.

## Acceptance

- The positive packet validates with zero violations and an exact replay identity.
- All ten negative vectors fail with their pinned first violation.
- The accepted P2D pack and Brief identities remain unchanged.
- The three static public contracts construct with exact pinned identities; lifecycle and sensing
  runtime materialization remain visibly false and both narrowed requests remain open.
- The Domain Pack stays JSON-only and gains no authority request beyond source read.
- No network, scheduler, delivery, publication, persuasion, Decision, Outcome, or external action is
  executed or implied.
