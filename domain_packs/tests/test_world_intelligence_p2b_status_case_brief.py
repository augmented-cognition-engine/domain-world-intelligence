from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from scripts.p2b_case_brief import WORLD_EPISTEMIC_STATUSES, run_case_brief
from scripts.p2b_status_case_brief import STATUS_SET_ID, run_status_case_brief

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"

#: The frozen WI-CR-005 identities. This packet is additive and must not move them.
FROZEN_CASE_ID = "case:2ee200c03f2576307b0bc43e6e128f30"
FROZEN_BRIEF_ID = "brief:8fb3173069eca502652b1c9c004c92e6"


def _load(name: str):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def _projection():
    return asyncio.run(run_status_case_brief())


def test_status_aware_governed_brief_matches_exact_projection():
    assert _projection() == _load("p2b_status_case_brief_expected.json")


def test_status_aware_governed_brief_is_deterministic():
    assert _projection() == _projection()


def test_status_case_brief_manifest_pins_exact_artifacts():
    manifest = _load("p2b_status_case_brief_manifest.json")
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_every_declared_status_is_bound_to_exact_claim_ids():
    status = _projection()["status_projection"]

    assert status["status_set_id"] == STATUS_SET_ID
    assert sorted(status["declared_status_ids"]) == sorted(WORLD_EPISTEMIC_STATUSES)
    assert status["all_seven_required_statuses_present"] is True
    assert status["every_required_status_used"] is True
    assert status["binds_every_receipted_claim"] is True
    assert status["claim_status_count"] == 11
    assert sorted(status["claims_per_status"]) == sorted(WORLD_EPISTEMIC_STATUSES)

    # Every statement carries its own machine-readable status keyed by claim ID.
    claim_ids = [item["claim_id"] for item in status["statuses_per_claim"]]
    assert len(claim_ids) == len(set(claim_ids)) == 11
    assert all(item["claim_id"].startswith("grounded_claim:") for item in status["statuses_per_claim"])
    assert all(item["support_count"] >= 1 for item in status["statuses_per_claim"])
    assert status["status_carrier"] == "brief_epistemic_status_projection.claim_statuses"
    assert status["section_membership_is_validated_status"] is False


def test_status_is_persisted_atomically_with_the_brief_and_receipt():
    governance = _projection()["governance"]

    assert governance["atomic_records"] == 3
    assert governance["record_kinds"] == [
        "brief",
        "case_brief_synthesis_receipt",
        "brief_epistemic_status_projection",
    ]
    assert governance["governed_state_preconditions"] == 4
    assert governance["durable_brief_count"] == 1
    assert governance["deterministic_replay"] is True
    assert governance["provider_invocations"] == 1


def test_corroborated_does_not_claim_source_family_independence():
    """WI-CR-003 stays open: cardinality and kind are enforced, independence is not."""

    projection = _projection()

    assert projection["proven"]["status_validated_against_support_count"] is True
    assert projection["proven"]["status_validated_against_support_kinds"] is True
    assert projection["proven"]["corroborated_proves_source_family_independence"] is False

    corroborated = [
        item for item in projection["status_projection"]["statuses_per_claim"] if item["status_id"] == "corroborated"
    ]
    assert corroborated, "the frozen scenario must exercise the corroborated status"
    for item in corroborated:
        assert item["support_count"] >= 2
        assert item["support_kinds"] == ["observation"]

    gaps = {item["request_id"] for item in projection["runtime_gaps"]}
    assert gaps == {"WI-CR-003", "WI-CR-004"}
    assert projection["closed_requests"] == ["WI-CR-002", "WI-CR-005"]


def test_the_frozen_wi_cr_005_packet_is_untouched_by_this_additive_packet():
    """The status packet activates an additive revision; the frozen one must not move."""

    frozen = asyncio.run(run_case_brief())

    assert frozen["case"]["case_id"] == FROZEN_CASE_ID
    assert frozen["brief"]["brief_id"] == FROZEN_BRIEF_ID
    assert frozen["governance"]["atomic_records"] == 2

    status = _projection()
    # A declared Pack module necessarily re-keys resources admitted under it, so
    # the status packet carries its own documented identities.
    assert status["case"]["case_id"] != FROZEN_CASE_ID
    assert status["brief"]["brief_id"] != FROZEN_BRIEF_ID
    assert status["scenario_id"] == frozen["scenario_id"]
    assert status["case"]["member_count"] == frozen["case"]["member_count"]
    assert status["synthesis_receipt"]["selected_context_count"] == 26


def test_world_adds_no_private_status_machinery():
    invariants = _projection()["invariants"]

    assert invariants == {
        "delivery_authority": False,
        "duplicated_source_records": False,
        "external_action": False,
        "imperative_pack_code": False,
        "live_resources": 0,
        "private_aggregation_in_world": False,
        "private_reasoning_runtime": False,
        "private_status_projector": False,
        "unreferenced_admitted_records": 2,
        "world_semantics_added_to_ace": False,
    }
