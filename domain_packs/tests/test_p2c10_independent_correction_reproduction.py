from __future__ import annotations

import copy
import importlib.util
import json

import pytest
from pydantic import ValidationError


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C10 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C10 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C10 requires the separately packaged Core reference adapter")


def test_recorded_bls_fixture_freezes_an_independent_exact_correction_pair() -> None:
    _require_candidate_contracts()
    from scripts.p2c10_independent_correction_reproduction import (
        bls_correction_fixture_digest,
        load_bls_correction_fixture,
    )

    fixture = load_bls_correction_fixture()

    assert fixture["network_access"] is False
    assert fixture["source_policy"]["source_family"] == "bls_public_errata"
    assert fixture["source_policy"]["historical_original_form_derived_from_erratum"] is True
    assert fixture["original"]["record_id"] == "USDL-25-1087"
    assert fixture["correction"]["corrects_record_id"] == fixture["original"]["record_id"]
    assert fixture["original"]["reported_sentence_without_required_minus_sign"].endswith("(39,000).")
    assert fixture["correction"]["corrected_sentence"].endswith("(−39,000).")
    assert fixture["original"]["release_uri"].startswith("https://www.bls.gov/")
    assert fixture["correction"]["errata_uri"] == "https://www.bls.gov/errata/"
    assert (
        bls_correction_fixture_digest(fixture)
        == "sha256:981183a2464f74f4421bd0a6470f0342a5abae8cfebc1b5a8da1562df26babb1"
    )


@pytest.mark.asyncio
async def test_independent_source_correction_becomes_an_exact_measured_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c10_independent_correction_reproduction import run_independent_correction_reproduction

    result = await run_independent_correction_reproduction(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-independent-correction-reviewer"
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
    assert result["scope"]["independent_source_family_reproduction"] is True
    assert result["scope"]["domain_neutral_core_contract_unchanged"] is True


@pytest.mark.asyncio
async def test_source_coverage_linkage_and_reviewed_workflow_are_matched(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c10_independent_correction_reproduction import run_independent_correction_reproduction

    result = await run_independent_correction_reproduction(tmp_path)
    treatment_artifact = result["artifacts"]["treatment"]
    control_artifact = result["artifacts"]["control"]
    treatment_reviews = result["observed_results"]["treatment"]
    control_reviews = result["observed_results"]["control"]

    assert treatment_artifact["original_observation"] == control_artifact["original_observation"]
    assert treatment_artifact["correction_observation"] == control_artifact["correction_observation"]
    assert treatment_artifact["corrects_source_record_id"] == control_artifact["corrects_source_record_id"]
    for reviews in (treatment_reviews, control_reviews):
        assert {item["source_coverage_complete"] for item in reviews} == {True}
        assert {item["correction_link_visible"] for item in reviews} == {True}
        assert {item["prior_record_preserved"] for item in reviews} == {True}
    assert {item["corrected_statement_exact"] for item in treatment_reviews} == {True}
    assert {item["stale_form_present"] for item in treatment_reviews} == {False}
    assert {item["correction_quality_score"] for item in treatment_reviews} == {1.0}
    assert {item["corrected_statement_exact"] for item in control_reviews} == {False}
    assert {item["stale_form_present"] for item in control_reviews} == {True}
    assert {item["correction_quality_score"] for item in control_reviews} == {0.0}
    assert result["scope"]["prior_record_preserved"] is True
    assert result["scope"]["network_access"] is False
    assert result["scope"]["population_correction_performance_claimed"] is False


@pytest.mark.asyncio
async def test_drifted_source_link_duplicate_identity_and_invented_score_fail_closed(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c10_independent_correction_reproduction import (
        IndependentCorrectionReviewV1Alpha1,
        OfficialCorrectionArtifactV1Alpha1,
        load_bls_correction_fixture,
        run_independent_correction_reproduction,
        validate_bls_correction_fixture,
    )

    fixture = copy.deepcopy(load_bls_correction_fixture())
    fixture["correction"]["corrects_record_id"] = "USDL-OTHER"
    with pytest.raises(AssertionError, match="correction linkage changed"):
        validate_bls_correction_fixture(fixture)

    fixture = copy.deepcopy(load_bls_correction_fixture())
    fixture["source_policy"]["statistical_validity_claimed"] = True
    with pytest.raises(AssertionError, match="source policy changed"):
        validate_bls_correction_fixture(fixture)

    result = await run_independent_correction_reproduction(tmp_path)
    artifact = copy.deepcopy(result["artifacts"]["treatment"])
    artifact["corrects_source_record_id"] = "USDL-OTHER"
    artifact["artifact_id"] = None
    artifact["artifact_digest"] = None
    with pytest.raises(ValidationError, match="lost its exact correction linkage"):
        OfficialCorrectionArtifactV1Alpha1.model_validate_json(json.dumps(artifact))

    artifact = copy.deepcopy(result["artifacts"]["treatment"])
    artifact["correction_observation"] = artifact["original_observation"]
    artifact["artifact_id"] = None
    artifact["artifact_digest"] = None
    with pytest.raises(ValidationError, match="requires distinct exact source records"):
        OfficialCorrectionArtifactV1Alpha1.model_validate_json(json.dumps(artifact))

    artifact = copy.deepcopy(result["artifacts"]["treatment"])
    artifact["displayed_statement"] = "The estimate was corrected."
    artifact["artifact_id"] = None
    artifact["artifact_digest"] = None
    with pytest.raises(ValidationError, match="introduced an unreviewed statement form"):
        OfficialCorrectionArtifactV1Alpha1.model_validate_json(json.dumps(artifact))

    review = copy.deepcopy(result["observed_results"]["control"][0])
    review["correction_quality_score"] = 1.0
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="score differs from the frozen product rule"):
        IndependentCorrectionReviewV1Alpha1.model_validate_json(json.dumps(review))


@pytest.mark.asyncio
async def test_independent_reproduction_is_substantively_deterministic_across_fresh_hosts(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c10_independent_correction_reproduction import run_independent_correction_reproduction

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = await run_independent_correction_reproduction(first_root)
    second = await run_independent_correction_reproduction(second_root)

    assert first["source_pair"]["fixture_digest"] == second["source_pair"]["fixture_digest"]
    assert first["review_policy"]["policy_id"] == second["review_policy"]["policy_id"]
    assert first["review_policy"]["policy_version"] == second["review_policy"]["policy_version"]
    for variant in ("treatment", "control"):
        first_scores = [item["correction_quality_score"] for item in first["observed_results"][variant]]
        second_scores = [item["correction_quality_score"] for item in second["observed_results"][variant]]
        assert first_scores == second_scores
    for field in ("classification", "matched_pair_count", "mean_effect"):
        assert first["evaluation"][field] == second["evaluation"][field]
    for field in ("action", "live_effect", "selectable", "requires_human_review"):
        assert first["proposal"][field] == second["proposal"][field]
