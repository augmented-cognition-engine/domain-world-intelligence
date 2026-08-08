#!/usr/bin/env python3
"""Status-aware governed Reality Brief for the frozen World P2B scenario.

This consumer harness closes WI-CR-002 through public ACE APIs and Pack IR only.
It declares the seven World epistemic statuses in an inert Domain Pack module,
activates that module as an additive consumer revision, and asks ACE's public
status-aware Case-bound synthesis service for one governed Brief plus its
durable per-statement status projection.

Why this is an additive activation
----------------------------------
Every Intelligence resource carries its ``activation_revision``, whose digest
derives from the compiled Pack IR digest. Declaring a new Pack module therefore
necessarily re-keys every resource admitted under it. The frozen WI-CR-005
packet -- ``case:2ee200c03f2576307b0bc43e6e128f30`` and
``brief:8fb3173069eca502652b1c9c004c92e6`` -- must stay byte-identical, so this
harness follows the repository's established pattern (see
``compile_replay_pack``) and builds a *separate* additive revision rather than
mutating the frozen one. ``scripts/p2b_case_brief.py`` is untouched and still
reproduces the exact frozen identities.

Honest scope
------------
``corroborated`` here enforces a minimum of two admitted Observation supports of
the ``observation`` kind. That is a cardinality and resource-kind rule. It does
NOT prove that those Observations come from independent source families, and
this harness does not claim otherwise. WI-CR-003 remains open.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from ace.application import (
    CaseBriefStatusSynthesisService,
    DomainActivationAdmissionService,
    PreparedIntelligenceLedgerService,
    bind_committed_activation,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedReasoningService,
    GovernedStateHeadPreconditionV1Alpha1,
    ReasoningExecutionBindingV1Alpha1,
    ProviderRouteV1Alpha1,
    ProviderStructuredOutputV1Alpha1,
    ProviderUsageV1Alpha1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    BriefDraftClaimStatusBindingV1Alpha1,
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    BriefSynthesisDraftV1Alpha2,
    CaseBriefSynthesisRequestV1Alpha1,
    CaseMemberAttentionBindingV1Alpha1,
    ClaimGroundingKind,
    IntelligenceRecordKind,
    OrganizationOverlayV1,
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
    resource_reference,
)
from ace.intelligence.contracts.activation import ActivationState
from ace.testing import InMemoryImmutableRecordStore

from scripts.p2a_compile_acceptance import _encoded, _pack_material, _replace_resource
from scripts.p2b_case_brief import (
    APPEND_ARTIFACT,
    REASONING_ARTIFACT,
    ROUTED_DERIVATIONS,
    WORLD_EPISTEMIC_STATUSES,
    _ActivationAuthority,
    _ActivationStore,
    _admit_material,
    _Clock,
    _head,
    _Runtime,
)
from scripts.p2b_prepared_replay import (
    ACTIVATED_AT,
    CATEGORICAL_RULES,
    ADDITIVE_ROUTES,
    PRODUCT_ID,
    build_replay_material,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"

#: The exact declared status set that governs the Reality Brief template.
STATUS_SET_ID = "world_reality_status"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_status_pack():
    """Compile an additive 0.3.0 revision that declares the epistemic status set.

    This mirrors ``compile_replay_pack`` exactly and then adds one further inert
    module. The frozen 0.1.0 manifest on disk is never mutated.
    """

    manifest, resources = _pack_material()
    manifest["metadata"]["version"] = "0.3.0"

    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    source = next(item for item in ontology["entity_types"] if item["entity_type_id"] == "source")
    source["attributes"].append({"attribute_id": "record_status", "value_type": "string", "required": False})
    _replace_resource(manifest, resources, "modules/ontology.json", ontology)

    detection = _load(PACK_ROOT / "modules" / "detection.json")
    detection["contract"] = "ace.intelligence.detection/v1alpha2"
    detection["categorical_transition_rules"] = list(CATEGORICAL_RULES)
    detection_module = next(item for item in manifest["modules"] if item["module_id"] == "world_detection")
    detection_module["contract"] = detection["contract"]
    _replace_resource(manifest, resources, "modules/detection.json", detection)

    personas = _load(PACK_ROOT / "modules" / "personas.json")
    personas["signal_routing_rules"].extend(ADDITIVE_ROUTES)
    _replace_resource(manifest, resources, "modules/personas.json", personas)

    epistemic = _load(PACK_ROOT / "modules" / "epistemic_status.json")
    path = "modules/epistemic_status.json"
    payload = _encoded(epistemic)
    resources[path] = payload
    manifest["resources"].append(
        {
            "resource_id": "world_epistemic_status",
            "path": path,
            "media_type": "application/json",
            "digest": f"sha256:{__import__('hashlib').sha256(payload).hexdigest()}",
        }
    )
    manifest["modules"].append(
        {
            "module_id": epistemic["module_id"],
            "contract": epistemic["contract"],
            "resource_id": "world_epistemic_status",
            "depends_on": ["world_synthesis"],
        }
    )
    return compile_pack_document(_encoded(manifest), resources)


def status_activation_revision():
    """Build the exact additive status-aware activation revision."""

    pack = compile_status_pack()
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id="world_p2b_status_case_brief",
            version="0.3.0",
            pack_id=pack.metadata.pack_id,
            pack_version=pack.metadata.version,
            pack_digest=pack.pack_digest,
        ),
    )
    spec = prepare_domain_activation(
        product_id=PRODUCT_ID,
        activation_key=pack.metadata.pack_id,
        pack=pack,
        overlay=overlay,
        compilation_receipt_ref="receipt:world-p2b-status-compilation",
        conformance_receipt_refs=("receipt:world-p2b-status-conformance",),
        capability_bindings=_capability_bindings(),
        authority_bindings=_authority_bindings(),
    )
    revision = prepare_activation_revision(
        spec=spec,
        state=ActivationState.ACTIVE,
        actor_ref="principal:world-p2b-reviewer",
        approval_receipt_ref="receipt:world-p2b-status-approval",
        occurred_at=ACTIVATED_AT,
    )
    return pack, revision


def _capability_bindings():
    from ace.intelligence import CapabilityBindingV1

    return (
        CapabilityBindingV1(
            requirement_id="public_record_snapshot",
            capability="source_snapshot",
            contract="ace.source.snapshot/v1alpha1",
            implementation_id="world_p2b_fixture_snapshot",
            implementation_version="0.1.0",
            artifact_digest="sha256:" + "1" * 64,
        ),
    )


def _authority_bindings():
    from ace.intelligence import AuthorityBindingV1

    return (
        AuthorityBindingV1(
            request_id="read_public_record_source",
            authority="source_read",
            grant_ref="authority_grant:world-public-record",
        ),
    )


#: The deliberate per-section allocation of the seven declared statuses. Each
#: entry is ``(section_id, status_id, grounding, bucket spec)`` where the bucket
#: spec names exact frozen resources by kind and index, so every one of the 26
#: selected context items is attributed exactly once.
CLAIM_PLAN = (
    ("what_happened", "admitted_record", "cited", (("observation", 0), ("observation", 1))),
    ("what_changed", "ace_inference", "inference", (("case", 0), ("entity_snapshot", 0), ("entity_snapshot", 1))),
    ("established_records", "admitted_record", "cited", (("observation", 2),)),
    ("attributed_claims", "attributed_claim", "cited", (("observation", 3),)),
    ("where_sources_agree", "corroborated", "cited", (("observation", 4), ("observation", 5))),
    ("where_sources_conflict", "disputed", "inference", (("shift", 0), ("shift", 1))),
    (
        "ace_inferences",
        "ace_inference",
        "inference",
        (("entity_snapshot", 2), ("entity_snapshot", 3), ("entity_snapshot", 4)),
    ),
    (
        "unknowns",
        "unknown",
        "inference",
        (("entity_snapshot", 5), ("entity_snapshot", 6), ("entity_snapshot", 7)),
    ),
    (
        "why_it_matters",
        "ace_inference",
        "inference",
        (("entity_snapshot", 8), ("entity_snapshot", 9), ("shift", 2)),
    ),
    ("watchpoints", "scenario", "inference", (("shift", 3), ("signal", 0))),
    (
        "limitations",
        "unknown",
        "inference",
        (("shift", 4), ("signal", 1), ("signal", 2), ("signal", 3)),
    ),
)

STATEMENTS = {
    "admitted_record": "The named admitted public records establish this statement directly.",
    "attributed_claim": "Exactly one named source record asserts this statement; the attribution is part of it.",
    "corroborated": (
        "At least two admitted records support this statement. This is support cardinality only "
        "and does not establish independent source families."
    ),
    "disputed": "The admitted material is materially in conflict on this statement.",
    "ace_inference": "ACE derived this statement only from the exact frozen resources named as supports.",
    "unknown": "The admitted evidence does not resolve this statement.",
    "scenario": "This is a conditional future state built only from the exact derived resources named.",
}

UNCERTAINTY = (
    "The frozen prepared records do not establish anything beyond the named exact resources."
)


class _StatusProvider:
    """Deterministic status-aware stand-in emitting draft ``v1alpha2``.

    It invents no narrative beyond the exact record identities, attributes every
    frozen context item exactly once, and names one declared status per
    statement. Section placement carries no meaning: the status binding is a
    separate machine-readable field keyed by exact draft claim identity.
    """

    artifact_identity = REASONING_ARTIFACT

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, request):
        self.calls += 1
        by_kind: dict[str, list[str]] = {}
        for item in request.context_items:
            by_kind.setdefault(item.record_kind, []).append(item.record_key)
        for values in by_kind.values():
            values.sort()

        instruction = json.loads(request.instruction_json)
        section_ids = tuple(instruction["required_sections"])
        declared = {item["status_id"] for item in instruction["epistemic_status_policy"]["statuses"]}
        planned = {item[1] for item in CLAIM_PLAN}
        if not planned <= declared:
            raise AssertionError(f"planned statuses are not declared by the Pack: {sorted(planned - declared)}")

        sections = []
        statuses = []
        attributed: set[str] = set()
        for section_id, status_id, grounding, bucket in CLAIM_PLAN:
            supports = tuple(by_kind[kind][index] for kind, index in bucket)
            attributed.update(supports)
            claim = BriefDraftClaimV1Alpha1(
                statement=STATEMENTS[status_id],
                grounding_kind=(
                    ClaimGroundingKind.CITED if grounding == "cited" else ClaimGroundingKind.INFERENCE
                ),
                support_refs=supports,
                confidence=1.0 if grounding == "cited" else 0.7,
                uncertainty=None if grounding == "cited" else UNCERTAINTY,
            )
            sections.append(BriefDraftSectionV1Alpha1(section_id=section_id, claims=(claim,)))
            statuses.append(
                BriefDraftClaimStatusBindingV1Alpha1(
                    draft_claim_id=str(claim.claim_id),
                    status_id=status_id,
                )
            )
        if tuple(item.section_id for item in sections) != section_ids:
            raise AssertionError("claim plan does not cover the routed template sections in order")
        expected = {item.record_key for item in request.context_items}
        if attributed != expected:
            raise AssertionError(
                f"claim plan left exact selected supports unattributed: {sorted(expected - attributed)}"
            )

        draft = BriefSynthesisDraftV1Alpha2(
            brief_type=instruction["brief_type"],
            persona_ids=tuple(item["persona_id"] for item in instruction["personas"]),
            sections=tuple(sections),
            claim_statuses=tuple(statuses),
            recommendation_claim_id=None,
        )
        return ProviderStructuredOutputV1Alpha1(
            route=ProviderRouteV1Alpha1(
                provider_id="world_p2b_status_fixture",
                model_id="deterministic",
                model_version="1",
                configuration_digest="sha256:" + "c" * 64,
            ),
            usage=ProviderUsageV1Alpha1(input_units=120, output_units=48, total_units=168, duration_ms=2),
            structured_json=canonical_json(draft.model_dump(mode="json")),
            referenced_context_ids=tuple(str(item.context_id) for item in request.context_items),
        )


async def run_status_case_brief() -> dict[str, Any]:
    """Synthesize the status-aware Reality Brief through public ACE APIs only."""

    pack, revision = status_activation_revision()
    material = build_replay_material(pack=pack, revision=revision)
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
    admissions, unreferenced_count = await _admit_material(
        ledger,
        material,
        attention_at=attention_at,
    )

    execution_head = _head("reasoning_configuration", "reasoning_configuration:world-status-case-brief")
    execution_binding = ReasoningExecutionBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=REASONING_ARTIFACT,
        configuration_ref="reasoning_configuration:world-status-case-brief",
        authority="reason",
        grant_ref="authority_grant:world-status-case-brief",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(execution_head),
    )
    append_head = _head(
        "governed_operation_configuration",
        "governed_operation_configuration:world-status-case-brief-append",
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=APPEND_ARTIFACT,
        configuration_ref="governed_operation_configuration:world-status-case-brief-append",
        authority="append_immutable_records",
        grant_ref="authority_grant:world-status-case-brief-append",
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
        ("authority_grant", execution_binding.grant_ref): _head(
            "authority_grant", execution_binding.grant_ref
        ),
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

    provider = _StatusProvider()
    reasoning = GovernedReasoningService(
        store=store,
        runtime_use=_Runtime(
            bindings=(execution_binding, append_binding),
            heads=heads,
            expires_at=requested_at + timedelta(hours=1),
        ),
        provider=provider,
        clock=_Clock(requested_at),
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=PRODUCT_ID,
        actor_ref="principal:world-p2b-reviewer",
        authentication_receipt_ref="authentication:world-p2b-status-case-brief",
        authentication_receipt_digest="sha256:" + "e" * 64,
        authenticated_at=ACTIVATED_AT,
        expires_at=requested_at + timedelta(hours=2),
    )
    service = CaseBriefStatusSynthesisService(
        activation_service=activation_service,
        pack=pack,
        store=store,
        reasoning=reasoning,
        execution_binding=execution_binding,
        append_binding=append_binding,
        clock=_Clock(requested_at),
    )
    request = CaseBriefSynthesisRequestV1Alpha1(
        synthesis_key="status-case-brief:world-meridia-72h",
        reasoning_attempt_key="reasoning:world-meridia-72h-status-case-brief",
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
    replay = await service.synthesize_with_status(request)
    receipt = admission.synthesis_receipt
    projection = admission.status_projection

    by_status: dict[str, int] = {}
    for binding_item in projection.claim_statuses:
        by_status[binding_item.status_id] = by_status.get(binding_item.status_id, 0) + 1
    durable_brief_count = await ledger.count_as_of(
        product_id=PRODUCT_ID,
        mode=orientation_case.mode,
        kind=IntelligenceRecordKind.BRIEF,
        available_at=admission.brief.generated_at,
    )
    declared = list(projection.declared_status_ids)

    return {
        "contract": "ace.world-intelligence.p2b-status-aware-governed-brief/v1alpha1",
        "scenario_id": material["scenario"]["scenario_id"],
        "case": {
            "case_id": str(orientation_case.resource_id),
            "case_digest": str(orientation_case.resource_digest),
            "member_count": len(orientation_case.lineage),
        },
        "brief": {
            "brief_id": str(admission.brief.resource_id),
            "brief_digest": str(admission.brief.resource_digest),
            "brief_type_ref": admission.brief.brief_type_ref,
            "claim_count": len(admission.brief.claims),
            "citation_count": len(admission.brief.citations),
            "lineage_count": len(admission.brief.lineage),
        },
        "synthesis_receipt": {
            "receipt_id": str(receipt.receipt_id),
            "receipt_digest": str(receipt.receipt_digest),
            "template_id": receipt.template_id,
            "selected_context_count": len(receipt.selected_context),
        },
        "status_projection": {
            "projection_id": str(projection.projection_id),
            "projection_digest": str(projection.projection_digest),
            "module_id": projection.module_id,
            "status_set_id": projection.status_set_id,
            "template_id": projection.template_id,
            "declared_status_ids": declared,
            "claim_status_count": len(projection.claim_statuses),
            "statuses_per_claim": [
                {
                    "claim_id": item.claim_id,
                    "grounding_kind": item.grounding_kind.value,
                    "status_id": item.status_id,
                    "support_count": item.support_count,
                    "support_kinds": [kind.value for kind in item.support_kinds],
                }
                for item in projection.claim_statuses
            ],
            "claims_per_status": dict(sorted(by_status.items())),
            "binds_every_receipted_claim": tuple(
                item.claim_id for item in projection.claim_statuses
            )
            == tuple(item.claim_id for item in receipt.claim_supports),
            "all_seven_required_statuses_present": sorted(declared)
            == sorted(WORLD_EPISTEMIC_STATUSES),
            "every_required_status_used": sorted(by_status) == sorted(WORLD_EPISTEMIC_STATUSES),
            "status_carrier": "brief_epistemic_status_projection.claim_statuses",
            "section_membership_is_validated_status": False,
        },
        "governance": {
            "atomic_records": len(admission.transaction_receipt.records),
            "record_kinds": [item.record_kind for item in admission.transaction_receipt.records],
            "governed_state_preconditions": len(
                admission.transaction_receipt.governed_state_preconditions
            ),
            "durable_brief_count": durable_brief_count,
            "deterministic_replay": bool(
                replay.replayed
                and replay.brief == admission.brief
                and replay.synthesis_receipt == receipt
                and replay.status_projection == projection
            ),
            "provider_invocations": provider.calls,
        },
        "proven": {
            "status_is_per_statement_and_machine_readable": True,
            "status_validated_against_grounding_kind": True,
            "status_validated_against_support_count": True,
            "status_validated_against_support_kinds": True,
            "corroborated_proves_source_family_independence": False,
        },
        "runtime_gaps": [
            {
                "request_id": "WI-CR-003",
                "boundary": "source_independence_closure",
                "finding": (
                    "The declared corroborated status enforces a minimum admitted-Observation "
                    "support count and a closed support-kind set, but no public runtime predicate "
                    "proves those supports come from distinct derivation or source families."
                ),
            },
            {
                "request_id": "WI-CR-004",
                "boundary": "supersession_impact_projection",
                "finding": (
                    "No public query enumerates the downstream resources affected by the admitted "
                    "record correction."
                ),
            },
        ],
        "closed_requests": ["WI-CR-002", "WI-CR-005"],
        "invariants": {
            "world_semantics_added_to_ace": False,
            "private_aggregation_in_world": False,
            "private_reasoning_runtime": False,
            "private_status_projector": False,
            "imperative_pack_code": False,
            "duplicated_source_records": False,
            "unreferenced_admitted_records": unreferenced_count,
            "live_resources": 0,
            "delivery_authority": False,
            "external_action": False,
        },
    }


if __name__ == "__main__":  # pragma: no cover - manual harness entry point
    import asyncio

    print(json.dumps(asyncio.run(run_status_case_brief()), indent=2, sort_keys=True))
