# World Intelligence 0.10.0 release-candidate audit — 2026-08-11

**Status:** bounded candidate evidence. This record does not claim public World installation,
publication, general benefit, an applied governance change, or ACE 0.6 completion.

## Exact source and dependency identity

- World candidate source: `6c35ee6e6aa5666d52dc37ba05400ed2753e8cbc`.
- World branch: `codex/world-v0.10.0-release`.
- Source epoch: `1786483870`.
- Public Core release: `ace-core==0.6.0`, tag `v0.6.0`, commit
  `1e383e1e265e59290478eef6483c2565a0d3dbbc`.
- Public Core wheel SHA-256:
  `1dd6e28f43f8d0894aba11e16e95b6b66eb8198c233ef297425e3561285373b3`.
- Public Core reference action-adapter wheel SHA-256:
  `eaa51ea704e9162363a4483d1f7d7779778b953ed2a2d80b67dfb332e1cd3f62`.

The lock resolves public `ace-core==0.6.0`; there is no Core Git or path override. The inert root
distribution declares `ace-core>=0.6.0,<0.7`. The separately packaged official-source adapter is
version 0.3.0 under the same Core window and remains absent from root runtime metadata.

## Reproducible candidate artifacts

Two independent builds used the exact source epoch. Root wheel, normalized root source archive,
and source-adapter wheel were byte-identical across the two builds and passed strict Twine checks.

| Artifact | SHA-256 |
|---|---|
| `ace_domain_world_intelligence-0.10.0-py3-none-any.whl` | `56b7e66dac31c0ab6b3d0e9ee1bf09b3763b88fbdf7d53f5f54bf844fe7978cb` |
| `ace_domain_world_intelligence-0.10.0.tar.gz` | `0db1c2055253ac38d7cb7bb0a26e22dd0afd54c28b5a63b4ddd0b67a699f2a2b` |
| `ace_ext_world_federal_register_source-0.3.0-py3-none-any.whl` | `5bb6b5e36585782576b9706a37b0bcfa14951b24605a08ecb15a11c8a7bc33fb` |

The root wheel contains 59 declared payloads and no Python module, source-adapter package, test,
entry point, or install hook. The normalized source archive contains 90 members, all with exact
epoch `1786483870`, uid/gid zero, and empty owner names. Release CI rebuilds both root artifacts a
second time and compares their bytes before accepting the candidate.

## Product result reproduced

The complete World packet ran against public Core 0.6.0 and the separately installed public Core
reference action adapter. The recorded-replay clock now keeps resource availability, criteria,
Decisions, Actions, and Outcomes in one explicit scenario timeline; it does not borrow the host
wall clock. Criteria are frozen before governed Decisions, and later correction/revision fixtures
advance only at their declared acquisition boundaries.

The unchanged domain-neutral Core contracts reproduce:

- exact artifact attribution through Decision and reviewed Action to observed Outcome;
- matched World-owned treatment and negative-control evidence under frozen conditions;
- useful, harmful, and unproven classifications with explicit exclusions and uncertainty;
- append-only evaluation and a non-effective proposal that remains non-selectable and unapplied;
- an authorized `reject` / `no_action` disposition that preserves the useful evaluation and leaves
  effective state unchanged;
- correction-delay, revision-stability, forecast-calibration, and independent BLS correction
  outcomes without moving source policy or domain nouns into Core.

## Verification

```text
# Complete World domain suite
135 passed in 25.54s

# Separately packaged official-source adapter suite
80 passed in 0.26s

# Root release contract, including deterministic archive normalization
9 passed in 0.05s

ruff check .
All checks passed!

ruff format --check .
113 files already formatted

workflow YAML parse
PASS

git diff --check
PASS

twine check --strict (root wheel, root sdist, source-adapter wheel)
PASS
```

A cache-free Python 3.12 environment installed the candidate root wheel with public
`ace-core==0.6.0`. The World manifest resolved from `site-packages`; neither optional adapter was
installed transitively.

## Boundary and remaining release gates

The measurements remain exact, small, recorded-source product checks. They do not establish
causality, population performance, general model quality, human benefit, current network
freshness, autonomous publication, or general SI4 completion. No proposal applies itself.

Publication remains blocked until the PR head passes hosted CI and review. After merge, the exact
merged source must be rebuilt, tagged, published, verified from the public index in a clean
environment, and used to reproduce the recorded World journey without a Core checkout. Only that
later released-artifact record may advance the World roadmap or support closing Core issue #38.

Core issue #49 remains open: F1 and F5 are complete; F3 remains contained and explicitly due
2026-11-05. This World packet neither reopens those items nor expands scope into F3.
