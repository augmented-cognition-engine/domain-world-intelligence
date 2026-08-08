from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.p2a_compile_acceptance import compile_world_pack
from scripts.p2b_prepared_replay import compile_replay_pack, run_positive
from scripts.p2b_scenario_acceptance import packet_identity

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"


def _load(name: str):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def test_prepared_interpreter_replay_matches_exact_projection():
    assert run_positive() == _load("p2b_prepared_replay_expected.json")


def test_prepared_replay_manifest_pins_exact_artifacts():
    manifest = _load("p2b_prepared_replay_manifest.json")
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_prepared_interpreter_replay_is_deterministic():
    assert run_positive() == run_positive()


def test_replay_exercises_all_frozen_shifts_and_only_expected_signals():
    projection = run_positive()
    expected = _load("p2b_expected.json")

    assert projection["shift_count"] == len(expected["shifts"]) == 5
    assert projection["signal_count"] == len(expected["signals"]) == 4
    assert projection["numeric_delta_percent"] == -12.2977
    assert projection["claim_corroboration_has_signal"] is False
    assert projection["claim_corroboration_resource_set"]["resource_count"] == 5
    assert projection["claim_corroboration_resource_set"]["contains_signal"] is False
    assert projection["orientation_case"]["member_count"] == 5
    assert len(projection["orientation_case"]["member_ids"]) == 5
    assert projection["orientation_case_resource_set"] == {
        "admission_digest": "sha256:5190fce71b6976bd00da6f8934255b42792d4543197aa7fbf1fed330e0c6722f",
        "admission_id": "resource_set_admission:d1833406b2e099cd1cbdfdf38d7ee2a8",
        "case_is_last": True,
        "resource_count": 28,
    }
    assert set(projection["shift_types"].values()) == {
        "claim_support_shift",
        "event_status_shift",
        "public_indicator_shift",
        "record_correction_shift",
    }
    assert set(projection["signal_types"].values()) == {
        "breaking_development",
        "claim_conflict",
        "material_correction",
        "public_indicator_move",
    }
    assert all(len(routes) == 1 for routes in projection["routes"].values())


def test_additive_replay_revision_does_not_move_frozen_pack_or_packet():
    default_pack = compile_world_pack()
    replay_pack = compile_replay_pack()
    p2a_pack = _load("p2a_manifest.json")["pack"]
    scenario = _load("p2b_scenario.json")
    expected = _load("p2b_expected.json")
    p2b_manifest = _load("p2b_manifest.json")

    assert default_pack.compiled_pack_id == p2a_pack["compiled_pack_id"]
    assert default_pack.pack_digest == p2a_pack["pack_digest"]
    assert packet_identity(scenario, expected) == p2b_manifest["packet_identity"]
    assert replay_pack.metadata.version == "0.2.0"
    assert replay_pack.compiled_pack_id != default_pack.compiled_pack_id


def test_runtime_falsification_findings_are_explicit_and_domain_neutral():
    projection = run_positive()
    gaps = {item["request_id"]: item["boundary"] for item in projection["runtime_gaps"]}

    # WI-CR-005 is no longer listed: Case-bound governed Brief synthesis is now a
    # public ACE capability and is verified by the P2B-CB1 case-brief packet.
    assert gaps == {
        "WI-CR-002": "epistemic_status_projection",
        "WI-CR-003": "source_independence_closure",
        "WI-CR-004": "supersession_impact_projection",
    }
    assert projection["invariants"] == {
        "default_pack_mutated": False,
        "delivery_authority": False,
        "external_action": False,
        "frozen_packet_mutated": False,
        "live_resources": 0,
        "private_detector_runtime": False,
    }
