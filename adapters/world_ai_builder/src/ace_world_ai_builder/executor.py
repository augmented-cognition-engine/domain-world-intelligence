"""Trusted application adapter for the recorded World AI Builder journey.

This package is intentionally separate from the inert World Domain Pack. Core
authenticates and authorizes the generic build request; this adapter translates
only the supported AI Command Center profile into World-owned builder inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib.metadata import distribution
from typing import Any, Protocol

from ace.application import (
    ActionResourceProjectionReader,
    AgentMemoryResourceProjectionReader,
    AgentResourceProjectionReader,
    CompositeIntelligenceResourceProjectionReader,
    DecisionOutcomeFeedbackResourceProjectionReader,
    IntelligenceBuilderPresentationService,
    IntelligenceBuilderResourceProjectionReader,
    IntelligenceLedgerResourceProjectionReader,
    IntelligenceResourcePlaneService,
    LiveSourceResourceProjectionReader,
    MonitoringResourceProjectionReader,
)
from ace.application.intelligence_agent_contracts import ProposedCadence
from ace.intelligence import (
    IntelligenceOnboardingProfileV1Alpha1,
    IntelligenceResourceKind,
    IntelligenceResourceQueryV1Alpha1,
)

from .journey import WorldAIBuilderPlan, run_world_ai_builder_journey

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

_CADENCES = {
    "urgent_only": ProposedCadence.IMMEDIATE,
    "daily_pulse": ProposedCadence.DAILY,
    "weekly_brief": ProposedCadence.WEEKLY,
}
_OUTCOME_INTENTS = {
    "build_or_buy_ai": "Evaluate how admitted AI policy progression changes build, buy, provider, and control requirements.",
    "strategy_and_investment": "Evaluate how admitted AI policy progression changes strategic exposure and investment assumptions.",
    "frontier_research_and_products": "Track how admitted AI policy progression changes research priorities and product constraints.",
    "policy_safety_and_operational_risk": (
        "Watch official AI policy progression and keep evidence-role limits visible."
    ),
    "competitive_landscape": "Compare how admitted AI policy progression changes provider and organizational positioning.",
    "custom_picture": "Track the admitted AI policy progression for the reviewed subject and preserve evidence-role limits.",
}


class WorldAIBuilderExecutorError(RuntimeError):
    """A reviewed request cannot be executed by the recorded World adapter."""


class AuthorizedIntelligenceBuildRequest(Protocol):
    profile_id: str
    subject: str
    outcome_id: str
    source_group_ids: tuple[str, ...]
    cadence_id: str


class AuthorizedIntelligenceBuildPort(Protocol):
    """Structural public boundary consumed from the Core-authorized host."""

    build_id: str
    request_digest: str
    product_id: str
    actor_ref: str
    request: AuthorizedIntelligenceBuildRequest
    authority_use: Any


@dataclass(frozen=True, slots=True)
class WorldAIRecordedExecutionContext:
    """Trusted host material needed to run and project one recorded journey."""

    environment: Any
    baseline: Any
    current: Any
    started_at: datetime
    resource_authority: Any
    resource_grant_ref: str


class WorldAIRecordedContextProvider(Protocol):
    async def prepare(self, build: AuthorizedIntelligenceBuildPort) -> WorldAIRecordedExecutionContext: ...


def load_world_ai_onboarding_profile() -> IntelligenceOnboardingProfileV1Alpha1:
    """Load the inert profile shipped by the separate World Domain Pack."""

    profile_path = distribution("ace-domain-world-intelligence").locate_file(
        "domain_packs/world_intelligence_ai/onboarding_profile.json"
    )
    material = profile_path.read_text(encoding="utf-8")
    return IntelligenceOnboardingProfileV1Alpha1.model_validate_json(material)


def plan_from_authorized_build(build: AuthorizedIntelligenceBuildPort) -> WorldAIBuilderPlan:
    """Translate one exact Core request without broadening its source claims."""

    request = build.request
    if request.profile_id != WORLD_AI_PROFILE_ID:
        raise WorldAIBuilderExecutorError("World AI Builder received an unsupported onboarding profile")
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


def _reader(store) -> CompositeIntelligenceResourceProjectionReader:
    return CompositeIntelligenceResourceProjectionReader(
        IntelligenceBuilderResourceProjectionReader(store=store, degrade_unsupported=False),
        ActionResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentMemoryResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentResourceProjectionReader(store=store, degrade_unsupported=False),
        IntelligenceLedgerResourceProjectionReader(store=store, degrade_unsupported=False),
        MonitoringResourceProjectionReader(store=store, degrade_unsupported=False),
        DecisionOutcomeFeedbackResourceProjectionReader(store=store, degrade_unsupported=False),
        LiveSourceResourceProjectionReader(store=store, degrade_unsupported=False),
    )


@dataclass(frozen=True, slots=True)
class WorldAIBuilderExecutor:
    """Core-compatible executor for one exact recorded World AI build."""

    contexts: WorldAIRecordedContextProvider
    onboarding_profile: IntelligenceOnboardingProfileV1Alpha1

    async def start(self, build: AuthorizedIntelligenceBuildPort):
        plan = plan_from_authorized_build(build)
        prepared = await self.contexts.prepare(build)
        environment = prepared.environment
        context = environment.context
        if context.product_id != build.product_id or context.actor_ref != build.actor_ref:
            raise WorldAIBuilderExecutorError("recorded execution context crossed the authorized build scope")
        if prepared.started_at.tzinfo is None or prepared.started_at.utcoffset() is None:
            raise WorldAIBuilderExecutorError("recorded execution time must include a timezone")

        await IntelligenceBuilderPresentationService(store=environment.store).admit_profile(
            product_id=build.product_id,
            profile=self.onboarding_profile,
            admitted_at=prepared.started_at - timedelta(seconds=1),
        )
        await run_world_ai_builder_journey(
            environment=environment,
            baseline=prepared.baseline,
            current=prepared.current,
            started_at=prepared.started_at,
            plan=plan,
        )

        records = tuple(environment.store.records.values())
        if not records:
            raise WorldAIBuilderExecutorError("recorded execution produced no governed records")
        as_of = max(record.as_of for record in records)
        available_at = max(record.available_at for record in records)
        evaluated_at = max(available_at, prepared.started_at + timedelta(seconds=10))
        if evaluated_at >= context.expires_at:
            raise WorldAIBuilderExecutorError("recorded execution fell outside the authenticated context")
        query = IntelligenceResourceQueryV1Alpha1(
            authenticated_context=context,
            product_id=build.product_id,
            authority_grant_ref=prepared.resource_grant_ref,
            resource_kinds=READ_KINDS,
            subject_refs=(),
            as_of=as_of,
            available_at=available_at,
            page_size=200,
        )
        return await IntelligenceResourcePlaneService(
            reader=_reader(environment.store),
            authority=prepared.resource_authority,
        ).query(query, evaluated_at=evaluated_at)


__all__ = [
    "READ_KINDS",
    "SUPPORTED_RECORDED_SOURCE_GROUP_IDS",
    "WORLD_AI_PROFILE_ID",
    "AuthorizedIntelligenceBuildPort",
    "AuthorizedIntelligenceBuildRequest",
    "WorldAIBuilderExecutor",
    "WorldAIBuilderExecutorError",
    "WorldAIRecordedContextProvider",
    "WorldAIRecordedExecutionContext",
    "load_world_ai_onboarding_profile",
    "plan_from_authorized_build",
]
