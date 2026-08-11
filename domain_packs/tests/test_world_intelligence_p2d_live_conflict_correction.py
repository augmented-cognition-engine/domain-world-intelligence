from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.p2d_live_conflict_correction import run_acceptance

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = (
    REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense" / "conformance" / "p2d_live_expected.json"
)


@pytest.mark.asyncio
async def test_live_conflict_correction_supersession_reaches_status_aware_brief() -> None:
    result = await run_acceptance()
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))

    assert result["pack"] | {} == {
        **expected["pack"],
        "json_only": True,
    }
    assert result["source"]["lineages"] == expected["source"]["lineages"]
    assert result["source"]["probabilities"] == expected["source"]["probabilities"]
    assert result["source"]["stable_entity_ref"] is True
    assert result["source"]["adapter_capture_calls"] == {"NASA": 2, "ESA": 2}
    assert set(result["source"]["transport_calls"].values()) == {1}
    assert result["source"]["network_access"] is False

    for key, value in expected["historical"].items():
        assert result["historical"][key] == value
    assert result["historical"]["shift_type"] == "official_estimate_divergence"
    assert result["historical"]["signal_type"] == ("planetary_defense_estimate_divergence")
    assert result["historical"]["status_replay_exact"] is True

    for key, value in expected["correction"].items():
        assert result["correction"][key] == value
    assert result["correction"]["impact_replay_exact"] is True
    assert result["correction"]["impact_is_dependency_not_falsehood"] is True
    assert all(item["rejected"] for item in result["correction"]["negative_vectors"].values())

    for key, value in expected["corrected"].items():
        assert result["corrected"][key] == value
    assert result["corrected"]["shift_types"] == ["official_estimate_downward_revision"]
    assert result["corrected"]["signal_types"] == ["planetary_defense_estimate_revision"]
    assert result["corrected"]["status_replay_exact"] is True
    assert result["corrected"]["same_lineage_supersessions_collapse"] is True
    assert result["corrected"]["corroborated_claim_family_count"] == 2

    assert result["historical_integrity"] == {
        "brief_id_unchanged": True,
        "brief_precedes_corrections": True,
        "brief_reopened_identically": True,
        "historical_artifact_rewritten": False,
    }
    assert result["separation"] == {
        **expected["separation"],
        "prepared_material_reused": False,
        "autonomous_publication": False,
        "external_action": False,
    }
