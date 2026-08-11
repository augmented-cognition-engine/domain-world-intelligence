# World Intelligence P2C9 forecast-calibration outcome audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, population-calibration proof,
model-skill finding, or applied governance change**

## Source identity

- World base: P2C8 commit `129767d27d4af22dba292deb9e691375a0695bb8`
- World branch: `codex/world-forecast-calibration`
- Core dependency: exact observed-result candidate commit
  `433e3d16c5458c975557dcd1552824fb959d4d12`
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact point-in-time result

The source fixture remains
`sha256:2b81d3950cbfd127408eec227ec5cd249677a189120d6ca7b603d85d01074543`,
with original Observation `observation:f1768d6f4191a86e245846a9a1e33768` and correction
Observation `observation:fced5d3bbc3802c0285021142b332e29`.

One source-checkout run recorded this exact availability order:

```text
original Observation available: 2026-08-11T03:15:24.023307Z
forecast issued:               2026-08-11T03:15:24.024601Z
latest reviewed Action done:   2026-08-11T03:15:24.057528Z
correction result available:   2026-08-11T03:15:24.061041Z
```

The two forecast records were:

```text
treatment:
  public_event_forecast:cadabc0db05387ffda21e167a7ae8a0c
  sha256:cadabc0db05387ffda21e167a7ae8a0cfba830841d39b9141f4faa1cfca4f56c
  probability: 0.75
control:
  public_event_forecast:2ebf7bd7c21363bcc6074bd654f020de
  sha256:2ebf7bd7c21363bcc6074bd654f020de32a021280450cde5f889e92f24243488
  probability: 0.25
```

Both records bind only the original Observation, the same target event, policy, source family,
resolution rule, and window. Neither contains correction document `2021-10670`, the correction
Observation coordinate, the eventual outcome, or an outcome score. The correction's exact immutable
reference becomes available after all four forecast Actions complete.

The reviews used World policy `world_recorded_binary_forecast_brier_quality` version `candidate-1`,
material `sha256:759c13b02bff4b6d749ff20888a9fa7d4f3a67e6ef94439801d28d9d99abf4e7`:

```text
treatment review 1: forecast_resolution_review:dceee9319c93d8f4aaa1712f6ad4a736
treatment review 2: forecast_resolution_review:388863533f4bceb49c49326c029048f9
control review 1:   forecast_resolution_review:585c2385de9b45b3aeee5705a577cfb0
control review 2:   forecast_resolution_review:6afe8778c77d840aca6b51d5a7198c3e

binary event outcome: 1.0
treatment Brier loss: 0.0625, 0.0625
treatment quality:    0.9375, 0.9375
control Brier loss:   0.5625, 0.5625
control quality:      0.4375, 0.4375
matched pairs: 2
mean effect: 0.5
classification: useful
proposal action: promote
proposal live effect: false
historical replay: true
replay reauthorization: false
```

The exact point-run evaluation was `impact_evaluation:d94ec6d786c8a4bbfb8038959ca7a7d4`
with material
`sha256:d94ec6d786c8a4bbfb8038959ca7a7d45567d4ddcdb3b6c431b8cdc2dac84c47`.
The exact non-effective proposal was
`impact_governance_proposal:260db0b19aff6fe01cb8f0fbc81f3327` with material
`sha256:260db0b19aff6fe01cb8f0fbc81f33278392794d8652a41442751bfebe79141f`.

These point-run identities deliberately include exact record-availability and reviewed-action time.
Historical replay in the same durable store returns those exact identities without reauthorization.
Fresh hosts reproduce the source content identities, target definition, probabilities, event
outcome, Brier material, classification, and proposal semantics; they do not pretend independent
wall clocks are the same immutable availability coordinate.

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
  domain_packs/tests/test_p2c9_forecast_calibration_outcome.py -q --tb=short
25 passed in 8.59s

python -B -m pytest -q --tb=short
108 passed in 22.22s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.22s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.04s

# Installed public ace-core==0.5.0; candidate tests skip explicitly.
python -B -m pytest -q --tb=short -rs
83 passed, 25 skipped in 13.72s

ruff check --no-cache <P2C9 changed Python files>
PASS

ruff format --check --no-cache <P2C9 changed Python files>
4 files already formatted

uv build --out-dir /tmp/ace-p2c9-dist-20260810
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The twenty-five public-Core skips are explicit candidate boundaries: P2C3 through P2C9 require
unreleased stacked Core measured-impact contracts. The public P2C2 journey and every released
boundary remain green. The wheel contains 45 inert Domain Pack JSON/metadata files, no Python or
entry points, and retains `ace-core>=0.5.0,<0.6`.

Repository-wide Ruff remains an inherited release-hygiene blocker. With the same locked Ruff
version, both the P2C8 parent and this P2C9 worktree report exactly 14 lint findings and 12 format
targets. Scoped P2C9 checks and `git diff --check` are green. This packet does not rewrite unrelated
history, but release closeout must reconcile the repository-wide gate before publication.

## Claim boundary

The World forecast contract forbids extra result material and requires every basis reference to be
available at issuance. The review exact-loads the forecast, original Observation, and later
correction Observation, derives the binary event from their explicit correction link, and derives
the Brier contribution from probability and event outcome. The Core Outcome points to that exact
review. Historical replay requires no new authority, and the proposal remains non-effective,
non-selectable, and unapplied.

This is a single-event probabilistic score over a held-out recorded result. It is not an empirical
calibration curve, population reliability estimate, historically contemporaneous forecast, ACE
probability-generation proof, model-skill finding, live-monitoring result, source-independence
finding, causal estimate, general Brief-quality score, legal-truth claim, or human-benefit result.

## Remaining work

A materially different real source, independent Market reproduction, combined-main review/CI,
public Core artifacts, repository-wide lint/format reconciliation, security/release checks, and
opt-in live transport remain future bounded work. Core issue #49 F1, F3, and F5 still require
explicit 0.6 release-owner disposition; this World packet neither implements nor re-dates them.
