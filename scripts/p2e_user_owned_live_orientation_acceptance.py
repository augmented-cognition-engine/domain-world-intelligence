#!/usr/bin/env python3
"""Validate the frozen P2E user-owned LIVE-orientation consumer packet.

This is conformance tooling, not a Monitor, Subscription, scheduler, source
transport, or delivery runtime. It freezes the consumer boundary and keeps the
missing generic platform contracts visible instead of simulating them in World.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ace.application import (
    LIVE_MONITORING_RECORD_SPACE,
    MonitoringLifecycleService,
    SensingWindowService,
)
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import (
    CompiledPackRefV1,
    ExactMaterialReferenceV1Alpha1,
    MonitorDisposition,
    MonitoringLifecycleAction,
    MonitoringLifecycleRequestV1Alpha1,
    MonitoringTargetKind,
    MonitorV1Alpha1,
    PersonaBindingV1Alpha1,
    SensingWindowDisposition,
    SensingWindowEvaluationV1Alpha1,
    SensingWindowMaterialKind,
    SensingWindowRequestV1Alpha1,
    SensingWindowSuppressionReason,
    SubscriptionDeliveryDisposition,
    SubscriptionV1Alpha1,
)

from scripts.p2d_live_conflict_correction import execute_acceptance

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense"
CONFORMANCE = PACK_ROOT / "conformance"

INPUT_PATH = CONFORMANCE / "p2e_user_owned_live_orientation_input.json"
EXPECTED_PATH = CONFORMANCE / "p2e_user_owned_live_orientation_expected.json"
REQUESTS_PATH = CONFORMANCE / "p2e_contract_requests.json"
NEGATIVE_PATH = CONFORMANCE / "p2e_negative_cases.json"

P2D_PACK_ID = "pack_ir:bb400cc0652622b43c01504e651110e0"
P2D_HISTORICAL_BRIEF_ID = "brief:c3549af0262b100ca65024ee19cbae6e"
P2D_CORRECTED_BRIEF_ID = "brief:806d69d8e41f83f93ee3dc10f58f0d16"
CORRECTION_KIND = "same_lineage_correction"
OWNER_GUARD_REASONS = {"owner_paused", "subscription_revoked"}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("P2E times must be timezone-aware")
    return parsed


def packet_identity(packet: dict[str, Any], expected: dict[str, Any]) -> str:
    identity_free_expected = copy.deepcopy(expected)
    identity_free_expected.pop("packet_identity", None)
    material = {"input": packet, "expected": identity_free_expected}
    return f"sha256:{hashlib.sha256(_canonical(material)).hexdigest()}"


def build_static_intent_contracts(
    packet: dict[str, Any] | None = None,
) -> tuple[MonitorV1Alpha1, PersonaBindingV1Alpha1, SubscriptionV1Alpha1]:
    """Construct the public ACE 0.5.0 intent contracts with exact identity."""

    packet = copy.deepcopy(packet) if packet is not None else _load(INPUT_PATH)
    ownership = packet["ownership"]
    prerequisites = packet["prerequisites"]
    compiled_pack = CompiledPackRefV1(
        pack_id="world_intelligence_planetary_defense",
        pack_version="0.1.0",
        compiled_pack_id=prerequisites["compiled_pack_id"],
        pack_digest=prerequisites["pack_digest"],
    )
    monitor = MonitorV1Alpha1(
        monitor_id=ownership["monitor_id"],
        product_id=packet["product_id"],
        subject_entity_type_ids=("planetary_defense_risk_estimate",),
        subject_refs=(ownership["subject_ref"],),
        detection_rule_ids=(
            "cross_source_impact_estimate_divergence",
            "same_source_impact_estimate_revision",
        ),
        compiled_pack=compiled_pack,
        activation_revision_ref=prerequisites["activation_revision_ref"],
        disposition=MonitorDisposition.ENABLED,
    )
    persona_binding = PersonaBindingV1Alpha1(
        product_id=packet["product_id"],
        principal_ref=ownership["owner_ref"],
        persona_id=ownership["persona_ids"][0],
        compiled_pack=compiled_pack,
        activation_revision_ref=prerequisites["activation_revision_ref"],
    )
    subscription = SubscriptionV1Alpha1(
        subscription_id=ownership["subscription_id"],
        product_id=packet["product_id"],
        persona_binding_ref=str(persona_binding.binding_ref),
        monitor_refs=(str(monitor.monitor_ref),),
        signal_types=(
            "planetary_defense_estimate_divergence",
            "planetary_defense_estimate_revision",
        ),
        brief_template_ids=(ownership["brief_template_id"],),
        minimum_confidence=0.8,
        delivery=SubscriptionDeliveryDisposition.RECORD_ONLY,
    )
    return monitor, persona_binding, subscription


def _lifecycle_state(packet: dict[str, Any], requested_at: datetime) -> tuple[str, str]:
    monitor_state = "absent"
    subscription_state = "absent"
    for event in sorted(packet["lifecycle"], key=lambda item: _time(item["effective_at"])):
        if _time(event["effective_at"]) > requested_at:
            break
        target = event["target_kind"]
        if target == "monitor":
            if event["event_type"] in {"created", "resumed"}:
                monitor_state = "active"
            elif event["event_type"] == "paused":
                monitor_state = "paused"
            elif event["event_type"] == "revoked":
                monitor_state = "revoked"
        elif target == "subscription":
            if event["event_type"] in {"created", "resumed"}:
                subscription_state = "active"
            elif event["event_type"] == "paused":
                subscription_state = "paused"
            elif event["event_type"] == "revoked":
                subscription_state = "revoked"
    return monitor_state, subscription_state


def validate_packet(
    packet: dict[str, Any],
    expected: dict[str, Any],
    *,
    pinned_identity: str | None = None,
) -> list[str]:
    """Return deterministic fail-closed violations."""

    violations: list[str] = []
    ownership = packet["ownership"]
    owner_ref = ownership.get("owner_ref")

    if not owner_ref:
        violations.append("missing_attention_owner")
    elif (
        ownership.get("monitor_owner_ref") != owner_ref
        or ownership.get("subscription_owner_ref") != owner_ref
        or any(event.get("actor_ref") != owner_ref for event in packet["lifecycle"])
        or any(window.get("requested_by") != owner_ref for window in packet["sensing_windows"])
    ):
        violations.append("attention_owner_changed")

    if (
        packet.get("mode") != "LIVE"
        or packet.get("prepared_material_reused") is not False
        or packet["safety"].get("prepared_record_count") != 0
        or packet["prerequisites"].get("p2d_prepared_record_count") != 0
    ):
        violations.append("prepared_live_mixed")

    if packet.get("static_intent_contracts_constructed") is not True:
        violations.append("static_intent_contract_invalid")
    else:
        try:
            monitor, persona_binding, subscription = build_static_intent_contracts(packet)
        except (KeyError, TypeError, ValueError):
            violations.append("static_intent_contract_invalid")
        else:
            if (
                monitor.monitor_ref != ownership.get("monitor_ref")
                or monitor.monitor_digest != ownership.get("monitor_digest")
                or persona_binding.binding_ref != ownership.get("persona_binding_ref")
                or persona_binding.binding_digest != ownership.get("persona_binding_digest")
                or subscription.subscription_ref != ownership.get("subscription_ref")
                or subscription.subscription_digest != ownership.get("subscription_digest")
                or subscription.delivery is not SubscriptionDeliveryDisposition.RECORD_ONLY
            ):
                violations.append("static_intent_contract_invalid")

    lifecycle_times = [_time(event["effective_at"]) for event in packet["lifecycle"]]
    window_times = [_time(window["requested_at"]) for window in packet["sensing_windows"]]
    if (
        lifecycle_times != sorted(lifecycle_times)
        or window_times != sorted(window_times)
        or any(
            not (
                _time(window["requested_at"])
                <= _time(window["window_started_at"])
                < _time(window["window_ended_at"])
                <= _time(window["evaluated_at"])
            )
            for window in packet["sensing_windows"]
        )
    ):
        violations.append("temporal_incoherence")

    for window in packet["sensing_windows"]:
        monitor_state, subscription_state = _lifecycle_state(packet, _time(window["requested_at"]))
        if window["monitor_state"] != monitor_state or window["subscription_state"] != subscription_state:
            violations.append("lifecycle_state_mismatch")
            break
        if (monitor_state == "paused" or subscription_state == "revoked") and (
            window["acquisition_request_count"] != 0
            or window["candidate_source_keys"]
            or window["accepted_new_source_keys"]
            or window["replayed_source_keys"]
        ):
            violations.append("acquisition_not_authorized")
            break

    for window in packet["sensing_windows"]:
        if window["material_kind"] == CORRECTION_KIND and (
            window["disposition"] != "routed"
            or window["suppression_reason"] is not None
            or window["correction_visible"] is not True
            or not window["accepted_new_source_keys"]
        ):
            violations.append("correction_visibility_lost")
            break
        if window["suppression_reason"] == "no_material_change" and (
            window["material_kind"] != "none"
            or window["accepted_new_source_keys"]
            or not window["replayed_source_keys"]
            or window["correction_visible"] is not False
        ):
            violations.append("invalid_no_material_change_suppression")
            break

    source_policy = packet["source_policy"]
    if (
        sorted(source_policy["publication_roots"]) != ["ESA", "NASA"]
        or source_policy["publication_root_independence_only"] is not True
        or source_policy["independent_measurements_claimed"] is not False
        or source_policy["same_lineage_revisions_count_as_new_families"] is not False
    ):
        violations.append("false_independence_claim")

    safety = packet["safety"]
    if (
        ownership["delivery_authorized"] is not False
        or packet["cadence_preference"]["scheduler_authorized"] is not False
        or packet["cadence_preference"]["autonomous_execution"] is not False
        or source_policy["transport_enabled_in_packet"] is not False
        or source_policy["network_access"] is not False
        or any(
            safety[key] is not False
            for key in (
                "delivery",
                "publication",
                "persuasion",
                "decision",
                "outcome",
                "external_action",
            )
        )
    ):
        violations.append("external_authority_smuggled")

    prerequisites = packet["prerequisites"]
    if (
        prerequisites["compiled_pack_id"] != P2D_PACK_ID
        or prerequisites["historical_brief_id"] != P2D_HISTORICAL_BRIEF_ID
        or prerequisites["corrected_brief_id"] != P2D_CORRECTED_BRIEF_ID
        or ownership["activation_revision"] != prerequisites["activation_revision_ref"]
    ):
        violations.append("historical_artifact_rewritten")

    if pinned_identity is not None and packet_identity(packet, expected) != pinned_identity:
        violations.append("divergent_replay_identity")
    return violations


def projection(packet: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    windows = packet["sensing_windows"]
    requests = _load(REQUESTS_PATH)["requests"]
    negatives = _load(NEGATIVE_PATH)["cases"]
    suppressions = [window["suppression_reason"] for window in windows if window["suppression_reason"] is not None]
    correction_windows = [window for window in windows if window["material_kind"] == CORRECTION_KIND]
    return {
        "mode": packet["mode"],
        "window_count": len(windows),
        "routed_window_count": sum(window["disposition"] == "routed" for window in windows),
        "suppressed_window_count": sum(window["disposition"] == "suppressed" for window in windows),
        "suppression_reasons": suppressions,
        "owner_guarded_zero_acquisition_windows": sum(
            window["suppression_reason"] in OWNER_GUARD_REASONS and window["acquisition_request_count"] == 0
            for window in windows
        ),
        "correction_window_count": len(correction_windows),
        "visible_correction_window_count": sum(window["correction_visible"] is True for window in correction_windows),
        "publication_family_count": len(packet["source_policy"]["publication_roots"]),
        "p2d_live_record_count": packet["prerequisites"]["p2d_live_record_count"],
        "prepared_record_count": packet["safety"]["prepared_record_count"],
        "static_intent_contracts_constructed": packet["static_intent_contracts_constructed"],
        "runtime_materialization_claimed": packet["runtime_materialization_claimed"],
        "open_contract_requests": [request["request_id"] for request in requests if request["status"] == "open"],
        "negative_vector_count": len(negatives),
        "network_access": packet["source_policy"]["network_access"],
        "scheduler_authorized": packet["cadence_preference"]["scheduler_authorized"],
        "delivery_authorized": packet["ownership"]["delivery_authorized"],
        "external_action": packet["safety"]["external_action"],
        "violations": validate_packet(
            packet,
            expected,
            pinned_identity=expected["packet_identity"],
        ),
    }


def run_positive() -> dict[str, Any]:
    packet = _load(INPUT_PATH)
    expected = _load(EXPECTED_PATH)
    return projection(packet, expected)


def _exact(reference: str | None, digest: str | None) -> ExactMaterialReferenceV1Alpha1:
    return ExactMaterialReferenceV1Alpha1(reference=str(reference), digest=str(digest))


def _resource_exact(resource: Any) -> ExactMaterialReferenceV1Alpha1:
    return _exact(resource.resource_id, resource.resource_digest)


def _source_request_exact(request: Any) -> ExactMaterialReferenceV1Alpha1:
    return _exact(request.request_id, request.request_digest)


def _source_transaction_exact(admission: Any) -> ExactMaterialReferenceV1Alpha1:
    return _exact(admission.admission_receipt.receipt_id, admission.admission_receipt.receipt_digest)


async def run_runtime_positive() -> dict[str, Any]:
    """Materialize P2E over the exact captured P2D LIVE record graph."""

    packet = _load(INPUT_PATH)
    p2d = await execute_acceptance()
    monitor, persona_binding, subscription = build_static_intent_contracts(packet)
    owner_ref = packet["ownership"]["owner_ref"]
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=packet["product_id"],
        actor_ref=owner_ref,
        authentication_receipt_ref="authentication_receipt:world-planetary-defense-p2e-owner",
        authentication_receipt_digest="sha256:" + "e" * 64,
        authenticated_at=p2d.environment.context.authenticated_at,
        expires_at=p2d.environment.context.expires_at,
    )
    targets = {"monitor": monitor, "subscription": subscription}
    target_kinds = {
        "monitor": MonitoringTargetKind.MONITOR,
        "subscription": MonitoringTargetKind.SUBSCRIPTION,
    }
    target_references = {
        "monitor": _exact(monitor.monitor_ref, monitor.monitor_digest),
        "subscription": _exact(subscription.subscription_ref, subscription.subscription_digest),
    }
    binding_reference = _exact(persona_binding.binding_ref, persona_binding.binding_digest)
    action_by_event = {
        "created": MonitoringLifecycleAction.CREATE,
        "paused": MonitoringLifecycleAction.PAUSE,
        "resumed": MonitoringLifecycleAction.RESUME,
        "revoked": MonitoringLifecycleAction.REVOKE,
    }
    lifecycle_service = MonitoringLifecycleService(store=p2d.environment.store)
    lifecycle_heads: dict[str, Any] = {}
    lifecycle_sequences = {"monitor": 0, "subscription": 0}
    lifecycle_receipts = []
    lifecycle_replays = []
    for event in packet["lifecycle"]:
        target_name = event["target_kind"]
        lifecycle_sequences[target_name] += 1
        prior = lifecycle_heads.get(target_name)
        request = MonitoringLifecycleRequestV1Alpha1(
            transition_key=event["event_id"],
            product_id=packet["product_id"],
            authenticated_context=context,
            target_kind=target_kinds[target_name],
            target=target_references[target_name],
            persona_binding=binding_reference,
            action=action_by_event[event["event_type"]],
            sequence=lifecycle_sequences[target_name],
            prior_receipt=prior.reference() if prior is not None else None,
            requested_at=_time(event["effective_at"]),
        )
        admission = await lifecycle_service.transition(
            request=request,
            persona_binding=persona_binding,
            target=targets[target_name],
            applied_at=_time(event["effective_at"]),
        )
        replay = await MonitoringLifecycleService(store=p2d.environment.store).transition(
            request=request,
            persona_binding=persona_binding,
            target=targets[target_name],
            applied_at=_time(event["effective_at"]),
        )
        lifecycle_heads[target_name] = admission.receipt
        lifecycle_receipts.append(admission.receipt)
        lifecycle_replays.append(replay.replayed and replay.receipt == admission.receipt)

    def lifecycle_at(
        target_kind: MonitoringTargetKind,
        available_at: datetime,
    ) -> ExactMaterialReferenceV1Alpha1:
        candidates = [
            receipt
            for receipt in lifecycle_receipts
            if receipt.target_kind is target_kind and receipt.applied_at <= available_at
        ]
        return max(candidates, key=lambda item: item.sequence).reference()

    routed_by_window = {
        "sensing_window:w1-initial-orientation": (
            p2d.admissions["esa_initial"].observation,
            p2d.admissions["nasa_initial"].observation,
            p2d.divergence.shift,
            p2d.divergence.signal,
            p2d.historical_case,
            p2d.historical_brief,
        ),
        "sensing_window:w3-nasa-correction": (p2d.admissions["nasa_revised"].observation,),
        "sensing_window:w5-esa-correction-after-resume": (
            p2d.admissions["esa_revised"].observation,
            p2d.nasa_revision.shift,
            p2d.nasa_revision.signal,
            p2d.esa_revision.shift,
            p2d.esa_revision.signal,
            p2d.corrected_case,
            p2d.corrected_brief,
        ),
    }
    material_kinds = {
        "none": SensingWindowMaterialKind.NONE,
        "initial_divergence": SensingWindowMaterialKind.MATERIAL_CHANGE,
        CORRECTION_KIND: SensingWindowMaterialKind.CORRECTION,
    }
    dispositions = {
        "routed": SensingWindowDisposition.ROUTED,
        "suppressed": SensingWindowDisposition.SUPPRESSED,
    }
    suppression_reasons = {item.value: item for item in SensingWindowSuppressionReason}
    sensing_service = SensingWindowService(store=p2d.environment.store)
    window_receipts = []
    window_replays = []
    for window in packet["sensing_windows"]:
        window_started_at = _time(window["window_started_at"])
        request = SensingWindowRequestV1Alpha1(
            window_key=window["window_id"],
            product_id=packet["product_id"],
            authenticated_context=context,
            monitor_lifecycle=lifecycle_at(MonitoringTargetKind.MONITOR, window_started_at),
            subscription_lifecycle=lifecycle_at(MonitoringTargetKind.SUBSCRIPTION, window_started_at),
            requested_at=_time(window["requested_at"]),
            window_started_at=window_started_at,
            window_ended_at=_time(window["window_ended_at"]),
        )
        candidate_keys = tuple(window["candidate_source_keys"])
        accepted_keys = tuple(window["accepted_new_source_keys"])
        replayed_keys = tuple(window["replayed_source_keys"])
        if len(candidate_keys) != window["acquisition_request_count"]:
            raise AssertionError("frozen sensing-window acquisition count crossed its candidate requests")
        evaluation = SensingWindowEvaluationV1Alpha1(
            request=request.reference(),
            acquisition_requests=tuple(_source_request_exact(p2d.environment.requests[key]) for key in candidate_keys),
            source_transactions=tuple(_source_transaction_exact(p2d.admissions[key]) for key in candidate_keys),
            accepted_resources=tuple(_resource_exact(p2d.admissions[key].observation) for key in accepted_keys),
            replayed_resources=tuple(_resource_exact(p2d.admissions[key].observation) for key in replayed_keys),
            routed_resources=tuple(_resource_exact(item) for item in routed_by_window.get(window["window_id"], ())),
            material_kind=material_kinds[window["material_kind"]],
            disposition=dispositions[window["disposition"]],
            suppression_reason=(
                suppression_reasons[window["suppression_reason"]] if window["suppression_reason"] is not None else None
            ),
            correction_visible=window["correction_visible"],
            evaluated_at=_time(window["evaluated_at"]),
        )
        admission = await sensing_service.record(request=request, evaluation=evaluation)
        replay = await SensingWindowService(store=p2d.environment.store).record(
            request=request,
            evaluation=evaluation,
        )
        window_receipts.append(admission.receipt)
        window_replays.append(replay.replayed and replay.receipt == admission.receipt)

    live_records = tuple(
        record
        for record in p2d.environment.store.records.values()
        if record.record_space in {"live", LIVE_MONITORING_RECORD_SPACE}
    )
    prepared_records = tuple(
        record for record in p2d.environment.store.records.values() if record.record_space == "prepared"
    )
    monitoring_records = tuple(
        record
        for record in p2d.environment.store.records.values()
        if record.record_space == LIVE_MONITORING_RECORD_SPACE
    )
    lineage_resources = (
        *(p2d.admissions[key].observation for key in ("esa_initial", "nasa_initial", "nasa_revised", "esa_revised")),
        p2d.divergence.shift,
        p2d.nasa_revision.shift,
        p2d.esa_revision.shift,
        p2d.divergence.signal,
        p2d.nasa_revision.signal,
        p2d.esa_revision.signal,
        p2d.historical_case,
        p2d.corrected_case,
        p2d.historical_brief,
        p2d.corrected_brief,
    )
    p2d_record_keys = {
        record.record_key for record in p2d.environment.store.records.values() if record.record_space == "live"
    }
    return {
        "contract": "ace.world-intelligence.p2e-user-owned-live-orientation-runtime/v1alpha1",
        "mode": "LIVE",
        "lifecycle_receipt_ids": [str(item.receipt_id) for item in lifecycle_receipts],
        "sensing_window_receipt_ids": [str(item.receipt_id) for item in window_receipts],
        "all_lifecycle_replays_exact": all(lifecycle_replays),
        "all_window_replays_exact": all(window_replays),
        "monitoring_record_count": len(monitoring_records),
        "p2d_live_record_count": p2d.projection["separation"]["live_record_count"],
        "composed_live_record_count": len(live_records),
        "prepared_record_count": len(prepared_records),
        "official_publication_roots": p2d.projection["source"]["independent_claimant_roots"],
        "source_observation_ids": [
            str(p2d.admissions[key].observation.resource_id)
            for key in ("esa_initial", "nasa_initial", "nasa_revised", "esa_revised")
        ],
        "shift_ids": [
            str(item.resource_id) for item in (p2d.divergence.shift, p2d.nasa_revision.shift, p2d.esa_revision.shift)
        ],
        "signal_ids": [
            str(item.resource_id) for item in (p2d.divergence.signal, p2d.nasa_revision.signal, p2d.esa_revision.signal)
        ],
        "case_ids": [str(p2d.historical_case.resource_id), str(p2d.corrected_case.resource_id)],
        "reality_brief_ids": [
            str(p2d.historical_brief.resource_id),
            str(p2d.corrected_brief.resource_id),
        ],
        "reality_brief_citation_counts": [
            len(p2d.historical_brief.citations),
            len(p2d.corrected_brief.citations),
        ],
        "correction_windows_visible": all(
            receipt.correction_visible
            for receipt in window_receipts
            if receipt.material_kind is SensingWindowMaterialKind.CORRECTION
        ),
        "owner_guarded_zero_acquisition_windows": sum(
            receipt.suppression_reason
            in {
                SensingWindowSuppressionReason.OWNER_PAUSED,
                SensingWindowSuppressionReason.SUBSCRIPTION_REVOKED,
            }
            and not receipt.acquisition_requests
            and not receipt.source_transactions
            for receipt in window_receipts
        ),
        "scheduler_authority": any(receipt.scheduler_authority for receipt in window_receipts),
        "delivery_authority": any(receipt.delivery_authority for receipt in window_receipts),
        "external_action_authority": any(receipt.external_action_authority for receipt in window_receipts),
        "all_lineage_records_persisted": all(str(item.resource_id) in p2d_record_keys for item in lineage_resources),
        "prepared_live_separated": len(prepared_records) == 0,
    }


def _mutated_packet(case_id: str) -> dict[str, Any]:
    packet = copy.deepcopy(_load(INPUT_PATH))
    windows = packet["sensing_windows"]
    if case_id == "missing_owner":
        packet["ownership"]["owner_ref"] = ""
    elif case_id == "owner_changed":
        packet["lifecycle"][2]["actor_ref"] = "principal:other-user"
    elif case_id == "prepared_live_mix":
        packet["prepared_material_reused"] = True
    elif case_id == "acquisition_while_paused":
        windows[3]["acquisition_request_count"] = 1
    elif case_id == "acquisition_after_revocation":
        windows[5]["acquisition_request_count"] = 1
    elif case_id == "correction_suppressed":
        windows[2]["disposition"] = "suppressed"
        windows[2]["suppression_reason"] = "no_material_change"
        windows[2]["correction_visible"] = False
    elif case_id == "false_measurement_independence":
        packet["source_policy"]["independent_measurements_claimed"] = True
    elif case_id == "hidden_delivery":
        packet["ownership"]["delivery_authorized"] = True
    elif case_id == "autonomous_schedule":
        packet["cadence_preference"]["scheduler_authorized"] = True
        packet["cadence_preference"]["autonomous_execution"] = True
    elif case_id == "history_rewrite":
        packet["prerequisites"]["historical_brief_id"] = "brief:rewritten"
    elif case_id == "divergent_replay":
        windows[1]["requested_at"] = "2026-08-11T18:06:01+00:00"
    else:
        raise KeyError(case_id)
    return packet


def run_negative_cases() -> dict[str, str]:
    expected = _load(EXPECTED_PATH)
    pinned_identity = expected["packet_identity"]
    results: dict[str, str] = {}
    for item in _load(NEGATIVE_PATH)["cases"]:
        violations = validate_packet(
            _mutated_packet(item["case_id"]),
            expected,
            pinned_identity=pinned_identity,
        )
        results[item["case_id"]] = violations[0] if violations else "accepted"
    return results


def main() -> None:
    packet = _load(INPUT_PATH)
    expected = _load(EXPECTED_PATH)
    print(
        json.dumps(
            {
                "contract": "ace.world-intelligence.p2e-user-owned-live-orientation-proof/v1alpha1",
                "packet_identity": packet_identity(packet, expected),
                "projection": projection(packet, expected),
                "runtime": asyncio.run(run_runtime_positive()),
                "negative_vectors": run_negative_cases(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
