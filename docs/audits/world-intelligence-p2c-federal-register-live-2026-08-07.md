# World Intelligence P2C — governed Federal Register LIVE admission

**Status:** verified consumer-side contract on 2026-08-07  
**Release candidate:** `ace-domain-world-intelligence` 0.8.0 (renamed from `ace-ext-world-intelligence` on 2026-08-08)  
**Source:** Federal Register document `2026-16197`  
**Network claim:** none; deterministic conformance uses a recorded injected retrieval

## Outcome

World Intelligence now proves the first governed official-source sensing boundary through public
ACE Core + Intelligence contracts. One exact capture produces, atomically and in order:

1. a source-acquisition receipt;
2. a canonical source snapshot;
3. one visibly LIVE Observation;
4. one exact-lineage LIVE Entity Snapshot; and
5. a LIVE source-admission receipt.

An exact replay and a fresh-service restart replay reopen those same records without invoking the
adapter or transport again. The acceptance creates no Signal, Shift, Brief, route, delivery,
Decision, Outcome, feedback, learning event, monitor, schedule, publication, persuasion, or other
external action.

## Architecture boundary

P2C does not edit ACE Core and does not put executable code in a Domain Pack.

- `domain_packs/world_intelligence_federal_register/` is a two-module, JSON-only additive activation
  pack: ontology plus source mapping.
- `adapters/federal_register_source/` is a separately versioned executable package implementing the
  public source-adapter protocol.
- `scripts/p2c_federal_register_live_acceptance.py` is the hermetic consumer acceptance harness.
- The existing `domain_packs/world_intelligence/` files remain byte-identical, so P2A/P2B PREPARED
  identities are not re-keyed.

The adapter contains no network client. It accepts only an injected reviewed transport and validates
one exact artifact identity, source type, HTTPS URI, empty redirect chain, no credentials, exact
HTTP 200 `application/json`, bounded strict JSON, globally routable resolved and connected address
attestations, DNS-rebinding protection, and monotonic operation times.

## Source and legal-status handling

The reviewed URI is:

`https://www.federalregister.gov/api/v1/documents/2026-16197.json`

The adapter canonicalizes only title, document number/type, publication date, agency, Federal
Register page, govinfo PDF, and two explicit source-status labels. Unmapped source fields cannot
enter the entity projection.

FederalRegister.gov is recorded as **not the official legal edition**. The mapped
`https://www.govinfo.gov/content/pkg/FR-2026-08-07/pdf/2026-16197.pdf` is retained as the
official-format verification reference. P2C does not interpret the rule, assess its impact, or
recommend a response.

## Deterministic evidence

| Material | Exact identity or digest |
|---|---|
> **Re-keyed 2026-08-08 by the connector rename.** The connector distribution moved from
> `ace-world-federal-register-source` to `ace-ext-world-federal-register-source` under the
> `ace-domain-*` / `ace-ext-*` convention, and its build was made reproducible. Because the exact
> artifact identity is bound into the governed capture, every record whose identity derives from it
> re-keyed. This is the contract working as designed: the acceptance run failed closed with
> `P2C LIVE identity projection changed from its exact pin` until the pin was regenerated.
>
> The captured canonical payload digest, the `domain_activation` ID, and the transaction ID are
> **unchanged**, because the captured content and the activation did not change — only the artifact
> bound to the capture.
>
> The superseded identities are recorded below for audit continuity. The prior adapter digest
> `6b794c47…9b1f97` came from a **non-reproducible** build: two builds of identical source produced
> different digests, so no outside reader could ever have reproduced it. The replacement is pinned
> under `SOURCE_DATE_EPOCH=1735689600` and verified byte-identical across repeated builds.

| Material | Exact identity or digest |
|---|---|
| Additive compiled pack | `pack_ir:1847032fc5301bba9b6f85d3d091400d` |
| World 0.8.0 wheel SHA-256 | `138603779764e9a160f4c6193af59d882c85928b152fb6d5454afa3cfb91bf46` |
| Adapter wheel SHA-256 (reproducible) | `bcb568fbd1b6cd54bf806ce306ad9044dcae9df557bd1af3df0f1ff980ca0e9a` |
| Ingress request | `live_source_ingress_request:f4d6fca0e39a0fe3b2a2887be757c48b` |
| Acquisition receipt | `source_acquisition_receipt:7481dbdbe8d956b4365c0f1082644e76` |
| Source snapshot | `source_snapshot:676fc90db2fe007feeeb1444cfc69e49` |
| LIVE Observation | `observation:b316859307d82d5b6696783f715cacc1` |
| LIVE Entity Snapshot | `entity_snapshot:25686860ee9a3506d753412685328a4e` |
| Admission receipt | `live_source_admission_receipt:91fc36ce6084aa1bb5a3e1130baa4f76` |
| Activation revision | `activation_revision:efa443d7d3d888c8bbfa3176cf0edd86` |
| Captured canonical payload (unchanged) | `sha256:5310fab9696e287eff47e21dc70cab11ad1e2d82f9249532e4586f3f6c5fb06e` |

Superseded identities from the original 2026-08-07 run, retained for audit continuity:

| Material | Superseded identity |
|---|---|
| Adapter wheel SHA-256 | `6b794c472161bbe522632fc5f323a93c412e6b6a27dd8837a7c4f674e49b1f97` (non-reproducible) |
| Acquisition receipt | `source_acquisition_receipt:869bfef33976584edbc1841b0f305353` |
| Source snapshot | `source_snapshot:9e01bbd2e58ddbd6fef667430fe45d04` |
| LIVE Observation | `observation:277c189b26023bc7d12b334c74b7b39f` |
| LIVE Entity Snapshot | `entity_snapshot:8c520d686df270dc17e3f9023d6c6edc` |
| Admission receipt | `live_source_admission_receipt:e90b80ab934eff6b4729e5a6e7e30c64` |
| Activation revision | `activation_revision:33dfed878ed17af0e966e2968848adfe` |

Rebuild the connector reproducibly with:

```bash
cd adapters/federal_register_source
SOURCE_DATE_EPOCH=1735689600 uv build --wheel
```

The adapter and transport are invoked exactly once across first admission, exact replay, and
fresh-service restart replay. Five immutable LIVE records and one append receipt persist; no other
record kind is present.

## Verification

- Adapter fail-closed unit suite: **24 passed**.
- P2C lifecycle/frozen-identity suite: **5 passed**.
- Complete World suite, including every frozen P2A/P2B packet: **81 passed**.
- ACE governed LIVE ingress, runtime-use/precondition, and kernel-boundary regression: **61 passed,
  2 skipped**.
- Static quality gate over all new P2C Python: **passed**.

## Honest limitations and next boundary

The accepted response is recorded fixture material obtained from the reviewed official API. The
normal test suite performs no network access, and the fixed `1.1.1.1` address is a conformance
attestation fixture—not a claim about FederalRegister.gov DNS. A production host must supply and
review a real transport that enforces address validation and rebinding protection throughout use.

This packet proves sensing and governed admission only. It does not promote the Observation into a
Signal or Shift, synthesize a Brief, establish independent corroboration, determine legal effect,
or authorize publishing. Those remain separate, governed steps.
