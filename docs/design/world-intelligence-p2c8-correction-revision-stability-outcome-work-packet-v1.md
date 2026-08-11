# World Intelligence P2C8 correction-revision-stability outcome work packet (v1)

**Status:** stacked source-checkout candidate; this packet does not release World Intelligence,
apply a governance proposal, close ACE Core issue #38, pass SI4, or complete ACE 0.6.0.

**Frozen:** 2026-08-10 from World P2C7 commit
`216a37a1fdcb4f0baf9ac148ab9e525559141c22`, stacked on the Core exact observed-result
provenance candidate `433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Measure whether a correction-induced Brief revision changes the claim it should while preserving
the exact identities of claims the correction does not affect. The packet extends the governed
recorded-data journey:

```text
original Observation + correction Observation -> prior Brief
  -> treatment revision / unrelated-drift control
  -> Decision -> reviewed Action -> exact independent revision review
  -> observed Outcome -> useful / harmful / unproven evaluation -> proposal only
```

The source pair remains FCC Federal Register document `2020-28779` and its explicit correction
`2021-10670`. P2C8 creates actual domain-neutral `BriefV1Alpha1` records rather than a weaker
World-only summary shape. The prior Brief has one affected instruction claim and two stable facts.
Both revised Briefs replace the affected claim with the exact correction instruction, retain the
same two source citations, and keep the claim count at three. Treatment reuses the exact two stable
claim identities; the control paraphrases both stable facts and therefore changes their content
identities despite unchanged correction semantics and source coverage.

## Product-owned review policy

World owns `world_recorded_correction_revision_stability` version `candidate-1`. Its source fixture,
prior Brief, affected claim, replacement claim, stable claim set, reviewer, formula, and policy
digest are inspectable. The score is the unaffected-claim preservation rate, but only when all four
gates pass:

1. the exact replacement claim is present and the stale affected claim is absent;
2. the correction citation and exact correction/prior lineage are visible;
3. original and correction source coverage is complete; and
4. the prior and revised claim counts match.

If any gate fails, the score is `0`. Treatment scores `1.0`; the unrelated-drift control scores
`0.0`. Core and Intelligence see only exact Brief/result coordinates and a scalar outcome. FCC,
Federal Register, correction, affected/unaffected claim policy, paraphrase classification, and
review vocabulary remain in World.

## Exact acceptance

P2C8 must:

1. rerun P2C2 through P2C7 and preserve every prior immutable record, evaluation, proposal, and
   reviewed disposition;
2. append an exact prior `BriefV1Alpha1` citing the original Observation;
3. append treatment and control `BriefV1Alpha1` revisions with exact prior, original, and
   correction lineage;
4. prove both revisions remove the stale affected claim, add the same exact replacement claim,
   cite the same original/correction sources, and retain the same claim count;
5. prove treatment preserves both stable claim identities while control preserves neither and
   introduces exactly two unrelated content identities;
6. create two distinct reviewed treatment/control Action pairs under matched task conditions;
7. append four independently authenticated review records and four Core Outcomes naming those
   exact review records;
8. classify the bounded two-pair difference `useful`, emit only a non-effective `promote`
   proposal, and perform no proposal application;
9. replay without reauthorization and reproduce Brief identities, claim sets, classification, and
   substantive metrics across fresh hosts; and
10. reject duplicate claims, incomplete stable-claim partitions, missing correction visibility
    paired with a positive score, and caller-invented aggregate scores.

## Negative and failure controls

The unrelated-drift Brief is the primary product negative control. It has the same exact prior,
source Observations, citations, claim count, replacement claim, reviewed workflow, and matched
conditions as treatment. Only the two unaffected claims are paraphrased, changing their content
identities. This is a frozen fixture classification, not a general semantic-equivalence engine.

`BriefV1Alpha1` rejects duplicate claim identities. The review contract requires the preserved and
drifted sets to partition the expected stable claims exactly and derives its rate and score from
that partition plus the four gates. Exact review loading rejects unavailable, changed, relabelled,
cross-product, or incomplete Brief material. Stacked Core tests remain authoritative for missing
attribution/result provenance, condition mismatch, cutoff leakage, unavailable Outcomes,
duplicate/replayed evidence, interruption, restart, and denied authority.

## Files and rollback

This packet owns:

- `scripts/p2c8_correction_revision_stability_outcome.py`;
- `domain_packs/tests/test_p2c8_correction_revision_stability_outcome.py`;
- the additive P2C7 state handoff;
- this work packet, its audit, and restrained README/roadmap references.

It changes no shipped Domain Pack, connector, fixture source policy, package version, dependency
range, lockfile, release record, Core contract, or public artifact. Rollback removes the P2C8
harness, tests, state handoff, and candidate documentation. Brief, review, Outcome, evaluation,
and proposal records already persisted by a host remain immutable history.

## Non-claims and next packet

This is one recorded correction pair and two replicated matched workflows. It establishes exact
claim-identity preservation and criterion sensitivity under one frozen World rule. It does not
establish live revision, general semantic equivalence, a population stability rate, calibration,
source independence, general Brief quality, causal benefit, legal truth, or human usefulness.

The next bounded outcome packet should freeze calibration under a declared forecast/observed-result
rule or repeat the unchanged correction/revision contracts over a materially different source.
Independent Market reproduction, public Core artifacts, combined-main review/CI, compatibility,
security and release gates, opt-in live transport, issue #49 disposition, repository-wide hygiene,
and any separately authorized proposal application remain separate work.
