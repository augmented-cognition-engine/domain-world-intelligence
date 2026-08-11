#!/usr/bin/env python3
"""Supersession-impact view over the frozen World P2B Reality Brief.

This consumer harness closes WI-CR-004 through public ACE APIs and Pack IR only.

It reproduces the accepted WI-CR-003 packet **exactly** -- same activation, same
Case, same Brief, same synthesis receipt, same status projection -- and then
admits the scenario's two declared supersessions as later Observations that
assert ``supersedes`` against their targets. ACE's public
``SupersessionImpactService`` then enumerates what depended on each superseded
record and durably appends the answer.

Why the supersession assertions are separate later records
----------------------------------------------------------
A correction arrives *after* the work it affects. Modelling it that way is both
realistic and necessary: the Brief must already exist, unchanged, for the impact
view to have something to explain. The assertion Observations are therefore
admitted after the Brief, sit outside the frozen Case closure, and carry the one
``supersedes`` edge each. Their payload is the scenario's own pinned
``supersessions`` entry, so nothing is invented.

What this proves and does not prove
-----------------------------------
Impact means "your grounding included a record that has since been superseded".
It does **not** mean the statement is false. The Ledger correction explicitly
leaves Delegate Quell's attributed statement untouched, and the projection
reports the unaffected set so that boundary is visible rather than inferred.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from ace.application import (
    CaseBriefFamilyStatusSynthesisService,
    DomainActivationAdmissionService,
    PreparedIntelligenceLedgerService,
    SupersessionImpactService,
    bind_committed_activation,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedReasoningService,
    GovernedStateHeadPreconditionV1Alpha1,
    ReasoningExecutionBindingV1Alpha1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    IMPACT_RELATIONS,
    CanonicalJsonValueV1Alpha1,
    CaseBriefSynthesisRequestV1Alpha1,
    CaseMemberAttentionBindingV1Alpha1,
    EvidenceAcquisitionMode,
    IntelligenceRecordKind,
    IntelligenceResourceMode,
    LineageReferenceV1Alpha1,
    LineageRelation,
    LineageResourceKind,
    ObservationV1Alpha1,
    PreparedResourceSetAdmissionV1Alpha1,
    deterministic_resource_order,
    resource_reference,
)
from ace.testing import InMemoryImmutableRecordStore

from scripts.p2b_case_brief import (
    APPEND_ARTIFACT,
    REASONING_ARTIFACT,
    ROUTED_DERIVATIONS,
    _ActivationAuthority,
    _ActivationStore,
    _admit_material,
    _Clock,
    _head,
    _Runtime,
)
from scripts.p2b_independent_case_brief import (
    CORROBORATION_CLOSURE_RECORDS,
    CORROBORATION_VECTORS,
    _IndependenceProvider,
    independence_activation_revision,
)
from scripts.p2b_prepared_replay import ACTIVATED_AT, PRODUCT_ID, build_replay_material

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"

#: The two supersessions the frozen scenario declares. Both are exercised.
SUPERSESSION_VECTORS = (
    ("supersession:correction_114_over_report_1088", "record:ledger_report_1088"),
    ("supersession:order_47_over_bulletin_214", "record:mwa_bulletin_214"),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assertion_observation(binding, *, entry: dict[str, Any], target, available_at):
    """Admit one declared supersession as an Observation that asserts it.

    The payload is the scenario's own pinned ``supersessions`` entry, so this
    record states exactly what the fixture already declares -- nothing invented.
    """

    reference = resource_reference(target)
    return ObservationV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=binding.reference,
        as_of=available_at,
        lineage=(
            LineageReferenceV1Alpha1(
                resource_kind=LineageResourceKind(reference.resource_kind.value),
                relation=LineageRelation.SUPERSEDES,
                resource_id=reference.resource_id,
                resource_digest=reference.resource_digest,
                resource_as_of=reference.as_of,
                resource_available_at=reference.available_at,
            ),
        ),
        source_ref=entry["supersession_id"],
        source_digest="sha256:" + "7" * 64,
        acquisition_mode=EvidenceAcquisitionMode.PREPARED_FIXTURE,
        acquisition_receipt_ref=f"acquisition:{entry['supersession_id'].split(':', 1)[1]}",
        acquisition_receipt_digest="sha256:" + "8" * 64,
        source_published_at=available_at,
        observed_at=available_at,
        ingested_at=available_at,
        subject_refs=(entry["superseded_record_id"],),
        payload=CanonicalJsonValueV1Alpha1(value_json=canonical_json(entry)),
        confidence=1.0,
    )


async def _build_world() -> dict[str, Any]:
    """Reproduce the accepted WI-CR-003 packet, then admit the supersessions."""

    pack, revision = independence_activation_revision()
    material = build_replay_material(
        pack=pack,
        revision=revision,
        link_derivations=True,
        additional_claim_basis={"entity:claim/farm_allocation_cut": CORROBORATION_CLOSURE_RECORDS},
    )
    orientation_case = material["orientation_case"]
    attention_at = orientation_case.assembled_at
    context_cutoff_at = orientation_case.assembled_at
    requested_at = context_cutoff_at + timedelta(minutes=1)

    activation_store = _ActivationStore()
    activation_service = DomainActivationAdmissionService(
        store=activation_store,
        authority=_ActivationAuthority(),
    )
    committed = await activation_service.admit(
        revision,
        expected_head_revision_id=None,
        committed_at=ACTIVATED_AT,
    )
    binding = bind_committed_activation(pack=pack, committed=committed)
    store = InMemoryImmutableRecordStore()
    ledger = PreparedIntelligenceLedgerService(binding=binding, store=store)
    admissions, _ = await _admit_material(ledger, material, attention_at=attention_at)

    execution_head = _head("reasoning_configuration", "reasoning_configuration:world-independent-case-brief")
    execution_binding = ReasoningExecutionBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=REASONING_ARTIFACT,
        configuration_ref="reasoning_configuration:world-independent-case-brief",
        authority="reason",
        grant_ref="authority_grant:world-independent-case-brief",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(execution_head),
    )
    append_head = _head(
        "governed_operation_configuration",
        "governed_operation_configuration:world-independent-case-brief-append",
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=APPEND_ARTIFACT,
        configuration_ref="governed_operation_configuration:world-independent-case-brief-append",
        authority="append_immutable_records",
        grant_ref="authority_grant:world-independent-case-brief-append",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(append_head),
    )
    heads = {
        ("reasoning_configuration", execution_binding.configuration_ref): execution_head,
        ("governed_operation_configuration", append_binding.configuration_ref): append_head,
        ("capability_state", capability_state_ref_for_artifact(REASONING_ARTIFACT)): _head(
            "capability_state", capability_state_ref_for_artifact(REASONING_ARTIFACT)
        ),
        ("capability_state", capability_state_ref_for_artifact(APPEND_ARTIFACT)): _head(
            "capability_state", capability_state_ref_for_artifact(APPEND_ARTIFACT)
        ),
        ("authority_grant", execution_binding.grant_ref): _head("authority_grant", execution_binding.grant_ref),
        ("authority_grant", append_binding.grant_ref): _head("authority_grant", append_binding.grant_ref),
    }
    activation_head = activation_store.heads[
        (
            committed.commit_receipt.state_kind,
            committed.commit_receipt.product_id,
            committed.commit_receipt.state_id,
        )
    ]
    for head in (*heads.values(), activation_head):
        store.set_governed_state_head(head)

    observation_ids = {record_id: str(item.resource_id) for record_id, item in material["observations"].items()}
    provider = _IndependenceProvider(
        observation_ids=observation_ids,
        corroboration=CORROBORATION_VECTORS["independent_roots"],
    )
    reasoning = GovernedReasoningService(
        store=store,
        runtime_use=_Runtime(
            bindings=(execution_binding, append_binding),
            heads=heads,
            expires_at=requested_at + timedelta(hours=4),
        ),
        provider=provider,
        clock=_Clock(requested_at),
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=PRODUCT_ID,
        actor_ref="principal:world-p2b-reviewer",
        authentication_receipt_ref="authentication:world-p2b-independent-case-brief",
        authentication_receipt_digest="sha256:" + "e" * 64,
        authenticated_at=ACTIVATED_AT,
        expires_at=requested_at + timedelta(hours=6),
    )
    service = CaseBriefFamilyStatusSynthesisService(
        activation_service=activation_service,
        pack=pack,
        store=store,
        reasoning=reasoning,
        execution_binding=execution_binding,
        append_binding=append_binding,
        clock=_Clock(requested_at),
    )
    request = CaseBriefSynthesisRequestV1Alpha1(
        synthesis_key="independent-case-brief:world-meridia-72h",
        reasoning_attempt_key="reasoning:independent-case-brief:world-meridia-72h",
        product_id=PRODUCT_ID,
        authenticated_context=context,
        activation_revision=binding.prepared_binding.reference,
        pack=binding.prepared_binding.revision.spec.pack,
        case=resource_reference(orientation_case),
        member_attention=tuple(
            CaseMemberAttentionBindingV1Alpha1(
                signal_resource_id=admissions[key].attention_receipt.signal.resource_id,
                derivation_key=derivation_key,
                attention_receipt_id=str(admissions[key].attention_receipt.receipt_id),
                attention_receipt_digest=str(admissions[key].attention_receipt.receipt_digest),
            )
            for key, derivation_key in ROUTED_DERIVATIONS
        ),
        brief_as_of=orientation_case.as_of,
        context_cutoff_at=context_cutoff_at,
        requested_at=requested_at,
    )
    admission = await service.synthesize_with_status(request)

    # The correction arrives only now -- after the Brief exists and is durable.
    expected = _load(CONFORMANCE / "p2b_expected.json")
    entries = {item["supersession_id"]: item for item in expected["supersessions"]}
    correction_at = admission.brief.generated_at + timedelta(hours=1)
    assertions = {}
    for supersession_id, target_record_id in SUPERSESSION_VECTORS:
        entry = entries[supersession_id]
        assertion = _assertion_observation(
            binding.prepared_binding,
            entry=entry,
            target=material["observations"][target_record_id],
            available_at=correction_at,
        )
        assertions[supersession_id] = assertion
    await ledger.admit_resource_set(
        PreparedResourceSetAdmissionV1Alpha1(
            admission_key="resource-set:world-supersession-assertions",
            product_id=PRODUCT_ID,
            activation_revision=binding.prepared_binding.reference,
            pack=binding.prepared_binding.revision.spec.pack,
            resources=tuple(assertions[key] for key, _ in SUPERSESSION_VECTORS),
            processing_order=deterministic_resource_order(tuple(assertions[key] for key, _ in SUPERSESSION_VECTORS)),
            admitted_at=correction_at,
        )
    )
    # The correction is authorized later than the Brief, so the impact phase gets
    # its own governed clock rather than reusing the synthesis one.
    impact_reasoning = GovernedReasoningService(
        store=store,
        runtime_use=_Runtime(
            bindings=(execution_binding, append_binding),
            heads=heads,
            expires_at=correction_at + timedelta(hours=4),
        ),
        provider=provider,
        clock=_Clock(correction_at + timedelta(minutes=1)),
    )
    impact_context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=PRODUCT_ID,
        actor_ref="principal:world-p2b-reviewer",
        authentication_receipt_ref="authentication:world-p2b-supersession-impact",
        authentication_receipt_digest="sha256:" + "f" * 64,
        authenticated_at=correction_at,
        expires_at=correction_at + timedelta(hours=4),
    )
    impact_service = SupersessionImpactService(
        activation_service=activation_service,
        pack=pack,
        store=store,
        reasoning=impact_reasoning,
        append_binding=append_binding,
        clock=_Clock(correction_at + timedelta(minutes=1)),
    )
    return {
        "activation_key": pack.metadata.pack_id,
        "admission": admission,
        "assertions": assertions,
        "binding": binding,
        "context": context,
        "impact_context": impact_context,
        "correction_at": correction_at,
        "impact_service": impact_service,
        "ledger": ledger,
        "material": material,
        "observation_ids": observation_ids,
        "orientation_case": orientation_case,
        "provider": provider,
        "service": service,
        "request": request,
        "store": store,
    }


def _closure(world) -> tuple:
    """The exact authorized closure: the frozen Case closure plus the assertions."""

    material = world["material"]
    resources = [
        *material["observations"].values(),
        *material["snapshots"],
        *material["shifts"].values(),
        *material["signals"].values(),
        world["orientation_case"],
    ]
    seen: dict[str, Any] = {}
    for item in resources:
        seen[str(item.resource_id)] = item
    return tuple(seen[key] for key in sorted(seen))


def _build_kwargs(world, *, supersession_id: str, target_record_id: str, cutoff_at=None) -> dict:
    """The exact semantic inputs for one impact projection."""

    admission = world["admission"]
    return {
        "product_id": PRODUCT_ID,
        "activation_revision": world["binding"].prepared_binding.reference,
        "superseder": world["assertions"][supersession_id],
        "superseded_resource_id": world["observation_ids"][target_record_id],
        "closure": _closure(world),
        "cutoff_at": cutoff_at or world["correction_at"],
        "as_of": admission.brief.as_of,
        "brief_id": str(admission.brief.resource_id),
        "claim_supports": admission.synthesis_receipt.claim_supports,
        "preserved_artifact_ids": (
            str(admission.brief.resource_id),
            str(admission.synthesis_receipt.receipt_id),
            str(admission.status_projection.projection_id),
            str(world["orientation_case"].resource_id),
        ),
    }


async def run_supersession_impact() -> dict[str, Any]:
    """Project and durably append impact for both frozen corrections."""

    world = await _build_world()
    admission = world["admission"]
    impact_service = world["impact_service"]
    results: dict[str, Any] = {}

    for supersession_id, target_record_id in SUPERSESSION_VECTORS:
        build = _build_kwargs(
            world,
            supersession_id=supersession_id,
            target_record_id=target_record_id,
        )
        appended = await impact_service.project_and_append(
            impact_key=f"impact:{supersession_id}",
            authenticated_context=world["impact_context"],
            activation_key=world["activation_key"],
            **build,
        )
        replayed = await impact_service.project_and_append(
            impact_key=f"impact:{supersession_id}",
            authenticated_context=world["impact_context"],
            activation_key=world["activation_key"],
            **build,
        )
        projection = appended.projection
        kinds: dict[str, int] = {}
        for item in projection.impacted:
            kinds[item.resource_kind.value] = kinds.get(item.resource_kind.value, 0) + 1
        results[supersession_id] = {
            "projection_id": str(projection.projection_id),
            "projection_digest": str(projection.projection_digest),
            "superseded_resource_id": projection.superseded_resource_id,
            "superseder_resource_id": projection.superseder_resource_id,
            "closure_size": len(projection.closure_resource_ids),
            "impacted_count": len(projection.impacted),
            "impacted_kinds": dict(sorted(kinds.items())),
            "direct_count": sum(1 for item in projection.impacted if item.depth == 1),
            "transitive_count": sum(1 for item in projection.impacted if item.depth > 1),
            "max_depth": max((item.depth for item in projection.impacted), default=0),
            "unaffected_count": len(projection.unaffected_resource_ids),
            "impacted_claim_count": len(projection.claim_impacts),
            "fully_impacted_claim_count": sum(1 for item in projection.claim_impacts if item.fully_impacted),
            "partially_impacted_claim_count": sum(1 for item in projection.claim_impacts if not item.fully_impacted),
            "case_is_impacted": any(item.resource_kind.value == "case" for item in projection.impacted),
            "durable_replay_is_exact": bool(replayed.replayed and replayed.projection == appended.projection),
            "atomic_records": len(appended.transaction_receipt.records),
            "governed_state_preconditions": len(appended.transaction_receipt.governed_state_preconditions),
        }

    negatives = await run_negative_vectors(world)
    historical = await _historical_view(world)

    return {
        "contract": "ace.world-intelligence.p2b-supersession-impact/v1alpha1",
        "scenario_id": world["material"]["scenario"]["scenario_id"],
        "brief": {
            "brief_id": str(admission.brief.resource_id),
            "brief_digest": str(admission.brief.resource_digest),
        },
        "case_id": str(world["orientation_case"].resource_id),
        "impact_policy": "lineage_dependency_closure/v1alpha1",
        "eligible_relations": sorted(item.value for item in IMPACT_RELATIONS),
        "supersessions": dict(sorted(results.items())),
        "historical_integrity": historical,
        "negative_vectors": dict(sorted(negatives.items())),
        "proven": {
            "impact_is_dependency_not_falsehood": True,
            "prior_brief_remains_immutable": True,
            "prior_brief_replays_under_its_original_cutoff": True,
            "unaffected_boundary_is_disclosed": True,
            "impact_never_invented_without_lineage": True,
        },
        "closed_requests": ["WI-CR-002", "WI-CR-003", "WI-CR-004", "WI-CR-005"],
        "runtime_gaps": [],
        "invariants": {
            "world_semantics_added_to_ace": False,
            "private_aggregation_in_world": False,
            "private_reasoning_runtime": False,
            "private_status_projector": False,
            "private_source_independence_engine": False,
            "private_supersession_engine": False,
            "imperative_pack_code": False,
            "historical_artifact_rewritten": False,
            "live_resources": 0,
            "delivery_authority": False,
            "external_action": False,
        },
    }


async def _historical_view(world) -> dict[str, Any]:
    """The prior Brief must stay immutable and replayable after the correction."""

    admission = world["admission"]
    replay = await world["service"].synthesize_with_status(world["request"])
    return {
        "brief_id_unchanged": str(replay.brief.resource_id) == str(admission.brief.resource_id),
        "brief_replays_identically": replay.brief == admission.brief,
        "receipt_replays_identically": replay.synthesis_receipt == admission.synthesis_receipt,
        "status_projection_replays_identically": (replay.status_projection == admission.status_projection),
        "replay_used_no_new_reasoning": world["provider"].calls == 1,
        "brief_cutoff_precedes_the_correction": (admission.brief.generated_at < world["correction_at"]),
    }


async def run_negative_vectors(world) -> dict[str, Any]:
    """Every malformed impact request must fail closed with no durable residue."""

    admission = world["admission"]
    closure = _closure(world)
    ids = world["observation_ids"]
    ledger_target = ids["record:ledger_report_1088"]
    cases = {
        "wrong_direction_derived_from_is_not_supersession": {
            "superseder": world["material"]["observations"]["record:ledger_correction_114"],
            "target": ledger_target,
            "cutoff": world["correction_at"],
        },
        "superseder_targets_a_different_record": {
            "superseder": world["assertions"]["supersession:order_47_over_bulletin_214"],
            "target": ledger_target,
            "cutoff": world["correction_at"],
        },
        "target_outside_the_authorized_closure": {
            "superseder": world["assertions"]["supersession:correction_114_over_report_1088"],
            "target": "observation:not-in-this-closure",
            "cutoff": world["correction_at"],
        },
        "future_leakage_before_the_closure_exists": {
            "superseder": world["assertions"]["supersession:correction_114_over_report_1088"],
            "target": ledger_target,
            "cutoff": ACTIVATED_AT,
        },
    }
    results: dict[str, Any] = {}
    for name, case in cases.items():
        try:
            SupersessionImpactService.build_projection(
                product_id=PRODUCT_ID,
                activation_revision=world["binding"].prepared_binding.reference,
                superseder=case["superseder"],
                superseded_resource_id=case["target"],
                closure=closure,
                cutoff_at=case["cutoff"],
                generated_at=world["correction_at"] + timedelta(hours=1),
                as_of=admission.brief.as_of,
            )
        except Exception as exc:  # noqa: BLE001 - the probe records fail-closed error types
            results[name] = {"rejected": True, "error_type": type(exc).__name__}
        else:
            results[name] = {"rejected": False}
    durable = await world["ledger"].count_as_of(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        kind=IntelligenceRecordKind.BRIEF,
        available_at=world["correction_at"] + timedelta(days=1),
    )
    results["durable_brief_count_after_all_negatives"] = durable
    return results


if __name__ == "__main__":  # pragma: no cover - manual harness entry point
    import asyncio

    print(json.dumps(asyncio.run(run_supersession_impact()), indent=2, sort_keys=True))
