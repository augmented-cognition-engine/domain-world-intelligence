#!/usr/bin/env python3
"""Hermetic P2C acceptance for one governed Federal Register LIVE admission."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import Any

from ace.application import DomainActivationAdmissionService, LiveSourceIngressService
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    AuthorityUseReceiptV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    CapabilityUseReceiptV1Alpha1,
    GovernedStateCommitRequestV1,
    GovernedStateHeadPreconditionV1Alpha1,
    GovernedStateHeadV1,
    ResolvedApprovalReceiptV1,
    ResolvedAuthorityGrantV1,
    ResolvedSourceDefinitionV1Alpha1,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    CapabilityBindingV1,
    LiveSourceIngressRequestV1Alpha1,
    OrganizationOverlayV1,
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
)
from ace.testing import InMemoryImmutableRecordStore, exercise_live_source_ingress_restart
from ace_world_federal_register_source import (
    FederalRegisterRetrievalResult,
    FederalRegisterSourceAdapter,
)

PACK_PACKAGE = "domain_packs.world_intelligence_federal_register"
INPUT_NAME = "p2c_live_source_input.json"
EXPECTED_NAME = "p2c_live_expected.json"


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("fixture time must include a timezone")
    return parsed.astimezone(UTC)


def _pack_file(name: str) -> bytes:
    try:
        root = resources.files(PACK_PACKAGE)
        candidate = root.joinpath(name)
        if candidate.is_file():
            return candidate.read_bytes()
    except (ModuleNotFoundError, NotADirectoryError, TypeError):
        pass
    root = (
        Path(__file__).resolve().parents[1]
        / "domain_packs"
        / "world_intelligence_federal_register"
    )
    return root.joinpath(name).read_bytes()


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads(_pack_file(f"conformance/{name}"))


def compile_live_pack():
    manifest_bytes = _pack_file("manifest.json")
    manifest = json.loads(manifest_bytes)
    return compile_pack_document(
        manifest_bytes,
        {
            resource["path"]: _pack_file(resource["path"])
            for resource in manifest["resources"]
        },
    )


class MemoryGovernedStateStore:
    """Minimal public-protocol activation store for the hermetic proof."""

    def __init__(self) -> None:
        self.heads: dict[tuple[str, str, str], Any] = {}
        self.revisions: dict[tuple[str, str], Any] = {}
        self.receipts: dict[tuple[str, str], Any] = {}

    async def commit(self, request: GovernedStateCommitRequestV1):
        revision = request.revision
        key = (revision.state_kind, revision.product_id, revision.state_id)
        current = self.heads.get(key)
        current_revision_id = None if current is None else current.revision_id
        if current_revision_id != request.expected_head_revision_id:
            raise ValueError("governed state head conflict")
        receipt = request.receipt()
        self.revisions[(revision.product_id, revision.revision_id)] = revision
        self.receipts[(revision.product_id, str(receipt.receipt_id))] = receipt
        self.heads[key] = GovernedStateHeadV1(
            state_kind=revision.state_kind,
            product_id=revision.product_id,
            state_id=revision.state_id,
            sequence=revision.sequence,
            revision_id=revision.revision_id,
            commit_receipt_id=str(receipt.receipt_id),
            updated_at=request.committed_at,
        )
        return receipt

    async def load_head(self, *, state_kind: str, product_id: str, state_id: str):
        return self.heads.get((state_kind, product_id, state_id))

    async def load_revision(self, revision_id: str, *, product_id: str):
        return self.revisions.get((product_id, revision_id))

    async def load_receipt(self, receipt_id: str, *, product_id: str):
        return self.receipts.get((product_id, receipt_id))


class ExactActivationAuthority:
    async def resolve_approval(self, **request):
        return ResolvedApprovalReceiptV1(
            receipt_ref=request["receipt_ref"],
            product_id=request["product_id"],
            subject_ref=request["subject_ref"],
            actor_ref=request["actor_ref"],
            receipt_hash="1" * 64,
            approved_at=request["effective_at"] - timedelta(seconds=1),
        )

    async def resolve_grant(self, **request):
        return ResolvedAuthorityGrantV1(
            grant_ref=request["grant_ref"],
            product_id=request["product_id"],
            authority=request["authority"],
            grant_hash="2" * 64,
            effective_at=request["effective_at"],
        )


class SequenceClock:
    def __init__(self, *values: datetime) -> None:
        if not values:
            raise ValueError("sequence clock requires at least one value")
        self.values = values
        self.index = 0

    def __call__(self) -> datetime:
        value = self.values[min(self.index, len(self.values) - 1)]
        self.index += 1
        return value


class InjectedTransport:
    """Recorded response transport; it performs no network access."""

    def __init__(self, result: FederalRegisterRetrievalResult) -> None:
        self.result = result
        self.calls = 0
        self.requests = []

    async def retrieve(self, request):
        self.calls += 1
        self.requests.append(request)
        return self.result


class ExactAdapterRegistry:
    def __init__(self, *, artifact, adapter) -> None:
        self.artifact = artifact
        self.adapter = adapter
        self.calls = 0

    def resolve_source_adapter(self, *, artifact):
        self.calls += 1
        return self.adapter if artifact == self.artifact else None


class ExactSourceDefinitionResolver:
    def __init__(self, definition: ResolvedSourceDefinitionV1Alpha1) -> None:
        self.definition = definition
        self.calls = 0

    async def resolve_source_definition(
        self, *, product_id, source_definition_ref, resolved_at
    ):
        del resolved_at
        self.calls += 1
        if (
            product_id != self.definition.product_id
            or source_definition_ref != self.definition.source_definition_ref
        ):
            raise ValueError("unknown exact source definition")
        return self.definition


class ExactRuntimeUseResolver:
    def __init__(
        self,
        *,
        context,
        artifact,
        configuration_ref,
        capability_head,
        authority,
        grant_ref,
        grant_hash,
        grant_expires_at,
        grant_head,
    ) -> None:
        self.context = context
        self.artifact = artifact
        self.configuration_ref = configuration_ref
        self.capability_head = capability_head
        self.authority = authority
        self.grant_ref = grant_ref
        self.grant_hash = grant_hash
        self.grant_expires_at = grant_expires_at
        self.grant_head = grant_head

    async def resolve_capability_use(
        self,
        *,
        context,
        use_subject_ref,
        use_subject_digest,
        operation,
        artifact,
        capability_state_ref,
        configuration_ref,
        evaluated_at,
    ):
        if (
            context != self.context
            or artifact != self.artifact
            or capability_state_ref != capability_state_ref_for_artifact(self.artifact)
            or configuration_ref != self.configuration_ref
            or operation != "capture"
        ):
            raise ValueError("capability use crossed exact fixture scope")
        return CapabilityUseReceiptV1Alpha1(
            product_id=context.product_id,
            actor_ref=context.actor_ref,
            authenticated_context=context,
            use_subject_ref=use_subject_ref,
            use_subject_digest=use_subject_digest,
            operation=operation,
            artifact=artifact,
            capability_state_ref=capability_state_ref,
            configuration_ref=configuration_ref,
            evaluated_at=evaluated_at,
            resolved_at=evaluated_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.capability_head
            ),
        )

    async def resolve_authority_use(
        self,
        *,
        context,
        use_subject_ref,
        use_subject_digest,
        operation,
        authority,
        grant_ref,
        evaluated_at,
    ):
        if (
            context != self.context
            or authority != self.authority
            or grant_ref != self.grant_ref
            or operation != "capture"
            or self.grant_expires_at <= evaluated_at
        ):
            raise ValueError("authority use crossed exact current grant scope")
        return AuthorityUseReceiptV1Alpha1(
            product_id=context.product_id,
            actor_ref=context.actor_ref,
            authenticated_context=context,
            use_subject_ref=use_subject_ref,
            use_subject_digest=use_subject_digest,
            operation=operation,
            authority=authority,
            grant_ref=grant_ref,
            grant_hash=self.grant_hash,
            evaluated_at=evaluated_at,
            expires_at=self.grant_expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.grant_head
            ),
        )


def _head(*, state_kind: str, product_id: str, state_id: str, material: dict[str, Any]):
    return GovernedStateHeadV1(
        state_kind=state_kind,
        product_id=product_id,
        state_id=state_id,
        sequence=material["sequence"],
        revision_id=material["revision_id"],
        commit_receipt_id=material["commit_receipt_id"],
        updated_at=_time(material["updated_at"]),
    )


@dataclass
class LiveEnvironment:
    fixture: dict[str, Any]
    pack: Any
    request: LiveSourceIngressRequestV1Alpha1
    activation_service: DomainActivationAdmissionService
    activation_store: MemoryGovernedStateStore
    committed_activation: Any
    immutable_store: InMemoryImmutableRecordStore
    source_definitions: ExactSourceDefinitionResolver
    runtime_use: ExactRuntimeUseResolver
    adapter: FederalRegisterSourceAdapter
    registry: ExactAdapterRegistry
    transport: InjectedTransport
    clock: SequenceClock

    def service(self, *, clock: SequenceClock | None = None) -> LiveSourceIngressService:
        return LiveSourceIngressService(
            activation_service=self.activation_service,
            source_definitions=self.source_definitions,
            runtime_use=self.runtime_use,
            adapters=self.registry,
            store=self.immutable_store,
            clock=clock or self.clock,
            max_payload_chars=32_768,
        )

    def install_current_heads(self) -> None:
        activation_id = self.committed_activation.revision.activation_id
        activation_head = self.activation_store.heads[
            ("domain_activation", self.request.product_id, activation_id)
        ]
        source_head = self.source_definitions.definition.state_head_precondition
        source = GovernedStateHeadV1(
            **source_head.model_dump(mode="python", exclude={"contract"}),
            updated_at=_time(self.fixture["scenario"]["activation_committed_at"]),
        )
        for head in (
            activation_head,
            self.runtime_use.capability_head,
            self.runtime_use.grant_head,
            source,
        ):
            self.immutable_store.set_governed_state_head(head)


async def build_environment() -> LiveEnvironment:
    fixture = load_fixture(INPUT_NAME)
    scenario = fixture["scenario"]
    artifact_data = fixture["adapter_artifact"]
    pack = compile_live_pack()
    artifact = CapabilityArtifactIdentityV1Alpha1(
        capability=artifact_data["capability"],
        contract=artifact_data["contract"],
        implementation_id=artifact_data["implementation_id"],
        implementation_version=artifact_data["implementation_version"],
        artifact_digest=artifact_data["artifact_digest"],
    )
    binding = fixture["activation_binding"]
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id=binding["overlay_id"],
            version=binding["overlay_version"],
            pack_id=pack.metadata.pack_id,
            pack_version=pack.metadata.version,
            pack_digest=pack.pack_digest,
        ),
    )
    capability = CapabilityBindingV1(
        requirement_id=binding["capability_requirement_id"],
        capability=artifact.capability,
        contract=artifact.contract,
        implementation_id=artifact.implementation_id,
        implementation_version=artifact.implementation_version,
        artifact_digest=artifact.artifact_digest,
        configuration_ref=scenario["configuration_ref"],
        secret_ref=None,
    )
    authority = AuthorityBindingV1(
        request_id=binding["authority_request_id"],
        authority=scenario["authority"],
        grant_ref=scenario["grant_ref"],
    )
    spec = prepare_domain_activation(
        product_id=scenario["product_id"],
        activation_key=scenario["activation_key"],
        pack=pack,
        overlay=overlay,
        compilation_receipt_ref=scenario["compilation_receipt_ref"],
        conformance_receipt_refs=(scenario["conformance_receipt_ref"],),
        capability_bindings=(capability,),
        authority_bindings=(authority,),
    )
    revision = prepare_activation_revision(
        spec=spec,
        state=ActivationState.ACTIVE,
        actor_ref=scenario["actor_ref"],
        approval_receipt_ref=scenario["approval_receipt_ref"],
        occurred_at=_time(scenario["activation_occurred_at"]),
    )
    activation_store = MemoryGovernedStateStore()
    activation_service = DomainActivationAdmissionService(
        store=activation_store,
        authority=ExactActivationAuthority(),
    )
    committed = await activation_service.admit(
        revision,
        expected_head_revision_id=None,
        committed_at=_time(scenario["activation_committed_at"]),
    )
    if committed.live_authority is not False:
        raise AssertionError("activation unexpectedly granted live authority")

    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=scenario["product_id"],
        actor_ref=scenario["actor_ref"],
        authentication_receipt_ref=scenario["authentication_receipt_ref"],
        authentication_receipt_digest=scenario["authentication_receipt_digest"],
        authenticated_at=_time(scenario["authenticated_at"]),
        expires_at=_time(scenario["authentication_expires_at"]),
    )
    request = LiveSourceIngressRequestV1Alpha1(
        product_id=scenario["product_id"],
        authenticated_context=context,
        idempotency_key=scenario["idempotency_key"],
        activation_key=scenario["activation_key"],
        mapping_id=scenario["mapping_id"],
        source_definition_ref=scenario["source_definition_ref"],
        compiled_pack_id=pack.compiled_pack_id,
        pack_digest=pack.pack_digest,
        requested_at=_time(scenario["requested_at"]),
    )

    capability_head = _head(
        state_kind="capability_state",
        product_id=scenario["product_id"],
        state_id=capability_state_ref_for_artifact(artifact),
        material=fixture["governed_heads"]["capability"],
    )
    grant_head = _head(
        state_kind="authority_grant",
        product_id=scenario["product_id"],
        state_id=scenario["grant_ref"],
        material=fixture["governed_heads"]["grant"],
    )
    source_head = _head(
        state_kind="source_definition",
        product_id=scenario["product_id"],
        state_id=scenario["source_definition_ref"],
        material=fixture["governed_heads"]["source_definition"],
    )
    definition = ResolvedSourceDefinitionV1Alpha1(
        product_id=scenario["product_id"],
        source_definition_ref=scenario["source_definition_ref"],
        source_type_ref=scenario["source_type_ref"],
        configuration_ref=scenario["configuration_ref"],
        configuration_digest=scenario["configuration_digest"],
        authorized_uri=fixture["transport_fixture"]["requested_uri"],
        subject_binding_id=scenario["subject_binding_id"],
        entity_type_id=scenario["entity_type_id"],
        entity_ref=scenario["entity_ref"],
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
            source_head
        ),
    )
    runtime_use = ExactRuntimeUseResolver(
        context=context,
        artifact=artifact,
        configuration_ref=scenario["configuration_ref"],
        capability_head=capability_head,
        authority=scenario["authority"],
        grant_ref=scenario["grant_ref"],
        grant_hash=scenario["grant_hash"],
        grant_expires_at=_time(scenario["grant_expires_at"]),
        grant_head=grant_head,
    )
    transport_fixture = fixture["transport_fixture"]
    transport = InjectedTransport(
        FederalRegisterRetrievalResult(
            source_type_ref=scenario["source_type_ref"],
            requested_uri=transport_fixture["requested_uri"],
            effective_uri=transport_fixture["effective_uri"],
            status_code=transport_fixture["status_code"],
            media_type=transport_fixture["media_type"],
            response_body=transport_fixture["response_body"],
            redirect_chain=tuple(transport_fixture["redirect_chain"]),
            resolved_ip_addresses=tuple(transport_fixture["resolved_ip_addresses"]),
            connected_ip_addresses=tuple(transport_fixture["connected_ip_addresses"]),
            dns_rebinding_protection_applied=transport_fixture[
                "dns_rebinding_protection_applied"
            ],
            credentials_used=transport_fixture["credentials_used"],
            locator=transport_fixture["locator"],
            observed_at=_time(scenario["observed_at"]),
            captured_at=_time(scenario["captured_at"]),
        )
    )
    adapter = FederalRegisterSourceAdapter(
        transport=transport,
        artifact_digest=artifact.artifact_digest,
    )
    environment = LiveEnvironment(
        fixture=fixture,
        pack=pack,
        request=request,
        activation_service=activation_service,
        activation_store=activation_store,
        committed_activation=committed,
        immutable_store=InMemoryImmutableRecordStore(),
        source_definitions=ExactSourceDefinitionResolver(definition),
        runtime_use=runtime_use,
        adapter=adapter,
        registry=ExactAdapterRegistry(artifact=artifact, adapter=adapter),
        transport=transport,
        clock=SequenceClock(
            _time(scenario["capture_started_at"]),
            _time(scenario["rechecked_at"]),
            _time(scenario["admitted_at"]),
        ),
    )
    environment.install_current_heads()
    return environment


def identity_projection(environment: LiveEnvironment, admission) -> dict[str, Any]:
    transaction = admission.transaction_receipt
    attributes = admission.entity_snapshot.attributes.parsed_value()
    records = [
        {
            "processing_order": item.processing_order,
            "record_kind": item.record_kind,
            "record_key": item.record_key,
            "storage_id": item.storage_id,
            "material_hash": item.material_hash,
        }
        for item in transaction.records
    ]
    prohibited = sorted(
        {
            record.record_kind
            for record in environment.immutable_store.records.values()
            if record.record_kind in environment.fixture["prohibited_record_kinds"]
        }
    )
    return {
        "pack": {
            "compiled_pack_id": environment.pack.compiled_pack_id,
            "pack_digest": environment.pack.pack_digest,
        },
        "activation": {
            "live_authority": environment.committed_activation.live_authority,
            "activation_id": environment.committed_activation.revision.activation_id,
            "revision_id": environment.committed_activation.revision.revision_id,
        },
        "request": {
            "request_id": environment.request.request_id,
            "request_digest": environment.request.request_digest,
            "operation": environment.request.operation,
        },
        "acquisition": {
            "receipt_id": admission.acquisition_receipt.receipt_id,
            "receipt_digest": admission.acquisition_receipt.receipt_digest,
            "captured_payload_digest": admission.acquisition_receipt.captured_payload_digest,
            "locator": admission.acquisition_receipt.locator,
            "resolved_ip_addresses": list(
                admission.acquisition_receipt.resolved_ip_addresses
            ),
        },
        "live_records": {
            "record_space": transaction.record_space,
            "record_count": len(transaction.records),
            "records": records,
            "source_snapshot_ref": admission.source_snapshot.source_snapshot_ref,
            "source_snapshot_digest": admission.source_snapshot.source_snapshot_digest,
            "observation_id": admission.observation.resource_id,
            "observation_digest": admission.observation.resource_digest,
            "observation_mode": admission.observation.mode.value,
            "entity_snapshot_id": admission.entity_snapshot.resource_id,
            "entity_snapshot_digest": admission.entity_snapshot.resource_digest,
            "entity_mode": admission.entity_snapshot.mode.value,
            "admission_receipt_id": admission.admission_receipt.receipt_id,
            "admission_receipt_digest": admission.admission_receipt.receipt_digest,
            "transaction_id": transaction.transaction_id,
            "transaction_receipt_id": transaction.receipt_id,
            "transaction_receipt_digest": transaction.receipt_hash,
        },
        "mapped_result": {
            "entity_ref": admission.entity_snapshot.entity_ref,
            "attributes": attributes,
            "source_uri": admission.source_snapshot.source_uri,
            "captured_payload_json": admission.source_snapshot.captured_payload_json,
        },
        "scope": {
            "transport_fixture_only": environment.fixture["transport_fixture"][
                "fixture_only"
            ],
            "network_access": environment.fixture["transport_fixture"][
                "network_access"
            ],
            "capture_calls": environment.adapter.capture_calls,
            "transport_calls": environment.transport.calls,
            "exact_record_order": [item.record_kind for item in transaction.records],
            "prohibited_record_kinds_present": prohibited,
            "reusable_authority": admission.reusable_authority,
            "live_acquisition": admission.live_acquisition,
            "admission_disposition": admission.admission_disposition,
        },
    }


async def run_acceptance(*, assert_expected: bool = True):
    environment = await build_environment()
    restarted = environment.service(
        clock=SequenceClock(_time(environment.fixture["scenario"]["admitted_at"]))
    )
    conformance = await exercise_live_source_ingress_restart(
        first_service=environment.service(),
        restarted_service=restarted,
        request=environment.request,
        pack=environment.pack,
    )
    if environment.adapter.capture_calls != 1 or environment.transport.calls != 1:
        raise AssertionError("exact replay reacquired source material")
    if conformance.first.entity_snapshot.attributes.parsed_value() != environment.fixture[
        "expected_attributes"
    ]:
        raise AssertionError("LIVE entity attributes did not match the exact mapping")
    if (
        len(environment.immutable_store.records) != 5
        or len(environment.immutable_store.receipts) != 1
    ):
        raise AssertionError("LIVE ingress was not one atomic five-record transaction")
    projection = identity_projection(environment, conformance.first)
    if projection["scope"]["exact_record_order"] != [
        "source_acquisition",
        "source_snapshot",
        "observation",
        "entity_snapshot",
        "source_admission",
    ]:
        raise AssertionError("LIVE record order changed")
    if projection["scope"]["prohibited_record_kinds_present"]:
        raise AssertionError("out-of-scope downstream records were admitted")
    if projection["live_records"]["observation_mode"] != "live":
        raise AssertionError("observation is not visibly LIVE")
    if assert_expected and projection != load_fixture(EXPECTED_NAME)["expected"]:
        raise AssertionError("P2C LIVE identity projection changed from its exact pin")
    return projection, environment, conformance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-projection", action="store_true")
    args = parser.parse_args()
    projection, _, _ = asyncio.run(
        run_acceptance(assert_expected=not args.emit_projection)
    )
    print(json.dumps(projection, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
