# World Intelligence P2C3 measured-feedback candidate audit — 2026-08-10

Status: **candidate evidence only; not a release or applied governance change**

## Source identity

- World base: `0a2c0829923aabd0cf69e51c16293b534f41dab6`
- World branch: `codex/measured-intelligence-world-journey`
- Core dependency: PR [#88](https://github.com/augmented-cognition-engine/core/pull/88), commit
  `9078018`
- Released World identity intentionally unchanged: `ace-domain-world-intelligence==0.9.0`,
  `ace-core>=0.5.0,<0.6`

## Exact acceptance result

One candidate run reproduced the exact P2C2 target Brief
`brief:c98524e788bc6bcccbc354e7d81fcdb5` from Federal Register documents `2026-15932` and
`2026-16197`. Its two required admitted Observation keys were:

- `observation:0ddeed52469da44bac7c94598e4b8fa7`
- `observation:66de839538acfb032dd4b0a84155c909`

Two treatment reviewed exports retained both keys and scored `1.0, 1.0`. Two matched reviewed
exports of the exact source-only control retained neither and scored `0.0, 0.0`. Under criterion
`impact_criterion:world-official-observation-citation-coverage` version `candidate-1`, the result
was:

```text
classification: useful
matched pairs: 2
treatment mean: 1.0
control mean: 0.0
mean effect: 1.0
95% deterministic interval: [1.0, 1.0]
proposal: promote
proposal live_effect: false
proposal selectable: false
proposal requires_human_review: true
historical replay: true
replay reauthorization: false
```

The run appended the evaluation and proposal as one exact measured-impact transaction. A fresh
service reopened it with an authorizer that raises on use, so the successful replay did not
reclassify evidence or obtain new authority.

## Verification

Source-checkout verification with Core PR #88 and the separately packaged reference action adapter:

```text
python -B -m pytest domain_packs/tests/test_p2c3_measured_feedback.py -q --tb=short
2 passed in 0.55s

python -B -m pytest -q --tb=short
85 passed in 14.81s

python -B -m pytest adapters/federal_register_source/tests -q --tb=short
26 passed in 0.26s

python -B -m pytest tests/test_release_contract.py -q --tb=short
7 passed in 0.03s

ruff check scripts/p2c2_governed_reality_brief.py \
  scripts/p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c3_measured_feedback.py
PASS

ruff format --check scripts/p2c3_measured_feedback.py \
  domain_packs/tests/test_p2c3_measured_feedback.py
PASS

git diff --check
PASS
```

Locked public-compatibility verification resolved `ace-core==0.5.0` without a Core checkout. The
focused candidate tests skipped explicitly because the unreleased contract was absent, and the
complete public-boundary suite stayed green:

```text
P2C3 focused: 2 skipped
complete World: 82 passed, 3 skipped in 14.37s
```

The other skipped test is the existing P2C2 cross-repository acceptance, whose independently
packaged reference adapter is intentionally absent from the root lock. The source-checkout run
above executes that test and both P2C3 tests.

`uv build` produced exactly the unchanged 0.9.0 source distribution and wheel in a temporary
directory. The release-contract suite confirms the wheel mapping remains inert JSON Domain Pack
material and excludes candidate scripts, tests, adapters, and audit documentation.

## Claim boundary

This record proves one product-defined structural comparison over exact official-public-data
lineage, reviewed actions, observed Outcomes, and governed feedback machinery. It does not prove
human benefit, causality, citation correctness, legal effect, general Brief quality, live network
freshness, autonomous publication, or effective promotion. The source-only control is deliberately
bounded and the two pairs are deterministic fixtures. The proposal was not applied.

The next packet is a separately authorized human disposition of this exact proposal. Broader World
measurement and live transport remain independent work.
