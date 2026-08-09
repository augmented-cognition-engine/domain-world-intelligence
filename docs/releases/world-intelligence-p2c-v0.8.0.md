# ACE World Intelligence 0.8.0 — P2C release record

**Release status:** released — tagged `v0.8.0`,
[GitHub Release published](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.8.0),
[public on PyPI](https://pypi.org/project/ace-domain-world-intelligence/0.8.0/) since
2026-08-09T18:33:44Z
**Root distribution:** `ace-domain-world-intelligence` 0.8.0 (inert, JSON-only Domain Pack)
**Connector distribution:** `ace-ext-world-federal-register-source` 0.1.0 (separate, optional)
**Platform requirement:** Python 3.12, `ace-core>=0.4.1,<0.5`
**Boundary:** governed read-only sensing and admission — no derivation, delivery, or external action

## Publication state

| Step | State |
|---|---|
| `v0.8.0` git tag | **done** — tag exists |
| GitHub Release | **done** — [published](https://github.com/augmented-cognition-engine/domain-world-intelligence/releases/tag/v0.8.0) |
| PyPI publication of `ace-domain-world-intelligence` 0.8.0 | **done** — [published](https://pypi.org/project/ace-domain-world-intelligence/0.8.0/) at 2026-08-09T18:33:44Z, via a publish-workflow rerun that succeeded |
| PyPI publication of `ace-ext-world-federal-register-source` 0.1.0 | **not part of this release**; the root publish workflow builds and uploads the root distribution only, and the connector remains unpublished |
| `ace-core` 0.4.1 | already public on PyPI |

The 0.8.0 root artifacts are installable from PyPI. A clean public install on Python 3.12 resolves
`ace-domain-world-intelligence==0.8.0` and `ace-core==0.4.1`; the connector distribution and import
package remain absent, by design.

## Scope

0.8.0 adds the first governed official-source sensing proof — P2C — to the World Intelligence
Domain Pack, and puts the distribution boundary into a publishable, machine-checked form.

**In scope:**

1. A second, additive, JSON-only activation pack,
   `domain_packs/world_intelligence_federal_register/` (ontology plus source mapping), that maps one
   exact Federal Register document.
2. A separately versioned executable connector, `adapters/federal_register_source/`, implementing
   the public ACE source-adapter protocol with an injected transport and no network client.
3. A hermetic consumer acceptance harness,
   `scripts/p2c_federal_register_live_acceptance.py`.
4. A publishable-identity release contract (`tests/test_release_contract.py`) plus CI and publish
   workflows that enforce it.
5. The distribution rename to `ace-domain-world-intelligence` and the connector rename to
   `ace-ext-world-federal-register-source`.

**Explicitly out of scope:** any change to `domain_packs/world_intelligence/`. Those files remain
byte-identical, so the frozen P2A/P2B PREPARED identities are not re-keyed by this release.

## What P2C proves

One exact capture produces, atomically and in order:

1. a source-acquisition receipt;
2. a canonical source snapshot;
3. one visibly LIVE Observation;
4. one exact-lineage LIVE Entity Snapshot; and
5. a LIVE source-admission receipt.

An exact replay and a fresh-service restart replay reopen those same records without invoking the
adapter or transport again. The adapter and transport are called exactly once across all three
paths. Five immutable LIVE records and one append receipt persist; no other record kind is present.

The reviewed source URI is
`https://www.federalregister.gov/api/v1/documents/2026-16197.json`. The adapter canonicalizes only
title, document number and type, publication date, agency, Federal Register page, the govinfo PDF,
and two explicit source-status labels; unmapped source fields cannot enter the entity projection.
FederalRegister.gov is recorded as **not the official legal edition**, and
`https://www.govinfo.gov/content/pkg/FR-2026-08-07/pdf/2026-16197.pdf` is retained as the
official-format verification reference. P2C does not interpret the rule, assess its impact, or
recommend a response.

## Artifacts

| Artifact | Identity |
|---|---|
| Root wheel | `ace_domain_world_intelligence-0.8.0-py3-none-any.whl` |
| Root sdist | `ace_domain_world_intelligence-0.8.0.tar.gz` |
| Root wheel SHA-256 | `ed088e4bef56fca95efd1cc7ac427fa83ed405a1eae414bde7fa3ce0a1f7c395` |
| Root sdist SHA-256 | `a91ec786ffc82f92a9d1250a85965fa6cd006f433a88f8692e82f7546fc917c5` |
| Connector wheel SHA-256 (reproducible) | `bcb568fbd1b6cd54bf806ce306ad9044dcae9df557bd1af3df0f1ff980ca0e9a` |

The root wheel carries 32 JSON resources across the two Domain Packs and nothing else. CI asserts
that it contains no `.py`, `.pyc`, `.so`, or `.pyd` file, no test package, no `scripts/` or
`adapters/` path, no connector import package, exactly one `Requires-Dist` (`ace-core>=0.4.1,<0.5`),
and `Requires-Python` of `>=3.12,<3.13`. Inert also means declarative: the project declares no
console scripts, no GUI scripts, and no entry points, so nothing executes on install or import.

Rebuild the connector reproducibly:

```bash
cd adapters/federal_register_source
SOURCE_DATE_EPOCH=1735689600 uv build --wheel
```

## Compatibility

- **Python:** 3.12 only (`>=3.12,<3.13`). CI asserts the synced interpreter is 3.12.
- **ACE Core:** `>=0.4.1,<0.5`. 0.4.0 and 0.5.0 are outside the window by contract test.
- **Connector:** optional, separately versioned at 0.1.0, on the same Python and `ace-core` windows.
  It is not a runtime dependency of the Domain Pack and no extra reintroduces it. It is referenced
  only by the local `dev` dependency group and a `[tool.uv.sources]` path entry, neither of which is
  published metadata, so neither reaches an installing consumer.
- **Frozen identities:** unchanged from 0.7.0 for everything under
  `domain_packs/world_intelligence/`.

### Identity re-keying in this release

The connector rename and reproducible-build change re-keyed every P2C record whose identity derives
from the exact artifact. This is the contract working as designed: the acceptance run failed closed
with `P2C LIVE identity projection changed from its exact pin` until the pin was regenerated. The
prior connector digest came from a non-reproducible build — two builds of identical source produced
different digests — so no outside reader could have reproduced it. The captured canonical payload
digest, the `domain_activation` ID, and the transaction ID are unchanged, because neither the
captured content nor the activation changed.

Superseded identities are retained for audit continuity in
[`../audits/world-intelligence-p2c-federal-register-live-2026-08-07.md`](../audits/world-intelligence-p2c-federal-register-live-2026-08-07.md).

## Evidence and reproducibility

Current P2C identities:

| Material | Exact identity or digest |
|---|---|
| Additive compiled pack | `pack_ir:1847032fc5301bba9b6f85d3d091400d` |
| Ingress request | `live_source_ingress_request:f4d6fca0e39a0fe3b2a2887be757c48b` |
| Acquisition receipt | `source_acquisition_receipt:7481dbdbe8d956b4365c0f1082644e76` |
| Source snapshot | `source_snapshot:676fc90db2fe007feeeb1444cfc69e49` |
| LIVE Observation | `observation:b316859307d82d5b6696783f715cacc1` |
| LIVE Entity Snapshot | `entity_snapshot:25686860ee9a3506d753412685328a4e` |
| Admission receipt | `live_source_admission_receipt:91fc36ce6084aa1bb5a3e1130baa4f76` |
| Activation revision | `activation_revision:efa443d7d3d888c8bbfa3176cf0edd86` |
| Captured canonical payload | `sha256:5310fab9696e287eff47e21dc70cab11ad1e2d82f9249532e4586f3f6c5fb06e` |

Carried forward unchanged from earlier packets:

| Material | Exact identity |
|---|---|
| P2A compiled pack | `pack_ir:683de57a71669814e507d07d65a109db` |
| Case | `case:412426eee708d56f6bda931ccf9e5d8b` |
| Public demo Brief | `brief:25d8232c9bfa27050bdcb160fb75f06c` |
| Case-bound Brief | `brief:8fb3173069eca502652b1c9c004c92e6` |

### Reproduce it

From a checkout, with the connector source on the path:

```bash
export REPO="$PWD"
export ACE=/path/to/ace-core
export PYTHONPATH="$REPO:$REPO/adapters/federal_register_source/src:$ACE"
export PY="$ACE/.venv/bin/python"

$PY -m pytest -q                                          # 81 passed
$PY -m pytest adapters/federal_register_source/tests -q   # 24 passed
$PY scripts/p2c_federal_register_live_acceptance.py
```

Or through the locked environment, as CI does:

```bash
uv sync --frozen --no-install-project
uv run --no-sync pytest
uv run --no-sync pytest tests/test_release_contract.py
uv run --no-sync pytest adapters/federal_register_source/tests
```

Accepted totals as of 2026-08-08:

| Gate | Result |
|---|---|
| Complete World suite, including every frozen P2A/P2B packet and P2C | **81 passed** |
| Connector fail-closed unit suite | **24 passed** |
| P2C lifecycle and frozen-identity subset | 5 passed |
| ACE governed LIVE ingress, runtime-use/precondition, kernel-boundary regression | 61 passed, 2 skipped |
| Static quality gate over all new P2C Python | passed |

CI additionally builds the root sdist and wheel, validates metadata with `twine check --strict`,
inspects the exact wheel payload, and installs the wheel into a clean `--no-config` virtual
environment against the public `ace-core` 0.4.1, asserting from outside the checkout that the pack
data resolves from site-packages and that the connector import package and distribution are absent.

After publication, an independent clean install from public PyPI on Python 3.12 resolved
`ace-domain-world-intelligence==0.8.0` and `ace-core==0.4.1`. Inspection of the installed
distribution found exactly 32 JSON Domain Pack resources, no `.py`, `.pyc`, or `.so` resource, and
no `ace_world_federal_register_source` import package.

The public demo reproduces `case:412426eee708d56f6bda931ccf9e5d8b` and
`brief:25d8232c9bfa27050bdcb160fb75f06c`, and its two artifacts are byte-identical across runs.

## Excluded capabilities

This release does not include, and must not be described as including:

- **Live news monitoring.** The conformance transport is a recorded, network-free response from the
  reviewed official API URI. The test suite performs no network access. The fixed `1.1.1.1` address
  is a conformance attestation fixture, not a claim about FederalRegister.gov DNS.
- **A network transport.** The connector accepts only an injected, separately reviewed transport. A
  production host must supply one that enforces address validation and rebinding protection
  throughout use.
- **Derivation from the LIVE capture.** No Signal, Shift, Brief, route, Decision, Outcome, feedback,
  learning event, monitor, or schedule is produced from the admitted Observation.
- **Legal interpretation.** P2C does not determine legal effect, interpret the rule, or recommend a
  response.
- **Autonomous or external action.** No publishing, delivery, persuasion, voter targeting, or action
  outside the invoking process. No scheduling and no background execution.
- **Production-readiness or benchmark claims.** The counts in this document describe these frozen
  scenarios. They are not capacity, accuracy, or scale benchmarks.
- **Truth determination.** Provenance structure and epistemic status are not claims that ACE has
  established objective truth. Independence is only as strong as the lineage admitted to the graph.

## Installation

The inert Domain Pack is public on
[PyPI](https://pypi.org/project/ace-domain-world-intelligence/0.8.0/). Consumers install it with
either tool:

```bash
uv add "ace-domain-world-intelligence==0.8.0"
```

```bash
pip install "ace-domain-world-intelligence==0.8.0"
```

Both resolve `ace-core>=0.4.1,<0.5` and **neither installs the connector**. Consumers who want the
P2C sensing path install `ace-ext-world-federal-register-source` deliberately and separately once it
has its own release, review it on its own boundary, and supply their own reviewed transport. This
0.8.0 workflow did not publish the connector. Development and acceptance-harness instructions for a
source checkout remain in the [README](../../README.md).

## Remaining gate

**Cross-domain GI2 is open.** It stays open until a clean-install journey is reproduced across ACE
Core plus **at least two** domain packs — that is, until a consumer starting from an empty
environment can install Core and two independently released packs from their published artifacts and
run each pack's accepted proofs without a source checkout. This release proves the single-pack
clean-install journey in CI for `ace-domain-world-intelligence` against public `ace-core` 0.4.1; the
second pack is not yet part of that evidence. No 0.8.0 claim depends on GI2 being closed, and this
release does not close it.

## Next boundary

Add a separately reviewed, opt-in network transport for the exact source-adapter contract, then
exercise P2D multi-source conflict and correction with LIVE inputs. Neither step may add publishing,
delivery, persuasion, or other external-action authority, and neither may weaken the prepared replay
or the trust labels demonstrated here.

## References

- [`../../README.md`](../../README.md) — install and consumption model
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — version history
- [`world-intelligence-public-demo-v0.7.0.md`](world-intelligence-public-demo-v0.7.0.md) — public proof surface
- [`../audits/world-intelligence-p2c-federal-register-live-2026-08-07.md`](../audits/world-intelligence-p2c-federal-register-live-2026-08-07.md) — P2C admission proof
- [`../audits/world-intelligence-p2a-2026-08-06.md`](../audits/world-intelligence-p2a-2026-08-06.md) and [`../audits/world-intelligence-p2b-2026-08-06.md`](../audits/world-intelligence-p2b-2026-08-06.md) — frozen pack and scenario proofs
