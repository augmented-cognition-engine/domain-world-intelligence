# World Intelligence P2C5 citation-correctness outcome work packet (v1)

**Status:** stacked source-checkout candidate; this packet does not release World Intelligence,
apply a governance proposal, close ACE Core issue #38, pass SI4, or complete ACE 0.6.0.

**Frozen:** 2026-08-10 from World P2C4 commit
`189c81be1812ee32ffc28148fb63539c66417661`, stacked on the Core exact observed-result
provenance candidate.

## Objective

Replace P2C3's structural coverage-only outcome with one independently recorded product-quality
result while preserving the full governed journey:

```text
Observation -> Shift -> Signal -> Brief -> Decision -> reviewed Action
            -> exact independent citation review -> observed Outcome
            -> useful / harmful / unproven evaluation -> proposal only
```

The packet must distinguish presence from correctness. Its negative control retains the exact two
citation identities used by the Brief but swaps the two official publication dates in the cited
claim. Treatment and control therefore both have `1.0` citation coverage while correctness is
`1.0` for the admitted Brief and `0.0` for the semantic-corruption control.

## Product-owned review policy

World owns `world_official_record_citation_correctness` version `candidate-1`. The frozen rule
reviews cited claims only, requires the exact two Brief citation identities, exact-loads the two
admitted Observation envelopes, derives the expected document/date statement from their canonical
payloads, and compares the cited statement to those exact recorded facts. Score is supported cited
claims divided by reviewed cited claims.

The exact review record names:

- the reviewed Brief or control immutable reference;
- the authenticated reviewer `principal:world-citation-correctness-reviewer`;
- the policy identity, version, and material digest;
- the two exact source Observation references;
- each claim identity, statement, exact citation set, verdict, and rationale;
- coverage, correctness score, limitations, review time, and derived review identity/digest.

Core and Intelligence see only the result's generic immutable reference from the Outcome measures.
Federal Register, citation, reviewer, and source-policy nouns remain in World.

## Exact acceptance

P2C5 must:

1. rerun P2C2 through P2C4 and preserve the earlier structural result and reject/no-action
   disposition as immutable history;
2. append one exact citation-preserving corrupted control artifact;
3. create two distinct reviewed treatment/control Action pairs under matched task conditions;
4. append four independently authenticated review records over the exact subjects and source
   Observations;
5. record four Core Outcomes whose measures name the exact review records that produced their
   scalar scores;
6. require exact observed-result provenance under a frozen correctness criterion;
7. show treatment/control coverage `1.0/1.0` but correctness `1.0/0.0` in both pairs;
8. classify the bounded result `useful`, emit only a non-effective `promote` proposal, and perform
   no proposal application;
9. replay the evaluation without reauthorization; and
10. retain explicit non-claims for network freshness, causality, general Brief quality, human
    benefit, and autonomous publication.

## Negative and failure controls

The citation-preserving date swap is the primary product negative control: an identifier/string
coverage scorer cannot distinguish it, while the frozen correctness review must. Core's stacked
tests separately require missing observed-result provenance to become unproven, reject cross-
product result coordinates, and exclude post-cutoff result material without loading its payload.
Earlier missing attribution, condition mismatch, Outcome unavailability, duplicate/replay,
interruption, restart, and denied-authority controls remain required.

## Files and rollback

This packet owns:

- `scripts/p2c5_citation_correctness_outcome.py`;
- `domain_packs/tests/test_p2c5_citation_correctness_outcome.py`;
- additive P2C3/P2C4 acceptance-state handoffs;
- this work packet, its audit, and restrained README/roadmap references.

It changes no shipped Domain Pack, connector, package version, dependency range, lockfile, release
record, or public artifact. Rollback removes the harness, tests, state handoffs, and candidate
documentation. Product review and Outcome records already persisted by a host remain immutable
history.

## Non-claims and next packet

The result covers one cited claim, two recorded official records, two matched pairs, and one exact
product rule. It does not validate inference claims, source independence, corrections, live
network freshness, human usefulness, general Brief quality, or causal benefit. The synthetic
control establishes criterion sensitivity, not a population estimate.

The next bounded outcome packet should measure contradiction/correction coverage or detection
delay over additional public records. Independent Market reproduction, public Core artifacts,
compatibility/security/release gates, opt-in live transport, and any separately authorized proposal
application remain separate work.
