from __future__ import annotations

import copy
import importlib.util
import json

import pytest
from pydantic import ValidationError


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C9 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C9 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C9 requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_exact_withheld_forecast_result_becomes_a_measured_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c9_forecast_calibration_outcome import run_forecast_calibration_outcome

    result = await run_forecast_calibration_outcome(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-forecast-calibration-reviewer"
    assert result["evaluation"]["criterion"]["requires_observed_result"] is True
    assert result["evaluation"]["classification"] == "useful"
    assert result["evaluation"]["matched_pair_count"] == 2
    assert result["evaluation"]["mean_effect"] == 0.5
    assert result["proposal"]["action"] == "promote"
    assert result["proposal"]["live_effect"] is False
    assert result["proposal"]["selectable"] is False
    assert result["proposal"]["requires_human_review"] is True
    assert result["replay"] == {
        "historical": True,
        "no_reauthorization": True,
        "transaction_receipt_id": result["replay"]["transaction_receipt_id"],
    }


@pytest.mark.asyncio
async def test_forecast_material_excludes_the_later_exact_result_and_conditions_match(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c9_forecast_calibration_outcome import run_forecast_calibration_outcome

    result = await run_forecast_calibration_outcome(tmp_path)
    treatment = result["forecasts"]["treatment"]
    control = result["forecasts"]["control"]
    reviews = (*result["observed_results"]["treatment"], *result["observed_results"]["control"])

    assert treatment["basis_observations"] == control["basis_observations"]
    assert treatment["target_event_key"] == control["target_event_key"]
    assert treatment["target_event_definition_json"] == control["target_event_definition_json"]
    assert treatment["policy_digest"] == control["policy_digest"]
    assert treatment["probability"] == 0.75
    assert control["probability"] == 0.25
    assert "2021-10670" not in json.dumps(treatment, sort_keys=True)
    assert "2021-10670" not in json.dumps(control, sort_keys=True)
    assert all(item["result_withheld_until_after_forecast"] for item in reviews)
    assert all(item["reviewed_forecast"]["available_at"] < item["observed_result"]["available_at"] for item in reviews)
    assert result["source_event"]["result_available_after_forecasts"] is True
    assert result["source_event"]["result_available_after_reviewed_actions"] is True
    assert (
        result["source_event"]["latest_forecast_action_completed_at"]
        < result["source_event"]["observed_result"]["available_at"]
    )


@pytest.mark.asyncio
async def test_single_event_brier_contribution_is_derived_not_asserted(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c9_forecast_calibration_outcome import run_forecast_calibration_outcome

    result = await run_forecast_calibration_outcome(tmp_path)
    treatment = result["observed_results"]["treatment"]
    control = result["observed_results"]["control"]

    assert {item["event_outcome"] for item in (*treatment, *control)} == {1.0}
    assert {item["explicit_correction_linkage_verified"] for item in (*treatment, *control)} == {True}
    assert {item["brier_loss"] for item in treatment} == {0.0625}
    assert {item["brier_quality_score"] for item in treatment} == {0.9375}
    assert {item["brier_loss"] for item in control} == {0.5625}
    assert {item["brier_quality_score"] for item in control} == {0.4375}
    assert result["scope"]["population_calibration_claimed"] is False
    assert result["scope"]["probability_generated_by_ace_claimed"] is False
    assert result["scope"]["historically_contemporaneous_forecast_claimed"] is False


@pytest.mark.asyncio
async def test_leaked_basis_missing_withholding_and_invented_brier_material_fail_closed(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c9_forecast_calibration_outcome import (
        ForecastResolutionReviewV1Alpha1,
        PublicEventForecastV1Alpha1,
        run_forecast_calibration_outcome,
    )

    result = await run_forecast_calibration_outcome(tmp_path)
    forecast = copy.deepcopy(result["forecasts"]["treatment"])
    forecast["probability"] = 1.1
    forecast["forecast_id"] = None
    forecast["forecast_digest"] = None
    with pytest.raises(ValidationError):
        PublicEventForecastV1Alpha1.model_validate_json(json.dumps(forecast))

    forecast = copy.deepcopy(result["forecasts"]["treatment"])
    forecast["basis_observations"][0]["available_at"] = forecast["resolution_window_end"]
    forecast["forecast_id"] = None
    forecast["forecast_digest"] = None
    with pytest.raises(ValidationError, match="basis includes evidence unavailable"):
        PublicEventForecastV1Alpha1.model_validate_json(json.dumps(forecast))

    forecast = copy.deepcopy(result["forecasts"]["treatment"])
    forecast["observed_result"] = result["source_event"]["observed_result"]
    forecast["forecast_id"] = None
    forecast["forecast_digest"] = None
    with pytest.raises(ValidationError):
        PublicEventForecastV1Alpha1.model_validate_json(json.dumps(forecast))

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["brier_quality_score"] = 1.0
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="Brier material differs"):
        ForecastResolutionReviewV1Alpha1.model_validate_json(json.dumps(review))

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["result_withheld_until_after_forecast"] = False
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="result was not withheld"):
        ForecastResolutionReviewV1Alpha1.model_validate_json(json.dumps(review))


@pytest.mark.asyncio
async def test_forecast_material_scores_and_classification_are_deterministic_across_fresh_hosts(
    tmp_path,
) -> None:
    _require_candidate_contracts()
    from scripts.p2c9_forecast_calibration_outcome import run_forecast_calibration_outcome

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = await run_forecast_calibration_outcome(first_root)
    second = await run_forecast_calibration_outcome(second_root)

    assert first["source_event"]["fixture_id"] == second["source_event"]["fixture_id"]
    assert first["source_event"]["fixture_digest"] == second["source_event"]["fixture_digest"]
    for coordinate in ("original_observation", "observed_result"):
        for field in ("record_key", "payload_contract"):
            assert first["source_event"][coordinate][field] == second["source_event"][coordinate][field]
    for variant in ("treatment", "control"):
        for field in (
            "target_event_key",
            "target_event_definition_json",
            "probability",
            "policy_id",
            "policy_version",
            "limitations",
        ):
            assert first["forecasts"][variant][field] == second["forecasts"][variant][field]
        first_scores = [
            (
                item["forecast_probability"],
                item["event_outcome"],
                item["brier_loss"],
                item["brier_quality_score"],
                item["explicit_correction_linkage_verified"],
                item["result_withheld_until_after_forecast"],
            )
            for item in first["observed_results"][variant]
        ]
        second_scores = [
            (
                item["forecast_probability"],
                item["event_outcome"],
                item["brier_loss"],
                item["brier_quality_score"],
                item["explicit_correction_linkage_verified"],
                item["result_withheld_until_after_forecast"],
            )
            for item in second["observed_results"][variant]
        ]
        assert first_scores == second_scores
    for field in (
        "classification",
        "matched_pair_count",
        "mean_effect",
        "treatment_mean",
        "control_mean",
    ):
        assert first["evaluation"][field] == second["evaluation"][field]
    for field in ("action", "live_effect", "selectable", "requires_human_review"):
        assert first["proposal"][field] == second["proposal"][field]
