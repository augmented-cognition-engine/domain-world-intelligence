"""Trusted application adapter for the recorded World AI Builder journey.

This package is intentionally separate from the inert World Domain Pack. Core
authenticates and authorizes the generic build request, supplies product-scoped
durable records, and owns the read projection. This adapter translates only the
supported AI Command Center profile into World-owned recorded Builder inputs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import distribution

from ace.application import (
    IntelligenceBuildRecordedSourcePort,
    IntelligenceBuilderPresentationService,
    IntelligenceBuilderSessionService,
    PreparedShiftSignalDerivationRequestV1Alpha1,
    RecordedSourceAdmission,
    RecordedSourceMaterialV1Alpha1,
)
from ace.application.intelligence_agent_contracts import ProposedCadence
from ace.application.intelligence_build_execution import (
    REQUIRED_INTELLIGENCE_BUILD_EFFECTS,
    AuthorizedIntelligenceBuild,
    IntelligenceBuildExecutor,
    IntelligenceBuildHostServices,
)
from ace.application.intelligence_builder_contracts import OnboardingArtifactKind, OnboardingStage
from ace.core import AuthenticatedRuntimeContextV1Alpha1, ImmutableRecordStore, canonical_hash, canonical_json
from ace.intelligence import (
    IntelligenceOnboardingProfileV1Alpha1,
    IntelligenceResourceKind,
    IntelligenceResourceMode,
    EntitySnapshotV1Alpha1,
    resource_reference,
)

from .journey import (
    AuthorizedWorldBuilderEffectsAuthority,
    WorldAIBuilderPlan,
    WorldAISourceMaterial,
    run_world_ai_builder_journey,
)

WORLD_AI_PROFILE_ID = "intelligence_onboarding_profile:world-ai-command-center"
SUPPORTED_RECORDED_SOURCE_GROUP_IDS = ("official_records",)
READ_KINDS = (
    IntelligenceResourceKind.CONNECTION,
    IntelligenceResourceKind.SOURCE,
    IntelligenceResourceKind.ENTITY,
    IntelligenceResourceKind.OBSERVATION,
    IntelligenceResourceKind.SIGNAL,
    IntelligenceResourceKind.SHIFT,
    IntelligenceResourceKind.CASE,
    IntelligenceResourceKind.BRIEF,
    IntelligenceResourceKind.MONITOR,
    IntelligenceResourceKind.SUBSCRIPTION,
    IntelligenceResourceKind.BUILDER_PROFILE,
    IntelligenceResourceKind.BUILDER_SESSION,
)

RECORDED_JOURNEY_STARTED_AT = datetime(2026, 8, 10, 20, 4, 35, tzinfo=UTC)
_RECORDED_SOURCE_FIXTURE_DIGEST = "cd01756995013fe1abae3077040fb8c6171109b74f9dec52c9adf3c338efe2e5"
_RECORDED_CANONICAL_PAYLOADS_DIGEST = "af07cbab3886a0fdff56c44fe951ef3ce578ea60751ffd5b2fead4faef6b5c71"
_POLICY_SUBJECT_BINDING_ID = "published_ai_policy_record"
_POLICY_ENTITY_TYPE_ID = "ai_policy_record"
_POLICY_ENTITY_REF = "entity:ai-policy/executive-order-14409"
_POLICY_DETECTOR_ID = "ai_policy_implementation_progression"
_RECORDED_SOURCE_IDENTITIES = (
    (
        "federal_register_ai_policy",
        "Federal Register AI policy record",
        "https://www.federalregister.gov/api/v1/documents/2026-11415.json",
        "source_snapshot:7b79e35507287aa63df2640bf121978e",
        "sha256:688f1d0075b464f6b890254e85465be6fbeddf7c5898c1cc449b5b16fd4213ab",
        "directive_issued",
        "federal_register:2026-11415",
    ),
    (
        "white_house_ai_policy",
        "White House AI policy release",
        (
            "https://www.whitehouse.gov/releases/2026/07/"
            "white-house-launches-gold-eagle-initiative-for-unprecedented-"
            "cybersecurity-vulnerability-coordination/"
        ),
        "source_snapshot:4bf705b079706f02f492c250bd7de899",
        "sha256:4e353594d4a0560046f13eae42ec43a867aeb23be8607f98ef493892f28fbfb9",
        "implementation_reported",
        "white_house_release:gold_eagle_2026_07_14",
    ),
)

_CADENCES = {
    "urgent_only": ProposedCadence.IMMEDIATE,
    "daily_pulse": ProposedCadence.DAILY,
    "weekly_brief": ProposedCadence.WEEKLY,
}
_OUTCOME_INTENTS = {
    "build_or_buy_ai": "Evaluate how admitted AI policy progression changes build, buy, provider, and control requirements.",
    "strategy_and_investment": (
        "Evaluate how admitted AI policy progression changes strategic exposure and investment assumptions."
    ),
    "frontier_research_and_products": (
        "Track how admitted AI policy progression changes research priorities and product constraints."
    ),
    "policy_safety_and_operational_risk": (
        "Watch official AI policy progression and keep evidence-role limits visible."
    ),
    "competitive_landscape": (
        "Compare how admitted AI policy progression changes provider and organizational positioning."
    ),
    "custom_picture": (
        "Track the admitted AI policy progression for the reviewed subject and preserve evidence-role limits."
    ),
}


class WorldAIBuilderExecutorError(RuntimeError):
    """A reviewed request cannot be executed by the recorded World adapter."""


@dataclass(frozen=True, slots=True)
class WorldAIBuilderEnvironment:
    """Only the invocation-scoped public capabilities the Builder needs."""

    context: AuthenticatedRuntimeContextV1Alpha1
    store: ImmutableRecordStore


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WorldAIBuilderExecutorError("recorded source time must include a timezone")
    return parsed.astimezone(UTC)


def _world_pack_file(relative_path: str):
    return distribution("ace-domain-world-intelligence").locate_file(
        f"domain_packs/world_intelligence_ai/{relative_path}"
    )


def load_world_ai_onboarding_profile() -> IntelligenceOnboardingProfileV1Alpha1:
    """Load the inert profile shipped by the separate World Domain Pack."""

    material = _world_pack_file("onboarding_profile.json").read_text(encoding="utf-8")
    return IntelligenceOnboardingProfileV1Alpha1.model_validate_json(material)


def load_recorded_world_ai_source_materials() -> tuple[WorldAISourceMaterial, ...]:
    """Load the exact two admitted records without claiming a live acquisition."""

    fixture = json.loads(_world_pack_file("conformance/ai_command_center_live_input.json").read_text(encoding="utf-8"))
    sources = fixture.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise WorldAIBuilderExecutorError("recorded World AI fixture omitted its two required sources")
    selected = sources[:2]
    if canonical_hash(selected) != _RECORDED_SOURCE_FIXTURE_DIGEST:
        raise WorldAIBuilderExecutorError("recorded World AI fixture changed without executor review")

    materials: list[WorldAISourceMaterial] = []
    for source, identity in zip(selected, _RECORDED_SOURCE_IDENTITIES, strict=True):
        option_id, display_name, expected_uri, source_ref, evidence_digest, stage, lineage = identity
        if source.get("requested_uri") != expected_uri:
            raise WorldAIBuilderExecutorError("recorded World AI source crossed its exact reviewed URI")
        materials.append(
            WorldAISourceMaterial(
                option_id=option_id,
                display_name=display_name,
                source_ref=source_ref,
                evidence_digest=evidence_digest,
                development_stage=stage,
                source_lineage=lineage,
                observed_at=_time(source["observed_at"]),
                as_of=_time(source["captured_at"]) + timedelta(seconds=1),
            )
        )
    return tuple(materials)


def load_recorded_world_ai_admission_materials(
    recorded_sources: IntelligenceBuildRecordedSourcePort,
) -> tuple[RecordedSourceMaterialV1Alpha1, ...]:
    """Bind the exact packaged policy pair for Core-owned recorded admission."""

    live_fixture = json.loads(
        _world_pack_file("conformance/ai_command_center_live_input.json").read_text(encoding="utf-8")
    )
    sources = live_fixture.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise WorldAIBuilderExecutorError("recorded World AI fixture omitted its two required sources")
    selected = sources[:2]
    if canonical_hash(selected) != _RECORDED_SOURCE_FIXTURE_DIGEST:
        raise WorldAIBuilderExecutorError("recorded World AI fixture changed without executor review")

    activation_fixture = json.loads(
        _world_pack_file("conformance/activation_golden_fixture.json").read_text(encoding="utf-8")
    )
    observations = activation_fixture.get("observations")
    if not isinstance(observations, list) or len(observations) != 1:
        raise WorldAIBuilderExecutorError("recorded World AI activation fixture changed shape")
    case = observations[0]
    try:
        payloads = (
            json.loads(case["baseline_attributes_json"]),
            json.loads(case["current_attributes_json"]),
        )
        semantic_times = (_time(case["baseline_as_of"]), _time(case["current_as_of"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise WorldAIBuilderExecutorError("recorded World AI canonical payloads failed exact review") from exc
    if canonical_hash(payloads) != _RECORDED_CANONICAL_PAYLOADS_DIGEST:
        raise WorldAIBuilderExecutorError("recorded World AI canonical payloads changed without executor review")

    materials: list[RecordedSourceMaterialV1Alpha1] = []
    for source, payload, semantic_time in zip(selected, payloads, semantic_times, strict=True):
        payload_json = canonical_json(payload)
        publication_date = payload.get("publication_date")
        if publication_date != semantic_time.date().isoformat():
            raise WorldAIBuilderExecutorError("recorded World AI semantic time crossed its publication date")
        subject = recorded_sources.bind_subject(
            subject_binding_id=_POLICY_SUBJECT_BINDING_ID,
            entity_type_id=_POLICY_ENTITY_TYPE_ID,
            entity_ref=_POLICY_ENTITY_REF,
        )
        materials.append(
            RecordedSourceMaterialV1Alpha1(
                source_group_id="official_records",
                mapping_id=source["mapping_id"],
                subject_binding=subject,
                source_definition_ref=source["source_definition_ref"],
                source_type_ref=source["source_type_ref"],
                source_uri=source["requested_uri"],
                captured_payload_json=payload_json,
                captured_payload_digest="sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
                source_published_at=semantic_time,
                observed_at=_time(source["observed_at"]),
                locator=source["locator"],
            )
        )
    return tuple(materials)


def _exact_policy_entities(
    admission: RecordedSourceAdmission,
    *,
    product_id: str,
) -> tuple[EntitySnapshotV1Alpha1, EntitySnapshotV1Alpha1]:
    entities = tuple(admission.entity_snapshots)
    if len(entities) != 2:
        raise WorldAIBuilderExecutorError("recorded World AI admission did not return its exact Entity pair")
    if any(
        item.mode is not IntelligenceResourceMode.PREPARED
        or item.product_id != product_id
        or item.entity_ref != _POLICY_ENTITY_REF
        or item.entity_type_ref != _POLICY_ENTITY_TYPE_ID
        for item in entities
    ):
        raise WorldAIBuilderExecutorError("recorded World AI admission crossed its PREPARED policy subject")
    ordered = tuple(sorted(entities, key=lambda item: (item.as_of, str(item.resource_id))))
    if (
        ordered[0].activation_revision != ordered[1].activation_revision
        or ordered[0].as_of >= ordered[1].as_of
        or ordered[0].resource_id == ordered[1].resource_id
    ):
        raise WorldAIBuilderExecutorError("recorded World AI Entity pair lost its semantic progression")
    return ordered


def plan_from_authorized_build(build: AuthorizedIntelligenceBuild) -> WorldAIBuilderPlan:
    """Translate one exact Core request without broadening its source claims."""

    request = build.request
    if request.profile_id != WORLD_AI_PROFILE_ID:
        raise WorldAIBuilderExecutorError("World AI Builder received an unsupported onboarding profile")
    if tuple(request.approved_effects) != REQUIRED_INTELLIGENCE_BUILD_EFFECTS:
        raise WorldAIBuilderExecutorError("World AI Builder requires the exact bounded onboarding effects")
    if tuple(sorted(request.source_group_ids)) != SUPPORTED_RECORDED_SOURCE_GROUP_IDS:
        raise WorldAIBuilderExecutorError(
            "The recorded World AI journey supports only the reviewed official_records source group"
        )
    try:
        cadence = _CADENCES[request.cadence_id]
        user_intent = _OUTCOME_INTENTS[request.outcome_id]
    except KeyError as exc:
        raise WorldAIBuilderExecutorError("World AI Builder received an unsupported outcome or cadence") from exc
    return WorldAIBuilderPlan(
        subject=request.subject,
        goal_ref=f"goal:world-ai-{request.outcome_id}-{build.request_digest.removeprefix('sha256:')[:16]}",
        outcome_id=request.outcome_id,
        user_intent=user_intent,
        audience_constraint=(
            "Orient the authenticated user without treating first-party claims as independent validation."
        ),
        cadence=cadence,
    )


class WorldAIBuilderExecutor(IntelligenceBuildExecutor):
    """Core-compatible executor for one exact recorded World AI build."""

    profile_id = WORLD_AI_PROFILE_ID

    def __init__(
        self,
        *,
        onboarding_profile: IntelligenceOnboardingProfileV1Alpha1 | None = None,
    ) -> None:
        self.onboarding_profile = onboarding_profile

    async def start(
        self,
        build: AuthorizedIntelligenceBuild,
        host_services: IntelligenceBuildHostServices,
    ):
        # Validate the whole bounded interpretation before the first durable write.
        plan = plan_from_authorized_build(build)
        context = build.authority_use.authenticated_context
        if (
            context.product_id != build.product_id
            or context.actor_ref != build.actor_ref
            or build.authority_use.use_subject_ref != build.build_id
            or build.authority_use.use_subject_digest != build.request_digest
        ):
            raise WorldAIBuilderExecutorError("authorized build identity crossed its authenticated context")
        if context.expires_at <= RECORDED_JOURNEY_STARTED_AT + timedelta(seconds=9):
            raise WorldAIBuilderExecutorError("authenticated context expired before the recorded journey")
        if host_services.recorded_sources is None or host_services.prepared_derivations is None:
            raise WorldAIBuilderExecutorError(
                "World AI Builder requires Core recorded-source and PREPARED-derivation host ports"
            )

        materials = load_recorded_world_ai_source_materials()
        admission_materials = load_recorded_world_ai_admission_materials(host_services.recorded_sources)
        admission = await host_services.recorded_sources.admit(admission_materials)
        baseline_entity, current_entity = _exact_policy_entities(admission, product_id=build.product_id)
        derivation = await host_services.prepared_derivations.derive(
            PreparedShiftSignalDerivationRequestV1Alpha1(
                derivation_key=f"prepared_derivation:{build.build_id}",
                detector_id=_POLICY_DETECTOR_ID,
                baseline_snapshot=resource_reference(baseline_entity),
                current_snapshot=resource_reference(current_entity),
                evaluated_at=build.authority_use.evaluated_at,
            )
        )
        if not derivation.material_shift or derivation.shift is None or derivation.signal is None:
            raise WorldAIBuilderExecutorError(
                "recorded World AI progression did not produce its declared Shift and Signal"
            )
        profile = self.onboarding_profile or load_world_ai_onboarding_profile()
        environment = WorldAIBuilderEnvironment(context=context, store=host_services.records)
        await IntelligenceBuilderPresentationService(store=host_services.records).admit_profile(
            product_id=build.product_id,
            profile=profile,
            admitted_at=RECORDED_JOURNEY_STARTED_AT - timedelta(seconds=1),
        )
        authority = AuthorizedWorldBuilderEffectsAuthority(
            product_id=build.product_id,
            actor_ref=build.actor_ref,
            build_id=build.build_id,
            request_digest=build.request_digest,
            approved_effects=tuple(build.request.approved_effects),
        )
        available_at = RECORDED_JOURNEY_STARTED_AT + timedelta(seconds=9)
        correlation_id = f"correlation:{build.build_id}"
        session_id = (
            "intelligence_builder_session:" + canonical_hash([build.product_id, correlation_id, plan.goal_ref])[:32]
        )
        existing = await IntelligenceBuilderSessionService(store=host_services.records).load_latest(
            product_id=build.product_id,
            session_id=session_id,
            available_at=available_at,
        )
        if existing is None:
            await run_world_ai_builder_journey(
                environment=environment,
                source_materials=materials,
                started_at=RECORDED_JOURNEY_STARTED_AT,
                plan=plan,
                authority=authority,
                correlation_id=correlation_id,
            )
        elif (
            existing.stage is not OnboardingStage.FIRST_BRIEFING_READY
            or existing.goal_ref != plan.goal_ref
            or existing.correlation_id != correlation_id
            or not any(
                item.artifact_kind is OnboardingArtifactKind.FIRST_BRIEFING_PREVIEW for item in existing.artifacts
            )
        ):
            raise WorldAIBuilderExecutorError("durable World AI Builder session is incomplete or conflicts")

        evaluated_at = max(build.authority_use.evaluated_at, available_at)
        if evaluated_at >= context.expires_at:
            raise WorldAIBuilderExecutorError("recorded execution fell outside the authenticated context")
        return await host_services.resources.query(
            resource_kinds=READ_KINDS,
            subject_refs=(),
            as_of=evaluated_at,
            available_at=evaluated_at,
            evaluated_at=evaluated_at,
            page_size=200,
        )


__all__ = [
    "READ_KINDS",
    "RECORDED_JOURNEY_STARTED_AT",
    "SUPPORTED_RECORDED_SOURCE_GROUP_IDS",
    "WORLD_AI_PROFILE_ID",
    "WorldAIBuilderEnvironment",
    "WorldAIBuilderExecutor",
    "WorldAIBuilderExecutorError",
    "load_recorded_world_ai_admission_materials",
    "load_recorded_world_ai_source_materials",
    "load_world_ai_onboarding_profile",
    "plan_from_authorized_build",
]
