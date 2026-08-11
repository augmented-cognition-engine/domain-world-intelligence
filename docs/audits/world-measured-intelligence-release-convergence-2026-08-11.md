# World measured-intelligence release-convergence audit — 2026-08-11

**Status:** bounded candidate artifact evidence. This is not a World or Core release, an SI4 pass,
ACE 0.6.0 completion, live-monitoring evidence, or an applied governance change.

## Source and artifact identity

- Core source: `433e3d16c5458c975557dcd1552824fb959d4d12`
- World generator and release-hygiene source: `7fec49b163fd4c50964576a45511c8645e856f3d`
- World branch: `codex/world-measured-intelligence-release-convergence`
- Canonical record:
  `artifacts/measured-intelligence/convergence-v1.json`
- Canonical record SHA-256:
  `c91359485418be85c6740462bce3c2afd5c8eca6250c7288669c0cdff07a4da9`

The candidate wheels were built with `SOURCE_DATE_EPOCH` set to their exact source-commit time:

| Artifact | Version | SHA-256 |
|---|---:|---|
| `ace_core-0.5.0-py3-none-any.whl` | 0.5.0 candidate | `29752aa751570286794ff2abd1071a43f622883d4778e161687e10363f76f6c3` |
| `ace_reference_workspace_action-0.1.0-py3-none-any.whl` | 0.1.0 | `9c600d4b3e0d19525f1e04629bd231d8d6913d2ad11bc63fa2858e7da396f8f1` |
| `ace_ext_world_federal_register_source-0.2.0-py3-none-any.whl` | 0.2.0 | `bee0161c6a02b2d82b698d72365e401e7c58af633c8f0e774e513619866a90d6` |
| `ace_domain_world_intelligence-0.9.0-py3-none-any.whl` | 0.9.0 candidate | `61abbd08bfedb2dc23cdd0eab8b9a0454b7d7a911ba150e4308e12d9e1cfa534` |

No version was advanced and no artifact was published. The Core candidate intentionally still
reports 0.5.0; its full source commit and wheel hash distinguish it from the released 0.5.0 wheel.

## Installed-artifact reproduction

A fresh Python 3.12 environment installed all four local wheels plus their public dependencies. In
that environment, `ace`, the reference action adapter, and the Federal Register source adapter all
imported from `site-packages`. The generator declared both Core worktrees and the primary Core
workspace forbidden; it would fail if `ace` resolved beneath any of them.

The installed candidate reran the complete append-only P2C2-P2C10 World journey twice from fresh
workspace roots. Both runs emitted byte-identical canonical JSON:

```text
sha256:c91359485418be85c6740462bce3c2afd5c8eca6250c7288669c0cdff07a4da9
```

The record preserves the exact public BLS fixture digest and stable Observation keys, product
policy version and scoring rule, matched treatment/control statements and scores, `useful`
classification, two matched pairs, mean effect `1.0`, proposal-only `promote`, and historical
replay without reauthorization. It deliberately excludes runtime availability/material digests
that change across honest fresh hosts.

## Verification

```text
# P2C3-P2C10 plus convergence controls
33 passed in 13.95s

# complete World domain suite after release-hygiene reconciliation
116 passed in 35.57s

# separately packaged Federal Register source adapter
26 passed in 0.37s

# unchanged 0.9.0 package/release contract
7 passed in 0.05s

ruff 0.16.2 check --no-cache .
All checks passed!

ruff 0.16.2 format --check --no-cache .
84 files already formatted

git diff --check
PASS
```

The repository-wide gate began with 17 lint findings and 20 formatting targets inherited from the
P2C10 parent. The mechanical hygiene commit sorted imports, marked shebang-bearing scripts
executable, documented two intentional fail-closed broad catches, used Python 3.12 native `Z`
parsing, applied the locked formatter, and refreshed only exact hashes whose pinned bytes changed.
The full suite proves that no expected outcome or public identity changed.

## Claim boundary and remaining release work

This result is a deterministic association under one frozen World correction rule. It is not
causality, population correction performance, JOLTS statistical validation, live freshness,
general source independence, general SI4 completion, or human benefit. The `promote` proposal is
non-effective, non-selectable, unapplied, and still requires separate Core authority.

The independent Market candidate exists at
`cd1f2f2c862e5665344e47885f594a77c5aaa59b`, but it remains separately reviewed candidate evidence.
Core combined verification, security review, merge-order review, final release artifacts, and
publication remain open. Core issue #49 F1, F3, and F5 are open 0.6 release gates; this packet does
not waive, defer, resolve, or re-date them.
