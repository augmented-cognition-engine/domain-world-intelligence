#!/usr/bin/env python3
"""Case-bound governed Reality Brief for the frozen World P2B scenario.

This consumer harness uses only public ACE APIs. It admits the frozen scenario's
routed derivations through ACE's durable PREPARED ledger, freezes the exact
five-development orientation Case, and asks ACE's public Case-bound synthesis
service for one governed Brief.

Nothing World-specific is pushed into ACE and nothing is aggregated privately
here: the template, personas, closure, grounding, authorization, and replay all
come from ACE contracts. Where a World requirement is not expressible through
those generic contracts, this harness records an exact falsification instead of
simulating the capability.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from ace.application import (
    CaseBriefSynthesisService,
    DomainActivationAdmissionService,
    PreparedIntelligenceLedgerService,
    bind_committed_activation,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    AuthorityUseReceiptV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    CapabilityUseReceiptV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedReasoningService,
    GovernedStateHeadPreconditionV1Alpha1,
    GovernedStateHeadV1,
    ProviderRouteV1Alpha1,
    ProviderStructuredOutputV1Alpha1,
    ProviderUsageV1Alpha1,
    ReasoningExecutionBindingV1Alpha1,
    ResolvedApprovalReceiptV1,
    ResolvedAuthorityGrantV1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    BriefSynthesisDraftV1Alpha1,
    CaseBriefSynthesisRequestV1Alpha1,
    CaseMemberAttentionBindingV1Alpha1,
    ClaimGroundingKind,
    IntelligenceRecordKind,
    PreparedResourceAdmissionV1Alpha1,
    PreparedResourceSetAdmissionV1Alpha1,
    deterministic_resource_order,
    resource_reference,
)
from ace.testing import InMemoryImmutableRecordStore

from scripts.p2b_prepared_replay import (
    ACTIVATED_AT,
    PRODUCT_ID,
    build_replay_material,
    replay_activation_revision,
)

REASONING_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="structured_reasoning",
    contract="ace.core.reasoning-provider/v1alpha1",
    implementation_id="world_p2b_case_brief_fixture",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "a" * 64,
)
APPEND_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="append_immutable_records",
    contract="ace.core.immutable-record-appender/v1alpha1",
    implementation_id="world_p2b_case_append_fixture",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "b" * 64,
)

#: Ordered routed derivations. Each entry admits only the Observations that are
#: not already durable, so no exact source record is ever admitted twice.
ROUTED_DERIVATIONS = (
    ("public_indicator", "derivation:world-public-indicator"),
    ("event_status", "derivation:world-event-status"),
    ("record_correction", "derivation:world-record-correction"),
    ("claim_disputed", "derivation:world-claim-disputed"),
)

#: The seven domain epistemic statuses the frozen packet requires per statement.
WORLD_EPISTEMIC_STATUSES = (
    "admitted_record",
    "attributed_claim",
    "corroborated",
    "disputed",
    "ace_inference",
    "unknown",
    "scenario",
)


class _ActivationAuthority:
    async def resolve_approval(self, **kwargs):
        return ResolvedApprovalReceiptV1(
            receipt_ref=kwargs["receipt_ref"],
            product_id=kwargs["product_id"],
            subject_ref=kwargs["subject_ref"],
            actor_ref=kwargs["actor_ref"],
            receipt_hash="b" * 64,
            approved_at=kwargs["effective_at"],
        )

    async def resolve_grant(self, **kwargs):
        return ResolvedAuthorityGrantV1(
            grant_ref=kwargs["grant_ref"],
            product_id=kwargs["product_id"],
            authority=kwargs["authority"],
            grant_hash="c" * 64,
            effective_at=kwargs["effective_at"],
        )


class _ActivationStore:
    def __init__(self) -> None:
        self.heads: dict[tuple[str, str, str], GovernedStateHeadV1] = {}
        self.revisions: dict[tuple[str, str], Any] = {}
        self.receipts: dict[tuple[str, str], Any] = {}

    async def commit(self, request):
        receipt = request.receipt()
        revision = request.revision
        self.heads[(revision.state_kind, revision.product_id, revision.state_id)] = GovernedStateHeadV1(
            state_kind=revision.state_kind,
            product_id=revision.product_id,
            state_id=revision.state_id,
            sequence=revision.sequence,
            revision_id=revision.revision_id,
            commit_receipt_id=str(receipt.receipt_id),
            updated_at=request.committed_at,
        )
        self.revisions[(revision.product_id, revision.revision_id)] = revision
        self.receipts[(revision.product_id, receipt.receipt_id)] = receipt
        return receipt

    async def load_head(self, *, state_kind, product_id, state_id):
        return self.heads.get((state_kind, product_id, state_id))

    async def load_revision(self, revision_id, *, product_id):
        return self.revisions.get((product_id, revision_id))

    async def load_receipt(self, receipt_id, *, product_id):
        return self.receipts.get((product_id, receipt_id))


class _Runtime:
    """Minimal exact runtime-use port over public ACE governance contracts."""

    def __init__(self, *, bindings, heads, expires_at) -> None:
        self.bindings = bindings
        self.heads = heads
        self.expires_at = expires_at
        self.capability_calls = 0
        self.authority_calls = 0

    def _binding(self, *, artifact=None, grant_ref=None):
        for binding in self.bindings:
            if artifact is not None and binding.artifact == artifact:
                return binding
            if grant_ref is not None and binding.grant_ref == grant_ref:
                return binding
        raise RuntimeError("no exact governed binding for the requested use")

    async def resolve_capability_use(self, **kwargs):
        self.capability_calls += 1
        binding = self._binding(artifact=kwargs["artifact"])
        if kwargs["configuration_ref"] != binding.configuration_ref:
            raise RuntimeError("capability configuration crossed the exact binding")
        return CapabilityUseReceiptV1Alpha1(
            product_id=PRODUCT_ID,
            actor_ref=kwargs["context"].actor_ref,
            authenticated_context=kwargs["context"],
            use_subject_ref=kwargs["use_subject_ref"],
            use_subject_digest=kwargs["use_subject_digest"],
            operation=kwargs["operation"],
            artifact=kwargs["artifact"],
            capability_state_ref=kwargs["capability_state_ref"],
            configuration_ref=kwargs["configuration_ref"],
            evaluated_at=kwargs["evaluated_at"],
            resolved_at=kwargs["evaluated_at"],
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.heads["capability_state", capability_state_ref_for_artifact(kwargs["artifact"])]
            ),
        )

    async def resolve_authority_use(self, **kwargs):
        self.authority_calls += 1
        binding = self._binding(grant_ref=kwargs["grant_ref"])
        if kwargs["authority"] != binding.authority:
            raise RuntimeError("authority crossed the exact binding")
        return AuthorityUseReceiptV1Alpha1(
            product_id=PRODUCT_ID,
            actor_ref=kwargs["context"].actor_ref,
            authenticated_context=kwargs["context"],
            use_subject_ref=kwargs["use_subject_ref"],
            use_subject_digest=kwargs["use_subject_digest"],
            operation=kwargs["operation"],
            authority=kwargs["authority"],
            grant_ref=kwargs["grant_ref"],
            grant_hash="d" * 64,
            evaluated_at=kwargs["evaluated_at"],
            expires_at=self.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.heads["authority_grant", kwargs["grant_ref"]]
            ),
        )


class _Clock:
    def __init__(self, start, step=timedelta(seconds=5)) -> None:
        self.current = start
        self.step = step

    def __call__(self):
        value = self.current
        self.current = value + self.step
        return value


class _DeterministicProvider:
    """Deterministic stand-in for a structured-reasoning provider.

    It attributes every frozen context item exactly once: persisted Observations
    become cited claims and every other exact Case resource becomes an explicit
    inference claim. It invents no narrative beyond the exact record identities.
    """

    artifact_identity = REASONING_ARTIFACT

    def __init__(self) -> None:
        self.calls = 0
        self.sections: tuple[str, ...] = ()

    async def execute(self, request):
        self.calls += 1
        observations = tuple(
            sorted(item.record_key for item in request.context_items if item.record_kind == "observation")
        )
        inferred = tuple(
            sorted(item.record_key for item in request.context_items if item.record_kind != "observation")
        )
        instruction = json.loads(request.instruction_json)
        section_ids = tuple(instruction["required_sections"])
        self.sections = section_ids
        cited_section = "established_records" if "established_records" in section_ids else section_ids[0]
        inference_sections = tuple(item for item in section_ids if item != cited_section)
        buckets: dict[str, list[str]] = {item: [] for item in inference_sections}
        for index, record_id in enumerate(inferred):
            buckets[inference_sections[index % len(inference_sections)]].append(record_id)

        sections = []
        for section_id in section_ids:
            if section_id == cited_section:
                claims = (
                    BriefDraftClaimV1Alpha1(
                        statement="The admitted public records below are the exact basis of this Case.",
                        grounding_kind=ClaimGroundingKind.CITED,
                        support_refs=observations,
                        confidence=1.0,
                    ),
                )
            else:
                support = tuple(buckets[section_id])
                if not support:
                    support = (inferred[0],)
                claims = (
                    BriefDraftClaimV1Alpha1(
                        statement=(
                            f"ACE derived this {section_id.replace('_', ' ')} statement only from the "
                            "exact frozen Case resources named as supports."
                        ),
                        grounding_kind=ClaimGroundingKind.INFERENCE,
                        support_refs=support,
                        confidence=0.7,
                        uncertainty=(
                            "The frozen prepared records do not establish anything beyond the "
                            "named exact resources."
                        ),
                    ),
                )
            sections.append(BriefDraftSectionV1Alpha1(section_id=section_id, claims=claims))

        draft = BriefSynthesisDraftV1Alpha1(
            brief_type=instruction["brief_type"],
            persona_ids=tuple(item["persona_id"] for item in instruction["personas"]),
            sections=tuple(sections),
            recommendation_claim_id=None,
        )
        return ProviderStructuredOutputV1Alpha1(
            route=ProviderRouteV1Alpha1(
                provider_id="world_p2b_fixture",
                model_id="deterministic",
                model_version="1",
                configuration_digest="sha256:" + "c" * 64,
            ),
            usage=ProviderUsageV1Alpha1(input_units=100, output_units=40, total_units=140, duration_ms=2),
            structured_json=canonical_json(draft.model_dump(mode="json")),
            referenced_context_ids=tuple(str(item.context_id) for item in request.context_items),
        )


def _head(kind: str, state_id: str, *, sequence: int = 1) -> GovernedStateHeadV1:
    return GovernedStateHeadV1(
        state_kind=kind,
        product_id=PRODUCT_ID,
        state_id=state_id,
        sequence=sequence,
        revision_id=f"{kind}_revision:{sequence}",
        commit_receipt_id=f"governed_state_commit:{kind}-{sequence}",
        updated_at=ACTIVATED_AT,
    )


async def _admit_material(ledger, material, *, attention_at):
    """Admit every frozen development through ACE's public durable ledger."""

    observations = material["observations"]
    snapshot_pairs = material["snapshot_pairs"]
    development_observations = material["development_observations"]
    shifts = material["shifts"]
    signals = material["signals"]

    admitted_observation_ids: set[str] = set()
    admissions: dict[str, Any] = {}
    for key, derivation_key in ROUTED_DERIVATIONS:
        fresh = tuple(
            item
            for item in development_observations[key]
            if str(item.resource_id) not in admitted_observation_ids
        )
        if not fresh:
            raise AssertionError(f"{key} would admit no new exact Observation")
        admitted_observation_ids.update(str(item.resource_id) for item in fresh)
        snapshots = snapshot_pairs[key]
        resources = (*fresh, *snapshots, shifts[key], signals[key])
        admissions[key] = await ledger.admit(
            PreparedResourceAdmissionV1Alpha1(
                derivation_key=derivation_key,
                product_id=PRODUCT_ID,
                activation_revision=material["binding"].reference,
                pack=material["binding"].revision.spec.pack,
                observations=fresh,
                entity_snapshots=snapshots,
                shift=shifts[key],
                signal=signals[key],
                brief=None,
                processing_order=deterministic_resource_order(resources),
                attention_evaluated_at=attention_at,
            )
        )

    corroboration = (
        *(
            item
            for item in development_observations["claim_corroborated"]
            if str(item.resource_id) not in admitted_observation_ids
        ),
        *snapshot_pairs["claim_corroborated"],
        shifts["claim_corroborated"],
    )
    admitted_observation_ids.update(
        str(item.resource_id)
        for item in development_observations["claim_corroborated"]
    )
    await ledger.admit_resource_set(
        PreparedResourceSetAdmissionV1Alpha1(
            admission_key="resource-set:world-claim-corroboration",
            product_id=PRODUCT_ID,
            activation_revision=material["binding"].reference,
            pack=material["binding"].revision.spec.pack,
            resources=corroboration,
            processing_order=deterministic_resource_order(corroboration),
            admitted_at=shifts["claim_corroborated"].detected_at,
        )
    )

    unreferenced = tuple(
        item for item in observations.values() if str(item.resource_id) not in admitted_observation_ids
    )
    if unreferenced:
        await ledger.admit_resource_set(
            PreparedResourceSetAdmissionV1Alpha1(
                admission_key="resource-set:world-unreferenced-records",
                product_id=PRODUCT_ID,
                activation_revision=material["binding"].reference,
                pack=material["binding"].revision.spec.pack,
                resources=unreferenced,
                processing_order=deterministic_resource_order(unreferenced),
                admitted_at=max(item.ingested_at for item in unreferenced),
            )
        )

    orientation_case = material["orientation_case"]
    await ledger.admit_resource_set(
        PreparedResourceSetAdmissionV1Alpha1(
            admission_key="resource-set:world-orientation-case",
            product_id=PRODUCT_ID,
            activation_revision=material["binding"].reference,
            pack=material["binding"].revision.spec.pack,
            resources=(orientation_case,),
            processing_order=deterministic_resource_order((orientation_case,)),
            admitted_at=orientation_case.assembled_at,
        )
    )
    return admissions, len(unreferenced)


def _epistemic_projection(receipt) -> dict[str, Any]:
    """Report which epistemic distinctions *this* single-derivation path binds.

    This harness deliberately keeps using the ``brief-synthesis-draft/v1alpha1``
    path so the frozen WI-CR-005 identities stay byte-identical. On that path a
    claim carries only its grounding kind. WI-CR-002 is closed separately by
    ``scripts/p2b_status_case_brief.py``, which declares the seven statuses in
    the Domain Pack and binds them per statement through ACE's public
    status-aware synthesis service.
    """

    expressible = sorted({item.grounding_kind.value for item in receipt.claim_supports})
    return {
        "required_statuses": list(WORLD_EPISTEMIC_STATUSES),
        "expressible_statuses": expressible,
        "expressible_status_count": len(expressible),
        "required_status_count": len(WORLD_EPISTEMIC_STATUSES),
        "status_carrier": "claim.grounding_kind",
        "section_membership_is_validated_status": False,
        "status_aware_path_available": True,
        "status_aware_packet": "P2B-SB1",
    }


async def run_case_brief() -> dict[str, Any]:
    """Synthesize the frozen Meridia Reality Brief through public ACE APIs only."""

    material = build_replay_material()
    orientation_case = material["orientation_case"]
    attention_at = orientation_case.assembled_at
    context_cutoff_at = orientation_case.assembled_at
    requested_at = context_cutoff_at + timedelta(minutes=1)

    pack, revision = replay_activation_revision()
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

    execution_head = _head("reasoning_configuration", "reasoning_configuration:world-case-brief")
    execution_binding = ReasoningExecutionBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=REASONING_ARTIFACT,
        configuration_ref="reasoning_configuration:world-case-brief",
        authority="reason",
        grant_ref="authority_grant:world-case-brief",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(execution_head),
    )
    append_head = _head(
        "governed_operation_configuration",
        "governed_operation_configuration:world-case-brief-append",
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=APPEND_ARTIFACT,
        configuration_ref="governed_operation_configuration:world-case-brief-append",
        authority="append_immutable_records",
        grant_ref="authority_grant:world-case-brief-append",
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

    provider = _DeterministicProvider()
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
        authentication_receipt_ref="authentication:world-p2b-case-brief",
        authentication_receipt_digest="sha256:" + "e" * 64,
        authenticated_at=ACTIVATED_AT,
        expires_at=requested_at + timedelta(hours=2),
    )
    service = CaseBriefSynthesisService(
        activation_service=activation_service,
        pack=pack,
        store=store,
        reasoning=reasoning,
        execution_binding=execution_binding,
        append_binding=append_binding,
        clock=_Clock(requested_at),
    )
    request = CaseBriefSynthesisRequestV1Alpha1(
        synthesis_key="case-brief:world-meridia-72h",
        reasoning_attempt_key="reasoning:world-meridia-72h-case-brief",
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

    admission = await service.synthesize(request)
    replay = await service.synthesize(request)
    receipt = admission.synthesis_receipt
    lineage_kinds: dict[str, int] = {}
    for item in admission.brief.lineage:
        lineage_kinds[item.resource_kind.value] = lineage_kinds.get(item.resource_kind.value, 0) + 1
    durable_brief_count = await ledger.count_as_of(
        product_id=PRODUCT_ID,
        mode=orientation_case.mode,
        kind=IntelligenceRecordKind.BRIEF,
        available_at=admission.brief.generated_at,
    )

    return {
        "contract": "ace.world-intelligence.p2b-case-bound-governed-brief/v1alpha1",
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
            "lineage_kinds": dict(sorted(lineage_kinds.items())),
            "binds_case_in_lineage": any(
                item.resource_id == str(orientation_case.resource_id) for item in admission.brief.lineage
            ),
        },
        "synthesis_receipt": {
            "receipt_id": str(receipt.receipt_id),
            "receipt_digest": str(receipt.receipt_digest),
            "template_id": receipt.template_id,
            "persona_ids": list(receipt.persona_ids),
            "case_member_count": len(receipt.case_member_ids),
            "routed_member_count": len(receipt.member_attention),
            "selected_context_count": len(receipt.selected_context),
            "section_ids": list(receipt.actual_section_ids),
        },
        "governance": {
            "atomic_records": len(admission.transaction_receipt.records),
            "governed_state_preconditions": len(
                admission.transaction_receipt.governed_state_preconditions
            ),
            "durable_brief_count": durable_brief_count,
            "deterministic_replay": bool(
                replay.replayed
                and replay.brief == admission.brief
                and replay.synthesis_receipt == receipt
            ),
            "provider_invocations": provider.calls,
        },
        "epistemic_status_projection": _epistemic_projection(receipt),
        "runtime_gaps": [
            {
                "request_id": "WI-CR-003",
                "boundary": "source_independence_closure",
                "finding": (
                    "The Case-bound closure proves complete membership but no public runtime predicate "
                    "proves that corroboration uses distinct derivation families."
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
        "closed_requests": ["WI-CR-005"],
        "wi_cr_002_closed_by": "P2B-SB1",
        "invariants": {
            "world_semantics_added_to_ace": False,
            "private_aggregation_in_world": False,
            "private_reasoning_runtime": False,
            "duplicated_source_records": False,
            "unreferenced_admitted_records": unreferenced_count,
            "live_resources": 0,
            "delivery_authority": False,
            "external_action": False,
        },
    }


if __name__ == "__main__":  # pragma: no cover - manual harness entry point
    import asyncio

    print(json.dumps(asyncio.run(run_case_brief()), indent=2, sort_keys=True))
