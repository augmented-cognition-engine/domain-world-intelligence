from __future__ import annotations

import pytest

from scripts.ai_command_center_live_acceptance import run_acceptance


@pytest.mark.asyncio
async def test_two_official_lineages_reach_live_case_and_cited_reality_brief() -> None:
    result = await run_acceptance()

    assert result["pack"]["module_count"] == 5
    assert result["pack"]["json_only"] is True
    assert result["source"] == {
        "modes": ["live", "live"],
        "lineages": [
            "federal_register:2026-11415",
            "white_house_release:gold_eagle_2026_07_14",
        ],
        "stages": ["directive_issued", "implementation_reported"],
        "stable_entity_ref": True,
        "capture_calls": [1, 1],
        "recorded_transport": True,
        "network_access": False,
    }
    assert result["intelligence"]["shift_type"] == "official_ai_policy_progression"
    assert result["intelligence"]["signal_type"] == "official_ai_policy_development"
    assert result["intelligence"]["attention"] == "route"
    assert result["intelligence"]["case_member_count"] == 4
    assert result["intelligence"]["brief_mode"] == "live"
    assert result["intelligence"]["citation_count"] == 2
    assert result["intelligence"]["claim_count"] == 5
    assert result["separation"]["prepared_record_count"] == 0
    assert result["separation"]["prepared_material_reused"] is False
    assert result["separation"]["autonomous_publication"] is False
    assert result["separation"]["external_action"] is False
