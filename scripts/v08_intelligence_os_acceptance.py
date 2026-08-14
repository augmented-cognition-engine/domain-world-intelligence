"""ACE 0.8 World Intelligence resource-plane acceptance.

This composes the already accepted P2C2/P2C3 journey, then reads its durable
state only through the public, domain-neutral Intelligence resource contracts.
It performs no network request and no new external effect beyond the existing
reviewed create-only workspace fixture.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ace.application import (
    ActionResourceProjectionReader,
    AgentMemoryResourceProjectionReader,
    AgentResourceProjectionReader,
    CompositeIntelligenceResourceProjectionReader,
    DecisionOutcomeFeedbackResourceProjectionReader,
    IntelligenceLedgerResourceProjectionReader,
    IntelligenceResourcePlaneService,
    LiveSourceResourceProjectionReader,
    MonitoringResourceProjectionReader,
)
from ace.core import (
    AppendOnlyTransactionRequestV1,
    AuthenticatedRuntimeContextV1Alpha1,
    GovernedStateHeadPreconditionV1Alpha1,
    ImmutableRecordV1,
    canonical_hash,
)
from ace.core.runtime_use import AuthorityUseReceiptV1Alpha1
from ace.intelligence import (
    CaseV1Alpha1,
    EntitySnapshotV1Alpha1,
    IntelligenceRecordKind,
    IntelligenceResourceKind,
    IntelligenceResourceMode,
    IntelligenceResourceQueryV1Alpha1,
    LineageReferenceV1Alpha1,
    LineageRelation,
    LineageResourceKind,
    ObservationV1Alpha1,
    ShiftV1Alpha1,
    SignalV1Alpha1,
)

from scripts.p2c3_measured_feedback import _authorize_append, run_measured_feedback

READ_GRANT = "authority_grant:world-intelligence-os-read"
READ_KINDS = (
    IntelligenceResourceKind.CONNECTION,
    IntelligenceResourceKind.SOURCE,
    IntelligenceResourceKind.ENTITY,
    IntelligenceResourceKind.OBSERVATION,
    IntelligenceResourceKind.SIGNAL,
    IntelligenceResourceKind.SHIFT,
    IntelligenceResourceKind.CASE,
    IntelligenceResourceKind.BRIEF,
    IntelligenceResourceKind.DECISION,
    IntelligenceResourceKind.ACTION,
    IntelligenceResourceKind.OUTCOME,
    IntelligenceResourceKind.FEEDBACK,
    IntelligenceResourceKind.EVIDENCE_LINEAGE,
)
REQUIRED_LOOP_KINDS = {
    IntelligenceResourceKind.OBSERVATION,
    IntelligenceResourceKind.SIGNAL,
    IntelligenceResourceKind.SHIFT,
    IntelligenceResourceKind.CASE,
    IntelligenceResourceKind.BRIEF,
    IntelligenceResourceKind.DECISION,
    IntelligenceResourceKind.ACTION,
    IntelligenceResourceKind.OUTCOME,
    IntelligenceResourceKind.FEEDBACK,
}
EXPECTED_DEGRADED_REASONS = ("degraded_reason:unsupported-decision-subject",)


class ExactReadAuthority:
    """Fixture authority that preserves the public observe-read receipt contract."""

    async def resolve_authority_use(self, **request) -> AuthorityUseReceiptV1Alpha1:
        if (
            request["operation"] != "query_intelligence_resources"
            or request["authority"] != "observe_read"
            or request["grant_ref"] != READ_GRANT
        ):
            raise ValueError("World resource query crossed the exact read boundary")
        context = request["context"]
        return AuthorityUseReceiptV1Alpha1(
            product_id=context.product_id,
            actor_ref=context.actor_ref,
            authenticated_context=context,
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=READ_GRANT,
            grant_hash="8" * 64,
            evaluated_at=request["evaluated_at"],
            expires_at=context.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1(
                state_kind="authority_grant",
                product_id=context.product_id,
                state_id=READ_GRANT,
                sequence=1,
                revision_id="authority_revision:world-intelligence-os-read",
                commit_receipt_id="authority_receipt:world-intelligence-os-read",
            ),
        )


def _reader(store):
    return CompositeIntelligenceResourceProjectionReader(
        ActionResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentMemoryResourceProjectionReader(store=store, degrade_unsupported=False),
        AgentResourceProjectionReader(store=store, degrade_unsupported=False),
        IntelligenceLedgerResourceProjectionReader(store=store, degrade_unsupported=False),
        MonitoringResourceProjectionReader(store=store, degrade_unsupported=False),
        DecisionOutcomeFeedbackResourceProjectionReader(store=store, degrade_unsupported=False),
        LiveSourceResourceProjectionReader(store=store, degrade_unsupported=False),
    )


def _resource_identity(item) -> tuple[str, str, int, str]:
    reference = item.reference
    return (
        reference.resource_kind.value,
        reference.resource_id,
        reference.revision,
        reference.resource_digest,
    )


def _availability(value) -> datetime:
    if isinstance(value, ObservationV1Alpha1):
        return value.ingested_at
    if isinstance(value, EntitySnapshotV1Alpha1):
        return value.projected_at
    if isinstance(value, (ShiftV1Alpha1, SignalV1Alpha1)):
        return value.detected_at
    raise TypeError("World 0.8 Case received an unsupported member")


def _lineage(record: ImmutableRecordV1, value, *, relation: LineageRelation) -> LineageReferenceV1Alpha1:
    return LineageReferenceV1Alpha1(
        resource_kind=LineageResourceKind(record.record_kind),
        relation=relation,
        resource_id=str(value.resource_id),
        resource_digest=str(value.resource_digest),
        resource_as_of=value.as_of,
        resource_available_at=record.available_at,
    )


async def _assemble_public_case(state: dict[str, Any]) -> CaseV1Alpha1:
    """Assemble one real LIVE Case over the exact monitored development closure."""

    environment = state["environment"]
    supported = {
        IntelligenceRecordKind.OBSERVATION.value: ObservationV1Alpha1,
        IntelligenceRecordKind.SHIFT.value: ShiftV1Alpha1,
        IntelligenceRecordKind.SIGNAL.value: SignalV1Alpha1,
    }
    members = []
    for record in environment.store.records.values():
        model = supported.get(record.record_kind)
        if record.record_space == IntelligenceResourceMode.LIVE.value and model is not None:
            members.append((record, model.model_validate(record.payload)))
    signals = [(record, value) for record, value in members if isinstance(value, SignalV1Alpha1)]
    shifts = [(record, value) for record, value in members if isinstance(value, ShiftV1Alpha1)]
    observations = [(record, value) for record, value in members if isinstance(value, ObservationV1Alpha1)]
    if len(signals) != 1 or len(shifts) != 1 or len(observations) != 2:
        raise AssertionError("World 0.8 Case requires the exact one-Shift, one-Signal, two-Observation closure")
    signal_record, signal = signals[0]
    shift_record, shift = shifts[0]
    requested_at = state["clock"]()
    closure_digest = "sha256:" + canonical_hash(
        sorted(record.material_hash for record, _ in (*observations, (shift_record, shift), (signal_record, signal)))
    )
    authorization = await _authorize_append(
        state,
        context=environment.context,
        authorization_key="case:world-intelligence-os:fcc-publication-change",
        subject_ref="case_closure:fcc-publication-change:2026-08-07",
        subject_digest=closure_digest,
        requested_at=requested_at,
    )
    case = CaseV1Alpha1(
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        activation_revision=signal.activation_revision,
        as_of=max(value.as_of for _, value in members),
        lineage=(
            _lineage(shift_record, shift, relation=LineageRelation.DERIVED_FROM),
            _lineage(signal_record, signal, relation=LineageRelation.DERIVED_FROM),
            *(_lineage(record, value, relation=LineageRelation.SUPPORTS) for record, value in observations),
        ),
        case_type_ref="case_type:official_publication_change",
        title="FCC public-record publication change",
        purpose="Orient the exact monitored change and official observations before executive review.",
        subject_refs=signal.subject_refs,
        assembled_at=authorization.authorized_at,
    )
    record = ImmutableRecordV1(
        product_id=case.product_id,
        record_space=case.mode.value,
        record_kind=IntelligenceRecordKind.CASE.value,
        record_key=str(case.resource_id),
        payload_contract=case.contract,
        payload=case.model_dump(mode="python"),
        as_of=case.as_of,
        available_at=case.assembled_at,
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=case.product_id,
        record_space=case.mode.value,
        transaction_key=f"world-intelligence-os-case:{case.resource_id}",
        records=(record,),
        submitted_at=case.assembled_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError("World 0.8 Case append returned divergent receipt material")
    return case


async def run_acceptance(
    workspace_root: Path,
    *,
    core_candidate_commit: str = "working-tree",
) -> dict[str, Any]:
    state: dict[str, Any] = {}
    journey = await run_measured_feedback(workspace_root, state_sink=state)
    environment = state["environment"]
    store = environment.store
    assembled_case = await _assemble_public_case(state)
    evaluated_at = datetime.now(UTC)
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=environment.fixture["product_id"],
        actor_ref="principal:world-intelligence-os-reviewer",
        authentication_receipt_ref="task_authentication_receipt:world-intelligence-os-reviewer",
        authentication_receipt_digest="sha256:" + "7" * 64,
        authenticated_at=evaluated_at - timedelta(seconds=1),
        expires_at=evaluated_at + timedelta(hours=1),
    )
    records = tuple(store.records.values())
    request = IntelligenceResourceQueryV1Alpha1(
        authenticated_context=context,
        product_id=context.product_id,
        authority_grant_ref=READ_GRANT,
        resource_kinds=READ_KINDS,
        subject_refs=(),
        as_of=max(record.as_of for record in records),
        available_at=max(record.available_at for record in records),
        page_size=200,
    )
    authority = ExactReadAuthority()
    first = await IntelligenceResourcePlaneService(
        reader=_reader(store),
        authority=authority,
    ).query(request, evaluated_at=evaluated_at)
    reopened = await IntelligenceResourcePlaneService(
        reader=_reader(store),
        authority=authority,
    ).query(request, evaluated_at=evaluated_at + timedelta(seconds=1))

    first_identities = tuple(_resource_identity(item) for item in first.items)
    reopened_identities = tuple(_resource_identity(item) for item in reopened.items)
    if first.next_cursor is not None or reopened.next_cursor is not None:
        raise AssertionError("World 0.8 proof exceeded its bounded single-page acceptance")
    if first.query_id != reopened.query_id or first_identities != reopened_identities:
        raise AssertionError("World resource plane did not reopen exact projected identities")

    kinds = {item.reference.resource_kind for item in first.items}
    missing = sorted(kind.value for kind in REQUIRED_LOOP_KINDS - kinds)
    if missing:
        present = sorted(kind.value for kind in kinds)
        raise AssertionError(
            f"World 0.8 evidence-to-outcome loop is missing {missing}; "
            f"present={present}; degraded={first.degraded_reason_refs}"
        )
    if any(item.reference.product_id != context.product_id for item in first.items):
        raise AssertionError("World resource page crossed product scope")
    if first.degraded_reason_refs != EXPECTED_DEGRADED_REASONS:
        raise AssertionError(
            f"World resource page changed its explicit evaluation-control limitation: {first.degraded_reason_refs}"
        )

    counts = {
        kind.value: sum(1 for item in first.items if item.reference.resource_kind is kind)
        for kind in sorted(kinds, key=lambda value: value.value)
    }
    return {
        "contract": "ace.world-intelligence.intelligence-os-acceptance/v1alpha1",
        "core_candidate_commit": core_candidate_commit,
        "domain": "world_intelligence",
        "product_id": context.product_id,
        "journey_contract": journey["contract"],
        "query": {
            "query_id": first.query_id,
            "page_state": first.state.value,
            "resource_count": len(first.items),
            "resource_counts": counts,
            "exact_restart_reopen": True,
            "single_page": True,
            "authority": first.authority_use.authority,
        },
        "loop": {
            "required_kinds": sorted(kind.value for kind in REQUIRED_LOOP_KINDS),
            "all_present": True,
            "proposal_applied": journey["scope"]["proposal_applied"],
            "autonomous_publication": journey["scope"]["autonomous_publication"],
            "case_id": str(assembled_case.resource_id),
        },
        "limitations": {
            "recorded_transport": True,
            "network_freshness_claimed": False,
            "human_benefit_claimed": False,
            "causality_claimed": False,
            "evaluation_control_subject_is_public_resource": False,
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ace-world-v08-") as directory:
        result = asyncio.run(run_acceptance(Path(directory)))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
