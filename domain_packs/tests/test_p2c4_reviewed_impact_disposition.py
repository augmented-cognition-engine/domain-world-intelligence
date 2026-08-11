from __future__ import annotations

import importlib.util

import pytest


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact_disposition") is None:
        pytest.skip("P2C4 candidate requires the stacked ACE Core proposal-disposition contract")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("P2C4 candidate requires the separately packaged Core reference adapter")


@pytest.mark.asyncio
async def test_structurally_useful_result_reaches_exact_reject_no_action_disposition(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c4_reviewed_impact_disposition import run_reviewed_disposition

    result = await run_reviewed_disposition(tmp_path)

    assert result["measured_feedback"]["evaluation"]["classification"] == "useful"
    assert result["measured_feedback"]["proposal"]["action"] == "promote"
    assert result["disposition"]["decision"]["intent"]["subject"] == result["disposition"]["proposal_reference"]
    assert result["disposition"]["decision"]["intent"]["disposition"] == "reject"
    assert result["disposition"]["decision"]["intent"]["action_disposition"] == "no_action"
    assert result["disposition"]["effective_state_changed"] is False
    assert result["disposition"]["replayed"] is True
    assert result["disposition"]["no_reauthorization"] is True


@pytest.mark.asyncio
async def test_reviewed_disposition_preserves_the_public_claim_boundary(tmp_path) -> None:
    _require_candidate_contracts()
    from scripts.p2c4_reviewed_impact_disposition import run_reviewed_disposition

    result = await run_reviewed_disposition(tmp_path)

    assert result["scope"] == {
        "measured_classification_preserved": "useful",
        "proposal_action_preserved": "promote",
        "proposal_disposition": "reject",
        "proposal_applied": False,
        "human_benefit_claimed": False,
        "causality_claimed": False,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
    }
    rationale = result["disposition"]["decision"]["intent"]["rationale"]
    assert "does not establish" in rationale
