from __future__ import annotations

import asyncio
import json
from pathlib import Path

import ace.application as ace_application
import pytest
from ace.intelligence import IntelligenceOnboardingProfileV1Alpha1

if not hasattr(ace_application, "IntelligenceResourcePlaneService"):
    pytest.skip("ACE Core 0.8 resource plane is required", allow_module_level=True)

from scripts.atrium_ai_command_center_demo import build_atrium_page

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_ai_command_center_source_catalog_is_broad_but_honest() -> None:
    catalog = json.loads(
        (REPOSITORY_ROOT / "domain_packs/world_intelligence_ai/source_catalog.json").read_text(encoding="utf-8")
    )
    watch_areas = catalog["watch_areas"]
    sources = catalog["sources"]
    source_ids = {source["source_id"] for source in sources}
    referenced_source_ids = {source_id for area in watch_areas for source_id in area["source_ids"]}

    assert catalog["topic_id"] == "artificial_intelligence"
    assert {area["watch_id"] for area in watch_areas} == {
        "models_and_capabilities",
        "benchmarks_and_independent_evals",
        "economics_and_pricing",
        "reliability_and_platform_health",
        "open_ecosystem_and_research",
        "safety_security_and_incidents",
        "policy_regulation_and_governance",
        "capital_and_company_moves",
        "compute_chips_and_infrastructure",
        "talent_patents_and_research",
        "adoption_procurement_and_outcomes",
        "narratives_executives_and_public_attention",
    }
    assert len(sources) >= 60
    assert len(source_ids) == len(sources)
    assert referenced_source_ids == source_ids
    assert all(source["evidence_role"] in catalog["evidence_roles"] for source in sources)
    assert all(source["demo_wave"] in catalog["demo_waves"] for source in sources)
    assert {source["connection_state"] for source in sources} == {"connected", "proposed"}
    assert sum(source["connection_state"] == "connected" for source in sources) == 7
    assert {source["source_id"] for source in sources if source["connection_state"] == "connected"} == {
        "openai_news",
        "anthropic_news",
        "google_deepmind_model_cards",
        "nist_ai_agent_security_report",
        "nvidia_ai_infrastructure_news",
        "us_federal_register_ai_policy",
        "white_house_ai_policy",
    }
    assert all("uri" in source or "uri_template" in source for source in sources)
    assert catalog["selection_policy"]["proposed_sources_are_not_admitted_evidence"] is True
    assert {signal["signal_id"] for signal in catalog["signature_intelligence"]} == {
        "capability_cost_frontier",
        "claim_vs_reality",
        "research_to_product_diffusion",
        "capital_to_capability_conversion",
        "infrastructure_bottleneck",
        "regulation_implementation_gap",
        "strategy_before_announcement",
        "executive_promise_tracker",
        "adoption_trust_gap",
    }


def test_world_ai_command_center_projects_a_real_atrium_page() -> None:
    required_profile_fields = {
        "domain_label",
        "topic_label",
        "starter_prompts",
        "source_groups",
    }
    if not required_profile_fields <= set(IntelligenceOnboardingProfileV1Alpha1.model_fields):
        pytest.skip("the expanded ACE Core onboarding-profile contract is required for the Atrium projection")

    page = asyncio.run(build_atrium_page())
    kinds = {item["reference"]["resource_kind"] for item in page["items"]}
    monitoring_items = [
        item for item in page["items"] if item["reference"]["resource_kind"] in {"monitor", "subscription"}
    ]
    builder_items = [item for item in page["items"] if item["reference"]["resource_kind"] == "builder_session"]
    brief_item = next(item for item in page["items"] if item["reference"]["resource_kind"] == "brief")

    assert page["product_id"] == "product:world-ai-command-center"
    assert page["next_cursor"] is None
    assert len(page["items"]) == 43
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
        "builder_profile",
        "builder_session",
    } <= kinds
    assert {item["summary"] for item in monitoring_items} == {
        "Monitor lifecycle is active.",
        "Subscription lifecycle is active.",
    }
    assert page["demo"] == {
        "contract": "ace.world-intelligence.atrium-demo/v1alpha1",
        "source_proof_contract": "ace.world-intelligence.ai-command-center-live-proof/v1alpha2",
        "recorded_transport": True,
        "network_freshness_claimed": False,
        "autonomous_publication": False,
        "topic_id": "artificial_intelligence",
        "source_catalog": "domain_packs/world_intelligence_ai/source_catalog.json",
        "admitted_source_count": 7,
        "reviewed_publisher_count": 7,
        "context_watch_areas": [
            "benchmarks_and_independent_evals",
            "capital_and_company_moves",
            "models_and_capabilities",
            "models_and_capabilities",
            "safety_security_and_incidents",
        ],
        "brief_grounded_source_count": 2,
        "builder_profile_id": "intelligence_onboarding_profile:world-ai-command-center",
        "builder_session_id": "intelligence_builder_session:29a1f1a93d178d269e2ec927064cb164",
        "builder_stage": "first_briefing_ready",
        "builder_agent_roles": ["connection", "ontology", "intelligence", "briefing"],
    }
    assert [item["reference"]["revision"] for item in builder_items] == list(range(1, 9))
    assert [json.loads(item["payload"]["value_json"])["stage"] for item in builder_items] == [
        "goal_selected",
        "sources_connecting",
        "sources_ready",
        "concept_model_proposed",
        "concept_model_approved",
        "intelligence_model_proposed",
        "intelligence_model_approved",
        "first_briefing_ready",
    ]
    assert all(item["availability"] == "available" for item in builder_items)
    assert brief_item["title"] == "AI Policy: Directive to Reported Implementation"
    assert brief_item["summary"].startswith("Executive Order 14409 moved from publication to reported implementation:")
    assert "This matters because the policy now has a reported operating mechanism" in brief_item["summary"]
    assert "The change is supported by two admitted records" in brief_item["summary"]
    assert (
        "The White House reported the implementation activity on July 14, 2026—39 days later" in brief_item["summary"]
    )
    assert "No admitted source yet shows how many vulnerabilities entered the program" in brief_item["summary"]
