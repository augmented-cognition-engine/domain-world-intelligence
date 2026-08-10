"""Independently review exact citation correctness and measure its impact."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ace.application import MeasuredImpactService
from ace.core import (
    AppendOnlyTransactionRequestV1,
    AuthenticatedRuntimeContextV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
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
from scripts.p2c4_reviewed_impact_disposition import run_reviewed_disposition

OUTCOME_TYPE = "independent_artifact_review"
MEASURE_ID = "official_citation_correctness"
CRITERION_ID = "impact_criterion:world-official-citation-correctness"
CRITERION_FROZEN_AT = _time("2026-08-07T18:01:08Z")
REVIEW_POLICY_ID = "world_official_record_citation_correctness"
REVIEW_POLICY_VERSION = "candidate-1"

IMPACT_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="measured_impact_evaluation",
    contract="ace.application.measured-impact-service/v1alpha1",
    implementation_id="world_citation_correctness_candidate",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "e" * 64,
)


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _derive_identity(value: _FrozenModel, *, prefix: str, id_field: str, digest_field: str) -> None:
    material = value.model_dump(mode="json", exclude={id_field, digest_field})
    digest = canonical_hash(material)
    expected_id = f"{prefix}:{digest[:32]}"
    expected_digest = f"sha256:{digest}"
    supplied_id = getattr(value, id_field)
    supplied_digest = getattr(value, digest_field)
    if supplied_id is not None and supplied_id != expected_id:
        raise ValueError(f"{id_field} does not match exact review material")
    if supplied_digest is not None and supplied_digest != expected_digest:
        raise ValueError(f"{digest_field} does not match exact review material")
    object.__setattr__(value, id_field, expected_id)
    object.__setattr__(value, digest_field, expected_digest)


class CitationClaimAssessmentV1Alpha1(_FrozenModel):
    """Product-owned correctness judgment for one exact cited claim."""

    contract: Literal["ace.world-intelligence.citation-claim-assessment/v1alpha1"] = (
        "ace.world-intelligence.citation-claim-assessment/v1alpha1"
    )
    claim_id: str
    statement: str
    citation_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    verdict: Literal["supported", "unsupported"]
    rationale: str
    assessment_id: str | None = None
    assessment_digest: str | None = None

    @field_validator("citation_ids")
    @classmethod
    def canonicalize_citations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        ordered = tuple(sorted(value))
        if len(ordered) != len(set(ordered)):
            raise ValueError("citation assessment cannot amplify duplicate citation identities")
        return ordered

    @model_validator(mode="after")
    def derive_identity(self) -> Self:
        _derive_identity(
            self,
            prefix="citation_claim_assessment",
            id_field="assessment_id",
            digest_field="assessment_digest",
        )
        return self


class CitationCorrectnessReviewV1Alpha1(_FrozenModel):
    """Exact independent review result later named by a Core Outcome."""

    contract: Literal["ace.world-intelligence.citation-correctness-review/v1alpha1"] = (
        "ace.world-intelligence.citation-correctness-review/v1alpha1"
    )
    product_id: str
    review_key: str
    reviewed_subject: ImmutableRecordReferenceV1
    reviewer_context: AuthenticatedRuntimeContextV1Alpha1
    policy_id: str
    policy_version: str
    policy_digest: str
    source_observations: tuple[ImmutableRecordReferenceV1, ...] = Field(min_length=1, max_length=16)
    assessments: tuple[CitationClaimAssessmentV1Alpha1, ...] = Field(min_length=1, max_length=16)
    citation_coverage: float = Field(ge=0.0, le=1.0)
    correctness_score: float = Field(ge=0.0, le=1.0)
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
        identities = tuple(item.storage_id for item in ordered)
        if len(identities) != len(set(identities)):
            raise ValueError("citation review cannot amplify duplicate Observation identities")
        return ordered

    @model_validator(mode="after")
    def validate_scope_scores_and_identity(self) -> Self:
        if (
            self.reviewed_subject.product_id != self.product_id
            or self.reviewer_context.product_id != self.product_id
            or any(item.product_id != self.product_id for item in self.source_observations)
        ):
            raise ValueError("citation correctness review crossed exact product scope")
        if len({item.assessment_id for item in self.assessments}) != len(self.assessments):
            raise ValueError("citation correctness review duplicated an assessment identity")
        expected_score = sum(item.verdict == "supported" for item in self.assessments) / len(self.assessments)
        if self.correctness_score != expected_score:
            raise ValueError("citation correctness score differs from exact assessments")
        _derive_identity(
            self,
            prefix="citation_correctness_review",
            id_field="review_id",
            digest_field="review_digest",
        )
        return self


class _ReplayMustNotAuthorize:
    async def authorize_action(self, request):
        raise AssertionError(f"historical citation evaluation requested new authority: {request.authorization_key}")


def _install_policy(state: dict[str, Any]):
    environment = state["environment"]
    runtime = state["runtime"]
    product_id = environment.fixture["product_id"]
    criterion_head = _head(product_id, "impact_criterion", CRITERION_ID, 60)
    operation_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-citation-correctness",
        61,
    )
    binding = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=IMPACT_ARTIFACT,
        configuration_ref=operation_head.state_id,
        authority="append_measured_impact",
        grant_ref="authority_grant:world-citation-correctness",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(operation_head),
    )
    capability_head = _head(product_id, "capability_state", capability_state_ref_for_artifact(IMPACT_ARTIFACT), 62)
    authority_head = _head(product_id, "authority_grant", binding.grant_ref, 63)
    for head in (criterion_head, operation_head, capability_head, authority_head):
        environment.store.set_governed_state_head(head)
        runtime.heads[head.state_kind, head.state_id] = head
    runtime.bindings = (*runtime.bindings, binding)
    return criterion_head, binding


async def _append_corrupted_control(
    state: dict[str, Any],
    *,
    citation_ids: tuple[str, ...],
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
    corrupted_statement: str,
) -> tuple[ImmutableRecordReferenceV1, str, tuple[dict[str, Any], ...]]:
    environment = state["environment"]
    content = (
        "# Citation-Preserving Correctness Control\n\n"
        f"{corrupted_statement}\n\n"
        f"Exact citation identities retained: {', '.join(citation_ids)}.\n\n"
        "Exact admitted Observation identities retained: "
        f"{', '.join(item.record_key for item in observation_refs)}.\n"
    )
    claims = (
        {
            "claim_id": f"corrupted_claim:{canonical_hash([corrupted_statement, citation_ids])[:32]}",
            "grounding_kind": "cited",
            "statement": corrupted_statement,
            "citation_ids": citation_ids,
        },
    )
    payload = {
        "control_type": "citation_preserving_semantic_corruption",
        "content_markdown": content,
        "claims": claims,
        "citation_ids": citation_ids,
        "observation_references": [item.model_dump(mode="json") for item in observation_refs],
        "limitations": ["synthetic_negative_control_over_exact_recorded_public_sources"],
    }
    requested_at = state["clock"]()
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key="append:world-citation-preserving-control",
        subject_ref="world_citation_preserving_control:2026-08-07",
        subject_digest=_digest(payload),
        requested_at=requested_at,
    )
    record = ImmutableRecordV1(
        product_id=environment.fixture["product_id"],
        record_space="world_intelligence",
        record_kind="brief_control",
        record_key="brief_control:citation-preserving-corruption:2026-08-07",
        payload_contract="ace.world-intelligence.citation-preserving-control/v1alpha1",
        payload=payload,
        as_of=state["impact_target_ref"].as_of,
        available_at=authorization.authorized_at,
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=record.product_id,
        record_space=record.record_space,
        transaction_key="world-citation-preserving-control:2026-08-07",
        records=(record,),
        submitted_at=record.available_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    if await environment.store.append(append) != append.receipt():
        raise AssertionError("citation-preserving control append returned divergent material")
    return record.reference(), content, claims


def _policy_digest(
    *,
    expected_statement: str,
    citation_ids: tuple[str, ...],
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
) -> str:
    return _digest(
        {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "expected_statement": expected_statement,
            "expected_citation_ids": citation_ids,
            "source_observations": [item.model_dump(mode="json") for item in observation_refs],
            "score": "supported_cited_claims / reviewed_cited_claims",
        }
    )


async def _statements_from_observations(
    state: dict[str, Any], observation_refs: tuple[ImmutableRecordReferenceV1, ...]
) -> tuple[str, str]:
    """Derive the positive and date-swapped claims from exact admitted records."""

    facts: list[tuple[str, str]] = []
    for reference in observation_refs:
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
            raise AssertionError("citation review source Observation is unavailable or changed")
        try:
            value = json.loads(record.payload["payload"]["value_json"])
            facts.append((value["document_number"], value["publication_date"]))
        except (KeyError, TypeError, json.JSONDecodeError):
            raise AssertionError("citation review Observation lost required official record facts") from None
    facts.sort()
    if len(facts) != 2 or len({number for number, _ in facts}) != 2:
        raise AssertionError("citation review requires two distinct exact official records")
    first, second = facts
    expected = (
        f"The admitted official records are {first[0]} published {first[1]} and {second[0]} published {second[1]}."
    )
    corrupted = (
        f"The admitted official records are {first[0]} published {second[1]} and {second[0]} published {first[1]}."
    )
    return expected, corrupted


async def _review_artifact(
    state: dict[str, Any],
    *,
    subject: ImmutableRecordReferenceV1,
    claims: tuple[dict[str, Any], ...],
    citation_ids: tuple[str, ...],
    observation_refs: tuple[ImmutableRecordReferenceV1, ...],
    expected_statement: str,
    pair_index: int,
    variant: str,
) -> tuple[CitationCorrectnessReviewV1Alpha1, ImmutableRecordReferenceV1]:
    environment = state["environment"]
    cited_claims = tuple(item for item in claims if item["grounding_kind"] == "cited")
    if not cited_claims:
        raise AssertionError("citation correctness review requires an exact cited claim")
    expected_ids = tuple(sorted(citation_ids))
    assessments = tuple(
        CitationClaimAssessmentV1Alpha1(
            claim_id=item["claim_id"],
            statement=item["statement"],
            citation_ids=tuple(item["citation_ids"]),
            verdict=(
                "supported"
                if item["statement"] == expected_statement and tuple(sorted(item["citation_ids"])) == expected_ids
                else "unsupported"
            ),
            rationale=(
                "The exact cited statement matches the product-frozen facts and exact citation set."
                if item["statement"] == expected_statement and tuple(sorted(item["citation_ids"])) == expected_ids
                else "Citation identities are present, but the statement contradicts the product-frozen publication dates."
            ),
        )
        for item in cited_claims
    )
    present_ids = {citation_id for item in cited_claims for citation_id in item["citation_ids"]}
    coverage = len(present_ids & set(expected_ids)) / len(expected_ids)
    reviewed_at = state["clock"]()
    reviewer = _context(environment.context, "principal:world-citation-correctness-reviewer")
    review = CitationCorrectnessReviewV1Alpha1(
        product_id=environment.fixture["product_id"],
        review_key=f"citation-correctness-review:{pair_index}:{variant}",
        reviewed_subject=subject,
        reviewer_context=reviewer,
        policy_id=REVIEW_POLICY_ID,
        policy_version=REVIEW_POLICY_VERSION,
        policy_digest=_policy_digest(
            expected_statement=expected_statement,
            citation_ids=expected_ids,
            observation_refs=observation_refs,
        ),
        source_observations=observation_refs,
        assessments=assessments,
        citation_coverage=coverage,
        correctness_score=sum(item.verdict == "supported" for item in assessments) / len(assessments),
        limitations=(
            "bounded_to_one_exact_cited_claim_and_two_recorded_official_sources",
            "does_not_establish_general_brief_quality_or_human_benefit",
        ),
        reviewed_at=reviewed_at,
    )
    authorization = await _authorize_append(
        state,
        context=reviewer,
        authorization_key=f"citation-correctness-review:{pair_index}:{variant}",
        subject_ref=str(review.review_id),
        subject_digest=str(review.review_digest),
        requested_at=reviewed_at,
    )
    reference = await _append_value(
        state,
        value=review,
        record_kind="citation_correctness_review",
        record_key=str(review.review_id),
        transaction_key=f"citation-correctness-review:{review.review_id}",
        as_of=reviewed_at,
        authorization=authorization,
    )
    return review, reference


async def _record_review_outcome(
    state: dict[str, Any],
    *,
    export: ReviewedExport,
    review: CitationCorrectnessReviewV1Alpha1,
    review_ref: ImmutableRecordReferenceV1,
    pair_index: int,
    variant: str,
) -> ImmutableRecordReferenceV1:
    environment = state["environment"]
    measures = ImpactOutcomeMeasuresV1Alpha1(
        primary_value=review.correctness_score,
        observed_result=review_ref,
        latency_ms=max(0, int((review.reviewed_at - export.intent.requested_at).total_seconds() * 1_000)),
        cost_usd=0.0,
        failure_count=0,
        degraded=False,
        limitations=review.limitations,
    )
    recorded_at = state["clock"]()
    observer = _context(environment.context, "principal:world-citation-outcome-observer")
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
        authorization_key=f"citation-correctness-outcome:{pair_index}:{variant}",
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


async def run_citation_correctness_outcome(workspace_root: Path) -> dict[str, Any]:
    """Run the P2C4 journey through exact independent citation review Outcomes."""

    state: dict[str, Any] = {}
    prior = await run_reviewed_disposition(workspace_root, state_sink=state)
    environment = state["environment"]
    target_ref = state["impact_target_ref"]
    treatment_exports = tuple(item.export for item in state["measured_treatments"])
    brief = state["brief_admission"].brief
    observation_refs = tuple(
        record
        for admission in state["admissions"]
        for record in admission.transaction_receipt.records
        if record.record_kind == "observation"
    )
    citation_ids = tuple(sorted(item.citation_id for item in brief.citations))
    treatment_claims = tuple(item.model_dump(mode="json") for item in brief.claims)
    expected_statement, corrupted_statement = await _statements_from_observations(state, observation_refs)
    control_ref, control_content, control_claims = await _append_corrupted_control(
        state,
        citation_ids=citation_ids,
        observation_refs=observation_refs,
        corrupted_statement=corrupted_statement,
    )
    control_exports = tuple(
        [
            await _run_reviewed_export(
                state,
                subject=control_ref,
                content=control_content,
                pair_index=index,
                variant="citation-control",
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
        useful_effect_threshold=0.5,
        harmful_effect_threshold=0.5,
        minimum_matched_pairs=2,
        requires_observed_result=True,
        harmful_action=ImpactGovernanceAction.ROLLBACK,
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(criterion_head),
        frozen_at=CRITERION_FROZEN_AT,
    )

    evidence: list[ImpactEvidenceV1Alpha1] = []
    treatment_reviews: list[CitationCorrectnessReviewV1Alpha1] = []
    control_reviews: list[CitationCorrectnessReviewV1Alpha1] = []
    observed_times: list[datetime] = []
    for index, (treatment_export, control_export) in enumerate(
        zip(treatment_exports, control_exports, strict=True), start=1
    ):
        treatment_attribution = await _record_attribution(
            state,
            export=treatment_export,
            subject=target_ref,
            pair_index=index,
            variant="citation-treatment",
        )
        control_attribution = await _record_attribution(
            state,
            export=control_export,
            subject=control_ref,
            pair_index=index,
            variant="citation-control",
        )
        treatment_review, treatment_review_ref = await _review_artifact(
            state,
            subject=target_ref,
            claims=treatment_claims,
            citation_ids=citation_ids,
            observation_refs=observation_refs,
            expected_statement=expected_statement,
            pair_index=index,
            variant="treatment",
        )
        control_review, control_review_ref = await _review_artifact(
            state,
            subject=control_ref,
            claims=control_claims,
            citation_ids=citation_ids,
            observation_refs=observation_refs,
            expected_statement=expected_statement,
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
            condition_key=f"world-citation-correctness-pair:{index}",
            route_id="world:fcc-independent-citation-review",
            context_json=canonical_json(
                {
                    "citation_count": len(citation_ids),
                    "pair_index": index,
                    "recorded_transport": True,
                    "review_policy_digest": treatment_review.policy_digest,
                    "task": "independent_exact_citation_correctness_review",
                }
            ),
            observation_window_start=CRITERION_FROZEN_AT + timedelta(seconds=1),
            observation_window_end=max(observed_times) + timedelta(minutes=1),
            frozen_at=CRITERION_FROZEN_AT,
        )
        evidence.append(
            ImpactEvidenceV1Alpha1(
                product_id=environment.fixture["product_id"],
                evidence_key=f"world-citation-correctness:{index}",
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

    cutoff_at = state["clock"]()
    request = ImpactEvaluationRequestV1Alpha1(
        evaluation_key="world-citation-correctness:fcc-publication-change:2026-08-07",
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
    if admission.replayed or not replay.replayed or replay.evaluation != admission.evaluation:
        raise AssertionError("citation correctness evaluation did not replay exact historical material")
    if admission.evaluation.classification is not ImpactClassification.USEFUL:
        raise AssertionError("frozen citation correctness criterion did not classify useful")
    if admission.proposal is None or admission.proposal.action is not ImpactGovernanceAction.PROMOTE:
        raise AssertionError("citation correctness result did not emit its proposal-only mapping")
    if any(item.citation_coverage != 1.0 for item in (*treatment_reviews, *control_reviews)):
        raise AssertionError("citation-preserving control lost an exact citation identity")
    if {item.correctness_score for item in treatment_reviews} != {1.0}:
        raise AssertionError("supported treatment citation did not score correct")
    if {item.correctness_score for item in control_reviews} != {0.0}:
        raise AssertionError("semantic-corruption control did not score incorrect")

    return {
        "contract": "ace.world-intelligence.citation-correctness-outcome/v1alpha1",
        "prior_reviewed_disposition": prior,
        "review_policy": {
            "policy_id": REVIEW_POLICY_ID,
            "policy_version": REVIEW_POLICY_VERSION,
            "policy_digest": treatment_reviews[0].policy_digest,
            "reviewer_ref": treatment_reviews[0].reviewer_context.actor_ref,
            "expected_statement": expected_statement,
        },
        "negative_control": {
            "control_reference": control_ref.model_dump(mode="json"),
            "corrupted_statement": corrupted_statement,
            "citation_ids_preserved": citation_ids,
            "treatment_citation_coverage": tuple(item.citation_coverage for item in treatment_reviews),
            "control_citation_coverage": tuple(item.citation_coverage for item in control_reviews),
            "treatment_correctness": tuple(item.correctness_score for item in treatment_reviews),
            "control_correctness": tuple(item.correctness_score for item in control_reviews),
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
            "independent_exact_review": True,
            "recorded_official_sources": True,
            "network_freshness_claimed": False,
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
            asyncio.run(run_citation_correctness_outcome(args.workspace_root)),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
