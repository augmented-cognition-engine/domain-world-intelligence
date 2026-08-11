# World Intelligence P2C10 independent correction reproduction audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, live-monitoring result,
population-performance finding, or applied governance change**

## Source identity

- World base: P2C9 commit `53feadb40fcc93d23f326b16979ed6640471c4cf`
- World branch: `codex/world-independent-correction-reproduction`
- Core dependency: exact observed-result candidate commit
  `433e3d16c5458c975557dcd1552824fb959d4d12`
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

The frozen BLS fixture is
`sha256:981183a2464f74f4421bd0a6470f0342a5abae8cfebc1b5a8da1562df26babb1`.
It binds release `USDL-25-1087` to correction `bls-errata-2025-07-01-jolts`, with recorded
Observation identities:

```text
original:   observation:faf25d26cc88802368cabf3e17538a7d
correction: observation:3a1351d6ac306374b8a5b472c192d2b9
```

The point-run treatment artifact was
`official_correction_artifact:34d538fbd2c3a6ef6d3e79d0fdb8a344` with material
`sha256:34d538fbd2c3a6ef6d3e79d0fdb8a3440c06b02a1e156a6001bfc1491fd86e21`.
The matched control was
`official_correction_artifact:ab6cfedd1b76602e51c0c8d3c1dbd6d2` with material
`sha256:ab6cfedd1b76602e51c0c8d3c1dbd6d22e5c76b01b1eb59350a8e1bdaa7d8207`.

Both artifacts name the same exact release and correction Observations, `corrects` relation,
source-policy digest, and reviewed workflow. Treatment renders `−39,000`; control renders the
reported pre-correction `(39,000)` form. All four reviews independently recorded complete source
coverage, visible correction linkage, and preserved prior history:

```text
treatment scores: 1.0, 1.0
control scores:   0.0, 0.0
matched pairs: 2
mean effect: 1.0
classification: useful
proposal action: promote
proposal live effect: false
historical replay: true
replay reauthorization: false
```

The exact point-run evaluation was `impact_evaluation:5490b5c680940d88d25d9dacca67103b`
with material
`sha256:5490b5c680940d88d25d9dacca67103b6fb33b8d8c98e0e756488f45dece964e`.
The exact non-effective proposal was
`impact_governance_proposal:da09bf45bb9f48d6cefbb3fb49122e67` with material
`sha256:da09bf45bb9f48d6cefbb3fb49122e679d010cd39140950a57c447e2465f7f86`.

Point-run artifact and evaluation identities include exact record-availability and reviewed-action
times. Historical replay in the same durable store returns those exact identities without
reauthorization. Fresh hosts reproduce the fixture digest, source content identities, scores,
classification, and proposal semantics without pretending independent wall-clock availability
coordinates are identical.

## Verification

The frozen World dependency versions plus the stacked Core candidate and separately packaged
reference action adapter produced:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py \
  domain_packs/tests/test_p2c6_contradiction_attention_outcome.py \
  domain_packs/tests/test_p2c7_correction_detection_delay_outcome.py \
  domain_packs/tests/test_p2c8_correction_revision_stability_outcome.py \
  domain_packs/tests/test_p2c9_forecast_calibration_outcome.py \
  domain_packs/tests/test_p2c10_independent_correction_reproduction.py -q --tb=short
30 passed in 11.01s

python -B -m pytest -q --tb=short
113 passed in 24.20s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.25s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.05s

# Installed public ace-core==0.5.0; candidate tests skip explicitly.
python -B -m pytest -q --tb=short -rs
83 passed, 30 skipped in 14.10s

ruff check --no-cache <P2C10 changed Python files>
PASS

ruff format --check --no-cache <P2C10 changed Python files>
3 files already formatted

UV_CACHE_DIR=/tmp/ace-p2c10-uv-cache uv build --out-dir /tmp/ace-p2c10-dist-20260810
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The thirty public-Core skips are explicit candidate boundaries: P2C3 through P2C10 require
unreleased stacked Core measured-impact contracts. The public P2C2 journey and every released
boundary remain green. The wheel contains 45 inert Domain Pack JSON/metadata files, no Python or
entry points, and retains `ace-core>=0.5.0,<0.6`.

Repository-wide Ruff remains an inherited release-hygiene blocker. With the same locked Ruff
version, both the P2C9 parent and this P2C10 worktree report exactly 14 lint findings and 12 format
targets. Scoped P2C10 checks and `git diff --check` are green. This packet does not rewrite
unrelated history, but release closeout must reconcile the repository-wide gate before publication.

## Claim boundary

BLS's public errata states that the sentence required a missing minus sign; the current archived
release already exposes the corrected form. The fixture explicitly derives the historical original
form from that erratum. It does not claim to preserve original response bytes.

The World review exact-loads the artifact and both immutable source Observations, derives source
coverage, correction linkage, prior-record preservation, corrected-form equality, and stale-form
absence, then records an exact observed result. Core and Intelligence receive only domain-neutral
records, conditions, scores, and classification. Historical replay requires no new authority, and
the proposal is non-effective, non-selectable, unapplied, and subject to separate human review.

This is one hermetic recorded BLS correction. It is not live monitoring, network-arrival evidence,
statistical validation of JOLTS, population correction performance, a general source-independence
claim, causality, general Brief quality, or human benefit.

## Remaining work

Independent Market reproduction, combined-main review/CI, public Core artifacts,
repository-wide lint/format reconciliation, security/release checks, and opt-in live transport
remain future bounded work. Core issue #49 F1, F3, and F5 still require explicit 0.6 release-owner
disposition; this World packet neither implements nor re-dates them.
