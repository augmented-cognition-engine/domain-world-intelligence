from __future__ import annotations

import asyncio
import json
from pathlib import Path

import ace.application as ace_application
import pytest

if not hasattr(ace_application, "IntelligenceResourcePlaneService"):
    pytest.skip("ACE Core 0.8 resource plane is required", allow_module_level=True)

from scripts.atrium_ai_command_center_demo import build_atrium_page

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_ai_command_center_source_catalog_is_broad_but_honest() -> None:
    catalog = json.loads(
        (REPOSITORY_ROOT / "domain_packs/world_intelligence_ai/source_catalog.json").read_text(encoding="utf-8")
    )
    watch_areas = catalog["watch_areas"]
    sources = [source for area in watch_areas for source in area["sources"]]

    assert catalog["topic_id"] == "artificial_intelligence"
    assert {area["watch_id"] for area in watch_areas} == {
        "models_and_capabilities",
        "economics_and_pricing",
        "safety_and_security",
        "policy_and_regulation",
        "capital_and_company_moves",
        "adoption_and_executive_signals",
    }
    assert len(sources) >= 15
    assert {source["connection_state"] for source in sources} == {"connected", "proposed"}
    assert sum(source["connection_state"] == "connected" for source in sources) == 2
    assert all("uri" in source or "uri_template" in source for source in sources)
    assert catalog["selection_policy"]["proposed_sources_are_not_admitted_evidence"] is True


def test_world_ai_command_center_projects_a_real_atrium_page() -> None:
    page = asyncio.run(build_atrium_page())
    kinds = {item["reference"]["resource_kind"] for item in page["items"]}
    monitoring_items = [
        item for item in page["items"] if item["reference"]["resource_kind"] in {"monitor", "subscription"}
    ]

    assert page["product_id"] == "product:world-ai-command-center"
    assert page["next_cursor"] is None
    assert len(page["items"]) == 14
    assert {
        "source",
        "connection",
        "entity",
        "observation",
        "shift",
        "signal",
        "case",
        "brief",
        "monitor",
        "subscription",
    } <= kinds
    assert {item["summary"] for item in monitoring_items} == {
        "Monitor lifecycle is active.",
        "Subscription lifecycle is active.",
    }
    assert page["demo"] == {
        "contract": "ace.world-intelligence.atrium-demo/v1alpha1",
        "source_proof_contract": "ace.world-intelligence.ai-command-center-live-proof/v1alpha1",
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
        "topic_id": "artificial_intelligence",
        "source_catalog": "domain_packs/world_intelligence_ai/source_catalog.json",
    }
