from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from scripts.p2b_case_brief import WORLD_EPISTEMIC_STATUSES, run_case_brief
from scripts.p2b_independent_case_brief import (
    CORROBORATION_VECTORS,
    HYDROLOGY_ROOT,
    LEDGER_ROOT,
    LEDGER_SYNDICATION,
    STATUS_SET_ID,
    run_independent_case_brief,
)
from scripts.p2b_status_case_brief import run_status_case_brief

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"

#: Identities frozen by earlier packets. This one is additive and must not move them.
WI_CR_005_CASE_ID = "case:2ee200c03f2576307b0bc43e6e128f30"
WI_CR_005_BRIEF_ID = "brief:8fb3173069eca502652b1c9c004c92e6"
WI_CR_002_CASE_ID = "case:bc28c76926d733c0ce0fe03b9c9222db"
WI_CR_002_BRIEF_ID = "brief:7adb24b596cac21d7aa4e5476bc8733c"


def _load(name: str):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def _projection():
    return asyncio.run(run_independent_case_brief())


def test_independent_governed_brief_matches_exact_projection():
    assert _projection() == _load("p2b_independent_case_brief_expected.json")


def test_independent_governed_brief_is_deterministic():
    assert _projection() == _projection()


def test_independent_case_brief_manifest_pins_exact_artifacts():
    manifest = _load("p2b_independent_case_brief_manifest.json")
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_corroborated_requires_two_independent_derivation_families():
    """The acceptance case: Ledger reporting root plus the Hydrology root."""

    independence = _projection()["independence"]

    assert independence["corroborated_claim_count"] == 1
    assert independence["corroborated_required_families"] == [2]
    assert independence["corroborated_distinct_families"] == [2]
    assert independence["corroborated_roots_are_ledger_and_hydrology"] is True
    assert independence["distinct_families_in_closure"] == 5


def test_syndication_and_reprints_collapse_and_cannot_corroborate():
    """Repetition fails at runtime, and fails for the intended reason.

    The syndicated copies are deliberately inside the exact Case closure, so a
    rejection cannot be the pre-existing "unknown support" guard firing instead
    of the independence predicate.
    """

    independence = _projection()["independence"]

    assert independence["syndicated_copies_are_inside_the_closure"] is True
    # Exact membership, not merely "not a root": both copies resolve specifically
    # to the Ledger reporting root, alongside the report and its correction.
    assert independence["syndicated_copies_are_exact_members_of_the_ledger_family"] is True
    assert independence["ledger_family_member_count"] == 4
    assert independence["hydrology_is_a_separate_single_member_family"] is True

    vectors = independence["negative_vectors"]
    assert set(vectors) == set(CORROBORATION_VECTORS) - {"independent_roots"}
    for name, result in vectors.items():
        assert result["rejected"] is True, name
        assert result["error_type"] == "CaseBriefFamilyStatusSynthesisError", name
        assert result["mentions_derivation_families"] is True, name
        assert result["durable_brief_count"] == 0, name


def test_two_distinct_publishers_of_one_origin_are_not_independent():
    """Publisher count is never independence."""

    vectors = _projection()["independence"]["negative_vectors"]

    assert len(LEDGER_SYNDICATION) == 2
    assert vectors["two_publishers_one_origin"]["rejected"] is True
    assert vectors["two_publishers_one_origin"]["durable_brief_count"] == 0
    assert CORROBORATION_VECTORS["independent_roots"] == (LEDGER_ROOT, HYDROLOGY_ROOT)


def test_the_projection_discloses_the_exact_predicate_and_proof_inputs():
    status = _projection()["status_projection"]

    assert status["status_set_id"] == STATUS_SET_ID
    assert status["derivation_family_policy"] == "observation_lineage_root_closure/v1alpha1"
    assert sorted(status["collapsing_relations"]) == ["derived_from", "supersedes"]
    assert status["closure_family_count"] == 5
    families = {item["root_record_id"]: item["member_record_ids"] for item in status["closure_families"]}
    assert len(families) == 5
    assert sorted(len(members) for members in families.values()) == [1, 1, 1, 1, 4]
    members = [member for value in families.values() for member in value]
    assert len(members) == len(set(members)) == 8, "one family per admitted Observation"
    for root, value in families.items():
        assert root in value
        assert value == sorted(value)
    assert sorted(status["declared_status_ids"]) == sorted(WORLD_EPISTEMIC_STATUSES)
    assert status["every_required_status_used"] is True
    assert status["claim_status_count"] == 11


def test_status_is_persisted_atomically_and_replays_deterministically():
    governance = _projection()["governance"]

    assert governance["atomic_records"] == 3
    assert governance["record_kinds"] == [
        "brief",
        "case_brief_synthesis_receipt",
        "brief_derivation_family_status_projection",
    ]
    assert governance["governed_state_preconditions"] == 4
    assert governance["durable_brief_count"] == 1
    assert governance["deterministic_replay"] is True
    assert governance["provider_invocations"] == 1


def test_earlier_packets_are_untouched_by_this_additive_packet():
    frozen = asyncio.run(run_case_brief())
    status_packet = asyncio.run(run_status_case_brief())
    independent = _projection()

    assert frozen["case"]["case_id"] == WI_CR_005_CASE_ID
    assert frozen["brief"]["brief_id"] == WI_CR_005_BRIEF_ID
    assert status_packet["case"]["case_id"] == WI_CR_002_CASE_ID
    assert status_packet["brief"]["brief_id"] == WI_CR_002_BRIEF_ID

    # Declaring a Pack module and admitting derivation lineage both re-key every
    # resource, so this packet carries its own documented identities.
    assert independent["case"]["case_id"] not in {WI_CR_005_CASE_ID, WI_CR_002_CASE_ID}
    assert independent["brief"]["brief_id"] not in {WI_CR_005_BRIEF_ID, WI_CR_002_BRIEF_ID}
    assert independent["scenario_id"] == frozen["scenario_id"]


def test_the_syndicated_copies_join_the_closure_in_this_packet_only():
    """The approved consequence: this packet has no unreferenced records."""

    frozen = asyncio.run(run_case_brief())
    independent = _projection()

    assert frozen["invariants"]["unreferenced_admitted_records"] == 2
    assert independent["invariants"]["unreferenced_admitted_records"] == 0
    assert independent["synthesis_receipt"]["selected_context_count"] == 28
    assert independent["brief"]["lineage_count"] == 28


def test_world_adds_no_private_independence_machinery():
    invariants = _projection()["invariants"]

    assert invariants == {
        "delivery_authority": False,
        "duplicated_source_records": False,
        "external_action": False,
        "imperative_pack_code": False,
        "live_resources": 0,
        "private_aggregation_in_world": False,
        "private_reasoning_runtime": False,
        "private_source_independence_engine": False,
        "private_status_projector": False,
        "unreferenced_admitted_records": 0,
        "world_semantics_added_to_ace": False,
    }


def test_wi_cr_004_remains_open():
    projection = _projection()

    assert projection["closed_requests"] == ["WI-CR-002", "WI-CR-003", "WI-CR-005"]
    assert [item["request_id"] for item in projection["runtime_gaps"]] == ["WI-CR-004"]
    assert projection["proven"]["independence_is_only_as_strong_as_admitted_lineage"] is True
