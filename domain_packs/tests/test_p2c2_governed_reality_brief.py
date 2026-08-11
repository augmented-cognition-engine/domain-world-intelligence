from __future__ import annotations

import importlib.util

import pytest

from scripts.p2c2_federal_register_monitor import compile_monitor_pack


def test_federal_register_monitor_pack_compiles_as_declarative_configuration() -> None:
    pack = compile_monitor_pack()

    assert pack.metadata.pack_id == "world_intelligence_federal_register_monitor"
    assert pack.metadata.version == "0.1.0"
    assert len(pack.modules) == 5


@pytest.mark.asyncio
async def test_official_records_reach_reviewed_verified_promoted_export(
    tmp_path,
) -> None:
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("cross-repo acceptance requires the independently packaged Core reference adapter")
    from scripts.p2c2_governed_reality_brief import run_acceptance

    state = {}
    result = await run_acceptance(tmp_path, state_sink=state)

    assert result["source"]["entity_ref_stable"] is True
    assert result["source"]["observation_modes"] == ["live", "live"]
    assert result["intelligence"]["shift_type"] == "official_publication_change"
    assert result["intelligence"]["signal_type"] == "official_publication"
    assert result["intelligence"]["attention"] == "route"
    assert result["intelligence"]["citation_count"] == 2
    assert result["intelligence"]["claim_count"] == 6
    assert result["intelligence"]["provider_invocations"] == 1
    assert result["decision"]["action_type"] == "create_workspace_export"
    assert result["action"]["disposition"] == "succeeded"
    assert result["action"]["effect_state"] == "confirmed"
    assert result["action"]["replayed_without_second_effect"] is True
    context = state["environment"].context
    decided_at = state["decision"].intent.decided_at
    completed_at = state["action_outcome"].terminal.result.completed_at
    assert context.authenticated_at <= decided_at < context.expires_at
    assert context.authenticated_at <= completed_at < context.expires_at
    assert state["action_binding"].artifact.implementation_id == "world_recorded_workspace_export_fixture"
    assert result["scope"] == {
        "autonomous_publication": False,
        "human_review_required": True,
        "network_access": False,
        "official_public_records": True,
        "political_persuasion": False,
        "recorded_transport": True,
    }
