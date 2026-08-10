"""Explicitly reject broader promotion of the exact P2C3 structural result."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ace.application import (
    MeasuredImpactDispositionRequestV1Alpha1,
    MeasuredImpactDispositionService,
)
from ace.core import (
    CapabilityArtifactIdentityV1Alpha1,
    DecisionActionDisposition,
    DecisionDisposition,
    GovernedOperationBindingV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    capability_state_ref_for_artifact,
)

from scripts.p2c2_governed_reality_brief import _context, _head
from scripts.p2c3_measured_feedback import run_measured_feedback

DISPOSITION_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_proposal_disposition",
    contract="ace.application.measured-impact-disposition-service/v1alpha1",
    implementation_id="world_measured_impact_disposition_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "d" * 64,
)


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(f"historical disposition requested new authority: {request.authorization_key}")


def _install_disposition_policy(state: dict[str, Any]) -> GovernedOperationBindingV1Alpha1:
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-measured-impact-disposition",
        50,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=DISPOSITION_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact_disposition",
        grant_ref="authority_grant:world-measured-impact-disposition",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(
        product_id,
        "capability_state",
        capability_state_ref_for_artifact(DISPOSITION_ARTIFACT),
        51,
    )
    authority_head = _head(
        product_id,
        "authority_grant",
        binding.grant_ref,
        52,
    )
    for head in (operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return binding


async def run_reviewed_disposition(workspace_root: Path) -> dict[str, Any]:
    """Run P2C3, then record one exact reject/no-action human Decision."""

    state: dict[str, Any] = {}
    measured = await run_measured_feedback(workspace_root, state_sink=state)
    environment = state["environment"]
    binding = _install_disposition_policy(state)
    evaluation_ref, proposal_ref = state["impact_admission"].transaction_receipt.records
    context = _context(environment.context, "principal:world-impact-governor")
    request = MeasuredImpactDispositionRequestV1Alpha1(
        product_id=environment.fixture["product_id"],
        authenticated_context=context,
        evaluation=evaluation_ref,
        proposal=proposal_ref,
        reviewer_role_ref="role:world-impact-governor",
        disposition=DecisionDisposition.REJECT,
        rationale=(
            "Reject broader promotion of the Reality Brief. The exact useful result establishes "
            "structural citation coverage under one frozen fixture criterion, but does not establish "
            "citation correctness, general Brief quality, human benefit, causality, or live freshness."
        ),
        decided_at=state["clock"](),
    )
    heads_before = dict(environment.store.governed_state_heads)
    admission = await MeasuredImpactDispositionService(
        store=environment.store,
        authorizer=state["reasoning"],
        operation_binding=binding,
    ).decide(request)
    heads_after = dict(environment.store.governed_state_heads)
    replay = await MeasuredImpactDispositionService(
        store=environment.store,
        authorizer=_ReplayMustNotAuthorize(),
        operation_binding=binding,
    ).decide(request)
    if (
        admission.replayed
        or not replay.replayed
        or admission.decision != replay.decision
        or admission.transaction_receipt != replay.transaction_receipt
    ):
        raise AssertionError("reviewed impact disposition did not replay exact historical material")
    if (
        admission.decision.intent.disposition is not DecisionDisposition.REJECT
        or admission.decision.intent.action_disposition is not DecisionActionDisposition.NO_ACTION
        or admission.decision.intent.subject != proposal_ref
    ):
        raise AssertionError("reviewed impact disposition crossed the exact reject/no-action boundary")
    if heads_after != heads_before:
        raise AssertionError("reviewed proposal disposition mutated effective governed state")

    return {
        "contract": "ace.world-intelligence.reviewed-impact-disposition/v1alpha1",
        "measured_feedback": measured,
        "disposition": {
            "decision": admission.decision.model_dump(mode="json"),
            "decision_reference": admission.decision_reference.model_dump(mode="json"),
            "proposal_reference": proposal_ref.model_dump(mode="json"),
            "evaluation_reference": evaluation_ref.model_dump(mode="json"),
            "replayed": replay.replayed,
            "no_reauthorization": True,
            "effective_state_changed": False,
        },
        "scope": {
            "measured_classification_preserved": measured["evaluation"]["classification"],
            "proposal_action_preserved": measured["proposal"]["action"],
            "proposal_disposition": admission.decision.intent.disposition.value,
            "proposal_applied": False,
            "human_benefit_claimed": False,
            "causality_claimed": False,
            "network_freshness_claimed": False,
            "autonomous_publication": False,
        },
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_root", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(run_reviewed_disposition(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
