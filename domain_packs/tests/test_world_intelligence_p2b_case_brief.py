from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from scripts.p2b_case_brief import WORLD_EPISTEMIC_STATUSES, run_case_brief

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"


def _load(name: str):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def _projection():
    return asyncio.run(run_case_brief())


def test_case_bound_governed_brief_matches_exact_projection():
    assert _projection() == _load("p2b_case_brief_expected.json")


def test_case_bound_governed_brief_is_deterministic():
    assert _projection() == _projection()


def test_case_brief_manifest_pins_exact_artifacts():
    manifest = _load("p2b_case_brief_manifest.json")
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_governed_brief_binds_the_pinned_orientation_case_and_complete_closure():
    projection = _projection()

    assert projection["case"] == {
        "case_id": "case:2ee200c03f2576307b0bc43e6e128f30",
        "case_digest": "sha256:2ee200c03f2576307b0bc43e6e128f309e9de7efd3c11b1cad2ad1c250b4591f",
        "member_count": 5,
    }
    assert projection["brief"]["binds_case_in_lineage"] is True
    assert projection["brief"]["lineage_kinds"] == {
        "case": 1,
        "entity_snapshot": 10,
        "observation": 6,
        "shift": 5,
        "signal": 4,
    }
    assert projection["brief"]["lineage_count"] == 26
    receipt = projection["synthesis_receipt"]
    assert receipt["case_member_count"] == 5
    assert receipt["routed_member_count"] == 4
    assert receipt["selected_context_count"] == 26
    assert receipt["template_id"] == "reality_change_brief"
    assert receipt["persona_ids"] == ["general_reader", "public_researcher"]
    assert len(receipt["section_ids"]) == 11


def test_governed_brief_is_atomic_and_replays_without_reasoning_again():
    governance = _projection()["governance"]

    assert governance["atomic_records"] == 2
    assert governance["durable_brief_count"] == 1
    assert governance["deterministic_replay"] is True
    assert governance["provider_invocations"] == 1
    assert governance["governed_state_preconditions"] == 4


def test_no_source_record_is_duplicated_to_reach_the_case_boundary():
    invariants = _projection()["invariants"]

    assert invariants == {
        "delivery_authority": False,
        "duplicated_source_records": False,
        "external_action": False,
        "live_resources": 0,
        "private_aggregation_in_world": False,
        "private_reasoning_runtime": False,
        "unreferenced_admitted_records": 2,
        "world_semantics_added_to_ace": False,
    }


def test_this_single_derivation_path_still_binds_only_grounding_kind():
    """This frozen path keeps draft ``v1alpha1``, so it carries no status itself.

    WI-CR-002 is closed by the additive status packet (P2B-SB1), which declares
    the seven statuses in the Domain Pack and binds them per statement. This
    harness stays on the legacy draft contract precisely so the frozen
    WI-CR-005 identities remain byte-identical.
    """

    projection = _projection()
    epistemic = projection["epistemic_status_projection"]

    assert tuple(epistemic["required_statuses"]) == WORLD_EPISTEMIC_STATUSES
    assert epistemic["required_status_count"] == 7
    assert epistemic["expressible_statuses"] == ["cited", "inference"]
    assert epistemic["expressible_status_count"] == 2
    assert epistemic["status_carrier"] == "claim.grounding_kind"
    assert epistemic["section_membership_is_validated_status"] is False
    assert epistemic["status_aware_path_available"] is True
    assert epistemic["status_aware_packet"] == "P2B-SB1"
    gaps = {item["request_id"]: item["boundary"] for item in projection["runtime_gaps"]}
    assert gaps == {
        "WI-CR-003": "source_independence_closure",
        "WI-CR-004": "supersession_impact_projection",
    }
    assert projection["closed_requests"] == ["WI-CR-005"]
    assert projection["wi_cr_002_closed_by"] == "P2B-SB1"
