"""Hermetic P2D LIVE conflict, correction, supersession, and Reality Brief proof."""

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
    CapabilityArtifactIdentityV1Alpha1,
    GovernedActionAuthorizationRequestV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    ImmutableRecordV1,
    ResolvedSourceDefinitionV1Alpha1,
    canonical_hash,
    canonical_json,
    capability_state_ref_for_artifact,
    immutable_record_storage_id,
)
from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    CapabilityBindingV1,
    CaseV1Alpha1,
    ClaimGroundingKind,
    IntelligenceResourceMode,
    LineageRelation,
    LineageResourceKind,
    LiveDerivationRequestV1Alpha1,
    LiveSourceIngressRequestV1Alpha1,
    OrganizationOverlayV1,
    resource_reference,
)
from ace.intelligence.contracts.epistemic import (
    BRIEF_DERIVATION_FAMILY_STATUS_PROJECTION_KIND,
    BriefDraftClaimStatusBindingV1Alpha1,
    BriefEpistemicStatusProjectionV1Alpha2,
    DerivationFamilyMembershipV1Alpha1,
)
from ace.intelligence.contracts.ledger import resource_available_at, resource_kind
from ace.intelligence.contracts.resources import (
    CanonicalJsonValueV1Alpha1,
    EvidenceAcquisitionMode,
    ObservationV1Alpha1,
)
from ace.intelligence.contracts.supersession import (
    SUPERSESSION_IMPACT_PROJECTION_KIND,
    SupersessionClaimImpactV1Alpha1,
    SupersessionImpactPathV1Alpha1,
    SupersessionImpactProjectionV1Alpha1,
)
from ace.intelligence.contracts.synthesis import BriefSynthesisDraftV1Alpha2
from ace.intelligence.derivation import (
    COLLAPSING_RELATIONS,
    DERIVATION_FAMILY_POLICY,
    derive_observation_families,
)
from ace.intelligence.epistemic import derive_claim_epistemic_statuses_with_families
from ace.intelligence.packs import (
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
)
from ace.intelligence.packs.runtime import (
    resolve_brief_synthesis_policy,
    resolve_epistemic_status_policy,
)
from ace.intelligence.supersession import (
    IMPACT_RELATIONS,
    SUPERSESSION_IMPACT_POLICY,
    SupersessionImpactError,
    project_claim_impact,
    project_supersession_impact,
)
from ace.intelligence.synthesis import assemble_canonical_brief
from ace.testing import InMemoryImmutableRecordStore
from ace_world_federal_register_source import (
    ESA_PLANETARY_DEFENCE_IMPLEMENTATION_ID,
    NASA_PLANETARY_DEFENSE_IMPLEMENTATION_ID,
    PLANETARY_DEFENSE_IMPLEMENTATION_VERSION,
    PlanetaryDefenseRetrievalResult,
    PlanetaryDefenseSourceAdapter,
)

from scripts.ai_command_center_live_acceptance import (
    ExactAdapterRegistry,
    ExactAppendAuthorizer,
    ExactRuntimeUse,
    ExactSourceDefinitions,
    RuntimeBinding,
    _head,
    _lineage,
)
from scripts.p2c_federal_register_live_acceptance import (
    ExactActivationAuthority,
    MemoryGovernedStateStore,
    SequenceClock,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense"
FIXTURE_PATH = PACK_ROOT / "conformance" / "p2d_live_conflict_correction_input.json"
LIVE_BRIEF_ASSEMBLY_RECEIPT_KIND = "live_brief_assembly_receipt"
LIVE_BRIEF_ASSEMBLY_RECEIPT_CONTRACT = "ace.world-intelligence.live-brief-assembly-receipt/v1alpha1"
APPEND_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="append_immutable_records",
    contract="ace.core.immutable-record-appender/v1alpha1",
    implementation_id="world_planetary_defense_live_append_fixture",
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


def compile_planetary_defense_pack():
    manifest_bytes = (PACK_ROOT / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    return compile_pack_document(
        manifest_bytes,
        {item["path"]: (PACK_ROOT / item["path"]).read_bytes() for item in manifest["resources"]},
    )


class RecordedPublicationTransport:
    """Network-free exact results keyed by reviewed URI."""

    def __init__(self, results: tuple[PlanetaryDefenseRetrievalResult, ...]) -> None:
        self.results = {item.requested_uri: item for item in results}
        self.calls: dict[str, int] = {item.requested_uri: 0 for item in results}

    async def retrieve(self, request):
        result = self.results.get(request.requested_uri)
        if result is None:
            raise ValueError("recorded transport crossed its exact URI set")
        self.calls[request.requested_uri] += 1
        return result


@dataclass
class P2DEnvironment:
    fixture: dict[str, Any]
    pack: Any
    context: AuthenticatedRuntimeContextV1Alpha1
    activation_service: DomainActivationAdmissionService
    committed_activation: Any
    store: InMemoryImmutableRecordStore
    definitions: ExactSourceDefinitions
    runtime_use: ExactRuntimeUse
    registry: ExactAdapterRegistry
    requests: dict[str, LiveSourceIngressRequestV1Alpha1]
    source_fixtures: dict[str, dict[str, Any]]
    adapters: dict[str, PlanetaryDefenseSourceAdapter]
    transports: dict[str, RecordedPublicationTransport]
    append_binding: GovernedOperationBindingV1Alpha1
    activation_head: Any
    append_head: Any

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


@dataclass(frozen=True, slots=True)
class P2DExecution:
    """Exact P2D projection plus the LIVE material used by later consumer proofs."""

    projection: dict[str, Any]
    environment: P2DEnvironment
    admissions: dict[str, Any]
    divergence: Any
    nasa_revision: Any
    esa_revision: Any
    historical_case: CaseV1Alpha1
    historical_brief: Any
    corrected_case: CaseV1Alpha1
    corrected_brief: Any


def _artifact(claimant: dict[str, Any]) -> CapabilityArtifactIdentityV1Alpha1:
    implementation_id = {
        "NASA": NASA_PLANETARY_DEFENSE_IMPLEMENTATION_ID,
        "ESA": ESA_PLANETARY_DEFENCE_IMPLEMENTATION_ID,
    }[claimant["claimant_org"]]
    return CapabilityArtifactIdentityV1Alpha1(
        capability="source_snapshot",
        contract="ace.source.snapshot/v1alpha1",
        implementation_id=implementation_id,
        implementation_version=PLANETARY_DEFENSE_IMPLEMENTATION_VERSION,
        artifact_digest=claimant["artifact_digest"],
    )


async def build_environment() -> P2DEnvironment:
    fixture = load_fixture()
    pack = compile_planetary_defense_pack()
    product_id = fixture["product_id"]
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=product_id,
        actor_ref=fixture["actor_ref"],
        authentication_receipt_ref=fixture["authentication"]["receipt_ref"],
        authentication_receipt_digest=fixture["authentication"]["receipt_digest"],
        authenticated_at=_time(fixture["authentication"]["authenticated_at"]),
        expires_at=_time(fixture["authentication"]["expires_at"]),
    )
    claimants = {item["claimant_org"]: item for item in fixture["claimants"]}
    artifacts = {name: _artifact(item) for name, item in claimants.items()}
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
                requirement_id=item["capability_requirement_id"],
                capability=artifacts[name].capability,
                contract=artifacts[name].contract,
                implementation_id=artifacts[name].implementation_id,
                implementation_version=artifacts[name].implementation_version,
                artifact_digest=artifacts[name].artifact_digest,
                configuration_ref=item["configuration_ref"],
                secret_ref=None,
            )
            for name, item in claimants.items()
        ),
        authority_bindings=tuple(
            AuthorityBindingV1(
                request_id=item["authority_request_id"],
                authority="source_read",
                grant_ref=item["grant_ref"],
            )
            for item in claimants.values()
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

    heads = []
    runtime_bindings = []
    for index, (name, item) in enumerate(claimants.items(), start=1):
        artifact = artifacts[name]
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
            state_id=item["grant_ref"],
            sequence=index + 10,
            updated_at=_time(fixture["activation"]["committed_at"]),
        )
        heads.extend((capability_head, grant_head))
        runtime_bindings.append(
            RuntimeBinding(
                artifact=artifact,
                configuration_ref=item["configuration_ref"],
                capability_head=capability_head,
                grant_ref=item["grant_ref"],
                grant_hash=item["grant_hash"],
                grant_head=grant_head,
            )
        )

    definitions = []
    requests = {}
    source_fixtures = {item["source_key"]: item for item in fixture["sources"]}
    source_heads = []
    for index, source in enumerate(fixture["sources"], start=1):
        claimant = claimants[source["claimant_org"]]
        source_head = _head(
            product_id=product_id,
            state_kind="source_definition",
            state_id=source["source_definition_ref"],
            sequence=index + 20,
            updated_at=_time(fixture["activation"]["committed_at"]),
        )
        source_heads.append(source_head)
        definitions.append(
            ResolvedSourceDefinitionV1Alpha1(
                product_id=product_id,
                source_definition_ref=source["source_definition_ref"],
                source_type_ref=claimant["source_type_ref"],
                configuration_ref=claimant["configuration_ref"],
                configuration_digest=claimant["configuration_digest"],
                authorized_uri=source["requested_uri"],
                subject_binding_id=fixture["subject_binding_id"],
                entity_type_id=fixture["entity_type_id"],
                entity_ref=fixture["entity_ref"],
                state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(source_head),
            )
        )
        requests[source["source_key"]] = LiveSourceIngressRequestV1Alpha1(
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

    results_by_claimant: dict[str, list[PlanetaryDefenseRetrievalResult]] = {
        "NASA": [],
        "ESA": [],
    }
    for source in fixture["sources"]:
        claimant = claimants[source["claimant_org"]]
        results_by_claimant[source["claimant_org"]].append(
            PlanetaryDefenseRetrievalResult(
                source_type_ref=claimant["source_type_ref"],
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
                locator=source["locator"],
                observed_at=_time(source["observed_at"]),
                captured_at=_time(source["captured_at"]),
            )
        )
    transports = {name: RecordedPublicationTransport(tuple(results)) for name, results in results_by_claimant.items()}
    adapters = {
        name: PlanetaryDefenseSourceAdapter(
            transport=transports[name],
            artifact_digest=artifacts[name].artifact_digest,
            source_type_ref=claimants[name]["source_type_ref"],
        )
        for name in claimants
    }
    append_head = _head(
        product_id=product_id,
        state_kind="governed_operation_configuration",
        state_id="governed_operation_configuration:world-planetary-defense-live-append",
        sequence=50,
        updated_at=_time(fixture["activation"]["committed_at"]),
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=APPEND_ARTIFACT,
        configuration_ref=append_head.state_id,
        authority="append_immutable_records",
        grant_ref="authority_grant:world-planetary-defense-live-append",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(append_head),
    )
    store = InMemoryImmutableRecordStore()
    for head in (activation_head, *heads, *source_heads, append_head):
        store.set_governed_state_head(head)
    return P2DEnvironment(
        fixture=fixture,
        pack=pack,
        context=context,
        activation_service=activation_service,
        committed_activation=committed,
        store=store,
        definitions=ExactSourceDefinitions(tuple(definitions)),
        runtime_use=ExactRuntimeUse(context=context, bindings=tuple(runtime_bindings)),
        registry=ExactAdapterRegistry(tuple(adapters.values())),
        requests=requests,
        source_fixtures=source_fixtures,
        adapters=adapters,
        transports=transports,
        append_binding=append_binding,
        activation_head=activation_head,
        append_head=append_head,
    )


async def _append_record(
    *,
    environment: P2DEnvironment,
    authorizer: ExactAppendAuthorizer,
    record: ImmutableRecordV1,
    subject_ref: str,
    subject_digest: str,
    transaction_key: str,
    submitted_at: datetime,
) -> bool:
    authorization = await authorizer.authorize_action(
        GovernedActionAuthorizationRequestV1Alpha1(
            authorization_key=f"append:{subject_ref}",
            product_id=record.product_id,
            authenticated_context=environment.context,
            execution_binding=environment.append_binding,
            operation="append_immutable_records",
            subject_ref=subject_ref,
            subject_digest=subject_digest,
            requested_at=submitted_at,
            required_state_preconditions=(
                GovernedStateHeadPreconditionV1Alpha1.from_head(environment.activation_head),
                GovernedStateHeadPreconditionV1Alpha1.from_head(environment.append_head),
            ),
        )
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=record.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        transaction_key=transaction_key,
        records=(record,),
        submitted_at=submitted_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    prior = await environment.store.load_transaction_receipt(
        product_id=record.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        transaction_key=transaction_key,
    )
    if prior is not None:
        if prior != append.receipt():
            raise AssertionError("LIVE append replay crossed exact transaction material")
        return True
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError("LIVE append did not preserve exact receipt material")
    return False


async def _append_resource(
    *,
    environment: P2DEnvironment,
    authorizer: ExactAppendAuthorizer,
    resource,
    transaction_key: str,
    submitted_at: datetime,
) -> bool:
    return await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=ImmutableRecordV1(
            product_id=resource.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind=resource_kind(resource).value,
            record_key=str(resource.resource_id),
            payload_contract=resource.contract,
            payload=resource.model_dump(mode="python"),
            as_of=resource.as_of,
            available_at=resource_available_at(resource),
            processing_order=0,
        ),
        subject_ref=str(resource.resource_id),
        subject_digest=str(resource.resource_digest),
        transaction_key=transaction_key,
        submitted_at=submitted_at,
    )


async def _admit_source(environment: P2DEnvironment, source_key: str):
    source = environment.source_fixtures[source_key]
    service = environment.ingress(
        SequenceClock(
            _time(source["capture_started_at"]),
            _time(source["rechecked_at"]),
            _time(source["admitted_at"]),
        )
    )
    admission = await service.admit(
        request=environment.requests[source_key],
        pack=environment.pack,
    )
    replay = await service.admit(
        request=environment.requests[source_key],
        pack=environment.pack,
    )
    if admission.replayed or not replay.replayed:
        raise AssertionError("LIVE source admission replay was not explicit")
    return admission


def _snapshot_reference(admission):
    available_at = next(
        item.available_at for item in admission.transaction_receipt.records if item.record_kind == "entity_snapshot"
    )
    return resource_reference(admission.entity_snapshot).model_copy(update={"available_at": available_at})


async def _derive(
    environment: P2DEnvironment,
    *,
    authorizer: ExactAppendAuthorizer,
    binding,
    derivation_fixture: dict[str, Any],
    admissions: dict[str, Any],
):
    request = LiveDerivationRequestV1Alpha1(
        derivation_key=derivation_fixture["derivation_key"],
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        activation_revision=binding.prepared_binding.reference,
        pack=binding.prepared_binding.revision.spec.pack,
        detector_id=derivation_fixture["detector_id"],
        baseline=_snapshot_reference(admissions[derivation_fixture["baseline_source_key"]]),
        current=_snapshot_reference(admissions[derivation_fixture["current_source_key"]]),
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
    admission = await bridge.derive(request)
    replay = await bridge.derive(request)
    if admission.replayed or not replay.replayed:
        raise AssertionError("LIVE Shift/Signal replay was not explicit")
    return admission


def _draft(policy, specifications: tuple[dict[str, Any], ...]) -> BriefSynthesisDraftV1Alpha2:
    claims = tuple(
        BriefDraftClaimV1Alpha1(
            statement=item["statement"],
            grounding_kind=item["grounding_kind"],
            support_refs=tuple(str(resource.resource_id) for resource in item["supports"]),
            confidence=item["confidence"],
            uncertainty=item.get("uncertainty"),
        )
        for item in specifications
    )
    return BriefSynthesisDraftV1Alpha2(
        brief_type=policy.template.brief_type,
        persona_ids=tuple(item.persona_id for item in policy.personas),
        sections=tuple(
            BriefDraftSectionV1Alpha1(
                section_id=specification["section_id"],
                claims=(claim,),
            )
            for specification, claim in zip(specifications, claims, strict=True)
        ),
        claim_statuses=tuple(
            BriefDraftClaimStatusBindingV1Alpha1(
                draft_claim_id=str(claim.claim_id),
                status_id=specification["status_id"],
            )
            for specification, claim in zip(specifications, claims, strict=True)
        ),
        recommendation_claim_id=None,
    )


def _historical_draft(policy, *, observations, derivation, case):
    esa, nasa = observations
    return _draft(
        policy,
        (
            {
                "section_id": "what_changed",
                "statement": (
                    "ACE detected a material dated difference between ESA's 1.8% estimate "
                    "and NASA's next-day 2.3% estimate for the same 2032 Earth-impact event."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (case,),
                "confidence": 0.9,
                "uncertainty": ("The detector reports quantitative divergence, not which estimate was more accurate."),
                "status_id": "ace_inference",
            },
            {
                "section_id": "established_records",
                "statement": (
                    "NASA's 7 February 2025 publication reported a 2.3% Earth-impact probability for 22 December 2032."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (nasa,),
                "confidence": 1.0,
                "status_id": "attributed_claim",
            },
            {
                "section_id": "source_comparison",
                "statement": (
                    "ESA's 6 February 2025 publication reported a 1.8% Earth-impact risk for 22 December 2032."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (esa,),
                "confidence": 1.0,
                "status_id": "attributed_claim",
            },
            {
                "section_id": "where_sources_conflict",
                "statement": (
                    "The admitted NASA and ESA publications carried materially different "
                    "dated estimates for the same event."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (esa, nasa, derivation.shift),
                "confidence": 0.95,
                "uncertainty": (
                    "The estimates were published on different dates while new observations "
                    "were arriving, so the difference is not evidence of misconduct or falsehood."
                ),
                "status_id": "disputed",
            },
            {
                "section_id": "current_orientation",
                "statement": (
                    "At this historical cutoff, the admitted official record consists of the "
                    "ESA 1.8% and NASA 2.3% dated estimates."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (esa, nasa),
                "confidence": 1.0,
                "status_id": "admitted_record",
            },
            {
                "section_id": "correction_visibility",
                "statement": "No later correction is admitted inside this historical cutoff.",
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (derivation.signal,),
                "confidence": 0.8,
                "uncertainty": "Later source records may revise either estimate.",
                "status_id": "unknown",
            },
            {
                "section_id": "unknowns",
                "statement": (
                    "The historical Case does not establish the eventual Earth-impact estimate "
                    "or which later observations will narrow the modeled trajectory."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (case,),
                "confidence": 0.8,
                "uncertainty": "The estimate is expected to evolve with additional observations.",
                "status_id": "unknown",
            },
            {
                "section_id": "limitations",
                "statement": (
                    "NASA and ESA are separate official claimant lineages, but these publications "
                    "do not prove independent measurements or a final impact outcome."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (esa, nasa),
                "confidence": 1.0,
                "status_id": "admitted_record",
            },
        ),
    )


def _corrected_draft(
    policy,
    *,
    observations,
    divergence,
    nasa_revision,
    esa_revision,
    assertions,
    case,
):
    esa_initial, nasa_initial, nasa_revised, esa_revised = observations
    nasa_assertion, esa_assertion = assertions
    return _draft(
        policy,
        (
            {
                "section_id": "what_changed",
                "statement": (
                    "Later official publications revised NASA's estimate from 2.3% to 0.004% "
                    "and ESA's estimate from 1.8% to 0.001%."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (case, nasa_revision.shift, esa_revision.shift),
                "confidence": 0.95,
                "uncertainty": (
                    "ACE classifies the admitted numeric changes; it does not reproduce the orbital models."
                ),
                "status_id": "ace_inference",
            },
            {
                "section_id": "established_records",
                "statement": (
                    "NASA published a 2.3% estimate on 7 February and a revised 0.004% estimate on 24 February 2025."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (nasa_initial, nasa_assertion),
                "confidence": 1.0,
                "status_id": "admitted_record",
            },
            {
                "section_id": "source_comparison",
                "statement": (
                    "ESA published a 1.8% estimate on 6 February and a revised 0.001% estimate on 25 February 2025."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (esa_initial, esa_assertion),
                "confidence": 1.0,
                "status_id": "admitted_record",
            },
            {
                "section_id": "where_sources_conflict",
                "statement": (
                    "The earlier NASA and ESA publications contained a material dated estimate "
                    "divergence before later observations narrowed both assessments."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (esa_initial, nasa_initial, divergence.shift),
                "confidence": 0.95,
                "uncertainty": (
                    "A dated estimate divergence is not a truth verdict and does not imply the "
                    "agencies used independent observation sets."
                ),
                "status_id": "disputed",
            },
            {
                "section_id": "current_orientation",
                "statement": (
                    "The later NASA and ESA publications independently report very low Earth-impact "
                    "estimates of 0.004% and 0.001%, respectively."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (nasa_assertion, esa_assertion),
                "confidence": 1.0,
                "status_id": "corroborated",
            },
            {
                "section_id": "correction_visibility",
                "statement": (
                    "The two later records explicitly supersede their same-source predecessors, "
                    "and the routed revision Signals preserve those corrections as additive LIVE material."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (
                    nasa_revised,
                    esa_revised,
                    nasa_revision.signal,
                    esa_revision.signal,
                ),
                "confidence": 0.95,
                "uncertainty": (
                    "Supersession impact identifies dependency and does not declare every affected claim false."
                ),
                "status_id": "ace_inference",
            },
            {
                "section_id": "unknowns",
                "statement": (
                    "The admitted publications do not establish independent measurement provenance, "
                    "future model revisions, or the asteroid's eventual physical trajectory."
                ),
                "grounding_kind": ClaimGroundingKind.INFERENCE,
                "supports": (case, divergence.signal),
                "confidence": 0.8,
                "uncertainty": "Additional observations and official revisions may change the assessment.",
                "status_id": "unknown",
            },
            {
                "section_id": "limitations",
                "statement": (
                    "All four citations are official publications from two claimant roots; they "
                    "do not constitute independent replication of the underlying orbital analysis."
                ),
                "grounding_kind": ClaimGroundingKind.CITED,
                "supports": (esa_initial, nasa_initial, nasa_assertion, esa_assertion),
                "confidence": 1.0,
                "status_id": "admitted_record",
            },
        ),
    )


def _record_kind_index(closure: tuple) -> dict[str, LineageResourceKind]:
    return {str(item.resource_id): LineageResourceKind(resource_kind(item).value) for item in closure}


async def _append_status_projection(
    *,
    environment: P2DEnvironment,
    authorizer: ExactAppendAuthorizer,
    binding,
    draft: BriefSynthesisDraftV1Alpha2,
    assembly,
    closure: tuple,
    template_id: str,
    generated_at: datetime,
    transaction_prefix: str,
):
    brief = assembly.brief
    status_policy = resolve_epistemic_status_policy(
        binding.prepared_binding,
        template_id=template_id,
    )
    families = derive_observation_families(closure=closure)
    claim_statuses = derive_claim_epistemic_statuses_with_families(
        draft=draft,
        policy=status_policy,
        claim_supports=assembly.claim_supports,
        kind_by_record_id=_record_kind_index(closure),
        families=families,
    )
    receipt_material = {
        "contract": LIVE_BRIEF_ASSEMBLY_RECEIPT_CONTRACT,
        "product_id": brief.product_id,
        "brief_id": str(brief.resource_id),
        "brief_digest": str(brief.resource_digest),
        "draft_id": str(draft.draft_id),
        "draft_digest": str(draft.draft_digest),
        "claim_supports": [item.model_dump(mode="json") for item in assembly.claim_supports],
        "created_at": generated_at.isoformat(),
    }
    receipt_hash = canonical_hash(receipt_material)
    receipt_id = f"live_brief_assembly_receipt:{receipt_hash[:32]}"
    receipt_digest = f"sha256:{receipt_hash}"
    receipt_payload = {
        **receipt_material,
        "receipt_id": receipt_id,
        "receipt_digest": receipt_digest,
    }
    await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=ImmutableRecordV1(
            product_id=brief.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind=LIVE_BRIEF_ASSEMBLY_RECEIPT_KIND,
            record_key=receipt_id,
            payload_contract=LIVE_BRIEF_ASSEMBLY_RECEIPT_CONTRACT,
            payload=receipt_payload,
            as_of=brief.as_of,
            available_at=generated_at,
            processing_order=0,
        ),
        subject_ref=receipt_id,
        subject_digest=receipt_digest,
        transaction_key=f"{transaction_prefix}:assembly-receipt",
        submitted_at=generated_at,
    )
    projection = BriefEpistemicStatusProjectionV1Alpha2(
        product_id=brief.product_id,
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=brief.activation_revision,
        brief_id=str(brief.resource_id),
        brief_digest=str(brief.resource_digest),
        synthesis_receipt_contract=LIVE_BRIEF_ASSEMBLY_RECEIPT_CONTRACT,
        synthesis_receipt_id=receipt_id,
        synthesis_receipt_digest=receipt_digest,
        module_id=status_policy.module_id,
        module_digest=status_policy.module_digest,
        status_set_id=status_policy.status_set.status_set_id,
        status_set_digest=status_policy.status_set_digest,
        template_id=status_policy.template_id,
        declared_status_ids=tuple(item.status_id for item in status_policy.status_set.statuses),
        claim_statuses=claim_statuses,
        derivation_family_policy=DERIVATION_FAMILY_POLICY,
        collapsing_relations=tuple(item.value for item in COLLAPSING_RELATIONS),
        closure_families=tuple(
            DerivationFamilyMembershipV1Alpha1(
                root_record_id=root,
                member_record_ids=members,
            )
            for root, members in families.members_by_root.items()
        ),
        as_of=brief.as_of,
        generated_at=generated_at,
    )
    replayed = await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=ImmutableRecordV1(
            product_id=brief.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind=BRIEF_DERIVATION_FAMILY_STATUS_PROJECTION_KIND,
            record_key=str(projection.projection_id),
            payload_contract=projection.contract,
            payload=projection.model_dump(mode="python"),
            as_of=projection.as_of,
            available_at=projection.generated_at,
            processing_order=0,
        ),
        subject_ref=str(projection.projection_id),
        subject_digest=str(projection.projection_digest),
        transaction_key=f"{transaction_prefix}:status-projection",
        submitted_at=generated_at,
    )
    if replayed:
        raise AssertionError("first LIVE status projection append unexpectedly replayed")
    exact_replay = await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=ImmutableRecordV1(
            product_id=brief.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind=BRIEF_DERIVATION_FAMILY_STATUS_PROJECTION_KIND,
            record_key=str(projection.projection_id),
            payload_contract=projection.contract,
            payload=projection.model_dump(mode="python"),
            as_of=projection.as_of,
            available_at=projection.generated_at,
            processing_order=0,
        ),
        subject_ref=str(projection.projection_id),
        subject_digest=str(projection.projection_digest),
        transaction_key=f"{transaction_prefix}:status-projection",
        submitted_at=generated_at,
    )
    return projection, families, exact_replay


def _supersession_assertion(
    *,
    environment: P2DEnvironment,
    binding,
    earlier,
    revised,
    asserted_at: datetime,
) -> ObservationV1Alpha1:
    revised_payload = revised.payload.parsed_value()
    earlier_lineage = earlier.payload.parsed_value()["source_lineage_id"]
    if revised_payload["predecessor_lineage_id"] != earlier_lineage:
        raise AssertionError("revised source does not name the exact same-source predecessor")
    payload = {
        "assertion": "supersedes",
        "claimant_org": revised_payload["claimant_org"],
        "predecessor_lineage_id": earlier_lineage,
        "revised_lineage_id": revised_payload["source_lineage_id"],
        "basis_observation_id": str(revised.resource_id),
        "superseded_observation_id": str(earlier.resource_id),
        "impact_is_dependency_not_falsehood": True,
    }
    return ObservationV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=binding.prepared_binding.reference,
        as_of=asserted_at,
        lineage=(
            _lineage(earlier, relation=LineageRelation.SUPERSEDES),
            _lineage(revised, relation=LineageRelation.SUPPORTS),
        ),
        source_ref=revised.source_ref,
        source_digest=revised.source_digest,
        acquisition_mode=EvidenceAcquisitionMode.LIVE,
        acquisition_receipt_ref=revised.acquisition_receipt_ref,
        acquisition_receipt_digest=revised.acquisition_receipt_digest,
        source_published_at=revised.source_published_at,
        event_effective_at=None,
        observed_at=revised.observed_at,
        ingested_at=asserted_at,
        subject_refs=(environment.fixture["entity_ref"],),
        payload=CanonicalJsonValueV1Alpha1(value_json=canonical_json(payload)),
        confidence=1.0,
    )


def _impact_projection(
    *,
    environment: P2DEnvironment,
    binding,
    assertion,
    target,
    closure: tuple,
    assembly,
    historical_case,
    historical_status,
    generated_at: datetime,
) -> SupersessionImpactProjectionV1Alpha1:
    impact = project_supersession_impact(
        superseder=assertion,
        superseded_resource_id=str(target.resource_id),
        closure=closure,
        cutoff_at=generated_at,
    )
    claim_impacts = tuple(
        SupersessionClaimImpactV1Alpha1(
            brief_id=str(assembly.brief.resource_id),
            claim_id=claim_id,
            impacted_support_record_ids=touched,
            total_support_count=total,
            fully_impacted=fully,
        )
        for claim_id, touched, total, fully in project_claim_impact(
            impact=impact,
            brief_id=str(assembly.brief.resource_id),
            claim_supports=assembly.claim_supports,
        )
    )
    assertion_reference = resource_reference(assertion)
    target_reference = resource_reference(target)
    return SupersessionImpactProjectionV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=binding.prepared_binding.reference,
        superseder_resource_id=impact.superseder_resource_id,
        superseder_resource_digest=assertion_reference.resource_digest,
        superseder_available_at=assertion_reference.available_at,
        superseded_resource_id=impact.superseded_resource_id,
        superseded_resource_digest=target_reference.resource_digest,
        superseded_resource_kind=LineageResourceKind(target_reference.resource_kind.value),
        impact_policy=SUPERSESSION_IMPACT_POLICY,
        eligible_relations=tuple(item.value for item in IMPACT_RELATIONS),
        closure_cutoff_at=generated_at,
        closure_resource_ids=impact.closure_resource_ids,
        impacted=tuple(
            SupersessionImpactPathV1Alpha1(
                resource_id=item.resource_id,
                resource_kind=item.resource_kind,
                resource_digest=item.resource_digest,
                depth=item.depth,
                via_resource_id=item.via_resource_id,
                via_relation=item.via_relation,
            )
            for item in impact.impacted
        ),
        unaffected_resource_ids=impact.unaffected_resource_ids,
        claim_impacts=claim_impacts,
        preserved_artifact_ids=(
            str(historical_case.resource_id),
            str(assembly.brief.resource_id),
            str(historical_status.projection_id),
        ),
        as_of=assembly.brief.as_of,
        generated_at=generated_at,
    )


async def _append_impact_projection(
    *,
    environment: P2DEnvironment,
    authorizer: ExactAppendAuthorizer,
    projection: SupersessionImpactProjectionV1Alpha1,
    transaction_key: str,
) -> bool:
    record = ImmutableRecordV1(
        product_id=projection.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        record_kind=SUPERSESSION_IMPACT_PROJECTION_KIND,
        record_key=str(projection.projection_id),
        payload_contract=projection.contract,
        payload=projection.model_dump(mode="python"),
        as_of=projection.as_of,
        available_at=projection.generated_at,
        processing_order=0,
    )
    first = await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=record,
        subject_ref=str(projection.projection_id),
        subject_digest=str(projection.projection_digest),
        transaction_key=transaction_key,
        submitted_at=projection.generated_at,
    )
    if first:
        raise AssertionError("first LIVE impact append unexpectedly replayed")
    return await _append_record(
        environment=environment,
        authorizer=authorizer,
        record=record,
        subject_ref=str(projection.projection_id),
        subject_digest=str(projection.projection_digest),
        transaction_key=transaction_key,
        submitted_at=projection.generated_at,
    )


def _negative_vectors(*, nasa_assertion, nasa_revised, nasa_initial, esa_initial, closure, cutoff):
    cases = {
        "cross_claimant_target": (nasa_assertion, esa_initial, closure, cutoff),
        "missing_target": (
            nasa_assertion,
            nasa_initial,
            tuple(item for item in closure if item != nasa_initial),
            cutoff,
        ),
        "future_leakage": (nasa_assertion, nasa_initial, closure, closure[0].as_of),
        "derived_from_is_not_supersession": (nasa_revised, nasa_initial, closure, cutoff),
    }
    results = {}
    for name, (superseder, target, exact_closure, exact_cutoff) in cases.items():
        try:
            project_supersession_impact(
                superseder=superseder,
                superseded_resource_id=str(target.resource_id),
                closure=exact_closure,
                cutoff_at=exact_cutoff,
            )
        except SupersessionImpactError as exc:
            results[name] = {"rejected": True, "error_type": type(exc).__name__}
        else:
            results[name] = {"rejected": False}
    return results


async def execute_acceptance() -> P2DExecution:
    """Execute P2D and retain its exact LIVE objects for composed acceptance."""

    environment = await build_environment()
    authorizer = ExactAppendAuthorizer()
    binding = bind_committed_activation(
        pack=environment.pack,
        committed=environment.committed_activation,
    )
    admissions = {key: await _admit_source(environment, key) for key in ("esa_initial", "nasa_initial")}
    divergence = await _derive(
        environment,
        authorizer=authorizer,
        binding=binding,
        derivation_fixture=environment.fixture["derivations"]["divergence"],
        admissions=admissions,
    )
    historical_time = _time(environment.fixture["historical"]["case_assembled_at"])
    historical_observations = (
        admissions["esa_initial"].observation,
        admissions["nasa_initial"].observation,
    )
    historical_case = CaseV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=binding.prepared_binding.reference,
        as_of=max(
            divergence.signal.as_of,
            *(item.as_of for item in historical_observations),
        ),
        lineage=(
            _lineage(divergence.shift, relation=LineageRelation.DERIVED_FROM),
            _lineage(divergence.signal, relation=LineageRelation.DERIVED_FROM),
            *(_lineage(item, relation=LineageRelation.SUPPORTS) for item in historical_observations),
        ),
        case_type_ref="case_type:planetary_defense_estimate_divergence",
        title="Historical NASA/ESA 2024 YR4 estimate divergence",
        purpose="Freeze the exact earlier official estimates before later revisions arrive.",
        subject_refs=(environment.fixture["entity_ref"],),
        assembled_at=historical_time,
    )
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=historical_case,
        transaction_key="live-case:planetary-defense:historical-divergence",
        submitted_at=historical_time,
    )
    policy = resolve_brief_synthesis_policy(
        binding.prepared_binding,
        template_id=str(divergence.attention_receipt.brief_template_id),
        persona_ids=divergence.attention_receipt.persona_ids,
    )
    historical_closure = (
        *historical_observations,
        divergence.shift,
        divergence.signal,
        historical_case,
    )
    historical_draft = _historical_draft(
        policy,
        observations=historical_observations,
        derivation=divergence,
        case=historical_case,
    )
    historical_brief_time = _time(environment.fixture["historical"]["brief_generated_at"])
    historical_assembly = assemble_canonical_brief(
        product_id=environment.fixture["product_id"],
        activation_revision=binding.prepared_binding.reference,
        brief_as_of=_time(environment.fixture["historical"]["brief_as_of"]),
        generated_at=historical_brief_time,
        draft=historical_draft,
        policy=policy,
        closure=historical_closure,
        observations=historical_observations,
        selected_context=(),
        mode=IntelligenceResourceMode.LIVE,
    )
    historical_brief = historical_assembly.brief
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=historical_brief,
        transaction_key="live-brief:planetary-defense:historical-divergence",
        submitted_at=historical_brief_time,
    )
    historical_status, historical_families, historical_status_replay = await _append_status_projection(
        environment=environment,
        authorizer=authorizer,
        binding=binding,
        draft=historical_draft,
        assembly=historical_assembly,
        closure=historical_closure,
        template_id=policy.template.template_id,
        generated_at=_time(environment.fixture["historical"]["status_generated_at"]),
        transaction_prefix="live-status:planetary-defense:historical",
    )

    for key in ("nasa_revised", "esa_revised"):
        admissions[key] = await _admit_source(environment, key)
    asserted_at = _time(environment.fixture["correction"]["asserted_at"])
    nasa_assertion = _supersession_assertion(
        environment=environment,
        binding=binding,
        earlier=admissions["nasa_initial"].observation,
        revised=admissions["nasa_revised"].observation,
        asserted_at=asserted_at,
    )
    esa_assertion = _supersession_assertion(
        environment=environment,
        binding=binding,
        earlier=admissions["esa_initial"].observation,
        revised=admissions["esa_revised"].observation,
        asserted_at=asserted_at,
    )
    for name, assertion in (("nasa", nasa_assertion), ("esa", esa_assertion)):
        await _append_resource(
            environment=environment,
            authorizer=authorizer,
            resource=assertion,
            transaction_key=f"live-supersession-assertion:planetary-defense:{name}",
            submitted_at=asserted_at,
        )

    impact_time = _time(environment.fixture["correction"]["impact_generated_at"])
    impact_closure = (
        admissions["esa_initial"].observation,
        admissions["nasa_initial"].observation,
        admissions["esa_initial"].entity_snapshot,
        admissions["nasa_initial"].entity_snapshot,
        divergence.shift,
        divergence.signal,
        historical_case,
        historical_brief,
    )
    nasa_impact = _impact_projection(
        environment=environment,
        binding=binding,
        assertion=nasa_assertion,
        target=admissions["nasa_initial"].observation,
        closure=impact_closure,
        assembly=historical_assembly,
        historical_case=historical_case,
        historical_status=historical_status,
        generated_at=impact_time,
    )
    esa_impact = _impact_projection(
        environment=environment,
        binding=binding,
        assertion=esa_assertion,
        target=admissions["esa_initial"].observation,
        closure=impact_closure,
        assembly=historical_assembly,
        historical_case=historical_case,
        historical_status=historical_status,
        generated_at=impact_time,
    )
    nasa_impact_replay = await _append_impact_projection(
        environment=environment,
        authorizer=authorizer,
        projection=nasa_impact,
        transaction_key="live-impact:planetary-defense:nasa",
    )
    esa_impact_replay = await _append_impact_projection(
        environment=environment,
        authorizer=authorizer,
        projection=esa_impact,
        transaction_key="live-impact:planetary-defense:esa",
    )
    negatives = _negative_vectors(
        nasa_assertion=nasa_assertion,
        nasa_revised=admissions["nasa_revised"].observation,
        nasa_initial=admissions["nasa_initial"].observation,
        esa_initial=admissions["esa_initial"].observation,
        closure=impact_closure,
        cutoff=impact_time,
    )

    nasa_revision = await _derive(
        environment,
        authorizer=authorizer,
        binding=binding,
        derivation_fixture=environment.fixture["derivations"]["nasa_revision"],
        admissions=admissions,
    )
    esa_revision = await _derive(
        environment,
        authorizer=authorizer,
        binding=binding,
        derivation_fixture=environment.fixture["derivations"]["esa_revision"],
        admissions=admissions,
    )
    corrected_time = _time(environment.fixture["correction"]["case_assembled_at"])
    all_observations = (
        admissions["esa_initial"].observation,
        admissions["nasa_initial"].observation,
        admissions["nasa_revised"].observation,
        admissions["esa_revised"].observation,
    )
    corrected_members = (
        *all_observations,
        divergence.shift,
        divergence.signal,
        nasa_revision.shift,
        nasa_revision.signal,
        esa_revision.shift,
        esa_revision.signal,
        nasa_assertion,
        esa_assertion,
    )
    corrected_case = CaseV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=binding.prepared_binding.reference,
        as_of=max(item.as_of for item in corrected_members),
        lineage=tuple(
            _lineage(
                item,
                relation=(
                    LineageRelation.SUPPORTS if isinstance(item, ObservationV1Alpha1) else LineageRelation.DERIVED_FROM
                ),
            )
            for item in corrected_members
        ),
        case_type_ref="case_type:planetary_defense_estimate_correction",
        title="Corrected NASA/ESA 2024 YR4 official estimate record",
        purpose=(
            "Freeze the earlier divergence, later same-source revisions, and exact "
            "supersession assertions for status-aware synthesis."
        ),
        subject_refs=(environment.fixture["entity_ref"],),
        assembled_at=corrected_time,
    )
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=corrected_case,
        transaction_key="live-case:planetary-defense:corrected",
        submitted_at=corrected_time,
    )
    corrected_closure = (*corrected_members, corrected_case)
    corrected_draft = _corrected_draft(
        policy,
        observations=all_observations,
        divergence=divergence,
        nasa_revision=nasa_revision,
        esa_revision=esa_revision,
        assertions=(nasa_assertion, esa_assertion),
        case=corrected_case,
    )
    corrected_brief_time = _time(environment.fixture["correction"]["brief_generated_at"])
    corrected_assembly = assemble_canonical_brief(
        product_id=environment.fixture["product_id"],
        activation_revision=binding.prepared_binding.reference,
        brief_as_of=_time(environment.fixture["correction"]["brief_as_of"]),
        generated_at=corrected_brief_time,
        draft=corrected_draft,
        policy=policy,
        closure=corrected_closure,
        observations=(*all_observations, nasa_assertion, esa_assertion),
        selected_context=(),
        mode=IntelligenceResourceMode.LIVE,
    )
    corrected_brief = corrected_assembly.brief
    await _append_resource(
        environment=environment,
        authorizer=authorizer,
        resource=corrected_brief,
        transaction_key="live-brief:planetary-defense:corrected",
        submitted_at=corrected_brief_time,
    )
    corrected_status, corrected_families, corrected_status_replay = await _append_status_projection(
        environment=environment,
        authorizer=authorizer,
        binding=binding,
        draft=corrected_draft,
        assembly=corrected_assembly,
        closure=corrected_closure,
        template_id=policy.template.template_id,
        generated_at=_time(environment.fixture["correction"]["status_generated_at"]),
        transaction_prefix="live-status:planetary-defense:corrected",
    )

    stored_historical_brief = await environment.store.load_record(
        immutable_record_storage_id(
            product_id=historical_brief.product_id,
            record_space=LIVE_SOURCE_RECORD_SPACE,
            record_kind="brief",
            record_key=str(historical_brief.resource_id),
        ),
        product_id=historical_brief.product_id,
        record_space=LIVE_SOURCE_RECORD_SPACE,
        record_kind="brief",
    )
    if stored_historical_brief is None:
        raise AssertionError("historical LIVE Brief was not durably reopened")
    reopened_historical_brief = type(historical_brief).model_validate(stored_historical_brief.payload)
    source_lineages = {
        key: admissions[key].entity_snapshot.attributes.parsed_value()["source_lineage_id"] for key in admissions
    }
    probabilities = {
        key: admissions[key].entity_snapshot.attributes.parsed_value()["impact_probability_percent"]
        for key in admissions
    }
    transport_calls = {
        uri: count for transport in environment.transports.values() for uri, count in transport.calls.items()
    }
    live_records = tuple(
        record for record in environment.store.records.values() if record.record_space == LIVE_SOURCE_RECORD_SPACE
    )
    prepared_records = tuple(
        record for record in environment.store.records.values() if record.record_space == "prepared"
    )
    projection = {
        "contract": "ace.world-intelligence.p2d-live-conflict-correction-proof/v1alpha1",
        "pack": {
            "compiled_pack_id": environment.pack.compiled_pack_id,
            "pack_digest": environment.pack.pack_digest,
            "module_count": len(environment.pack.modules),
            "json_only": True,
        },
        "source": {
            "lineages": source_lineages,
            "probabilities": probabilities,
            "stable_entity_ref": len({item.entity_snapshot.entity_ref for item in admissions.values()}) == 1,
            "adapter_capture_calls": {name: adapter.capture_calls for name, adapter in environment.adapters.items()},
            "transport_calls": transport_calls,
            "independent_claimant_roots": ["ESA", "NASA"],
            "network_access": False,
        },
        "historical": {
            "shift_type": divergence.shift.shift_type_ref,
            "signal_type": divergence.signal.signal_type_ref,
            "case_id": str(historical_case.resource_id),
            "brief_id": str(historical_brief.resource_id),
            "brief_digest": str(historical_brief.resource_digest),
            "citation_count": len(historical_brief.citations),
            "claim_count": len(historical_brief.claims),
            "status_projection_id": str(historical_status.projection_id),
            "claim_statuses": [item.status_id for item in historical_status.claim_statuses],
            "family_count": len(historical_families.members_by_root),
            "status_replay_exact": historical_status_replay,
        },
        "correction": {
            "assertion_ids": [
                str(nasa_assertion.resource_id),
                str(esa_assertion.resource_id),
            ],
            "superseded_observation_ids": [
                str(admissions["nasa_initial"].observation.resource_id),
                str(admissions["esa_initial"].observation.resource_id),
            ],
            "impact_projection_ids": [
                str(nasa_impact.projection_id),
                str(esa_impact.projection_id),
            ],
            "impact_counts": {
                "NASA": len(nasa_impact.impacted),
                "ESA": len(esa_impact.impacted),
            },
            "impacted_claim_counts": {
                "NASA": len(nasa_impact.claim_impacts),
                "ESA": len(esa_impact.claim_impacts),
            },
            "unaffected_counts": {
                "NASA": len(nasa_impact.unaffected_resource_ids),
                "ESA": len(esa_impact.unaffected_resource_ids),
            },
            "impact_replay_exact": nasa_impact_replay and esa_impact_replay,
            "impact_is_dependency_not_falsehood": True,
            "negative_vectors": negatives,
        },
        "corrected": {
            "shift_types": sorted({nasa_revision.shift.shift_type_ref, esa_revision.shift.shift_type_ref}),
            "signal_types": sorted(
                {
                    nasa_revision.signal.signal_type_ref,
                    esa_revision.signal.signal_type_ref,
                }
            ),
            "case_id": str(corrected_case.resource_id),
            "case_member_count": len(corrected_case.lineage),
            "brief_id": str(corrected_brief.resource_id),
            "brief_digest": str(corrected_brief.resource_digest),
            "citation_count": len(corrected_brief.citations),
            "claim_count": len(corrected_brief.claims),
            "status_projection_id": str(corrected_status.projection_id),
            "claim_statuses": [item.status_id for item in corrected_status.claim_statuses],
            "family_count": len(corrected_families.members_by_root),
            "family_roots": sorted(corrected_families.members_by_root),
            "same_lineage_supersessions_collapse": bool(
                corrected_families.root_of(str(nasa_assertion.resource_id))
                == corrected_families.root_of(str(admissions["nasa_initial"].observation.resource_id))
                and corrected_families.root_of(str(esa_assertion.resource_id))
                == corrected_families.root_of(str(admissions["esa_initial"].observation.resource_id))
            ),
            "corroborated_claim_family_count": next(
                item.distinct_derivation_family_count
                for item in corrected_status.claim_statuses
                if item.status_id == "corroborated"
            ),
            "status_replay_exact": corrected_status_replay,
        },
        "historical_integrity": {
            "brief_reopened_identically": reopened_historical_brief == historical_brief,
            "brief_id_unchanged": (str(reopened_historical_brief.resource_id) == str(historical_brief.resource_id)),
            "brief_precedes_corrections": historical_brief.generated_at < asserted_at,
            "historical_artifact_rewritten": False,
        },
        "separation": {
            "live_record_count": len(live_records),
            "prepared_record_count": len(prepared_records),
            "prepared_material_reused": False,
            "autonomous_publication": False,
            "external_action": False,
        },
    }
    return P2DExecution(
        projection=projection,
        environment=environment,
        admissions=admissions,
        divergence=divergence,
        nasa_revision=nasa_revision,
        esa_revision=esa_revision,
        historical_case=historical_case,
        historical_brief=historical_brief,
        corrected_case=corrected_case,
        corrected_brief=corrected_brief,
    )


async def run_acceptance() -> dict[str, Any]:
    """Return the stable public P2D acceptance projection."""

    return (await execute_acceptance()).projection


def main() -> None:
    print(json.dumps(asyncio.run(run_acceptance()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
