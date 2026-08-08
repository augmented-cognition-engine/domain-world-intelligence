# ACE World Intelligence

ACE World Intelligence is an inert Domain Pack and reference solution for making sense of a
changing public issue. It separates admitted records, attributed claims, corroboration, disputes,
ACE inference, unknowns, and conditional scenarios instead of presenting one opaque summary as
truth.

This repository is a consumer of the public ACE Core + Intelligence distribution. It does not own
a reasoning runtime, graph, state store, authority system, detector engine, or feedback loop.

## Product loop

```text
authorized public sources
  → attributable Observations and entity state
  → event, actor, institution, issue, policy, claim, and source graph
  → meaningful Signal or Shift
  → cited reality Brief
  → user correction or disposition
  → governed Outcome and feedback
```

## Current milestone

P2A proved that a materially different, JSON-only World Intelligence pack compiles through the
unchanged ACE pack compiler (`pack_ir:683de57a71669814e507d07d65a109db`, seven conformance tests).

P2B freezes the golden 72-hour public-issue scenario: the synthetic, hermetic, redistributable
`meridia_reservoir_release_72h` packet. It pins eight timestamped source records across four
provenance families (including two syndicated copies and a publisher correction), a
nineteen-entity graph exercising all eleven relation types, an official status change, four
material categorical shifts plus one numeric shift, one runtime-routable signal, and an exact
Reality Brief whose seventeen statements carry all seven epistemic statuses. Nine negative
vectors fail closed, from missing attribution through divergent replay.

The additive P2B PREPARED replay now compiles and activation-binds detection `v1alpha2`, admits all
eight source records as PREPARED Observations, reproduces all five Shifts, emits only the intended
four Signals, and resolves all four persona routes. The claim-corroboration Shift is represented
through ACE's generic resource-set admission without inventing a Signal. The frozen scenario and
default `0.1.0` pack identities remain unchanged.

The replay also freezes those developments into ACE's public immutable Case contract. Four routed
Signals plus the non-routed corroboration Shift form one five-member Case that transitively binds
the complete 28-resource scenario closure. World supplies the case type and purpose; ACE owns the
identity, temporal validation, lineage resolution, admission, and replay.

An additive Case-bound packet now consumes ACE's public `CaseBriefSynthesisService` over that exact
Case. It admits the routed derivations through ACE's durable PREPARED ledger without duplicating any
source record, derives one compatible template and persona scope from the four exact attention
receipts, freezes all 26 closure resources as Core context, and emits one governed, grounded,
atomically persisted, deterministically replayable Reality Brief that carries the Case in lineage:
`brief:8fb3173069eca502652b1c9c004c92e6`. `WI-CR-005` is closed.

Per-statement epistemic status (`WI-CR-002`) and derivation-family independence (`WI-CR-003`) are
now closed through public, domain-neutral ACE contracts. World declares its seven-label vocabulary;
ACE validates each statement against its exact supports and proves that `corroborated` spans at least
two admitted derivation families. The Ledger report and the independent Basin gauge satisfy that
rule, while Coastal Wire and Harborview collapse into the Ledger root despite being different
publishers. The durable projection discloses the exact root-to-member partition used by the proof.
Supersession-impact enumeration (`WI-CR-004`) is now closed too, so **no public-platform contract
request remains open**. When a record is superseded, ACE enumerates exactly what depended on it,
directly and transitively, and appends that answer as an additive immutable record. Both frozen
corrections are exercised: the Ledger correction reaches 11 resources and 9 Brief claims, the Order
supersession reaches 7 resources and 5 claims, and each projection discloses the resources it found
**unaffected** so the boundary is visible rather than inferred. Impact means dependency, not
falsehood — the prior Brief keeps its exact identity, replays byte-identically, and is never
rewritten.

P2C adds the first official-source sensing proof without mutating that frozen pack. A separate,
JSON-only activation pack maps one exact Federal Register document, while a separately versioned,
transport-injected adapter validates the exact source, artifact, URI, network attestations, and
closed payload. ACE then admits one acquisition receipt, source snapshot, visibly LIVE Observation,
LIVE Entity Snapshot, and admission receipt as one atomic transaction. Exact replay and
fresh-service restart replay perform no second capture.

The conformance transport is a recorded, network-free response from the reviewed official API URI;
it proves the governed LIVE contract and deterministic admission, not that the test suite performed
a live network request. FederalRegister.gov is explicitly labeled as not the official legal edition,
and the corresponding `govinfo.gov` PDF is retained as the official-format verification reference.
No Signal, Shift, Brief, Decision, Outcome, feedback, delivery, publishing, persuasion, or external
action is created.

## Public proof surface

Generate a self-contained visual Reality Brief and its exact machine-readable backing data:

```bash
PYTHONPATH=/path/to/domain-world-intelligence:/path/to/ace-core \
  /path/to/ace-core/.venv/bin/python scripts/public_demo.py
```

The command writes `artifacts/public-demo/index.html` and `demo-data.json`. It runs the accepted
independence and correction-impact harnesses, refuses to render if the pinned release proof drifts,
and uses no external web assets. The page is explicitly a synthetic PREPARED / FROZEN scenario,
not a live news product. See
[`docs/releases/world-intelligence-public-demo-v0.7.0.md`](docs/releases/world-intelligence-public-demo-v0.7.0.md)
for the release boundary and exact identities.

Run the acceptance proofs alongside an ACE checkout or installation.

This repository ships an **inert Domain Pack**. The Federal Register connector is a separately
versioned executable artifact (`ace-ext-world-federal-register-source`) with its own review
boundary, so it is not a dependency of the pack and must be put on the path explicitly. Omit it and
the P2C modules skip rather than fail.

```bash
export REPO=/path/to/domain-world-intelligence
export ACE=/path/to/ace-core
export PYTHONPATH="$REPO:$REPO/adapters/federal_register_source/src:$ACE"
export PY="$ACE/.venv/bin/python"

# Complete suite, including every frozen P2A/P2B packet and P2C: 81 passed
$PY -m pytest -q

# Connector fail-closed unit suite: 24 passed
$PY -m pytest adapters/federal_register_source/tests -q

# Individual acceptance harnesses
$PY scripts/p2a_compile_acceptance.py
$PY scripts/p2b_scenario_acceptance.py --negative
$PY scripts/p2b_prepared_replay.py
$PY scripts/p2b_case_brief.py
$PY scripts/p2b_status_case_brief.py
$PY scripts/p2b_independent_case_brief.py
$PY scripts/p2c_federal_register_live_acceptance.py
```

Expected totals as of 2026-08-08: complete suite `81 passed`, connector suite `24 passed`. The
public demo reproduces `case:412426eee708d56f6bda931ccf9e5d8b` and
`brief:25d8232c9bfa27050bdcb160fb75f06c`, and its two artifacts are byte-identical across runs.

The exact identities, negative cases, and artifact proofs are recorded in
[`docs/audits/world-intelligence-p2a-2026-08-06.md`](docs/audits/world-intelligence-p2a-2026-08-06.md)
and
[`docs/audits/world-intelligence-p2b-2026-08-06.md`](docs/audits/world-intelligence-p2b-2026-08-06.md),
with the interpreter and Case proof in
[`docs/audits/world-intelligence-p2b-prepared-replay-2026-08-07.md`](docs/audits/world-intelligence-p2b-prepared-replay-2026-08-07.md)
and the governed Case-bound Brief proof in
[`docs/audits/world-intelligence-p2b-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-case-brief-2026-08-07.md),
the per-statement status proof in
[`docs/audits/world-intelligence-p2b-status-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-status-case-brief-2026-08-07.md),
and the independent-corroboration proof in
[`docs/audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md`](docs/audits/world-intelligence-p2b-independent-case-brief-2026-08-07.md).
The governed official-source admission proof is recorded in
[`docs/audits/world-intelligence-p2c-federal-register-live-2026-08-07.md`](docs/audits/world-intelligence-p2c-federal-register-live-2026-08-07.md).

## Guardrails

- A publisher is not assigned a hidden universal truth score.
- Repetition and syndication are not independent corroboration.
- Claims retain attribution.
- Corrections append state rather than rewriting history.
- Inference and scenario material remain explicitly labeled.
- Persona routing never changes an evidence status.
- No political persuasion, voter targeting, autonomous publishing, or external action.

Next: add a separately reviewed, opt-in network transport for the exact source-adapter contract,
then exercise P2D multi-source conflict and correction with LIVE inputs. Neither step may add
publishing, delivery, persuasion, or other external-action authority.
