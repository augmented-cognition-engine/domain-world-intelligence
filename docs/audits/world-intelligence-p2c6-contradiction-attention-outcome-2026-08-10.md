# World Intelligence P2C6 contradiction-attention outcome audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, live-conflict proof, or applied
governance change**

## Source identity

- World base: P2C5 commit `e43fc5e88ba1d79e01d1d9bddf2c1c0ae052b9ac`
- World branch: `codex/world-contradiction-recall`
- Core dependency: exact observed-result candidate commit
  `433e3d16c5458c975557dcd1552824fb959d4d12`
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

One source-checkout run recorded two treatment reviews and two inverted-control reviews under
product policy
`sha256:94ad25bb2d3e2c153365659cf90c909fdb02ead9a188bff71d450dffe4a4832f`:

```text
treatment artifact: contradiction_attention_artifact:5650baf1ebe06831aa476390c243502e
control artifact: contradiction_attention_artifact:8a941d93bef7413c57068380b75019bb
treatment review 1: contradiction_attention_review:55c06985ebb527a7b113014069ee3249
treatment review 2: contradiction_attention_review:2266b1f5af3392dcd79b2b324ea7a480
control review 1: contradiction_attention_review:68e6426d78aa72ffb028d4285a02915c
control review 2: contradiction_attention_review:5e4ea73f1c08bee985aec0135ba80d63
treatment alert volume: 1, 1
control alert volume: 1, 1
treatment contradiction recall: 1.0, 1.0
control contradiction recall: 0.0, 0.0
treatment false-alert rate: 0.0, 0.0
control false-alert rate: 1.0, 1.0
treatment valid silence count: 1, 1
control valid silence count: 0, 0
treatment quality score: 1.0, 1.0
control quality score: 0.0, 0.0
matched pairs: 2
mean effect: 1.0
classification: useful
proposal action: promote
proposal live effect: false
historical replay: true
replay reauthorization: false
```

The exact evaluation was `impact_evaluation:c88c9ae913307d93d46650339c103624` with material
`sha256:c88c9ae913307d93d46650339c103624311bf856e4e4b9fee0572f6f2fbfd927`.
The exact non-effective proposal was
`impact_governance_proposal:6a42a1a57040983e8f323176ca2f09f8` with material
`sha256:6a42a1a57040983e8f323176ca2f09f8a441715795d1c9618db14888742a50e5`.

The frozen candidate set was:

```text
valid comparator:
  contradiction_candidate:00890df1781c09df7c01b67cef19252b
  2026-15932 published 2026-08-06; 2026-16197 published 2026-08-07

contradiction:
  contradiction_candidate:1e1388a5652933a8b18f42d704e684d1
  2026-15932 published 2026-08-07; 2026-16197 published 2026-08-06
```

Treatment alerts only on the contradiction. Control reverses both decisions. Equal alert volume
therefore makes raw ingestion or alert count incapable of explaining the measured difference, and
the treatment's true negative makes silence an explicit valid result.

## Verification

The exact locked World environment (`uv.lock`, Ruff `0.16.2`) plus the stacked Core candidate and
separately packaged reference action adapter produced:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py \
  domain_packs/tests/test_p2c6_contradiction_attention_outcome.py -q --tb=short
10 passed in 2.62s

python -B -m pytest -q --tb=short
93 passed in 17.05s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.31s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.05s

# Installed public ace-core==0.5.0; no Core source checkout or reference action adapter.
python -B -m pytest -q --tb=short -rs
82 passed, 11 skipped in 14.66s

ruff check --no-cache <P2C5/P2C6 changed Python files>
PASS

ruff format --check --no-cache <P2C5/P2C6 changed Python files>
4 files already formatted

uv build --out-dir <temporary-directory>
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The eleven public-Core skips are explicit boundaries: one P2C2 test requires the separately
packaged Core reference action adapter; P2C3–P2C6 require unreleased stacked Core candidate
contracts. The wheel contains 45 inert Domain Pack JSON/metadata files, no Python or entry points,
and retains `ace-core>=0.5.0,<0.6`.

Repository-wide Ruff is an inherited release-hygiene blocker, not made green by this packet. Under
the exact locked Ruff, the P2C5 parent reports 16 lint findings and this candidate reports 15 after
the touched P2C5 import block is normalized; no P2C6 file adds a finding. Broad format checking also
reports existing drift outside the scoped Python files. P2C6 does not rewrite that unrelated
history, but release closeout must reconcile the repository-wide gate before publication.

## Claim boundary

The World reviewer exact-loads the treatment or control attention artifact and verifies its exact
Brief, Observation, candidate, decision, and policy material. It records every confusion class and
derives recall, false-alert rate, valid silence, alert volume, and quality score from those exact
assessments. The Core Outcome points to that exact review record. Replay returns historical
evaluation material without new authority, and fresh hosts reproduce the classification and
metrics.

This demonstrates one product-policy challenge over two recorded official public records. The
contradiction is a deterministic semantic negative control, not evidence that the public sources
contradicted each other or that ACE discovered a live conflict. Two candidates do not establish a
population false-alert rate, calibration, correction quality, detection delay, source
independence, general Brief quality, causality, or human benefit. The proposal remains
non-effective and unapplied.

## Remaining work

Detection delay, actual correction handling, calibration, revision stability, a materially
different Market journey, combined-main review/CI, public artifacts, security/release checks, and
opt-in live transport remain future bounded work. Core issue #49 F1, F3, and F5 still require
explicit 0.6 release-owner disposition; this World packet neither implements nor re-dates them.
