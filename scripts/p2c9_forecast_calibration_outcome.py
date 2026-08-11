"""Measure one withheld-result probabilistic forecast under a World-owned rule."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
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
    ObservationV1Alpha1,
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
from scripts.p2c5_citation_correctness_outcome import _derive_identity, _FrozenModel
from scripts.p2c7_correction_detection_delay_outcome import (
    _load_observation,
    correction_fixture_digest,
)
from scripts.p2c8_correction_revision_stability_outcome import (
    run_correction_revision_stability_outcome,
)

OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "recorded_binary_forecast_brier_quality"
CRITERION_ID = "impact_criterion:world-recorded-binary-forecast-brier-quality"
REVIEW_POLICY_ID = "world_recorded_binary_forecast_brier_quality"
REVIEW_POLICY_VERSION = "candidate-1"

RESOLUTION_WINDOW_END = _time("2026-08-11T19:00:00Z")

TARGET_EVENT_KEY = "recorded-replay:explicit-correction:2020-28779"
TARGET_EVENT_DEFINITION = canonical_json(
    {
        "basis_document_number": "2020-28779",
        "event_type": "later_admitted_source_explicitly_corrects_basis_document",
        "resolution_rule": ("true only when a later exact admitted source names the basis document as corrected"),
        "source_family": "federal_register",
        "withheld_result_policy": "forecast material contains no outcome identity or outcome material",
    }
)

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_recorded_binary_forecast_brier_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "c" * 64,
)


class PublicEventForecastV1Alpha1(_FrozenModel):
    """One World-owned probability issued before an exact result is available."""

    contract: Literal["ace.world-intelligence.public-event-forecast/v1alpha1"] = (
        "ace.world-intelligence.public-event-forecast/v1alpha1"
    )
    product_id: str
    forecast_key: str
    basis_observations: tuple[ImmutableRecordReferenceV1, ...] = Field(min_length=1, max_length=16)
    target_event_key: str
    target_event_definition_json: str
    probability: float = Field(ge=0.0, le=1.0)
    policy_id: str
    policy_version: str
    policy_digest: str
    issued_at: datetime
    resolution_window_start: datetime
    resolution_window_end: datetime
    limitations: tuple[str, ...]
    forecast_id: str | None = None
    forecast_digest: str | None = None

    @field_validator("basis_observations")
    @classmethod
    def canonicalize_basis(
        cls, value: tuple[ImmutableRecordReferenceV1, ...]
    ) -> tuple[ImmutableRecordReferenceV1, ...]:
        ordered = tuple(sorted(value, key=lambda item: item.storage_id))
        if len({item.storage_id for item in ordered}) != len(ordered):
            raise ValueError("forecast basis cannot amplify duplicate exact records")
        return ordered

    @field_validator("target_event_definition_json")
    @classmethod
    def validate_target_definition(cls, value: str) -> str:
        try:
            material = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("forecast target definition must be canonical JSON") from exc
        if canonical_json(material) != value or material != json.loads(TARGET_EVENT_DEFINITION):
            raise ValueError("forecast target definition differs from the frozen World event rule")
        return value

    @field_validator("limitations")
    @classmethod
    def canonicalize_limitations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        ordered = tuple(sorted(value))
        if not ordered or len(ordered) != len(set(ordered)):
            raise ValueError("forecast limitations must be non-empty and unique")
        return ordered

    @model_validator(mode="after")
    def validate_scope_time_and_identity(self) -> Self:
        if any(item.product_id != self.product_id for item in self.basis_observations):
            raise ValueError("forecast basis crossed exact product scope")
        if any(item.available_at > self.issued_at for item in self.basis_observations):
            raise ValueError("forecast basis includes evidence unavailable when the forecast was issued")
        if not self.issued_at <= self.resolution_window_start < self.resolution_window_end:
            raise ValueError("forecast resolution window must begin at or after issuance")
        if self.target_event_key != TARGET_EVENT_KEY:
            raise ValueError("forecast target key differs from the frozen World event")
        _derive_identity(
            self,
            prefix="public_event_forecast",
            id_field="forecast_id",
            digest_field="forecast_digest",
        )
        return self


class ForecastResolutionReviewV1Alpha1(_FrozenModel):
    """Exact product-owned resolution and single-event Brier contribution."""

    contract: Literal["ace.world-intelligence.forecast-resolution-review/v1alpha1"] = (
        "ace.world-intelligence.forecast-resolution-review/v1alpha1"
    )
    product_id: str
    review_key: str
    reviewed_forecast: ImmutableRecordReferenceV1
    basis_observation: ImmutableRecordReferenceV1
    observed_result: ImmutableRecordReferenceV1
    reviewer_context: AuthenticatedRuntimeContextV1Alpha1
    policy_id: str
    policy_version: str
    policy_digest: str
    source_fixture_digest: str
    target_event_key: str
    target_event_definition_json: str
    forecast_issued_at: datetime
    resolution_window_start: datetime
    resolution_window_end: datetime
    forecast_probability: float = Field(ge=0.0, le=1.0)
    result_withheld_until_after_forecast: bool
    explicit_correction_linkage_verified: bool
    event_outcome: float = Field(ge=0.0, le=1.0)
    brier_loss: float = Field(ge=0.0, le=1.0)
    brier_quality_score: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...]
    reviewed_at: datetime
    review_id: str | None = None
    review_digest: str | None = None

    @field_validator("target_event_definition_json")
    @classmethod
    def validate_target_definition(cls, value: str) -> str:
        if value != TARGET_EVENT_DEFINITION:
            raise ValueError("forecast review changed the frozen target event definition")
        return value

    @field_validator("limitations")
    @classmethod
    def canonicalize_limitations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        ordered = tuple(sorted(value))
        if not ordered or len(ordered) != len(set(ordered)):
            raise ValueError("forecast review limitations must be non-empty and unique")
        return ordered

    @model_validator(mode="after")
    def validate_scope_resolution_score_and_identity(self) -> Self:
        references = (self.reviewed_forecast, self.basis_observation, self.observed_result)
        if any(item.product_id != self.product_id for item in references):
            raise ValueError("forecast resolution review crossed exact product scope")
        if self.reviewed_forecast.storage_id in {
            self.basis_observation.storage_id,
            self.observed_result.storage_id,
        }:
            raise ValueError("forecast, basis, and observed result require distinct exact records")
        withheld = self.observed_result.available_at > self.reviewed_forecast.available_at
        if self.result_withheld_until_after_forecast != withheld or not withheld:
            raise ValueError("forecast result was not withheld until after exact forecast availability")
        if not (
            self.forecast_issued_at
            <= self.resolution_window_start
            <= self.observed_result.available_at
            <= self.reviewed_at
            <= self.resolution_window_end
        ):
            raise ValueError("forecast resolution escaped its declared time window")
        if self.target_event_key != TARGET_EVENT_KEY:
            raise ValueError("forecast review changed the frozen target event")
        expected_outcome = float(self.explicit_correction_linkage_verified)
        if self.event_outcome != expected_outcome:
            raise ValueError("forecast outcome differs from exact correction linkage")
        expected_loss = (self.forecast_probability - self.event_outcome) ** 2
        expected_score = 1.0 - expected_loss
        if self.brier_loss != expected_loss or self.brier_quality_score != expected_score:
            raise ValueError("forecast Brier material differs from the frozen product formula")
        _derive_identity(
            self,
            prefix="forecast_resolution_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(f"historical forecast evaluation requested new authority: {request.authorization_key}")


def _policy_digest(original_ref: ImmutableRecordReferenceV1, *, issued_at: datetime) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "basis_observation": original_ref.model_dump(mode="json"),
            "target_event_key": TARGET_EVENT_KEY,
            "target_event_definition_json": TARGET_EVENT_DEFINITION,
            "resolution_window_start": issued_at.isoformat(),
            "resolution_window_end": RESOLUTION_WINDOW_END.isoformat(),
            "score": "1 - (forecast_probability - binary_event_outcome) ** 2",
            "claim_boundary": "single-event Brier contribution, not population calibration",
        }
    )


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 100)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-recorded-binary-forecast-brier-quality",
        101,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-recorded-binary-forecast-brier-quality",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(
        product_id,
        "capability_state",
        capability_state_ref_for_artifact(IMPACT_ARTIFACT),
        102,
    )
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 103)
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return criterion_head, binding


async def _append_forecast(
    state: dict[str, Any],
    *,
    original_ref: ImmutableRecordReferenceV1,
    variant: Literal["treatment", "control"],
    probability: float,
    issued_at: datetime,
) -> tuple[PublicEventForecastV1Alpha1, ImmutableRecordReferenceV1, str]:
    environment = state["environment"]
    forecast = PublicEventForecastV1Alpha1(
        product_id=environment.fixture["product_id"],
        forecast_key=f"recorded-binary-forecast:{variant}:2020-28779",
        basis_observations=(original_ref,),
        target_event_key=TARGET_EVENT_KEY,
        target_event_definition_json=TARGET_EVENT_DEFINITION,
        probability=probability,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(original_ref, issued_at=issued_at),
        issued_at=issued_at,
        resolution_window_start=issued_at,
        resolution_window_end=RESOLUTION_WINDOW_END,
        limitations=(
            "declared_fixture_probability_not_generated_by_ace",
            "offline_recorded_replay_not_live_forecasting",
            "single_event_brier_contribution_not_population_calibration",
        ),
    )
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-recorded-binary-forecast:{variant}",
        subject_ref=str(forecast.forecast_id),
        subject_digest=str(forecast.forecast_digest),
        requested_at=requested_at,
    )
    reference = await _append_value(
        state,
        value=forecast,
        record_kind="public_event_forecast",
        record_key=str(forecast.forecast_id),
        transaction_key=f"public-event-forecast:{forecast.forecast_id}",
        as_of=forecast.issued_at,
        authorization=authorization,
    )
    content = (
        "# Recorded Binary Public-Event Forecast\n\n"
        f"Basis Observation: {original_ref.storage_id}\n\n"
        f"Target: {forecast.target_event_key}\n\n"
        f"Declared probability: {forecast.probability}\n\n"
        "The exact outcome identity and outcome material are withheld from this forecast record.\n"
    )
    return forecast, reference, content


async def _issue_forecasts_before_correction(
    state: dict[str, Any],
    _fixture: dict[str, Any],
    original: ObservationV1Alpha1,
    original_ref: ImmutableRecordReferenceV1,
) -> None:
    original_payload = original.payload.parsed_value()["record"]
    if original_payload["document_number"] != "2020-28779":
        raise AssertionError("forecast basis changed its exact original public record")
    criterion_head, impact_binding = _install_policy(state)
    issued_at = state["clock"]()
    treatment, treatment_ref, treatment_content = await _append_forecast(
        state,
        original_ref=original_ref,
        variant="treatment",
        probability=0.75,
        issued_at=issued_at,
    )
    control, control_ref, control_content = await _append_forecast(
        state,
        original_ref=original_ref,
        variant="control",
        probability=0.25,
        issued_at=issued_at,
    )
    treatment_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=treatment_ref,
                content=treatment_content,
                pair_index=index,
                variant="forecast-calibration-treatment",
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
                variant="forecast-calibration-control",
            )
            for index in (1, 2)
        ]
    )
    state.update(
        {
            "p2c9_criterion_head": criterion_head,
            "p2c9_criterion_frozen_at": issued_at,
            "p2c9_forecast_issued_at": issued_at,
            "p2c9_impact_binding": impact_binding,
            "p2c9_treatment_forecast": treatment,
            "p2c9_treatment_forecast_ref": treatment_ref,
            "p2c9_control_forecast": control,
            "p2c9_control_forecast_ref": control_ref,
            "p2c9_treatment_exports": treatment_exports,
            "p2c9_control_exports": control_exports,
        }
    )


async def _load_forecast(state: dict[str, Any], reference: ImmutableRecordReferenceV1) -> PublicEventForecastV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.world-intelligence.public-event-forecast/v1alpha1"
    ):
        raise AssertionError("recorded forecast is unavailable or changed")
    return PublicEventForecastV1Alpha1.model_validate(record.payload)


async def _review_forecast(
    state: dict[str, Any],
    *,
    forecast_ref: ImmutableRecordReferenceV1,
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: Literal["treatment", "control"],
) -> tuple[ForecastResolutionReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    forecast = await _load_forecast(state, forecast_ref)
    original = await _load_observation(state, original_ref)
    correction = await _load_observation(state, correction_ref)
    original_payload = original.payload.parsed_value()["record"]
    correction_payload = correction.payload.parsed_value()["record"]
    linkage_verified = bool(
        correction_payload["corrects_document_number"] == original_payload["document_number"]
        and correction_payload["document_number"] == "2021-10670"
        and forecast.basis_observations == (original_ref,)
        and forecast.target_event_key == TARGET_EVENT_KEY
    )
    event_outcome = float(linkage_verified)
    brier_loss = (forecast.probability - event_outcome) ** 2
    reviewed_at = state["clock"]()
    reviewer = _context(environment.context, "principal:world-forecast-calibration-reviewer")
    review = ForecastResolutionReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"recorded-binary-forecast-resolution:{pair_index}:{variant}",
        reviewed_forecast=forecast_ref,
        basis_observation=original_ref,
        observed_result=correction_ref,
        reviewer_context=reviewer,
        policy_id=forecast.policy_id,
        policy_version=forecast.policy_version,
        policy_digest=forecast.policy_digest,
        source_fixture_digest=correction_fixture_digest(state["p2c7_fixture"]),
        target_event_key=forecast.target_event_key,
        target_event_definition_json=forecast.target_event_definition_json,
        forecast_issued_at=forecast.issued_at,
        resolution_window_start=forecast.resolution_window_start,
        resolution_window_end=forecast.resolution_window_end,
        forecast_probability=forecast.probability,
        result_withheld_until_after_forecast=correction_ref.available_at > forecast_ref.available_at,
        explicit_correction_linkage_verified=linkage_verified,
        event_outcome=event_outcome,
        brier_loss=brier_loss,
        brier_quality_score=1.0 - brier_loss,
        limitations=forecast.limitations,
        reviewed_at=reviewed_at,
    )
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"recorded-binary-forecast-resolution:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=requested_at,
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="forecast_resolution_review",
        record_key=str(review.review_id),
        transaction_key=f"forecast-resolution-review:{review.review_id}",
        as_of=review.reviewed_at,
        authorization=authorization,
    )
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: ForecastResolutionReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: Literal["treatment", "control"],
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    latency_ms = int((review.reviewed_at - review.forecast_issued_at).total_seconds() * 1_000)
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.brier_quality_score,
        observed_result=review_ref,
        latency_ms=latency_ms,
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-forecast-calibration-outcome-observer")
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
        authorization_key=f"recorded-binary-forecast-outcome:{pair_index}:{variant}",
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


async def run_forecast_calibration_outcome(workspace_root: Path) -> dict[str, Any]:
    """Run P2C9 over a withheld exact correction result and declared probabilities."""

    state: dict[str, Any] = {}
    prior_packet = await run_correction_revision_stability_outcome(
        workspace_root,
        state_sink=state,
        before_correction=_issue_forecasts_before_correction,
    )
    environment = state["environment"]
    original_ref = state["p2c7_original_observation_ref"]
    correction_ref = state["p2c7_correction_observation_ref"]
    treatment_ref = state["p2c9_treatment_forecast_ref"]
    control_ref = state["p2c9_control_forecast_ref"]
    treatment_exports = state["p2c9_treatment_exports"]
    control_exports = state["p2c9_control_exports"]
    if correction_ref.available_at <= max(treatment_ref.available_at, control_ref.available_at):
        raise AssertionError("held-out correction became available before the exact forecasts")
    latest_forecast_action_completed_at = max(
        *(item.terminal.result.completed_at for item in treatment_exports),
        *(item.terminal.result.completed_at for item in control_exports),
    )
    if correction_ref.available_at <= latest_forecast_action_completed_at:
        raise AssertionError("held-out correction became available before the reviewed forecast actions completed")

    evidence: list[ImpactEvidenceV1Alpha1] = []
    treatment_reviews: list[ForecastResolutionReviewV1Alpha1] = []
    control_reviews: list[ForecastResolutionReviewV1Alpha1] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=treatment_ref,
            pair_index=index,
            variant="forecast-calibration-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="forecast-calibration-control",
        )
        treatment_review, treatment_review_ref = await _review_forecast(
            state,
            forecast_ref=treatment_ref,
            original_ref=original_ref,
            correction_ref=correction_ref,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_forecast(
            state,
            forecast_ref=control_ref,
            original_ref=original_ref,
            correction_ref=correction_ref,
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
        conditions = ImpactConditionsV1Alpha1(
            product_id=environment.fixture["product_id"],
            condition_key=f"world-recorded-binary-forecast-brier-pair:{index}",
            route_id="world:fcc-recorded-binary-forecast-review",
            context_json=canonical_json(
                {
                    "basis_observation": original_ref.model_dump(mode="json"),
                    "pair_index": index,
                    "review_policy_digest": treatment_review.policy_digest,
                    "target_event_definition_json": TARGET_EVENT_DEFINITION,
                    "target_event_key": TARGET_EVENT_KEY,
                    "task": "score_declared_probability_after_exact_withheld_result",
                    "withheld_result_policy": "no outcome coordinate in frozen conditions",
                }
            ),
            observation_window_start=state["p2c9_forecast_issued_at"],
            observation_window_end=RESOLUTION_WINDOW_END,
            frozen_at=state["p2c9_criterion_frozen_at"],
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-recorded-binary-forecast-brier:{index}",
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
        requires_observed_result=True,
        harmful_action=ImpactGovernanceAction.ROLLBACK,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(state["p2c9_criterion_head"]),
        frozen_at=state["p2c9_criterion_frozen_at"],
    )
    request = ImpactEvaluationRequestV1Alpha1(
        evaluation_key="world-recorded-binary-forecast-brier:fcc-2021-10670",
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
        operation_binding=state["p2c9_impact_binding"],
    )
    admission = await service.evaluate(request)
    historical = await MeasuredImpactService(
        store=environment.store,
        authorizer=_ReplayMustNotAuthorize(),
        operation_binding=state["p2c9_impact_binding"],
    ).evaluate(request)
    if admission.replayed or not historical.replayed or historical.evaluation != admission.evaluation:
        raise AssertionError("forecast evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen forecast Brier criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("forecast evaluation did not emit its proposal-only mapping")
    if {item.brier_quality_score for item in treatment_reviews} != {0.9375}:
        raise AssertionError("treatment forecast lost its exact Brier contribution")
    if {item.brier_quality_score for item in control_reviews} != {0.4375}:
        raise AssertionError("control forecast lost its exact Brier contribution")

    return {
        "contract": "ace.world-intelligence.forecast-calibration-outcome/v1alpha1",
        "prior_revision_stability": prior_packet,
        "source_event": {
            "fixture_id": state["p2c7_fixture"]["fixture_id"],
            "fixture_digest": correction_fixture_digest(state["p2c7_fixture"]),
            "original_observation": original_ref.model_dump(mode="json"),
            "observed_result": correction_ref.model_dump(mode="json"),
            "result_available_after_forecasts": True,
            "latest_forecast_action_completed_at": latest_forecast_action_completed_at.isoformat(),
            "result_available_after_reviewed_actions": True,
        },
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "score_rule": "1 - (forecast_probability - binary_event_outcome) ** 2",
            "claim_boundary": "single-event Brier contribution, not population calibration",
        },
        "forecasts": {
            "treatment": state["p2c9_treatment_forecast"].model_dump(mode="json"),
            "control": state["p2c9_control_forecast"].model_dump(mode="json"),
        },
        "observed_results": {
            "treatment": tuple(item.model_dump(mode="json") for item in treatment_reviews),
            "control": tuple(item.model_dump(mode="json") for item in control_reviews),
        },
        "evaluation": admission.evaluation.model_dump(mode="json"),
        "proposal": admission.proposal.model_dump(mode="json"),
        "replay": {
            "historical": historical.replayed,
            "no_reauthorization": True,
            "transaction_receipt_id": str(historical.transaction_receipt.receipt_id),
        },
        "scope": {
            "exact_real_correction_result": True,
            "result_withheld_until_after_forecast_records": True,
            "exact_probability_and_result_scoring": True,
            "network_access": False,
            "historically_contemporaneous_forecast_claimed": False,
            "probability_generated_by_ace_claimed": False,
            "model_forecast_skill_claimed": False,
            "population_calibration_claimed": False,
            "causality_claimed": False,
            "human_benefit_claimed": False,
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
            asyncio.run(run_forecast_calibration_outcome(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
