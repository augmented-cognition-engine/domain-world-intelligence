from __future__ import annotations

import copy
import importlib.util
import json

import pytest
from pydantic import ValidationError


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C6 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C6 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C6 requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_exact_contradiction_attention_review_becomes_a_measured_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c6_contradiction_attention_outcome import run_contradiction_attention_outcome

    result = await run_contradiction_attention_outcome(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-contradiction-attention-reviewer"
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
    reviews = (*result["observed_results"]["treatment"], *result["observed_results"]["control"])
    assert {item["contract"] for item in reviews} == {"ace.world-intelligence.contradiction-attention-review/v1alpha1"}
    assert {len(item["source_observations"]) for item in reviews} == {2}


@pytest.mark.asyncio
async def test_equal_alert_volume_separates_recall_false_alerts_and_valid_silence(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c6_contradiction_attention_outcome import run_contradiction_attention_outcome

    result = await run_contradiction_attention_outcome(tmp_path)
    challenge = result["challenge"]
    treatments = result["observed_results"]["treatment"]
    controls = result["observed_results"]["control"]

    assert challenge["treatment_alert_volume"] == challenge["control_alert_volume"] == 1
    assert challenge["contradiction_candidate_id"] != challenge["valid_comparator_id"]
    assert {item["contradiction_recall"] for item in treatments} == {1.0}
    assert {item["false_alert_rate"] for item in treatments} == {0.0}
    assert {item["quality_score"] for item in treatments} == {1.0}
    assert {item["valid_silence_count"] for item in treatments} == {1}
    assert {item["true_positive_count"] for item in treatments} == {1}
    assert {item["true_negative_count"] for item in treatments} == {1}
    assert {item["contradiction_recall"] for item in controls} == {0.0}
    assert {item["false_alert_rate"] for item in controls} == {1.0}
    assert {item["quality_score"] for item in controls} == {0.0}
    assert {item["false_negative_count"] for item in controls} == {1}
    assert {item["false_positive_count"] for item in controls} == {1}
    assert result["scope"]["equal_alert_volume_control"] is True
    assert result["scope"]["valid_silence_measured"] is True
    assert result["scope"]["live_public_conflict_claimed"] is False
    assert result["scope"]["population_false_alert_rate_claimed"] is False


@pytest.mark.asyncio
async def test_duplicate_candidates_and_invented_scores_fail_closed(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c6_contradiction_attention_outcome import (
        ContradictionAttentionArtifactV1Alpha1,
        ContradictionAttentionReviewV1Alpha1,
        run_contradiction_attention_outcome,
    )

    result = await run_contradiction_attention_outcome(tmp_path)
    artifact = copy.deepcopy(result["artifacts"]["treatment"])
    artifact["decisions"] = [artifact["decisions"][0], artifact["decisions"][0]]
    artifact["artifact_id"] = None
    artifact["artifact_digest"] = None
    with pytest.raises(ValidationError, match="duplicated a candidate identity"):
        ContradictionAttentionArtifactV1Alpha1.model_validate(artifact)

    review = copy.deepcopy(result["observed_results"]["treatment"][0])
    review["quality_score"] = 0.5
    review["review_id"] = None
    review["review_digest"] = None
    with pytest.raises(ValidationError, match="quality score differs"):
        ContradictionAttentionReviewV1Alpha1.model_validate_json(json.dumps(review))


@pytest.mark.asyncio
async def test_packet_classification_is_deterministic_across_fresh_hosts(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c6_contradiction_attention_outcome import run_contradiction_attention_outcome

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first = await run_contradiction_attention_outcome(first_root)
    second = await run_contradiction_attention_outcome(second_root)

    assert first["challenge"] == second["challenge"]
    for variant in ("treatment", "control"):
        assert first["artifacts"][variant]["decisions"] == second["artifacts"][variant]["decisions"]
        assert first["artifacts"][variant]["emitted_alert_count"] == second["artifacts"][variant]["emitted_alert_count"]
        first_metrics = [
            (
                item["contradiction_recall"],
                item["false_alert_rate"],
                item["quality_score"],
                item["valid_silence_count"],
            )
            for item in first["observed_results"][variant]
        ]
        second_metrics = [
            (
                item["contradiction_recall"],
                item["false_alert_rate"],
                item["quality_score"],
                item["valid_silence_count"],
            )
            for item in second["observed_results"][variant]
        ]
        assert first_metrics == second_metrics
    for field in ("classification", "matched_pair_count", "mean_effect"):
        assert first["evaluation"][field] == second["evaluation"][field]
    for field in ("action", "live_effect", "selectable", "requires_human_review"):
        assert first["proposal"][field] == second["proposal"][field]
