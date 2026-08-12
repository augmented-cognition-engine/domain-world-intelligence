# World Intelligence ACE 0.7E activation conformance evidence

**Result:** consumer candidate accepted locally against the exact installed Core wheel; publication
to a World draft PR remains the final handoff step.

## Artifact identities

| Artifact | Exact identity |
|---|---|
| Core source | commit `10bbed620291ac5f552c3313dd37580938a5b9d7`, base `dab0866af239af9a13b4d2772a0d3950f932fa2e` |
| Core wheel | `ace_core-0.6.0-py3-none-any.whl`, 5,955,226 bytes, SHA-256 `19b75ab8dd2e2cc69f432a97fd7401eb0f55c9b5b7e2deeed0ae17e2396dff57` |
| Core wheel availability | ephemeral `/tmp` input; no durable uploaded byte-retrieval coordinate; commit is source identity only |
| World wheel | `ace_domain_world_intelligence-0.9.0-py3-none-any.whl`, 83,276 bytes, SHA-256 `fe51c3266036b3a83c34d510ce3460524d4ad4a5ae515adc4272b2a9d3fc4ad8` |
| World Pack IR | `pack_ir:3358dd780974acaea5b0ebfc861f826f`, `sha256:3358dd780974acaea5b0ebfc861f826f36b334c47bb66200a9bf2e57150ba017` |
| Conformance | `pack_conformance:1f0da3850fa13fc5f636f38a32412490`, passing |

The authoritative Core wheel was independently checked before install and was never rebuilt,
overwritten, or substituted. The installed run loaded both distributions from the clean target's
`site-packages`; no Core source path was present.

## World lifecycle coordinates

| Stage | Plan | Revision / receipt |
|---|---|---|
| Onboarding handoff | `activation_onboarding_handoff:39e44660037d554016d034a665c76b57` | `pre_activation_handoff`, `live_authority=false` |
| Initial activation | `intelligence_activation_plan:48e481610646e676933a6459be3221ab` | `activation_revision:b066b8923626a8acd3aed163e667bfb6`; `governed_state_commit:fc36194a127a4fa38eae28aa71dba343` |
| Separately approved upgrade | `intelligence_activation_plan:ee2c82fae487e5ff0bcba86e69f82821` | `activation_revision:5a448f3ece35a4df5185a5f4f815fb61` |
| Separately approved rollback | `intelligence_activation_plan:75841bdf53cefd495121f3ce2ce9a590` | `activation_revision:31784ac368453b5d3099e2238d8a5952`; `governed_state_commit:98c16783fe20e4f1a16509d0a5baa218` |

All World coordinates are disjoint from the neutral Core comparison coordinates. Initial and
rolled-back committed material reloaded byte-equivalently from fresh admission-service instances.
Rollback names the exact earlier active revision and preserves the upgrade in immutable history.

## Exact preview and runtime bindings

The approved live-effect set is exactly `pack_activation`, `monitor_binding`,
`subscription_binding`, `shift_derivation`, and `brief_synthesis`. The only capability is the
secret-free `source_snapshot` implementation
`world_federal_register_recorded_snapshot@0.2.0`; the only authority is `source_read` under
`authority_grant:world-federal-register-reviewed-read`.

The current rollback revision binds these consumer resources:

- Monitor `monitor:33ac724d863d9ac3a0bee5ab035cb151`;
- persona binding `persona_binding:26826b2d07dcdd30dc026d02239233ce`;
- record-only Subscription `subscription:bc356674a985423addc2abfbcce576fe`;
- Shift `shift:eab8f3b0275360337a278c4d33f511e6`; and
- canonical Brief `brief:302af48e2089fce5303bab52315daa45`.

The rollback commit reference is
`ace.application.domain-activation-commit-reference/v1alpha2`, is exactly validated against its
committed tuple, and remains `authority_stage=historical_reference` and `live_authority=false`.
Parsing it as a runtime `activation-revision-reference/v1alpha1` fails validation. No lifecycle or
runtime authorization call receives the historical reference.

## Negative proof and checks

A receipt drifted to a foreign compiler contract is rejected as stale/mismatched before authority
resolution: zero approval calls, zero grant calls, and zero committed heads. The positive journey
requires three distinct approval subjects: initial, upgrade, and rollback plan IDs.

Verified locally:

- focused World 0.7E test: `1 passed`;
- complete World Domain Pack suite on the candidate: `90 passed, 1 expected optional-adapter skip`;
- connector plus release-contract suites on the candidate: `87 passed`;
- exact source-checkout consumer run in clean Core-wheel target: passed;
- exact installed World-wheel consumer run in a second clean target: passed with identical Pack,
  handoff, plan, revision, receipt, Monitor, Subscription, Shift, and Brief coordinates;
- Core wheel size/hash and World wheel size/hash: matched the identities above; and
- no network, credentials, provider call, external action, package upload, merge, or Core edit.

## Limitation

The already released World 0.9.0 wheel metadata requires `ace-core>=0.5.0,<0.6`; changing or
republishing that release was outside this task. The candidate World wheel was therefore installed
with dependencies disabled only after the exact Core 0.6.0 candidate wheel and all of its
dependencies were installed and verified. This proves the consumer APIs and packaged data against
the candidate, but it is not a public resolver-level compatibility or release claim. A future World
release must deliberately update its Core compatibility window after ACE 0.7E acceptance.
