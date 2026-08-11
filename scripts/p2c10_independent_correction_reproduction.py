"""Reproduce measured correction quality over an independent BLS source family."""

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
from scripts.p2c7_correction_detection_delay_outcome import _load_observation
from scripts.p2c9_forecast_calibration_outcome import run_forecast_calibration_outcome

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "domain_packs" / "tests" / "fixtures" / "p2c10_bls_correction_pair.json"
)
OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "official_correction_statement_quality"
CRITERION_ID = "impact_criterion:world-independent-official-correction-statement-quality"
CRITERION_FROZEN_AT = _time("2026-08-10T23:59:00Z")
REVIEW_POLICY_ID = "world_independent_official_correction_statement_quality"
REVIEW_POLICY_VERSION = "candidate-1"

ORIGINAL_STATEMENT = "The number of job openings decreased in federal government (39,000)."
CORRECTED_STATEMENT = "The number of job openings decreased in federal government (−39,000)."
RELEASE_URI = "https://www.bls.gov/news.release/archives/jolts_07012025.htm"
ERRATA_URI = "https://www.bls.gov/errata/"

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_independent_correction_reproduction_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "d" * 64,
)


class OfficialCorrectionArtifactV1Alpha1(_FrozenModel):
    """One exact World rendering of an official correction pair."""

    contract: Literal["ace.world-intelligence.official-correction-artifact/v1alpha1"] = (
        "ace.world-intelligence.official-correction-artifact/v1alpha1"
    )
    product_id: str
    artifact_key: str
    original_observation: ImmutableRecordReferenceV1
    correction_observation: ImmutableRecordReferenceV1
    source_family: Literal["bls_public_errata"] = "bls_public_errata"
    source_release_id: str
    correction_record_id: str
    corrects_source_record_id: str
    correction_relation: Literal["corrects"] = "corrects"
    original_statement: str
    corrected_statement: str
    displayed_statement: str
    source_coverage_complete: Literal[True] = True
    correction_link_visible: Literal[True] = True
    prior_record_preserved: Literal[True] = True
    limitations: tuple[str, ...]
    generated_at: datetime
    artifact_id: str | None = None
    artifact_digest: str | None = None

    @field_validator("limitations")
    @classmethod
    def canonicalize_limitations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        ordered = tuple(sorted(value))
        if not ordered or len(ordered) != len(set(ordered)):
            raise ValueError("official-correction limitations must be non-empty and unique")
        return ordered

    @model_validator(mode="after")
    def validate_scope_pair_and_identity(self) -> Self:
        if (
            self.original_observation.product_id != self.product_id
            or self.correction_observation.product_id != self.product_id
        ):
            raise ValueError("official-correction artifact crossed exact product scope")
        if self.original_observation.storage_id == self.correction_observation.storage_id:
            raise ValueError("official-correction artifact requires distinct exact source records")
        if self.corrects_source_record_id != self.source_release_id:
            raise ValueError("official-correction artifact lost its exact correction linkage")
        if self.original_statement != ORIGINAL_STATEMENT or self.corrected_statement != CORRECTED_STATEMENT:
            raise ValueError("official-correction artifact changed the frozen statement pair")
        if self.displayed_statement not in {self.original_statement, self.corrected_statement}:
            raise ValueError("official-correction artifact introduced an unreviewed statement form")
        _derive_identity(
            self,
            prefix="official_correction_artifact",
            id_field="artifact_id",
            digest_field="artifact_digest",
        )
        return self


class IndependentCorrectionReviewV1Alpha1(_FrozenModel):
    """Exact product-owned review of correction visibility and statement quality."""

    contract: Literal["ace.world-intelligence.independent-correction-review/v1alpha1"] = (
        "ace.world-intelligence.independent-correction-review/v1alpha1"
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
    source_family: Literal["bls_public_errata"] = "bls_public_errata"
    source_coverage_complete: bool
    correction_link_visible: bool
    prior_record_preserved: bool
    original_statement: str
    expected_corrected_statement: str
    displayed_statement: str
    corrected_statement_exact: bool
    stale_form_present: bool
    correction_quality_score: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...]
    reviewed_at: datetime
    review_id: str | None = None
    review_digest: str | None = None

    @field_validator("limitations")
    @classmethod
    def canonicalize_limitations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        ordered = tuple(sorted(value))
        if not ordered or len(ordered) != len(set(ordered)):
            raise ValueError("independent-correction review limitations must be non-empty and unique")
        return ordered

    @model_validator(mode="after")
    def validate_scope_score_and_identity(self) -> Self:
        references = (self.reviewed_subject, self.original_observation, self.correction_observation)
        if any(item.product_id != self.product_id for item in references):
            raise ValueError("independent-correction review crossed exact product scope")
        if self.reviewer_context.product_id != self.product_id:
            raise ValueError("independent-correction reviewer crossed exact product scope")
        if self.original_observation.storage_id == self.correction_observation.storage_id:
            raise ValueError("independent-correction review requires distinct source records")
        exact = self.displayed_statement == self.expected_corrected_statement
        stale = self.displayed_statement == self.original_statement
        if self.corrected_statement_exact != exact or self.stale_form_present != stale:
            raise ValueError("independent-correction statement disposition was not derived exactly")
        expected_score = float(
            self.source_coverage_complete
            and self.correction_link_visible
            and self.prior_record_preserved
            and exact
            and not stale
        )
        if self.correction_quality_score != expected_score:
            raise ValueError("correction quality score differs from the frozen product rule")
        _derive_identity(
            self,
            prefix="independent_correction_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(
            f"historical independent-correction evaluation requested new authority: {request.authorization_key}"
        )


def validate_bls_correction_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if the recorded BLS source pair or its policy drifts."""

    if fixture.get("network_access") is not False:
        raise AssertionError("recorded BLS correction fixture must remain network-free")
    if fixture.get("source_policy") != {
        "publisher": "U.S. Bureau of Labor Statistics",
        "source_family": "bls_public_errata",
        "release_uri": RELEASE_URI,
        "errata_uri": ERRATA_URI,
        "recorded_replay": True,
        "historical_original_form_derived_from_erratum": True,
        "statistical_validity_claimed": False,
    }:
        raise AssertionError("recorded BLS correction source policy changed")
    original = fixture.get("original", {})
    correction = fixture.get("correction", {})
    if original.get("record_id") != "USDL-25-1087" or original.get("release_uri") != RELEASE_URI:
        raise AssertionError("recorded BLS release identity changed")
    if original.get("reported_sentence_without_required_minus_sign") != ORIGINAL_STATEMENT:
        raise AssertionError("recorded BLS original statement changed")
    if (
        correction.get("record_id") != "bls-errata-2025-07-01-jolts"
        or correction.get("corrects_record_id") != original.get("record_id")
        or correction.get("errata_uri") != ERRATA_URI
    ):
        raise AssertionError("recorded BLS correction linkage changed")
    if correction.get("corrected_sentence") != CORRECTED_STATEMENT:
        raise AssertionError("recorded BLS corrected statement changed")
    return fixture


def load_bls_correction_fixture() -> dict[str, Any]:
    return validate_bls_correction_fixture(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def bls_correction_fixture_digest(fixture: dict[str, Any]) -> str:
    return f"sha256:{canonical_hash(fixture)}"


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 110)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-independent-official-correction-quality",
        111,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-independent-official-correction-quality",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(
        product_id,
        "capability_state",
        capability_state_ref_for_artifact(IMPACT_ARTIFACT),
        112,
    )
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 113)
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
    source_id = source["record_id"]
    published_at = _time(source["published_at"] if role == "original" else source["corrected_at"])
    ingested_at = _time(fixture["recorded_at"])
    fixture_digest = bls_correction_fixture_digest(fixture)
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
        source_ref=f"bls_{'release' if role == 'original' else 'erratum'}:{source_id}",
        source_digest=_digest(source),
        acquisition_mode=EvidenceAcquisitionMode.RECORDED_REPLAY,
        acquisition_receipt_ref=f"recorded_replay_acquisition:{source_id}",
        acquisition_receipt_digest=_digest(
            {"fixture_digest": fixture_digest, "record_id": source_id, "network_access": False}
        ),
        source_published_at=published_at,
        event_effective_at=None,
        observed_at=published_at,
        ingested_at=ingested_at,
        subject_refs=("bls_program:jolts", "bls_release:USDL-25-1087"),
        payload=CanonicalJsonValueV1Alpha1(value_json=canonical_json(payload)),
        confidence=1.0,
    )
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-bls-correction-observation:{role}",
        subject_ref=str(observation.resource_id),
        subject_digest=str(observation.resource_digest),
        requested_at=requested_at,
    )
    reference = await _append_value(
        state,
        value=observation,
        record_kind="observation",
        record_key=str(observation.resource_id),
        transaction_key=f"world-bls-correction-observation:{observation.resource_id}",
        as_of=observation.as_of,
        authorization=authorization,
    )
    return observation, reference


async def _append_artifact(
    state: dict[str, Any],
    *,
    fixture: dict[str, Any],
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    variant: Literal["treatment", "control"],
) -> tuple[OfficialCorrectionArtifactV1Alpha1, ImmutableRecordReferenceV1, str]:
    environment = state["environment"]
    displayed = CORRECTED_STATEMENT if variant == "treatment" else ORIGINAL_STATEMENT
    artifact = OfficialCorrectionArtifactV1Alpha1(
        product_id=environment.fixture["product_id"],
        artifact_key=f"bls-jolts-correction:{variant}:USDL-25-1087",
        original_observation=original_ref,
        correction_observation=correction_ref,
        source_release_id=fixture["original"]["record_id"],
        correction_record_id=fixture["correction"]["record_id"],
        corrects_source_record_id=fixture["correction"]["corrects_record_id"],
        original_statement=ORIGINAL_STATEMENT,
        corrected_statement=CORRECTED_STATEMENT,
        displayed_statement=displayed,
        limitations=(
            "historical_original_form_derived_from_public_erratum",
            "one_recorded_bls_correction_not_population_performance",
            "recorded_replay_not_live_monitoring",
            "statement_quality_not_statistical_validity_or_human_benefit",
        ),
        generated_at=state["clock"](),
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-bls-correction-artifact:{variant}",
        subject_ref=str(artifact.artifact_id),
        subject_digest=str(artifact.artifact_digest),
        requested_at=state["clock"](),
    )
    reference = await _append_value(
        state,
        value=artifact,
        record_kind="official_correction_artifact",
        record_key=str(artifact.artifact_id),
        transaction_key=f"world-bls-correction-artifact:{artifact.artifact_id}",
        as_of=artifact.generated_at,
        authorization=authorization,
    )
    content = (
        "# BLS JOLTS Correction Review\n\n"
        f"Original Observation: {original_ref.storage_id}\n\n"
        f"Correction Observation: {correction_ref.storage_id}\n\n"
        f"Release: {RELEASE_URI}\n\n"
        f"Erratum: {ERRATA_URI}\n\n"
        f"Reviewed statement: {displayed}\n"
    )
    return artifact, reference, content


async def _load_artifact(
    state: dict[str, Any], reference: ImmutableRecordReferenceV1
) -> OfficialCorrectionArtifactV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.world-intelligence.official-correction-artifact/v1alpha1"
    ):
        raise AssertionError("official-correction artifact is unavailable or changed")
    return OfficialCorrectionArtifactV1Alpha1.model_validate(record.payload)


def _policy_digest(
    fixture: dict[str, Any],
    *,
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "fixture_digest": bls_correction_fixture_digest(fixture),
            "original_observation": original_ref.model_dump(mode="json"),
            "correction_observation": correction_ref.model_dump(mode="json"),
            "original_statement": ORIGINAL_STATEMENT,
            "corrected_statement": CORRECTED_STATEMENT,
            "score": (
                "1 only when exact source coverage, correction linkage, prior-record preservation, "
                "corrected statement, and stale-form removal all pass; otherwise 0"
            ),
        }
    )


async def _review_artifact(
    state: dict[str, Any],
    *,
    fixture: dict[str, Any],
    subject_ref: ImmutableRecordReferenceV1,
    original_ref: ImmutableRecordReferenceV1,
    correction_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: Literal["treatment", "control"],
) -> tuple[IndependentCorrectionReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    artifact = await _load_artifact(state, subject_ref)
    original = await _load_observation(state, original_ref)
    correction = await _load_observation(state, correction_ref)
    original_payload = original.payload.parsed_value()
    correction_payload = correction.payload.parsed_value()
    expected_original = original_payload["record"] == fixture["original"]
    expected_correction = correction_payload["record"] == fixture["correction"]
    source_coverage = bool(
        expected_original
        and expected_correction
        and artifact.original_observation == original_ref
        and artifact.correction_observation == correction_ref
    )
    linkage = bool(
        artifact.correction_relation == "corrects"
        and artifact.corrects_source_record_id == artifact.source_release_id
        and fixture["correction"]["corrects_record_id"] == fixture["original"]["record_id"]
    )
    prior_preserved = bool(await _load_observation(state, original_ref) == original)
    exact = artifact.displayed_statement == CORRECTED_STATEMENT
    stale = artifact.displayed_statement == ORIGINAL_STATEMENT
    reviewer = _context(environment.context, "principal:world-independent-correction-reviewer")
    review = IndependentCorrectionReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"bls-independent-correction-quality:{pair_index}:{variant}",
        reviewed_subject=subject_ref,
        original_observation=original_ref,
        correction_observation=correction_ref,
        reviewer_context=reviewer,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(
            fixture,
            original_ref=original_ref,
            correction_ref=correction_ref,
        ),
        source_fixture_digest=bls_correction_fixture_digest(fixture),
        source_coverage_complete=source_coverage,
        correction_link_visible=linkage,
        prior_record_preserved=prior_preserved,
        original_statement=ORIGINAL_STATEMENT,
        expected_corrected_statement=CORRECTED_STATEMENT,
        displayed_statement=artifact.displayed_statement,
        corrected_statement_exact=exact,
        stale_form_present=stale,
        correction_quality_score=float(source_coverage and linkage and prior_preserved and exact and not stale),
        limitations=artifact.limitations,
        reviewed_at=state["clock"](),
    )
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"review:world-bls-independent-correction:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=state["clock"](),
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="independent_correction_review",
        record_key=str(review.review_id),
        transaction_key=f"world-independent-correction-review:{review.review_id}",
        as_of=review.reviewed_at,
        authorization=authorization,
    )
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: IndependentCorrectionReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: Literal["treatment", "control"],
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    latency_ms = max(0, int((review.reviewed_at - export.intent.requested_at).total_seconds() * 1_000))
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.correction_quality_score,
        observed_result=review_ref,
        latency_ms=latency_ms,
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    observer = _context(environment.context, "principal:world-independent-correction-outcome-observer")
    recorded_at = state["clock"]()
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
        authorization_key=f"outcome:world-bls-independent-correction:{pair_index}:{variant}",
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


async def run_independent_correction_reproduction(workspace_root: Path) -> dict[str, Any]:
    """Run P2C10 over a recorded BLS correction and unchanged impact contracts."""

    state: dict[str, Any] = {}
    prior_packet = await run_forecast_calibration_outcome(workspace_root, state_sink=state)
    environment = state["environment"]
    fixture = load_bls_correction_fixture()
    state["clock"].set(_time(fixture["recorded_at"]) + timedelta(seconds=1))
    original, original_ref = await _append_source_observation(state, fixture=fixture, role="original")
    correction, correction_ref = await _append_source_observation(state, fixture=fixture, role="correction")
    criterion_head, impact_binding = _install_policy(state)
    state["clock"].set(CRITERION_FROZEN_AT + timedelta(seconds=1))
    treatment_artifact, treatment_ref, treatment_content = await _append_artifact(
        state,
        fixture=fixture,
        original_ref=original_ref,
        correction_ref=correction_ref,
        variant="treatment",
    )
    control_artifact, control_ref, control_content = await _append_artifact(
        state,
        fixture=fixture,
        original_ref=original_ref,
        correction_ref=correction_ref,
        variant="control",
    )
    treatment_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=treatment_ref,
                content=treatment_content,
                pair_index=index,
                variant="bls-independent-correction-treatment",
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
                variant="bls-independent-correction-control",
            )
            for index in (1, 2)
        ]
    )

    evidence: list[ImpactEvidenceV1Alpha1] = []
    treatment_reviews: list[IndependentCorrectionReviewV1Alpha1] = []
    control_reviews: list[IndependentCorrectionReviewV1Alpha1] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=treatment_ref,
            pair_index=index,
            variant="bls-independent-correction-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="bls-independent-correction-control",
        )
        treatment_review, treatment_review_ref = await _review_artifact(
            state,
            fixture=fixture,
            subject_ref=treatment_ref,
            original_ref=original_ref,
            correction_ref=correction_ref,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_artifact(
            state,
            fixture=fixture,
            subject_ref=control_ref,
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
            condition_key=f"world-bls-independent-correction-quality-pair:{index}",
            route_id="world:bls-recorded-correction-review",
            context_json=canonical_json(
                {
                    "fixture_digest": bls_correction_fixture_digest(fixture),
                    "pair_index": index,
                    "review_policy_digest": treatment_review.policy_digest,
                    "source_family": "bls_public_errata",
                    "source_refs": sorted((original_ref.storage_id, correction_ref.storage_id)),
                    "task": "render_exact_official_correction_with_prior_record_preserved",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT,
            observation_window_end=state["clock"](),
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-bls-independent-correction-quality:{index}",
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
        useful_effect_threshold=1.0,
        harmful_effect_threshold=1.0,
        minimum_matched_pairs=2,
        requires_observed_result=True,
        harmful_action=ImpactGovernanceAction.ROLLBACK,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(criterion_head),
        frozen_at=CRITERION_FROZEN_AT,
    )
    request = ImpactEvaluationRequestV1Alpha1(
        evaluation_key="world-independent-correction-quality:bls-jolts-2025-minus-sign",
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
        raise AssertionError("independent-correction evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen independent-correction criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("independent-correction result did not emit its proposal-only mapping")
    if {item.correction_quality_score for item in treatment_reviews} != {1.0}:
        raise AssertionError("independent-correction treatment lost the exact corrected statement")
    if {item.correction_quality_score for item in control_reviews} != {0.0}:
        raise AssertionError("independent-correction control did not retain the stale statement form")

    state.update(
        {
            "p2c10_fixture": fixture,
            "p2c10_original_observation": original,
            "p2c10_original_observation_ref": original_ref,
            "p2c10_correction_observation": correction,
            "p2c10_correction_observation_ref": correction_ref,
        }
    )
    return {
        "contract": "ace.world-intelligence.independent-correction-reproduction/v1alpha1",
        "prior_forecast_calibration": prior_packet,
        "source_pair": {
            "fixture_id": fixture["fixture_id"],
            "fixture_digest": bls_correction_fixture_digest(fixture),
            "network_access": fixture["network_access"],
            "source_policy": fixture["source_policy"],
            "original": fixture["original"],
            "correction": fixture["correction"],
            "original_observation": original_ref.model_dump(mode="json"),
            "correction_observation": correction_ref.model_dump(mode="json"),
        },
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "score_rule": (
                "1 only when exact source coverage, correction linkage, prior-record preservation, "
                "corrected statement, and stale-form removal all pass; otherwise 0"
            ),
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
            "independent_source_family_reproduction": True,
            "exact_recorded_official_correction_pair": True,
            "prior_record_preserved": True,
            "domain_neutral_core_contract_unchanged": True,
            "domain_pack_changed": False,
            "connector_changed": False,
            "network_access": False,
            "live_monitoring_claimed": False,
            "statistical_validity_claimed": False,
            "population_correction_performance_claimed": False,
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
            asyncio.run(run_independent_correction_reproduction(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
