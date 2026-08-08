# World Intelligence — P2B-SI1 supersession-impact view (2026-08-07)

Closes **WI-CR-004**. The World consumer contract-request backlog is now empty.

## Result

Both frozen corrections are exercised, and they produce genuinely different
blast radii because their lineage genuinely differs.

| Supersession | Impacted | Direct / transitive | Max depth | Unaffected | Impacted claims |
|---|---|---|---|---|---|
| `correction_114` over `ledger_report_1088` | 11 | 6 / 5 | 3 | 16 | 9 (3 full, 6 partial) |
| `order_47` over `mwa_bulletin_214` | 7 | 2 / 5 | 4 | 20 | 5 (0 full, 5 partial) |

Closure size is 28 in both cases, and `impacted + unaffected + target == closure`
exactly, so the boundary is disclosed rather than inferred.

The Ledger correction reaches **3 Observations** — the Coastal Wire syndication,
the Harborview reprint, and the correction record itself, all of which derive
from the superseded report — plus 4 entity snapshots, 2 Shifts, 1 Signal, and the
Case. The Order supersession reaches **no Observation at all**, because nothing
derives from the bulletin; it reaches only derived state (2 snapshots, 2 Shifts,
2 Signals, the Case). Impact was not invented where lineage does not support it.

## Exact new identities (P2B-SI1)

| Artifact | Identity |
|---|---|
| Ledger impact projection | `supersession_impact_projection:f3723de8e9ac5c4390c5c46137f3765e` |
| Order impact projection | `supersession_impact_projection:61e8fb0eae42019e7344e97210638a54` |

## No new activation was needed

This packet **reuses the accepted WI-CR-003 activation** (`world_intelligence`
0.4.0) unchanged. No Pack module was added, because impact is a property of
admitted lineage rather than of domain vocabulary. The packet therefore
reproduces the WI-CR-003 packet byte-for-byte:

- `case:412426eee708d56f6bda931ccf9e5d8b`
- `brief:25d8232c9bfa27050bdcb160fb75f06c`

WI-CR-005 (`case:2ee2…`, `brief:8fb31…`) and WI-CR-002 (`case:bc28…`,
`brief:7adb…`) remain untouched and are re-verified in the same suite run.

## History is preserved, not rewritten

The correction is admitted **one hour after** the Brief is durable, as two
Observations that assert `supersedes` against their targets. Their payload is
the scenario's own pinned `supersessions` entry, so nothing is invented, and
they sit outside the frozen Case closure — exactly as a real correction would.

`historical_integrity` proves all of:

- the Brief identity is unchanged,
- the Brief, receipt, and status projection replay **identically**,
- the replay consumed **no new reasoning** (`provider.calls == 1`),
- the Brief's cutoff precedes the correction.

The impact projection names the Brief, receipt, status projection, and Case in
`preserved_artifact_ids` and never touches them.

## Negative vectors

All four fail closed with `SupersessionImpactAdmissionError`, and exactly the one
legitimate Brief remains durable afterwards:

- `wrong_direction_derived_from_is_not_supersession` — the real
  `ledger_correction_114` record derives from the report but asserts no
  `supersedes` edge, so it is **not** accepted as a superseder,
- `superseder_targets_a_different_record` — the Order assertion cannot be used
  against the Ledger report,
- `target_outside_the_authorized_closure`,
- `future_leakage_before_the_closure_exists` — a cutoff predating the closure.

## Honest limits

* **Impact is dependency, not falsehood.** The fixture's own correction leaves
  Delegate Quell's attributed statement untouched. The projection reports scope,
  never a verdict.
* **Impact is only as strong as the admitted lineage**, exactly as with
  derivation families.
* **Supersession must be asserted, never guessed.** Absent a `supersedes` edge,
  ACE reports no impact rather than inventing one.

## Boundary invariants

World added no private graph, persistence, authority, reasoning runtime, status
projector, source-independence engine, **supersession engine**, or imperative
Pack code. `historical_artifact_rewritten` is `False`.

## Verification

```
domain_packs/tests    70 passed, 0 xfailed   (baseline 55 passed, 1 xfailed)
ruff check scripts/ domain_packs/            All checks passed
git diff --check                             clean
```

Marketing regression control (source unchanged): `88 passed, 1 skipped`.

## Next step toward a public one-command visual demo

Four harnesses now emit pinned JSON projections covering the full arc: admission
→ Case → governed Brief → per-statement status → independence → supersession
impact. The remaining step is a single entry point (`scripts/demo.py`) that runs
them in order and renders one timeline: what was admitted, what ACE concluded and
with what epistemic status, which corroboration was genuinely independent, and
which statements a later correction touches — with every claim clickable to its
exact record identities. That is presentation over already-pinned data; no new
platform capability is required.
