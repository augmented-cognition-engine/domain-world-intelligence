"""Hermetic LIVE AI command-center acceptance over two official lineages.

The source responses are recorded and network-free. ACE still admits them as
LIVE runtime records because they cross the governed source-ingress boundary;
that mode does not claim capture-time network freshness.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ace.application import (
    LIVE_SOURCE_RECORD_SPACE,
    DomainActivationAdmissionService,
    LiveIntelligenceBridgeService,
    LiveSourceIngressService,
    bind_committed_activation,
)
from ace.core import (
    AppendOnlyTransactionRequestV1,
    AuthenticatedRuntimeContextV1Alpha1,
    AuthorityUseReceiptV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    CapabilityUseReceiptV1Alpha1,
    GovernedActionAuthorizationProjection,
    GovernedActionAuthorizationRequestV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    GovernedStateHeadV1,
    ImmutableRecordV1,
    ReceiptReferenceV1Alpha1,
    ResolvedSourceDefinitionV1Alpha1,
    capability_state_ref_for_artifact,
    immutable_record_storage_id,
)
from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    BriefSynthesisDraftV1Alpha1,
    CapabilityBindingV1,
    CaseV1Alpha1,
    ClaimGroundingKind,
    IntelligenceResourceMode,
    LineageReferenceV1Alpha1,
    LineageRelation,
    LineageResourceKind,
    LiveDerivationRequestV1Alpha1,
    LiveSourceIngressRequestV1Alpha1,
    OrganizationOverlayV1,
    resource_reference,
)
from ace.intelligence.contracts.ledger import resource_available_at, resource_kind
from ace.intelligence.packs import (
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
)
from ace.intelligence.packs.runtime import resolve_brief_synthesis_policy
from ace.intelligence.synthesis import assemble_canonical_brief
from ace.testing import InMemoryImmutableRecordStore
from ace_world_federal_register_source import (
    AI_POLICY_DOCUMENT_URI,
    AI_POLICY_IMPLEMENTATION_ID,
    AI_POLICY_IMPLEMENTATION_VERSION,
    AI_POLICY_LOCATOR,
    AI_POLICY_SOURCE_TYPE,
    REVIEWED_AI_PUBLICATION_IMPLEMENTATION_VERSION,
    REVIEWED_AI_PUBLICATION_LOCATOR,
    REVIEWED_AI_PUBLICATION_PROFILES,
    REVIEWED_AI_PUBLICATION_SOURCE_TYPE,
    WHITE_HOUSE_IMPLEMENTATION_ID,
    WHITE_HOUSE_IMPLEMENTATION_VERSION,
    WHITE_HOUSE_LOCATOR,
    WHITE_HOUSE_RELEASE_URI,
    WHITE_HOUSE_SOURCE_TYPE,
    AIPolicyFederalRegisterSourceAdapter,
    FederalRegisterRetrievalResult,
    ReviewedAIPublicationRetrievalResult,
    ReviewedAIPublicationSourceAdapter,
    WhiteHouseAIPolicySourceAdapter,
    WhiteHouseRetrievalResult,
)

from scripts.p2c_federal_register_live_acceptance import (
    ExactActivationAuthority,
    MemoryGovernedStateStore,
    SequenceClock,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_ai"
FIXTURE_PATH = PACK_ROOT / "conformance" / "ai_command_center_live_input.json"
APPEND_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="append_immutable_records",
    contract="ace.core.immutable-record-appender/v1alpha1",
    implementation_id="world_ai_command_center_append_fixture",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "2" * 64,
)


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("fixture time must include a timezone")
    return parsed.astimezone(UTC)


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def compile_ai_pack():
    manifest_bytes = (PACK_ROOT / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    return compile_pack_document(
        manifest_bytes,
        {item["path"]: (PACK_ROOT / item["path"]).read_bytes() for item in manifest["resources"]},
    )


def _head(
    *,
    product_id: str,
    state_kind: str,
    state_id: str,
    sequence: int,
    updated_at: datetime,
) -> GovernedStateHeadV1:
    return GovernedStateHeadV1(
        state_kind=state_kind,
        product_id=product_id,
        state_id=state_id,
        sequence=sequence,
        revision_id=f"{state_kind}_revision:ai-command-center-{sequence}",
        commit_receipt_id=f"governed_state_commit:ai-command-center-{sequence}",
        updated_at=updated_at,
    )


class ExactSourceDefinitions:
    def __init__(self, definitions: tuple[ResolvedSourceDefinitionV1Alpha1, ...]) -> None:
        self.definitions = {item.source_definition_ref: item for item in definitions}

    async def resolve_source_definition(
        self,
        *,
        product_id,
        source_definition_ref,
        resolved_at,
    ):
        del resolved_at
        definition = self.definitions.get(source_definition_ref)
        if definition is None or definition.product_id != product_id:
            raise ValueError("unknown exact AI command-center source definition")
        return definition


class ExactAdapterRegistry:
    def __init__(self, adapters: tuple[Any, ...]) -> None:
        self.adapters = {item.artifact_identity: item for item in adapters}

    def resolve_source_adapter(self, *, artifact):
        return self.adapters.get(artifact)


class RecordedTransport:
    """One network-free transport result under an exact URI allowlist."""

    def __init__(self, result: Any) -> None:
        self.result = result
        self.calls = 0

    async def retrieve(self, request):
        if request.requested_uri != self.result.requested_uri:
            raise ValueError("recorded transport crossed its exact URI")
        self.calls += 1
        return self.result


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    artifact: CapabilityArtifactIdentityV1Alpha1
    configuration_ref: str
    capability_head: GovernedStateHeadV1
    grant_ref: str
    grant_hash: str
    grant_head: GovernedStateHeadV1


class ExactRuntimeUse:
    def __init__(
        self,
        *,
        context: AuthenticatedRuntimeContextV1Alpha1,
        bindings: tuple[RuntimeBinding, ...],
    ) -> None:
        self.context = context
        self.by_artifact = {item.artifact: item for item in bindings}
        self.by_grant = {item.grant_ref: item for item in bindings}

    async def resolve_capability_use(self, **request):
        binding = self.by_artifact.get(request["artifact"])
        if (
            binding is None
            or request["context"] != self.context
            or request["operation"] != "capture"
            or request["configuration_ref"] != binding.configuration_ref
            or request["capability_state_ref"] != capability_state_ref_for_artifact(binding.artifact)
        ):
            raise ValueError("capability use crossed exact AI source scope")
        return CapabilityUseReceiptV1Alpha1(
            product_id=self.context.product_id,
            actor_ref=self.context.actor_ref,
            authenticated_context=self.context,
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            artifact=binding.artifact,
            capability_state_ref=request["capability_state_ref"],
            configuration_ref=binding.configuration_ref,
            evaluated_at=request["evaluated_at"],
            resolved_at=request["evaluated_at"],
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(binding.capability_head),
        )

    async def resolve_authority_use(self, **request):
        binding = self.by_grant.get(request["grant_ref"])
        if (
            binding is None
            or request["context"] != self.context
            or request["operation"] != "capture"
            or request["authority"] != "source_read"
            or request["evaluated_at"] >= self.context.expires_at
        ):
            raise ValueError("authority use crossed exact AI source scope")
        return AuthorityUseReceiptV1Alpha1(
            product_id=self.context.product_id,
            actor_ref=self.context.actor_ref,
            authenticated_context=self.context,
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=binding.grant_ref,
            grant_hash=binding.grant_hash,
            evaluated_at=request["evaluated_at"],
            expires_at=self.context.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(binding.grant_head),
        )


class ExactAppendAuthorizer:
    def __init__(self) -> None:
        self.issued: dict[tuple[str, str, str], GovernedActionAuthorizationProjection] = {}

    async def authorize_action(self, request):
        projection = GovernedActionAuthorizationProjection(
            authorization_ref=ReceiptReferenceV1Alpha1(
                receipt_id=f"governed_action_authorization:{request.request_id.split(':')[-1]}",
                receipt_digest="sha256:" + "3" * 64,
            ),
            authorized_at=request.requested_at,
            state_preconditions=request.required_state_preconditions,
        )
        self.issued[(request.operation, request.subject_ref, request.subject_digest)] = projection
        return projection

    async def verify_action_reference(
        self,
        *,
        product_id,
        operation,
        subject_ref,
        subject_digest,
        expected,
    ):
        del product_id
        projection = self.issued.get((operation, subject_ref, subject_digest))
        if projection is None or projection.authorization_ref != expected:
            raise RuntimeError("no exact append authorization on record")
        return projection


@dataclass
class CommandCenterEnvironment:
    fixture: dict[str, Any]
    pack: Any
    context: AuthenticatedRuntimeContextV1Alpha1
    activation_service: DomainActivationAdmissionService
    committed_activation: Any
    store: InMemoryImmutableRecordStore
    definitions: ExactSourceDefinitions
    runtime_use: ExactRuntimeUse
    registry: ExactAdapterRegistry
    requests: tuple[LiveSourceIngressRequestV1Alpha1, ...]
    adapters: tuple[Any, ...]
    transports: tuple[RecordedTransport, ...]
    append_binding: GovernedOperationBindingV1Alpha1
    activation_head: GovernedStateHeadV1
    append_head: GovernedStateHeadV1

    def ingress(self, clock: SequenceClock) -> LiveSourceIngressService:
        return LiveSourceIngressService(
            activation_service=self.activation_service,
            source_definitions=self.definitions,
            runtime_use=self.runtime_use,
            adapters=self.registry,
            store=self.store,
            clock=clock,
            max_payload_chars=512_000,
        )


async def build_environment() -> CommandCenterEnvironment:
    fixture = load_fixture()
    product_id = fixture["product_id"]
    pack = compile_ai_pack()
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=product_id,
        actor_ref=fixture["actor_ref"],
        authentication_receipt_ref=fixture["authentication"]["receipt_ref"],
        authentication_receipt_digest=fixture["authentication"]["receipt_digest"],
        authenticated_at=_time(fixture["authentication"]["authenticated_at"]),
        expires_at=_time(fixture["authentication"]["expires_at"]),
    )

    policy_artifacts = (
        CapabilityArtifactIdentityV1Alpha1(
            capability="source_snapshot",
            contract="ace.source.snapshot/v1alpha1",
            implementation_id=AI_POLICY_IMPLEMENTATION_ID,
            implementation_version=AI_POLICY_IMPLEMENTATION_VERSION,
            artifact_digest=fixture["sources"][0]["artifact_digest"],
        ),
        CapabilityArtifactIdentityV1Alpha1(
            capability="source_snapshot",
            contract="ace.source.snapshot/v1alpha1",
            implementation_id=WHITE_HOUSE_IMPLEMENTATION_ID,
            implementation_version=WHITE_HOUSE_IMPLEMENTATION_VERSION,
            artifact_digest=fixture["sources"][1]["artifact_digest"],
        ),
    )
    reviewed_profiles_by_uri = {profile.source_uri: profile for profile in REVIEWED_AI_PUBLICATION_PROFILES}
    reviewed_artifacts = tuple(
        CapabilityArtifactIdentityV1Alpha1(
            capability="source_snapshot",
            contract="ace.source.snapshot/v1alpha1",
            implementation_id=reviewed_profiles_by_uri[source["requested_uri"]].implementation_id,
            implementation_version=REVIEWED_AI_PUBLICATION_IMPLEMENTATION_VERSION,
            artifact_digest=source["artifact_digest"],
        )
        for source in fixture["sources"][2:]
    )
    artifacts = (*policy_artifacts, *reviewed_artifacts)
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id=fixture["activation"]["overlay_id"],
            version=fixture["activation"]["overlay_version"],
            pack_id=pack.metadata.pack_id,
            pack_version=pack.metadata.version,
            pack_digest=pack.pack_digest,
        ),
    )
    spec = prepare_domain_activation(
        product_id=product_id,
        activation_key=fixture["activation_key"],
        pack=pack,
        overlay=overlay,
        compilation_receipt_ref=fixture["activation"]["compilation_receipt_ref"],
        conformance_receipt_refs=(fixture["activation"]["conformance_receipt_ref"],),
        capability_bindings=tuple(
            CapabilityBindingV1(
                requirement_id=source["capability_requirement_id"],
                capability=artifact.capability,
                contract=artifact.contract,
                implementation_id=artifact.implementation_id,
                implementation_version=artifact.implementation_version,
                artifact_digest=artifact.artifact_digest,
                configuration_ref=source["configuration_ref"],
                secret_ref=None,
            )
            for source, artifact in zip(fixture["sources"], artifacts, strict=True)
        ),
        authority_bindings=tuple(
            AuthorityBindingV1(
                request_id=source["authority_request_id"],
                authority="source_read",
                grant_ref=source["grant_ref"],
            )
            for source in fixture["sources"]
        ),
    )
    revision = prepare_activation_revision(
        spec=spec,
        state=ActivationState.ACTIVE,
        actor_ref=fixture["actor_ref"],
        approval_receipt_ref=fixture["activation"]["approval_receipt_ref"],
        occurred_at=_time(fixture["activation"]["occurred_at"]),
    )
    activation_store = MemoryGovernedStateStore()
    activation_service = DomainActivationAdmissionService(
        store=activation_store,
        authority=ExactActivationAuthority(),
    )
    committed = await activation_service.admit(
        revision,
        expected_head_revision_id=None,
        committed_at=_time(fixture["activation"]["committed_at"]),
    )
    activation_head = activation_store.heads[("domain_activation", product_id, committed.revision.activation_id)]

    heads: list[GovernedStateHeadV1] = []
    runtime_bindings: list[RuntimeBinding] = []
    definitions: list[ResolvedSourceDefinitionV1Alpha1] = []
    requests: list[LiveSourceIngressRequestV1Alpha1] = []
    for index, (source, artifact) in enumerate(
        zip(fixture["sources"], artifacts, strict=True),
        start=1,
    ):
        capability_head = _head(
            product_id=product_id,
            state_kind="capability_state",
            state_id=capability_state_ref_for_artifact(artifact),
            sequence=index,
            updated_at=_time(fixture["activation"]["committed_at"]),
        )
        grant_head = _head(
            product_id=product_id,
            state_kind="authority_grant",
            state_id=source["grant_ref"],
            sequence=index + 10,
            updated_at=_time(fixture["activation"]["committed_at"]),
        )
        source_head = _head(
            product_id=product_id,
            state_kind="source_definition",
            state_id=source["source_definition_ref"],
            sequence=index + 20,
            updated_at=_time(fixture["activation"]["committed_at"]),
        )
        heads.extend((capability_head, grant_head, source_head))
        runtime_bindings.append(
            RuntimeBinding(
                artifact=artifact,
                configuration_ref=source["configuration_ref"],
                capability_head=capability_head,
                grant_ref=source["grant_ref"],
                grant_hash=source["grant_hash"],
                grant_head=grant_head,
            )
        )
        definitions.append(
            ResolvedSourceDefinitionV1Alpha1(
                product_id=product_id,
                source_definition_ref=source["source_definition_ref"],
                source_type_ref=source["source_type_ref"],
                configuration_ref=source["configuration_ref"],
                configuration_digest=source["configuration_digest"],
                authorized_uri=source["requested_uri"],
                subject_binding_id=source.get("subject_binding_id", fixture["subject_binding_id"]),
                entity_type_id=source.get("entity_type_id", fixture["entity_type_id"]),
                entity_ref=source.get("entity_ref", fixture["entity_ref"]),
                state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(source_head),
            )
        )
        requests.append(
            LiveSourceIngressRequestV1Alpha1(
                product_id=product_id,
                authenticated_context=context,
                idempotency_key=source["idempotency_key"],
                activation_key=fixture["activation_key"],
                mapping_id=source["mapping_id"],
                source_definition_ref=source["source_definition_ref"],
                compiled_pack_id=pack.compiled_pack_id,
                pack_digest=pack.pack_digest,
                requested_at=_time(source["requested_at"]),
            )
        )

    first, second, *_ = fixture["sources"]
    federal_transport = RecordedTransport(
        FederalRegisterRetrievalResult(
            source_type_ref=AI_POLICY_SOURCE_TYPE,
            requested_uri=AI_POLICY_DOCUMENT_URI,
            effective_uri=AI_POLICY_DOCUMENT_URI,
            status_code=200,
            media_type=first["media_type"],
            response_body=first["response_body"],
            redirect_chain=(),
            resolved_ip_addresses=("1.1.1.1",),
            connected_ip_addresses=("1.1.1.1",),
            dns_rebinding_protection_applied=True,
            credentials_used=False,
            locator=AI_POLICY_LOCATOR,
            observed_at=_time(first["observed_at"]),
            captured_at=_time(first["captured_at"]),
        )
    )
    white_house_transport = RecordedTransport(
        WhiteHouseRetrievalResult(
            source_type_ref=WHITE_HOUSE_SOURCE_TYPE,
            requested_uri=WHITE_HOUSE_RELEASE_URI,
            effective_uri=WHITE_HOUSE_RELEASE_URI,
            status_code=200,
            media_type=second["media_type"],
            response_body=second["response_body"],
            redirect_chain=(),
            resolved_ip_addresses=("1.1.1.1",),
            connected_ip_addresses=("1.1.1.1",),
            dns_rebinding_protection_applied=True,
            credentials_used=False,
            locator=WHITE_HOUSE_LOCATOR,
            observed_at=_time(second["observed_at"]),
            captured_at=_time(second["captured_at"]),
        )
    )
    policy_adapters = (
        AIPolicyFederalRegisterSourceAdapter(
            transport=federal_transport,
            artifact_digest=artifacts[0].artifact_digest,
        ),
        WhiteHouseAIPolicySourceAdapter(
            transport=white_house_transport,
            artifact_digest=artifacts[1].artifact_digest,
        ),
    )
    reviewed_transports = tuple(
        RecordedTransport(
            ReviewedAIPublicationRetrievalResult(
                source_type_ref=REVIEWED_AI_PUBLICATION_SOURCE_TYPE,
                requested_uri=source["requested_uri"],
                effective_uri=source["requested_uri"],
                status_code=200,
                media_type=source["media_type"],
                response_body=source["response_body"],
                redirect_chain=(),
                resolved_ip_addresses=("1.1.1.1",),
                connected_ip_addresses=("1.1.1.1",),
                dns_rebinding_protection_applied=True,
                credentials_used=False,
                locator=REVIEWED_AI_PUBLICATION_LOCATOR,
                observed_at=_time(source["observed_at"]),
                captured_at=_time(source["captured_at"]),
            )
        )
        for source in fixture["sources"][2:]
    )
    reviewed_adapters = tuple(
        ReviewedAIPublicationSourceAdapter(
            profile=reviewed_profiles_by_uri[source["requested_uri"]],
            transport=transport,
            artifact_digest=artifact.artifact_digest,
        )
        for source, transport, artifact in zip(
            fixture["sources"][2:],
            reviewed_transports,
            reviewed_artifacts,
            strict=True,
        )
    )
    adapters = (*policy_adapters, *reviewed_adapters)

    append_head = _head(
        product_id=product_id,
        state_kind="governed_operation_configuration",
        state_id="governed_operation_configuration:world-ai-live-append",
        sequence=40,
        updated_at=_time(fixture["activation"]["committed_at"]),
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=APPEND_ARTIFACT,
        configuration_ref=append_head.state_id,
        authority="append_immutable_records",
        grant_ref="authority_grant:world-ai-live-append",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(append_head),
    )
    store = InMemoryImmutableRecordStore()
    for head in (activation_head, *heads, append_head):
        store.set_governed_state_head(head)
    return CommandCenterEnvironment(
        fixture=fixture,
        pack=pack,
        context=context,
        activation_service=activation_service,
        committed_activation=committed,
        store=store,
        definitions=ExactSourceDefinitions(tuple(definitions)),
        runtime_use=ExactRuntimeUse(
            context=context,
            bindings=tuple(runtime_bindings),
        ),
        registry=ExactAdapterRegistry(adapters),
        requests=tuple(requests),
        adapters=adapters,
        transports=(federal_transport, white_house_transport, *reviewed_transports),
        append_binding=append_binding,
        activation_head=activation_head,
        append_head=append_head,
    )


async def admit_sources(environment: CommandCenterEnvironment):
    admissions = []
    for source, request in zip(
        environment.fixture["sources"],
        environment.requests,
        strict=True,
    ):
        service = environment.ingress(
            SequenceClock(
                _time(source["capture_started_at"]),
                _time(source["rechecked_at"]),
                _time(source["admitted_at"]),
            )
        )
        admission = await service.admit(request=request, pack=environment.pack)
        replay = await service.admit(request=request, pack=environment.pack)
        if admission.replayed or not replay.replayed:
            raise AssertionError("LIVE source admission replay was not explicit")
        admissions.append(admission)
    if [adapter.capture_calls for adapter in environment.adapters] != [1] * len(environment.adapters):
        raise AssertionError("each official source must be captured exactly once")
    if [transport.calls for transport in environment.transports] != [1] * len(environment.transports):
        raise AssertionError("recorded transports were reacquired during replay")
    return tuple(admissions)


def _lineage(resource, *, relation: LineageRelation) -> LineageReferenceV1Alpha1:
    reference = resource_reference(resource)
    return LineageReferenceV1Alpha1(
        resource_kind=LineageResourceKind(reference.resource_kind.value),
        relation=relation,
        resource_id=reference.resource_id,
        resource_digest=reference.resource_digest,
        resource_as_of=reference.as_of,
        resource_available_at=reference.available_at,
    )


async def _append_resource(
    *,
    environment: CommandCenterEnvironment,
    authorizer: ExactAppendAuthorizer,
    resource,
    transaction_key: str,
    submitted_at: datetime,
) -> None:
    authorization = await authorizer.authorize_action(
        GovernedActionAuthorizationRequestV1Alpha1(
            authorization_key=f"append:{resource.resource_id}",
            product_id=resource.product_id,
            authenticated_context=environment.context,
            execution_binding=environment.append_binding,
            operation="append_immutable_records",
            subject_ref=str(resource.resource_id),
            subject_digest=str(resource.resource_digest),
            requested_at=submitted_at,
            required_state_preconditions=(
                GovernedStateHeadPreconditionV1Alpha1.from_head(environment.activation_head),
                GovernedStateHeadPreconditionV1Alpha1.from_head(environment.append_head),
            ),
        )
    )
    record = ImmutableRecordV1(
        product_id=resource.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        record_kind=resource_kind(resource).value,
        record_key=str(resource.resource_id),
        payload_contract=resource.contract,
        payload=resource.model_dump(mode="python"),
        as_of=resource.as_of,
        available_at=resource_available_at(resource),
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=resource.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        transaction_key=transaction_key,
        records=(record,),
        submitted_at=submitted_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError("LIVE resource append did not preserve exact receipt material")


def _brief_draft(*, observations, shift, signal, case, policy):
    baseline, current = observations
    baseline_id = str(baseline.resource_id)
    current_id = str(current.resource_id)
    sections = {
        "what_changed": BriefDraftClaimV1Alpha1(
            statement=(
                "Executive Order 14409 moved from publication to reported implementation: the "
                "White House says GOLD EAGLE has begun accepting and prioritizing identified "
                "cybersecurity vulnerabilities."
            ),
            grounding_kind=ClaimGroundingKind.INFERENCE,
            support_refs=(str(case.resource_id),),
            confidence=0.9,
            uncertainty=(
                "The progression classifies admitted publication metadata; it does not establish "
                "legal effect, operational completeness, or policy success."
            ),
        ),
        "how_we_know": BriefDraftClaimV1Alpha1(
            statement=(
                "The change is supported by two admitted records: the published Federal Register "
                "order and a later White House release connecting GOLD EAGLE to that order and "
                "reporting that intake and prioritization had begun."
            ),
            grounding_kind=ClaimGroundingKind.CITED,
            support_refs=(baseline_id, current_id),
            confidence=1.0,
        ),
        "why_it_matters": BriefDraftClaimV1Alpha1(
            statement=(
                "This matters because the policy now has a reported operating mechanism, not only "
                "a directive. The next evidence to watch is implementation scope, prioritization "
                "criteria, agency follow-through, and independently measured outcomes."
            ),
            grounding_kind=ClaimGroundingKind.INFERENCE,
            support_refs=(str(signal.resource_id),),
            confidence=0.85,
            uncertainty="Materiality is the declared routing policy, not a measured real-world impact.",
        ),
        "when_it_changed": BriefDraftClaimV1Alpha1(
            statement=(
                "The directive was published on June 5, 2026. The White House reported the "
                "implementation activity on July 14, 2026—39 days later."
            ),
            grounding_kind=ClaimGroundingKind.CITED,
            support_refs=(baseline_id, current_id),
            confidence=1.0,
        ),
        "unknowns": BriefDraftClaimV1Alpha1(
            statement=(
                "No admitted source yet shows how many vulnerabilities entered the program, how "
                "priorities were set, which agencies acted, or whether the activity improved "
                "cybersecurity outcomes."
            ),
            grounding_kind=ClaimGroundingKind.INFERENCE,
            support_refs=(str(shift.resource_id),),
            confidence=0.8,
            uncertainty="Additional official and independent evidence may change this assessment.",
        ),
        "limitations": BriefDraftClaimV1Alpha1(
            statement=(
                "Both records are U.S. government publications. They establish what the government "
                "issued and later reported, but they do not independently verify implementation or "
                "results."
            ),
            grounding_kind=ClaimGroundingKind.CITED,
            support_refs=(baseline_id, current_id),
            confidence=1.0,
        ),
    }
    return BriefSynthesisDraftV1Alpha1(
        brief_type=policy.template.brief_type,
        persona_ids=tuple(item.persona_id for item in policy.personas),
        sections=tuple(
            BriefDraftSectionV1Alpha1(
                section_id=section_id,
                claims=(sections[section_id],),
            )
            for section_id in policy.template.required_sections
        ),
        recommendation_claim_id=None,
    )


async def run_acceptance(*, state_sink: dict[str, Any] | None = None) -> dict[str, Any]:
    environment = await build_environment()
    baseline, current, *context_admissions = await admit_sources(environment)
    authorizer = ExactAppendAuthorizer()
    binding = bind_committed_activation(
        pack=environment.pack,
        committed=environment.committed_activation,
    )
    derivation_fixture = environment.fixture["derivation"]

    def snapshot_reference(admission):
        available_at = next(
            item.available_at for item in admission.transaction_receipt.records if item.record_kind == "entity_snapshot"
        )
        return resource_reference(admission.entity_snapshot).model_copy(update={"available_at": available_at})

    derivation_request = LiveDerivationRequestV1Alpha1(
        derivation_key=derivation_fixture["derivation_key"],
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        activation_revision=binding.prepared_binding.reference,
        pack=binding.prepared_binding.revision.spec.pack,
        detector_id=derivation_fixture["detector_id"],
        baseline=snapshot_reference(baseline),
        current=snapshot_reference(current),
        detected_at=_time(derivation_fixture["detected_at"]),
        attention_evaluated_at=_time(derivation_fixture["attention_evaluated_at"]),
        requested_at=_time(derivation_fixture["requested_at"]),
    )
    bridge = LiveIntelligenceBridgeService(
        activation_service=environment.activation_service,
        pack=environment.pack,
        store=environment.store,
        authorizer=authorizer,
        operation_binding=environment.append_binding,
    )
    derivation = await bridge.derive(derivation_request)
    derivation_replay = await bridge.derive(derivation_request)
    if derivation.replayed or not derivation_replay.replayed:
        raise AssertionError("LIVE Shift/Signal replay was not explicit")

    observations = (baseline.observation, current.observation)
    case_time = _time(environment.fixture["case"]["assembled_at"])
    case = CaseV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=binding.prepared_binding.reference,
        as_of=max(
            derivation.signal.as_of,
            *(item.as_of for item in observations),
        ),
        lineage=(
            _lineage(derivation.shift, relation=LineageRelation.DERIVED_FROM),
            _lineage(derivation.signal, relation=LineageRelation.DERIVED_FROM),
            *(_lineage(item, relation=LineageRelation.SUPPORTS) for item in observations),
        ),
        case_type_ref="case_type:ai_policy_progression",
        title="Executive Order 14409 to reported GOLD EAGLE implementation",
        purpose=("Freeze the exact two-lineage official-source progression before cited synthesis."),
        subject_refs=(environment.fixture["entity_ref"],),
        assembled_at=case_time,
    )
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=case,
        transaction_key="live-case:ai-policy:eo-14409-to-gold-eagle",
        submitted_at=case_time,
    )

    policy = resolve_brief_synthesis_policy(
        binding.prepared_binding,
        template_id=str(derivation.attention_receipt.brief_template_id),
        persona_ids=derivation.attention_receipt.persona_ids,
    )
    closure = (
        *observations,
        derivation.shift,
        derivation.signal,
        case,
    )
    draft = _brief_draft(
        observations=observations,
        shift=derivation.shift,
        signal=derivation.signal,
        case=case,
        policy=policy,
    )
    brief_time = _time(environment.fixture["brief"]["generated_at"])
    assembly = assemble_canonical_brief(
        product_id=environment.fixture["product_id"],
        activation_revision=binding.prepared_binding.reference,
        brief_as_of=_time(environment.fixture["brief"]["as_of"]),
        generated_at=brief_time,
        draft=draft,
        policy=policy,
        closure=closure,
        observations=observations,
        selected_context=(),
        mode=IntelligenceResourceMode.LIVE,
    )
    brief = assembly.brief
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=brief,
        transaction_key="live-brief:ai-policy:eo-14409-to-gold-eagle",
        submitted_at=brief_time,
    )

    stored_case = await environment.store.load_record(
        immutable_record_storage_id(
            product_id=case.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind="case",
            record_key=str(case.resource_id),
        ),
        product_id=case.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        record_kind="case",
    )
    stored_brief = await environment.store.load_record(
        immutable_record_storage_id(
            product_id=brief.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind="brief",
            record_key=str(brief.resource_id),
        ),
        product_id=brief.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        record_kind="brief",
    )
    if stored_case is None or stored_brief is None:
        raise AssertionError("LIVE Case or Reality Brief was not durably reopened")

    if state_sink is not None:
        state_sink.update(
            {
                "environment": environment,
                "baseline": baseline,
                "current": current,
                "context_admissions": tuple(context_admissions),
                "derivation": derivation,
                "case": case,
                "brief": brief,
            }
        )

    return {
        "contract": "ace.world-intelligence.ai-command-center-live-proof/v1alpha2",
        "pack": {
            "compiled_pack_id": environment.pack.compiled_pack_id,
            "pack_digest": environment.pack.pack_digest,
            "module_count": len(environment.pack.modules),
            "json_only": True,
        },
        "source": {
            "modes": [item.observation.mode.value for item in (baseline, current, *context_admissions)],
            "lineages": [
                item.entity_snapshot.attributes.parsed_value()["source_lineage_id"]
                for item in (baseline, current, *context_admissions)
            ],
            "stages": [
                item.entity_snapshot.attributes.parsed_value()["development_stage"] for item in (baseline, current)
            ],
            "stable_entity_ref": (
                baseline.entity_snapshot.entity_ref
                == current.entity_snapshot.entity_ref
                == environment.fixture["entity_ref"]
            ),
            "capture_calls": [item.capture_calls for item in environment.adapters],
            "context_watch_areas": sorted(
                item.entity_snapshot.attributes.parsed_value()["watch_area"] for item in context_admissions
            ),
            "publisher_count": len(
                {item.entity_snapshot.attributes.parsed_value()["publisher"] for item in context_admissions}
            ),
            "recorded_transport": True,
            "network_access": False,
        },
        "intelligence": {
            "shift_id": str(derivation.shift.resource_id),
            "shift_type": derivation.shift.shift_type_ref,
            "signal_id": str(derivation.signal.resource_id),
            "signal_type": derivation.signal.signal_type_ref,
            "attention": derivation.attention_receipt.disposition.value,
            "case_id": str(case.resource_id),
            "case_member_count": len(case.lineage),
            "brief_id": str(brief.resource_id),
            "brief_digest": str(brief.resource_digest),
            "brief_mode": brief.mode.value,
            "citation_count": len(brief.citations),
            "claim_count": len(brief.claims),
            "cited_source_refs": sorted(citation.source_ref for citation in brief.citations),
        },
        "separation": {
            "live_record_count": sum(
                1 for record in environment.store.records.values() if record.record_space == LIVE_SOURCE_RECORD_SPACE
            ),
            "prepared_record_count": sum(
                1 for record in environment.store.records.values() if record.record_space == "prepared"
            ),
            "prepared_material_reused": False,
            "autonomous_publication": False,
            "external_action": False,
        },
    }


def main() -> None:
    print(json.dumps(asyncio.run(run_acceptance()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
