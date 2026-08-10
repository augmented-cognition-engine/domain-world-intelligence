from __future__ import annotations

import importlib.util

import pytest


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("P2C3 candidate requires the ACE Core measured-impact contract from PR #88")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C3 candidate requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_official_record_brief_reaches_measured_proposal_only_feedback(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c3_measured_feedback import run_measured_feedback

    result = await run_measured_feedback(tmp_path)

    assert result["journey"]["intelligence"]["shift_type"] == "official_publication_change"
    assert result["journey"]["intelligence"]["signal_type"] == "official_publication"
    assert result["journey"]["intelligence"]["citation_count"] == 2
    assert result["controls"]["treatment_scores"] == (1.0, 1.0)
    assert result["controls"]["control_scores"] == (0.0, 0.0)
    assert result["evaluation"]["classification"] == "useful"
    assert result["evaluation"]["matched_pair_count"] == 2
    assert result["evaluation"]["mean_effect"] == 1.0
    assert result["proposal"]["action"] == "promote"
    assert result["proposal"]["live_effect"] is False
    assert result["proposal"]["selectable"] is False
    assert result["proposal"]["requires_human_review"] is True
    assert result["replay"]["historical"] is True
    assert result["replay"]["no_reauthorization"] is True


@pytest.mark.asyncio
async def test_measured_world_journey_keeps_its_claim_boundary_explicit(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c3_measured_feedback import run_measured_feedback

    result = await run_measured_feedback(tmp_path)

    assert result["scope"] == {
        "official_public_records": True,
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "human_benefit_claimed": False,
        "causality_claimed": False,
        "proposal_applied": False,
        "autonomous_publication": False,
    }
    assert "structural" in " ".join(result["evaluation"]["limitations"])
