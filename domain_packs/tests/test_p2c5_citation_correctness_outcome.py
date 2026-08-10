from __future__ import annotations

import importlib.util

import pytest


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C5 requires the stacked ACE Core measured-impact candidate")
    from ace.intelligence import ImpactOutcomeMeasuresV1Alpha1

    if "observed_result" not in ImpactOutcomeMeasuresV1Alpha1.model_fields:
        pytest.skip("P2C5 requires exact observed-result provenance from the stacked Core candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C5 requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_independent_citation_review_becomes_an_exact_measured_outcome(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c5_citation_correctness_outcome import run_citation_correctness_outcome

    result = await run_citation_correctness_outcome(tmp_path)

    assert result["review_policy"]["reviewer_ref"] == "principal:world-citation-correctness-reviewer"
    assert result["evaluation"]["criterion"]["requires_observed_result"] is True
    assert result["evaluation"]["classification"] == "useful"
    assert result["evaluation"]["matched_pair_count"] == 2
    assert result["evaluation"]["mean_effect"] == 1.0
    assert result["proposal"]["action"] == "promote"
    assert result["proposal"]["live_effect"] is False
    assert result["proposal"]["selectable"] is False
    assert result["proposal"]["requires_human_review"] is True
    assert result["replay"] == {
        "historical": True,
        "no_reauthorization": True,
        "transaction_receipt_id": result["replay"]["transaction_receipt_id"],
    }
    reviews = (*result["observed_results"]["treatment"], *result["observed_results"]["control"])
    assert {item["contract"] for item in reviews} == {"ace.world-intelligence.citation-correctness-review/v1alpha1"}
    assert {item["reviewer_context"]["actor_ref"] for item in reviews} == {
        "principal:world-citation-correctness-reviewer"
    }
    assert {len(item["source_observations"]) for item in reviews} == {2}


@pytest.mark.asyncio
async def test_citation_preserving_negative_control_separates_coverage_from_correctness(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c5_citation_correctness_outcome import run_citation_correctness_outcome

    result = await run_citation_correctness_outcome(tmp_path)
    control = result["negative_control"]

    assert len(control["citation_ids_preserved"]) == 2
    assert control["treatment_citation_coverage"] == (1.0, 1.0)
    assert control["control_citation_coverage"] == (1.0, 1.0)
    assert control["treatment_correctness"] == (1.0, 1.0)
    assert control["control_correctness"] == (0.0, 0.0)
    assert "2026-15932 published 2026-08-07" in control["corrupted_statement"]
    assert result["scope"] == {
        "independent_exact_review": True,
        "recorded_official_sources": True,
        "network_freshness_claimed": False,
        "general_brief_quality_claimed": False,
        "human_benefit_claimed": False,
        "causality_claimed": False,
        "proposal_applied": False,
        "autonomous_publication": False,
    }
