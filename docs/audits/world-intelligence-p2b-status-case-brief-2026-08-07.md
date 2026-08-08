# World Intelligence — P2B-SB1 status-aware governed Reality Brief (2026-08-07)

Closes **WI-CR-002**. Keeps **WI-CR-003** and **WI-CR-004** open.

## Result

The frozen `meridia_reservoir_release_72h` scenario now produces a governed
Reality Brief **package** in which all seven World epistemic statuses are
represented per statement, bound to exact claim IDs, through public ACE APIs and
Pack IR only.

- 11 claims, each carrying exactly one declared status.
- All seven declared statuses are used:
  `ace_inference` 3, `admitted_record` 2, `unknown` 2, `attributed_claim` 1,
  `corroborated` 1, `disputed` 1, `scenario` 1.
- One atomic transaction of **three** records:
  `brief`, `case_brief_synthesis_receipt`, `brief_epistemic_status_projection`.
- Deterministic replay: 1 provider invocation across two `synthesize_with_status`
  calls; Brief, receipt, and projection all replay identically.

## Exact new identities (P2B-SB1, pack `world_intelligence` 0.3.0)

| Artifact | Identity |
|---|---|
| Status pack IR | `pack_ir:36cccb917b1420bf85e8c79f0dd9c579` |
| Case | `case:bc28c76926d733c0ce0fe03b9c9222db` |
| Brief | `brief:7adb24b596cac21d7aa4e5476bc8733c` |
| Synthesis receipt | `case_brief_synthesis_receipt:e79d934e0300901e18e0fe4af1064ba2` |
| Status projection | `brief_epistemic_status_projection:fca9062883e92e2e632388c0069c310e` |

## Why the status packet has its own Case identity

Every Intelligence resource carries `activation_revision`, whose digest derives
from the compiled Pack IR digest. Declaring the epistemic-status module
therefore **necessarily** re-keys every resource admitted under it — including
the Case. Preserving `case:2ee200c03f2576307b0bc43e6e128f30` and declaring the
status vocabulary in the Pack are mutually exclusive under content addressing.

This packet resolves that by following the repository's established pattern
(`compile_replay_pack`): it builds a **separate additive** 0.3.0 activation and
leaves the frozen one untouched. `scripts/p2b_case_brief.py` is unchanged in
behaviour and still reproduces the frozen WI-CR-005 identities exactly:

- `case:2ee200c03f2576307b0bc43e6e128f30` — unchanged
- `brief:8fb3173069eca502652b1c9c004c92e6` — unchanged
- `case_brief_synthesis_receipt:3e122634e7f7a76390e6574dfc4f3e8d` — unchanged

`test_the_frozen_wi_cr_005_packet_is_untouched_by_this_additive_packet` asserts
both sides of this in one test.

## Honest scope of `corroborated`

The declared `corroborated` status enforces **at least two supports of kind
`observation`**. That is support cardinality and resource kind only.

It does **not** prove that those Observations come from independent source
families. ACE exposes no derivation-family or source-independence predicate, and
`EpistemicStatusDeclarationV1.proves_source_family_independence` is pinned to
`False` by the platform so the Pack cannot overclaim. The P2B golden fixture's
`independent_family_ids` remains a *fixture* assertion and is deliberately not
promoted into any runtime guarantee here.

**WI-CR-003 stays open.** `test_corroborated_does_not_claim_source_family_independence`
asserts exactly this, including that the runtime gaps are `{WI-CR-003, WI-CR-004}`.

## Boundary invariants

World added no private aggregation, graph, persistence, authority, reasoning
runtime, status projector, or imperative Pack code. The status vocabulary is a
declarative JSON module (`modules/epistemic_status.json`); everything else is a
public ACE call. Dependency direction Domain → Intelligence → Core is preserved:
ACE learns no World label, and `ClaimGroundingKind` remains `{cited, inference}`.

`test_wi_cr_002_is_closed_by_a_domain_neutral_status_capability` replaces the old
strict-xfail, which asserted `"attributed" in ClaimGroundingKind` — satisfying
that would have pushed World vocabulary into the platform, so it was the wrong
close condition and was removed rather than made to pass.

## Verification

```
domain_packs/tests    42 passed, 2 xfailed   (baseline 33 passed, 3 xfailed)
ruff check scripts/ domain_packs/            All checks passed
git diff --check                             clean
```

Marketing regression control (unchanged source): `88 passed, 1 skipped`,
identical to baseline. Market is not forced to adopt any status vocabulary —
a template with no governing status set simply has no status-aware path, and
`resolve_epistemic_status_policy` fails closed rather than defaulting permissive.
