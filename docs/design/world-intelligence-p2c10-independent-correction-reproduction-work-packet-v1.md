# World Intelligence P2C10 independent correction reproduction work packet (v1)

**Status:** stacked source-checkout candidate; this packet does not release World Intelligence,
apply a governance proposal, close ACE Core issue #38, pass SI4, or complete ACE 0.6.0.

**Frozen:** 2026-08-10 from World P2C9 commit
`53feadb40fcc93d23f326b16979ed6640471c4cf`, stacked on the Core exact observed-result
provenance candidate `433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Falsify source-family coupling by reproducing the measured correction journey over a materially
different real publisher and source policy while leaving the shared Core + Intelligence contracts
unchanged:

```text
BLS release Observation + later BLS erratum Observation
  -> treatment corrected artifact / stale-form control
  -> Decision -> reviewed Action -> independent review -> exact Outcome
  -> useful / harmful / unproven evaluation -> proposal only
```

The source pair is the BLS Job Openings and Labor Turnover release `USDL-25-1087` and its public
erratum. The [archived release](https://www.bls.gov/news.release/archives/jolts_07012025.htm) now
contains the corrected `−39,000` form. The [BLS errata page](https://www.bls.gov/errata/) states
that the July 1, 2025 sentence required a missing minus sign and that corrections were made July 2.
The fixture therefore labels the pre-correction form as derived from that explicit erratum; it does
not pretend the current archive still exposes the superseded bytes.

## Frozen product policy and matched control

World owns `world_independent_official_correction_statement_quality` version `candidate-1`. A
review scores `1.0` only when all of the following are exact and inspectable:

1. both the original-release and correction Observations are present;
2. the correction names the exact release it corrects;
3. the original immutable record remains loadable and unchanged;
4. the rendered statement equals the public corrected statement; and
5. the reported pre-correction form is absent.

Otherwise the score is `0.0`. Treatment and control share both source references, correction
linkage, policy digest, two reviewed Action workflows, observation window, and matched conditions.
Treatment renders `The number of job openings decreased in federal government (−39,000).`; control
retains the missing-sign form `(39,000)`. Source coverage and action volume therefore cannot explain
the score difference.

The criterion requires two matched pairs and an effect of `1.0`. Intelligence derives useful,
harmful, or unproven under that frozen rule. Core appends exact reviews, Outcomes, evaluation, and
proposal history. A useful result maps only to a non-effective, non-selectable `promote` proposal
requiring separate human review.

## Exact acceptance

P2C10 must:

1. rerun P2C2 through P2C9 and preserve all prior immutable results and proposals;
2. admit the recorded BLS release and erratum as distinct exact Observations without network use;
3. retain BLS source vocabulary and historical-original derivation policy only in World;
4. append treatment and stale-form control artifacts that name the same exact source pair and
   correction relation;
5. complete two reviewed treatment Actions and two reviewed control Actions;
6. exact-load each artifact and both source Observations before deriving the product score;
7. append four authenticated reviews and four Core Outcomes naming those reviews as observed
   results;
8. classify `1.0` versus `0.0` over two pairs as useful and emit proposal-only `promote`;
9. replay without reauthorization and reproduce the fixture digest, scores, classification, and
   proposal semantics across fresh hosts; and
10. reject drifted source linkage, duplicate source identity, changed statement forms, invented
    scores, and fixture-policy drift.

Stacked Core tests remain authoritative for missing attribution, condition mismatch, cutoff
leakage, unavailable Outcomes, duplicate/replayed evidence, interruption, restart, and denied
authority. This packet exercises those unchanged contracts through a second real source family
rather than duplicating their lower-level tests in World.

## Ownership boundary

World owns BLS vocabulary, source URLs, the historical-original derivation disclosure, correction
statement policy, fixture, matched control, review contract, and product evidence. Core owns durable
identities, append-only records, provenance, Decisions, reviewed Actions, Outcomes, authority, and
replay. Intelligence owns domain-neutral conditions, matched evaluation, uncertainty,
classification, and proposal contracts. No BLS, JOLTS, errata, or minus-sign noun moves into Core or
Intelligence.

The installable Domain Pack remains inert JSON and unchanged. The Federal Register connector is
unchanged and is not used to fetch BLS. The fixture is recorded, hermetic, and network-free.

## Files, rollback, and deletion criteria

This packet owns:

- `domain_packs/tests/fixtures/p2c10_bls_correction_pair.json`;
- `scripts/p2c10_independent_correction_reproduction.py`;
- `domain_packs/tests/test_p2c10_independent_correction_reproduction.py`;
- the additive P2C9 state handoff; and
- this work packet, its audit, and restrained README/roadmap references.

It changes no shipped Domain Pack, connector, package version, dependency range, lockfile, release
record, Core contract, or public artifact. Rollback removes the harness, tests, handoff, fixture,
and candidate documentation. Records already persisted by a host remain immutable history.

Delete or replace this fixture only if BLS removes the public correction evidence, the exact URLs
cannot be independently verified, or a stronger redistributable snapshot supersedes it. Such a
change requires a new fixture identity and cannot rewrite prior evidence.

## Non-claims and next packet

This packet does not establish live monitoring, network freshness, the statistical validity of the
JOLTS estimate, general correction quality, population performance, source independence beyond the
two exercised families, causality, general Brief quality, or human benefit. It does not apply a
proposal or grant authority to a Domain Pack.

The next bounded falsification packet is an independent Market Intelligence reproduction of the
same public Core + Intelligence contracts. Combined-main review/CI, public Core artifacts,
compatibility and security checks, repository-wide hygiene, and separately reviewed opt-in live
transport remain release work. Core issue #49 F1, F3, and F5 still require explicit 0.6
release-owner disposition; this packet does not implement, defer, or re-date them.
