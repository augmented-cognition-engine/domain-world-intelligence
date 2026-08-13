"""Build the World AI Command Center page consumed by ACE Atrium.

The artifact is not a second UI and it does not invent presentation-only
intelligence. It runs the accepted recorded-source journey, then queries the
same public, domain-neutral Intelligence resource plane Atrium uses.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    MonitoringLifecycleService,
    MonitoringResourceProjectionReader,
)
from ace.core import GovernedStateHeadPreconditionV1Alpha1
from ace.core.runtime_use import AuthorityUseReceiptV1Alpha1
from ace.intelligence import (
    ExactMaterialReferenceV1Alpha1,
    IntelligenceOnboardingProfileV1Alpha1,
    IntelligenceResourceKind,
    IntelligenceResourceQueryV1Alpha1,
    MonitorDisposition,
    MonitoringLifecycleAction,
    MonitoringLifecycleRequestV1Alpha1,
    MonitoringTargetKind,
    MonitorV1Alpha1,
    PersonaBindingV1Alpha1,
    SubscriptionDeliveryDisposition,
    SubscriptionV1Alpha1,
)

from scripts.ai_command_center_live_acceptance import run_acceptance
from scripts.world_ai_builder_journey import run_world_ai_builder_journey

READ_GRANT = "authority_grant:world-ai-atrium-read"
READ_KINDS = tuple(IntelligenceResourceKind)
REPOSITORY_ROOT = Path(__file__).parents[1]


class ExactReadAuthority:
    async def resolve_authority_use(self, **request) -> AuthorityUseReceiptV1Alpha1:
        if (
            request["operation"] != "query_intelligence_resources"
            or request["authority"] != "observe_read"
            or request["grant_ref"] != READ_GRANT
        ):
            raise ValueError("Atrium demo query crossed its exact read boundary")
        context = request["context"]
        return AuthorityUseReceiptV1Alpha1(
            product_id=context.product_id,
            actor_ref=context.actor_ref,
            authenticated_context=context,
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=READ_GRANT,
            grant_hash="9" * 64,
            evaluated_at=request["evaluated_at"],
            expires_at=context.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1(
                state_kind="authority_grant",
                product_id=context.product_id,
                state_id=READ_GRANT,
                sequence=1,
                revision_id="authority_revision:world-ai-atrium-read",
                commit_receipt_id="authority_receipt:world-ai-atrium-read",
            ),
        )


def _reader(store):
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


def _exact_material(reference: str, digest: str) -> ExactMaterialReferenceV1Alpha1:
    return ExactMaterialReferenceV1Alpha1(reference=reference, digest=digest)


async def _admit_ai_policy_watch(environment) -> None:
    """Create a real owner-scoped monitor and subscription over the activated pack."""

    product_id = environment.context.product_id
    activation = environment.committed_activation.revision
    pack = activation.spec.pack
    activation_ref = str(activation.revision_id)
    monitor = MonitorV1Alpha1(
        monitor_id="ai_policy_progression",
        product_id=product_id,
        subject_entity_type_ids=("ai_policy_record",),
        subject_refs=("entity:ai-policy/executive-order-14409",),
        detection_rule_ids=("ai_policy_implementation_progression",),
        compiled_pack=pack,
        activation_revision_ref=activation_ref,
        disposition=MonitorDisposition.ENABLED,
    )
    binding = PersonaBindingV1Alpha1(
        product_id=product_id,
        principal_ref=environment.context.actor_ref,
        persona_id="ai_policy_researcher",
        compiled_pack=pack,
        activation_revision_ref=activation_ref,
    )
    subscription = SubscriptionV1Alpha1(
        subscription_id="ai_policy_reality_brief",
        product_id=product_id,
        persona_binding_ref=str(binding.binding_ref),
        monitor_refs=(str(monitor.monitor_ref),),
        signal_types=("official_ai_policy_development",),
        brief_template_ids=("ai_policy_reality_brief",),
        minimum_confidence=0.8,
        delivery=SubscriptionDeliveryDisposition.RECORD_ONLY,
    )
    lifecycle = MonitoringLifecycleService(store=environment.store)
    for key, kind, target, requested_at in (
        (
            "world-ai-policy-monitor-create",
            MonitoringTargetKind.MONITOR,
            monitor,
            datetime(2026, 8, 10, 20, 4, 30, tzinfo=UTC),
        ),
        (
            "world-ai-policy-subscription-create",
            MonitoringTargetKind.SUBSCRIPTION,
            subscription,
            datetime(2026, 8, 10, 20, 4, 31, tzinfo=UTC),
        ),
    ):
        target_ref = (
            _exact_material(str(target.monitor_ref), str(target.monitor_digest))
            if isinstance(target, MonitorV1Alpha1)
            else _exact_material(str(target.subscription_ref), str(target.subscription_digest))
        )
        request = MonitoringLifecycleRequestV1Alpha1(
            transition_key=f"monitoring_transition:{key}",
            product_id=product_id,
            authenticated_context=environment.context,
            target_kind=kind,
            target=target_ref,
            persona_binding=_exact_material(str(binding.binding_ref), str(binding.binding_digest)),
            action=MonitoringLifecycleAction.CREATE,
            sequence=1,
            requested_at=requested_at,
        )
        await lifecycle.transition(
            request=request,
            persona_binding=binding,
            target=target,
            applied_at=requested_at,
        )


async def build_atrium_page() -> dict[str, Any]:
    state: dict[str, Any] = {}
    proof = await run_acceptance(state_sink=state)
    environment = state["environment"]
    await _admit_ai_policy_watch(environment)
    profile = IntelligenceOnboardingProfileV1Alpha1.model_validate_json(
        (REPOSITORY_ROOT / "domain_packs/world_intelligence_ai/onboarding_profile.json").read_text(
            encoding="utf-8"
        )
    )
    await IntelligenceBuilderPresentationService(store=environment.store).admit_profile(
        product_id=environment.context.product_id,
        profile=profile,
        admitted_at=datetime(2026, 8, 10, 20, 4, 34, tzinfo=UTC),
    )
    builder = await run_world_ai_builder_journey(
        environment=environment,
        baseline=state["baseline"],
        current=state["current"],
        started_at=datetime(2026, 8, 10, 20, 4, 35, tzinfo=UTC),
    )
    records = tuple(environment.store.records.values())
    evaluated_at = datetime(2026, 8, 10, 20, 5, tzinfo=UTC)
    request = IntelligenceResourceQueryV1Alpha1(
        authenticated_context=environment.context,
        product_id=environment.context.product_id,
        authority_grant_ref=READ_GRANT,
        resource_kinds=READ_KINDS,
        subject_refs=(),
        as_of=max(record.as_of for record in records),
        available_at=max(record.available_at for record in records),
        page_size=200,
    )
    page = await IntelligenceResourcePlaneService(
        reader=_reader(environment.store),
        authority=ExactReadAuthority(),
    ).query(request, evaluated_at=evaluated_at)
    payload = page.model_dump(mode="json")
    payload["demo"] = {
        "contract": "ace.world-intelligence.atrium-demo/v1alpha1",
        "source_proof_contract": proof["contract"],
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
        "topic_id": "artificial_intelligence",
        "source_catalog": "domain_packs/world_intelligence_ai/source_catalog.json",
        "admitted_source_count": len(proof["source"]["lineages"]),
        "reviewed_publisher_count": proof["source"]["publisher_count"] + 2,
        "context_watch_areas": proof["source"]["context_watch_areas"],
        "brief_grounded_source_count": 2,
        "builder_profile_id": profile.profile_id,
        "builder_session_id": builder.session.revision.session_id,
        "builder_stage": builder.session.revision.stage.value,
        "builder_agent_roles": ["connection", "ontology", "intelligence", "briefing"],
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/atrium-demo/world-ai-resource-page.json"),
    )
    arguments = parser.parse_args()
    payload = asyncio.run(build_atrium_page())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "product_id": payload["product_id"],
                "resource_count": len(payload["items"]),
                "state": payload["state"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
