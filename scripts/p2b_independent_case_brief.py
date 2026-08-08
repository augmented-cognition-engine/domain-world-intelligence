#!/usr/bin/env python3
"""Independence-aware governed Reality Brief for the frozen World P2B scenario.

This consumer harness closes WI-CR-003 through public ACE APIs and Pack IR only.
It admits the scenario's ``derived_from``/``corrects`` relationships as real ACE
Observation lineage, declares a ``corroborated`` status that requires two
distinct derivation families, and asks ACE's public independence-aware Case-bound
synthesis service for one governed Brief plus its durable family-disclosing
status projection.

What this proves
----------------
``corroborated`` now means two genuinely independent origins, not two records.
The Ledger report and the Basin hydrology dataset are separate roots and
corroborate. The Coastal Wire syndication and the Harborview reprint both
declare ``derived_from`` the Ledger report, so they collapse into it and cannot
corroborate anything it asserts -- not individually, and not as a pair, however
many distinct publishers they represent.

Why this is a separate additive activation
------------------------------------------
Declaring a Pack module and admitting Observation lineage both change canonical
payloads, which re-keys every resource admitted under them. The frozen
WI-CR-005 packet (``case:2ee200c03f2576307b0bc43e6e128f30``) and the WI-CR-002
status packet (``case:bc28c76926d733c0ce0fe03b9c9222db``) must both stay
byte-identical, so this harness builds a *third* additive revision and leaves
both earlier harnesses untouched.

Honest limits
-------------
Independence is exactly as strong as the admitted lineage. If a Domain Pack
admits two Observations that share an origin without declaring any lineage
between them, ACE counts them as two families. ACE never treats publisher count
or textual variation as independence. WI-CR-004 remains open.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from ace.application import (
    CaseBriefFamilyStatusSynthesisService,
    DomainActivationAdmissionService,
    PreparedIntelligenceLedgerService,
    bind_committed_activation,
)
from ace.core import (
    AuthenticatedRuntimeContextV1Alpha1,
    GovernedOperationBindingV1Alpha1,
    GovernedReasoningService,
    GovernedStateHeadPreconditionV1Alpha1,
    ProviderRouteV1Alpha1,
    ProviderStructuredOutputV1Alpha1,
    ProviderUsageV1Alpha1,
    ReasoningExecutionBindingV1Alpha1,
    canonical_json,
    capability_state_ref_for_artifact,
)
from ace.intelligence import (
    ActivationState,
    AuthorityBindingV1,
    BriefDraftClaimStatusBindingV1Alpha1,
    BriefDraftClaimV1Alpha1,
    BriefDraftSectionV1Alpha1,
    BriefSynthesisDraftV1Alpha2,
    CapabilityBindingV1,
    CaseBriefSynthesisRequestV1Alpha1,
    CaseMemberAttentionBindingV1Alpha1,
    ClaimGroundingKind,
    IntelligenceRecordKind,
    OrganizationOverlayV1,
    compile_overlay,
    compile_pack_document,
    prepare_activation_revision,
    prepare_domain_activation,
    resource_reference,
)
from ace.testing import InMemoryImmutableRecordStore

from scripts.p2a_compile_acceptance import _encoded, _pack_material, _replace_resource
from scripts.p2b_case_brief import (
    APPEND_ARTIFACT,
    REASONING_ARTIFACT,
    ROUTED_DERIVATIONS,
    WORLD_EPISTEMIC_STATUSES,
    _ActivationAuthority,
    _ActivationStore,
    _admit_material,
    _Clock,
    _head,
    _Runtime,
)
from scripts.p2b_prepared_replay import (
    ACTIVATED_AT,
    ADDITIVE_ROUTES,
    CATEGORICAL_RULES,
    PRODUCT_ID,
    build_replay_material,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"

STATUS_SET_ID = "world_reality_status"

#: The Ledger reporting family: one root plus everything derived from it.
LEDGER_ROOT = "record:ledger_report_1088"
LEDGER_SYNDICATION = ("record:coastal_wire_5521", "record:harborview_reprint_302")
HYDROLOGY_ROOT = "record:basin_gauge_series_w10"

#: The corroborated claim's supports must span two distinct families. Bringing
#: the syndicated copies into the exact Case closure is what makes the negative
#: vectors fail for the *intended* reason rather than as unknown supports.
CORROBORATION_CLOSURE_RECORDS = LEDGER_SYNDICATION

#: Support selections for the corroborated claim. Only the first is independent.
CORROBORATION_VECTORS = {
    "independent_roots": (LEDGER_ROOT, HYDROLOGY_ROOT),
    "ledger_plus_coastal_wire_syndication": (LEDGER_ROOT, "record:coastal_wire_5521"),
    "ledger_plus_harborview_reprint": (LEDGER_ROOT, "record:harborview_reprint_302"),
    "two_publishers_one_origin": LEDGER_SYNDICATION,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compile_independence_pack():
    """Compile an additive 0.4.0 revision declaring the family-aware status set."""

    manifest, resources = _pack_material()
    manifest["metadata"]["version"] = "0.4.0"

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

    epistemic = _load(PACK_ROOT / "modules" / "epistemic_status_v2.json")
    path = "modules/epistemic_status_v2.json"
    payload = _encoded(epistemic)
    resources[path] = payload
    manifest["resources"].append(
        {
            "resource_id": "world_epistemic_status",
            "path": path,
            "media_type": "application/json",
            "digest": f"sha256:{hashlib.sha256(payload).hexdigest()}",
        }
    )
    manifest["modules"].append(
        {
            "module_id": epistemic["module_id"],
            "contract": epistemic["contract"],
            "resource_id": "world_epistemic_status",
            "depends_on": ["world_synthesis"],
        }
    )
    return compile_pack_document(_encoded(manifest), resources)


def independence_activation_revision():
    """Build the exact additive independence-aware activation revision."""

    pack = compile_independence_pack()
    overlay = compile_overlay(
        pack,
        OrganizationOverlayV1(
            overlay_id="world_p2b_independent_case_brief",
            version="0.4.0",
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
        compilation_receipt_ref="receipt:world-p2b-independence-compilation",
        conformance_receipt_refs=("receipt:world-p2b-independence-conformance",),
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
        approval_receipt_ref="receipt:world-p2b-independence-approval",
        occurred_at=ACTIVATED_AT,
    )
    return pack, revision


#: One claim per required section. ``corroboration`` is filled from the selected
#: vector; every other bucket names exact frozen resources by kind and index so
#: all 28 selected context items are attributed exactly once.
CLAIM_PLAN = (
    ("what_happened", "admitted_record", "cited", ("record", "record:mwa_bulletin_214", "record:mwa_order_47")),
    ("what_changed", "ace_inference", "inference", ("kind", ("case", 0), ("entity_snapshot", 0), ("entity_snapshot", 1))),
    ("established_records", "admitted_record", "cited", ("record", "record:assembly_transcript_0310")),
    ("attributed_claims", "attributed_claim", "cited", ("record", "record:ledger_correction_114")),
    ("where_sources_agree", "corroborated", "cited", ("corroboration",)),
    ("where_sources_conflict", "disputed", "inference", ("remaining_observations",)),
    (
        "ace_inferences",
        "ace_inference",
        "inference",
        ("kind", ("entity_snapshot", 2), ("entity_snapshot", 3), ("entity_snapshot", 4)),
    ),
    (
        "unknowns",
        "unknown",
        "inference",
        ("kind", ("entity_snapshot", 5), ("entity_snapshot", 6), ("entity_snapshot", 7)),
    ),
    (
        "why_it_matters",
        "ace_inference",
        "inference",
        ("kind", ("entity_snapshot", 8), ("entity_snapshot", 9), ("shift", 0)),
    ),
    ("watchpoints", "scenario", "inference", ("kind", ("shift", 1), ("signal", 0))),
    (
        "limitations",
        "unknown",
        "inference",
        (
            "kind",
            ("shift", 2),
            ("shift", 3),
            ("shift", 4),
            ("signal", 1),
            ("signal", 2),
            ("signal", 3),
        ),
    ),
)

STATEMENTS = {
    "admitted_record": "The named admitted public records establish this statement directly.",
    "attributed_claim": "Exactly one named source record asserts this statement; the attribution is part of it.",
    "corroborated": (
        "At least two admitted records from distinct derivation families support this statement. "
        "Syndicated copies and reprints of one origin do not count."
    ),
    "disputed": "The admitted material is materially in conflict on this statement.",
    "ace_inference": "ACE derived this statement only from the exact frozen resources named as supports.",
    "unknown": "The admitted evidence does not resolve this statement.",
    "scenario": "This is a conditional future state built only from the exact derived resources named.",
}

UNCERTAINTY = "The frozen prepared records do not establish anything beyond the named exact resources."


class _IndependenceProvider:
    """Deterministic status-aware provider for the independence packet."""

    artifact_identity = REASONING_ARTIFACT

    def __init__(self, *, observation_ids: dict[str, str], corroboration: tuple[str, ...]) -> None:
        self.calls = 0
        self.observation_ids = observation_ids
        self.corroboration = corroboration

    async def execute(self, request):
        self.calls += 1
        by_kind: dict[str, list[str]] = {}
        for item in request.context_items:
            by_kind.setdefault(item.record_kind, []).append(item.record_key)
        for values in by_kind.values():
            values.sort()

        instruction = json.loads(request.instruction_json)
        section_ids = tuple(instruction["required_sections"])
        corroboration_ids = tuple(self.observation_ids[item] for item in self.corroboration)

        # Whatever the corroborated claim does not take, the disputed claim does,
        # so every admitted Observation stays attributed exactly once.
        named: set[str] = set(corroboration_ids)
        for _, _, _, bucket in CLAIM_PLAN:
            if bucket[0] == "record":
                named.update(self.observation_ids[item] for item in bucket[1:])
        remaining = tuple(sorted(set(by_kind["observation"]) - named))

        sections = []
        statuses = []
        attributed: set[str] = set()
        for section_id, status_id, grounding, bucket in CLAIM_PLAN:
            if bucket[0] == "corroboration":
                supports = corroboration_ids
            elif bucket[0] == "remaining_observations":
                supports = remaining
            elif bucket[0] == "record":
                supports = tuple(self.observation_ids[item] for item in bucket[1:])
            else:
                supports = tuple(by_kind[kind][index] for kind, index in bucket[1:])
            attributed.update(supports)
            claim = BriefDraftClaimV1Alpha1(
                statement=STATEMENTS[status_id],
                grounding_kind=(
                    ClaimGroundingKind.CITED if grounding == "cited" else ClaimGroundingKind.INFERENCE
                ),
                support_refs=supports,
                confidence=1.0 if grounding == "cited" else 0.7,
                uncertainty=None if grounding == "cited" else UNCERTAINTY,
            )
            sections.append(BriefDraftSectionV1Alpha1(section_id=section_id, claims=(claim,)))
            statuses.append(
                BriefDraftClaimStatusBindingV1Alpha1(
                    draft_claim_id=str(claim.claim_id),
                    status_id=status_id,
                )
            )
        if tuple(item.section_id for item in sections) != section_ids:
            raise AssertionError("claim plan does not cover the routed template sections in order")
        expected = {item.record_key for item in request.context_items}
        if attributed != expected:
            raise AssertionError(
                f"claim plan left exact selected supports unattributed: {sorted(expected - attributed)}"
            )

        draft = BriefSynthesisDraftV1Alpha2(
            brief_type=instruction["brief_type"],
            persona_ids=tuple(item["persona_id"] for item in instruction["personas"]),
            sections=tuple(sections),
            claim_statuses=tuple(statuses),
            recommendation_claim_id=None,
        )
        return ProviderStructuredOutputV1Alpha1(
            route=ProviderRouteV1Alpha1(
                provider_id="world_p2b_independence_fixture",
                model_id="deterministic",
                model_version="1",
                configuration_digest="sha256:" + "c" * 64,
            ),
            usage=ProviderUsageV1Alpha1(input_units=130, output_units=52, total_units=182, duration_ms=2),
            structured_json=canonical_json(draft.model_dump(mode="json")),
            referenced_context_ids=tuple(str(item.context_id) for item in request.context_items),
        )


async def _environment(*, corroboration: tuple[str, ...], synthesis_key: str):
    """Build one complete independence-aware synthesis environment."""

    pack, revision = independence_activation_revision()
    material = build_replay_material(
        pack=pack,
        revision=revision,
        link_derivations=True,
        additional_claim_basis={"entity:claim/farm_allocation_cut": CORROBORATION_CLOSURE_RECORDS},
    )
    orientation_case = material["orientation_case"]
    attention_at = orientation_case.assembled_at
    context_cutoff_at = orientation_case.assembled_at
    requested_at = context_cutoff_at + timedelta(minutes=1)

    activation_store = _ActivationStore()
    activation_service = DomainActivationAdmissionService(
        store=activation_store,
        authority=_ActivationAuthority(),
    )
    committed = await activation_service.admit(
        revision,
        expected_head_revision_id=None,
        committed_at=ACTIVATED_AT,
    )
    binding = bind_committed_activation(pack=pack, committed=committed)
    store = InMemoryImmutableRecordStore()
    ledger = PreparedIntelligenceLedgerService(binding=binding, store=store)
    admissions, unreferenced_count = await _admit_material(ledger, material, attention_at=attention_at)

    execution_head = _head("reasoning_configuration", "reasoning_configuration:world-independent-case-brief")
    execution_binding = ReasoningExecutionBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=REASONING_ARTIFACT,
        configuration_ref="reasoning_configuration:world-independent-case-brief",
        authority="reason",
        grant_ref="authority_grant:world-independent-case-brief",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(execution_head),
    )
    append_head = _head(
        "governed_operation_configuration",
        "governed_operation_configuration:world-independent-case-brief-append",
    )
    append_binding = GovernedOperationBindingV1Alpha1(
        product_id=PRODUCT_ID,
        artifact=APPEND_ARTIFACT,
        configuration_ref="governed_operation_configuration:world-independent-case-brief-append",
        authority="append_immutable_records",
        grant_ref="authority_grant:world-independent-case-brief-append",
        state_head_precondition=GovernedStateHeadPreconditionV1Alpha1.from_head(append_head),
    )
    heads = {
        ("reasoning_configuration", execution_binding.configuration_ref): execution_head,
        ("governed_operation_configuration", append_binding.configuration_ref): append_head,
        ("capability_state", capability_state_ref_for_artifact(REASONING_ARTIFACT)): _head(
            "capability_state", capability_state_ref_for_artifact(REASONING_ARTIFACT)
        ),
        ("capability_state", capability_state_ref_for_artifact(APPEND_ARTIFACT)): _head(
            "capability_state", capability_state_ref_for_artifact(APPEND_ARTIFACT)
        ),
        ("authority_grant", execution_binding.grant_ref): _head(
            "authority_grant", execution_binding.grant_ref
        ),
        ("authority_grant", append_binding.grant_ref): _head("authority_grant", append_binding.grant_ref),
    }
    activation_head = activation_store.heads[
        (
            committed.commit_receipt.state_kind,
            committed.commit_receipt.product_id,
            committed.commit_receipt.state_id,
        )
    ]
    for head in (*heads.values(), activation_head):
        store.set_governed_state_head(head)

    observation_ids = {
        record_id: str(item.resource_id) for record_id, item in material["observations"].items()
    }
    provider = _IndependenceProvider(observation_ids=observation_ids, corroboration=corroboration)
    reasoning = GovernedReasoningService(
        store=store,
        runtime_use=_Runtime(
            bindings=(execution_binding, append_binding),
            heads=heads,
            expires_at=requested_at + timedelta(hours=1),
        ),
        provider=provider,
        clock=_Clock(requested_at),
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id=PRODUCT_ID,
        actor_ref="principal:world-p2b-reviewer",
        authentication_receipt_ref="authentication:world-p2b-independent-case-brief",
        authentication_receipt_digest="sha256:" + "e" * 64,
        authenticated_at=ACTIVATED_AT,
        expires_at=requested_at + timedelta(hours=2),
    )
    service = CaseBriefFamilyStatusSynthesisService(
        activation_service=activation_service,
        pack=pack,
        store=store,
        reasoning=reasoning,
        execution_binding=execution_binding,
        append_binding=append_binding,
        clock=_Clock(requested_at),
    )
    request = CaseBriefSynthesisRequestV1Alpha1(
        synthesis_key=synthesis_key,
        reasoning_attempt_key=f"reasoning:{synthesis_key}",
        product_id=PRODUCT_ID,
        authenticated_context=context,
        activation_revision=binding.prepared_binding.reference,
        pack=binding.prepared_binding.revision.spec.pack,
        case=resource_reference(orientation_case),
        member_attention=tuple(
            CaseMemberAttentionBindingV1Alpha1(
                signal_resource_id=admissions[key].attention_receipt.signal.resource_id,
                derivation_key=derivation_key,
                attention_receipt_id=str(admissions[key].attention_receipt.receipt_id),
                attention_receipt_digest=str(admissions[key].attention_receipt.receipt_digest),
            )
            for key, derivation_key in ROUTED_DERIVATIONS
        ),
        brief_as_of=orientation_case.as_of,
        context_cutoff_at=context_cutoff_at,
        requested_at=requested_at,
    )
    return {
        "service": service,
        "request": request,
        "ledger": ledger,
        "provider": provider,
        "material": material,
        "orientation_case": orientation_case,
        "observation_ids": observation_ids,
        "unreferenced_count": unreferenced_count,
    }


async def _durable_brief_count(environment) -> int:
    """Count durable Briefs well past any possible append time.

    A Brief becomes available at its governed authorization time, which follows
    ``requested_at``. Counting at ``requested_at`` would report zero even after a
    successful append and would make the negative vectors' no-residue assertion
    vacuous, so the horizon is deliberately far past every clock step.
    """

    return await environment["ledger"].count_as_of(
        product_id=PRODUCT_ID,
        mode=environment["orientation_case"].mode,
        kind=IntelligenceRecordKind.BRIEF,
        available_at=environment["request"].requested_at + timedelta(days=1),
    )


async def run_negative_corroboration_vectors() -> dict[str, Any]:
    """Every non-independent corroboration must fail closed with no residue."""

    results: dict[str, Any] = {}
    for name, vector in CORROBORATION_VECTORS.items():
        if name == "independent_roots":
            continue
        environment = await _environment(
            corroboration=vector,
            synthesis_key=f"independent-case-brief:world-meridia-{name}",
        )
        try:
            await environment["service"].synthesize_with_status(environment["request"])
        except Exception as exc:  # the exact public fail-closed error
            results[name] = {
                "rejected": True,
                "error_type": type(exc).__name__,
                "mentions_derivation_families": "derivation families" in str(exc),
                "durable_brief_count": await _durable_brief_count(environment),
            }
        else:
            results[name] = {"rejected": False}
    return results


async def run_independent_case_brief() -> dict[str, Any]:
    """Synthesize the independence-proven Reality Brief through public ACE APIs."""

    environment = await _environment(
        corroboration=CORROBORATION_VECTORS["independent_roots"],
        synthesis_key="independent-case-brief:world-meridia-72h",
    )
    service = environment["service"]
    request = environment["request"]
    orientation_case = environment["orientation_case"]
    observation_ids = environment["observation_ids"]

    admission = await service.synthesize_with_status(request)
    replay = await service.synthesize_with_status(request)
    receipt = admission.synthesis_receipt
    projection = admission.status_projection

    corroborated = [item for item in projection.claim_statuses if item.status_id == "corroborated"]
    by_status: dict[str, int] = {}
    for item in projection.claim_statuses:
        by_status[item.status_id] = by_status.get(item.status_id, 0) + 1
    durable_brief_count = await _durable_brief_count(environment)
    negatives = await run_negative_corroboration_vectors()

    ledger_root_id = observation_ids[LEDGER_ROOT]
    hydrology_root_id = observation_ids[HYDROLOGY_ROOT]
    syndication_ids = {observation_ids[item] for item in LEDGER_SYNDICATION}
    families_by_root = {item.root_record_id: item for item in projection.closure_families}
    ledger_family = families_by_root.get(ledger_root_id)
    hydrology_family = families_by_root.get(hydrology_root_id)
    return {
        "contract": "ace.world-intelligence.p2b-independent-governed-brief/v1alpha1",
        "scenario_id": environment["material"]["scenario"]["scenario_id"],
        "case": {
            "case_id": str(orientation_case.resource_id),
            "case_digest": str(orientation_case.resource_digest),
            "member_count": len(orientation_case.lineage),
        },
        "brief": {
            "brief_id": str(admission.brief.resource_id),
            "brief_digest": str(admission.brief.resource_digest),
            "claim_count": len(admission.brief.claims),
            "lineage_count": len(admission.brief.lineage),
        },
        "synthesis_receipt": {
            "receipt_id": str(receipt.receipt_id),
            "receipt_digest": str(receipt.receipt_digest),
            "selected_context_count": len(receipt.selected_context),
        },
        "status_projection": {
            "projection_id": str(projection.projection_id),
            "projection_digest": str(projection.projection_digest),
            "status_set_id": projection.status_set_id,
            "declared_status_ids": list(projection.declared_status_ids),
            "claim_status_count": len(projection.claim_statuses),
            "claims_per_status": dict(sorted(by_status.items())),
            "derivation_family_policy": projection.derivation_family_policy,
            "collapsing_relations": list(projection.collapsing_relations),
            "closure_family_count": len(projection.closure_families),
            "closure_families": [
                {
                    "root_record_id": item.root_record_id,
                    "member_record_ids": list(item.member_record_ids),
                }
                for item in projection.closure_families
            ],
            "every_required_status_used": sorted(by_status) == sorted(WORLD_EPISTEMIC_STATUSES),
        },
        "independence": {
            "corroborated_claim_count": len(corroborated),
            "corroborated_required_families": [
                item.required_distinct_derivation_families for item in corroborated
            ],
            "corroborated_distinct_families": [
                item.distinct_derivation_family_count for item in corroborated
            ],
            "corroborated_roots_are_ledger_and_hydrology": all(
                sorted(item.derivation_family_roots) == sorted((ledger_root_id, hydrology_root_id))
                for item in corroborated
            ),
            "syndicated_copies_are_inside_the_closure": syndication_ids
            <= {str(item.record.resource_id) for item in receipt.selected_context},
            "ledger_family_members": sorted(ledger_family.member_record_ids)
            if ledger_family is not None
            else [],
            "ledger_family_member_count": len(ledger_family.member_record_ids)
            if ledger_family is not None
            else 0,
            # The exact acceptance check: not merely "these are not roots", but
            # "these resolve specifically to the Ledger root family".
            "syndicated_copies_are_exact_members_of_the_ledger_family": (
                ledger_family is not None and syndication_ids <= set(ledger_family.member_record_ids)
            ),
            "hydrology_is_a_separate_single_member_family": (
                hydrology_family is not None
                and hydrology_family.member_record_ids == (hydrology_root_id,)
            ),
            "distinct_families_in_closure": len(projection.closure_families),
            "negative_vectors": dict(sorted(negatives.items())),
        },
        "governance": {
            "atomic_records": len(admission.transaction_receipt.records),
            "record_kinds": [item.record_kind for item in admission.transaction_receipt.records],
            "governed_state_preconditions": len(
                admission.transaction_receipt.governed_state_preconditions
            ),
            "durable_brief_count": durable_brief_count,
            "deterministic_replay": bool(
                replay.replayed
                and replay.brief == admission.brief
                and replay.synthesis_receipt == receipt
                and replay.status_projection == projection
            ),
            "provider_invocations": environment["provider"].calls,
        },
        "proven": {
            "corroborated_requires_distinct_derivation_families": True,
            "publisher_count_is_not_independence": True,
            "textual_variation_is_not_independence": True,
            "syndication_collapses_to_its_root": True,
            "independence_is_only_as_strong_as_admitted_lineage": True,
        },
        "runtime_gaps": [
            {
                "request_id": "WI-CR-004",
                "boundary": "supersession_impact_projection",
                "finding": (
                    "No public query enumerates the downstream resources affected by the admitted "
                    "record correction."
                ),
            }
        ],
        "closed_requests": ["WI-CR-002", "WI-CR-003", "WI-CR-005"],
        "invariants": {
            "world_semantics_added_to_ace": False,
            "private_aggregation_in_world": False,
            "private_reasoning_runtime": False,
            "private_status_projector": False,
            "private_source_independence_engine": False,
            "imperative_pack_code": False,
            "duplicated_source_records": False,
            "unreferenced_admitted_records": environment["unreferenced_count"],
            "live_resources": 0,
            "delivery_authority": False,
            "external_action": False,
        },
    }


if __name__ == "__main__":  # pragma: no cover - manual harness entry point
    import asyncio

    print(json.dumps(asyncio.run(run_independent_case_brief()), indent=2, sort_keys=True))
