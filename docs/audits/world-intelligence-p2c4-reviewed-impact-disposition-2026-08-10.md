# World Intelligence P2C4 reviewed impact disposition audit — 2026-08-10

Status: **stacked candidate evidence only; not a release or applied governance change**

## Source identity

- World base: P2C3 commit `c712b2ca9bf67381a9862f07eb780f5c13e2f379`
- World branch: `codex/measured-impact-world-disposition`
- Core base: measured-impact kickoff commit `9078018a5fd3c310011b6c9efbfe5255e0e36887`
- Core dependency: stacked `codex/measured-impact-disposition` candidate
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

One candidate run retained the P2C3 `useful` classification and non-effective `promote` proposal,
then recorded a separately authorized Core Decision whose subject was that exact proposal:

```text
evaluation: impact_evaluation:8c133e576587fae76927828ab882210d
evaluation material: sha256:68808bb0f0d462035fb297e0c14825910a5fe4e1510fd8994cc20d1a704d4f59
proposal: impact_governance_proposal:c8021b5d1798ef9c61ab90abacccbddf
proposal material: sha256:7eddbeb2485db19ac19ee6c5540925bd7a6dc89d3b50ec521a3ed7226785730d
decision: decision:5e0ca6230ab92ed3702a5363264ff098
decision material: sha256:ef4027ba44b9a25569b0071dd27a22fc81256c44787c7cf8040c304be2e5a840
measured classification: useful
proposal action: promote
reviewer disposition: reject
Decision action disposition: no_action
proposal applied: false
effective governed state changed: false
historical replay: true
replay reauthorization: false
```

The rationale rejected broader promotion because the exact criterion measured only structural
coverage of two required admitted Observation identities in reviewed exports. The Decision did not
reclassify the evaluation or replace the proposal.

## Verification

Stacked source-checkout verification with the Core disposition candidate and the separately
packaged reference action adapter:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py -q --tb=short
4 passed in 0.88s

ruff check scripts/p2c3_measured_feedback.py \
  scripts/p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py
PASS

ruff format --check scripts/p2c3_measured_feedback.py \
  scripts/p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py
PASS

python -B -m pytest -q --tb=short
87 passed in 17.00s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.26s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.04s

# Locked environment with public ace-core==0.5.0 and no candidate source checkout.
python -B -m pytest -q --tb=short -rs
82 passed, 5 skipped in 15.38s

uv build --out-dir <temporary-directory>
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The five locked-environment skips are explicit boundaries: one P2C2 test requires the separately
packaged reference adapter, two P2C3 tests require the unreleased measured-impact contract, and two
P2C4 tests require the stacked proposal-disposition contract. The public 0.5 dependency range and
0.9.0 artifact therefore remain coherent. The built wheel contains only inert Domain Pack data and
no candidate script, test, adapter, or audit Python.

## Claim boundary

The named World principal and governed role/grant prove that the fixture followed explicit product
review policy; this neutral contract does not independently prove biological personhood. Recorded
official source responses preserve exact public provenance but do not prove a live network request
or test-time freshness. The useful result remains a deterministic two-pair structural rule, not a
causal estimate, population result, correctness score, or human-benefit finding.

P2C4 proves that ACE can retain a measured result, retain its proposed governance action, and
record a contrary authorized disposition without silently applying or rewriting either. It does
not publish 0.6, pass SI4, update the Domain Pack release, or create effective state.

## Remaining work

The next measurement packet needs independently reviewed product-quality evidence such as citation
correctness, contradiction coverage, correction quality, detection delay, or false-alert rate.
Market reproduction, public Core artifacts, compatibility/security/release gates, opt-in live
transport, and any separately authorized proposal application remain outside this candidate.
