"""Authority-neutral planner for the recorded World AI Command Center."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.metadata import distribution

from ace.application import (
    INTELLIGENCE_BUILD_PLANNER_V1ALPHA3_CONTRACT,
    INTELLIGENCE_BUILD_PLANNING_CAPABILITY,
    IntelligenceBuildActivationProposalV1Alpha1,
    IntelligenceBuildPlanRequestV1Alpha2,
    IntelligenceBuildPlanV1Alpha3,
    RecordedSourceSelectionV1Alpha1,
)
from ace.core import CapabilityArtifactIdentityV1Alpha1, canonical_hash
from ace.intelligence import CompiledOverlayV1, CompiledPackRefV1
from ace.intelligence.contracts.intelligence_builder_presentation import IntelligenceOnboardingProfileV1Alpha1
from ace.intelligence.contracts.pack import CompiledDomainPackV1

from .executor import WORLD_AI_PROFILE_ID

WORLD_AI_OFFICIAL_RECORDS_PACK = CompiledPackRefV1(
    pack_id="world_intelligence_ai_official_records",
    pack_version="1.0.0",
    compiled_pack_id="pack_ir:df6127f517247e7f5eac1175aaa9ca89",
    pack_digest="sha256:df6127f517247e7f5eac1175aaa9ca89721e1bd6ac95b59d96061df98b99bde5",
)
WORLD_AI_PLANNER_VERSION = "0.2.0"
_INVENTORY_PATH = "domain_packs/world_intelligence_ai_official_records/conformance/recorded_sources.json"
_INVENTORY_DIGEST = "c0da9c8315a4d6a354c16c9b9dee9988393ffb5f6e464826859aefa9e33441e7"


class WorldAIBuilderPlannerError(RuntimeError):
    """The installed World planner cannot preserve exact reviewed material."""


def _world_domain_file(relative_path: str):
    return distribution("ace-domain-world-intelligence").locate_file(relative_path)


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WorldAIBuilderPlannerError("recorded source time must include a timezone")
    return parsed.astimezone(UTC)


def _inventory() -> dict:
    try:
        material = json.loads(_world_domain_file(_INVENTORY_PATH).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise WorldAIBuilderPlannerError("recorded World source inventory is unavailable") from exc
    if (
        material.get("contract") != "ace.world-intelligence.recorded-source-inventory/v1alpha1"
        or material.get("inventory_id") != "eo_14409_to_gold_eagle_official_records"
        or material.get("inventory_version") != "1.0.0"
        or material.get("source_group_id") != "official_records"
    ):
        raise WorldAIBuilderPlannerError("recorded World source inventory identity changed")
    materials = material.get("materials")
    if not isinstance(materials, list) or len(materials) != 2:
        raise WorldAIBuilderPlannerError("recorded World source inventory must contain exactly two materials")
    return material


def _artifact_identity() -> CapabilityArtifactIdentityV1Alpha1:
    return CapabilityArtifactIdentityV1Alpha1(
        capability=INTELLIGENCE_BUILD_PLANNING_CAPABILITY,
        contract=INTELLIGENCE_BUILD_PLANNER_V1ALPHA3_CONTRACT,
        implementation_id="world_ai_official_records_planner",
        implementation_version=WORLD_AI_PLANNER_VERSION,
        artifact_digest=f"sha256:{canonical_hash([WORLD_AI_PLANNER_VERSION, WORLD_AI_OFFICIAL_RECORDS_PACK.model_dump(mode='json'), _INVENTORY_DIGEST])}",
    )


class WorldAIBuilderPlanner:
    """Propose the exact two-source World program without binding authority."""

    profile_id = WORLD_AI_PROFILE_ID
    pack_reference = WORLD_AI_OFFICIAL_RECORDS_PACK
    artifact_identity = _artifact_identity()

    async def prepare(
        self,
        request: IntelligenceBuildPlanRequestV1Alpha2,
        *,
        profile: IntelligenceOnboardingProfileV1Alpha1,
        pack: CompiledDomainPackV1,
    ) -> IntelligenceBuildPlanV1Alpha3:
        if profile.profile_id != self.profile_id or request.profile_id != self.profile_id:
            raise WorldAIBuilderPlannerError("World planner received a different onboarding profile")
        if request.source_group_ids != ("official_records",):
            raise WorldAIBuilderPlannerError("World recorded proof requires the exact official_records group")
        if (
            pack.metadata.pack_id != self.pack_reference.pack_id
            or pack.metadata.version != self.pack_reference.pack_version
            or pack.compiled_pack_id != self.pack_reference.compiled_pack_id
            or pack.pack_digest != self.pack_reference.pack_digest
        ):
            raise WorldAIBuilderPlannerError("World planner received a different compiled Pack")
        inventory = _inventory()
        subject = inventory.get("subject_binding")
        if not isinstance(subject, dict):
            raise WorldAIBuilderPlannerError("recorded World inventory omitted its exact subject")
        selections = tuple(
            RecordedSourceSelectionV1Alpha1(
                product_id=request.product_id,
                pack=self.pack_reference,
                source_group_id="official_records",
                mapping_id=item["mapping_id"],
                subject_binding_id=subject["subject_binding_id"],
                entity_type_id=subject["entity_type_id"],
                entity_ref=subject["entity_ref"],
                source_definition_ref=item["source_definition_ref"],
                source_type_ref=item["source_type_ref"],
                source_uri=item["source_uri"],
                captured_payload_digest=item["captured_payload_digest"],
                source_published_at=_time(item["source_published_at"]),
                event_effective_at=_time(item["event_effective_at"]),
                observed_at=_time(item["observed_at"]),
                locator=item["locator"],
            )
            for item in inventory["materials"]
        )
        overlay = CompiledOverlayV1(
            overlay_id="world_ai_official_records",
            version="1.0.0",
            pack_id=self.pack_reference.pack_id,
            pack_version=self.pack_reference.pack_version,
            pack_digest=self.pack_reference.pack_digest,
        )
        proposal = IntelligenceBuildActivationProposalV1Alpha1(
            product_id=request.product_id,
            activation_key="world_intelligence_ai_command_center",
            pack=self.pack_reference,
            overlay=overlay,
            capability_requirement_ids=tuple(item.requirement_id for item in pack.capability_requirements),
            authority_request_ids=tuple(item.request_id for item in pack.authority_requests),
        )
        return IntelligenceBuildPlanV1Alpha3(
            request=request,
            planner_artifact=self.artifact_identity,
            pack_reference=self.pack_reference,
            activation_proposal=proposal,
            recorded_source_selections=selections,
        )


__all__ = [
    "WORLD_AI_OFFICIAL_RECORDS_PACK",
    "WORLD_AI_PLANNER_VERSION",
    "WorldAIBuilderPlanner",
    "WorldAIBuilderPlannerError",
]
