from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_ai_command_center_onboarding_profile_is_outcome_led_and_non_authorizing() -> None:
    catalog = json.loads(
        (REPOSITORY_ROOT / "domain_packs/world_intelligence_ai/source_catalog.json").read_text(encoding="utf-8")
    )
    profile = json.loads(
        (REPOSITORY_ROOT / "domain_packs/world_intelligence_ai/onboarding_profile.json").read_text(
            encoding="utf-8"
        )
    )
    watch_ids = {watch["watch_id"] for watch in catalog["watch_areas"]}
    intelligence_ids = {item["signal_id"] for item in catalog["signature_intelligence"]}

    assert profile["contract"] == "ace.domain-pack.intelligence-onboarding-profile/v1alpha1"
    assert profile["topic_id"] == catalog["topic_id"]
    assert profile["prompt"] == "What do you need to stay ahead of?"
    assert len(profile["outcomes"]) == 6
    assert {outcome["outcome_id"] for outcome in profile["outcomes"]} == {
        "build_or_buy_ai",
        "strategy_and_investment",
        "frontier_research_and_products",
        "policy_safety_and_operational_risk",
        "competitive_landscape",
        "custom_picture",
    }
    assert all(
        set(outcome["recommended_watch_ids"]) <= watch_ids for outcome in profile["outcomes"]
    )
    assert all(
        set(outcome["recommended_intelligence_ids"]) <= intelligence_ids
        for outcome in profile["outcomes"]
    )
    assert all(outcome["icon_hint"] in {"choice", "strategy", "research", "risk", "competition", "custom"} for outcome in profile["outcomes"])
    assert all("recommended_topic_labels" in outcome for outcome in profile["outcomes"])
    assert all("recommended_intelligence_labels" in outcome for outcome in profile["outcomes"])
    assert {cadence["cadence_id"] for cadence in profile["cadences"]} == {
        "urgent_only",
        "daily_pulse",
        "weekly_brief",
    }
    assert profile["default_cadence_id"] == "weekly_brief"
    assert profile["guardrails"] == {
        "declarative_only": True,
        "authorizes_connections": False,
        "authorizes_monitors": False,
        "proposed_sources_are_not_connected": True,
        "feedback_may_reweight_relevance_not_authority": True,
    }
