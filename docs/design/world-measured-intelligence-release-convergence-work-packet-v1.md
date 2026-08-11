# World measured-intelligence release convergence work packet (v1)

**Status:** bounded artifact candidate. This packet does not publish World or Core, close ACE Core
issue [#38](https://github.com/augmented-cognition-engine/core/issues/38), pass SI4, or complete ACE
0.6.0.

**Frozen:** 2026-08-10 from World P2C10 commit
`112c0725b87ff59cf6b480a519aa2d4aa6a5fb53` and Core observed-result commit
`433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Turn the source-checkout P2C10 result into one canonical, machine-readable candidate record whose
Core runtime is installed from exact built artifacts outside the Core checkout:

```text
recorded public BLS release + erratum
  -> exact Observation / correction lineage
  -> matched corrected and stale-form artifacts
  -> Decision -> reviewed Action -> exact observed result -> Outcome
  -> useful evaluation -> non-effective proposal -> historical replay
  -> canonical convergence-v1.json
```

## Acceptance

The generator must:

1. hash the exact Core, separate reference action-adapter, World source-adapter, and World wheels;
2. reject a runtime importing `ace` from any declared Core checkout;
3. rerun the complete P2C2-P2C10 append-only journey without network access;
4. freeze stable source keys, product-policy version/rule, comparison, classification, proposal,
   replay, and non-claim fields while excluding wall-clock-dependent record and material digests;
5. fail if the fixture, source identities, scores, matched effect, useful classification,
   proposal-only authority, or historical replay drifts; and
6. reproduce the committed JSON byte-for-byte from a fresh workspace.

The candidate still carries package version `0.5.0` because no release version is changed in this
packet. The full artifact hash and source commit distinguish it from the released 0.5.0 wheel.

## Ownership and exclusions

World owns the BLS fixture, correction policy, matched control, artifact generator, and public
record. Core owns immutable identity, authority, Decision, reviewed Action, Outcome, and durable
replay. Intelligence owns only the neutral evaluation and proposal contracts. No BLS or World noun
moves into Core or Intelligence.

This packet does not add network transport, source freshness, a proposal-application path, a new
Domain Pack entry, schema, package version, CLI, or action authority. It does not establish
causality, population performance, statistical validity, general source independence, or human
benefit.

## Owned files and rollback

- `scripts/measured_intelligence_release_convergence.py`
- `domain_packs/tests/test_measured_intelligence_release_convergence.py`
- `artifacts/measured-intelligence/convergence-v1.json`
- this work packet, its audit, and restrained README/roadmap references

Rollback removes those additive files and references. No durable history or released artifact is
rewritten.

## External release gates

Independent Market reproduction now exists as a separate candidate, but combined compatibility,
security, repository hygiene, and release-owner review remain required. Core issue #49 F1, F3,
and F5 retain overdue `next minor` deadlines; this packet neither implements nor re-dates them.
