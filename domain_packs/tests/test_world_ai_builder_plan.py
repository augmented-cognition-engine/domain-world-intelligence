from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from ace import __version__ as ACE_CORE_VERSION
from ace.application import IntelligenceBuilderSessionService
from ace.application.intelligence_agent_contracts import IntelligenceModelProposalV1, ProposedCadence

from scripts.ai_command_center_live_acceptance import run_acceptance
from scripts.world_ai_builder_journey import (
    DEFAULT_WORLD_AI_BUILDER_PLAN,
    SUPPORTED_RECORDED_SOURCE_OPTION_IDS,
    WorldAIBuilderPlan,
    run_world_ai_builder_journey,
)

STARTED_AT = datetime(2026, 8, 10, 20, 4, 35, tzinfo=UTC)


async def _run_plan(plan: WorldAIBuilderPlan):
    state: dict[str, object] = {}
    await run_acceptance(state_sink=state)
    environment = state["environment"]
    admission = await run_world_ai_builder_journey(
        environment=environment,
        baseline=state["baseline"],
        current=state["current"],
        started_at=STARTED_AT,
        plan=plan,
    )
    model_reference = next(
        item
        for item in admission.session.revision.artifacts
        if item.artifact_kind.value == "intelligence_model_proposal"
    )
    intelligence_model = await IntelligenceBuilderSessionService(store=environment.store).load_artifact(
        product_id=environment.context.product_id,
        reference=model_reference,
        artifact_type=IntelligenceModelProposalV1,
        available_at=STARTED_AT + timedelta(seconds=9),
    )
    return admission, intelligence_model


def _citation_closure(admission) -> set[tuple[str, str, str]]:
    return {
        (citation.source_ref, citation.evidence_digest, citation.field_path) for citation in admission.brief.citations
    }


def test_reviewed_builder_plan_changes_persisted_intelligence_without_changing_evidence() -> None:
    strategic_plan = WorldAIBuilderPlan(
        subject="Federal AI cybersecurity policy",
        goal_ref="goal:evaluate-federal-ai-cybersecurity-policy",
        outcome_id="strategy_and_investment",
        user_intent="Evaluate how reported federal AI cybersecurity implementation changes strategic exposure.",
        audience_constraint="Orient a strategy leader while preserving the limits of first-party evidence.",
        cadence=ProposedCadence.WEEKLY,
    )

    default_admission, default_model = asyncio.run(_run_plan(DEFAULT_WORLD_AI_BUILDER_PLAN))
    strategic_admission, strategic_model = asyncio.run(_run_plan(strategic_plan))

    assert default_admission.session.revision.goal_ref == "goal:track-material-ai-change"
    assert strategic_admission.session.revision.goal_ref == strategic_plan.goal_ref
    assert default_model.user_intent == DEFAULT_WORLD_AI_BUILDER_PLAN.user_intent
    expected_model_digests = {
        "0.8.2": "sha256:1c89a4c82712a27b85c4e10771e623506abfda9853a44c7721842e0be34de559",
        "0.8.3": "sha256:567dedf093afbe170c60a1c8641b3d6e5cb4b785777b97d77651d72545c33f85",
        "1.0.0": "sha256:567dedf093afbe170c60a1c8641b3d6e5cb4b785777b97d77651d72545c33f85",
    }
    assert str(default_model.proposal_digest) == expected_model_digests[ACE_CORE_VERSION]
    expected_brief_digests = {
        "0.8.2": "sha256:befbab8736acd0b73c1c0d5fd4bebc195163d451da1110f00b5aaba17793c011",
        "0.8.3": "sha256:5eb70eedca91828f75f6cded0ba49028984eca2dba7dbe9a12e71bc7a489f660",
        "1.0.0": "sha256:5eb70eedca91828f75f6cded0ba49028984eca2dba7dbe9a12e71bc7a489f660",
    }
    assert str(default_admission.brief.brief_digest) == expected_brief_digests[ACE_CORE_VERSION]
    assert strategic_model.user_intent == strategic_plan.user_intent
    assert default_model.routes[0].cadence == ProposedCadence.DAILY
    assert strategic_model.routes[0].cadence == ProposedCadence.WEEKLY
    assert default_model.proposal_digest != strategic_model.proposal_digest
    assert default_admission.brief.brief_digest != strategic_admission.brief.brief_digest
    assert default_admission.brief.title == "AI policy moved from directive to reported implementation"
    assert strategic_admission.brief.title == (
        "Federal AI cybersecurity policy moved from directive to reported implementation"
    )
    strategic_shift = next(
        item for item in strategic_admission.brief.items if item.item_id == "reported_implementation_shift"
    )
    assert strategic_shift.recommended_attention == (
        "Assess whether the reported implementation changes investment timing, partner dependencies, "
        "or strategic exposure."
    )
    assert strategic_shift.decision_question == (
        "Which strategic assumptions now depend on this implementation milestone?"
    )
    assert _citation_closure(default_admission) == _citation_closure(strategic_admission)
    expected_source_digests = {
        "0.8.2": {
            "source_snapshot:7b79e35507287aa63df2640bf121978e": (
                "sha256:688f1d0075b464f6b890254e85465be6fbeddf7c5898c1cc449b5b16fd4213ab"
            ),
            "source_snapshot:4bf705b079706f02f492c250bd7de899": (
                "sha256:4e353594d4a0560046f13eae42ec43a867aeb23be8607f98ef493892f28fbfb9"
            ),
        },
        "0.8.3": {
            "source_snapshot:7b79e35507287aa63df2640bf121978e": (
                "sha256:78d200c8f91e64e35c2949e485153200677cdb7157f4195696e3ecc7b9323d56"
            ),
            "source_snapshot:4bf705b079706f02f492c250bd7de899": (
                "sha256:2839eb8c332dcf5e535be38a977529c2368150d4553a33eca54674b0a5830a41"
            ),
        },
        "1.0.0": {
            "source_snapshot:7b79e35507287aa63df2640bf121978e": (
                "sha256:78d200c8f91e64e35c2949e485153200677cdb7157f4195696e3ecc7b9323d56"
            ),
            "source_snapshot:4bf705b079706f02f492c250bd7de899": (
                "sha256:2839eb8c332dcf5e535be38a977529c2368150d4553a33eca54674b0a5830a41"
            ),
        },
    }
    assert _citation_closure(strategic_admission) == {
        (source_ref, evidence_digest, field_path)
        for source_ref, evidence_digest in expected_source_digests[ACE_CORE_VERSION].items()
        for field_path in ("/development_stage", "/source_lineage")
    }


def test_recorded_builder_plan_rejects_unimplemented_source_choices() -> None:
    assert SUPPORTED_RECORDED_SOURCE_OPTION_IDS == (
        "federal_register_ai_policy",
        "white_house_ai_policy",
    )
    with pytest.raises(ValueError, match="requires the exact reviewed Federal Register and White House"):
        WorldAIBuilderPlan(source_option_ids=("github_releases",))
