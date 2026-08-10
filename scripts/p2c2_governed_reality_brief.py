"""Complete official-source Reality Brief -> reviewed action acceptance."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ace.application import (
    LiveBriefSynthesisService,
    LiveIntelligenceBridgeService,
    bind_committed_activation,
)
from ace.core import (
    ActionIntentV1Alpha1,
    ActionPromotionDisposition,
    ActionReviewDisposition,
    ActionVerificationDisposition,
    AppendOnlyTransactionRequestV1,
    AuthenticatedRuntimeContextV1Alpha1,
    AuthorityUseReceiptV1Alpha1,
    CapabilityArtifactIdentityV1Alpha1,
    CapabilityUseReceiptV1Alpha1,
    DecisionActionDisposition,
    DecisionDisposition,
    DecisionIntentV1Alpha1,
    DecisionV1Alpha1,
    GovernedActionAuthorizationRequestV1Alpha1,
    GovernedActionExecutionService,
    GovernedActionReviewService,
    GovernedOperationBindingV1Alpha1,
    GovernedReasoningService,
    GovernedStateHeadPreconditionV1Alpha1,
    GovernedStateHeadV1,
    ImmutableRecordV1,
    ProviderRouteV1Alpha1,
    ProviderStructuredOutputV1Alpha1,
    ProviderUsageV1Alpha1,
    ReasoningExecutionBindingV1Alpha1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    BriefSynthesisDraftV1Alpha1,
    BriefSynthesisRequestV1Alpha1,
    ClaimGroundingKind,
    IntelligenceResourceMode,
    LiveDerivationRequestV1Alpha1,
    resource_reference,
)
from ace_reference_workspace_action import (
    ACTION_TYPE,
    ADAPTER_ARTIFACT,
    ReferenceWorkspaceActionAdapter,
)

from scripts.p2c2_federal_register_monitor import (
    _time,
    admit_snapshots,
    build_environment,
    source_projection,
)

REASONING_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="structured_reasoning",
    contract="ace.core.reasoning-provider/v1alpha1",
    implementation_id="world_official_record_brief_fixture",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "7" * 64,
)
APPEND_ARTIFACT = CapabilityArtifactIdentityV1Alpha1(
    capability="append_immutable_records",
    contract="ace.core.immutable-record-appender/v1alpha1",
    implementation_id="world_official_record_append_fixture",
    implementation_version="0.1.0",
    artifact_digest="sha256:" + "8" * 64,
)


class MutableClock:
    def __init__(self, current: datetime, *, step: timedelta = timedelta(seconds=1)) -> None:
        self.current = current
        self.step = step
        self.realtime = False

    def set(self, current: datetime) -> None:
        self.current = current
        self.realtime = False

    def use_realtime(self) -> None:
        self.realtime = True

    def __call__(self) -> datetime:
        if self.realtime:
            return datetime.now(UTC)
        value = self.current
        self.current = value + self.step
        return value


def _head(product_id: str, kind: str, state_id: str, sequence: int) -> GovernedStateHeadV1:
    return GovernedStateHeadV1(
        state_kind=kind,
        product_id=product_id,
        state_id=state_id,
        sequence=sequence,
        revision_id=f"revision:{kind}:{sequence}",
        commit_receipt_id=f"governed_state_commit:{kind}:{sequence}",
        updated_at=datetime(2026, 8, 6, 17, 52, tzinfo=UTC),
    )


class ExactRuntimeUse:
    """Exact Core runtime-use resolver for the consumer acceptance host."""

    def __init__(self, *, product_id, bindings, heads, expires_at) -> None:
        self.product_id = product_id
        self.bindings = tuple(bindings)
        self.heads = heads
        self.expires_at = expires_at

    def _binding(self, *, artifact=None, grant_ref=None):
        for binding in self.bindings:
            if artifact is not None and binding.artifact == artifact:
                return binding
            if grant_ref is not None and binding.grant_ref == grant_ref:
                return binding
        raise RuntimeError("no exact governed binding for the requested use")

    async def resolve_capability_use(self, **request):
        binding = self._binding(artifact=request["artifact"])
        if request["configuration_ref"] != binding.configuration_ref:
            raise RuntimeError("capability configuration crossed the exact binding")
        return CapabilityUseReceiptV1Alpha1(
            product_id=self.product_id,
            actor_ref=request["context"].actor_ref,
            authenticated_context=request["context"],
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            artifact=request["artifact"],
            capability_state_ref=request["capability_state_ref"],
            configuration_ref=request["configuration_ref"],
            evaluated_at=request["evaluated_at"],
            resolved_at=request["evaluated_at"],
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.heads[
                    "capability_state",
                    capability_state_ref_for_artifact(request["artifact"]),
                ]
            ),
        )

    async def resolve_authority_use(self, **request):
        binding = self._binding(grant_ref=request["grant_ref"])
        if request["authority"] != binding.authority:
            raise RuntimeError("authority crossed the exact binding")
        return AuthorityUseReceiptV1Alpha1(
            product_id=self.product_id,
            actor_ref=request["context"].actor_ref,
            authenticated_context=request["context"],
            use_subject_ref=request["use_subject_ref"],
            use_subject_digest=request["use_subject_digest"],
            operation=request["operation"],
            authority=request["authority"],
            grant_ref=request["grant_ref"],
            grant_hash="9" * 64,
            evaluated_at=request["evaluated_at"],
            expires_at=self.expires_at,
            state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
                self.heads["authority_grant", request["grant_ref"]]
            ),
        )


class OfficialRecordBriefProvider:
    """Deterministic structured provider grounded only in selected LIVE context."""

    artifact_identity = REASONING_ARTIFACT

    def __init__(self, *, baseline: dict[str, Any], current: dict[str, Any]) -> None:
        self.baseline = baseline
        self.current = current
        self.calls = 0

    async def execute(self, request):
        self.calls += 1
        instruction = json.loads(request.instruction_json)
        observations = tuple(
            sorted(
                item.record_key
                for item in request.context_items
                if item.record_kind == "observation"
            )
        )
        inferred = tuple(
            sorted(
                item.record_key
                for item in request.context_items
                if item.record_kind != "observation"
            )
        )
        statements = {
            "what_changed": (
                f"The monitored FCC publication changed from Federal Register document "
                f"{self.baseline['document_number']} ({self.baseline['document_type']}) to "
                f"{self.current['document_number']} ({self.current['document_type']})."
            ),
            "why_it_matters": (
                "The newer record is a proposed rule concerning communications-supply-chain "
                "security, so it may warrant direct review by people tracking that topic."
            ),
            "unknowns": (
                "These records alone do not establish the proposal's eventual disposition, "
                "implementation, or practical impact."
            ),
            "watchpoints": (
                "Watch for later official notices, rules, corrections, or linked docket material."
            ),
            "limitations": (
                "This proof uses two exact recorded Federal Register API responses and does not "
                "claim live network freshness beyond their stated publication dates."
            ),
        }
        sections = []
        for section_id in instruction["required_sections"]:
            if section_id == "established_records":
                claim = BriefDraftClaimV1Alpha1(
                    statement=(
                        f"The admitted official records are {self.baseline['document_number']} "
                        f"published {self.baseline['publication_date']} and "
                        f"{self.current['document_number']} published "
                        f"{self.current['publication_date']}."
                    ),
                    grounding_kind=ClaimGroundingKind.CITED,
                    support_refs=observations,
                    confidence=1.0,
                )
            else:
                claim = BriefDraftClaimV1Alpha1(
                    statement=statements[section_id],
                    grounding_kind=ClaimGroundingKind.INFERENCE,
                    support_refs=inferred,
                    confidence=0.8,
                    uncertainty=(
                        "Interpretation is bounded to the exact admitted records and may change "
                        "when additional official evidence is admitted."
                    ),
                )
            sections.append(
                BriefDraftSectionV1Alpha1(section_id=section_id, claims=(claim,))
            )
        draft = BriefSynthesisDraftV1Alpha1(
            brief_type=instruction["brief_type"],
            persona_ids=tuple(item["persona_id"] for item in instruction["personas"]),
            sections=tuple(sections),
            recommendation_claim_id=None,
        )
        return ProviderStructuredOutputV1Alpha1(
            route=ProviderRouteV1Alpha1(
                provider_id="world_official_record_fixture",
                model_id="deterministic",
                model_version="1",
                configuration_digest="sha256:" + "a" * 64,
            ),
            usage=ProviderUsageV1Alpha1(
                input_units=120,
                output_units=80,
                total_units=200,
                duration_ms=2,
            ),
            structured_json=canonical_json(draft.model_dump(mode="json")),
            referenced_context_ids=tuple(
                str(item.context_id) for item in request.context_items
            ),
        )


def _context(base: AuthenticatedRuntimeContextV1Alpha1, actor_ref: str):
    return AuthenticatedRuntimeContextV1Alpha1(
        product_id=base.product_id,
        actor_ref=actor_ref,
        authentication_receipt_ref=f"authentication_receipt:{actor_ref.split(':')[-1]}",
        authentication_receipt_digest="sha256:"
        + hashlib.sha256(actor_ref.encode()).hexdigest(),
        authenticated_at=base.authenticated_at,
        expires_at=base.expires_at,
    )


def _bindings(environment, clock):
    product_id = environment.fixture["product_id"]
    execution_head = _head(
        product_id,
        "reasoning_configuration",
        "reasoning_configuration:world-official-record-brief",
        10,
    )
    append_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-live-append",
        11,
    )
    action_head = _head(
        product_id,
        "governed_operation_configuration",
        "governed_operation_configuration:world-reviewed-export",
        12,
    )
    execution = ReasoningExecutionBindingV1Alpha1(
        product_id=product_id,
        artifact=REASONING_ARTIFACT,
        configuration_ref=execution_head.state_id,
        authority="reason",
        grant_ref="authority_grant:world-official-record-reason",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
            execution_head
        ),
    )
    append = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=APPEND_ARTIFACT,
        configuration_ref=append_head.state_id,
        authority="append_immutable_records",
        grant_ref="authority_grant:world-live-append",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
            append_head
        ),
    )
    action = GovernedOperationBindingV1Alpha1(
        product_id=product_id,
        artifact=ADAPTER_ARTIFACT,
        configuration_ref=action_head.state_id,
        authority="execute_action",
        grant_ref="authority_grant:world-reviewed-export",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(
            action_head
        ),
    )
    heads = {
        (item.state_kind, item.state_id): item
        for item in (execution_head, append_head, action_head)
    }
    for index, artifact in enumerate(
        (REASONING_ARTIFACT, APPEND_ARTIFACT, ADAPTER_ARTIFACT), start=20
    ):
        state_id = capability_state_ref_for_artifact(artifact)
        item = _head(product_id, "capability_state", state_id, index)
        heads[item.state_kind, item.state_id] = item
    for index, binding in enumerate((execution, append, action), start=30):
        item = _head(product_id, "authority_grant", binding.grant_ref, index)
        heads[item.state_kind, item.state_id] = item
    for item in heads.values():
        environment.store.set_governed_state_head(item)
    runtime = ExactRuntimeUse(
        product_id=product_id,
        bindings=(execution, append, action),
        heads=heads,
        expires_at=environment.context.expires_at,
    )
    return execution, append, action, runtime


def _activation_precondition(environment):
    receipt = environment.committed_activation.commit_receipt
    return GovernedStateHeadPreconditionV1Alpha1(
        state_kind=receipt.state_kind,
        product_id=receipt.product_id,
        state_id=receipt.state_id,
        sequence=receipt.sequence,
        revision_id=receipt.revision_id,
        commit_receipt_id=str(receipt.receipt_id),
    )


async def _record_decision(
    *, environment, reasoning, append_binding, brief_admission, decided_at
):
    brief_record = brief_admission.transaction_receipt.records[0]
    intent = DecisionIntentV1Alpha1(
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        subject=brief_record,
        actor_role_ref="persona:public-researcher",
        decision_type="direction",
        disposition=DecisionDisposition.ACCEPT,
        action_disposition=DecisionActionDisposition.AUTHORIZE_ACTION,
        action_type=ACTION_TYPE,
        rationale=(
            "Approve export of the exact cited Reality Brief to the bounded review workspace."
        ),
        decided_at=decided_at,
    )
    authorization = await reasoning.authorize_action(
        GovernedActionAuthorizationRequestV1Alpha1(
            authorization_key=f"decision:{intent.intent_id}",
            product_id=intent.product_id,
            authenticated_context=intent.authenticated_context,
            execution_binding=append_binding,
            operation="append_immutable_records",
            subject_ref=str(intent.intent_id),
            subject_digest=str(intent.intent_digest),
            requested_at=decided_at,
            required_state_preconditions=(
                _activation_precondition(environment),
                append_binding.state_head_precondition,
            ),
        )
    )
    decision = DecisionV1Alpha1(intent=intent, authorization=authorization)
    record = ImmutableRecordV1(
        product_id=intent.product_id,
        record_space="world_intelligence",
        record_kind="decision",
        record_key=str(decision.decision_id),
        payload_contract=decision.contract,
        payload=decision.model_dump(mode="python"),
        as_of=decided_at,
        available_at=authorization.authorized_at,
        processing_order=0,
    )
    append = AppendOnlyTransactionRequestV1(
        product_id=intent.product_id,
        record_space=record.record_space,
        transaction_key=f"decision:{decision.decision_id}",
        records=(record,),
        submitted_at=authorization.authorized_at,
        governed_state_preconditions=authorization.state_preconditions,
    )
    receipt = await environment.store.append(append)
    if receipt != append.receipt():
        raise AssertionError("Decision append returned divergent receipt material")
    return decision, record.reference(), receipt


async def run_acceptance(workspace_root: Path) -> dict[str, Any]:
    environment = await build_environment()
    admissions = await admit_snapshots(environment)
    baseline, current = admissions
    binding = environment.committed_activation
    prepared_binding = environment.pack
    clock = MutableClock(_time("2026-08-07T18:01:03Z"))
    execution_binding, append_binding, action_binding, runtime = _bindings(
        environment, clock
    )
    baseline_data = baseline.entity_snapshot.attributes.parsed_value()
    current_data = current.entity_snapshot.attributes.parsed_value()
    provider = OfficialRecordBriefProvider(
        baseline=baseline_data,
        current=current_data,
    )
    reasoning = GovernedReasoningService(
        store=environment.store,
        runtime_use=runtime,
        provider=provider,
        clock=clock,
    )
    activation_binding = bind_committed_activation(
        pack=prepared_binding, committed=binding
    )
    derivation_fixture = environment.fixture["derivation"]
    baseline_ref = resource_reference(baseline.entity_snapshot).model_copy(
        update={
            "available_at": next(
                item.available_at
                for item in baseline.transaction_receipt.records
                if item.record_kind == "entity_snapshot"
            )
        }
    )
    current_ref = resource_reference(current.entity_snapshot).model_copy(
        update={
            "available_at": next(
                item.available_at
                for item in current.transaction_receipt.records
                if item.record_kind == "entity_snapshot"
            )
        }
    )
    derivation_request = LiveDerivationRequestV1Alpha1(
        derivation_key=derivation_fixture["derivation_key"],
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        activation_revision=activation_binding.prepared_binding.reference,
        pack=activation_binding.prepared_binding.revision.spec.pack,
        detector_id=derivation_fixture["detector_id"],
        baseline=baseline_ref,
        current=current_ref,
        detected_at=_time(derivation_fixture["detected_at"]),
        attention_evaluated_at=_time(
            derivation_fixture["attention_evaluated_at"]
        ),
        requested_at=_time(derivation_fixture["requested_at"]),
    )
    bridge = LiveIntelligenceBridgeService(
        activation_service=environment.activation_service,
        pack=environment.pack,
        store=environment.store,
        authorizer=reasoning,
        operation_binding=append_binding,
    )
    derivation = await bridge.derive(derivation_request)
    derivation_replay = await bridge.derive(derivation_request)
    if derivation.replayed or not derivation_replay.replayed:
        raise AssertionError("LIVE derivation replay was not explicit")

    brief_request = BriefSynthesisRequestV1Alpha1(
        synthesis_key="live-brief:fcc-publication-change:2026-08-07",
        reasoning_attempt_key="reasoning:fcc-publication-change:2026-08-07",
        derivation_key=derivation_fixture["derivation_key"],
        product_id=environment.fixture["product_id"],
        mode=IntelligenceResourceMode.LIVE,
        authenticated_context=environment.context,
        activation_revision=activation_binding.prepared_binding.reference,
        pack=activation_binding.prepared_binding.revision.spec.pack,
        attention_receipt_id=str(derivation.attention_receipt.receipt_id),
        attention_receipt_digest=str(derivation.attention_receipt.receipt_digest),
        brief_as_of=derivation.signal.as_of,
        context_cutoff_at=_time("2026-08-07T18:01:05Z"),
        requested_at=_time("2026-08-07T18:01:06Z"),
    )
    briefs = LiveBriefSynthesisService(
        activation_service=environment.activation_service,
        pack=environment.pack,
        store=environment.store,
        reasoning=reasoning,
        execution_binding=execution_binding,
        append_binding=append_binding,
    )
    clock.set(_time("2026-08-07T18:01:07Z"))
    brief = await briefs.synthesize(brief_request)
    brief_replay = await briefs.synthesize(brief_request)
    if brief.replayed or not brief_replay.replayed or provider.calls != 1:
        raise AssertionError("LIVE Brief did not replay without re-reasoning")

    now = datetime.now(UTC)
    clock.use_realtime()
    decision, decision_ref, decision_receipt = await _record_decision(
        environment=environment,
        reasoning=reasoning,
        append_binding=append_binding,
        brief_admission=brief,
        decided_at=now - timedelta(seconds=2),
    )
    intent = ActionIntentV1Alpha1(
        action_key="action:world-reality-brief-export:2026-16197",
        product_id=environment.fixture["product_id"],
        authenticated_context=environment.context,
        decision=decision_ref,
        action_type=ACTION_TYPE,
        parameters_json=canonical_json(
            {
                "relative_path": "world-reality-brief-2026-16197.md",
                "content": brief.brief.body_markdown,
            }
        ),
        requested_at=decision_ref.available_at,
    )
    adapter = ReferenceWorkspaceActionAdapter(workspace_root=workspace_root)
    executor = GovernedActionExecutionService(
        store=environment.store,
        authorizer=reasoning,
        operation_binding=action_binding,
        adapter=adapter,
        clock=clock,
    )
    review_service = GovernedActionReviewService(
        store=environment.store,
        executor=executor,
        clock=clock,
    )
    prepared = await review_service.prepare_for_review(intent)
    review = await review_service.review(
        prepared,
        review_key="review:world-reality-brief-export:2026-16197",
        reviewer_context=_context(environment.context, "principal:world-reviewer"),
        disposition=ActionReviewDisposition.APPROVE,
        rationale="The exact file target, content digest, permission, and create-only effect are approved.",
    )
    outcome = await review_service.execute_reviewed(review)
    target = workspace_root / "world-reality-brief-2026-16197.md"
    written = target.read_text(encoding="utf-8")
    if written != brief.brief.body_markdown:
        raise AssertionError("exported Reality Brief differs from the exact reviewed content")
    verification = await review_service.verify(
        review,
        outcome,
        verification_key="verification:world-reality-brief-export:2026-16197",
        verifier_context=_context(environment.context, "principal:world-verifier"),
        disposition=ActionVerificationDisposition.VERIFIED,
        rationale="The created file exists and exactly matches the governed LIVE Brief.",
    )
    promotion = await review_service.promote(
        verification,
        promotion_key="promotion:world-reality-brief-export:2026-16197",
        promoter_context=_context(environment.context, "principal:world-promoter"),
        disposition=ActionPromotionDisposition.PROMOTED,
        target_ref="workspace:approved-world-intelligence-demo",
        rationale="Adopt the verified export as the approved World Intelligence demo artifact.",
    )
    action_replay = await review_service.execute_reviewed(review)
    if not action_replay.replayed:
        raise AssertionError("reviewed action did not reopen without a second effect")

    return {
        "contract": "ace.world-intelligence.governed-reality-brief-action/v1alpha1",
        "source": source_projection(admissions),
        "intelligence": {
            "shift_id": str(derivation.shift.resource_id),
            "shift_type": derivation.shift.shift_type_ref,
            "signal_id": str(derivation.signal.resource_id),
            "signal_type": derivation.signal.signal_type_ref,
            "attention": derivation.attention_receipt.disposition.value,
            "brief_id": str(brief.brief.resource_id),
            "brief_digest": str(brief.brief.resource_digest),
            "citation_count": len(brief.brief.citations),
            "claim_count": len(brief.brief.claims),
            "deterministic_replay": brief_replay.replayed,
            "provider_invocations": provider.calls,
        },
        "decision": {
            "decision_id": str(decision.decision_id),
            "decision_digest": str(decision.decision_digest),
            "transaction_receipt_id": str(decision_receipt.receipt_id),
            "action_type": decision.intent.action_type,
        },
        "action": {
            "intent_id": str(intent.intent_id),
            "review_receipt_id": str(review.receipt_id),
            "terminal_receipt_id": str(outcome.terminal.receipt_id),
            "verification_receipt_id": str(verification.receipt_id),
            "promotion_receipt_id": str(promotion.receipt_id),
            "effect_state": outcome.result.effect_state.value,
            "disposition": outcome.result.disposition.value,
            "replayed_without_second_effect": action_replay.replayed,
            "export_path": str(target),
            "export_digest": "sha256:"
            + hashlib.sha256(written.encode("utf-8")).hexdigest(),
        },
        "scope": {
            "official_public_records": True,
            "recorded_transport": True,
            "network_access": False,
            "human_review_required": True,
            "autonomous_publication": False,
            "political_persuasion": False,
        },
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run_acceptance(args.workspace_root)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
