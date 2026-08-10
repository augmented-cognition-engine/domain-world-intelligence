# World Intelligence P2C5 citation-correctness outcome audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, or applied governance change**

## Source identity

- World base: P2C4 commit `189c81be1812ee32ffc28148fb63539c66417661`
- World branch: `codex/world-citation-correctness`
- Core base: measured-impact disposition commit
  `3c920bb5c411bd9d91a5e2a6c96d4014e9b66763`
- Core dependency: stacked `codex/measured-impact-observed-result` candidate
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

One source-checkout run recorded two independent treatment reviews and two independent control
reviews under product policy
`sha256:ab9b609d9bba9edc4163cdccdbe8761d8494b2bf52789a92f3124b5d3324750c`:

```text
treatment review 1: citation_correctness_review:27b875cf41e4f417cec5715aebeca73b
treatment review 2: citation_correctness_review:d4c7f54c69289eb258c84d65ad7c996b
control review 1: citation_correctness_review:b1c980ee2df061ab00caa6e3a46d6e7c
control review 2: citation_correctness_review:a2122102390c938dd3edf5104f63f415
treatment citation coverage: 1.0, 1.0
control citation coverage: 1.0, 1.0
treatment correctness: 1.0, 1.0
control correctness: 0.0, 0.0
matched pairs: 2
mean effect: 1.0
classification: useful
proposal action: promote
proposal live effect: false
historical replay: true
replay reauthorization: false
```

The exact evaluation was
`impact_evaluation:eef78b8febd33d4b6121d6f8ce6e1335` with material
`sha256:eef78b8febd33d4b6121d6f8ce6e13354dcb09ef743c5de61940021473595d3a`.
The exact non-effective proposal was
`impact_governance_proposal:d928a69adc1984ff89b1225ed87d93fa` with material
`sha256:d928a69adc1984ff89b1225ed87d93fa0881c3e6f981233d08d9e7756a6c8b80`.

The negative control preserved both exact citation identities but changed the cited statement from
the admitted publication dates to `2026-15932 published 2026-08-07` and `2026-16197 published
2026-08-06`. It therefore falsifies the structural-coverage proxy without requiring a different
source set.

## Verification

Stacked source-checkout verification with the Core observed-result candidate and separately
packaged reference action adapter:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py -q --tb=short
6 passed in 1.16s

ruff check scripts/p2c3_measured_feedback.py \
  scripts/p2c4_reviewed_impact_disposition.py \
  scripts/p2c5_citation_correctness_outcome.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py
PASS

ruff format --check <the four changed Python files above>
PASS

python -B -m pytest -q --tb=short
89 passed in 15.40s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.23s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.04s

# Isolated environment with the built World wheel, public ace-core==0.5.0,
# and the separately installed Federal Register source adapter; no Core checkout.
python -B -m pytest -q --tb=short -rs
82 passed, 7 skipped in 15.04s

ruff check .
PASS

uv build --out-dir <temporary-directory>
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The seven isolated-environment skips are explicit candidate boundaries: one P2C2 test requires
the separately packaged Core reference action adapter, and two tests each require the unreleased
P2C3, P2C4, and P2C5 Core candidates. The released dependency range and 0.9.0 artifact remain
coherent. Wheel inspection contains only inert Domain Pack JSON and distribution metadata; no
candidate script, test, adapter, or audit Python is shipped.

Repository-wide `ruff format --check .` reports 19 pre-existing files outside this packet that do
not match the Core candidate environment's formatter version. The four changed Python files pass
the scoped formatting gate and the complete repository passes `ruff check .`; this packet does not
rewrite unrelated World history.

## Claim boundary

The World reviewer exact-loads both admitted Observation envelopes and derives the expected
document/date statement from their canonical payloads. Its exact result makes reviewer, source
Observations, policy, claim, citations, verdict, score, time, and limitations inspectable. The Core
Outcome points to that exact result and the evaluator refuses missing or future result provenance
when the criterion requires it.

This demonstrates deterministic product-policy sensitivity over two recorded official public
records. It does not prove a live request, current freshness, legal truth, reviewer infallibility,
source independence, correction handling, population performance, general Brief quality, causal
impact, or human benefit. The resulting proposal remains non-effective and unapplied.

## Remaining work

Contradiction/correction coverage, detection delay, false-alert rate, revision stability, a
materially different Market journey, public artifacts, compatibility/security/release checks,
opt-in live transport, and any explicit proposal application remain future bounded packets.
