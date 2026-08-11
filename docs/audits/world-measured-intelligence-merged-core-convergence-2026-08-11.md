# World measured-intelligence merged-Core convergence — 2026-08-11

**Status:** bounded draft-PR artifact evidence. This is not a World or Core release, a tag,
publication, SI4 pass, live-monitoring proof, applied governance change, or ACE 0.6.0 completion.

## Exact source identity

- Core merged `main`: `7013de62ae7320c51c3de9e9a03b049e768e4d84`
- Core main push CI: [run 31520372788](https://github.com/augmented-cognition-engine/core/actions/runs/31520372788), all six gates passed
- World executable/evidence source: `cb7b6fdb2b9fe4dd3c34df8afc1368c86d026710`
- World draft: [PR #17](https://github.com/augmented-cognition-engine/domain-world-intelligence/pull/17)

Core pull requests #88 through #93 were merged in dependency order. This receipt rebuilds the
World convergence artifact from that exact default-branch source instead of inheriting the earlier
stacked Core candidate hash.

## Reproducible candidate artifacts

Each wheel was built twice from its exact source with a fixed source epoch. Both copies were
byte-identical.

| Artifact | Source epoch | SHA-256 |
|---|---:|---|
| `ace_core-0.5.0-py3-none-any.whl` | `1786471152` | `662c4197f3ff0cf7dc1e64b0f8bc6bc705c8a1d6373a8468d9cb1d2df3d8c214` |
| `ace_reference_workspace_action-0.1.0-py3-none-any.whl` | `1786471152` | `31463fbcfe2a9c62b5cc9abe0a67814cd7fdd36de3c9f6ec47835d7be080ed5a` |
| `ace_ext_world_federal_register_source-0.2.0-py3-none-any.whl` | `1786466888` | `4841a02b46fba867d8bac092cd2eab1a45e71537d364fda389192857313e049c` |
| `ace_domain_world_intelligence-0.9.0-py3-none-any.whl` | `1786466888` | `8470b903c165e6897159172c918245fbc7bae7470ce6ad82dbb940776417c049` |

No version changed and no artifact was published. The Core wheel still reports `0.5.0`; the
complete source commit and artifact hash distinguish this local candidate from public Core 0.5.0.

## Installed-artifact result

A fresh Python 3.12 environment installed all four exact wheels plus public dependencies. Core,
the reference action adapter, and the official-source adapter imported from `site-packages`; the
generator rejected every declared Core checkout root. Two fresh workspace runs emitted
byte-identical canonical records:

```text
sha256:c62a7db77b66a15f2930c850bdb8bbc44b542f928c2e0b146b5bf3dde08f30df
```

The updated
[`convergence-v1.json`](../../artifacts/measured-intelligence/convergence-v1.json) retains the
frozen BLS correction pair, treatment scores `[1.0, 1.0]`, control scores `[0.0, 0.0]`, two
matched pairs, mean effect `1.0`, and bounded `useful` classification. The `promote` proposal
remains non-effective, non-selectable, unapplied, requires separate human review, and is not
reauthorized on historical replay. Only the exact source and artifact coordinates changed.

## Verification

```text
# complete World suite against the installed merged Core wheel
123 passed in 37.82s

# complete Federal Register / official-source connector suite
80 passed in 0.65s

# package and release contract
7 passed in 0.07s

# repeated canonical artifact generation
2 identical results; sha256:c62a7db77b66a15f2930c850bdb8bbc44b542f928c2e0b146b5bf3dde08f30df
```

The run used recorded public-source fixtures and made no network request, external action,
provider call, tag, release, or publication.

## Claim boundary and remaining gates

This remains one deterministic recorded-replay association under a World-owned correction rule.
It is not causality, population correction performance, statistical validation, current
freshness, general SI4 completion, or human benefit. World PR #17 remains a draft until its new
head passes review and CI. Core still requires the cross-domain merged-source evidence, issue #49
disposition, final package-version and artifact identities, public-index installation, and an
explicit release-owner decision before ACE 0.6.0 can be published or closed.
