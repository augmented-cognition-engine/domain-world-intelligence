from __future__ import annotations

import asyncio

import ace.application as ace_application
import pytest

if not hasattr(ace_application, "IntelligenceResourcePlaneService"):
    pytest.skip("ACE Core 0.8 resource plane is required", allow_module_level=True)

from scripts.atrium_ai_command_center_demo import build_atrium_page


def test_world_ai_command_center_projects_a_real_atrium_page() -> None:
    page = asyncio.run(build_atrium_page())
    kinds = {item["reference"]["resource_kind"] for item in page["items"]}

    assert page["product_id"] == "product:world-ai-command-center"
    assert page["next_cursor"] is None
    assert {"source", "connection", "entity", "observation", "shift", "signal", "case", "brief"} <= kinds
    assert page["demo"] == {
        "contract": "ace.world-intelligence.atrium-demo/v1alpha1",
        "source_proof_contract": "ace.world-intelligence.ai-command-center-live-proof/v1alpha1",
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
    }
