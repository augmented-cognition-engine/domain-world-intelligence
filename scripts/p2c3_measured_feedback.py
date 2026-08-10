"""Measured feedback over the exact P2C2 public-record Reality Brief journey."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ace.application import MeasuredImpactService
from ace.core import (
    ActionIntentV1Alpha1,
    ActionReviewDisposition,
    ActionVerificationDisposition,
    AppendOnlyTransactionRequestV1,
    CapabilityArtifactIdentityV1Alpha1,
    ContextBindingV1Alpha1,
    ContextUseReceiptV1Alpha1,
    DecisionActionDisposition,
    DecisionDisposition,
    DecisionIntentV1Alpha1,
    DecisionV1Alpha1,
    GovernedActionAuthorizationRequestV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    ImmutableRecordReferenceV1,
    ImmutableRecordV1,
    OutcomeIntentV1Alpha1,
    OutcomeV1Alpha1,
    canonical_hash,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    ImpactClassification,
    ImpactConditionsV1Alpha1,
    ImpactCriterionV1Alpha1,
    ImpactEvaluationRequestV1Alpha1,
    ImpactEvidenceV1Alpha1,
    ImpactGovernanceAction,
    ImpactMetricDirection,
    ImpactOutcomeMeasuresV1Alpha1,
    ImpactTargetKind,
)
from ace_reference_workspace_action import ACTION_TYPE

from scripts.p2c2_federal_register_monitor import _time
from scripts.p2c2_governed_reality_brief import (
    _activation_precondition,
    _context,
    _head,
    run_acceptance,
)

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_measured_feedback_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "c" * 64,
)
OUTCOME_TYPE = "review_artifact_quality"
MEASURE_ID = "official_observation_citation_coverage"
CRITERION_ID = "impact_criterion:world-official-observation-citation-coverage"
CRITERION_FROZEN_AT = _time("2026-08-07T18:01:08Z")


@dataclass(frozen=True, slots=True)
class ReviewedExport:
    decision: DecisionV1Alpha1
    decision_ref: ImmutableRecordReferenceV1
    intent: ActionIntentV1Alpha1
    review_ref: ImmutableRecordReferenceV1
    admission_ref: ImmutableRecordReferenceV1
    terminal_ref: ImmutableRecordReferenceV1
    terminal: Any
    content: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class MeasuredVariant:
    export: ReviewedExport
    attribution_ref: ImmutableRecordReferenceV1
    outcome_ref: ImmutableRecordReferenceV1
    score: float


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(f"historical replay attempted new authorization: {request.authorization_key}")


def _digest(material: Any) -> str:
    return f"sha256:{canonical_hash(material)}"


def _record_reference(store, *, kind: str, key: str) -> ImmutableRecordReferenceV1:
    matches = [
        record.reference()
        for record in store.records.values()
        if record.record_kind == kind and record.record_key == key
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one exact {kind} record for {key}, found {len(matches)}")
    return matches[0]


async def _authorize_append(
    state: dict[str, Any],
    *,
    context,
    authorization_key: str,
    subject_ref: str,
    subject_digest: str,
    requested_at: datetime,
):
    environment = state["environment"]
    append_binding = state["append_binding"]
    return await state["reasoning"].authorize_action(
        GovernedActionAuthorizationRequestV1Alpha1(
            authorization_key=authorization_key,
            product_id=environment.fixture["product_id"],
            authenticated_context=context,
            execution_binding=append_binding,
            operation="append_immutable_records",
            subject_ref=subject_ref,
            subject_digest=subject_digest,
            requested_at=requested_at,
            required_state_preconditions=(
                _activation_precondition(environment),
                append_binding.state_head_precondition,
            ),
        )
    )


async def _append_value(
    state: dict[str, Any],
    *,
    value,
    record_kind: str,
    record_key: str,
    transaction_key: str,
    as_of: datetime,
    authorization,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    record = ImmutableRecordV1(
        product_id=environment.fixture["product_id"],
        record_space="world_intelligence",
        record_kind=record_kind,
        record_key=record_key,
        payload_contract=value.contract,
        payload=value.model_dump(mode="python"),
        as_of=as_of,
        available_at=authorization.authorized_at,
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=record.product_id,
        record_space=record.record_space,
        transaction_key=transaction_key,
        records=(record,),
        submitted_at=record.available_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError(f"{record_kind} append returned divergent receipt material")
    return record.reference()


async def _append_control_artifact(state: dict[str, Any]) -> tuple[ImmutableRecordReferenceV1, str]:
    environment = state["environment"]
    brief_ref = state["brief_admission"].transaction_receipt.records[0]
    content = (
        "# Official Record Review Baseline\n\n"
        "Two Federal Communications Commission Federal Register items were admitted for review.\n\n"
        "This source-only control intentionally omits exact admitted Observation identities, routed "
        "context, interpretive claims, and citation linkage.\n"
    )
    payload = {
        "control_type": "source_only_review_artifact",
        "content_markdown": content,
        "document_numbers": ["2026-15932", "2026-16197"],
        "limitations": [
            "recorded_transport_not_network_freshness",
            "control_is_structural_not_a_human-benefit_baseline",
        ],
    }
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key="append:world-source-only-control",
        subject_ref="world_source_only_control:2026-15932:2026-16197",
        subject_digest=_digest(payload),
        requested_at=requested_at,
    )
    record = ImmutableRecordV1(
        product_id=environment.fixture["product_id"],
        record_space="world_intelligence",
        record_kind="brief_control",
        record_key="brief_control:fcc-publication-change:2026-08-07",
        payload_contract="ace.world-intelligence.source-only-control/v1alpha1",
        payload=payload,
        as_of=brief_ref.as_of,
        available_at=authorization.authorized_at,
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=record.product_id,
        record_space=record.record_space,
        transaction_key="world-source-only-control:2026-08-07",
        records=(record,),
        submitted_at=record.available_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError("source-only control append returned divergent receipt material")
    return record.reference(), content


async def _record_decision(
    state: dict[str, Any],
    *,
    subject: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> tuple[DecisionV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    decided_at = state["clock"]()
    intent = DecisionIntentV1Alpha1(
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        subject=subject,
        actor_role_ref="persona:public-researcher",
        decision_type="matched_review_export",
        disposition=DecisionDisposition.ACCEPT,
        action_disposition=DecisionActionDisposition.AUTHORIZE_ACTION,
        action_type=ACTION_TYPE,
        rationale=(
            f"Approve the exact {variant} review artifact for matched citation-coverage pair "
            f"{pair_index}; this Decision does not judge beneficial impact."
        ),
        decided_at=decided_at,
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"decision:measured-feedback:{pair_index}:{variant}",
        subject_ref=str(intent.intent_id),
        subject_digest=str(intent.intent_digest),
        requested_at=decided_at,
    )
    decision = DecisionV1Alpha1(intent=intent, authorization=authorization)
    reference = await _append_value(
        state,
        value=decision,
        record_kind="decision",
        record_key=str(decision.decision_id),
        transaction_key=f"decision:{decision.decision_id}",
        as_of=decided_at,
        authorization=authorization,
    )
    return decision, reference


async def _run_reviewed_export(
    state: dict[str, Any],
    *,
    subject: ImmutableRecordReferenceV1,
    content: str,
    pair_index: int,
    variant: str,
) -> ReviewedExport:
    environment = state["environment"]
    decision, decision_ref = await _record_decision(
        state,
        subject=subject,
        pair_index=pair_index,
        variant=variant,
    )
    relative_path = f"measured-feedback-pair-{pair_index}-{variant}.md"
    intent = ActionIntentV1Alpha1(
        action_key=f"action:world-measured-feedback:{pair_index}:{variant}",
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        decision=decision_ref,
        action_type=ACTION_TYPE,
        parameters_json=canonical_json(
            {
                "relative_path": relative_path,
                "content": content,
            }
        ),
        requested_at=decision_ref.available_at,
    )
    service = state["review_service"]
    prepared = await service.prepare_for_review(intent)
    review = await service.review(
        prepared,
        review_key=f"review:world-measured-feedback:{pair_index}:{variant}",
        reviewer_context=_context(environment.context, "principal:world-impact-reviewer"),
        disposition=ActionReviewDisposition.APPROVE,
        rationale=(
            "The exact create-only path, content digest, and matched evaluation role are approved; "
            "this review does not classify impact."
        ),
    )
    outcome = await service.execute_reviewed(review)
    target = Path(state["workspace_root"]) / relative_path
    written = target.read_text(encoding="utf-8")
    if written != content:
        raise AssertionError("matched review export differs from exact reviewed content")
    await service.verify(
        review,
        outcome,
        verification_key=f"verification:world-measured-feedback:{pair_index}:{variant}",
        verifier_context=_context(environment.context, "principal:world-impact-verifier"),
        disposition=ActionVerificationDisposition.VERIFIED,
        rationale="The created file exists and exactly matches the reviewed artifact.",
    )
    replay = await service.execute_reviewed(review)
    if not replay.replayed:
        raise AssertionError("matched reviewed action did not reopen without a second effect")
    return ReviewedExport(
        decision=decision,
        decision_ref=decision_ref,
        intent=intent,
        review_ref=_record_reference(
            environment.store,
            kind="action_review",
            key=str(review.receipt_id),
        ),
        admission_ref=outcome.admission_transaction.records[0],
        terminal_ref=outcome.terminal_transaction.records[0],
        terminal=outcome.terminal,
        content=written,
        relative_path=relative_path,
    )


def _existing_treatment_export(state: dict[str, Any]) -> ReviewedExport:
    environment = state["environment"]
    review = state["review"]
    outcome = state["action_outcome"]
    return ReviewedExport(
        decision=state["decision"],
        decision_ref=state["decision_ref"],
        intent=review.intent,
        review_ref=_record_reference(
            environment.store,
            kind="action_review",
            key=str(review.receipt_id),
        ),
        admission_ref=outcome.admission_transaction.records[0],
        terminal_ref=outcome.terminal_transaction.records[0],
        terminal=outcome.terminal,
        content=state["written"],
        relative_path="world-reality-brief-2026-16197.md",
    )


async def _record_attribution(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    subject: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    recorded_at = state["clock"]()
    use = ContextUseReceiptV1Alpha1(
        product_id=environment.fixture["product_id"],
        request_id=str(export.decision.intent.intent_id),
        request_digest=str(export.decision.intent.intent_digest),
        result_id=str(export.terminal.result.result_id),
        result_digest=str(export.terminal.result.result_digest),
        context=ContextBindingV1Alpha1(
            context_id=f"context:world-measured-feedback:{pair_index}:{variant}",
            context_digest=_digest(
                {
                    "pair_index": pair_index,
                    "variant": variant,
                    "subject": subject.model_dump(mode="json"),
                }
            ),
            storage_id=subject.storage_id,
            material_digest=subject.material_hash,
            as_of=subject.as_of,
            available_at=subject.available_at,
        ),
        output_referenced=True,
        recorded_at=recorded_at,
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"attribution:world-measured-feedback:{pair_index}:{variant}",
        subject_ref=str(use.receipt_id),
        subject_digest=str(use.receipt_digest),
        requested_at=recorded_at,
    )
    return await _append_value(
        state,
        value=use,
        record_kind="context_use",
        record_key=str(use.receipt_id),
        transaction_key=f"context-use:{use.receipt_id}",
        as_of=recorded_at,
        authorization=authorization,
    )


async def _record_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    observation_keys: tuple[str, ...],
    pair_index: int,
    variant: str,
) -> tuple[ImmutableRecordReferenceV1, float]:
    environment = state["environment"]
    score = sum(key in export.content for key in observation_keys) / len(observation_keys)
    completed_at = export.terminal.result.completed_at
    latency_ms = max(
        0,
        int((completed_at - export.intent.requested_at).total_seconds() * 1_000),
    )
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=float(score),
        latency_ms=latency_ms,
        cost_usd=0.0,
        failure_count=0 if export.terminal.result.disposition.value == "succeeded" else 1,
        degraded=False,
        limitations=(
            "citation_coverage_is_structural_not_a_human-benefit_measure",
            "official_records_use_recorded_transport_not_network_freshness",
        ),
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-outcome-observer")
    intent = OutcomeIntentV1Alpha1(
        product_id=environment.fixture["product_id"],
        authenticated_context=observer,
        decision=export.decision_ref,
        outcome_type=OUTCOME_TYPE,
        measure_id=MEASURE_ID,
        value_json=canonical_json(measures.model_dump(mode="json")),
        observed_at=completed_at,
        recorded_at=recorded_at,
    )
    authorization = await _authorize_append(
        state,
        context=observer,
        authorization_key=f"outcome:world-measured-feedback:{pair_index}:{variant}",
        subject_ref=str(intent.intent_id),
        subject_digest=str(intent.intent_digest),
        requested_at=recorded_at,
    )
    outcome = OutcomeV1Alpha1(intent=intent, authorization=authorization)
    reference = await _append_value(
        state,
        value=outcome,
        record_kind="outcome",
        record_key=str(outcome.outcome_id),
        transaction_key=f"outcome:{outcome.outcome_id}",
        as_of=completed_at,
        authorization=authorization,
    )
    return reference, float(score)


async def _measure_variant(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    subject: ImmutableRecordReferenceV1,
    observation_keys: tuple[str, ...],
    pair_index: int,
    variant: str,
) -> MeasuredVariant:
    attribution_ref = await _record_attribution(
        state,
        export=export,
        subject=subject,
        pair_index=pair_index,
        variant=variant,
    )
    outcome_ref, score = await _record_outcome(
        state,
        export=export,
        observation_keys=observation_keys,
        pair_index=pair_index,
        variant=variant,
    )
    return MeasuredVariant(
        export=export,
        attribution_ref=attribution_ref,
        outcome_ref=outcome_ref,
        score=score,
    )


def _install_impact_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 40)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-measured-feedback",
        41,
    )
    impact_binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-measured-feedback",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(
        product_id,
        "capability_state",
        capability_state_ref_for_artifact(IMPACT_ARTIFACT),
        42,
    )
    authority_head = _head(
        product_id,
        "authority_grant",
        impact_binding.grant_ref,
        43,
    )
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, impact_binding)
    return criterion_head, impact_binding


async def run_measured_feedback(workspace_root: Path) -> dict[str, Any]:
    """Run official records through matched Outcomes and proposal-only feedback."""

    state: dict[str, Any] = {"workspace_root": workspace_root}
    prior = await run_acceptance(workspace_root, state_sink=state)
    environment = state["environment"]
    target_ref = state["brief_admission"].transaction_receipt.records[0]
    control_ref, control_content = await _append_control_artifact(state)
    criterion_head, impact_binding = _install_impact_policy(state)
    observation_refs = tuple(
        record
        for admission in state["admissions"]
        for record in admission.transaction_receipt.records
        if record.record_kind == "observation"
    )
    observation_keys = tuple(sorted(item.record_key for item in observation_refs))
    if len(observation_keys) != 2:
        raise AssertionError("measured World packet requires the two exact admitted Observations")

    treatment_exports = (
        _existing_treatment_export(state),
        await _run_reviewed_export(
            state,
            subject=target_ref,
            content=state["brief_admission"].brief.body_markdown,
            pair_index=2,
            variant="treatment",
        ),
    )
    control_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=control_ref,
                content=control_content,
                pair_index=index,
                variant="control",
            )
            for index in (1, 2)
        ]
    )
    treatments = tuple(
        [
            await _measure_variant(
                state,
                export=export,
                subject=target_ref,
                observation_keys=observation_keys,
                pair_index=index,
                variant="treatment",
            )
            for index, export in enumerate(treatment_exports, start=1)
        ]
    )
    controls = tuple(
        [
            await _measure_variant(
                state,
                export=export,
                subject=control_ref,
                observation_keys=observation_keys,
                pair_index=index,
                variant="control",
            )
            for index, export in enumerate(control_exports, start=1)
        ]
    )
    latest_observed_at = max(
        *(item.export.terminal.result.completed_at for item in treatments),
        *(item.export.terminal.result.completed_at for item in controls),
    )
    window_end = latest_observed_at + timedelta(minutes=1)
    evidence = []
    for index, (treatment, control) in enumerate(zip(treatments, controls, strict=True), start=1):
        conditions = ImpactConditionsV1Alpha1(
            product_id=environment.fixture["product_id"],
            condition_key=f"world-official-record-review-pair:{index}",
            route_id="world:fcc-official-publication-reviewed-export",
            context_json=canonical_json(
                {
                    "pair_index": index,
                    "recorded_transport": True,
                    "required_observation_count": len(observation_keys),
                    "task": "create_only_review_export",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT + timedelta(seconds=1),
            observation_window_end=window_end,
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-measured-feedback:{index}",
                treatment_attribution=treatment.attribution_ref,
                control_attribution=control.attribution_ref,
                treatment_decision=treatment.export.decision_ref,
                control_decision=control.export.decision_ref,
                treatment_action_review=treatment.export.review_ref,
                treatment_action_admission=treatment.export.admission_ref,
                treatment_action_terminal=treatment.export.terminal_ref,
                control_action_review=control.export.review_ref,
                control_action_admission=control.export.admission_ref,
                control_action_terminal=control.export.terminal_ref,
                treatment_outcome=treatment.outcome_ref,
                control_outcome=control.outcome_ref,
                treatment_conditions=conditions,
                control_conditions=conditions,
            )
        )
    criterion = ImpactCriterionV1Alpha1(
        product_id=environment.fixture["product_id"],
        criterion_id=CRITERION_ID,
        criterion_version="candidate-1",
        target_kind=ImpactTargetKind.INTELLIGENCE_ARTIFACT,
        outcome_type=OUTCOME_TYPE,
        measure_id=MEASURE_ID,
        metric_direction=ImpactMetricDirection.HIGHER_IS_BETTER,
        useful_effect_threshold=0.5,
        harmful_effect_threshold=0.5,
        minimum_matched_pairs=2,
        harmful_action=ImpactGovernanceAction.ROLLBACK,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(criterion_head),
        frozen_at=CRITERION_FROZEN_AT,
    )
    cutoff_at = state["clock"]()
    request = ImpactEvaluationRequestV1Alpha1(
        evaluation_key="world-measured-feedback:fcc-publication-change:2026-08-07",
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        criterion=criterion,
        target=target_ref,
        control=control_ref,
        evidence=tuple(evidence),
        cutoff_at=cutoff_at,
        requested_at=state["clock"](),
    )
    service = MeasuredImpactService(
        store=environment.store,
        authorizer=state["reasoning"],
        operation_binding=impact_binding,
    )
    admission = await service.evaluate(request)
    replay = await MeasuredImpactService(
        store=environment.store,
        authorizer=_ReplayMustNotAuthorize(),
        operation_binding=impact_binding,
    ).evaluate(request)
    if (
        admission.replayed
        or not replay.replayed
        or replay
        != admission.__class__(
            evaluation=admission.evaluation,
            proposal=admission.proposal,
            transaction_receipt=admission.transaction_receipt,
            replayed=True,
        )
    ):
        raise AssertionError("World measured feedback did not reopen exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen World citation-coverage criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("useful World evaluation did not emit the product-mapped proposal")

    return {
        "contract": "ace.world-intelligence.measured-feedback/v1alpha1",
        "journey": prior,
        "criterion": {
            "criterion_id": criterion.criterion_id,
            "criterion_digest": criterion.criterion_digest,
            "measure_id": criterion.measure_id,
            "minimum_matched_pairs": criterion.minimum_matched_pairs,
            "useful_effect_threshold": criterion.useful_effect_threshold,
        },
        "controls": {
            "target": target_ref.model_dump(mode="json"),
            "control": control_ref.model_dump(mode="json"),
            "observation_keys": observation_keys,
            "treatment_scores": tuple(item.score for item in treatments),
            "control_scores": tuple(item.score for item in controls),
        },
        "evaluation": admission.evaluation.model_dump(mode="json"),
        "proposal": admission.proposal.model_dump(mode="json"),
        "replay": {
            "historical": replay.replayed,
            "transaction_receipt_id": str(replay.transaction_receipt.receipt_id),
            "no_reauthorization": True,
        },
        "scope": {
            "official_public_records": True,
            "recorded_transport": True,
            "network_freshness_claimed": False,
            "human_benefit_claimed": False,
            "causality_claimed": False,
            "proposal_applied": False,
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
            asyncio.run(run_measured_feedback(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
