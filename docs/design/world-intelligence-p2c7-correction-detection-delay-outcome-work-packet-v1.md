# World Intelligence P2C7 correction-detection-delay outcome work packet (v1)

**Status:** stacked source-checkout candidate; this packet does not release World Intelligence,
apply a governance proposal, close ACE Core issue #38, pass SI4, or complete ACE 0.6.0.

**Frozen:** 2026-08-10 from World P2C6 commit
`590cf9bb640681ab5095d3abd451092f72f8d929`, stacked on the Core exact observed-result
provenance candidate `433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Measure whether one exact World correction-handling artifact links an official correction to the
record it corrects, preserves the prior immutable record, and detects the correction within an
explicit product-owned replay target. The packet preserves the governed journey:

```text
recorded original Observation + recorded correction Observation
  -> correction-handling artifact -> Decision -> reviewed Action
  -> exact independent correction review -> observed Outcome
  -> useful / harmful / unproven evaluation -> proposal only
```

The frozen pair is FCC Federal Register document `2020-28779`, published 2020-12-29 at
`85 FR 85524`, and its explicit correction `2021-10670`, published 2021-05-20 at `86 FR 27275`.
The correction names the earlier document and changes the instruction on page 85530: remove
instruction 20a and redesignate 20b and 20c as 20a and 20b. FederalRegister.gov is retained as a
display reference and the corresponding govinfo.gov PDFs as official-format verification
references. The fixture does not claim to be the official legal edition or determine legal truth.

## Product-owned review policy

World owns `world_recorded_official_correction_detection` version `candidate-1`. Its fixture,
exact original/correction Observation references, target, rule, reviewer, and policy digest are
inspectable. The recorded-replay availability instant is frozen at `2021-05-20T00:00:00Z`; this is
a test coordinate, not a measured network-arrival timestamp. The product target is 600 seconds.

Treatment detects at `00:05:00Z` and the delayed control at `06:00:00Z`. Both carry the same exact
correction relationship and instruction, both preserve the prior Observation, and both traverse
matched reviewed export workflows. The score is:

```text
1 if linkage, instruction, and prior-record preservation are correct and delay <= 600 seconds
0 otherwise
```

The exact review record names:

- the reviewed correction-handling artifact and exact original/correction Observations;
- authenticated reviewer `principal:world-correction-delay-reviewer`;
- product policy identity, version, digest, and source-fixture digest;
- exact linkage, corrected instruction, prior-record preservation, availability, detection time,
  delay, target disposition, score, limitations, review time, and derived identity/digest.

Core and Intelligence see only the generic exact observed-result coordinate, latency, and scalar
outcome. FCC, Federal Register, correction, document, page, instruction, replay policy, and review
vocabulary remain in World.

## Exact acceptance

P2C7 must:

1. rerun P2C2 through P2C6 and preserve all prior evaluations, proposals, and reviewed
   dispositions as immutable history;
2. admit the exact original and correction as distinct PREPARED recorded-replay Observations with
   exact acquisition/source digests and explicit source-policy limits;
3. append treatment and delayed-control correction artifacts that name both exact source records,
   the correction relationship and instruction, and preserve rather than replace the original;
4. create two distinct reviewed treatment/control Action pairs under matched task conditions;
5. append four independently authenticated review records and four Core Outcomes naming those
   exact review records;
6. show exact linkage, instruction, and prior-record preservation for both variants, treatment
   delay `300` seconds and score `1.0`, and control delay `21600` seconds and score `0.0`;
7. classify the bounded two-pair difference `useful`, emit only a non-effective `promote`
   proposal, and perform no proposal application;
8. replay the evaluation without reauthorization and reproduce its classification and substantive
   metrics across fresh hosts;
9. reject pre-availability detection and caller-invented review scores; and
10. retain explicit non-claims for live monitoring, network-arrival delay, population detection
    performance, legal truth, causality, general Brief quality, human benefit, and autonomous
    publication.

## Negative and failure controls

The delayed-control artifact is the primary product negative control: it has the same exact source
pair, correction semantics, reviewed workflow, and matched conditions as treatment, but detects
the correction after the declared target. A detection time before the correction's frozen replay
availability and a score inconsistent with the exact rule fail model validation. Exact review
loading rejects unavailable, changed, relabelled, cross-product, or incomplete artifact/source
material. The stacked Core tests remain authoritative for missing attribution/result provenance,
condition mismatch, cutoff leakage, unavailable Outcomes, duplicate/replayed evidence,
interruption, restart, and denied authority.

## Files and rollback

This packet owns:

- `domain_packs/tests/fixtures/p2c7_fcc_correction_pair.json`;
- `scripts/p2c7_correction_detection_delay_outcome.py`;
- `domain_packs/tests/test_p2c7_correction_detection_delay_outcome.py`;
- the additive P2C6 acceptance-state handoff;
- this work packet, its audit, and restrained README/roadmap references.

It changes no shipped Domain Pack, connector, package version, dependency range, lockfile, release
record, Core contract, or public artifact. Rollback removes the P2C7 fixture, harness, tests, state
handoff, and candidate documentation. Product correction, review, Outcome, evaluation, and
proposal records already persisted by a host remain immutable history.

## Non-claims and next packet

This is one recorded official correction pair replayed through two replicated matched workflows.
The availability instant and treatment/control detection times are frozen test coordinates; the
test suite performs no network access. It establishes exact linkage, append-only correction
visibility, criterion sensitivity, latency provenance, and proposal-only governance under one
product rule. It does not establish live correction discovery, actual network-arrival latency, a
population delay distribution, source independence, calibration, revision stability, general
Brief quality, causal benefit, legal truth, or human usefulness.

The next bounded outcome packet should freeze calibration or revision stability, or exercise the
same correction contract over an additional source/event without changing Core + Intelligence.
Independent Market reproduction, public Core artifacts, combined-main review/CI, compatibility,
security and release gates, opt-in live transport, issue #49 disposition, and any separately
authorized proposal application remain separate work.
