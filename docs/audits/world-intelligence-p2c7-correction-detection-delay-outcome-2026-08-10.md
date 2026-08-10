# World Intelligence P2C7 correction-detection-delay outcome audit — 2026-08-10

Status: **stacked candidate evidence only; not a release, SI4 pass, live-monitoring proof, or
applied governance change**

## Source identity

- World base: P2C6 commit `590cf9bb640681ab5095d3abd451092f72f8d929`
- World branch: `codex/world-correction-detection-delay`
- Core dependency: exact observed-result candidate commit
  `433e3d16c5458c975557dcd1552824fb959d4d12`
- Released identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Frozen source pair and source policy

The immutable recorded fixture digest is
`sha256:2b81d3950cbfd127408eec227ec5cd249677a189120d6ca7b603d85d01074543`.
It names:

```text
original: 2020-28779, published 2020-12-29, 85 FR 85524
correction: 2021-10670, published 2021-05-20, 86 FR 27275
correction relationship: 2021-10670 corrects 2020-28779
corrected page: 85530
corrected instruction:
  Remove instruction 20a and redesignate instructions 20b and 20c as instructions 20a and 20b.
original Observation: observation:f1768d6f4191a86e245846a9a1e33768
correction Observation: observation:fced5d3bbc3802c0285021142b332e29
```

The display pages are FederalRegister.gov and the corresponding official-format PDF references
are govinfo.gov:

- original display: <https://www.federalregister.gov/documents/2020/12/29/2020-28779/completing-the-transition-to-electronic-filing-licenses-and-authorizations-and-correspondence-in-the>
- original official-format PDF: <https://www.govinfo.gov/content/pkg/FR-2020-12-29/pdf/2020-28779.pdf>
- correction display: <https://www.federalregister.gov/documents/2021/05/20/2021-10670/completing-the-transition-to-electronic-filing-licenses-and-authorizations-and-correspondence-in-the>
- correction official-format PDF: <https://www.govinfo.gov/content/pkg/FR-2021-05-20/pdf/2021-10670.pdf>

FederalRegister.gov is not represented as the official legal edition. The fixture retains the
govinfo PDFs as verification references and explicitly claims neither legal truth nor network
access.

## Exact point-in-time result

One source-checkout run recorded two treatment and two delayed-control reviews under product
policy `world_recorded_official_correction_detection` version `candidate-1`, material
`sha256:7a68f95458908479ad714b2f7815734edbdef06fc4898ce32f06c73bb8a6b37f`:

```text
frozen replay availability: 2021-05-20T00:00:00Z
product target: 600 seconds

treatment artifact:
  correction_handling_artifact:aa69e85159cf8a7499fced4863cd76af
  sha256:aa69e85159cf8a7499fced4863cd76af746b0db0b1bad7a6fcaa124b7d06dcac
control artifact:
  correction_handling_artifact:cbd406f42315f3c4f64921ca21b4f46f
  sha256:cbd406f42315f3c4f64921ca21b4f46f61d200b53c0a0111ae65c830ca0f22fe

treatment delay: 300, 300 seconds
control delay: 21600, 21600 seconds
treatment linkage/instruction/prior preserved: true, true, true
control linkage/instruction/prior preserved: true, true, true
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

The exact review identities were:

```text
treatment 1: correction_detection_review:3b3de3ca793a3a199d824c05e0dddd65
treatment 2: correction_detection_review:dd481d3fc071d11419bdebab971ada2c
control 1: correction_detection_review:b48c8126b27b85816cb78f5b5edf55a7
control 2: correction_detection_review:e96a3ab662b0603734b63bb05cb5d89d
```

The exact evaluation was `impact_evaluation:5c743a57ca27f4a818ef18980d421764` with material
`sha256:5c743a57ca27f4a818ef18980d42176459ce8deef1f6a3693f46ad6276d17888`.
The exact non-effective proposal was
`impact_governance_proposal:443218f00acca01bee0e565f60841b61` with material
`sha256:443218f00acca01bee0e565f60841b61a43bcf5a19ceff7367f03506a2e5b7e2`.

## Verification

The frozen World dependency versions (`pydantic==2.13.4`, `pytest==9.1.1`,
`pytest-asyncio==1.4.0`, Ruff `0.16.2`) plus the stacked Core candidate and separately packaged
reference action adapter produced:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c4_reviewed_impact_disposition.py \
  domain_packs/tests/test_p2c5_citation_correctness_outcome.py \
  domain_packs/tests/test_p2c6_contradiction_attention_outcome.py \
  domain_packs/tests/test_p2c7_correction_detection_delay_outcome.py -q --tb=short
15 passed in 4.16s

python -B -m pytest -q --tb=short
98 passed in 18.43s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.27s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.05s

# Installed public ace-core==0.5.0; no Core source checkout or reference action adapter.
python -B -m pytest -q --tb=short -rs
82 passed, 16 skipped in 14.15s

ruff check --no-cache <P2C7 changed Python files>
PASS

ruff format --check --no-cache <P2C7 changed Python files>
3 files already formatted

uv build --out-dir <temporary-directory>
Successfully built unchanged 0.9.0 source distribution and inert data-only wheel

git diff --check
PASS
```

The sixteen public-Core skips are explicit boundaries: one P2C2 test requires the separately
packaged Core reference action adapter; P2C3-P2C7 require unreleased stacked Core candidate
contracts. The wheel contains 45 inert Domain Pack JSON/metadata files, no Python or entry points,
and retains `ace-core>=0.5.0,<0.6`.

An attempt to create another isolated locked environment was interrupted twice by the local Codex
permission review timeout before `uv sync` could start. Verification therefore reused the existing
environment with versions checked against `uv.lock`; its editable parent-checkout namespace hook
was excluded from the full-suite process so only this isolated worktree supplied World code. The
package build independently resolved its declared build requirement and completed successfully.

Repository-wide Ruff remains an inherited release-hygiene blocker, not made green by this packet.
The exact locked check reports the same 15 lint findings as P2C6 and broad format checking reports
20 existing files that would be reformatted. Scoped P2C7 checks and `git diff --check` are green.
P2C7 does not rewrite unrelated history, but release closeout must reconcile the repository-wide
gate before publication.

## Claim boundary

The World reviewer exact-loads the correction artifact and its two immutable Observations, then
derives linkage, instruction correctness, prior-record preservation, target disposition, and score
from the frozen policy. The Core Outcome points to that exact review record and carries the delay
as generic latency. Replay returns historical evaluation material without new authority, and
fresh hosts reproduce the fixture, classification, delays, scores, and proposal disposition.

This demonstrates one explicit official correction pair under recorded replay. The availability
and detection times are frozen test coordinates, not observed network-arrival times. Two replicated
workflows over one event do not establish live discovery, a population delay distribution,
calibration, revision stability, source independence, general Brief quality, causality, legal
truth, or human benefit. The proposal remains non-effective and unapplied.

## Remaining work

Calibration, revision stability, another independently sourced correction event, a materially
different Market journey, combined-main review/CI, public artifacts, repository-wide lint/format
reconciliation, security/release checks, and opt-in live transport remain future bounded work.
Core issue #49 F1, F3, and F5 still require explicit 0.6 release-owner disposition; this World
packet neither implements nor re-dates them.
