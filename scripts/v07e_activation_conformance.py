"""ACE 0.7E World consumer activation conformance.

This provider-free packet consumes the exact Core candidate as an installed
wheel. World owns every pack noun, fixture, lifecycle choice, and downstream
resource binding; Core owns compilation, conformance, admission, immutable
commit receipts, and the domain-neutral contracts.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from pathlib import Path
from typing import Any

from ace.application import (
    BriefingAgent,
    DomainActivationPlanAdmissionError,
    DomainActivationPlanAdmissionService,
    IntelligenceAgent,
    IntelligenceBuilderSessionService,
    activation_commit_reference,
    prepare_activation_onboarding_handoff,
    validate_activation_commit_reference,
)
from ace.application.domain_activation_plan_contracts import (
    ActivationPlanAction,
    ActivationRequestedEffect,
    ActivationRuntimeState,
    DomainActivationRevisionV1Alpha2,
    IntelligenceActivationPlanV1Alpha2,
)
from ace.application.intelligence_agent_contracts import ProposedCadence
from ace.application.intelligence_builder_contracts import OnboardingStage
from ace.core import (
    GovernedStateCommitRequestV1,
    GovernedStateHeadV1,
    ResolvedApprovalReceiptV1,
    ResolvedAuthorityGrantV1,
)
from ace.intelligence import (
    ActivationRevisionReferenceV1Alpha1,
    AuthorityBindingV1,
    BriefV1Alpha1,
    CanonicalJsonValueV1Alpha1,
    CapabilityBindingV1,
    CitationV1Alpha1,
    ClaimGroundingKind,
    CompiledPackRefV1,
    EvidenceAcquisitionMode,
    GroundedClaimV1Alpha1,
    IntelligenceResourceMode,
    MonitorDisposition,
    MonitorV1Alpha1,
    OrganizationOverlayV1,
    PersonaBindingV1Alpha1,
    ShiftV1Alpha1,
    SubscriptionDeliveryDisposition,
    SubscriptionV1Alpha1,
)
from ace.intelligence.packs import compile_overlay, compile_pack_document, prepare_domain_activation
from ace.testing import (
    FixtureBriefingStrategy,
    FixtureCoreAuthorityResolver,
    FixtureIntelligenceModelStrategy,
    edited_fixture_intelligence_model,
    exercise_ontology_agent_restart,
    fixture_observations,
    run_domain_pack_conformance,
)
from pydantic import ValidationError

CORE_COMMIT = "10bbed620291ac5f552c3313dd37580938a5b9d7"
CORE_BASE_COMMIT = "dab0866af239af9a13b4d2772a0d3950f932fa2e"
CORE_WHEEL_NAME = "ace_core-0.6.0-py3-none-any.whl"
CORE_WHEEL_SIZE = 5_955_226
CORE_WHEEL_SHA256 = "19b75ab8dd2e2cc69f432a97fd7401eb0f55c9b5b7e2deeed0ae17e2396dff57"
CORE_REFERENCE_COORDINATES = {
    "handoff": "activation_onboarding_handoff:5f149bc12671ae32ece4894d9a62dd6c",
    "plan": "intelligence_activation_plan:59a927411a8a99e4a4c93d9c6ee0ddf4",
    "revision": "activation_revision:8dd82bd06590aad5dba19707d0304298",
    "receipt": "governed_state_commit:873014a8ee951ae3b84c797a9eaf8b16",
}

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_federal_register_monitor"
BASE = datetime(2026, 8, 12, 16, 0, tzinfo=UTC)
PRODUCT_ID = "product:world-federal-register-watch"
ACTIVATION_KEY = "world_federal_register_monitor_v07e"
ACTOR = "principal:world-intelligence-operator"
LIVE_EFFECTS = (
    ActivationRequestedEffect.PACK_ACTIVATION,
    ActivationRequestedEffect.MONITOR_BINDING,
    ActivationRequestedEffect.SUBSCRIPTION_BINDING,
    ActivationRequestedEffect.SHIFT_DERIVATION,
    ActivationRequestedEffect.BRIEF_SYNTHESIS,
)


def _pack_root(*, installed: bool):
    if installed:
        return files("domain_packs.world_intelligence_federal_register_monitor")
    return PACK_ROOT


def _resources(*, installed: bool = False) -> tuple[bytes, dict[str, bytes]]:
    root = _pack_root(installed=installed)
    manifest = root.joinpath("manifest.json").read_bytes()
    document = json.loads(manifest)
    return manifest, {item["path"]: root.joinpath(item["path"]).read_bytes() for item in document["resources"]}


def _compile_monitor_pack(*, installed: bool = False):
    manifest, resources = _resources(installed=installed)
    return compile_pack_document(manifest, resources)


class _MemoryGovernedStateStore:
    """Consumer-owned in-memory implementation of Core's public state-store port."""

    def __init__(self) -> None:
        self.heads: dict[tuple[str, str, str], Any] = {}
        self.revisions: dict[tuple[str, str], Any] = {}
        self.receipts: dict[tuple[str, str], Any] = {}

    async def commit(self, request: GovernedStateCommitRequestV1):
        revision = request.revision
        key = (revision.state_kind, revision.product_id, revision.state_id)
        current = self.heads.get(key)
        actual = None if current is None else current.revision_id
        if actual != request.expected_head_revision_id:
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


def _core_identity(core_wheel: Path | None) -> dict[str, Any]:
    version = importlib.metadata.version("ace-core")
    if version != "0.6.0":
        raise AssertionError(f"ACE 0.7E requires installed ace-core==0.6.0, found {version}")
    identity: dict[str, Any] = {
        "distribution": "ace-core==0.6.0",
        "source_commit": CORE_COMMIT,
        "base_commit": CORE_BASE_COMMIT,
        "wheel_filename": CORE_WHEEL_NAME,
        "expected_wheel_sha256": CORE_WHEEL_SHA256,
        "installed_location": str(importlib.metadata.distribution("ace-core").locate_file("")),
    }
    if core_wheel is not None:
        if core_wheel.name != CORE_WHEEL_NAME:
            raise AssertionError("Core wheel filename does not match the accepted candidate")
        if core_wheel.stat().st_size != CORE_WHEEL_SIZE:
            raise AssertionError("Core wheel size does not match the accepted candidate")
        digest = hashlib.sha256(core_wheel.read_bytes()).hexdigest()
        if digest != CORE_WHEEL_SHA256:
            raise AssertionError("Core wheel bytes do not match the accepted candidate")
        identity["verified_wheel_sha256"] = digest
        identity["verified_wheel_size"] = core_wheel.stat().st_size
        identity["artifact_availability"] = "ephemeral /tmp artifact; no durable uploaded byte-retrieval coordinate"
        identity["source_identity_is_not_wheel_provenance"] = True
    return identity


def _world_artifact_identity(world_wheel: Path | None) -> dict[str, Any]:
    try:
        distribution = importlib.metadata.distribution("ace-domain-world-intelligence")
    except importlib.metadata.PackageNotFoundError:
        identity: dict[str, Any] = {
            "distribution": "source-checkout consumer",
            "installed_location": None,
        }
    else:
        identity = {
            "distribution": f"ace-domain-world-intelligence=={distribution.version}",
            "installed_location": str(distribution.locate_file("")),
        }
    if world_wheel is not None:
        identity.update(
            {
                "wheel_filename": world_wheel.name,
                "wheel_size": world_wheel.stat().st_size,
                "wheel_sha256": hashlib.sha256(world_wheel.read_bytes()).hexdigest(),
            }
        )
    return identity


async def _world_watch_material() -> dict[str, Any]:
    """Create a World-specific 0.7D handoff through the unchanged public agents."""

    mapped = await exercise_ontology_agent_restart()
    sessions = IntelligenceBuilderSessionService(store=mapped.store)
    approval_ref = "approval:world-federal-register-watch-model"
    intelligence = IntelligenceAgent(
        sessions=sessions,
        authority=FixtureCoreAuthorityResolver(approved_receipt_refs=(approval_ref,)),
        strategy=FixtureIntelligenceModelStrategy(confidence=0.94),
    )
    admitted_at = BASE
    observations = fixture_observations(mapped, admitted_at=admitted_at)
    admitted = await intelligence.admit_observations(
        mapped.approved.session.revision,
        concept_model=mapped.restarted_proposal,
        concept_disposition=mapped.restarted_disposition,
        source_profile=mapped.source_profile,
        observations=observations,
        occurred_at=admitted_at,
    )
    proposed = await intelligence.propose(
        mapped.approved.session.revision,
        concept_model=mapped.restarted_proposal,
        concept_disposition=mapped.restarted_disposition,
        observations=observations,
        user_intent=(
            "Watch exact public-record status and material value changes for the World Federal Register review queue."
        ),
        audience_constraints=("Orient general readers and public researchers without legal conclusions or execution.",),
        cadence_constraints=(ProposedCadence.DAILY,),
        actor_ref="agent:world-intelligence-watch",
        occurred_at=admitted_at + timedelta(seconds=1),
    )
    if not proposed.proposed or proposed.proposal is None:
        raise AssertionError("World Watch proposal was not produced")
    edited_model = edited_fixture_intelligence_model(
        proposed.proposal.proposal,
        created_at=admitted_at + timedelta(seconds=2),
    )
    edited = await intelligence.revise(
        proposed.proposal.session.revision,
        prior=proposed.proposal.proposal,
        edited=edited_model,
        actor_ref=ACTOR,
        occurred_at=admitted_at + timedelta(seconds=2),
    )
    approved = await intelligence.approve(
        edited.session.revision,
        proposal=edited.proposal,
        approval_receipt_ref=approval_ref,
        actor_ref=ACTOR,
        occurred_at=admitted_at + timedelta(seconds=3),
    )
    briefing = BriefingAgent(
        sessions=sessions,
        strategy=FixtureBriefingStrategy(),
    )
    outcome = await briefing.create_first_brief(
        approved.session.revision,
        concept_model=mapped.restarted_proposal,
        concept_disposition=mapped.restarted_disposition,
        intelligence_model=approved.proposal,
        intelligence_disposition=approved.disposition,
        observations=observations,
        actor_ref="agent:world-intelligence-briefing",
        occurred_at=admitted_at + timedelta(seconds=4),
    )
    if not outcome.ready or outcome.briefing is None:
        raise AssertionError("World first Brief preview was not produced")
    material = {
        "session": outcome.briefing.session.revision,
        "observations": admitted.observation_set,
        "intelligence_model": approved.proposal,
        "intelligence_disposition": approved.disposition,
        "first_briefing": outcome.briefing.brief,
    }
    if material["session"].stage is not OnboardingStage.FIRST_BRIEFING_READY:
        raise AssertionError("World onboarding did not close at first_briefing_ready")
    handoff = prepare_activation_onboarding_handoff(**material)
    if handoff.handoff_id == CORE_REFERENCE_COORDINATES["handoff"]:
        raise AssertionError("World onboarding handoff copied the neutral Core fixture")
    return {"handoff": handoff, **material}


class _ExactAuthority:
    def __init__(self) -> None:
        self.approvals: list[dict[str, Any]] = []
        self.grants: list[dict[str, Any]] = []

    async def resolve_approval(self, **request):
        self.approvals.append(request)
        return ResolvedApprovalReceiptV1(
            receipt_ref=request["receipt_ref"],
            product_id=request["product_id"],
            subject_ref=request["subject_ref"],
            actor_ref=request["actor_ref"],
            receipt_hash=hashlib.sha256(request["subject_ref"].encode()).hexdigest(),
            approved_at=request["effective_at"] - timedelta(seconds=1),
        )

    async def resolve_grant(self, **request):
        self.grants.append(request)
        return ResolvedAuthorityGrantV1(
            grant_ref=request["grant_ref"],
            product_id=request["product_id"],
            authority=request["authority"],
            grant_hash=hashlib.sha256(request["grant_ref"].encode()).hexdigest(),
            effective_at=request["effective_at"],
        )


def _spec(*, pack, receipt, overlay_version: str):
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id="world_federal_register_activation",
            version=overlay_version,
            pack_id=pack.metadata.pack_id,
            pack_version=pack.metadata.version,
            pack_digest=pack.pack_digest,
        ),
    )
    capability = CapabilityBindingV1(
        requirement_id="federal_register_snapshot",
        capability="source_snapshot",
        contract="ace.source.snapshot/v1alpha1",
        implementation_id="world_federal_register_recorded_snapshot",
        implementation_version="0.2.0",
        artifact_digest="sha256:" + "a7" * 32,
        configuration_ref="configuration:world-federal-register-reviewed-records",
        secret_ref=None,
    )
    authority = AuthorityBindingV1(
        request_id="read_federal_register_document",
        authority="source_read",
        grant_ref="authority_grant:world-federal-register-reviewed-read",
    )
    return prepare_domain_activation(
        product_id=PRODUCT_ID,
        activation_key=ACTIVATION_KEY,
        pack=pack,
        overlay=overlay,
        compilation_receipt_ref=receipt.compilation_result_id,
        conformance_receipt_refs=(receipt.receipt_id,),
        conformance_receipts=(receipt,),
        capability_bindings=(capability,),
        authority_bindings=(authority,),
    )


def _plan(*, spec, handoff, action, at, head=None, target=None):
    return IntelligenceActivationPlanV1Alpha2(
        action=action,
        onboarding_handoff=handoff,
        spec=spec,
        requested_effects=LIVE_EFFECTS,
        requested_capabilities=spec.capability_bindings,
        requested_authorities=spec.authority_bindings,
        expected_head_revision_id=head,
        rollback_target_revision_id=None if target is None else target.revision_id,
        rollback_target_revision_digest=None if target is None else target.revision_digest,
        created_at=at,
    )


def _revision(*, plan, sequence: int, at: datetime, approval: str):
    return DomainActivationRevisionV1Alpha2(
        revision=sequence,
        plan=plan,
        state=ActivationRuntimeState.ACTIVE,
        prior_revision_id=plan.expected_head_revision_id,
        actor_ref=ACTOR,
        approval_receipt_ref=approval,
        occurred_at=at,
    )


def _runtime_bindings(*, pack, revision):
    activation = ActivationRevisionReferenceV1Alpha1(
        product_id=PRODUCT_ID,
        activation_key=ACTIVATION_KEY,
        activation_id=revision.activation_id,
        revision=revision.revision,
        revision_id=revision.revision_id,
        revision_digest=revision.revision_digest,
    )
    pack_ref = CompiledPackRefV1(
        pack_id=pack.metadata.pack_id,
        pack_version=pack.metadata.version,
        compiled_pack_id=pack.compiled_pack_id,
        pack_digest=pack.pack_digest,
    )
    monitor = MonitorV1Alpha1(
        monitor_id="fcc_official_publication_change",
        product_id=PRODUCT_ID,
        subject_entity_type_ids=("federal_register_agency_monitor",),
        subject_refs=("entity:monitor/fcc-latest-federal-register-publication",),
        detection_rule_ids=("fcc_latest_publication_change",),
        compiled_pack=pack_ref,
        activation_revision_ref=revision.revision_id,
        disposition=MonitorDisposition.ENABLED,
    )
    persona = PersonaBindingV1Alpha1(
        product_id=PRODUCT_ID,
        principal_ref="principal:world-public-researcher",
        persona_id="public_researcher",
        compiled_pack=pack_ref,
        activation_revision_ref=revision.revision_id,
    )
    subscription = SubscriptionV1Alpha1(
        subscription_id="fcc_official_publication_record_only",
        product_id=PRODUCT_ID,
        persona_binding_ref=persona.binding_ref,
        monitor_refs=(monitor.monitor_ref,),
        signal_types=("official_publication",),
        brief_template_ids=("official_record_change_brief",),
        minimum_confidence=0.8,
        delivery=SubscriptionDeliveryDisposition.RECORD_ONLY,
    )
    as_of = datetime(2026, 8, 7, 18, 0, 5, tzinfo=UTC)
    shift = ShiftV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=activation,
        as_of=as_of,
        shift_type_ref="shift_type:official_publication_change",
        title="FCC official publication changed",
        summary="The latest admitted FCC Federal Register record changed from 2026-15932 to 2026-16197.",
        subject_refs=("entity:monitor/fcc-latest-federal-register-publication",),
        baseline_as_of=datetime(2026, 8, 6, 18, 0, 5, tzinfo=UTC),
        baseline=CanonicalJsonValueV1Alpha1(value_json='{"document_number":"2026-15932"}'),
        current=CanonicalJsonValueV1Alpha1(value_json='{"document_number":"2026-16197"}'),
        delta=CanonicalJsonValueV1Alpha1(value_json='{"from":"2026-15932","to":"2026-16197"}'),
        detected_at=as_of + timedelta(minutes=1),
        confidence=1.0,
    )
    citation = CitationV1Alpha1(
        source_ref="source:federal-register/2026-16197",
        source_digest="sha256:" + "c7" * 32,
        acquisition_mode=EvidenceAcquisitionMode.PREPARED_FIXTURE,
        acquisition_receipt_ref="acquisition_receipt:world-v07e-2026-16197",
        acquisition_receipt_digest="sha256:" + "d7" * 32,
        source_as_of=as_of,
        retrieved_at=as_of,
        locator="https://www.federalregister.gov/documents/2026/08/07/2026-16197/",
        excerpt="Protecting Against National Security Threats to the Communications Supply Chain",
    )
    claim = GroundedClaimV1Alpha1(
        statement="Federal Register record 2026-16197 is the current bounded fixture record for this monitor.",
        grounding_kind=ClaimGroundingKind.CITED,
        citation_ids=(citation.citation_id,),
        confidence=1.0,
    )
    brief = BriefV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=activation,
        as_of=as_of,
        brief_type_ref="brief_type:official_record_change_brief",
        title="FCC official-record change brief",
        executive_summary="The bounded fixture advances from record 2026-15932 to 2026-16197.",
        body_markdown=(
            "The exact recorded evidence identifies Federal Register record 2026-16197. "
            "This provider-free conformance artifact makes no claim of current network freshness or legal effect."
        ),
        generated_at=as_of + timedelta(minutes=2),
        citations=(citation,),
        claims=(claim,),
    )
    return activation, monitor, persona, subscription, shift, brief


async def run_acceptance(
    *,
    core_wheel: Path | None = None,
    world_wheel: Path | None = None,
    installed_world: bool = False,
) -> dict[str, Any]:
    core = _core_identity(core_wheel)
    world_artifact = _world_artifact_identity(world_wheel)
    manifest, resources = _resources(installed=installed_world)
    pack = _compile_monitor_pack(installed=installed_world)
    fixture = _pack_root(installed=installed_world).joinpath("conformance/activation_golden_fixture.json").read_bytes()
    receipt = run_domain_pack_conformance(
        manifest_document=manifest,
        resources=resources,
        fixture_document=fixture,
    )
    if not receipt.passed:
        raise AssertionError("World activation pack did not pass exact conformance")
    watch = await _world_watch_material()
    initial_spec = _spec(pack=pack, receipt=receipt, overlay_version="0.1.0")
    store = _MemoryGovernedStateStore()
    authority = _ExactAuthority()
    service = DomainActivationPlanAdmissionService(store=store, authority=authority)

    initial_plan = _plan(
        spec=initial_spec,
        handoff=watch["handoff"],
        action=ActivationPlanAction.INITIAL_ACTIVATION,
        at=BASE + timedelta(minutes=10),
    )
    initial = _revision(
        plan=initial_plan,
        sequence=1,
        at=BASE + timedelta(minutes=11),
        approval="approval:world-v07e-initial",
    )
    initial_commit = await service.admit(
        initial,
        pack=pack,
        conformance_receipts=(receipt,),
        committed_at=BASE + timedelta(minutes=12),
        **{
            key: watch[key]
            for key in ("session", "observations", "intelligence_model", "intelligence_disposition", "first_briefing")
        },
    )
    restarted_initial = await DomainActivationPlanAdmissionService(
        store=store,
        authority=_ExactAuthority(),
    ).reload(product_id=PRODUCT_ID, activation_key=ACTIVATION_KEY)
    if restarted_initial != initial_commit:
        raise AssertionError("fresh service did not reload the exact initial World activation")

    upgraded_spec = _spec(pack=pack, receipt=receipt, overlay_version="0.2.0")
    upgrade_plan = _plan(
        spec=upgraded_spec,
        handoff=watch["handoff"],
        action=ActivationPlanAction.UPGRADE,
        head=initial.revision_id,
        at=BASE + timedelta(minutes=20),
    )
    upgrade = _revision(
        plan=upgrade_plan,
        sequence=2,
        at=BASE + timedelta(minutes=21),
        approval="approval:world-v07e-upgrade",
    )
    await service.admit(
        upgrade,
        pack=pack,
        conformance_receipts=(receipt,),
        committed_at=BASE + timedelta(minutes=22),
        **{
            key: watch[key]
            for key in ("session", "observations", "intelligence_model", "intelligence_disposition", "first_briefing")
        },
    )
    rollback_plan = _plan(
        spec=initial_spec,
        handoff=watch["handoff"],
        action=ActivationPlanAction.ROLLBACK,
        head=upgrade.revision_id,
        target=initial,
        at=BASE + timedelta(minutes=30),
    )
    rollback = _revision(
        plan=rollback_plan,
        sequence=3,
        at=BASE + timedelta(minutes=31),
        approval="approval:world-v07e-rollback",
    )
    rollback_commit = await service.admit(
        rollback,
        pack=pack,
        conformance_receipts=(receipt,),
        committed_at=BASE + timedelta(minutes=32),
        **{
            key: watch[key]
            for key in ("session", "observations", "intelligence_model", "intelligence_disposition", "first_briefing")
        },
    )
    restarted = await DomainActivationPlanAdmissionService(
        store=store,
        authority=_ExactAuthority(),
    ).reload(product_id=PRODUCT_ID, activation_key=ACTIVATION_KEY)
    if restarted != rollback_commit:
        raise AssertionError("fresh service did not reload the exact rolled-back World activation")

    historical = activation_commit_reference(rollback_commit)
    validate_activation_commit_reference(historical, committed=rollback_commit)
    if historical.live_authority is not False or historical.authority_stage != "historical_reference":
        raise AssertionError("historical activation reference unexpectedly carried authority")
    try:
        ActivationRevisionReferenceV1Alpha1.model_validate(historical.model_dump(mode="python"))
    except ValidationError:
        pass
    else:
        raise AssertionError("historical reference was accepted as runtime activation authority")

    activation, monitor, persona, subscription, shift, brief = _runtime_bindings(
        pack=pack,
        revision=rollback,
    )

    stale = receipt.model_copy(
        update={
            "compiler_contract": "ace.intelligence.pack-compiler/v2",
            "receipt_id": None,
            "receipt_digest": None,
        }
    )
    negative_store = _MemoryGovernedStateStore()
    negative_authority = _ExactAuthority()
    negative_service = DomainActivationPlanAdmissionService(
        store=negative_store,
        authority=negative_authority,
    )
    rejected = None
    try:
        await negative_service.admit(
            initial,
            pack=pack,
            conformance_receipts=(stale,),
            committed_at=BASE + timedelta(minutes=12),
            **{
                key: watch[key]
                for key in (
                    "session",
                    "observations",
                    "intelligence_model",
                    "intelligence_disposition",
                    "first_briefing",
                )
            },
        )
    except DomainActivationPlanAdmissionError as exc:
        rejected = str(exc)
    if rejected is None or negative_authority.approvals or negative_authority.grants or negative_store.heads:
        raise AssertionError(
            "stale conformance did not fail closed before authority and persistence: "
            f"rejected={rejected!r}, approvals={len(negative_authority.approvals)}, "
            f"grants={len(negative_authority.grants)}, heads={len(negative_store.heads)}"
        )

    world_coordinates = {
        "handoff": watch["handoff"].handoff_id,
        "initial_plan": initial.plan.plan_id,
        "initial_revision": initial.revision_id,
        "initial_receipt": initial_commit.commit_receipt.receipt_id,
        "upgrade_plan": upgrade.plan.plan_id,
        "upgrade_revision": upgrade.revision_id,
        "rollback_plan": rollback.plan.plan_id,
        "rollback_revision": rollback.revision_id,
        "rollback_receipt": rollback_commit.commit_receipt.receipt_id,
    }
    if set(world_coordinates.values()) & set(CORE_REFERENCE_COORDINATES.values()):
        raise AssertionError("World lifecycle copied a neutral Core fixture coordinate")
    approval_subjects = [item["subject_ref"] for item in authority.approvals]
    if approval_subjects != [initial.plan.plan_id, upgrade.plan.plan_id, rollback.plan.plan_id]:
        raise AssertionError("lifecycle approvals did not bind three separate exact plans")

    return {
        "contract": "ace.world-intelligence.activation-conformance/v1alpha1",
        "core": core,
        "consumer_artifact": world_artifact,
        "pack": {
            "pack_id": pack.metadata.pack_id,
            "pack_version": pack.metadata.version,
            "compiled_pack_id": pack.compiled_pack_id,
            "pack_digest": pack.pack_digest,
            "conformance_receipt_id": receipt.receipt_id,
            "conformance_receipt_digest": receipt.receipt_digest,
            "conformance_passed": receipt.passed,
        },
        "preview": {
            "effects": [item.value for item in initial.plan.requested_effects],
            "capabilities": [item.model_dump(mode="json") for item in initial.plan.requested_capabilities],
            "authorities": [item.model_dump(mode="json") for item in initial.plan.requested_authorities],
        },
        "coordinates": world_coordinates,
        "restart": {
            "initial_exact": restarted_initial == initial_commit,
            "rollback_exact": restarted == rollback_commit,
        },
        "lifecycle": {
            "approval_subjects": approval_subjects,
            "upgrade_separately_approved": upgrade.approval_receipt_ref,
            "rollback_separately_approved": rollback.approval_receipt_ref,
            "rollback_target_revision_id": rollback.plan.rollback_target_revision_id,
        },
        "historical_reference": {
            **historical.model_dump(mode="json"),
            "rejected_as_runtime_activation": True,
        },
        "bindings": {
            "activation_revision": activation.model_dump(mode="json"),
            "monitor_ref": monitor.monitor_ref,
            "persona_binding_ref": persona.binding_ref,
            "subscription_ref": subscription.subscription_ref,
            "shift_id": shift.resource_id,
            "brief_id": brief.resource_id,
            "brief_claim_count": len(brief.claims),
            "brief_citation_count": len(brief.citations),
        },
        "negative": {
            "stale_or_mismatched_conformance": rejected,
            "authority_calls": 0,
            "grant_calls": 0,
            "committed_heads": 0,
        },
        "scope": {
            "credentials": False,
            "network": False,
            "silent_activation": False,
            "broadened_grants": False,
            "package_release": False,
        },
    }


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument("--core-wheel", type=Path)
    parser.add_argument("--world-wheel", type=Path)
    parser.add_argument("--installed-world", action="store_true")
    arguments = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(
                run_acceptance(
                    core_wheel=arguments.core_wheel,
                    world_wheel=arguments.world_wheel,
                    installed_world=arguments.installed_world,
                )
            ),
            indent=2,
            sort_keys=True,
        )
    )
