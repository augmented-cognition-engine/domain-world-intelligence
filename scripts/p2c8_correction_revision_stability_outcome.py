"""Measure bounded correction-induced Brief revision stability."""

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
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    BriefV1Alpha1,
    CitationV1Alpha1,
    ClaimGroundingKind,
    GroundedClaimV1Alpha1,
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
    LineageReferenceV1Alpha1,
    LineageRelation,
    LineageResourceKind,
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
from scripts.p2c7_correction_detection_delay_outcome import (
    correction_fixture_digest,
    run_correction_detection_delay_outcome,
)

OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "recorded_correction_revision_stability"
CRITERION_ID = "impact_criterion:world-recorded-correction-revision-stability"
PRIOR_BRIEF_AT = _time("2026-08-10T23:14:00Z")
REVISED_BRIEF_AT = _time("2026-08-10T23:15:00Z")
CRITERION_FROZEN_AT = _time("2026-08-10T23:16:00Z")
REVIEW_POLICY_ID = "world_recorded_correction_revision_stability"
REVIEW_POLICY_VERSION = "candidate-1"

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_recorded_correction_revision_stability_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "b" * 64,
)


class BriefRevisionStabilityReviewV1Alpha1(_FrozenModel):
    """Exact product review of one prior/revised Brief pair."""

    contract: Literal["ace.world-intelligence.brief-revision-stability-review/v1alpha1"] = (
        "ace.world-intelligence.brief-revision-stability-review/v1alpha1"
    )
    product_id: str
    review_key: str
    prior_brief: ImmutableRecordReferenceV1
    revised_brief: ImmutableRecordReferenceV1
    original_observation: ImmutableRecordReferenceV1
    correction_observation: ImmutableRecordReferenceV1
    reviewer_context: AuthenticatedRuntimeContextV1Alpha1
    policy_id: str
    policy_version: str
    policy_digest: str
    source_fixture_digest: str
    expected_affected_claim_id: str
    expected_replacement_claim_id: str
    expected_stable_claim_ids: tuple[str, ...] = Field(min_length=1)
    preserved_stable_claim_ids: tuple[str, ...]
    drifted_stable_claim_ids: tuple[str, ...]
    unexpected_claim_ids: tuple[str, ...]
    prior_claim_count: int = Field(gt=0)
    revised_claim_count: int = Field(gt=0)
    replacement_claim_present: bool
    stale_affected_claim_present: bool
    affected_update_correct: bool
    correction_visible: bool
    source_coverage_complete: bool
    claim_count_preserved: bool
    unaffected_preservation_rate: float = Field(ge=0.0, le=1.0)
    revision_stability_score: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...]
    reviewed_at: datetime
    review_id: str | None = None
    review_digest: str | None = None

    @model_validator(mode="after")
    def validate_partition_score_and_identity(self) -> Self:
        tuples = (
            self.expected_stable_claim_ids,
            self.preserved_stable_claim_ids,
            self.drifted_stable_claim_ids,
            self.unexpected_claim_ids,
        )
        if any(items != tuple(sorted(set(items))) for items in tuples):
            raise ValueError("revision review claim identities must be unique and sorted")
        expected = set(self.expected_stable_claim_ids)
        preserved = set(self.preserved_stable_claim_ids)
        drifted = set(self.drifted_stable_claim_ids)
        if preserved & drifted or preserved | drifted != expected:
            raise ValueError("preserved and drifted claims must exactly partition stable claims")
        if self.expected_affected_claim_id in expected:
            raise ValueError("the affected claim cannot also be an expected stable claim")
        expected_update = self.replacement_claim_present and not self.stale_affected_claim_present
        if self.affected_update_correct != expected_update:
            raise ValueError("affected update disposition differs from exact claim presence")
        expected_count_preserved = self.prior_claim_count == self.revised_claim_count
        if self.claim_count_preserved != expected_count_preserved:
            raise ValueError("claim-count disposition differs from exact counts")
        expected_rate = len(preserved) / len(expected)
        if self.unaffected_preservation_rate != expected_rate:
            raise ValueError("unaffected preservation rate differs from exact claim partition")
        gates = (
            self.affected_update_correct,
            self.correction_visible,
            self.source_coverage_complete,
            self.claim_count_preserved,
        )
        expected_score = expected_rate if all(gates) else 0.0
        if self.revision_stability_score != expected_score:
            raise ValueError("revision stability score differs from frozen product rule")
        _derive_identity(
            self,
            prefix="brief_revision_stability_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(
            f"historical revision-stability evaluation requested new authority: {request.authorization_key}"
        )


def _lineage(
    resource: ObservationV1Alpha1 | BriefV1Alpha1,
    *,
    relation: LineageRelation = LineageRelation.DERIVED_FROM,
) -> LineageReferenceV1Alpha1:
    if isinstance(resource, ObservationV1Alpha1):
        kind = LineageResourceKind.OBSERVATION
        available_at = resource.ingested_at
    else:
        kind = LineageResourceKind.BRIEF
        available_at = resource.generated_at
    return LineageReferenceV1Alpha1(
        resource_kind=kind,
        relation=relation,
        resource_id=str(resource.resource_id),
        resource_digest=str(resource.resource_digest),
        resource_as_of=resource.as_of,
        resource_available_at=available_at,
    )


def _citation(
    observation: ObservationV1Alpha1,
    *,
    locator: str,
    excerpt: str,
) -> CitationV1Alpha1:
    return CitationV1Alpha1(
        source_ref=observation.source_ref,
        source_digest=observation.source_digest,
        acquisition_mode=observation.acquisition_mode,
        acquisition_receipt_ref=observation.acquisition_receipt_ref,
        acquisition_receipt_digest=observation.acquisition_receipt_digest,
        source_as_of=observation.source_published_at or observation.observed_at,
        retrieved_at=observation.ingested_at,
        locator=locator,
        excerpt=excerpt,
    )


def _claim(statement: str, citation: CitationV1Alpha1) -> GroundedClaimV1Alpha1:
    return GroundedClaimV1Alpha1(
        statement=statement,
        grounding_kind=ClaimGroundingKind.CITED,
        citation_ids=(str(citation.citation_id),),
        confidence=1.0,
        uncertainty="Bounded to the exact recorded Federal Register documents and source-policy limits.",
    )


def _body(title: str, claims: tuple[GroundedClaimV1Alpha1, ...]) -> str:
    return "\n".join((f"# {title}", "", *(f"- {item.statement}" for item in claims))) + "\n"


def _build_briefs(state: dict[str, Any]) -> dict[str, Any]:
    environment = state["environment"]
    original: ObservationV1Alpha1 = state["p2c7_original_observation"]
    correction: ObservationV1Alpha1 = state["p2c7_correction_observation"]
    activation_revision = state["brief_admission"].brief.activation_revision
    original_citation = _citation(
        original,
        locator="Federal Register 85 FR 85524 and page 85530 instruction material",
        excerpt="FCC document 2020-28779, 85 FR 85524.",
    )
    correction_citation = _citation(
        correction,
        locator="Federal Register 86 FR 27275 correction to page 85530",
        excerpt=("Remove instruction 20a and redesignate instructions 20b and 20c as instructions 20a and 20b."),
    )
    affected = _claim(
        "The page 85530 amendment instructions include instructions 20a, 20b, and 20c.",
        original_citation,
    )
    stable_publication = _claim(
        "FCC document 2020-28779 was published on 2020-12-29 at 85 FR 85524.",
        original_citation,
    )
    stable_agency = _claim(
        "The issuing agency is the Federal Communications Commission.",
        original_citation,
    )
    prior_claims = (affected, stable_publication, stable_agency)
    prior = BriefV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=activation_revision,
        as_of=PRIOR_BRIEF_AT,
        lineage=(_lineage(original),),
        brief_type_ref="brief_type:world-reality-brief",
        title="FCC Electronic Filing Rule — Recorded Brief",
        executive_summary="Recorded orientation to the original FCC electronic-filing rule instructions.",
        body_markdown=_body("FCC Electronic Filing Rule — Recorded Brief", prior_claims),
        generated_at=PRIOR_BRIEF_AT,
        citations=(original_citation,),
        claims=prior_claims,
    )
    replacement = _claim(
        (
            "Correction 2021-10670 directs removal of instruction 20a and redesignation of "
            "instructions 20b and 20c as instructions 20a and 20b on page 85530."
        ),
        correction_citation,
    )
    treatment_claims = (replacement, stable_publication, stable_agency)
    control_publication = _claim(
        "Publication of FCC document 2020-28779 occurred on 2020-12-29 in 85 FR 85524.",
        original_citation,
    )
    control_agency = _claim(
        "The Federal Communications Commission issued the document.",
        original_citation,
    )
    control_claims = (replacement, control_publication, control_agency)
    common = {
        "product_id": environment.fixture["product_id"],
        "mode": IntelligenceResourceMode.PREPARED,
        "activation_revision": activation_revision,
        "as_of": REVISED_BRIEF_AT,
        "lineage": (
            _lineage(original),
            _lineage(correction),
            _lineage(prior, relation=LineageRelation.CONTEXT),
        ),
        "brief_type_ref": "brief_type:world-reality-brief",
        "title": "FCC Electronic Filing Rule — Corrected Brief",
        "executive_summary": "The explicit FCC correction is visible while unaffected facts remain stable.",
        "generated_at": REVISED_BRIEF_AT,
        "citations": (original_citation, correction_citation),
    }
    treatment = BriefV1Alpha1(
        **common,
        body_markdown=_body("FCC Electronic Filing Rule — Corrected Brief", treatment_claims),
        claims=treatment_claims,
    )
    control = BriefV1Alpha1(
        **common,
        body_markdown=_body("FCC Electronic Filing Rule — Corrected Brief", control_claims),
        claims=control_claims,
    )
    return {
        "prior": prior,
        "treatment": treatment,
        "control": control,
        "original_citation": original_citation,
        "correction_citation": correction_citation,
        "affected_claim": affected,
        "replacement_claim": replacement,
        "stable_claims": (stable_publication, stable_agency),
    }


async def _append_brief(
    state: dict[str, Any],
    *,
    brief: BriefV1Alpha1,
    role: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    clock = state["clock"]
    if clock.current <= brief.as_of:
        clock.set(brief.as_of + timedelta(seconds=1))
    requested_at = clock()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key=f"append:world-correction-revision-brief:{role}",
        subject_ref=str(brief.resource_id),
        subject_digest=str(brief.resource_digest),
        requested_at=requested_at,
    )
    return await _append_value(
        state,
        value=brief,
        record_kind="brief",
        record_key=str(brief.resource_id),
        transaction_key=f"world-correction-revision-brief:{role}:{brief.resource_id}",
        as_of=brief.as_of,
        authorization=authorization,
    )


async def _load_brief(state: dict[str, Any], reference: ImmutableRecordReferenceV1) -> BriefV1Alpha1:
    record = await state["environment"].store.load_record(
        reference.storage_id,
        product_id=reference.product_id,
        record_space=reference.record_space,
        record_kind=reference.record_kind,
    )
    if (
        record is None
        or record.reference() != reference
        or record.payload_contract != "ace.intelligence.brief/v1alpha1"
    ):
        raise AssertionError("revision-stability Brief is unavailable or changed")
    return BriefV1Alpha1.model_validate(record.payload)


def _policy_digest(
    *,
    fixture_digest: str,
    prior_ref: ImmutableRecordReferenceV1,
    affected_claim_id: str,
    replacement_claim_id: str,
    stable_claim_ids: tuple[str, ...],
) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "fixture_digest": fixture_digest,
            "prior_brief": prior_ref.model_dump(mode="json"),
            "expected_affected_claim_id": affected_claim_id,
            "expected_replacement_claim_id": replacement_claim_id,
            "expected_stable_claim_ids": stable_claim_ids,
            "score": (
                "unaffected preservation rate when the affected update, correction visibility, "
                "source coverage, and claim count all pass; otherwise 0"
            ),
        }
    )


async def _review_revision(
    state: dict[str, Any],
    *,
    material: dict[str, Any],
    prior_ref: ImmutableRecordReferenceV1,
    revised_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> tuple[BriefRevisionStabilityReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    prior = await _load_brief(state, prior_ref)
    revised = await _load_brief(state, revised_ref)
    expected_stable = tuple(sorted(str(item.claim_id) for item in material["stable_claims"]))
    affected_id = str(material["affected_claim"].claim_id)
    replacement_id = str(material["replacement_claim"].claim_id)
    prior_ids = {str(item.claim_id) for item in prior.claims}
    revised_ids = {str(item.claim_id) for item in revised.claims}
    preserved = tuple(sorted(set(expected_stable) & revised_ids))
    drifted = tuple(sorted(set(expected_stable) - revised_ids))
    unexpected = tuple(sorted(revised_ids - set(expected_stable) - {replacement_id}))
    correction_citation_id = str(material["correction_citation"].citation_id)
    original_citation_id = str(material["original_citation"].citation_id)
    revised_citation_ids = {str(item.citation_id) for item in revised.citations}
    lineage = {(item.resource_id, item.resource_digest) for item in revised.lineage}
    correction = state["p2c7_correction_observation"]
    prior_lineage = (str(prior.resource_id), str(prior.resource_digest)) in lineage
    correction_lineage = (str(correction.resource_id), str(correction.resource_digest)) in lineage
    replacement_present = replacement_id in revised_ids
    stale_present = affected_id in revised_ids
    correction_visible = correction_citation_id in revised_citation_ids and correction_lineage and prior_lineage
    source_coverage_complete = {original_citation_id, correction_citation_id}.issubset(revised_citation_ids)
    claim_count_preserved = len(prior.claims) == len(revised.claims)
    preservation_rate = len(preserved) / len(expected_stable)
    affected_update_correct = replacement_present and not stale_present
    score = (
        preservation_rate
        if affected_update_correct and correction_visible and source_coverage_complete and claim_count_preserved
        else 0.0
    )
    reviewed_at = state["clock"]()
    reviewer = _context(environment.context, "principal:world-revision-stability-reviewer")
    fixture_digest = correction_fixture_digest(state["p2c7_fixture"])
    review = BriefRevisionStabilityReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"recorded-correction-revision-stability:{pair_index}:{variant}",
        prior_brief=prior_ref,
        revised_brief=revised_ref,
        original_observation=state["p2c7_original_observation_ref"],
        correction_observation=state["p2c7_correction_observation_ref"],
        reviewer_context=reviewer,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(
            fixture_digest=fixture_digest,
            prior_ref=prior_ref,
            affected_claim_id=affected_id,
            replacement_claim_id=replacement_id,
            stable_claim_ids=expected_stable,
        ),
        source_fixture_digest=fixture_digest,
        expected_affected_claim_id=affected_id,
        expected_replacement_claim_id=replacement_id,
        expected_stable_claim_ids=expected_stable,
        preserved_stable_claim_ids=preserved,
        drifted_stable_claim_ids=drifted,
        unexpected_claim_ids=unexpected,
        prior_claim_count=len(prior.claims),
        revised_claim_count=len(revised.claims),
        replacement_claim_present=replacement_present,
        stale_affected_claim_present=stale_present,
        affected_update_correct=affected_update_correct,
        correction_visible=correction_visible,
        source_coverage_complete=source_coverage_complete,
        claim_count_preserved=claim_count_preserved,
        unaffected_preservation_rate=preservation_rate,
        revision_stability_score=score,
        limitations=(
            "recorded_replay_not_live_revision",
            "one_explicit_correction_pair",
            "two_replicated_workflows_not_independent_events",
            "semantic_equivalence_of_paraphrases_is_product_fixture_policy",
        ),
        reviewed_at=reviewed_at,
    )
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"recorded-correction-revision-stability:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=reviewed_at,
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="brief_revision_stability_review",
        record_key=str(review.review_id),
        transaction_key=f"brief-revision-stability-review:{review.review_id}",
        as_of=reviewed_at,
        authorization=authorization,
    )
    if affected_id not in prior_ids:
        raise AssertionError("frozen affected claim is absent from the exact prior Brief")
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: BriefRevisionStabilityReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.revision_stability_score,
        observed_result=review_ref,
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-revision-stability-outcome-observer")
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
        authorization_key=f"recorded-correction-revision-stability-outcome:{pair_index}:{variant}",
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


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 90)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-recorded-correction-revision-stability",
        91,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-recorded-correction-revision-stability",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(
        product_id,
        "capability_state",
        capability_state_ref_for_artifact(IMPACT_ARTIFACT),
        92,
    )
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 93)
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return criterion_head, binding


async def run_correction_revision_stability_outcome(
    workspace_root: Path,
    *,
    state_sink: dict[str, Any] | None = None,
    before_correction=None,
) -> dict[str, Any]:
    """Run P2C8 over exact prior, stable revision, and drift-control Briefs."""

    state: dict[str, Any] = {} if state_sink is None else state_sink
    prior_packet = await run_correction_detection_delay_outcome(
        workspace_root,
        state_sink=state,
        before_correction=before_correction,
    )
    environment = state["environment"]
    material = _build_briefs(state)
    prior_ref = await _append_brief(state, brief=material["prior"], role="prior")
    treatment_ref = await _append_brief(state, brief=material["treatment"], role="treatment")
    control_ref = await _append_brief(state, brief=material["control"], role="drift-control")
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
    if state["clock"].current <= CRITERION_FROZEN_AT:
        state["clock"].set(CRITERION_FROZEN_AT + timedelta(seconds=1))
    treatment_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=treatment_ref,
                content=material["treatment"].body_markdown,
                pair_index=index,
                variant="correction-revision-treatment",
            )
            for index in (1, 2)
        ]
    )
    control_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=control_ref,
                content=material["control"].body_markdown,
                pair_index=index,
                variant="correction-revision-control",
            )
            for index in (1, 2)
        ]
    )
    evidence: list[ImpactEvidenceV1Alpha1] = []
    treatment_reviews: list[BriefRevisionStabilityReviewV1Alpha1] = []
    control_reviews: list[BriefRevisionStabilityReviewV1Alpha1] = []
    observed_times: list[datetime] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=treatment_ref,
            pair_index=index,
            variant="correction-revision-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="correction-revision-control",
        )
        treatment_review, treatment_review_ref = await _review_revision(
            state,
            material=material,
            prior_ref=prior_ref,
            revised_ref=treatment_ref,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_revision(
            state,
            material=material,
            prior_ref=prior_ref,
            revised_ref=control_ref,
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
            condition_key=f"world-recorded-correction-revision-stability-pair:{index}",
            route_id="world:fcc-recorded-correction-revision-review",
            context_json=canonical_json(
                {
                    "fixture_digest": correction_fixture_digest(state["p2c7_fixture"]),
                    "pair_index": index,
                    "prior_brief": prior_ref.model_dump(mode="json"),
                    "review_policy_digest": treatment_review.policy_digest,
                    "task": "exact_correction_update_with_unaffected_claim_identity_preservation",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT,
            observation_window_end=max(observed_times),
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-recorded-correction-revision-stability:{index}",
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
        evaluation_key="world-recorded-correction-revision-stability:fcc-2021-10670",
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
        raise AssertionError("revision-stability evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError(
            "frozen revision-stability criterion did not classify useful: "
            f"{admission.evaluation.model_dump(mode='json')}"
        )
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("revision-stability result did not emit its proposal-only mapping")
    if {item.revision_stability_score for item in treatment_reviews} != {1.0}:
        raise AssertionError("treatment did not preserve every unaffected claim identity")
    if {item.revision_stability_score for item in control_reviews} != {0.0}:
        raise AssertionError("drift control did not expose gratuitous unrelated revision")
    if {item.affected_update_correct for item in (*treatment_reviews, *control_reviews)} != {True}:
        raise AssertionError("one revision lost the exact correction update")
    if {item.source_coverage_complete for item in (*treatment_reviews, *control_reviews)} != {True}:
        raise AssertionError("one revision changed exact source coverage")

    state.update(
        {
            "p2c8_prior_brief": material["prior"],
            "p2c8_prior_brief_ref": prior_ref,
            "p2c8_treatment_brief": material["treatment"],
            "p2c8_treatment_brief_ref": treatment_ref,
            "p2c8_control_brief": material["control"],
            "p2c8_control_brief_ref": control_ref,
        }
    )
    return {
        "contract": "ace.world-intelligence.correction-revision-stability-outcome/v1alpha1",
        "prior_correction_detection": prior_packet,
        "source_pair": {
            "fixture_id": state["p2c7_fixture"]["fixture_id"],
            "fixture_digest": correction_fixture_digest(state["p2c7_fixture"]),
            "original_observation_id": str(state["p2c7_original_observation"].resource_id),
            "correction_observation_id": str(state["p2c7_correction_observation"].resource_id),
        },
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "score_rule": (
                "unaffected preservation rate gated by exact correction update, correction visibility, "
                "source coverage, and claim-count preservation"
            ),
        },
        "briefs": {
            "prior": material["prior"].model_dump(mode="json"),
            "treatment": material["treatment"].model_dump(mode="json"),
            "control": material["control"].model_dump(mode="json"),
        },
        "expected_revision": {
            "affected_claim_id": str(material["affected_claim"].claim_id),
            "replacement_claim_id": str(material["replacement_claim"].claim_id),
            "stable_claim_ids": tuple(sorted(str(item.claim_id) for item in material["stable_claims"])),
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
            "actual_brief_contracts": True,
            "exact_correction_update_reviewed": True,
            "unaffected_claim_identity_preservation_reviewed": True,
            "equal_source_coverage_control": True,
            "equal_claim_count_control": True,
            "network_access": False,
            "live_revision_claimed": False,
            "semantic_equivalence_engine_claimed": False,
            "population_revision_stability_claimed": False,
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
            asyncio.run(run_correction_revision_stability_outcome(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
