# World measured-intelligence P2D main reconciliation audit — 2026-08-11

**Status:** bounded draft-PR reconciliation evidence. This record restores source-level
mergeability and verifies coexistence with the merged P2D proof. It is not a rebuilt-artifact
convergence record, merge, tag, release, SI4 pass, ACE 0.6.0 completion, live-monitoring proof, or
applied governance change.

## Exact source identity

- World predecessor candidate: `2d7a0ace72bed4d175b0884c8a9b81b6ec063d56`
- World merged P2D `main`: `5447cf160e1b56ffa8b4c505ce4b00b33b6a1aea`
- Reconciled executable merge: `df11bcad790ce854369f640c379cacbecdbf3089`
- Branch: `codex/world-measured-intelligence-main-convergence`
- Installed measured-impact Core candidate: `433e3d16c5458c975557dcd1552824fb959d4d12`

The exact full merge commit above was verified with `git rev-parse HEAD` before this additive audit
commit was created.

## Reconciliation

P2D changed the release workflow, root package payload, connector package, release-contract test,
README, and roadmap. Git merged every executable, fixture, manifest, package, workflow, and release
contract change without a code conflict. The only conflicts were the README evidence/dispatch text
and the roadmap candidate/next sections.

The resolution retains both candidate families:

- P2C3–P2C10 measured feedback, non-effective proposal disposition, and artifact-convergence
  history remain visible and unchanged; and
- P2D LIVE conflict, correction, supersession, historical-artifact preservation, and per-claim
  status evidence remain visible, while World dispatch advances to user-owned monitoring and
  subscription state.

No product rule, source coordinate, immutable identity, evaluation criterion, authority boundary,
package version, schema, or public tool changed in the resolution.

## Verification

```text
# measured-impact convergence, P2C3–P2C10, P2D pack/journey, and P2D connector focus
54 passed in 16.84s

# complete World suite with the installed measured-impact Core candidate
123 passed in 35.32s

# complete Federal Register / official-source connector suite
80 passed in 0.49s

# package and release contract
7 passed in 0.07s

ruff check --no-cache tests scripts adapters/federal_register_source/tests
All checks passed!

ruff format --check --no-cache tests scripts adapters/federal_register_source/tests
29 files already formatted

git diff --cached --check
PASS
```

The first Ruff invocation could not access the sandbox-external default `uv` cache. The exact same
locked commands passed with a task-local temporary cache; no dependency or source changed between
attempts.

## Artifact and release boundary

The existing `artifacts/measured-intelligence/convergence-v1.json` and its earlier audit remain
point-in-time evidence for their named source commits and artifact hashes. This reconciliation did
not rebuild or silently relabel them after P2D changed the World package payload.

Final convergence still requires Core to land, World and Market to rebuild against the exact merged
Core artifact, fresh artifact hashes, compatibility and security gates, and public-index install
proof. The measured-impact proposal remains non-effective, non-selectable, unapplied, and subject to
separate human review.
