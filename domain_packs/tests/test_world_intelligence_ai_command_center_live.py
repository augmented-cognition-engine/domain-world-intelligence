from __future__ import annotations

import pytest

from scripts.ai_command_center_live_acceptance import run_acceptance


@pytest.mark.asyncio
async def test_reviewed_ai_source_wave_reaches_live_atrium_context_and_cited_policy_brief() -> None:
    result = await run_acceptance()

    assert result["pack"]["module_count"] == 5
    assert result["pack"]["json_only"] is True
    assert result["source"] == {
        "modes": ["live"] * 7,
        "lineages": [
            "federal_register:2026-11415",
            "white_house_release:gold_eagle_2026_07_14",
            "reviewed_ai_publication:openai_gpt_5_6_release:2026-07-09",
            "reviewed_ai_publication:anthropic_claude_sonnet_5_release:2026-06-30",
            "reviewed_ai_publication:deepmind_gemini_3_6_model_cards:2026-07-21",
            "reviewed_ai_publication:nist_ai_agent_security_report:2026-05-18",
            "reviewed_ai_publication:nvidia_naver_ai_factory_investment:2026-07-24",
        ],
        "stages": ["directive_issued", "implementation_reported"],
        "stable_entity_ref": True,
        "capture_calls": [1] * 7,
        "context_watch_areas": [
            "benchmarks_and_independent_evals",
            "capital_and_company_moves",
            "models_and_capabilities",
            "models_and_capabilities",
            "safety_security_and_incidents",
        ],
        "publisher_count": 5,
        "recorded_transport": True,
        "network_access": False,
    }
    assert result["intelligence"]["shift_type"] == "official_ai_policy_progression"
    assert result["intelligence"]["signal_type"] == "official_ai_policy_development"
    assert result["intelligence"]["attention"] == "route"
    assert result["intelligence"]["case_member_count"] == 4
    assert result["intelligence"]["brief_mode"] == "live"
    assert result["intelligence"]["citation_count"] == 2
    assert result["intelligence"]["claim_count"] == 6
    assert result["separation"]["prepared_record_count"] == 0
    assert result["separation"]["prepared_material_reused"] is False
    assert result["separation"]["autonomous_publication"] is False
    assert result["separation"]["external_action"] is False
