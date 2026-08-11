# World Intelligence P2C8 correction-revision-stability outcome audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, live-revision proof, or applied
governance change**

## Source identity

- World base: P2C7 commit `216a37a1fdcb4f0baf9ac148ab9e525559141c22`
- World branch: `codex/world-correction-revision-stability`
- Core dependency: exact observed-result candidate commit
  `433e3d16c5458c975557dcd1552824fb959d4d12`
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

The source fixture remains
`sha256:2b81d3950cbfd127408eec227ec5cd249677a189120d6ca7b603d85d01074543`,
with original Observation `observation:f1768d6f4191a86e245846a9a1e33768` and correction
Observation `observation:fced5d3bbc3802c0285021142b332e29`.

One source-checkout run recorded actual prior, treatment, and control `BriefV1Alpha1` resources:

```text
prior Brief:
  brief:b0911c340cc4a39cd7a908f7884d71bd
  sha256:b0911c340cc4a39cd7a908f7884d71bd6348b6202b9d8f521d4339e708273250
treatment Brief:
  brief:d1dafb5352ebfd99bc35c1044bc627ac
  sha256:d1dafb5352ebfd99bc35c1044bc627ac3e30846b8092561ec28bfca4ae4921c3
control Brief:
  brief:f86f101516ea496108557498e5950672
  sha256:f86f101516ea496108557498e5950672660ead2c1a01949a46776250cbf3f075

affected prior claim:
  grounded_claim:fddf5435d53f01312739f8f8ff355eb6
replacement correction claim:
  grounded_claim:ff1683b3155f734bcf942c0cab9ed7e4
stable claims:
  grounded_claim:7c6c683cae2dabeb050d5542405e992a
  grounded_claim:8fab51672b58cdd0c45734ea637d7aaf
control-only paraphrase identities:
  grounded_claim:82b05b5ec627f03a43e76c76eff27fde
  grounded_claim:ec5fc4e83b25519dc44f2878ed69588b

original citation: citation:0cb9a00ce581b4d09a0ab14f755caf05
correction citation: citation:13ae2675d1ce8f512389eda12e4b6632
```

Treatment and control both have three claims, both remove the affected prior claim, both add the
same replacement, and both cite the same original and correction sources. Treatment preserves both
stable claim identities. Control preserves neither and introduces the two frozen paraphrase
identities.

The reviews used product policy `world_recorded_correction_revision_stability` version
`candidate-1`, material
`sha256:0145cc35244c21b84f3ba346ccb16192b825fd91d1bcff950e3f0a8005ac932b`:

```text
treatment review 1: brief_revision_stability_review:3b50050e155af3d3eb4391e232a178d0
treatment review 2: brief_revision_stability_review:9f0544d7c79b9a6601760d98133db156
control review 1: brief_revision_stability_review:ac1422dde272aed347045d671e2c6276
control review 2: brief_revision_stability_review:1a4d0d821b3752a47d15a3d6a1746bc7
treatment preserved stable claims: 2, 2
control preserved stable claims: 0, 0
treatment drifted stable claims: 0, 0
control drifted stable claims: 2, 2
treatment score: 1.0, 1.0
control score: 0.0, 0.0
matched pairs: 2
mean effect: 1.0
classification: useful
proposal action: promote
proposal live effect: false
historical replay: true
replay reauthorization: false
```

The exact evaluation was `impact_evaluation:d0ba0242b75dd5ec63ba27aa223a0225` with material
`sha256:d0ba0242b75dd5ec63ba27aa223a0225ff83239a40398a8cbd50d54cea1a3a0a`.
The exact non-effective proposal was
`impact_governance_proposal:9e5a4eab5ea3c147310f6e6f8011c7cd` with material
`sha256:9e5a4eab5ea3c147310f6e6f8011c7cd56682933711e3be8924fbe294426b40d`.

## Verification

The frozen World dependency versions plus the stacked Core candidate and separately packaged
reference action adapter produced:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py \
  domain_packs/tests/test_p2c6_contradiction_attention_outcome.py \
  domain_packs/tests/test_p2c7_correction_detection_delay_outcome.py \
  domain_packs/tests/test_p2c8_correction_revision_stability_outcome.py -q --tb=short
20 passed in 6.50s

python -B -m pytest -q --tb=short
103 passed in 20.04s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.26s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.05s

# Installed public ace-core==0.5.0; no Core source checkout or reference action adapter.
python -B -m pytest -q --tb=short -rs
82 passed, 21 skipped in 14.24s

ruff check --no-cache <P2C8 changed Python files>
PASS

ruff format --check --no-cache <P2C8 changed Python files>
3 files already formatted

uv build --out-dir <temporary-directory>
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The twenty-one public-Core skips are explicit boundaries: one P2C2 test requires the separately
packaged Core reference action adapter; P2C3-P2C8 require unreleased stacked Core candidate
contracts. The wheel contains 45 inert Domain Pack JSON/metadata files, no Python or entry points,
and retains `ace-core>=0.5.0,<0.6`.

Repository-wide Ruff remains an inherited release-hygiene blocker. The exact locked check reports
the same 15 lint findings and 20 format targets as the P2C7 parent. Scoped P2C8 checks and
`git diff --check` are green. P2C8 does not rewrite unrelated history, but release closeout must
reconcile the repository-wide gate before publication.

## Claim boundary

The World reviewer exact-loads the prior and revised Briefs, then derives affected-update
correctness, correction visibility, complete source coverage, claim-count preservation, and the
exact stable-claim partition. The Core Outcome points to that review record. Historical replay
requires no new authority, and fresh hosts reproduce the exact Brief identities, claim sets,
classification, metrics, and proposal disposition.

The paraphrase control is a frozen World policy fixture, not a general semantic-equivalence engine.
One correction and two replicated workflows do not establish live revision, a population stability
rate, calibration, source independence, general Brief quality, causality, legal truth, or human
benefit. The proposal remains non-effective and unapplied.

## Remaining work

Calibration, another independently sourced correction event, a materially different Market
journey, combined-main review/CI, public artifacts, repository-wide lint/format reconciliation,
security/release checks, and opt-in live transport remain future bounded work. Core issue #49 F1,
F3, and F5 still require explicit 0.6 release-owner disposition; this World packet neither
implements nor re-dates them.
