# World Intelligence 0.10.0 — Measured Intelligence

**Release status:** released 2026-08-11. The
[`v0.10.0` GitHub Release](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.10.0)
and [`0.10.0 PyPI distribution`](https://pypi.org/project/ace-domain-world-intelligence/0.10.0/)
are public.

## Install target

```bash
uv add "ace-domain-world-intelligence==0.10.0"
# or
pip install "ace-domain-world-intelligence==0.10.0"
```

Requires Python 3.12 and `ace-core>=0.6.0,<0.7`.

## Exact release identity

- World tag and source commit: `v0.10.0` at
  `f6fdad88ce51ff983e582f5f913801cf3084807d`.
- Core tag and source commit: `v0.6.0` at
  `1e383e1e265e59290478eef6483c2565a0d3dbbc`.
- World merged-main CI:
  [run 31538767665](https://github.com/augmented-cognition-engine/domain-world-intelligence/actions/runs/31538767665),
  passed.
- World trusted-publication workflow:
  [run 31538936902](https://github.com/augmented-cognition-engine/domain-world-intelligence/actions/runs/31538936902),
  passed.

| Public artifact | SHA-256 | Published |
|---|---|---|
| `ace_domain_world_intelligence-0.10.0-py3-none-any.whl` | `616ae3f3d8d670b142761eaff7ded7e0baf37029201027ccc5b0b9c1018da9ad` | PyPI 2026-08-11T21:40:32.681331Z |
| `ace_domain_world_intelligence-0.10.0.tar.gz` | `079c674a14499c540c53efb6684e54969dae1c6c2c3e3655219e71ae025b082a` | PyPI 2026-08-11T21:40:33.855803Z |
| `ace_ext_world_federal_register_source-0.3.0-py3-none-any.whl` | `b4b28220a85f1c8353d772bece9e22c775fe7e73a825db0510d90e3dff39e652` | GitHub Release 2026-08-11T21:40:32Z |
| `ace_reference_workspace_action-0.2.0-py3-none-any.whl` | `eaa51ea704e9162363a4483d1f7d7779778b953ed2a2d80b67dfb332e1cd3f62` | Core GitHub Release |

The World wheel and normalized source archive were each rebuilt twice from the merge-commit epoch
`1786484257`; both pairs were byte-identical. The independently packaged World source-adapter wheel
also reproduced byte-for-byte. All three artifacts passed strict metadata checks. Public PyPI and
GitHub hashes exactly match those local merged-source builds.

## Public-artifact reproduction

A cache-free Python 3.12 environment installed only
`ace-domain-world-intelligence==0.10.0` from the public PyPI index. It resolved public
`ace-core==0.6.0`, loaded the `world_intelligence` manifest from `site-packages`, and did not install
either optional adapter transitively.

A second isolated run cloned only the exact public World tag and explicitly installed the two
hash-verified public adapter assets above. Core and both adapters imported from `site-packages`; no
Core checkout was present. Two fresh workspace runs produced equal bounded projections across the
complete recorded World journey:

| World-owned measure | Classification | Matched pairs | Mean effect | Proposal |
|---|---|---:|---:|---|
| structural citation coverage | useful | 2 | 1.0 | promote, non-effective |
| citation correctness | useful | 2 | 1.0 | promote, non-effective |
| contradiction attention | useful | 2 | 1.0 | promote, non-effective |
| correction detection delay | useful | 2 | 1.0 | promote, non-effective |
| correction-induced revision stability | useful | 2 | 1.0 | promote, non-effective |
| single-event forecast scoring | useful | 2 | 0.5 | promote, non-effective |
| independent BLS correction quality | useful | 2 | 1.0 | promote, non-effective |

Every proposal was non-selectable and had no live effect. The separately authorized review of the
structural-coverage proposal reproduced `reject` with `no_action`; it preserved the useful
classification and promote proposal, applied nothing, and changed no effective governed state.
Historical evaluation replay required no new authorization.

## Verification before publication

```text
complete World domain suite: 135 passed
separate official-source adapter suite: 80 passed
root release-contract suite: 9 passed
Ruff check and format: passed
workflow YAML and diff checks: passed
strict artifact metadata checks: passed
repeated artifact builds: byte-identical
```

## Boundary

This release proves exact recorded-source product evaluation under explicit World-owned criteria.
It does not establish causality, population performance, general model quality, human benefit,
current network freshness, autonomous monitoring, autonomous publication, or general SI4
completion. Domain nouns and source policy remain in World. No proposal applies itself, and no
evaluation result grants action or policy authority.
