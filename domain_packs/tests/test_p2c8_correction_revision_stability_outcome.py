from __future__ import annotations

import copy
import importlib.util
import json

import pytest
from pydantic import ValidationError


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C8 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C8 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C8 requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_exact_brief_revision_review_becomes_a_measured_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c8_correction_revision_stability_outcome import run_correction_revision_stability_outcome

    result = await run_correction_revision_stability_outcome(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-revision-stability-reviewer"
    assert result["evaluation"]["criterion"]["requires_observed_result"] is True
    assert result["evaluation"]["classification"] == "useful"
    assert result["evaluation"]["matched_pair_count"] == 2
    assert result["evaluation"]["mean_effect"] == 1.0
    assert result["proposal"]["action"] == "promote"
    assert result["proposal"]["live_effect"] is False
    assert result["proposal"]["selectable"] is False
    assert result["proposal"]["requires_human_review"] is True
    assert result["replay"]["historical"] is True
    assert result["replay"]["no_reauthorization"] is True
    assert {item["contract"] for item in result["briefs"].values()} == {"ace.intelligence.brief/v1alpha1"}


@pytest.mark.asyncio
async def test_equal_coverage_control_isolates_unaffected_claim_identity_stability(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c8_correction_revision_stability_outcome import run_correction_revision_stability_outcome

    result = await run_correction_revision_stability_outcome(tmp_path)
    prior = result["briefs"]["prior"]
    treatment = result["briefs"]["treatment"]
    control = result["briefs"]["control"]
    expected = result["expected_revision"]
    treatment_reviews = result["observed_results"]["treatment"]
    control_reviews = result["observed_results"]["control"]

    assert len(prior["claims"]) == len(treatment["claims"]) == len(control["claims"]) == 3
    assert len(treatment["citations"]) == len(control["citations"]) == 2
    assert {item["affected_update_correct"] for item in (*treatment_reviews, *control_reviews)} == {True}
    assert {item["correction_visible"] for item in (*treatment_reviews, *control_reviews)} == {True}
    assert {item["source_coverage_complete"] for item in (*treatment_reviews, *control_reviews)} == {True}
    assert {item["claim_count_preserved"] for item in (*treatment_reviews, *control_reviews)} == {True}
    assert {tuple(item["preserved_stable_claim_ids"]) for item in treatment_reviews} == {
        tuple(expected["stable_claim_ids"])
    }
    assert {tuple(item["drifted_stable_claim_ids"]) for item in treatment_reviews} == {()}
    assert {tuple(item["preserved_stable_claim_ids"]) for item in control_reviews} == {()}
    assert {tuple(item["drifted_stable_claim_ids"]) for item in control_reviews} == {
        tuple(expected["stable_claim_ids"])
    }
    assert {item["revision_stability_score"] for item in treatment_reviews} == {1.0}
    assert {item["revision_stability_score"] for item in control_reviews} == {0.0}


@pytest.mark.asyncio
async def test_revised_briefs_name_the_prior_and_exact_correction_without_rewriting_history(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c8_correction_revision_stability_outcome import run_correction_revision_stability_outcome

    result = await run_correction_revision_stability_outcome(tmp_path)
    prior = result["briefs"]["prior"]
    expected = result["expected_revision"]
    source_pair = result["source_pair"]

    for variant in ("treatment", "control"):
        revised = result["briefs"][variant]
        lineage_ids = {item["resource_id"] for item in revised["lineage"]}
        claim_ids = {item["claim_id"] for item in revised["claims"]}
        assert prior["resource_id"] in lineage_ids
        assert source_pair["original_observation_id"] in lineage_ids
        assert source_pair["correction_observation_id"] in lineage_ids
        assert expected["affected_claim_id"] not in claim_ids
        assert expected["replacement_claim_id"] in claim_ids
    assert result["scope"]["actual_brief_contracts"] is True
    assert result["scope"]["unaffected_claim_identity_preservation_reviewed"] is True
    assert result["scope"]["live_revision_claimed"] is False
    assert result["scope"]["semantic_equivalence_engine_claimed"] is False
    assert result["scope"]["proposal_applied"] is False


@pytest.mark.asyncio
async def test_duplicate_claims_missing_correction_visibility_and_invented_scores_fail_closed(tmp_path) -> None:
    _require_candidate_contracts()
    from ace.intelligence import BriefV1Alpha1

    from scripts.p2c8_correction_revision_stability_outcome import (
        BriefRevisionStabilityReviewV1Alpha1,
        run_correction_revision_stability_outcome,
    )

    result = await run_correction_revision_stability_outcome(tmp_path)
    duplicate = copy.deepcopy(result["briefs"]["treatment"])
    duplicate["claims"] = [duplicate["claims"][0], duplicate["claims"][0], duplicate["claims"][2]]
    duplicate["resource_id"] = None
    duplicate["resource_digest"] = None
    with pytest.raises(ValidationError, match="unique content identities"):
        BriefV1Alpha1.model_validate_json(json.dumps(duplicate))

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["correction_visible"] = False
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="score differs from frozen product rule"):
        BriefRevisionStabilityReviewV1Alpha1.model_validate_json(json.dumps(review))

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["preserved_stable_claim_ids"] = review["preserved_stable_claim_ids"][:1]
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="exactly partition stable claims"):
        BriefRevisionStabilityReviewV1Alpha1.model_validate_json(json.dumps(review))


@pytest.mark.asyncio
async def test_packet_briefs_and_classification_are_deterministic_across_fresh_hosts(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c8_correction_revision_stability_outcome import run_correction_revision_stability_outcome

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = await run_correction_revision_stability_outcome(first_root)
    second = await run_correction_revision_stability_outcome(second_root)

    assert first["source_pair"] == second["source_pair"]
    assert first["expected_revision"] == second["expected_revision"]
    for variant in ("prior", "treatment", "control"):
        assert first["briefs"][variant]["resource_id"] == second["briefs"][variant]["resource_id"]
        assert first["briefs"][variant]["resource_digest"] == second["briefs"][variant]["resource_digest"]
    for variant in ("treatment", "control"):
        first_scores = [item["revision_stability_score"] for item in first["observed_results"][variant]]
        second_scores = [item["revision_stability_score"] for item in second["observed_results"][variant]]
        assert first_scores == second_scores
    for field in ("classification", "matched_pair_count", "mean_effect"):
        assert first["evaluation"][field] == second["evaluation"][field]
    for field in ("action", "live_effect", "selectable", "requires_human_review"):
        assert first["proposal"][field] == second["proposal"][field]
