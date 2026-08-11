# World Intelligence P2C9 forecast-calibration outcome work packet (v1)

**Status:** stacked source-checkout candidate; this packet does not release World Intelligence,
apply a governance proposal, close ACE Core issue #38, pass SI4, or complete ACE 0.6.0.

**Frozen:** 2026-08-10 from World P2C8 commit
`129767d27d4af22dba292deb9e691375a0695bb8`, stacked on the Core exact observed-result
provenance candidate `433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Prove that a World-owned probabilistic forecast can be issued from exact admitted evidence before
an exact result is available, resolved under an inspectable scoring rule, and compared through the
unchanged domain-neutral measured-impact contract:

```text
original Observation -> treatment probability / probability control
  -> Decision -> reviewed Action
  -> later correction Observation -> exact resolution review
  -> observed Outcome -> useful / harmful / unproven evaluation -> proposal only
```

The real source pair remains FCC Federal Register document `2020-28779` and its explicit correction
`2021-10670`. P2C9 intercepts the recorded replay after the original Observation is admitted but
before the correction Observation is appended. It records two exact World forecast artifacts and
completes their reviewed Actions first. Only then does the existing P2C7/P2C8 journey admit and use
the correction result.

## Frozen forecast and scoring policy

Both forecasts use the same exact original Observation, target event definition, resolution rule,
window, reviewed workflow, later correction result, and matched conditions. The only deliberate
difference is probability: treatment declares `0.75`; control declares `0.25`. The binary event is
`1.0` only when the later exact admitted source explicitly names the basis document as corrected.

World owns `world_recorded_binary_forecast_brier_quality` version `candidate-1`. For each exact
forecast/result pair it derives:

```text
brier_loss = (forecast_probability - binary_event_outcome) ** 2
brier_quality = 1 - brier_loss
```

The observed event is true, so treatment quality is `0.9375`, control quality is `0.4375`, and the
paired effect is `0.5` across two replicated reviewed workflows. The product criterion requires two
matched pairs and a useful threshold of `0.5`.

This is one single-event Brier contribution. It exercises exact probability/result provenance and
score sensitivity; it is not an empirical calibration curve, population reliability estimate, or
evidence that ACE generated a skillful forecast. The two probabilities are declared fixture inputs,
not model outputs.

## Exact acceptance

P2C9 must:

1. rerun P2C2 through P2C8 and preserve every prior immutable result and proposal;
2. append treatment and control forecast records from the exact original Observation without any
   correction identity or correction material in either forecast;
3. complete two reviewed treatment Actions and two reviewed control Actions before the correction
   result becomes available;
4. admit the existing exact correction Observation only after those forecast Actions;
5. exact-load the forecast, basis Observation, and correction Observation and derive the binary
   outcome from the correction's explicit link to the original document;
6. append four independently authenticated resolution reviews and four Core Outcomes naming those
   exact reviews as their observed results;
7. derive, never accept, the Brier loss and quality score from each exact probability/outcome pair;
8. classify the two-pair difference `useful` and emit only a non-effective, non-selectable
   `promote` proposal requiring separate human review;
9. replay without reauthorization and reproduce the target definition, probabilities, event
   outcome, scores, classification, and proposal semantics across fresh hosts; and
10. reject future/unavailable basis material, result coordinates injected into forecast material,
    missing withholding, out-of-range probabilities, changed event linkage, and invented scores.

## Negative and leakage controls

The forecast contract has no observed-result field. Its only exact evidence coordinates are the
basis Observations, all of which must be available by forecast issuance. Extra result material is
forbidden. The resolution review requires the result reference to become available after the exact
forecast reference and within the declared window. The harness additionally proves every reviewed
forecast Action completed before the correction record became available.

The control is not a source-only or no-action baseline. It is an exact probability control under
the same event and workflow. This isolates sensitivity to declared probability while holding result
identity, source linkage, action topology, review policy, and conditions constant. Stacked Core
tests remain authoritative for missing attribution, condition mismatch, cutoff leakage, unavailable
Outcomes, duplicate/replayed evidence, interruption, restart, and denied authority.

## Ownership boundary

World owns the public-event target, forecast vocabulary, probability fixtures, binary resolution
rule, Brier-quality mapping, source-policy limits, tests, and evidence. Core owns immutable records,
provenance, Decisions, reviewed Actions, Outcomes, authority, replay, and append-only history.
Intelligence owns domain-neutral conditions, matched evaluation, uncertainty, classification, and
proposal contracts. No FCC, Federal Register, forecast-policy, or Brier noun moves into Core or
Intelligence.

## Files and rollback

This packet owns:

- `scripts/p2c9_forecast_calibration_outcome.py`;
- `domain_packs/tests/test_p2c9_forecast_calibration_outcome.py`;
- the additive P2C7/P2C8 pre-correction state handoff;
- this work packet, its audit, and restrained README/roadmap references.

It changes no shipped Domain Pack, connector, fixture source policy, package version, dependency
range, lockfile, release record, Core contract, or public artifact. Rollback removes the P2C9
harness, tests, handoff, and candidate documentation. Forecast, review, Outcome, evaluation, and
proposal records already persisted by a host remain immutable history.

## Non-claims and next packet

This packet does not establish a historically contemporaneous forecast, probability generation by
ACE, model skill, population calibration, live monitoring, network freshness, source independence,
causal benefit, legal truth, general Brief quality, or human usefulness. It does not apply the
proposal or grant authority to a Domain Pack.

The next bounded packet should repeat a correction/outcome measure over a materially different
source or reproduce the unchanged measured-impact contracts independently in Market Intelligence.
Public Core artifacts, combined-main review/CI, compatibility, security and release gates, opt-in
live transport, repository-wide hygiene, and any separately authorized proposal application remain
separate work. Core issue #49 F1, F3, and F5 still require explicit 0.6 release-owner disposition;
this packet does not implement or re-date them.
