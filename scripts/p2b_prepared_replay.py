#!/usr/bin/env python3
"""Activation-bound PREPARED replay for the frozen World P2B scenario.

This consumer harness uses only public ACE contracts. It deliberately stops at
the current governed-Brief boundary instead of simulating a private synthesis
aggregator or epistemic projector.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    CanonicalJsonValueV1Alpha1,
    CapabilityBindingV1,
    CaseV1Alpha1,
    EntitySnapshotV1Alpha1,
    EvidenceAcquisitionMode,
    IntelligenceResourceMode,
    ObservationV1Alpha1,
    OrganizationOverlayV1,
    PreparedResourceSetAdmissionV1Alpha1,
    bind_prepared_activation,
    compile_overlay,
    compile_pack_document,
    detect_categorical_shift,
    detect_numeric_shift,
    deterministic_resource_order,
    eligible_signal_routes,
    prepare_activation_revision,
    prepare_domain_activation,
    resource_reference,
    route_categorical_shift_as_signal,
    route_shift_as_signal,
)
from ace.intelligence.contracts.resources import (
    LineageReferenceV1Alpha1,
    LineageRelation,
    LineageResourceKind,
)

from scripts.p2a_compile_acceptance import _encoded, _pack_material, _replace_resource

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"
CONFORMANCE = PACK_ROOT / "conformance"

PRODUCT_ID = "product:world-intelligence-showcase"
ACTIVATED_AT = datetime.fromisoformat("2026-03-09T00:00:00+00:00")

CATEGORICAL_RULES = (
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
    },
)

ADDITIVE_ROUTES = (
    {
        "routing_rule_id": "route_breaking_development",
        "signal_type": "breaking_development",
        "persona_ids": ["general_reader", "public_researcher"],
        "minimum_confidence": 0.8,
        "brief_template_id": "reality_change_brief",
    },
    {
        "routing_rule_id": "route_claim_conflict",
        "signal_type": "claim_conflict",
        "persona_ids": ["general_reader", "public_researcher"],
        "minimum_confidence": 0.8,
        "brief_template_id": "reality_change_brief",
    },
    {
        "routing_rule_id": "route_material_correction",
        "signal_type": "material_correction",
        "persona_ids": ["public_researcher"],
        "minimum_confidence": 0.8,
        "brief_template_id": "reality_change_brief",
    },
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compile_replay_pack():
    """Compile an additive 0.2.0 consumer revision without mutating the frozen pack."""

    manifest, resources = _pack_material()
    manifest["metadata"]["version"] = "0.2.0"

    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    source = next(item for item in ontology["entity_types"] if item["entity_type_id"] == "source")
    source["attributes"].append({"attribute_id": "record_status", "value_type": "string", "required": False})
    _replace_resource(manifest, resources, "modules/ontology.json", ontology)

    detection = _load(PACK_ROOT / "modules" / "detection.json")
    detection["contract"] = "ace.intelligence.detection/v1alpha2"
    detection["categorical_transition_rules"] = list(CATEGORICAL_RULES)
    detection_module = next(item for item in manifest["modules"] if item["module_id"] == "world_detection")
    detection_module["contract"] = detection["contract"]
    _replace_resource(manifest, resources, "modules/detection.json", detection)

    personas = _load(PACK_ROOT / "modules" / "personas.json")
    personas["signal_routing_rules"].extend(ADDITIVE_ROUTES)
    _replace_resource(manifest, resources, "modules/personas.json", personas)
    return compile_pack_document(_encoded(manifest), resources)


def replay_activation_revision():
    """Build the exact additive activation revision shared by every consumer harness."""

    pack = compile_replay_pack()
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id="world_p2b_prepared_replay",
            version="0.2.0",
            pack_id=pack.metadata.pack_id,
            pack_version=pack.metadata.version,
            pack_digest=pack.pack_digest,
        ),
    )
    spec = prepare_domain_activation(
        product_id=PRODUCT_ID,
        activation_key=pack.metadata.pack_id,
        pack=pack,
        overlay=overlay,
        compilation_receipt_ref="receipt:world-p2b-compilation",
        conformance_receipt_refs=("receipt:world-p2b-conformance",),
        capability_bindings=(
            CapabilityBindingV1(
                requirement_id="public_record_snapshot",
                capability="source_snapshot",
                contract="ace.source.snapshot/v1alpha1",
                implementation_id="world_p2b_fixture_snapshot",
                implementation_version="0.1.0",
                artifact_digest="sha256:" + "1" * 64,
            ),
        ),
        authority_bindings=(
            AuthorityBindingV1(
                request_id="read_public_record_source",
                authority="source_read",
                grant_ref="authority_grant:world-p2b-fixture-read",
            ),
        ),
    )
    revision = prepare_activation_revision(
        spec=spec,
        state=ActivationState.ACTIVE,
        actor_ref="principal:world-p2b-reviewer",
        approval_receipt_ref="receipt:world-p2b-approval",
        occurred_at=ACTIVATED_AT,
    )
    return pack, revision


def prepared_binding(*, pack=None, revision=None):
    """Bind the frozen replay revision, or an exact additive one supplied by a consumer.

    Passing no arguments reproduces the frozen WI-CR-005 binding byte for byte.
    """

    if pack is None or revision is None:
        pack, revision = replay_activation_revision()
    return bind_prepared_activation(pack=pack, revision=revision)


def _build_observations(
    binding,
    records: dict[str, dict[str, Any]],
    *,
    link_derivations: bool,
) -> dict[str, ObservationV1Alpha1]:
    """Build every Observation, parents first when derivation lineage is admitted."""

    if not link_derivations:
        return {record_id: _observation(binding, record) for record_id, record in records.items()}

    built: dict[str, ObservationV1Alpha1] = {}
    pending = dict(records)
    while pending:
        progressed = False
        for record_id in sorted(pending):
            record = pending[record_id]
            parent_ids = tuple(
                record[field] for field in DERIVATION_FIELDS if field in record
            )
            if any(parent not in built for parent in parent_ids):
                continue
            built[record_id] = _observation(
                binding,
                record,
                parents=tuple(built[parent] for parent in parent_ids),
            )
            del pending[record_id]
            progressed = True
        if not progressed:
            raise AssertionError(
                f"scenario derivation lineage is not acyclic: {sorted(pending)}"
            )
    return built


def _record_index(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["record_id"]: item for item in scenario["source_records"]}


def _subjects(record_id: str) -> tuple[str, ...]:
    subjects = {
        "record:mwa_bulletin_214": (
            "entity:event/accelerated_reservoir_release",
            "entity:public_indicator/reservoir_storage_percent",
        ),
        "record:mwa_order_47": ("entity:event/accelerated_reservoir_release",),
        "record:assembly_transcript_0310": ("entity:claim/supply_restoration",),
        "record:ledger_report_1088": (
            "entity:claim/farm_allocation_cut",
            "source:ledger_report_1088",
        ),
        "record:ledger_correction_114": ("source:ledger_report_1088",),
        "record:basin_gauge_series_w10": (
            "entity:claim/supply_restoration",
            "entity:claim/farm_allocation_cut",
            "entity:public_indicator/reservoir_storage_percent",
        ),
    }
    return subjects.get(record_id, ())


#: Scenario fields that express "this record came from that record". A consumer
#: may ask for them to be admitted as real ACE Observation lineage so ACE's
#: public derivation-family closure has structure to collapse.
DERIVATION_FIELDS = ("derived_from_record_id", "corrects_record_id")


def _observation(
    binding,
    record: dict[str, Any],
    *,
    parents: tuple[ObservationV1Alpha1, ...] = (),
) -> ObservationV1Alpha1:
    material = _encoded(record)
    digest = hashlib.sha256(material).hexdigest()
    ingested_at = _time(record["ingested_at"])
    return ObservationV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=binding.reference,
        as_of=ingested_at,
        lineage=tuple(_lineage(item) for item in parents),
        source_ref=record["record_id"],
        source_digest=f"sha256:{digest}",
        acquisition_mode=EvidenceAcquisitionMode.PREPARED_FIXTURE,
        acquisition_receipt_ref=f"acquisition:{record['record_id'].split(':', 1)[1]}",
        acquisition_receipt_digest=f"sha256:{hashlib.sha256(('acquired:' + digest).encode()).hexdigest()}",
        source_published_at=_time(record["source_published_at"]),
        event_effective_at=_time(record["event_effective_at"]) if "event_effective_at" in record else None,
        observed_at=_time(record["observed_at"]),
        ingested_at=ingested_at,
        subject_refs=_subjects(record["record_id"]),
        payload=CanonicalJsonValueV1Alpha1(value_json=json.dumps(record, sort_keys=True, separators=(",", ":"))),
        confidence=1.0,
    )


def _lineage(observation: ObservationV1Alpha1) -> LineageReferenceV1Alpha1:
    reference = resource_reference(observation)
    return LineageReferenceV1Alpha1(
        resource_kind=LineageResourceKind.OBSERVATION,
        relation=LineageRelation.DERIVED_FROM,
        resource_id=reference.resource_id,
        resource_digest=reference.resource_digest,
        resource_as_of=reference.as_of,
        resource_available_at=reference.available_at,
    )


def _development_lineage(resource, kind: LineageResourceKind) -> LineageReferenceV1Alpha1:
    reference = resource_reference(resource)
    return LineageReferenceV1Alpha1(
        resource_kind=kind,
        relation=LineageRelation.DERIVED_FROM,
        resource_id=reference.resource_id,
        resource_digest=reference.resource_digest,
        resource_as_of=reference.as_of,
        resource_available_at=reference.available_at,
    )


def _snapshot(
    binding,
    *,
    entity_ref: str,
    entity_type: str,
    attributes: dict[str, Any],
    observations: tuple[ObservationV1Alpha1, ...],
    as_of: datetime,
) -> EntitySnapshotV1Alpha1:
    return EntitySnapshotV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=binding.reference,
        as_of=as_of,
        lineage=tuple(_lineage(item) for item in observations),
        entity_ref=entity_ref,
        entity_type_ref=entity_type,
        attributes=CanonicalJsonValueV1Alpha1(value_json=json.dumps(attributes, sort_keys=True, separators=(",", ":"))),
        projected_at=as_of,
        confidence=1.0,
    )


def _runtime_gaps() -> list[dict[str, str]]:
    return [
        {
            "request_id": "WI-CR-002",
            "boundary": "epistemic_status_projection",
            "finding": "Brief claims expose cited or inference grounding but cannot bind the seven domain statuses per statement.",
        },
        {
            "request_id": "WI-CR-003",
            "boundary": "source_independence_closure",
            "finding": "No public runtime predicate proves that corroboration uses distinct derivation families.",
        },
        {
            "request_id": "WI-CR-004",
            "boundary": "supersession_impact_projection",
            "finding": "No public query enumerates downstream resources affected by a superseding record.",
        },
    ]


def build_replay_material(
    *,
    pack=None,
    revision=None,
    link_derivations: bool = False,
    additional_claim_basis: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Build the frozen scenario material under the frozen or an additive binding.

    ``link_derivations`` admits the scenario's ``derived_from``/``corrects``
    relationships as real ACE Observation lineage. It is off by default so the
    frozen WI-CR-005 and WI-CR-002 packets stay byte-identical.

    ``additional_claim_basis`` widens one claim's current basis records so a
    consumer can bring syndicated copies into the exact Case closure.
    """

    scenario = _load(CONFORMANCE / "p2b_scenario.json")
    expected = _load(CONFORMANCE / "p2b_expected.json")
    records = _record_index(scenario)
    binding = prepared_binding(pack=pack, revision=revision)
    observations = _build_observations(binding, records, link_derivations=link_derivations)

    indicator = scenario["indicator_snapshots"]
    indicator_baseline_obs = observations[indicator[0]["source_record_id"]]
    indicator_current_obs = observations[indicator[1]["source_record_id"]]
    indicator_baseline = _snapshot(
        binding,
        entity_ref=indicator[0]["indicator_entity_id"],
        entity_type="public_indicator",
        attributes={
            "name": "Reservoir storage",
            "value": indicator[0]["value"],
            "unit": indicator[0]["unit"],
            "jurisdiction": indicator[0]["jurisdiction"],
        },
        observations=(indicator_baseline_obs,),
        as_of=indicator_baseline_obs.ingested_at,
    )
    indicator_current = _snapshot(
        binding,
        entity_ref=indicator[1]["indicator_entity_id"],
        entity_type="public_indicator",
        attributes={
            "name": "Reservoir storage",
            "value": indicator[1]["value"],
            "unit": indicator[1]["unit"],
            "jurisdiction": indicator[1]["jurisdiction"],
        },
        observations=(indicator_current_obs,),
        as_of=indicator_current_obs.ingested_at,
    )

    event_timeline = expected["entity_status_timeline"][0]
    event_base_obs = observations[event_timeline["transitions"][0]["basis_record_ids"][0]]
    event_current_obs = observations[event_timeline["transitions"][1]["basis_record_ids"][0]]
    event_baseline = _snapshot(
        binding,
        entity_ref=event_timeline["entity_id"],
        entity_type="event",
        attributes={"name": "Accelerated reservoir release program", "status": "announced"},
        observations=(event_base_obs,),
        as_of=event_base_obs.ingested_at,
    )
    event_current = _snapshot(
        binding,
        entity_ref=event_timeline["entity_id"],
        entity_type="event",
        attributes={"name": "Accelerated reservoir release program", "status": "suspended"},
        observations=(event_current_obs,),
        as_of=event_current_obs.ingested_at,
    )

    correction_base_obs = observations["record:ledger_report_1088"]
    correction_current_obs = observations["record:ledger_correction_114"]
    correction_baseline = _snapshot(
        binding,
        entity_ref="source:ledger_report_1088",
        entity_type="source",
        attributes={
            "name": "Meridia Ledger report 1088",
            "source_category": "secondary_reporting",
            "provenance_family": "family:meridia_ledger_reporting",
            "record_status": "as_published",
        },
        observations=(correction_base_obs,),
        as_of=correction_base_obs.ingested_at,
    )
    correction_current = _snapshot(
        binding,
        entity_ref="source:ledger_report_1088",
        entity_type="source",
        attributes={
            "name": "Meridia Ledger report 1088",
            "source_category": "secondary_reporting",
            "provenance_family": "family:meridia_ledger_reporting",
            "record_status": "corrected",
        },
        observations=(correction_current_obs,),
        as_of=correction_current_obs.ingested_at,
    )

    claim_pairs: dict[str, tuple[EntitySnapshotV1Alpha1, EntitySnapshotV1Alpha1]] = {}
    claim_observations: dict[str, tuple[tuple[ObservationV1Alpha1, ...], tuple[ObservationV1Alpha1, ...]]] = {}
    claim_entities = {item["entity_id"]: item for item in scenario["entities"] if item["entity_type_id"] == "claim"}
    for timeline in expected["claim_status_timeline"]:
        baseline_transition, current_transition = timeline["transitions"]
        entity_ref = timeline["claim_entity_id"]
        current_basis = tuple(current_transition["basis_record_ids"]) + tuple(
            (additional_claim_basis or {}).get(entity_ref, ())
        )
        baseline_observations = tuple(observations[item] for item in baseline_transition["basis_record_ids"])
        current_observations = tuple(observations[item] for item in current_basis)
        statement = claim_entities[entity_ref]["attributes"]["statement"]
        claim_observations[entity_ref] = (baseline_observations, current_observations)
        claim_pairs[entity_ref] = (
            _snapshot(
                binding,
                entity_ref=entity_ref,
                entity_type="claim",
                attributes={"statement": statement, "status": baseline_transition["status"]},
                observations=baseline_observations,
                as_of=max(item.ingested_at for item in baseline_observations),
            ),
            _snapshot(
                binding,
                entity_ref=entity_ref,
                entity_type="claim",
                attributes={"statement": statement, "status": current_transition["status"]},
                observations=current_observations,
                as_of=max(item.ingested_at for item in current_observations),
            ),
        )

    expected_shifts = {item["shift_id"]: item for item in expected["shifts"]}
    numeric = detect_numeric_shift(
        binding=binding,
        detector_id="public_indicator_change",
        baseline=indicator_baseline,
        current=indicator_current,
        detected_at=_time(expected_shifts["shift:public_indicator_reservoir_storage"]["detected_at"]),
    )
    event = detect_categorical_shift(
        binding=binding,
        detector_id="event_status_change",
        baseline=event_baseline,
        current=event_current,
        detected_at=_time(expected_shifts["shift:event_status_suspension"]["detected_at"]),
    )
    correction = detect_categorical_shift(
        binding=binding,
        detector_id="record_correction",
        baseline=correction_baseline,
        current=correction_current,
        detected_at=_time(expected_shifts["shift:record_correction_ledger_1088"]["detected_at"]),
    )
    disputed_pair = claim_pairs["entity:claim/supply_restoration"]
    disputed = detect_categorical_shift(
        binding=binding,
        detector_id="claim_support_change",
        baseline=disputed_pair[0],
        current=disputed_pair[1],
        detected_at=_time(expected_shifts["shift:claim_support_supply_restoration"]["detected_at"]),
    )
    corroborated_pair = claim_pairs["entity:claim/farm_allocation_cut"]
    corroborated = detect_categorical_shift(
        binding=binding,
        detector_id="claim_support_change",
        baseline=corroborated_pair[0],
        current=corroborated_pair[1],
        detected_at=_time(expected_shifts["shift:claim_support_farm_allocation"]["detected_at"]),
    )
    shifts = {
        "public_indicator": numeric,
        "event_status": event,
        "record_correction": correction,
        "claim_disputed": disputed,
        "claim_corroborated": corroborated,
    }
    if any(item is None for item in shifts.values()):
        raise AssertionError("a frozen material transition did not produce a Shift")

    corroboration_observations = {
        str(item.resource_id): item
        for item in (
            observations["record:ledger_report_1088"],
            observations["record:basin_gauge_series_w10"],
        )
    }
    shift_only_resources = (
        *corroboration_observations.values(),
        *corroborated_pair,
        shifts["claim_corroborated"],
    )
    shift_only_admission = PreparedResourceSetAdmissionV1Alpha1(
        admission_key="resource-set:claim-corroboration",
        product_id=PRODUCT_ID,
        activation_revision=binding.reference,
        pack=binding.revision.spec.pack,
        resources=shift_only_resources,
        processing_order=deterministic_resource_order(shift_only_resources),
        admitted_at=shifts["claim_corroborated"].detected_at,
    )

    routed_signal_material = (
        (
            "public_indicator",
            "public_indicator_change",
            route_shift_as_signal,
            _time(expected["signals"][0]["detected_at"]),
        ),
        (
            "event_status",
            "event_status_change",
            route_categorical_shift_as_signal,
            _time(expected["signals"][1]["detected_at"]),
        ),
        (
            "record_correction",
            "record_correction",
            route_categorical_shift_as_signal,
            _time(expected["signals"][2]["detected_at"]),
        ),
        (
            "claim_disputed",
            "claim_support_change",
            route_categorical_shift_as_signal,
            _time(expected["signals"][3]["detected_at"]),
        ),
    )
    signals = {}
    routes = {}
    for key, detector_id, router, detected_at in routed_signal_material:
        signal = router(
            binding=binding,
            detector_id=detector_id,
            shift=shifts[key],
            detected_at=detected_at,
        )
        signals[key] = signal
        eligible = eligible_signal_routes(binding=binding, signal=signal)
        routes[key] = [
            {
                "routing_rule_id": item.routing_rule_id,
                "persona_ids": list(item.persona_ids),
                "brief_template_id": item.brief_template_id,
            }
            for item in eligible
        ]

    developments = (*signals.values(), shifts["claim_corroborated"])
    case_as_of = max(item.as_of for item in developments)
    case_assembled_at = max(item.detected_at for item in developments)
    orientation_case = CaseV1Alpha1(
        product_id=PRODUCT_ID,
        mode=IntelligenceResourceMode.PREPARED,
        activation_revision=binding.reference,
        as_of=case_as_of,
        lineage=(
            *(
                _development_lineage(item, LineageResourceKind.SIGNAL)
                for item in signals.values()
            ),
            _development_lineage(
                shifts["claim_corroborated"],
                LineageResourceKind.SHIFT,
            ),
        ),
        case_type_ref="case_type:reality_change_window",
        title="Meridia reservoir release: 72-hour orientation case",
        purpose="Freeze the exact material developments needed for a governed Reality Brief.",
        subject_refs=tuple(
            sorted({subject for item in developments for subject in item.subject_refs})
        ),
        assembled_at=case_assembled_at,
    )
    all_snapshots = (
        indicator_baseline,
        indicator_current,
        event_baseline,
        event_current,
        correction_baseline,
        correction_current,
        *(snapshot for pair in claim_pairs.values() for snapshot in pair),
    )
    case_resources = (
        *observations.values(),
        *all_snapshots,
        *shifts.values(),
        *signals.values(),
        orientation_case,
    )
    case_admission = PreparedResourceSetAdmissionV1Alpha1(
        admission_key="resource-set:meridia-72h-orientation-case",
        product_id=PRODUCT_ID,
        activation_revision=binding.reference,
        pack=binding.revision.spec.pack,
        resources=case_resources,
        processing_order=deterministic_resource_order(case_resources),
        admitted_at=orientation_case.assembled_at,
    )

    disputed_ref = "entity:claim/supply_restoration"
    corroborated_ref = "entity:claim/farm_allocation_cut"
    return {
        "scenario": scenario,
        "binding": binding,
        "observations": observations,
        "snapshots": all_snapshots,
        "snapshot_pairs": {
            "public_indicator": (indicator_baseline, indicator_current),
            "event_status": (event_baseline, event_current),
            "record_correction": (correction_baseline, correction_current),
            "claim_disputed": claim_pairs[disputed_ref],
            "claim_corroborated": claim_pairs[corroborated_ref],
        },
        "development_observations": {
            "public_indicator": (indicator_baseline_obs, indicator_current_obs),
            "event_status": (event_base_obs, event_current_obs),
            "record_correction": (correction_base_obs, correction_current_obs),
            "claim_disputed": (
                *claim_observations[disputed_ref][0],
                *claim_observations[disputed_ref][1],
            ),
            "claim_corroborated": (
                *claim_observations[corroborated_ref][0],
                *claim_observations[corroborated_ref][1],
            ),
        },
        "shifts": shifts,
        "signals": signals,
        "routes": routes,
        "shift_only_admission": shift_only_admission,
        "orientation_case": orientation_case,
        "case_admission": case_admission,
    }


def run_positive() -> dict[str, Any]:
    material = build_replay_material()
    scenario = material["scenario"]
    binding = material["binding"]
    observations = material["observations"]
    shifts = material["shifts"]
    signals = material["signals"]
    routes = material["routes"]
    shift_only_admission = material["shift_only_admission"]
    orientation_case = material["orientation_case"]
    case_admission = material["case_admission"]
    numeric_delta = shifts["public_indicator"].delta.parsed_value()
    return {
        "contract": "ace.world-intelligence.p2b-prepared-interpreter-replay/v1alpha1",
        "scenario_id": scenario["scenario_id"],
        "pack": {
            "pack_version": binding.pack.metadata.version,
            "compiled_pack_id": binding.pack.compiled_pack_id,
            "pack_digest": binding.pack.pack_digest,
        },
        "activation_revision": binding.reference.model_dump(mode="json"),
        "observation_count": len(observations),
        "shift_count": len(shifts),
        "signal_count": len(signals),
        "shift_types": {key: value.shift_type_ref for key, value in shifts.items()},
        "signal_types": {key: value.signal_type_ref for key, value in signals.items()},
        "routes": routes,
        "numeric_delta_percent": round(numeric_delta["metric_value"], 4),
        "claim_corroboration_has_signal": False,
        "claim_corroboration_resource_set": {
            "admission_id": shift_only_admission.admission_id,
            "admission_digest": shift_only_admission.admission_digest,
            "resource_count": len(shift_only_admission.resources),
            "contains_signal": any(
                reference.resource_kind.value == "signal"
                for reference in shift_only_admission.processing_order
            ),
        },
        "orientation_case": {
            "case_id": orientation_case.resource_id,
            "case_digest": orientation_case.resource_digest,
            "member_count": len(orientation_case.lineage),
            "member_ids": [item.resource_id for item in orientation_case.lineage],
            "subject_refs": list(orientation_case.subject_refs),
            "as_of": orientation_case.as_of.isoformat(),
            "assembled_at": orientation_case.assembled_at.isoformat(),
        },
        "orientation_case_resource_set": {
            "admission_id": case_admission.admission_id,
            "admission_digest": case_admission.admission_digest,
            "resource_count": len(case_admission.resources),
            "case_is_last": case_admission.processing_order[-1].resource_kind.value
            == "case",
        },
        "shift_ids": {key: value.resource_id for key, value in shifts.items()},
        "signal_ids": {key: value.resource_id for key, value in signals.items()},
        "runtime_gaps": _runtime_gaps(),
        "invariants": {
            "frozen_packet_mutated": False,
            "default_pack_mutated": False,
            "private_detector_runtime": False,
            "live_resources": 0,
            "delivery_authority": False,
            "external_action": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_positive(), indent=2, sort_keys=True))
