from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from scripts.p2b_independent_case_brief import run_independent_case_brief
from scripts.p2b_supersession_impact import SUPERSESSION_VECTORS, run_supersession_impact

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = REPO_ROOT / "domain_packs" / "world_intelligence" / "conformance"

LEDGER = "supersession:correction_114_over_report_1088"
ORDER = "supersession:order_47_over_bulletin_214"

#: Identities frozen by earlier packets. This one is additive over WI-CR-003 and
#: reuses its exact activation, so it must reproduce them byte-for-byte.
WI_CR_003_CASE_ID = "case:412426eee708d56f6bda931ccf9e5d8b"
WI_CR_003_BRIEF_ID = "brief:25d8232c9bfa27050bdcb160fb75f06c"


def _load(name: str):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def _projection():
    return asyncio.run(run_supersession_impact())


def test_supersession_impact_matches_exact_projection():
    assert _projection() == _load("p2b_supersession_impact_expected.json")


def test_supersession_impact_is_deterministic():
    assert _projection() == _projection()


def test_supersession_impact_manifest_pins_exact_artifacts():
    manifest = _load("p2b_supersession_impact_manifest.json")
    for artifact in manifest["artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_both_frozen_corrections_are_exercised():
    projection = _projection()

    assert {item[0] for item in SUPERSESSION_VECTORS} == {LEDGER, ORDER}
    assert set(projection["supersessions"]) == {LEDGER, ORDER}


def test_the_ledger_correction_reaches_its_syndication_and_derived_state():
    """The Ledger family is reached; nothing outside the lineage is invented."""

    ledger = _projection()["supersessions"][LEDGER]

    assert ledger["closure_size"] == 28
    assert ledger["impacted_count"] == 11
    assert ledger["direct_count"] == 6
    assert ledger["transitive_count"] == 5
    assert ledger["max_depth"] == 3
    # The syndicated copies and the correction record itself all derive from the
    # superseded report, so they and their downstream state are in scope.
    assert ledger["impacted_kinds"] == {
        "case": 1,
        "entity_snapshot": 4,
        "observation": 3,
        "shift": 2,
        "signal": 1,
    }
    assert ledger["unaffected_count"] == 16
    assert ledger["impacted_count"] + ledger["unaffected_count"] + 1 == ledger["closure_size"]


def test_the_order_supersession_reaches_only_derived_state():
    """A different correction with a genuinely different, smaller blast radius."""

    order = _projection()["supersessions"][ORDER]

    assert order["impacted_count"] == 7
    assert order["direct_count"] == 2
    assert order["transitive_count"] == 5
    # The bulletin has no derived Observations, so no Observation is impacted.
    assert "observation" not in order["impacted_kinds"]
    assert order["impacted_kinds"] == {
        "case": 1,
        "entity_snapshot": 2,
        "shift": 2,
        "signal": 2,
    }
    assert order["unaffected_count"] == 20
    assert order["impacted_count"] + order["unaffected_count"] + 1 == order["closure_size"]


def test_impact_is_never_invented_where_lineage_does_not_support_it():
    """The two vectors differ exactly as their lineage differs."""

    supersessions = _projection()["supersessions"]

    assert supersessions[LEDGER]["impacted_count"] != supersessions[ORDER]["impacted_count"]
    assert supersessions[LEDGER]["unaffected_count"] != supersessions[ORDER]["unaffected_count"]
    for vector in supersessions.values():
        assert vector["case_is_impacted"] is True, "the Case closes over the affected members"
        assert vector["unaffected_count"] > 0, "the boundary must be disclosed, not empty"


def test_brief_claims_are_partially_and_fully_impacted_as_their_supports_dictate():
    supersessions = _projection()["supersessions"]

    ledger = supersessions[LEDGER]
    assert ledger["impacted_claim_count"] == 9
    assert ledger["fully_impacted_claim_count"] == 3
    assert ledger["partially_impacted_claim_count"] == 6

    order = supersessions[ORDER]
    assert order["impacted_claim_count"] == 5
    # Not one claim is *entirely* grounded on the superseded bulletin's lineage.
    assert order["fully_impacted_claim_count"] == 0
    assert order["partially_impacted_claim_count"] == 5


def test_the_prior_brief_stays_immutable_and_replayable_after_the_correction():
    projection = _projection()
    historical = projection["historical_integrity"]

    assert historical["brief_id_unchanged"] is True
    assert historical["brief_replays_identically"] is True
    assert historical["receipt_replays_identically"] is True
    assert historical["status_projection_replays_identically"] is True
    assert historical["replay_used_no_new_reasoning"] is True
    assert historical["brief_cutoff_precedes_the_correction"] is True

    # The exact WI-CR-003 identities are reproduced, not merely "some Brief".
    assert projection["brief"]["brief_id"] == WI_CR_003_BRIEF_ID
    assert projection["case_id"] == WI_CR_003_CASE_ID


def test_the_accepted_wi_cr_003_packet_is_reproduced_byte_for_byte():
    independent = asyncio.run(run_independent_case_brief())
    impact = _projection()

    assert independent["brief"]["brief_id"] == impact["brief"]["brief_id"]
    assert independent["brief"]["brief_digest"] == impact["brief"]["brief_digest"]
    assert independent["case"]["case_id"] == impact["case_id"]


def test_the_impact_projection_is_appended_atomically_and_replays_exactly():
    for vector in _projection()["supersessions"].values():
        assert vector["atomic_records"] == 1
        assert vector["governed_state_preconditions"] == 4
        assert vector["durable_replay_is_exact"] is True


def test_malformed_impact_requests_fail_closed_without_residue():
    negatives = _projection()["negative_vectors"]

    for name in (
        "wrong_direction_derived_from_is_not_supersession",
        "superseder_targets_a_different_record",
        "target_outside_the_authorized_closure",
        "future_leakage_before_the_closure_exists",
    ):
        assert negatives[name]["rejected"] is True, name
        assert negatives[name]["error_type"] == "SupersessionImpactAdmissionError", name
    # Exactly the one legitimate Brief remains; no negative left residue.
    assert negatives["durable_brief_count_after_all_negatives"] == 1


def test_world_adds_no_private_supersession_machinery():
    projection = _projection()

    assert projection["impact_policy"] == "lineage_dependency_closure/v1alpha1"
    assert projection["invariants"] == {
        "delivery_authority": False,
        "external_action": False,
        "historical_artifact_rewritten": False,
        "imperative_pack_code": False,
        "live_resources": 0,
        "private_aggregation_in_world": False,
        "private_reasoning_runtime": False,
        "private_source_independence_engine": False,
        "private_status_projector": False,
        "private_supersession_engine": False,
        "world_semantics_added_to_ace": False,
    }


def test_all_four_contract_requests_are_closed():
    projection = _projection()

    assert projection["closed_requests"] == [
        "WI-CR-002",
        "WI-CR-003",
        "WI-CR-004",
        "WI-CR-005",
    ]
    assert projection["runtime_gaps"] == []
    assert projection["proven"]["impact_is_dependency_not_falsehood"] is True
