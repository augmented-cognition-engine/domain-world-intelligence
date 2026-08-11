"""Measure contradiction attention without rewarding raw alert volume."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Self

from ace.application import MeasuredImpactService
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    ImmutableRecordReferenceV1,
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
from pydantic import Field, field_validator, model_validator

from scripts.p2c2_federal_register_monitor import _time
from scripts.p2c2_governed_reality_brief import _context, _head
from scripts.p2c3_measured_feedback import (
    ReviewedExport,
    _append_value,
    _authorize_append,
    _digest,
    _record_attribution,
    _run_reviewed_export,
)
from scripts.p2c5_citation_correctness_outcome import (
    _derive_identity,
    _FrozenModel,
    _statements_from_observations,
    run_citation_correctness_outcome,
)

OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "contradiction_attention_quality"
CRITERION_ID = "impact_criterion:world-contradiction-attention-quality"
CRITERION_FROZEN_AT = _time("2026-08-07T18:01:20Z")
REVIEW_POLICY_ID = "world_official_record_contradiction_attention"
REVIEW_POLICY_VERSION = "candidate-1"

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_contradiction_attention_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "f" * 64,
)


class ContradictionAttentionDecisionV1Alpha1(_FrozenModel):
    """One World-owned alert-or-silence decision over an exact candidate statement."""

    contract: Literal["ace.world-intelligence.contradiction-attention-decision/v1alpha1"] = (
        "ace.world-intelligence.contradiction-attention-decision/v1alpha1"
    )
    candidate_id: str
    statement: str
    disposition: Literal["alert", "silence"]
    rationale: str
    decision_id: str | None = None
    decision_digest: str | None = None

    @model_validator(mode="after")
    def derive_identity(self) -> Self:
        _derive_identity(
            self,
            prefix="contradiction_attention_decision",
            id_field="decision_id",
            digest_field="decision_digest",
        )
        return self


class ContradictionAttentionArtifactV1Alpha1(_FrozenModel):
    """Exact product response to one contradiction and one valid comparator."""

    contract: Literal["ace.world-intelligence.contradiction-attention-artifact/v1alpha1"] = (
        "ace.world-intelligence.contradiction-attention-artifact/v1alpha1"
    )
    product_id: str
    artifact_key: str
    source_brief: ImmutableRecordReferenceV1
    source_observations: tuple[ImmutableRecordReferenceV1, ...] = Field(min_length=2, max_length=2)
    decisions: tuple[ContradictionAttentionDecisionV1Alpha1, ...] = Field(min_length=2, max_length=2)
    emitted_alert_count: int = Field(ge=0, le=2)
    limitations: tuple[str, ...]
    generated_at: datetime
    artifact_id: str | None = None
    artifact_digest: str | None = None

    @field_validator("source_observations")
    @classmethod
    def canonicalize_observations(
        cls, value: tuple[ImmutableRecordReferenceV1, ...]
    ) -> tuple[ImmutableRecordReferenceV1, ...]:
        ordered = tuple(sorted(value, key=lambda item: item.storage_id))
        if len({item.storage_id for item in ordered}) != len(ordered):
            raise ValueError("contradiction artifact duplicated an Observation identity")
        return ordered

    @field_validator("decisions")
    @classmethod
    def canonicalize_decisions(
        cls, value: tuple[ContradictionAttentionDecisionV1Alpha1, ...]
    ) -> tuple[ContradictionAttentionDecisionV1Alpha1, ...]:
        ordered = tuple(sorted(value, key=lambda item: item.candidate_id))
        if len({item.candidate_id for item in ordered}) != len(ordered):
            raise ValueError("contradiction artifact duplicated a candidate identity")
        return ordered

    @model_validator(mode="after")
    def validate_scope_volume_and_identity(self) -> Self:
        if self.source_brief.product_id != self.product_id or any(
            item.product_id != self.product_id for item in self.source_observations
        ):
            raise ValueError("contradiction artifact crossed exact product scope")
        expected_alert_count = sum(item.disposition == "alert" for item in self.decisions)
        if self.emitted_alert_count != expected_alert_count:
            raise ValueError("contradiction artifact alert count differs from exact decisions")
        _derive_identity(
            self,
            prefix="contradiction_attention_artifact",
            id_field="artifact_id",
            digest_field="artifact_digest",
        )
        return self


class ContradictionAttentionAssessmentV1Alpha1(_FrozenModel):
    """Independent comparison of one exact decision with frozen World policy."""

    contract: Literal["ace.world-intelligence.contradiction-attention-assessment/v1alpha1"] = (
        "ace.world-intelligence.contradiction-attention-assessment/v1alpha1"
    )
    candidate_id: str
    statement: str
    expected_disposition: Literal["alert", "silence"]
    actual_disposition: Literal["alert", "silence"]
    confusion: Literal["true_positive", "false_negative", "false_positive", "true_negative"]
    rationale: str
    assessment_id: str | None = None
    assessment_digest: str | None = None

    @model_validator(mode="after")
    def validate_confusion_and_derive_identity(self) -> Self:
        expected = {
            ("alert", "alert"): "true_positive",
            ("alert", "silence"): "false_negative",
            ("silence", "alert"): "false_positive",
            ("silence", "silence"): "true_negative",
        }[(self.expected_disposition, self.actual_disposition)]
        if self.confusion != expected:
            raise ValueError("contradiction assessment confusion label is inconsistent")
        _derive_identity(
            self,
            prefix="contradiction_attention_assessment",
            id_field="assessment_id",
            digest_field="assessment_digest",
        )
        return self


class ContradictionAttentionReviewV1Alpha1(_FrozenModel):
    """Exact independent review later named by a Core Outcome."""

    contract: Literal["ace.world-intelligence.contradiction-attention-review/v1alpha1"] = (
        "ace.world-intelligence.contradiction-attention-review/v1alpha1"
    )
    product_id: str
    review_key: str
    reviewed_subject: ImmutableRecordReferenceV1
    source_brief: ImmutableRecordReferenceV1
    source_observations: tuple[ImmutableRecordReferenceV1, ...] = Field(min_length=2, max_length=2)
    reviewer_context: AuthenticatedRuntimeContextV1Alpha1
    policy_id: str
    policy_version: str
    policy_digest: str
    assessments: tuple[ContradictionAttentionAssessmentV1Alpha1, ...] = Field(min_length=2, max_length=2)
    emitted_alert_count: int = Field(ge=0, le=2)
    true_positive_count: int = Field(ge=0, le=2)
    false_negative_count: int = Field(ge=0, le=2)
    false_positive_count: int = Field(ge=0, le=2)
    true_negative_count: int = Field(ge=0, le=2)
    contradiction_recall: float = Field(ge=0.0, le=1.0)
    false_alert_rate: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    valid_silence_count: int = Field(ge=0, le=2)
    limitations: tuple[str, ...]
    reviewed_at: datetime
    review_id: str | None = None
    review_digest: str | None = None

    @field_validator("source_observations")
    @classmethod
    def canonicalize_observations(
        cls, value: tuple[ImmutableRecordReferenceV1, ...]
    ) -> tuple[ImmutableRecordReferenceV1, ...]:
        ordered = tuple(sorted(value, key=lambda item: item.storage_id))
        if len({item.storage_id for item in ordered}) != len(ordered):
            raise ValueError("contradiction review duplicated an Observation identity")
        return ordered

    @field_validator("assessments")
    @classmethod
    def canonicalize_assessments(
        cls, value: tuple[ContradictionAttentionAssessmentV1Alpha1, ...]
    ) -> tuple[ContradictionAttentionAssessmentV1Alpha1, ...]:
        ordered = tuple(sorted(value, key=lambda item: item.candidate_id))
        if len({item.candidate_id for item in ordered}) != len(ordered):
            raise ValueError("contradiction review duplicated a candidate identity")
        return ordered

    @model_validator(mode="after")
    def validate_scope_metrics_and_identity(self) -> Self:
        if (
            self.reviewed_subject.product_id != self.product_id
            or self.source_brief.product_id != self.product_id
            or self.reviewer_context.product_id != self.product_id
            or any(item.product_id != self.product_id for item in self.source_observations)
        ):
            raise ValueError("contradiction review crossed exact product scope")
        counts = {
            name: sum(item.confusion == name for item in self.assessments)
            for name in ("true_positive", "false_negative", "false_positive", "true_negative")
        }
        supplied = {
            "true_positive": self.true_positive_count,
            "false_negative": self.false_negative_count,
            "false_positive": self.false_positive_count,
            "true_negative": self.true_negative_count,
        }
        if counts != supplied:
            raise ValueError("contradiction review counts differ from exact assessments")
        actual_alerts = counts["true_positive"] + counts["false_positive"]
        if self.emitted_alert_count != actual_alerts:
            raise ValueError("contradiction review alert count differs from exact assessments")
        positives = counts["true_positive"] + counts["false_negative"]
        negatives = counts["false_positive"] + counts["true_negative"]
        recall = counts["true_positive"] / positives if positives else 0.0
        false_alert_rate = counts["false_positive"] / negatives if negatives else 0.0
        quality = (recall + (1.0 - false_alert_rate)) / 2.0
        if self.contradiction_recall != recall:
            raise ValueError("contradiction recall differs from exact assessments")
        if self.false_alert_rate != false_alert_rate:
            raise ValueError("false-alert rate differs from exact assessments")
        if self.quality_score != quality:
            raise ValueError("contradiction quality score differs from frozen product rule")
        if self.valid_silence_count != counts["true_negative"]:
            raise ValueError("valid-silence count differs from exact assessments")
        _derive_identity(
            self,
            prefix="contradiction_attention_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(
            f"historical contradiction evaluation requested new authority: {request.authorization_key}"
        )


def _candidate_id(
    *,
    candidate_kind: str,
    statement: str,
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
) -> str:
    digest = canonical_hash(
        {
            "candidate_kind": candidate_kind,
            "statement": statement,
            "source_observations": [item.model_dump(mode="json") for item in observation_refs],
        }
    )
    return f"contradiction_candidate:{digest[:32]}"


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 70)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-contradiction-attention",
        71,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-contradiction-attention",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(product_id, "capability_state", capability_state_ref_for_artifact(IMPACT_ARTIFACT), 72)
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 73)
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return criterion_head, binding


def _policy_digest(
    *,
    source_brief: ImmutableRecordReferenceV1,
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
    expected_dispositions: dict[str, str],
    statements: dict[str, str],
) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "source_brief": source_brief.model_dump(mode="json"),
            "source_observations": [item.model_dump(mode="json") for item in observation_refs],
            "expected_dispositions": dict(sorted(expected_dispositions.items())),
            "statements": dict(sorted(statements.items())),
            "score": "(contradiction_recall + (1 - false_alert_rate)) / 2",
        }
    )


async def _append_attention_artifact(
    state: dict[str, Any],
    *,
    source_brief: ImmutableRecordReferenceV1,
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
    decisions: tuple[ContradictionAttentionDecisionV1Alpha1, ...],
    variant: str,
) -> tuple[ContradictionAttentionArtifactV1Alpha1, ImmutableRecordReferenceV1, str]:
    environment = state["environment"]
    generated_at = state["clock"]()
    artifact = ContradictionAttentionArtifactV1Alpha1(
        product_id=environment.fixture["product_id"],
        artifact_key=f"contradiction-attention:{variant}:2026-08-07",
        source_brief=source_brief,
        source_observations=observation_refs,
        decisions=decisions,
        emitted_alert_count=sum(item.disposition == "alert" for item in decisions),
        limitations=(
            "bounded_to_one_contradiction_and_one_valid_comparator",
            "recorded_official_sources_not_network_freshness",
            "challenge_response_not_population_alert_performance",
        ),
        generated_at=generated_at,
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-contradiction-attention:{variant}",
        subject_ref=str(artifact.artifact_id),
        subject_digest=str(artifact.artifact_digest),
        requested_at=generated_at,
    )
    reference = await _append_value(
        state,
        value=artifact,
        record_kind="contradiction_attention_artifact",
        record_key=str(artifact.artifact_id),
        transaction_key=f"contradiction-attention-artifact:{artifact.artifact_id}",
        as_of=generated_at,
        authorization=authorization,
    )
    lines = [
        "# Contradiction Attention Artifact",
        "",
        f"Exact source Brief: {source_brief.storage_id}",
        f"Emitted alert count: {artifact.emitted_alert_count}",
        "",
    ]
    lines.extend(f"- {item.disposition.upper()}: {item.statement} ({item.candidate_id})" for item in artifact.decisions)
    return artifact, reference, "\n".join(lines) + "\n"


async def _load_exact_artifact(
    state: dict[str, Any], reference: ImmutableRecordReferenceV1
) -> ContradictionAttentionArtifactV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.world-intelligence.contradiction-attention-artifact/v1alpha1"
    ):
        raise AssertionError("contradiction review subject is unavailable or changed")
    return ContradictionAttentionArtifactV1Alpha1.model_validate(record.payload)


async def _review_artifact(
    state: dict[str, Any],
    *,
    subject: ImmutableRecordReferenceV1,
    source_brief: ImmutableRecordReferenceV1,
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
    expected_dispositions: dict[str, str],
    statements: dict[str, str],
    pair_index: int,
    variant: str,
) -> tuple[ContradictionAttentionReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    artifact = await _load_exact_artifact(state, subject)
    if artifact.source_brief != source_brief or artifact.source_observations != observation_refs:
        raise AssertionError("contradiction artifact lost its exact Brief or Observation provenance")
    decisions = {item.candidate_id: item for item in artifact.decisions}
    if set(decisions) != set(expected_dispositions):
        raise AssertionError("contradiction artifact did not cover the exact frozen candidate set")
    assessments: list[ContradictionAttentionAssessmentV1Alpha1] = []
    for candidate_id in sorted(expected_dispositions):
        decision = decisions[candidate_id]
        expected = expected_dispositions[candidate_id]
        if decision.statement != statements[candidate_id]:
            raise AssertionError("contradiction candidate identity was relabelled with different material")
        confusion = {
            ("alert", "alert"): "true_positive",
            ("alert", "silence"): "false_negative",
            ("silence", "alert"): "false_positive",
            ("silence", "silence"): "true_negative",
        }[(expected, decision.disposition)]
        assessments.append(
            ContradictionAttentionAssessmentV1Alpha1(
                candidate_id=candidate_id,
                statement=decision.statement,
                expected_disposition=expected,
                actual_disposition=decision.disposition,
                confusion=confusion,
                rationale=(
                    "The exact decision matches the frozen contradiction-attention policy."
                    if expected == decision.disposition
                    else "The exact decision conflicts with the frozen contradiction-attention policy."
                ),
            )
        )
    counts = {
        name: sum(item.confusion == name for item in assessments)
        for name in ("true_positive", "false_negative", "false_positive", "true_negative")
    }
    positives = counts["true_positive"] + counts["false_negative"]
    negatives = counts["false_positive"] + counts["true_negative"]
    recall = counts["true_positive"] / positives
    false_alert_rate = counts["false_positive"] / negatives
    reviewed_at = state["clock"]()
    reviewer = _context(environment.context, "principal:world-contradiction-attention-reviewer")
    review = ContradictionAttentionReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"contradiction-attention-review:{pair_index}:{variant}",
        reviewed_subject=subject,
        source_brief=source_brief,
        source_observations=observation_refs,
        reviewer_context=reviewer,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(
            source_brief=source_brief,
            observation_refs=observation_refs,
            expected_dispositions=expected_dispositions,
            statements=statements,
        ),
        assessments=tuple(assessments),
        emitted_alert_count=artifact.emitted_alert_count,
        true_positive_count=counts["true_positive"],
        false_negative_count=counts["false_negative"],
        false_positive_count=counts["false_positive"],
        true_negative_count=counts["true_negative"],
        contradiction_recall=recall,
        false_alert_rate=false_alert_rate,
        quality_score=(recall + (1.0 - false_alert_rate)) / 2.0,
        valid_silence_count=counts["true_negative"],
        limitations=artifact.limitations,
        reviewed_at=reviewed_at,
    )
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"contradiction-attention-review:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=reviewed_at,
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="contradiction_attention_review",
        record_key=str(review.review_id),
        transaction_key=f"contradiction-attention-review:{review.review_id}",
        as_of=reviewed_at,
        authorization=authorization,
    )
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: ContradictionAttentionReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.quality_score,
        observed_result=review_ref,
        latency_ms=max(0, int((review.reviewed_at - export.intent.requested_at).total_seconds() * 1_000)),
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-contradiction-outcome-observer")
    intent = OutcomeIntentV1Alpha1(
        product_id=environment.fixture["product_id"],
        authenticated_context=observer,
        decision=export.decision_ref,
        outcome_type=OUTCOME_TYPE,
        measure_id=MEASURE_ID,
        value_json=canonical_json(measures.model_dump(mode="json")),
        observed_at=review.reviewed_at,
        recorded_at=recorded_at,
    )
    authorization = await _authorize_append(
        state,
        context=observer,
        authorization_key=f"contradiction-attention-outcome:{pair_index}:{variant}",
        subject_ref=str(intent.intent_id),
        subject_digest=str(intent.intent_digest),
        requested_at=recorded_at,
    )
    outcome = OutcomeV1Alpha1(intent=intent, authorization=authorization)
    return await _append_value(
        state,
        value=outcome,
        record_kind="outcome",
        record_key=str(outcome.outcome_id),
        transaction_key=f"outcome:{outcome.outcome_id}",
        as_of=review.reviewed_at,
        authorization=authorization,
    )


async def run_contradiction_attention_outcome(
    workspace_root: Path,
    *,
    state_sink: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the recorded World journey through exact contradiction-attention Outcomes."""

    state: dict[str, Any] = {} if state_sink is None else state_sink
    prior = await run_citation_correctness_outcome(workspace_root, state_sink=state)
    environment = state["environment"]
    source_brief = state["impact_target_ref"]
    observation_refs = tuple(
        record
        for admission in state["admissions"]
        for record in admission.transaction_receipt.records
        if record.record_kind == "observation"
    )
    expected_statement, corrupted_statement = await _statements_from_observations(state, observation_refs)
    valid_id = _candidate_id(
        candidate_kind="valid_comparator",
        statement=expected_statement,
        observation_refs=observation_refs,
    )
    contradiction_id = _candidate_id(
        candidate_kind="contradiction",
        statement=corrupted_statement,
        observation_refs=observation_refs,
    )
    statements = {valid_id: expected_statement, contradiction_id: corrupted_statement}
    expected_dispositions = {valid_id: "silence", contradiction_id: "alert"}

    treatment_decisions = tuple(
        ContradictionAttentionDecisionV1Alpha1(
            candidate_id=candidate_id,
            statement=statements[candidate_id],
            disposition=expected_dispositions[candidate_id],
            rationale="Apply the exact frozen World contradiction-attention rule.",
        )
        for candidate_id in sorted(statements)
    )
    control_decisions = tuple(
        ContradictionAttentionDecisionV1Alpha1(
            candidate_id=candidate_id,
            statement=statements[candidate_id],
            disposition="silence" if expected_dispositions[candidate_id] == "alert" else "alert",
            rationale="Deterministic inverted-routing negative control with equal alert volume.",
        )
        for candidate_id in sorted(statements)
    )
    treatment_artifact, treatment_ref, treatment_content = await _append_attention_artifact(
        state,
        source_brief=source_brief,
        observation_refs=observation_refs,
        decisions=treatment_decisions,
        variant="treatment",
    )
    control_artifact, control_ref, control_content = await _append_attention_artifact(
        state,
        source_brief=source_brief,
        observation_refs=observation_refs,
        decisions=control_decisions,
        variant="inverted-control",
    )
    treatment_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=treatment_ref,
                content=treatment_content,
                pair_index=index,
                variant="contradiction-treatment",
            )
            for index in (1, 2)
        ]
    )
    control_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=control_ref,
                content=control_content,
                pair_index=index,
                variant="contradiction-control",
            )
            for index in (1, 2)
        ]
    )
    criterion_head, impact_binding = _install_policy(state)
    criterion = ImpactCriterionV1Alpha1(
        product_id=environment.fixture["product_id"],
        criterion_id=CRITERION_ID,
        criterion_version="candidate-1",
        target_kind=ImpactTargetKind.INTELLIGENCE_ARTIFACT,
        outcome_type=OUTCOME_TYPE,
        measure_id=MEASURE_ID,
        metric_direction=ImpactMetricDirection.HIGHER_IS_BETTER,
        useful_effect_threshold=0.75,
        harmful_effect_threshold=0.75,
        minimum_matched_pairs=2,
        requires_observed_result=True,
        harmful_action=ImpactGovernanceAction.ROLLBACK,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(criterion_head),
        frozen_at=CRITERION_FROZEN_AT,
    )

    evidence: list[ImpactEvidenceV1Alpha1] = []
    treatment_reviews: list[ContradictionAttentionReviewV1Alpha1] = []
    control_reviews: list[ContradictionAttentionReviewV1Alpha1] = []
    observed_times: list[datetime] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=treatment_ref,
            pair_index=index,
            variant="contradiction-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="contradiction-control",
        )
        treatment_review, treatment_review_ref = await _review_artifact(
            state,
            subject=treatment_ref,
            source_brief=source_brief,
            observation_refs=observation_refs,
            expected_dispositions=expected_dispositions,
            statements=statements,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_artifact(
            state,
            subject=control_ref,
            source_brief=source_brief,
            observation_refs=observation_refs,
            expected_dispositions=expected_dispositions,
            statements=statements,
            pair_index=index,
            variant="control",
        )
        treatment_outcome = await _record_review_outcome(
            state,
            export=treatment_export,
            review=treatment_review,
            review_ref=treatment_review_ref,
            pair_index=index,
            variant="treatment",
        )
        control_outcome = await _record_review_outcome(
            state,
            export=control_export,
            review=control_review,
            review_ref=control_review_ref,
            pair_index=index,
            variant="control",
        )
        treatment_reviews.append(treatment_review)
        control_reviews.append(control_review)
        observed_times.extend((treatment_review.reviewed_at, control_review.reviewed_at))
        conditions = ImpactConditionsV1Alpha1(
            product_id=environment.fixture["product_id"],
            condition_key=f"world-contradiction-attention-pair:{index}",
            route_id="world:fcc-contradiction-attention-review",
            context_json=canonical_json(
                {
                    "alert_budget": 1,
                    "candidate_count": 2,
                    "pair_index": index,
                    "recorded_transport": True,
                    "review_policy_digest": treatment_review.policy_digest,
                    "task": "exact_contradiction_attention_with_valid_silence",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT + timedelta(seconds=1),
            observation_window_end=max(observed_times) + timedelta(minutes=1),
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-contradiction-attention:{index}",
                treatment_attribution=treatment_attribution,
                control_attribution=control_attribution,
                treatment_decision=treatment_export.decision_ref,
                control_decision=control_export.decision_ref,
                treatment_action_review=treatment_export.review_ref,
                treatment_action_admission=treatment_export.admission_ref,
                treatment_action_terminal=treatment_export.terminal_ref,
                control_action_review=control_export.review_ref,
                control_action_admission=control_export.admission_ref,
                control_action_terminal=control_export.terminal_ref,
                treatment_outcome=treatment_outcome,
                control_outcome=control_outcome,
                treatment_conditions=conditions,
                control_conditions=conditions,
            )
        )

    request = ImpactEvaluationRequestV1Alpha1(
        evaluation_key="world-contradiction-attention:fcc-publication-change:2026-08-07",
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        criterion=criterion,
        target=treatment_ref,
        control=control_ref,
        evidence=tuple(evidence),
        cutoff_at=state["clock"](),
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
    if admission.replayed or not replay.replayed or replay.evaluation != admission.evaluation:
        raise AssertionError("contradiction evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen contradiction-attention criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("contradiction result did not emit its proposal-only mapping")
    if treatment_artifact.emitted_alert_count != control_artifact.emitted_alert_count:
        raise AssertionError("contradiction control changed raw alert volume")
    if {item.contradiction_recall for item in treatment_reviews} != {1.0}:
        raise AssertionError("treatment did not recall the exact contradiction")
    if {item.false_alert_rate for item in treatment_reviews} != {0.0}:
        raise AssertionError("treatment emitted an alert for the valid comparator")
    if {item.valid_silence_count for item in treatment_reviews} != {1}:
        raise AssertionError("treatment did not preserve silence for the valid comparator")
    if {item.quality_score for item in control_reviews} != {0.0}:
        raise AssertionError("inverted control unexpectedly satisfied the frozen product rule")

    return {
        "contract": "ace.world-intelligence.contradiction-attention-outcome/v1alpha1",
        "prior_citation_correctness": prior,
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "score": "(contradiction_recall + (1 - false_alert_rate)) / 2",
        },
        "challenge": {
            "candidate_ids": tuple(sorted(statements)),
            "contradiction_candidate_id": contradiction_id,
            "valid_comparator_id": valid_id,
            "contradictory_statement": corrupted_statement,
            "valid_statement": expected_statement,
            "treatment_alert_volume": treatment_artifact.emitted_alert_count,
            "control_alert_volume": control_artifact.emitted_alert_count,
        },
        "artifacts": {
            "treatment": treatment_artifact.model_dump(mode="json"),
            "control": control_artifact.model_dump(mode="json"),
        },
        "observed_results": {
            "treatment": tuple(item.model_dump(mode="json") for item in treatment_reviews),
            "control": tuple(item.model_dump(mode="json") for item in control_reviews),
        },
        "evaluation": admission.evaluation.model_dump(mode="json"),
        "proposal": admission.proposal.model_dump(mode="json"),
        "replay": {
            "historical": replay.replayed,
            "no_reauthorization": True,
            "transaction_receipt_id": str(replay.transaction_receipt.receipt_id),
        },
        "scope": {
            "exact_brief_and_observation_provenance": True,
            "equal_alert_volume_control": True,
            "valid_silence_measured": True,
            "recorded_official_sources": True,
            "network_freshness_claimed": False,
            "live_public_conflict_claimed": False,
            "population_false_alert_rate_claimed": False,
            "general_brief_quality_claimed": False,
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
            asyncio.run(run_contradiction_attention_outcome(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
