from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from ace.application import (
    REQUIRED_INTELLIGENCE_BUILD_EFFECTS,
    IntelligenceBuildPlanRequestV1Alpha2,
    IntelligenceBuildPlanV1Alpha3,
    validate_intelligence_build_planner_v1alpha3_registration,
)
from ace.intelligence import IntelligenceOnboardingProfileV1Alpha1
from ace.intelligence.packs import compile_pack_document

import ace_world_ai_builder.planner as planner_module
from ace_world_ai_builder import (
    WORLD_AI_OFFICIAL_RECORDS_PACK,
    WorldAIBuilderPlanner,
    WorldAIBuilderPlannerError,
)

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "domain_packs/world_intelligence_ai_official_records"
PROFILE_PATH = ROOT / "domain_packs/world_intelligence_ai/onboarding_profile.json"
NOW = datetime(2026, 8, 14, 18, tzinfo=UTC)


def _pack():
    manifest = (PACK / "manifest.json").read_bytes()
    material = json.loads(manifest)
    return compile_pack_document(
        manifest,
        {item["path"]: (PACK / item["path"]).read_bytes() for item in material["resources"]},
    )


def _profile() -> IntelligenceOnboardingProfileV1Alpha1:
    return IntelligenceOnboardingProfileV1Alpha1.model_validate_json(PROFILE_PATH.read_text(encoding="utf-8"))


def _request(profile: IntelligenceOnboardingProfileV1Alpha1, **updates) -> IntelligenceBuildPlanRequestV1Alpha2:
    material = {
        "product_id": "product:world-v1",
        "actor_ref": "principal:owner",
        "client_request_id": "atrium:world-v1",
        "profile_id": profile.profile_id,
        "profile_digest": profile.profile_digest,
        "subject": "Track official AI policy progression and operational implications.",
        "outcome_id": "policy_safety_and_operational_risk",
        "source_group_ids": ("official_records",),
        "cadence_id": "daily_pulse",
        "proposed_effects": REQUIRED_INTELLIGENCE_BUILD_EFFECTS,
        "requested_at": NOW,
    }
    material.update(updates)
    return IntelligenceBuildPlanRequestV1Alpha2(**material)


@pytest.fixture(autouse=True)
def _source_checkout(monkeypatch):
    monkeypatch.setattr(planner_module, "_world_domain_file", lambda relative: ROOT / relative)
    monkeypatch.setattr(WorldAIBuilderPlanner, "artifact_identity", planner_module._artifact_identity())


@pytest.mark.asyncio
async def test_world_planner_proposes_exact_two_source_program_without_authority_binding() -> None:
    profile = _profile()
    planner = WorldAIBuilderPlanner()
    plan = await planner.prepare(_request(profile), profile=profile, pack=_pack())

    assert IntelligenceBuildPlanV1Alpha3.model_validate(plan.model_dump(mode="python")) == plan
    assert validate_intelligence_build_planner_v1alpha3_registration(
        planner,
        profile_id=profile.profile_id,
    ) == (WORLD_AI_OFFICIAL_RECORDS_PACK, planner.artifact_identity)
    assert plan.pack_reference == WORLD_AI_OFFICIAL_RECORDS_PACK
    assert plan.activation_proposal.activation_key == "world_intelligence_ai_command_center"
    assert plan.activation_proposal.capability_requirement_ids == (
        "ai_policy_federal_register_snapshot",
        "ai_policy_white_house_snapshot",
    )
    assert plan.activation_proposal.authority_request_ids == (
        "read_ai_policy_federal_register_document",
        "read_ai_policy_white_house_release",
    )
    assert len(plan.recorded_source_selections) == 2
    assert {item.source_definition_ref for item in plan.recorded_source_selections} == {
        "source_definition:ai-policy-eo-14409",
        "source_definition:white-house-gold-eagle-2026-07-14",
    }
    assert not hasattr(plan, "execution_request_id")
    assert not hasattr(plan.activation_proposal, "capability_bindings")
    assert not hasattr(plan.activation_proposal, "authority_grant_bindings")


@pytest.mark.asyncio
async def test_world_planner_rejects_an_unimplemented_source_group() -> None:
    profile = _profile()
    with pytest.raises(WorldAIBuilderPlannerError, match="exact official_records"):
        await WorldAIBuilderPlanner().prepare(
            _request(profile, source_group_ids=("official_publications",)),
            profile=profile,
            pack=_pack(),
        )
