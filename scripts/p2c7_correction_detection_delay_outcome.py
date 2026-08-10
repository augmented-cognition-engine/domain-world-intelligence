"""Measure recorded-replay correction handling and detection delay."""

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
    canonical_hash,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    CanonicalJsonValueV1Alpha1,
    EvidenceAcquisitionMode,
    ImpactClassification,
    ImpactConditionsV1Alpha1,
    ImpactCriterionV1Alpha1,
    ImpactEvaluationRequestV1Alpha1,
    ImpactEvidenceV1Alpha1,
    ImpactGovernanceAction,
    ImpactMetricDirection,
    ImpactOutcomeMeasuresV1Alpha1,
    ImpactTargetKind,
    IntelligenceResourceMode,
    ObservationV1Alpha1,
)
from pydantic import Field, model_validator

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
from scripts.p2c6_contradiction_attention_outcome import run_contradiction_attention_outcome

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "domain_packs" / "tests" / "fixtures" / "p2c7_fcc_correction_pair.json"
)
OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "recorded_correction_detection_timeliness"
CRITERION_ID = "impact_criterion:world-recorded-correction-detection-timeliness"
CRITERION_FROZEN_AT = _time("2026-08-10T23:09:00Z")
REVIEW_POLICY_ID = "world_recorded_official_correction_detection"
REVIEW_POLICY_VERSION = "candidate-1"

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_recorded_correction_delay_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "a" * 64,
)


class CorrectionHandlingArtifactV1Alpha1(_FrozenModel):
    """One exact correction link and its recorded-replay detection time."""

    contract: Literal["ace.world-intelligence.correction-handling-artifact/v1alpha1"] = (
        "ace.world-intelligence.correction-handling-artifact/v1alpha1"
    )
    product_id: str
    artifact_key: str
    original_observation: ImmutableRecordReferenceV1
    correction_observation: ImmutableRecordReferenceV1
    correction_relation: Literal["corrects"] = "corrects"
    correction_document_number: str
    corrects_document_number: str
    corrected_instruction: str
    correction_available_at: datetime
    detected_at: datetime
    detection_delay_seconds: int = Field(ge=0)
    prior_record_preserved: Literal[True] = True
    limitations: tuple[str, ...]
    generated_at: datetime
    artifact_id: str | None = None
    artifact_digest: str | None = None

    @model_validator(mode="after")
    def validate_scope_delay_and_identity(self) -> Self:
        if (
            self.original_observation.product_id != self.product_id
            or self.correction_observation.product_id != self.product_id
        ):
            raise ValueError("correction artifact crossed exact product scope")
        if self.original_observation.storage_id == self.correction_observation.storage_id:
            raise ValueError("correction artifact requires distinct original and correction records")
        if self.detected_at < self.correction_available_at:
            raise ValueError("correction detection cannot precede correction availability")
        expected_delay = int((self.detected_at - self.correction_available_at).total_seconds())
        if self.detection_delay_seconds != expected_delay:
            raise ValueError("correction delay differs from exact event times")
        _derive_identity(
            self,
            prefix="correction_handling_artifact",
            id_field="artifact_id",
            digest_field="artifact_digest",
        )
        return self


class CorrectionDetectionReviewV1Alpha1(_FrozenModel):
    """Product-owned correction and timeliness review named by a Core Outcome."""

    contract: Literal["ace.world-intelligence.correction-detection-review/v1alpha1"] = (
        "ace.world-intelligence.correction-detection-review/v1alpha1"
    )
    product_id: str
    review_key: str
    reviewed_subject: ImmutableRecordReferenceV1
    original_observation: ImmutableRecordReferenceV1
    correction_observation: ImmutableRecordReferenceV1
    reviewer_context: AuthenticatedRuntimeContextV1Alpha1
    policy_id: str
    policy_version: str
    policy_digest: str
    source_fixture_digest: str
    linkage_correct: bool
    instruction_correct: bool
    prior_record_preserved: bool
    detection_delay_seconds: int = Field(ge=0)
    target_detection_delay_seconds: int = Field(gt=0)
    within_target: bool
    timeliness_score: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...]
    reviewed_at: datetime
    review_id: str | None = None
    review_digest: str | None = None

    @model_validator(mode="after")
    def validate_scope_score_and_identity(self) -> Self:
        if (
            self.reviewed_subject.product_id != self.product_id
            or self.original_observation.product_id != self.product_id
            or self.correction_observation.product_id != self.product_id
            or self.reviewer_context.product_id != self.product_id
        ):
            raise ValueError("correction review crossed exact product scope")
        if self.original_observation.storage_id == self.correction_observation.storage_id:
            raise ValueError("correction review requires distinct source records")
        within_target = self.detection_delay_seconds <= self.target_detection_delay_seconds
        if self.within_target != within_target:
            raise ValueError("correction review target disposition differs from exact delay")
        expected_score = float(
            self.linkage_correct and self.instruction_correct and self.prior_record_preserved and within_target
        )
        if self.timeliness_score != expected_score:
            raise ValueError("correction timeliness score differs from frozen product rule")
        _derive_identity(
            self,
            prefix="correction_detection_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(f"historical correction evaluation requested new authority: {request.authorization_key}")


def load_correction_fixture() -> dict[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if fixture["network_access"] is not False:
        raise AssertionError("recorded correction fixture must remain network-free")
    if fixture["source_policy"] != {
        "display_source": "FederalRegister.gov",
        "display_source_is_official_legal_edition": False,
        "official_format_source": "govinfo.gov",
        "legal_truth_claimed": False,
    }:
        raise AssertionError("recorded correction fixture changed its exact source-policy boundary")
    original = fixture["original"]
    correction = fixture["correction"]
    if correction["corrects_document_number"] != original["document_number"]:
        raise AssertionError("recorded correction no longer names the exact original document")
    if not original["official_pdf_uri"].startswith("https://www.govinfo.gov/") or not correction[
        "official_pdf_uri"
    ].startswith("https://www.govinfo.gov/"):
        raise AssertionError("recorded correction pair lost its govinfo verification references")
    return fixture


def correction_fixture_digest(fixture: dict[str, Any]) -> str:
    return f"sha256:{canonical_hash(fixture)}"


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 80)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-recorded-correction-delay",
        81,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-recorded-correction-delay",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(product_id, "capability_state", capability_state_ref_for_artifact(IMPACT_ARTIFACT), 82)
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 83)
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return criterion_head, binding


async def _append_source_observation(
    state: dict[str, Any],
    *,
    fixture: dict[str, Any],
    role: Literal["original", "correction"],
) -> tuple[ObservationV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    source = fixture[role]
    fixture_digest = correction_fixture_digest(fixture)
    published_at = _time(f"{source['publication_date']}T00:00:00Z")
    ingested_at = _time(fixture["recorded_at"])
    payload = {
        "fixture_id": fixture["fixture_id"],
        "fixture_digest": fixture_digest,
        "record_role": role,
        "source_policy": fixture["source_policy"],
        "record": source,
    }
    observation = ObservationV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=state["brief_admission"].brief.activation_revision,
        as_of=ingested_at,
        source_ref=f"federal_register_document:{source['document_number']}",
        source_digest=_digest(source),
        acquisition_mode=EvidenceAcquisitionMode.RECORDED_REPLAY,
        acquisition_receipt_ref=f"recorded_replay_acquisition:{source['document_number']}",
        acquisition_receipt_digest=_digest(
            {
                "fixture_digest": fixture_digest,
                "document_number": source["document_number"],
                "network_access": False,
            }
        ),
        source_published_at=published_at,
        event_effective_at=None,
        observed_at=published_at,
        ingested_at=ingested_at,
        subject_refs=("fcc_docket:wt-19-212",),
        payload=CanonicalJsonValueV1Alpha1(value_json=canonical_json(payload)),
        confidence=1.0,
    )
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-recorded-correction-observation:{role}",
        subject_ref=str(observation.resource_id),
        subject_digest=str(observation.resource_digest),
        requested_at=requested_at,
    )
    reference = await _append_value(
        state,
        value=observation,
        record_kind="observation",
        record_key=str(observation.resource_id),
        transaction_key=f"recorded-correction-observation:{observation.resource_id}",
        as_of=observation.as_of,
        authorization=authorization,
    )
    return observation, reference


async def _append_correction_artifact(
    state: dict[str, Any],
    *,
    fixture: dict[str, Any],
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    detected_at: datetime,
    variant: str,
) -> tuple[CorrectionHandlingArtifactV1Alpha1, ImmutableRecordReferenceV1, str]:
    environment = state["environment"]
    correction = fixture["correction"]
    available_at = _time(fixture["recorded_replay"]["correction_available_at"])
    generated_at = state["clock"]()
    artifact = CorrectionHandlingArtifactV1Alpha1(
        product_id=environment.fixture["product_id"],
        artifact_key=f"recorded-correction-handling:{variant}:2021-10670",
        original_observation=original_ref,
        correction_observation=correction_ref,
        correction_document_number=correction["document_number"],
        corrects_document_number=correction["corrects_document_number"],
        corrected_instruction=correction["corrected_instruction"],
        correction_available_at=available_at,
        detected_at=detected_at,
        detection_delay_seconds=int((detected_at - available_at).total_seconds()),
        limitations=(
            "recorded_replay_not_live_monitoring",
            "bounded_to_one_explicit_federal_register_correction_pair",
            "source_publication_time_is_not_network_arrival_time",
        ),
        generated_at=generated_at,
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-recorded-correction-artifact:{variant}",
        subject_ref=str(artifact.artifact_id),
        subject_digest=str(artifact.artifact_digest),
        requested_at=generated_at,
    )
    reference = await _append_value(
        state,
        value=artifact,
        record_kind="correction_handling_artifact",
        record_key=str(artifact.artifact_id),
        transaction_key=f"correction-handling-artifact:{artifact.artifact_id}",
        as_of=generated_at,
        authorization=authorization,
    )
    content = (
        "# Recorded Correction Handling Artifact\n\n"
        f"Correction: {correction['document_number']}\n\n"
        f"Corrects: {correction['corrects_document_number']}\n\n"
        f"Instruction: {correction['corrected_instruction']}\n\n"
        f"Recorded-replay detection delay: {artifact.detection_delay_seconds} seconds\n\n"
        f"Original immutable Observation preserved: {original_ref.storage_id}\n"
    )
    return artifact, reference, content


async def _load_observation(state: dict[str, Any], reference: ImmutableRecordReferenceV1) -> ObservationV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.intelligence.observation/v1alpha1"
    ):
        raise AssertionError("recorded correction Observation is unavailable or changed")
    return ObservationV1Alpha1.model_validate(record.payload)


async def _load_artifact(
    state: dict[str, Any], reference: ImmutableRecordReferenceV1
) -> CorrectionHandlingArtifactV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.world-intelligence.correction-handling-artifact/v1alpha1"
    ):
        raise AssertionError("recorded correction artifact is unavailable or changed")
    return CorrectionHandlingArtifactV1Alpha1.model_validate(record.payload)


def _policy_digest(
    *,
    fixture_digest: str,
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    target_delay_seconds: int,
) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "fixture_digest": fixture_digest,
            "original_observation": original_ref.model_dump(mode="json"),
            "correction_observation": correction_ref.model_dump(mode="json"),
            "target_detection_delay_seconds": target_delay_seconds,
            "score": "1 if exact correction linkage and instruction are preserved within target else 0",
        }
    )


async def _review_artifact(
    state: dict[str, Any],
    *,
    fixture: dict[str, Any],
    subject: ImmutableRecordReferenceV1,
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> tuple[CorrectionDetectionReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    artifact = await _load_artifact(state, subject)
    original = await _load_observation(state, original_ref)
    correction = await _load_observation(state, correction_ref)
    original_payload = original.payload.parsed_value()["record"]
    correction_payload = correction.payload.parsed_value()["record"]
    fixture_digest = correction_fixture_digest(fixture)
    if (
        original.payload.parsed_value()["fixture_digest"] != fixture_digest
        or correction.payload.parsed_value()["fixture_digest"] != fixture_digest
    ):
        raise AssertionError("recorded correction Observations lost their exact fixture identity")
    linkage_correct = bool(
        artifact.original_observation == original_ref
        and artifact.correction_observation == correction_ref
        and artifact.correction_relation == "corrects"
        and artifact.correction_document_number == correction_payload["document_number"]
        and artifact.corrects_document_number == original_payload["document_number"]
        and correction_payload["corrects_document_number"] == original_payload["document_number"]
    )
    instruction_correct = bool(
        artifact.corrected_instruction == correction_payload["corrected_instruction"]
        and correction_payload["corrects_federal_register_page"] == 85524
        and correction_payload["corrected_page"] == 85530
    )
    target_delay_seconds = fixture["recorded_replay"]["target_detection_delay_seconds"]
    within_target = artifact.detection_delay_seconds <= target_delay_seconds
    score = float(linkage_correct and instruction_correct and artifact.prior_record_preserved and within_target)
    reviewed_at = state["clock"]()
    reviewer = _context(environment.context, "principal:world-correction-delay-reviewer")
    review = CorrectionDetectionReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"recorded-correction-delay-review:{pair_index}:{variant}",
        reviewed_subject=subject,
        original_observation=original_ref,
        correction_observation=correction_ref,
        reviewer_context=reviewer,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(
            fixture_digest=fixture_digest,
            original_ref=original_ref,
            correction_ref=correction_ref,
            target_delay_seconds=target_delay_seconds,
        ),
        source_fixture_digest=fixture_digest,
        linkage_correct=linkage_correct,
        instruction_correct=instruction_correct,
        prior_record_preserved=artifact.prior_record_preserved,
        detection_delay_seconds=artifact.detection_delay_seconds,
        target_detection_delay_seconds=target_delay_seconds,
        within_target=within_target,
        timeliness_score=score,
        limitations=artifact.limitations,
        reviewed_at=reviewed_at,
    )
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"recorded-correction-delay-review:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=reviewed_at,
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="correction_detection_review",
        record_key=str(review.review_id),
        transaction_key=f"correction-detection-review:{review.review_id}",
        as_of=reviewed_at,
        authorization=authorization,
    )
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: CorrectionDetectionReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.timeliness_score,
        observed_result=review_ref,
        latency_ms=review.detection_delay_seconds * 1_000,
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-correction-delay-outcome-observer")
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
        authorization_key=f"recorded-correction-delay-outcome:{pair_index}:{variant}",
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


async def run_correction_detection_delay_outcome(workspace_root: Path) -> dict[str, Any]:
    """Run P2C7 over an exact recorded official correction pair."""

    state: dict[str, Any] = {}
    prior = await run_contradiction_attention_outcome(workspace_root, state_sink=state)
    environment = state["environment"]
    fixture = load_correction_fixture()
    original, original_ref = await _append_source_observation(state, fixture=fixture, role="original")
    correction, correction_ref = await _append_source_observation(state, fixture=fixture, role="correction")
    replay = fixture["recorded_replay"]
    treatment_artifact, treatment_ref, treatment_content = await _append_correction_artifact(
        state,
        fixture=fixture,
        original_ref=original_ref,
        correction_ref=correction_ref,
        detected_at=_time(replay["treatment_detected_at"]),
        variant="treatment",
    )
    control_artifact, control_ref, control_content = await _append_correction_artifact(
        state,
        fixture=fixture,
        original_ref=original_ref,
        correction_ref=correction_ref,
        detected_at=_time(replay["control_detected_at"]),
        variant="delayed-control",
    )
    treatment_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=treatment_ref,
                content=treatment_content,
                pair_index=index,
                variant="correction-delay-treatment",
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
                variant="correction-delay-control",
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
    treatment_reviews: list[CorrectionDetectionReviewV1Alpha1] = []
    control_reviews: list[CorrectionDetectionReviewV1Alpha1] = []
    observed_times: list[datetime] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=treatment_ref,
            pair_index=index,
            variant="correction-delay-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="correction-delay-control",
        )
        treatment_review, treatment_review_ref = await _review_artifact(
            state,
            fixture=fixture,
            subject=treatment_ref,
            original_ref=original_ref,
            correction_ref=correction_ref,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_artifact(
            state,
            fixture=fixture,
            subject=control_ref,
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
        observed_times.extend((treatment_review.reviewed_at, control_review.reviewed_at))
        conditions = ImpactConditionsV1Alpha1(
            product_id=environment.fixture["product_id"],
            condition_key=f"world-recorded-correction-delay-pair:{index}",
            route_id="world:fcc-recorded-correction-delay-review",
            context_json=canonical_json(
                {
                    "fixture_digest": correction_fixture_digest(fixture),
                    "pair_index": index,
                    "recorded_transport": True,
                    "review_policy_digest": treatment_review.policy_digest,
                    "target_detection_delay_seconds": replay["target_detection_delay_seconds"],
                    "task": "exact_recorded_correction_linkage_and_detection_delay",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT,
            observation_window_end=max(observed_times),
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-recorded-correction-delay:{index}",
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
        evaluation_key="world-recorded-correction-delay:fcc-2021-10670",
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
    historical = await MeasuredImpactService(
        store=environment.store,
        authorizer=_ReplayMustNotAuthorize(),
        operation_binding=impact_binding,
    ).evaluate(request)
    if admission.replayed or not historical.replayed or historical.evaluation != admission.evaluation:
        raise AssertionError("correction-delay evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen correction-delay criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("correction-delay result did not emit its proposal-only mapping")
    if {item.linkage_correct for item in (*treatment_reviews, *control_reviews)} != {True}:
        raise AssertionError("recorded correction linkage was not preserved in every review")
    if {item.prior_record_preserved for item in (*treatment_reviews, *control_reviews)} != {True}:
        raise AssertionError("recorded correction handling rewrote or lost the original record")
    if {item.detection_delay_seconds for item in treatment_reviews} != {300}:
        raise AssertionError("treatment did not preserve the exact five-minute replay delay")
    if {item.detection_delay_seconds for item in control_reviews} != {21_600}:
        raise AssertionError("control did not preserve the exact six-hour replay delay")

    return {
        "contract": "ace.world-intelligence.correction-detection-delay-outcome/v1alpha1",
        "prior_contradiction_attention": prior,
        "source_pair": {
            "fixture_id": fixture["fixture_id"],
            "fixture_digest": correction_fixture_digest(fixture),
            "network_access": fixture["network_access"],
            "source_policy": fixture["source_policy"],
            "original": fixture["original"],
            "correction": fixture["correction"],
            "original_observation_id": str(original.resource_id),
            "correction_observation_id": str(correction.resource_id),
        },
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "target_detection_delay_seconds": replay["target_detection_delay_seconds"],
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
            "historical": historical.replayed,
            "no_reauthorization": True,
            "transaction_receipt_id": str(historical.transaction_receipt.receipt_id),
        },
        "scope": {
            "exact_recorded_official_correction_pair": True,
            "exact_correction_linkage_reviewed": True,
            "prior_record_preserved": True,
            "network_access": False,
            "live_monitoring_claimed": False,
            "network_arrival_delay_claimed": False,
            "population_detection_performance_claimed": False,
            "legal_truth_claimed": False,
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
            asyncio.run(run_correction_detection_delay_outcome(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
