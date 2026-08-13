from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from ace.core import GovernedStateHeadPreconditionV1Alpha1
from ace.core.runtime_use import AuthorityUseReceiptV1Alpha1
from ace.intelligence import IntelligenceResourcePageState
from scripts.ai_command_center_live_acceptance import run_acceptance

from ace_world_ai_builder import (
    WORLD_AI_PROFILE_ID,
    WorldAIBuilderExecutor,
    WorldAIBuilderExecutorError,
    WorldAIRecordedExecutionContext,
    load_world_ai_onboarding_profile,
    plan_from_authorized_build,
)

STARTED_AT = datetime(2026, 8, 10, 20, 4, 35, tzinfo=UTC)
BUILD_GRANT = "authority_grant:world-ai-build"
READ_GRANT = "authority_grant:world-ai-read"


@dataclass(frozen=True, slots=True)
class BuildRequest:
    authority_grant_ref: str
    client_request_id: str
    profile_id: str
    subject: str
    outcome_id: str
    source_group_ids: tuple[str, ...]
    cadence_id: str
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class AuthorizedBuild:
    build_id: str
    request_digest: str
    product_id: str
    actor_ref: str
    request: BuildRequest
    authority_use: AuthorityUseReceiptV1Alpha1


def _authority(
    *,
    context,
    subject_ref: str,
    subject_digest: str,
    operation: str,
    authority: str,
    grant_ref: str,
    evaluated_at: datetime = STARTED_AT,
):
    return AuthorityUseReceiptV1Alpha1(
        product_id=context.product_id,
        actor_ref=context.actor_ref,
        authenticated_context=context,
        use_subject_ref=subject_ref,
        use_subject_digest=subject_digest,
        operation=operation,
        authority=authority,
        grant_ref=grant_ref,
        grant_hash="9" * 64,
        evaluated_at=evaluated_at,
        expires_at=context.expires_at,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1(
            state_kind="authority_grant",
            product_id=context.product_id,
            state_id=grant_ref,
            sequence=1,
            revision_id=f"authority_revision:{grant_ref.rsplit(':', 1)[-1]}",
            commit_receipt_id=f"authority_receipt:{grant_ref.rsplit(':', 1)[-1]}",
        ),
    )


def _build(*, context, source_group_ids=("official_records",), cadence_id="weekly_brief"):
    request = BuildRequest(
        authority_grant_ref=BUILD_GRANT,
        client_request_id="request:world-ai-builder-test",
        profile_id=WORLD_AI_PROFILE_ID,
        subject="Federal AI cybersecurity implementation",
        outcome_id="strategy_and_investment",
        source_group_ids=source_group_ids,
        cadence_id=cadence_id,
        requested_at=STARTED_AT,
    )
    build_id = "intelligence_build:world-ai-builder-test"
    request_digest = "sha256:" + "7" * 64
    return AuthorizedBuild(
        build_id=build_id,
        request_digest=request_digest,
        product_id=context.product_id,
        actor_ref=context.actor_ref,
        request=request,
        authority_use=_authority(
            context=context,
            subject_ref=build_id,
            subject_digest=request_digest,
            operation="start_intelligence_build",
            authority="intelligence_build",
            grant_ref=BUILD_GRANT,
        ),
    )


class ExactReadAuthority:
    async def resolve_authority_use(self, **request):
        return _authority(
            context=request["context"],
            subject_ref=request["use_subject_ref"],
            subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=request["grant_ref"],
            evaluated_at=request["evaluated_at"],
        )


class RecordedContextProvider:
    def __init__(self, *, state):
        self.state = state
        self.builds = []

    async def prepare(self, build):
        self.builds.append(build)
        return WorldAIRecordedExecutionContext(
            environment=self.state["environment"],
            baseline=self.state["baseline"],
            current=self.state["current"],
            started_at=STARTED_AT,
            resource_authority=ExactReadAuthority(),
            resource_grant_ref=READ_GRANT,
        )


async def test_executor_consumes_authorized_core_request_and_returns_exact_resource_page() -> None:
    state = {}
    await run_acceptance(state_sink=state)
    build = _build(context=state["environment"].context)
    provider = RecordedContextProvider(state=state)
    executor = WorldAIBuilderExecutor(
        contexts=provider,
        onboarding_profile=load_world_ai_onboarding_profile(),
    )

    page = await executor.start(build)

    assert provider.builds == [build]
    assert page.product_id == build.product_id
    assert page.actor_ref == build.actor_ref
    assert page.state is IntelligenceResourcePageState.COMPLETE
    assert page.degraded_reason_refs == ()
    kinds = {item.reference.resource_kind.value for item in page.items}
    assert {"source", "connection", "entity", "observation", "shift", "signal", "case", "brief"} <= kinds
    sessions = [item for item in page.items if item.reference.resource_kind.value == "builder_session"]
    assert [item.reference.revision for item in sessions] == list(range(1, 9))
    assert page.authority_use.operation == "query_intelligence_resources"
    assert page.authority_use.authority == "observe_read"
    plan = plan_from_authorized_build(build)
    assert plan.subject == "Federal AI cybersecurity implementation"
    assert plan.goal_ref == "goal:world-ai-strategy_and_investment-7777777777777777"
    assert plan.cadence.value == "weekly"


async def test_executor_rejects_unimplemented_source_groups_before_preparing_context() -> None:
    state = {}
    await run_acceptance(state_sink=state)
    build = _build(
        context=state["environment"].context,
        source_group_ids=("official_records", "open_ecosystem"),
    )
    provider = RecordedContextProvider(state=state)
    executor = WorldAIBuilderExecutor(
        contexts=provider,
        onboarding_profile=load_world_ai_onboarding_profile(),
    )

    with pytest.raises(WorldAIBuilderExecutorError, match="supports only the reviewed official_records"):
        await executor.start(build)
    assert provider.builds == []
