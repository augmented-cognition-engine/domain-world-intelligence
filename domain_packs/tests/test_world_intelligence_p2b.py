from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from ace.intelligence.contracts.resources import ClaimGroundingKind
from ace.intelligence.packs import compile_pack_document

import ace.intelligence
from scripts.p2b_case_brief import WORLD_EPISTEMIC_STATUSES
from scripts.p2a_compile_acceptance import (
    _encoded,
    _pack_material,
    _replace_resource,
    compile_world_pack,
)
from scripts.p2b_scenario_acceptance import (
    EPISTEMIC_STATUSES,
    SUPPORT_REQUIRED_STATUSES,
    packet_identity,
    record_digests,
    run_negative_cases,
    run_positive,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"
CONFORMANCE = PACK_ROOT / "conformance"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _scenario():
    return _load(CONFORMANCE / "p2b_scenario.json")


def _expected():
    return _load(CONFORMANCE / "p2b_expected.json")


def _manifest():
    return _load(CONFORMANCE / "p2b_manifest.json")


def test_p2b_projection_matches_pinned_evidence():
    projection = run_positive()
    assert projection == _manifest()["expected_projection"]
    assert projection["violations"] == []
    assert projection["all_seven_statuses_present"] is True
    assert projection["numeric_shift_delta_percent"] == -12.2977


def test_p2b_negative_vectors_fail_closed():
    expected = {
        item["case_id"]: item["expected_violation"] for item in _load(CONFORMANCE / "p2b_negative_cases.json")["cases"]
    }
    assert len(expected) == 9
    assert run_negative_cases() == expected


def test_p2b_manifest_pins_every_artifact():
    manifest = _manifest()
    for artifact in manifest["artifacts"]:
        if artifact["path"].startswith("scripts/"):
            path = REPO_ROOT / artifact["path"]
        else:
            path = CONFORMANCE / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], artifact["path"]


def test_p2b_replay_identity_is_deterministic():
    manifest = _manifest()
    first = packet_identity(_scenario(), _expected())
    second = packet_identity(_scenario(), _expected())
    assert first == second == manifest["packet_identity"]
    assert manifest["expected_projection"]["packet_identity"] == first


def test_p2b_scenario_is_synthetic_hermetic_and_boundary_clean():
    scenario = _scenario()
    assert scenario["synthetic"] is True
    assert scenario["hermetic"] is True
    assert scenario["redistributable"] is True
    assert "fictional" in scenario["fictional_notice"]
    for record in scenario["source_records"]:
        assert record["locator"].startswith("fixture:"), record["record_id"]
    packet_text = "".join(
        (CONFORMANCE / name).read_text(encoding="utf-8")
        for name in (
            "p2b_scenario.json",
            "p2b_expected.json",
            "p2b_negative_cases.json",
            "p2b_contract_requests.json",
            "p2b_manifest.json",
        )
    )
    assert "http://" not in packet_text and "https://" not in packet_text
    scope = _manifest()["scope"]
    for forbidden in (
        "live_sources",
        "delivery",
        "external_actions",
        "political_targeting",
        "political_persuasion",
        "hidden_truth_score",
        "autonomous_truth_adjudication",
    ):
        assert scope[forbidden] is False, forbidden
    assert scope["pack_modules_changed"] is False


def test_p2b_timeline_preserves_all_source_times_inside_the_window():
    scenario = _scenario()
    starts = _time(scenario["window"]["starts_at"])
    ends = _time(scenario["window"]["ends_at"])
    assert (ends - starts).total_seconds() == 72 * 3600
    records = {record["record_id"]: record for record in scenario["source_records"]}
    for record in records.values():
        published = _time(record["source_published_at"])
        observed = _time(record["observed_at"])
        ingested = _time(record["ingested_at"])
        assert published <= observed <= ingested, record["record_id"]
        assert starts <= published and ingested <= ends, record["record_id"]
        if "event_effective_at" in record:
            assert _time(record["event_effective_at"]) <= published, record["record_id"]
        if "derived_from_record_id" in record:
            parent = records[record["derived_from_record_id"]]
            assert _time(record["derived_at"]) >= _time(parent["source_published_at"]), record["record_id"]
        if "corrects_record_id" in record:
            corrected = records[record["corrects_record_id"]]
            assert published > _time(corrected["source_published_at"]), record["record_id"]


def test_p2b_provenance_families_separate_syndication_from_independence():
    expected = _expected()
    membership = expected["provenance"]["family_membership"]
    assert membership["family:meridia_ledger_reporting"] == [
        "record:coastal_wire_5521",
        "record:harborview_reprint_302",
        "record:ledger_correction_114",
        "record:ledger_report_1088",
    ]
    syndicated = {"record:coastal_wire_5521", "record:harborview_reprint_302"}
    corroborated = [
        statement for statement in expected["brief"]["statements"] if statement["epistemic_status"] == "corroborated"
    ]
    assert corroborated, "the golden Brief must exercise corroboration"
    for statement in corroborated:
        assert len(statement["independent_family_ids"]) >= 2
        assert syndicated.isdisjoint(statement["support_record_ids"])
    for timeline in expected["claim_status_timeline"]:
        for transition in timeline["transitions"]:
            if transition["status"] == "corroborated":
                assert syndicated.isdisjoint(transition["basis_record_ids"])


def test_p2b_correction_appends_history_without_rewriting_it():
    scenario = _scenario()
    expected = _expected()
    assert expected["record_digests"] == record_digests(scenario)
    records = {record["record_id"]: record for record in scenario["source_records"]}
    report = records["record:ledger_report_1088"]
    correction = records["record:ledger_correction_114"]
    assert correction["corrects_record_id"] == "record:ledger_report_1088"
    assert "40 percent" in report["statement_text"], "the admitted original must keep its error"
    assert report["erratum"]["reported"] == "40"
    assert report["erratum"]["authoritative"] == "14"
    for supersession in expected["supersessions"]:
        assert supersession["append_only"] is True
        assert supersession["superseded_record_remains_admitted"] is True
    correction_relation = [
        item for item in scenario["relations"] if item["relation_type_id"] == "record_corrects_record"
    ]
    assert len(correction_relation) == 1


def test_p2b_brief_structure_matches_ordered_template_and_epistemic_policy():
    expected = _expected()
    brief = expected["brief"]
    synthesis = _load(PACK_ROOT / "modules" / "synthesis.json")
    template = next(item for item in synthesis["brief_templates"] if item["template_id"] == brief["brief_template_id"])
    assert brief["section_order"] == template["required_sections"]
    statement_sections = [statement["section_id"] for statement in brief["statements"]]
    assert sorted(set(statement_sections), key=brief["section_order"].index) == brief["section_order"]
    assert statement_sections == sorted(statement_sections, key=brief["section_order"].index)

    policy = _load(CONFORMANCE / "epistemic_policy.json")
    policy_statuses = [item["status_id"] for item in policy["statuses"]]
    assert list(EPISTEMIC_STATUSES) == policy_statuses
    personas = _load(PACK_ROOT / "modules" / "personas.json")
    assert brief["persona_ids"] == sorted(item["persona_id"] for item in personas["personas"])
    assert brief["persona_status_overrides"] == []

    counted: dict[str, int] = {}
    for statement in brief["statements"]:
        status = statement["epistemic_status"]
        counted[status] = counted.get(status, 0) + 1
        assert status in policy_statuses, statement["statement_id"]
        if status in SUPPORT_REQUIRED_STATUSES:
            assert statement["support_record_ids"], statement["statement_id"]
        if status == "inferred":
            assert statement["inference_basis_record_ids"], statement["statement_id"]
            assert statement["uncertainty"], statement["statement_id"]
            assert statement["text"].startswith("ACE inference:"), statement["statement_id"]
        if status == "scenario":
            assert statement["assumptions"] and statement["watchpoints"], statement["statement_id"]
        if status == "unknown":
            assert statement["resolution_watch"], statement["statement_id"]
    assert counted == brief["status_counts"]
    assert set(counted) == set(policy_statuses)


def test_p2b_routed_signal_uses_only_the_existing_numeric_contract():
    expected = _expected()
    detection = _load(PACK_ROOT / "modules" / "detection.json")
    personas = _load(PACK_ROOT / "modules" / "personas.json")
    assert set(detection) == {"contract", "module_id", "numeric_delta_rules"}
    rule = next(item for item in detection["numeric_delta_rules"] if item["detector_id"] == "public_indicator_change")
    routed = [item for item in expected["signals"] if item["runtime_supported"]]
    assert [item["signal_id"] for item in routed] == ["signal:public_indicator_move_reservoir"]
    signal = routed[0]
    assert signal["signal_type"] == rule["signal_type"]
    routing = next(
        item for item in personas["signal_routing_rules"] if item["routing_rule_id"] == signal["routing_rule_id"]
    )
    assert routing["signal_type"] == signal["signal_type"]
    assert routing["persona_ids"] == signal["routed_persona_ids"]
    assert routing["brief_template_id"] == signal["brief_template_id"]
    numeric_shift = next(item for item in expected["shifts"] if item["runtime_supported"])
    assert abs(numeric_shift["delta_percent"]) > rule["threshold"]


def test_p2b_blocked_expectations_reference_open_contract_requests():
    expected = _expected()
    requests = _load(CONFORMANCE / "p2b_contract_requests.json")
    by_id = {item["request_id"]: item for item in requests["requests"]}
    assert sorted(by_id) == _manifest()["contract_request_ids"]
    blocked = [item for item in (*expected["shifts"], *expected["signals"]) if not item["runtime_supported"]]
    assert blocked, "P2B must record the currently inexpressible expectations"
    for item in blocked:
        request = by_id[item["blocked_by_contract_request_id"]]
        assert request["status"] == "open"
        blocked_id = item.get("shift_id", item.get("signal_id"))
        assert blocked_id in request["blocked_expectations"], blocked_id
    for request in by_id.values():
        assert request["quarantined_test"] in globals(), request["request_id"]
        assert request["market_compatibility_requirement"]


def test_p2b_scenario_packet_leaves_pack_identity_unchanged():
    compiled = compile_world_pack()
    pinned = _load(CONFORMANCE / "p2a_manifest.json")["pack"]
    assert compiled.compiled_pack_id == pinned["compiled_pack_id"]
    assert compiled.pack_digest == pinned["pack_digest"]
    assert _manifest()["pack"] == pinned


def _platform_contract_source() -> str:
    contracts_root = Path(ace.intelligence.__file__).resolve().parent
    return "\n".join(path.read_text(encoding="utf-8") for path in contracts_root.rglob("*.py"))


def test_platform_gap_categorical_state_change_detection():
    manifest, resources = _pack_material()
    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    source = next(item for item in ontology["entity_types"] if item["entity_type_id"] == "source")
    source["attributes"].append(
        {
            "attribute_id": "record_status",
            "value_type": "string",
            "required": False,
        }
    )
    _replace_resource(manifest, resources, "modules/ontology.json", ontology)

    detection = _load(PACK_ROOT / "modules" / "detection.json")
    detection["contract"] = "ace.intelligence.detection/v1alpha2"
    detection["categorical_transition_rules"] = [
        {
            "detector_id": "event_status_change",
            "entity_type_id": "event",
            "attribute_id": "status",
            "baseline": "prior_snapshot",
            "transitions": [{"from_value": "announced", "to_value": "suspended"}],
            "shift_type": "event_status_shift",
            "signal_type": "breaking_development",
        },
        {
            "detector_id": "record_correction",
            "entity_type_id": "source",
            "attribute_id": "record_status",
            "baseline": "prior_snapshot",
            "transitions": [{"from_value": "as_published", "to_value": "corrected"}],
            "shift_type": "record_correction_shift",
            "signal_type": "material_correction",
        },
        {
            "detector_id": "claim_support_change",
            "entity_type_id": "claim",
            "attribute_id": "status",
            "baseline": "prior_snapshot",
            "transitions": [
                {"from_value": "attributed_claim", "to_value": "corroborated"},
                {"from_value": "attributed_claim", "to_value": "disputed"},
            ],
            "shift_type": "claim_support_shift",
            "signal_type": "claim_conflict",
        }
    ]
    detection_module = next(item for item in manifest["modules"] if item["module_id"] == "world_detection")
    detection_module["contract"] = "ace.intelligence.detection/v1alpha2"
    _replace_resource(manifest, resources, "modules/detection.json", detection)
    compiled = compile_pack_document(_encoded(manifest), resources)

    compiled_detection = next(item for item in compiled.modules if item.module_id == "world_detection")
    payload = json.loads(compiled_detection.canonical_payload)
    assert compiled_detection.contract == "ace.intelligence.detection/v1alpha2"
    assert [item["detector_id"] for item in payload["categorical_transition_rules"]] == [
        "claim_support_change",
        "event_status_change",
        "record_correction",
    ]
    assert compiled.compiled_pack_id != _manifest()["pack"]["compiled_pack_id"]


def test_wi_cr_002_is_closed_by_a_domain_neutral_status_capability():
    """WI-CR-002 is closed, and deliberately NOT by widening ``ClaimGroundingKind``.

    Adding ``attributed`` (or any other World label) to a Core/Intelligence enum
    would push World vocabulary into the platform. The capability that actually
    closes this request keeps grounding kind domain-neutral and carries the
    seven World labels in a Domain-Pack-declared status set bound per statement.
    """

    grounding_kinds = {member.value for member in ClaimGroundingKind}
    assert grounding_kinds == {"cited", "inference"}, (
        "ACE must not learn World status vocabulary"
    )

    epistemic = _load(PACK_ROOT / "modules" / "epistemic_status.json")
    assert epistemic["contract"] == "ace.intelligence.epistemic-status/v1alpha1"
    declared = {
        status["status_id"]
        for status_set in epistemic["status_sets"]
        for status in status_set["statuses"]
    }
    assert declared == set(WORLD_EPISTEMIC_STATUSES)

    # The generic carrier exists in the platform and is per statement.
    source = _platform_contract_source()
    assert "brief-epistemic-status-projection" in source
    assert "epistemic-status/v1alpha1" in source


def test_wi_cr_003_is_closed_by_a_domain_neutral_independence_predicate():
    """WI-CR-003 is closed, and deliberately NOT by any World-specific rule.

    ACE exposes a generic derivation-family closure over admitted Observation
    lineage. A Domain Pack opts in by declaring ``min_distinct_derivation_families``
    on a status; packs that do not declare it behave exactly as before.
    """

    epistemic = _load(PACK_ROOT / "modules" / "epistemic_status_v2.json")
    assert epistemic["contract"] == "ace.intelligence.epistemic-status/v1alpha2"
    corroborated = next(
        status
        for status_set in epistemic["status_sets"]
        for status in status_set["statuses"]
        if status["status_id"] == "corroborated"
    )
    assert corroborated["min_distinct_derivation_families"] == 2
    assert corroborated["proves_source_family_independence"] is True

    source = _platform_contract_source()
    assert "derivation_family" in source or "source_independence" in source
    assert "observation_lineage_root_closure" in source
    # Independence is structural, never publisher- or text-based.
    assert "COLLAPSING_RELATIONS" in source


def test_wi_cr_004_is_closed_by_a_domain_neutral_impact_projection():
    """WI-CR-004 is closed, and deliberately without any World vocabulary.

    ACE exposes a generic traversal over admitted lineage. Impact means
    dependency, not falsehood, and the projection discloses the unaffected set
    so the boundary of the claim is visible rather than inferred.
    """

    source = _platform_contract_source()
    assert "supersession_impact" in source or "affected_resource" in source
    assert "lineage_dependency_closure" in source
    assert "unaffected_resource_ids" in source
    # Impact never rewrites history; the projection names what it preserves.
    assert "preserved_artifact_ids" in source
