# World measured-intelligence main-convergence audit — 2026-08-11

**Status:** bounded direct-to-main candidate evidence. This is not a merge, tag, release, SI4 pass,
ACE 0.6.0 completion, live-monitoring proof, or applied governance change.

## Exact source and artifact identity

- World live-main base: `8de1027c4c995582b42c4a1f936a72e2c42878a0`
- World executable source: `87625d55c717a9c649d4f44a06d1767b52fed255`
- Core measured-impact source: `433e3d16c5458c975557dcd1552824fb959d4d12`
- Branch: `codex/world-measured-intelligence-main-convergence`

| Artifact | Version | SHA-256 |
|---|---:|---|
| `ace_core-0.5.0-py3-none-any.whl` | 0.5.0 candidate | `29752aa751570286794ff2abd1071a43f622883d4778e161687e10363f76f6c3` |
| `ace_reference_workspace_action-0.1.0-py3-none-any.whl` | 0.1.0 | `9c600d4b3e0d19525f1e04629bd231d8d6913d2ad11bc63fa2858e7da396f8f1` |
| `ace_ext_world_federal_register_source-0.2.0-py3-none-any.whl` | 0.2.0 | `1b80cc598b467a8ab0f47aabb5f01bd0cb1c7709b48aa02352a0ef802988b4fe` |
| `ace_domain_world_intelligence-0.9.0-py3-none-any.whl` | 0.9.0 candidate | `a067b3106772437d2dcfee890dc7d89005d3f7afd9e6dc0cbed027327bea9cae` |

Both World-owned wheels were built twice from the exact source with
`SOURCE_DATE_EPOCH=1786459215`; each repeated wheel was byte-identical. The two generated source
distributions contained the same source but their gzip containers were not byte-identical, so this
packet makes no reproducible-sdist claim. A final release must bind one exact sdist and wheel set.

No version was advanced and no artifact was published.

## Live-main reconciliation

The existing thirteen candidate commits were replayed in order onto live `main` without rewriting
or updating any stacked review branch. The only conflict was the README audit list and dispatch
paragraph: the resolution preserved both the merged AI Command Center lineage evidence and the
measured-feedback evidence. No Python, fixture, manifest, or expected-result conflict occurred.

The repository-wide locked formatter then identified eight files inherited from the new live-main
commit. One mechanical commit formatted those files. The focused AI/source tests remained green,
and no product rule, fixture, source coordinate, expected outcome, or authority boundary changed.

## Installed-artifact reproduction

A fresh Python 3.12 environment loaded Core, the reference action adapter, and the Federal Register
source adapter from `site-packages`. The generator rejected every declared Core checkout root. Two
fresh workspace roots produced byte-identical canonical JSON:

```text
sha256:b70f972e6b7e86ddce09eb3feaa3cd89eede2b236d3e592ee5417dda4d3e95f7
```

The record retains the exact public BLS correction pair, product-owned scoring rule, treatment
scores `[1.0, 1.0]`, control scores `[0.0, 0.0]`, two matched pairs, mean effect `1.0`, useful
classification, and proposal-only `promote`. The proposal remains non-effective, non-selectable,
unapplied, requires human review, and is not reauthorized on historical replay.

## Verification

```text
# combined live-main AI lineage plus P2C3-P2C10 and convergence controls
37 passed in 19.49s

# complete World suite with the exact candidate Core artifact
120 passed in 31.74s

# Federal Register adapter suite
62 passed in 0.39s

# package/release contract
7 passed in 0.07s

# focused post-format AI/source controls
66 passed in 0.52s

ruff 0.16.2 check --no-cache .
All checks passed!

ruff 0.16.2 format --check --no-cache .
98 files already formatted

git diff --check
PASS
```

## Claim boundary and remaining gates

This is one deterministic recorded-replay association under a frozen World correction rule. It is
not causality, population correction performance, JOLTS statistical validation, live freshness,
general SI4 completion, or human benefit. The newly coexisting AI Command Center proof is also
recorded transport, not autonomous live monitoring or publishing.

Core issue #49 F1, F3, and F5 remain open 0.6 gates. Core stack review, merged-source security and
compatibility checks, final version and artifact decisions, public-index installation, and
publication remain release-owner work.
