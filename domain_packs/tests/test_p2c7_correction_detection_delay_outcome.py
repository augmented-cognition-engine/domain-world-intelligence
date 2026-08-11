from __future__ import annotations

import copy
import importlib.util
import json

import pytest
from pydantic import ValidationError


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C7 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C7 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C7 requires the separately packaged Core reference adapter")


def test_recorded_correction_fixture_names_one_exact_official_pair() -> None:
    _require_candidate_contracts()
    from scripts.p2c7_correction_detection_delay_outcome import correction_fixture_digest, load_correction_fixture

    fixture = load_correction_fixture()

    assert fixture["network_access"] is False
    assert fixture["original"]["document_number"] == "2020-28779"
    assert fixture["correction"]["document_number"] == "2021-10670"
    assert fixture["correction"]["corrects_document_number"] == fixture["original"]["document_number"]
    assert fixture["correction"]["corrected_page"] == 85530
    assert fixture["recorded_replay"] == {
        "correction_available_at": "2021-05-20T00:00:00Z",
        "treatment_detected_at": "2021-05-20T00:05:00Z",
        "control_detected_at": "2021-05-20T06:00:00Z",
        "target_detection_delay_seconds": 600,
    }
    assert fixture["source_policy"] == {
        "display_source": "FederalRegister.gov",
        "display_source_is_official_legal_edition": False,
        "official_format_source": "govinfo.gov",
        "legal_truth_claimed": False,
    }
    assert (
        correction_fixture_digest(fixture) == "sha256:2b81d3950cbfd127408eec227ec5cd249677a189120d6ca7b603d85d01074543"
    )


@pytest.mark.asyncio
async def test_exact_correction_review_becomes_a_measured_detection_delay_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c7_correction_detection_delay_outcome import run_correction_detection_delay_outcome

    result = await run_correction_detection_delay_outcome(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-correction-delay-reviewer"
    assert result["review_policy"]["target_detection_delay_seconds"] == 600
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
    assert result["source_pair"]["original"]["document_number"] == "2020-28779"
    assert result["source_pair"]["correction"]["corrects_document_number"] == "2020-28779"


@pytest.mark.asyncio
async def test_matched_replay_separates_correction_semantics_from_detection_timeliness(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c7_correction_detection_delay_outcome import run_correction_detection_delay_outcome

    result = await run_correction_detection_delay_outcome(tmp_path)
    treatments = result["observed_results"]["treatment"]
    controls = result["observed_results"]["control"]

    for reviews in (treatments, controls):
        assert {item["linkage_correct"] for item in reviews} == {True}
        assert {item["instruction_correct"] for item in reviews} == {True}
        assert {item["prior_record_preserved"] for item in reviews} == {True}
    assert {item["detection_delay_seconds"] for item in treatments} == {300}
    assert {item["within_target"] for item in treatments} == {True}
    assert {item["timeliness_score"] for item in treatments} == {1.0}
    assert {item["detection_delay_seconds"] for item in controls} == {21_600}
    assert {item["within_target"] for item in controls} == {False}
    assert {item["timeliness_score"] for item in controls} == {0.0}
    assert result["scope"]["prior_record_preserved"] is True
    assert result["scope"]["live_monitoring_claimed"] is False
    assert result["scope"]["network_arrival_delay_claimed"] is False
    assert result["scope"]["population_detection_performance_claimed"] is False


@pytest.mark.asyncio
async def test_preavailability_detection_and_invented_review_score_fail_closed(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c7_correction_detection_delay_outcome import (
        CorrectionDetectionReviewV1Alpha1,
        CorrectionHandlingArtifactV1Alpha1,
        run_correction_detection_delay_outcome,
    )

    result = await run_correction_detection_delay_outcome(tmp_path)
    artifact = copy.deepcopy(result["artifacts"]["treatment"])
    artifact["detected_at"] = "2021-05-19T23:59:59Z"
    artifact["detection_delay_seconds"] = 0
    artifact["artifact_id"] = None
    artifact["artifact_digest"] = None
    with pytest.raises(ValidationError, match="cannot precede correction availability"):
        CorrectionHandlingArtifactV1Alpha1.model_validate_json(json.dumps(artifact))

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["timeliness_score"] = 0.0
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="score differs from frozen product rule"):
        CorrectionDetectionReviewV1Alpha1.model_validate_json(json.dumps(review))


@pytest.mark.asyncio
async def test_packet_classification_is_deterministic_across_fresh_hosts(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c7_correction_detection_delay_outcome import run_correction_detection_delay_outcome

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = await run_correction_detection_delay_outcome(first_root)
    second = await run_correction_detection_delay_outcome(second_root)

    assert first["source_pair"]["fixture_digest"] == second["source_pair"]["fixture_digest"]
    assert first["review_policy"]["policy_id"] == second["review_policy"]["policy_id"]
    assert first["review_policy"]["policy_version"] == second["review_policy"]["policy_version"]
    for variant in ("treatment", "control"):
        assert (
            first["artifacts"][variant]["detection_delay_seconds"]
            == second["artifacts"][variant]["detection_delay_seconds"]
        )
        first_scores = [item["timeliness_score"] for item in first["observed_results"][variant]]
        second_scores = [item["timeliness_score"] for item in second["observed_results"][variant]]
        assert first_scores == second_scores
    for field in ("classification", "matched_pair_count", "mean_effect"):
        assert first["evaluation"][field] == second["evaluation"][field]
    for field in ("action", "live_effect", "selectable", "requires_human_review"):
        assert first["proposal"][field] == second["proposal"][field]
