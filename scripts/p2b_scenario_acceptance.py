#!/usr/bin/env python3
"""Hermetic World Intelligence P2B golden-scenario acceptance.

Validates the frozen 72-hour Meridia scenario packet: reference resolution,
attribution, temporal coherence, append-only history, provenance-family
independence, epistemic statement rules, persona invariance, context closure,
and exact replay identity. The validator inspects frozen fixtures only; it is
conformance tooling, not a reasoning runtime, detector, or truth adjudicator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timedelta
from importlib.resources import files
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"

EPISTEMIC_STATUSES = (
    "observed",
    "attributed_claim",
    "corroborated",
    "disputed",
    "inferred",
    "unknown",
    "scenario",
)
SUPPORT_REQUIRED_STATUSES = {"observed", "attributed_claim", "corroborated", "disputed"}
HERMETIC_LOCATOR_PREFIX = "fixture:"


def _pack_root():
    """Prefer the installed pack; namespace packages resolve as Traversable, not Path."""
    if CHECKOUT_PACK_ROOT.joinpath("manifest.json").is_file():
        return CHECKOUT_PACK_ROOT
    try:
        installed = files("domain_packs.world_intelligence")
    except (ModuleNotFoundError, TypeError):
        return CHECKOUT_PACK_ROOT
    if installed.joinpath("manifest.json").is_file():
        return installed
    return CHECKOUT_PACK_ROOT


PACK_ROOT = _pack_root()
CONFORMANCE = PACK_ROOT / "conformance"


def _load(path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def _sha256(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def record_digests(scenario: dict[str, Any]) -> dict[str, str]:
    return {record["record_id"]: _sha256(record) for record in scenario["source_records"]}


def packet_identity(scenario: dict[str, Any], expected: dict[str, Any]) -> str:
    return _sha256({"scenario": scenario, "expected": expected})


def _entity_type(entity_id: str, declared: dict[str, str]) -> str | None:
    if entity_id in declared:
        return declared[entity_id]
    if entity_id.startswith("source:"):
        return "source"
    return None


def _family_roots(scenario: dict[str, Any]) -> dict[str, str]:
    """Resolve each record to the family of its derivation root."""
    records = {record["record_id"]: record for record in scenario["source_records"]}
    resolved: dict[str, str] = {}
    for record_id, record in records.items():
        seen = {record_id}
        cursor = record
        while cursor.get("derived_from_record_id") in records:
            parent_id = cursor["derived_from_record_id"]
            if parent_id in seen:
                break
            seen.add(parent_id)
            cursor = records[parent_id]
        resolved[record_id] = cursor["provenance_family_id"]
    return resolved


def validate_packet(
    scenario: dict[str, Any],
    expected: dict[str, Any],
    pinned_identity: str,
) -> list[str]:
    """Return fail-closed violations in deterministic first-failure order."""
    violations: list[str] = []
    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    relation_types = {item["relation_type_id"]: item for item in ontology["relation_types"]}

    declared_types = {item["entity_id"]: item["entity_type_id"] for item in scenario["entities"]}
    records = {record["record_id"]: record for record in scenario["source_records"]}
    source_entities = {record["source_entity_id"] for record in scenario["source_records"]}
    families = {item["family_id"] for item in scenario["provenance_families"]}
    known_nodes = set(declared_types) | source_entities
    brief = expected["brief"]
    statements = brief["statements"]

    def check_reference_resolution() -> None:
        for relation in scenario["relations"]:
            declaration = relation_types.get(relation["relation_type_id"])
            source_type = _entity_type(relation["source_entity_id"], declared_types)
            target_type = _entity_type(relation["target_entity_id"], declared_types)
            if (
                declaration is None
                or relation["source_entity_id"] not in known_nodes
                or relation["target_entity_id"] not in known_nodes
                or source_type not in declaration["source_entity_types"]
                or target_type not in declaration["target_entity_types"]
            ):
                violations.append("unresolved_reference")
                return
        for record in scenario["source_records"]:
            if record["provenance_family_id"] not in families:
                violations.append("unresolved_reference")
                return
            if not record["locator"].startswith(HERMETIC_LOCATOR_PREFIX):
                violations.append("nonhermetic_locator")
                return
        for statement in statements:
            refs = list(statement["support_record_ids"])
            refs.extend(statement.get("inference_basis_record_ids", []))
            if any(ref not in records for ref in refs):
                violations.append("unresolved_reference")
                return

    def check_claim_attribution() -> None:
        attribution_edges: dict[str, int] = {}
        for relation in scenario["relations"]:
            if relation["relation_type_id"] == "actor_made_claim":
                target = relation["target_entity_id"]
                attribution_edges[target] = attribution_edges.get(target, 0) + 1
        for entity in scenario["entities"]:
            if entity["entity_type_id"] == "claim" and attribution_edges.get(entity["entity_id"], 0) != 1:
                violations.append("missing_claim_attribution")
                return

    def check_temporal_coherence() -> None:
        window = scenario["window"]
        starts = _time(window["starts_at"])
        ends = _time(window["ends_at"])
        if ends - starts != timedelta(hours=window["duration_hours"]):
            violations.append("temporal_incoherence")
            return
        for record in scenario["source_records"]:
            published = _time(record["source_published_at"])
            observed = _time(record["observed_at"])
            ingested = _time(record["ingested_at"])
            ordered = published <= observed <= ingested
            if "event_effective_at" in record:
                ordered = ordered and _time(record["event_effective_at"]) <= published
            if not ordered or not (starts <= published and ingested <= ends):
                violations.append("temporal_incoherence")
                return
            parent_id = record.get("derived_from_record_id")
            if parent_id is not None:
                parent = records.get(parent_id)
                if parent is None or _time(record["derived_at"]) < _time(parent["source_published_at"]):
                    violations.append("temporal_incoherence")
                    return
            corrected_id = record.get("corrects_record_id")
            if corrected_id is not None:
                corrected = records.get(corrected_id)
                if corrected is None or published <= _time(corrected["source_published_at"]):
                    violations.append("temporal_incoherence")
                    return

    def check_append_only_history() -> None:
        pinned = expected["record_digests"]
        for record in scenario["source_records"]:
            if pinned.get(record["record_id"]) != _sha256(record):
                violations.append("historical_record_rewritten")
                return

    def check_provenance_independence() -> None:
        resolved = _family_roots(scenario)
        for record_id, family_id in resolved.items():
            if records[record_id]["provenance_family_id"] != family_id:
                violations.append("false_independent_corroboration")
                return
        membership = {
            family_id: sorted(
                record_id for record_id, resolved_family in resolved.items() if resolved_family == family_id
            )
            for family_id in sorted(families)
        }
        if membership != expected["provenance"]["family_membership"]:
            violations.append("false_independent_corroboration")
            return
        minimum = expected["provenance"]["independent_corroboration_minimum_families"]
        corroborated_items: list[tuple[list[str], list[str] | None]] = [
            (statement["support_record_ids"], statement.get("independent_family_ids"))
            for statement in statements
            if statement["epistemic_status"] == "corroborated"
        ]
        for timeline in expected["claim_status_timeline"]:
            for transition in timeline["transitions"]:
                if transition["status"] == "corroborated":
                    corroborated_items.append((transition["basis_record_ids"], None))
        for support_ids, declared_families in corroborated_items:
            support_families = sorted({resolved[record_id] for record_id in support_ids if record_id in resolved})
            if len(support_families) < minimum:
                violations.append("false_independent_corroboration")
                return
            if declared_families is not None and declared_families != support_families:
                violations.append("false_independent_corroboration")
                return

    def check_statement_rules() -> None:
        for statement in statements:
            status = statement["epistemic_status"]
            if status not in EPISTEMIC_STATUSES:
                violations.append("unknown_epistemic_status")
                return
            if "inference_basis_record_ids" in statement and status != "inferred":
                violations.append("inference_presented_as_observation")
                return
            if status == "inferred" and (
                not statement.get("inference_basis_record_ids") or not statement.get("uncertainty")
            ):
                violations.append("inference_presented_as_observation")
                return
            if status == "scenario" and (not statement.get("assumptions") or not statement.get("watchpoints")):
                violations.append("scenario_presented_as_prediction")
                return
            if status in SUPPORT_REQUIRED_STATUSES and not statement["support_record_ids"]:
                violations.append("unsupported_material_statement")
                return
            if status == "unknown" and not statement.get("resolution_watch"):
                violations.append("unsupported_material_statement")
                return

    def check_persona_invariance() -> None:
        if brief["persona_status_overrides"]:
            violations.append("persona_dependent_evidence_status")

    def check_context_closure() -> None:
        cutoff = _time(brief["context_cutoff_at"])
        if not _time(brief["brief_as_of"]) <= cutoff <= _time(brief["generated_at"]):
            violations.append("stale_closure")
            return
        for statement in statements:
            for record_id in statement["support_record_ids"]:
                if _time(records[record_id]["ingested_at"]) > cutoff:
                    violations.append("stale_closure")
                    return

    def check_replay_identity() -> None:
        if packet_identity(scenario, expected) != pinned_identity:
            violations.append("divergent_replay_identity")

    for check in (
        check_reference_resolution,
        check_claim_attribution,
        check_temporal_coherence,
        check_append_only_history,
        check_provenance_independence,
        check_statement_rules,
        check_persona_invariance,
        check_context_closure,
        check_replay_identity,
    ):
        check()
        if violations:
            return violations
    return violations


def _packet_material() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    scenario = _load(CONFORMANCE / "p2b_scenario.json")
    expected = _load(CONFORMANCE / "p2b_expected.json")
    manifest = _load(CONFORMANCE / "p2b_manifest.json")
    return scenario, expected, manifest


def build_projection(
    scenario: dict[str, Any],
    expected: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    brief = expected["brief"]
    statements = brief["statements"]
    entity_counts: dict[str, int] = {}
    for entity in scenario["entities"]:
        entity_counts[entity["entity_type_id"]] = entity_counts.get(entity["entity_type_id"], 0) + 1
    entity_counts["source"] = len(scenario["source_records"])
    relation_counts: dict[str, int] = {}
    for relation in scenario["relations"]:
        relation_counts[relation["relation_type_id"]] = relation_counts.get(relation["relation_type_id"], 0) + 1
    status_counts: dict[str, int] = {}
    for statement in statements:
        status = statement["epistemic_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    baseline, current = (snapshot["value"] for snapshot in scenario["indicator_snapshots"])
    return {
        "contract": "ace.world-intelligence.p2b-scenario-evidence/v1alpha1",
        "scenario_id": scenario["scenario_id"],
        "window_hours": scenario["window"]["duration_hours"],
        "synthetic": scenario["synthetic"],
        "hermetic": scenario["hermetic"],
        "entity_count_by_type": dict(sorted(entity_counts.items())),
        "relation_count_by_type": dict(sorted(relation_counts.items())),
        "provenance_family_count": len(scenario["provenance_families"]),
        "source_record_count": len(scenario["source_records"]),
        "supersession_count": len(expected["supersessions"]),
        "numeric_shift_delta_percent": round((current - baseline) / baseline * 100, 4),
        "runtime_supported_shift_ids": sorted(
            item["shift_id"] for item in expected["shifts"] if item["runtime_supported"]
        ),
        "contract_blocked_shift_ids": sorted(
            item["shift_id"] for item in expected["shifts"] if not item["runtime_supported"]
        ),
        "runtime_supported_signal_ids": sorted(
            item["signal_id"] for item in expected["signals"] if item["runtime_supported"]
        ),
        "contract_blocked_signal_ids": sorted(
            item["signal_id"] for item in expected["signals"] if not item["runtime_supported"]
        ),
        "blocking_contract_request_ids": sorted(
            {
                item["blocked_by_contract_request_id"]
                for item in (*expected["shifts"], *expected["signals"])
                if not item["runtime_supported"]
            }
        ),
        "brief_section_order": list(brief["section_order"]),
        "brief_statement_count": len(statements),
        "epistemic_status_counts": dict(sorted(status_counts.items())),
        "all_seven_statuses_present": sorted(status_counts) == sorted(EPISTEMIC_STATUSES),
        "violations": validate_packet(scenario, expected, manifest["packet_identity"]),
        "packet_identity": packet_identity(scenario, expected),
    }


def run_positive() -> dict[str, Any]:
    scenario, expected, manifest = _packet_material()
    return build_projection(scenario, expected, manifest)


def run_negative_cases() -> dict[str, str]:
    baseline_scenario, baseline_expected, manifest = _packet_material()
    results: dict[str, str] = {}

    def rejected(case_id: str, scenario: dict[str, Any], expected: dict[str, Any]) -> None:
        found = validate_packet(scenario, expected, manifest["packet_identity"])
        if not found:
            raise AssertionError(f"invalid P2B mutation {case_id!r} validated cleanly")
        results[case_id] = found[0]

    def statement(expected: dict[str, Any], statement_id: str) -> dict[str, Any]:
        return next(item for item in expected["brief"]["statements"] if item["statement_id"] == statement_id)

    scenario = copy.deepcopy(baseline_scenario)
    scenario["relations"] = [
        item for item in scenario["relations"] if item["relation_id"] != "rel:quell_made_allocation_claim"
    ]
    rejected("missing_attribution", scenario, baseline_expected)

    expected = copy.deepcopy(baseline_expected)
    statement(expected, "stmt:sa_allocation")["support_record_ids"] = [
        "record:coastal_wire_5521",
        "record:ledger_report_1088",
    ]
    rejected("false_independent_corroboration", baseline_scenario, expected)

    scenario = copy.deepcopy(baseline_scenario)
    report = next(item for item in scenario["source_records"] if item["record_id"] == "record:ledger_report_1088")
    report["statement_text"] = report["statement_text"].replace("40 percent", "14 percent")
    rejected("history_rewrite", scenario, baseline_expected)

    expected = copy.deepcopy(baseline_expected)
    statement(expected, "stmt:inf_suspension_driver")["epistemic_status"] = "observed"
    rejected("inference_as_observation", baseline_scenario, expected)

    expected = copy.deepcopy(baseline_expected)
    statement(expected, "stmt:wp_rationing_scenario")["assumptions"] = []
    rejected("scenario_as_prediction", baseline_scenario, expected)

    expected = copy.deepcopy(baseline_expected)
    expected["brief"]["persona_status_overrides"] = [
        {
            "persona_id": "general_reader",
            "statement_id": "stmt:sc_supply",
            "epistemic_status": "corroborated",
        }
    ]
    rejected("persona_dependent_evidence_status", baseline_scenario, expected)

    expected = copy.deepcopy(baseline_expected)
    statement(expected, "stmt:wh_announcement")["support_record_ids"] = []
    rejected("unsupported_claim", baseline_scenario, expected)

    expected = copy.deepcopy(baseline_expected)
    expected["brief"]["context_cutoff_at"] = "2026-03-12T00:00:00Z"
    rejected("stale_closure", baseline_scenario, expected)

    expected = copy.deepcopy(baseline_expected)
    expected["brief"]["generated_at"] = "2026-03-13T07:00:01Z"
    rejected("divergent_replay", baseline_scenario, expected)

    return results


def run_acceptance() -> dict[str, Any]:
    positive = run_positive()
    scenario, expected, manifest = _packet_material()
    if positive != manifest["expected_projection"]:
        raise AssertionError("World P2B positive projection diverged from pinned evidence")
    if positive["violations"]:
        raise AssertionError(f"World P2B packet failed coherence: {positive['violations']}")
    if expected["record_digests"] != record_digests(scenario):
        raise AssertionError("World P2B record digests diverged from admitted records")
    return {"positive": positive, "negative_cases": run_negative_cases()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--negative", action="store_true", help="include negative-case results")
    args = parser.parse_args()
    result = run_acceptance() if args.negative else run_positive()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
