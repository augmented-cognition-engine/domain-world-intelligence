from __future__ import annotations

import json
from pathlib import Path

import ace.application
import ace.intelligence
from ace.intelligence import SubscriptionDeliveryDisposition

from scripts.p2d_live_conflict_correction import compile_planetary_defense_pack
from scripts.p2e_user_owned_live_orientation_acceptance import (
    EXPECTED_PATH,
    INPUT_PATH,
    NEGATIVE_PATH,
    REQUESTS_PATH,
    build_static_intent_contracts,
    packet_identity,
    run_negative_cases,
    run_positive,
    run_runtime_positive,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_p2e_positive_projection_is_exact_and_runtime_materialized() -> None:
    expected = _load(EXPECTED_PATH)
    assert run_positive() == expected["expected_projection"]
    assert expected["expected_projection"]["runtime_materialization_claimed"] is True
    assert expected["expected_projection"]["open_contract_requests"] == []


async def test_p2e_materializes_exact_live_lineage_through_cited_reality_briefs() -> None:
    expected = _load(EXPECTED_PATH)["expected_runtime"]
    result = await run_runtime_positive()

    assert result == expected
    assert result["official_publication_roots"] == ["ESA", "NASA"]
    assert len(result["source_observation_ids"]) == 4
    assert len(result["shift_ids"]) == len(result["signal_ids"]) == 3
    assert len(result["case_ids"]) == len(result["reality_brief_ids"]) == 2
    assert result["reality_brief_citation_counts"] == [2, 4]
    assert result["all_lineage_records_persisted"] is True
    assert result["prepared_record_count"] == 0
    assert result["prepared_live_separated"] is True


def test_p2e_packet_identity_replays_exactly() -> None:
    packet = _load(INPUT_PATH)
    expected = _load(EXPECTED_PATH)
    first = packet_identity(packet, expected)
    second = packet_identity(packet, expected)
    assert first == second == expected["packet_identity"]


def test_p2e_negative_vectors_fail_closed_with_pinned_first_violations() -> None:
    expected = {item["case_id"]: item["expected_violation"] for item in _load(NEGATIVE_PATH)["cases"]}
    assert len(expected) == 11
    assert run_negative_cases() == expected


def test_p2e_owner_state_blocks_acquisition_before_source_access() -> None:
    packet = _load(INPUT_PATH)
    guarded = {
        window["suppression_reason"]: window
        for window in packet["sensing_windows"]
        if window["suppression_reason"] in {"owner_paused", "subscription_revoked"}
    }
    assert set(guarded) == {"owner_paused", "subscription_revoked"}
    for window in guarded.values():
        assert window["acquisition_request_count"] == 0
        assert window["candidate_source_keys"] == []
        assert window["accepted_new_source_keys"] == []
        assert window["replayed_source_keys"] == []


def test_p2e_constructs_exact_public_monitor_binding_and_record_only_subscription() -> None:
    packet = _load(INPUT_PATH)
    ownership = packet["ownership"]
    monitor, persona_binding, subscription = build_static_intent_contracts(packet)

    assert monitor.monitor_ref == ownership["monitor_ref"]
    assert monitor.monitor_digest == ownership["monitor_digest"]
    assert persona_binding.principal_ref == ownership["owner_ref"]
    assert persona_binding.binding_ref == ownership["persona_binding_ref"]
    assert persona_binding.binding_digest == ownership["persona_binding_digest"]
    assert subscription.persona_binding_ref == persona_binding.binding_ref
    assert subscription.monitor_refs == (monitor.monitor_ref,)
    assert subscription.subscription_ref == ownership["subscription_ref"]
    assert subscription.subscription_digest == ownership["subscription_digest"]
    assert subscription.delivery is SubscriptionDeliveryDisposition.RECORD_ONLY


def test_p2e_corrections_are_never_suppressed_as_duplicate_or_fatigue() -> None:
    packet = _load(INPUT_PATH)
    corrections = [
        window for window in packet["sensing_windows"] if window["material_kind"] == "same_lineage_correction"
    ]
    assert [window["window_id"] for window in corrections] == [
        "sensing_window:w3-nasa-correction",
        "sensing_window:w5-esa-correction-after-resume",
    ]
    for window in corrections:
        assert window["correction_visible"] is True
        assert window["disposition"] == "routed"
        assert window["suppression_reason"] is None


def test_p2e_preserves_publication_family_boundary_without_measurement_claim() -> None:
    policy = _load(INPUT_PATH)["source_policy"]
    assert sorted(policy["publication_roots"]) == ["ESA", "NASA"]
    assert policy["publication_root_independence_only"] is True
    assert policy["independent_measurements_claimed"] is False
    assert policy["same_lineage_revisions_count_as_new_families"] is False


def test_p2e_keeps_p2d_pack_and_brief_identities_unchanged() -> None:
    packet = _load(INPUT_PATH)
    pack = compile_planetary_defense_pack()
    assert pack.compiled_pack_id == packet["prerequisites"]["compiled_pack_id"]
    assert packet["prerequisites"]["historical_brief_id"] == ("brief:c3549af0262b100ca65024ee19cbae6e")
    assert packet["prerequisites"]["corrected_brief_id"] == ("brief:806d69d8e41f83f93ee3dc10f58f0d16")


def test_p2e_domain_pack_remains_inert_and_grants_no_new_authority() -> None:
    manifest = _load(PACK_ROOT / "manifest.json")
    assert {item["authority"] for item in manifest["authority_requests"]} == {"source_read"}
    assert all(path.suffix == ".json" for path in PACK_ROOT.rglob("*") if path.is_file())
    assert not tuple(PACK_ROOT.rglob("*.py"))
    packet = _load(INPUT_PATH)
    assert packet["source_policy"]["network_access"] is False
    assert packet["cadence_preference"]["scheduler_authorized"] is False
    assert packet["ownership"]["delivery_authorized"] is False
    assert packet["safety"]["external_action"] is False


def _public_intelligence_source() -> str:
    root = Path(ace.intelligence.__file__).resolve().parent
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))


def test_wi_cr_007_platform_gap_user_owned_monitor_subscription() -> None:
    requests = {item["request_id"]: item for item in _load(REQUESTS_PATH)["requests"]}
    assert requests["WI-CR-007"]["status"] == "closed"
    assert hasattr(ace.intelligence, "MonitorV1Alpha1")
    assert hasattr(ace.intelligence, "PersonaBindingV1Alpha1")
    assert hasattr(ace.intelligence, "SubscriptionV1Alpha1")
    assert hasattr(ace.application, "MonitoringLifecycleService")
    assert hasattr(ace.intelligence, "MonitoringLifecycleRequestV1Alpha1")
    assert hasattr(ace.intelligence, "MonitoringLifecycleReceiptV1Alpha1")
    source = _public_intelligence_source()
    assert "ace.intelligence.monitor/v1alpha1" in source
    assert "ace.intelligence.subscription/v1alpha1" in source
    assert "ace.intelligence.monitoring-lifecycle-receipt/v1alpha1" in source
    assert "MonitoringLifecycleState.REVOKED" in source


def test_wi_cr_008_platform_gap_sensing_window_disposition() -> None:
    requests = {item["request_id"]: item for item in _load(REQUESTS_PATH)["requests"]}
    assert requests["WI-CR-008"]["status"] == "closed"
    assert hasattr(ace.application, "SensingWindowService")
    assert hasattr(ace.intelligence, "SensingWindowReceiptV1Alpha1")
    source = _public_intelligence_source()
    assert "ace.intelligence.sensing-window-receipt/v1alpha1" in source
    assert "subscription_revoked" in source
