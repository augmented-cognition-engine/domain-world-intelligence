"""Official-source World monitor: two LIVE snapshots -> Shift -> Signal.

This packet extends P2C without mutating its frozen single-record identities.
The two recorded responses are exact public Federal Register records. Network
transport remains a separately reviewed opt-in boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ace.application import (
    DomainActivationAdmissionService,
    LiveIntelligenceBridgeService,
    LiveSourceIngressService,
    bind_committed_activation,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    GovernedStateHeadV1,
    ResolvedSourceDefinitionV1Alpha1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    CapabilityBindingV1,
    LiveDerivationRequestV1Alpha1,
    LiveSourceIngressRequestV1Alpha1,
    OrganizationOverlayV1,
    resource_reference,
)
from ace.intelligence.packs import (
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
)
from ace.testing import InMemoryImmutableRecordStore
from ace_world_federal_register_source import (
    FEDERAL_REGISTER_LOCATOR,
    FEDERAL_REGISTER_SOURCE_TYPE,
    FederalRegisterDocumentProfile,
    FederalRegisterRetrievalResult,
    FederalRegisterSourceAdapter,
)

from scripts.p2c_federal_register_live_acceptance import (
    ExactActivationAuthority,
    ExactAdapterRegistry,
    ExactRuntimeUseResolver,
    MemoryGovernedStateStore,
    SequenceClock,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_federal_register_monitor"
INPUT_PATH = PACK_ROOT / "conformance" / "p2c2_monitor_input.json"


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("fixture time must include a timezone")
    return parsed.astimezone(UTC)


def load_fixture() -> dict[str, Any]:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def compile_monitor_pack():
    manifest_bytes = (PACK_ROOT / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    return compile_pack_document(
        manifest_bytes,
        {
            item["path"]: (PACK_ROOT / item["path"]).read_bytes()
            for item in manifest["resources"]
        },
    )


def _head(*, kind: str, product_id: str, state_id: str, material: dict[str, Any]):
    return GovernedStateHeadV1(
        state_kind=kind,
        product_id=product_id,
        state_id=state_id,
        sequence=material["sequence"],
        revision_id=material["revision_id"],
        commit_receipt_id=material["commit_receipt_id"],
        updated_at=_time(material["updated_at"]),
    )


class ExactSourceDefinitions:
    def __init__(self, definitions: tuple[ResolvedSourceDefinitionV1Alpha1, ...]) -> None:
        self.definitions = {
            item.source_definition_ref: item for item in definitions
        }

    async def resolve_source_definition(
        self, *, product_id, source_definition_ref, resolved_at
    ):
        del resolved_at
        definition = self.definitions.get(source_definition_ref)
        if definition is None or definition.product_id != product_id:
            raise ValueError("unknown exact source definition")
        return definition


class RecordedDocumentTransport:
    """Network-free exact responses from two reviewed official API records."""

    def __init__(self, results: tuple[FederalRegisterRetrievalResult, ...]) -> None:
        self.results = {item.requested_uri: item for item in results}
        self.calls: list[str] = []

    async def retrieve(self, request):
        self.calls.append(request.requested_uri)
        try:
            return self.results[request.requested_uri]
        except KeyError as exc:
            raise ValueError("transport request crossed the recorded allowlist") from exc


@dataclass
class MonitorEnvironment:
    fixture: dict[str, Any]
    pack: Any
    context: AuthenticatedRuntimeContextV1Alpha1
    activation_service: DomainActivationAdmissionService
    activation_store: MemoryGovernedStateStore
    committed_activation: Any
    store: InMemoryImmutableRecordStore
    requests: tuple[LiveSourceIngressRequestV1Alpha1, ...]
    definitions: ExactSourceDefinitions
    runtime_use: ExactRuntimeUseResolver
    registry: ExactAdapterRegistry
    adapter: FederalRegisterSourceAdapter
    transport: RecordedDocumentTransport

    def ingress(self, clock: SequenceClock) -> LiveSourceIngressService:
        return LiveSourceIngressService(
            activation_service=self.activation_service,
            source_definitions=self.definitions,
            runtime_use=self.runtime_use,
            adapters=self.registry,
            store=self.store,
            clock=clock,
            max_payload_chars=32_768,
        )


def _response(document: dict[str, Any]) -> str:
    return canonical_json(
        {
            "title": document["title"],
            "document_number": document["document_number"],
            "type": document["document_type"],
            "publication_date": document["publication_date"],
            "agencies": [{"name": document["agency_name"], "id": 161}],
            "html_url": document["html_uri"],
            "pdf_url": document["official_pdf_uri"],
        }
    )


async def build_environment() -> MonitorEnvironment:
    fixture = load_fixture()
    product_id = fixture["product_id"]
    pack = compile_monitor_pack()
    artifact = CapabilityArtifactIdentityV1Alpha1(**fixture["adapter_artifact"])
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
        capability_bindings=(
            CapabilityBindingV1(
                requirement_id=fixture["activation"]["capability_requirement_id"],
                capability=artifact.capability,
                contract=artifact.contract,
                implementation_id=artifact.implementation_id,
                implementation_version=artifact.implementation_version,
                artifact_digest=artifact.artifact_digest,
                configuration_ref=fixture["configuration_ref"],
                secret_ref=None,
            ),
        ),
        authority_bindings=(
            AuthorityBindingV1(
                request_id=fixture["activation"]["authority_request_id"],
                authority=fixture["authority"],
                grant_ref=fixture["grant_ref"],
            ),
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
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=product_id,
        actor_ref=fixture["actor_ref"],
        authentication_receipt_ref=fixture["authentication"]["receipt_ref"],
        authentication_receipt_digest=fixture["authentication"]["receipt_digest"],
        authenticated_at=_time(fixture["authentication"]["authenticated_at"]),
        expires_at=_time(fixture["authentication"]["expires_at"]),
    )
    capability_head = _head(
        kind="capability_state",
        product_id=product_id,
        state_id=capability_state_ref_for_artifact(artifact),
        material=fixture["governed_heads"]["capability"],
    )
    grant_head = _head(
        kind="authority_grant",
        product_id=product_id,
        state_id=fixture["grant_ref"],
        material=fixture["governed_heads"]["grant"],
    )
    definitions = []
    requests = []
    profiles = []
    results = []
    source_heads = []
    for document in fixture["documents"]:
        number = document["document_number"]
        source_head = _head(
            kind="source_definition",
            product_id=product_id,
            state_id=document["source_definition_ref"],
            material=fixture["governed_heads"]["sources"][number],
        )
        source_heads.append(source_head)
        definitions.append(
            ResolvedSourceDefinitionV1Alpha1(
                product_id=product_id,
                source_definition_ref=document["source_definition_ref"],
                source_type_ref=fixture["source_type_ref"],
                configuration_ref=fixture["configuration_ref"],
                configuration_digest=fixture["configuration_digest"],
                authorized_uri=document["requested_uri"],
                subject_binding_id=fixture["subject_binding_id"],
                entity_type_id=fixture["entity_type_id"],
                entity_ref=fixture["entity_ref"],
                state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                    source_head
                ),
            )
        )
        requests.append(
            LiveSourceIngressRequestV1Alpha1(
                product_id=product_id,
                authenticated_context=context,
                idempotency_key=document["idempotency_key"],
                activation_key=fixture["activation_key"],
                mapping_id=document["mapping_id"],
                source_definition_ref=document["source_definition_ref"],
                compiled_pack_id=pack.compiled_pack_id,
                pack_digest=pack.pack_digest,
                requested_at=_time(document["requested_at"]),
            )
        )
        profiles.append(
            FederalRegisterDocumentProfile(
                document_number=number,
                title=document["title"],
                document_type=document["document_type"],
                publication_date=document["publication_date"],
                agency_name=document["agency_name"],
                document_uri=document["requested_uri"],
                html_uri=document["html_uri"],
                official_pdf_uri=document["official_pdf_uri"],
            )
        )
        results.append(
            FederalRegisterRetrievalResult(
                source_type_ref=FEDERAL_REGISTER_SOURCE_TYPE,
                requested_uri=document["requested_uri"],
                effective_uri=document["requested_uri"],
                status_code=200,
                media_type="application/json",
                response_body=_response(document),
                redirect_chain=(),
                resolved_ip_addresses=("1.1.1.1",),
                connected_ip_addresses=("1.1.1.1",),
                dns_rebinding_protection_applied=True,
                credentials_used=False,
                locator=FEDERAL_REGISTER_LOCATOR,
                observed_at=_time(document["observed_at"]),
                captured_at=_time(document["captured_at"]),
            )
        )
    transport = RecordedDocumentTransport(tuple(results))
    adapter = FederalRegisterSourceAdapter(
        transport=transport,
        artifact_digest=artifact.artifact_digest,
        profiles=tuple(profiles),
        implementation_id=artifact.implementation_id,
        implementation_version=artifact.implementation_version,
    )
    runtime_use = ExactRuntimeUseResolver(
        context=context,
        artifact=artifact,
        configuration_ref=fixture["configuration_ref"],
        capability_head=capability_head,
        authority=fixture["authority"],
        grant_ref=fixture["grant_ref"],
        grant_hash=fixture["grant_hash"],
        grant_expires_at=_time(fixture["grant_expires_at"]),
        grant_head=grant_head,
    )
    store = InMemoryImmutableRecordStore()
    activation_head = activation_store.heads[
        ("domain_activation", product_id, committed.revision.activation_id)
    ]
    for head in (activation_head, capability_head, grant_head, *source_heads):
        store.set_governed_state_head(head)
    return MonitorEnvironment(
        fixture=fixture,
        pack=pack,
        context=context,
        activation_service=activation_service,
        activation_store=activation_store,
        committed_activation=committed,
        store=store,
        requests=tuple(requests),
        definitions=ExactSourceDefinitions(tuple(definitions)),
        runtime_use=runtime_use,
        registry=ExactAdapterRegistry(artifact=artifact, adapter=adapter),
        adapter=adapter,
        transport=transport,
    )


async def admit_snapshots(environment: MonitorEnvironment):
    admissions = []
    for document, request in zip(
        environment.fixture["documents"], environment.requests, strict=True
    ):
        service = environment.ingress(
            SequenceClock(
                _time(document["capture_started_at"]),
                _time(document["rechecked_at"]),
                _time(document["admitted_at"]),
            )
        )
        admission = await service.admit(request=request, pack=environment.pack)
        replay = await service.admit(request=request, pack=environment.pack)
        if admission.replayed or not replay.replayed:
            raise AssertionError("LIVE source admission replay was not explicit")
        admissions.append(admission)
    if environment.adapter.capture_calls != 2 or len(environment.transport.calls) != 2:
        raise AssertionError("the exact two-record source boundary was not preserved")
    return tuple(admissions)


async def run_monitor_derivation(*, authorizer, operation_binding):
    environment = await build_environment()
    baseline, current = await admit_snapshots(environment)
    binding = bind_committed_activation(
        pack=environment.pack,
        committed=environment.committed_activation,
    )
    timing = environment.fixture["derivation"]
    baseline_ref = resource_reference(baseline.entity_snapshot).model_copy(
        update={
            "available_at": next(
                item.available_at
                for item in baseline.transaction_receipt.records
                if item.record_kind == "entity_snapshot"
            )
        }
    )
    current_ref = resource_reference(current.entity_snapshot).model_copy(
        update={
            "available_at": next(
                item.available_at
                for item in current.transaction_receipt.records
                if item.record_kind == "entity_snapshot"
            )
        }
    )
    request = LiveDerivationRequestV1Alpha1(
        derivation_key=timing["derivation_key"],
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        activation_revision=binding.prepared_binding.reference,
        pack=binding.prepared_binding.revision.spec.pack,
        detector_id=timing["detector_id"],
        baseline=baseline_ref,
        current=current_ref,
        detected_at=_time(timing["detected_at"]),
        attention_evaluated_at=_time(timing["attention_evaluated_at"]),
        requested_at=_time(timing["requested_at"]),
    )
    service = LiveIntelligenceBridgeService(
        activation_service=environment.activation_service,
        pack=environment.pack,
        store=environment.store,
        authorizer=authorizer,
        operation_binding=operation_binding,
    )
    derivation = await service.derive(request)
    replay = await service.derive(request)
    if derivation.replayed or not replay.replayed:
        raise AssertionError("LIVE derivation replay was not explicit")
    return environment, (baseline, current), request, derivation


def source_projection(admissions) -> dict[str, Any]:
    return {
        "baseline": admissions[0].entity_snapshot.attributes.parsed_value(),
        "current": admissions[1].entity_snapshot.attributes.parsed_value(),
        "entity_ref_stable": (
            admissions[0].entity_snapshot.entity_ref
            == admissions[1].entity_snapshot.entity_ref
        ),
        "observation_modes": [item.observation.mode.value for item in admissions],
    }


if __name__ == "__main__":
    raise SystemExit(
        "This packet is composed by the governed Reality Brief acceptance harness."
    )
