from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from ace.application import (
    IntelligenceBuilderResourceProjectionReader,
    IntelligenceBuilderSessionService,
    IntelligenceResourcePlaneService,
)
from ace.application.briefing_agent_contracts import FirstBriefingPreviewV1
from ace.application.intelligence_build_execution import (
    REQUIRED_INTELLIGENCE_BUILD_EFFECTS,
    AuthorizedIntelligenceBuild,
    IntelligenceBuildHostServices,
    IntelligenceBuildStartV1,
    ProductScopedImmutableRecordStore,
    RecordedSourceReferenceV1,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    ResolvedApprovalReceiptV1,
    canonical_hash,
)
from ace.core.runtime_use import AuthorityUseReceiptV1Alpha1
from ace.intelligence import (
    ActivationRevisionReferenceV1Alpha1,
    CanonicalJsonValueV1Alpha1,
    EntitySnapshotV1Alpha1,
    IntelligenceResourceMode,
    IntelligenceResourceKind,
    IntelligenceResourcePageState,
    IntelligenceResourceQueryV1Alpha1,
)
from ace.testing import InMemoryImmutableRecordStore

from ace_world_ai_builder import (
    READ_KINDS,
    RECORDED_JOURNEY_STARTED_AT,
    WORLD_AI_PROFILE_ID,
    WorldAIBuilderExecutor,
    WorldAIBuilderExecutorError,
    load_recorded_world_ai_admission_materials,
    load_recorded_world_ai_source_materials,
    load_world_ai_onboarding_profile,
    plan_from_authorized_build,
)

STARTED_AT = datetime(2026, 8, 13, 20, 4, 35, tzinfo=UTC)
BUILD_GRANT = "authority_grant:world-ai-build"
READ_GRANT = "authority_grant:world-ai-read"
PRODUCT = "product:world-ai-personal"
ACTOR = "principal:world-ai-analyst"
ACTIVATION_KEY = "world_intelligence_ai_command_center"
ACTIVATION_DIGEST = "sha256:" + "6" * 64
ACTIVATION = ActivationRevisionReferenceV1Alpha1(
    product_id=PRODUCT,
    activation_key=ACTIVATION_KEY,
    activation_id=f"domain_activation:{canonical_hash([PRODUCT, ACTIVATION_KEY])[:32]}",
    revision=1,
    revision_id=f"activation_revision:{ACTIVATION_DIGEST.removeprefix('sha256:')[:32]}",
    revision_digest=ACTIVATION_DIGEST,
)
APPROVAL = ResolvedApprovalReceiptV1(
    receipt_ref="approval_receipt:world-ai-personal",
    product_id=PRODUCT,
    subject_ref="activation_spec:world-ai-personal",
    actor_ref=ACTOR,
    receipt_hash="5" * 64,
    approved_at=STARTED_AT - timedelta(minutes=2),
)


def _context() -> AuthenticatedRuntimeContextV1Alpha1:
    return AuthenticatedRuntimeContextV1Alpha1(
        product_id=PRODUCT,
        actor_ref=ACTOR,
        authentication_receipt_ref="task_authentication:world-ai-test",
        authentication_receipt_digest="sha256:" + "8" * 64,
        authenticated_at=STARTED_AT - timedelta(minutes=1),
        expires_at=STARTED_AT + timedelta(hours=1),
    )


def _authority(
    *,
    context,
    subject_ref: str,
    subject_digest: str,
    operation: str,
    authority: str,
    grant_ref: str,
    evaluated_at: datetime = STARTED_AT,
):
    return AuthorityUseReceiptV1Alpha1(
        product_id=context.product_id,
        actor_ref=context.actor_ref,
        authenticated_context=context,
        use_subject_ref=subject_ref,
        use_subject_digest=subject_digest,
        operation=operation,
        authority=authority,
        grant_ref=grant_ref,
        grant_hash="9" * 64,
        evaluated_at=evaluated_at,
        expires_at=context.expires_at,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1(
            state_kind="authority_grant",
            product_id=context.product_id,
            state_id=grant_ref,
            sequence=1,
            revision_id=f"authority_revision:{grant_ref.rsplit(':', 1)[-1]}",
            commit_receipt_id=f"authority_receipt:{grant_ref.rsplit(':', 1)[-1]}",
        ),
    )


def _recorded_source_refs():
    port = CanonicalRecordedSourcePort(CanonicalReplayState())
    materials = load_recorded_world_ai_admission_materials(port)
    return tuple(
        RecordedSourceReferenceV1(
            source_group_id=item.source_group_id,
            material_id=str(item.material_id),
            material_digest=str(item.material_digest),
        )
        for item in materials
    )


def _build(*, source_group_ids=("official_records",), cadence_id="weekly_brief"):
    context = _context()
    request = IntelligenceBuildStartV1(
        authority_grant_ref=BUILD_GRANT,
        resource_authority_grant_ref=READ_GRANT,
        activation_approval_receipt_ref=APPROVAL.receipt_ref,
        activation_approval_subject_ref=APPROVAL.subject_ref,
        client_request_id="request:world-ai-builder-test",
        profile_id=WORLD_AI_PROFILE_ID,
        subject="Federal AI cybersecurity implementation",
        outcome_id="strategy_and_investment",
        source_group_ids=source_group_ids,
        recorded_source_refs=_recorded_source_refs(),
        cadence_id=cadence_id,
        approved_effects=REQUIRED_INTELLIGENCE_BUILD_EFFECTS,
        requested_at=STARTED_AT,
    )
    build_id = "intelligence_build:world-ai-builder-test"
    request_digest = "sha256:" + "7" * 64
    return AuthorizedIntelligenceBuild(
        build_id=build_id,
        request_digest=request_digest,
        product_id=context.product_id,
        actor_ref=context.actor_ref,
        request=request,
        authority_use=_authority(
            context=context,
            subject_ref=build_id,
            subject_digest=request_digest,
            operation="start_intelligence_build",
            authority="intelligence_build",
            grant_ref=BUILD_GRANT,
        ),
        activation_approval=APPROVAL,
    )


class ExactReadAuthority:
    def __init__(self) -> None:
        self.calls = []

    async def resolve_authority_use(self, **request):
        self.calls.append(request)
        return _authority(
            context=request["context"],
            subject_ref=request["use_subject_ref"],
            subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=request["grant_ref"],
            evaluated_at=request["evaluated_at"],
        )


class DurableResourcePort:
    def __init__(self, *, build, store) -> None:
        self.build = build
        self.store = store
        self.authority = ExactReadAuthority()

    async def query(
        self,
        *,
        resource_kinds,
        subject_refs,
        as_of,
        available_at,
        evaluated_at,
        page_size=200,
    ):
        query = IntelligenceResourceQueryV1Alpha1(
            authenticated_context=self.build.authority_use.authenticated_context,
            product_id=self.build.product_id,
            authority_grant_ref=self.build.request.resource_authority_grant_ref,
            resource_kinds=resource_kinds,
            subject_refs=subject_refs,
            as_of=as_of,
            available_at=available_at,
            page_size=page_size,
        )
        return await IntelligenceResourcePlaneService(
            reader=IntelligenceBuilderResourceProjectionReader(store=self.store, degrade_unsupported=False),
            authority=self.authority,
        ).query(query, evaluated_at=evaluated_at)


@dataclass
class CanonicalReplayState:
    admitted: tuple | None = None
    derivation_request: object | None = None


class CanonicalRecordedSourcePort:
    def __init__(self, state: CanonicalReplayState, *, expected_refs=()) -> None:
        self.state = state
        self.expected_refs = tuple(expected_refs)
        self.calls = 0

    def bind_subject(self, *, subject_binding_id, entity_type_id, entity_ref):
        from ace.intelligence import ResolvedSubjectBindingV1Alpha1

        return ResolvedSubjectBindingV1Alpha1(
            product_id=PRODUCT,
            mode=IntelligenceResourceMode.PREPARED,
            activation_revision=ACTIVATION,
            subject_binding_id=subject_binding_id,
            entity_type_id=entity_type_id,
            entity_ref=entity_ref,
        )

    async def admit(self, materials):
        self.calls += 1
        actual_refs = tuple(
            sorted(
                (
                    item.source_group_id,
                    str(item.material_id),
                    str(item.material_digest),
                )
                for item in materials
            )
        )
        expected_refs = tuple(
            (item.source_group_id, item.material_id, item.material_digest) for item in self.expected_refs
        )
        assert actual_refs == expected_refs
        if self.state.admitted is None:
            self.state.admitted = tuple(materials)
        assert tuple(materials) == self.state.admitted
        entities = tuple(
            EntitySnapshotV1Alpha1(
                product_id=PRODUCT,
                mode=IntelligenceResourceMode.PREPARED,
                activation_revision=ACTIVATION,
                as_of=item.source_published_at,
                entity_ref=item.subject_binding.entity_ref,
                entity_type_ref=item.subject_binding.entity_type_id,
                attributes=CanonicalJsonValueV1Alpha1(value_json=item.captured_payload_json),
                projected_at=STARTED_AT,
                confidence=1.0,
            )
            for item in materials
        )
        return SimpleNamespace(entity_snapshots=entities, replayed=self.calls > 1)


class CanonicalPreparedDerivationPort:
    def __init__(self, state: CanonicalReplayState) -> None:
        self.state = state
        self.calls = []

    async def derive(self, request):
        self.calls.append(request)
        replayed = self.state.derivation_request is not None
        if self.state.derivation_request is None:
            self.state.derivation_request = request
        assert request == self.state.derivation_request
        return SimpleNamespace(material_shift=True, shift=object(), signal=object(), replayed=replayed)


def _host(
    *,
    build,
    backing,
    canonical_state=None,
    include_recorded_sources=True,
    include_prepared_derivations=True,
):
    records = ProductScopedImmutableRecordStore(product_id=build.product_id, store=backing)
    port = DurableResourcePort(build=build, store=records)
    state = canonical_state or CanonicalReplayState()
    recorded = (
        CanonicalRecordedSourcePort(state, expected_refs=build.request.recorded_source_refs)
        if include_recorded_sources
        else None
    )
    derivations = CanonicalPreparedDerivationPort(state) if include_prepared_derivations else None
    return (
        IntelligenceBuildHostServices(
            records=records,
            resources=port,
            activation_authority=port.authority,
            recorded_sources=recorded,
            prepared_derivations=derivations,
        ),
        port,
        recorded,
        derivations,
    )


async def test_executor_uses_durable_host_records_and_core_owned_resource_port() -> None:
    build = _build()
    backing = InMemoryImmutableRecordStore()
    host, port, recorded, derivations = _host(build=build, backing=backing)
    executor = WorldAIBuilderExecutor(onboarding_profile=load_world_ai_onboarding_profile())

    page = await executor.start(build, host)

    assert page.product_id == build.product_id
    assert page.actor_ref == build.actor_ref
    assert page.state is IntelligenceResourcePageState.COMPLETE
    assert page.degraded_reason_refs == ()
    kinds = {item.reference.resource_kind.value for item in page.items}
    assert kinds == {"builder_profile", "builder_session"}
    sessions = [item for item in page.items if item.reference.resource_kind.value == "builder_session"]
    assert [item.reference.revision for item in sessions] == list(range(1, 9))
    assert sessions[-1].title == "First briefing ready"
    assert port.authority.calls[0]["operation"] == "query_intelligence_resources"
    assert port.authority.calls[0]["authority"] == "observe_read"
    assert port.authority.calls[0]["grant_ref"] == READ_GRANT
    assert recorded.calls == 1
    assert len(derivations.calls) == 1
    assert derivations.calls[0].detector_id == "ai_policy_implementation_progression"
    assert derivations.calls[0].baseline_snapshot.as_of < derivations.calls[0].current_snapshot.as_of
    artifact_contracts = {
        record.payload_contract for record in backing.records.values() if record.record_kind == "onboarding_artifact"
    }
    assert "ace.application.first-briefing-preview/v1alpha1" in artifact_contracts
    brief_record = next(
        record
        for record in backing.records.values()
        if record.payload_contract == "ace.application.first-briefing-preview/v1alpha1"
    )
    brief = FirstBriefingPreviewV1.model_validate(brief_record.payload)
    assert Counter((item.source_ref, item.evidence_digest) for item in brief.citations) == Counter(
        {
            (
                "source_snapshot:7b79e35507287aa63df2640bf121978e",
                "sha256:688f1d0075b464f6b890254e85465be6fbeddf7c5898c1cc449b5b16fd4213ab",
            ): 2,
            (
                "source_snapshot:4bf705b079706f02f492c250bd7de899",
                "sha256:4e353594d4a0560046f13eae42ec43a867aeb23be8607f98ef493892f28fbfb9",
            ): 2,
        }
    )
    assert {record.product_id for record in backing.records.values()} == {build.product_id}
    plan = plan_from_authorized_build(build)
    assert plan.subject == "Federal AI cybersecurity implementation"
    assert plan.goal_ref == "goal:world-ai-strategy_and_investment-7777777777777777"
    assert plan.cadence.value == "weekly"


async def test_fresh_executor_and_resource_service_reopen_exact_durable_journey() -> None:
    build = _build()
    backing = InMemoryImmutableRecordStore()
    canonical = CanonicalReplayState()
    first_host, _, _, first_derivations = _host(build=build, backing=backing, canonical_state=canonical)
    first_page = await WorldAIBuilderExecutor().start(build, first_host)
    first_count = len(backing.records)

    fresh_host, fresh_port, _, fresh_derivations = _host(
        build=build,
        backing=backing,
        canonical_state=canonical,
    )
    reopened_page = await WorldAIBuilderExecutor().start(build, fresh_host)
    session_id = next(
        item.reference.resource_id
        for item in reopened_page.items
        if item.reference.resource_kind.value == "builder_session" and item.reference.revision == 8
    )
    reopened = await IntelligenceBuilderSessionService(store=fresh_host.records).load_latest(
        product_id=build.product_id,
        session_id=session_id,
        available_at=RECORDED_JOURNEY_STARTED_AT + timedelta(seconds=9),
    )

    assert reopened is not None
    assert reopened.sequence == 8
    assert reopened.stage.value == "first_briefing_ready"
    assert reopened_page == first_page
    assert len(backing.records) == first_count
    assert len(fresh_port.authority.calls) == 1
    assert first_derivations.calls == fresh_derivations.calls


async def test_executor_rejects_unimplemented_source_groups_before_any_write() -> None:
    build = _build(source_group_ids=("official_records", "open_ecosystem"))
    backing = InMemoryImmutableRecordStore()
    host, port, _, _ = _host(build=build, backing=backing)

    with pytest.raises(WorldAIBuilderExecutorError, match="supports only the reviewed official_records"):
        await WorldAIBuilderExecutor().start(build, host)
    assert backing.records == {}
    assert port.authority.calls == []


async def test_executor_rechecks_exact_effects_before_any_write() -> None:
    build = _build()
    narrowed = AuthorizedIntelligenceBuild(
        build_id=build.build_id,
        request_digest=build.request_digest,
        product_id=build.product_id,
        actor_ref=build.actor_ref,
        request=build.request.model_copy(update={"approved_effects": ("connect_sources",)}),
        authority_use=build.authority_use,
        activation_approval=build.activation_approval,
    )
    backing = InMemoryImmutableRecordStore()
    host, port, _, _ = _host(build=narrowed, backing=backing)

    with pytest.raises(WorldAIBuilderExecutorError, match="exact bounded onboarding effects"):
        await WorldAIBuilderExecutor().start(narrowed, host)
    assert backing.records == {}
    assert port.authority.calls == []


@pytest.mark.parametrize(
    ("include_recorded_sources", "include_prepared_derivations"),
    ((False, True), (True, False), (False, False)),
)
async def test_executor_requires_both_canonical_ports_before_any_write(
    include_recorded_sources: bool,
    include_prepared_derivations: bool,
) -> None:
    build = _build()
    backing = InMemoryImmutableRecordStore()
    host, port, recorded, derivations = _host(
        build=build,
        backing=backing,
        include_recorded_sources=include_recorded_sources,
        include_prepared_derivations=include_prepared_derivations,
    )

    with pytest.raises(WorldAIBuilderExecutorError, match="requires Core recorded-source"):
        await WorldAIBuilderExecutor().start(build, host)
    assert backing.records == {}
    assert port.authority.calls == []
    if recorded is not None:
        assert recorded.calls == 0
    if derivations is not None:
        assert derivations.calls == []


def test_recorded_source_material_preserves_exact_live_acceptance_citations() -> None:
    materials = load_recorded_world_ai_source_materials()

    assert [(item.source_ref, item.evidence_digest) for item in materials] == [
        (
            "source_snapshot:7b79e35507287aa63df2640bf121978e",
            "sha256:688f1d0075b464f6b890254e85465be6fbeddf7c5898c1cc449b5b16fd4213ab",
        ),
        (
            "source_snapshot:4bf705b079706f02f492c250bd7de899",
            "sha256:4e353594d4a0560046f13eae42ec43a867aeb23be8607f98ef493892f28fbfb9",
        ),
    ]
    assert [item.development_stage for item in materials] == ["directive_issued", "implementation_reported"]
    assert [item.source_lineage for item in materials] == [
        "federal_register:2026-11415",
        "white_house_release:gold_eagle_2026_07_14",
    ]


def test_discovered_executor_declares_exact_profile_without_fixture_injection() -> None:
    executor = WorldAIBuilderExecutor()

    assert executor.profile_id == WORLD_AI_PROFILE_ID
    assert READ_KINDS[-2:] == (
        IntelligenceResourceKind.BUILDER_PROFILE,
        IntelligenceResourceKind.BUILDER_SESSION,
    )
