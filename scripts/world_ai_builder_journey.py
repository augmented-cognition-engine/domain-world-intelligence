"""World-owned strategies for the governed AI Command Center onboarding journey.

The Domain Pack remains inert JSON. This demonstration host binds two already
admitted recorded official-source lineages to public ACE agent seams. It makes
no network request, uses no model, and grants no authority implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ace.application import (
    BriefingAgent,
    ConnectionAgent,
    ConnectionEffect,
    IntelligenceAgent,
    IntelligenceBuilderSessionService,
    OntologyAgent,
    SourceFieldProfileV1,
    SourceOptionCatalogV1,
    SourceOptionV1,
    SourceSampleV1,
    SourceScopeProposalV1,
    SourceScopeSelectionV1,
    SourceValueKind,
)
from ace.application.briefing_agent_contracts import (
    BriefingDerivationV1,
    BriefingItemKind,
    BriefingItemV1,
    FirstBriefingPreviewV1,
)
from ace.application.intelligence_agent_contracts import (
    AudienceProposalV1,
    AuthorizedObservationSetV1,
    AuthorizedObservationV1,
    BaselineProposalV1,
    DetectorProposalV1,
    DetectorStrategyKind,
    EpistemicClassification,
    EpistemicStatementV1,
    IntelligenceCitationV1,
    IntelligenceConflictV1,
    IntelligenceModelProposalV1,
    MaterialityRuleV1,
    ProposedCadence,
    RoutingCadenceProposalV1,
    SuppressionGroupingRuleV1,
    WatchTargetKind,
    WatchTargetV1,
)
from ace.application.ontology_agent_contracts import (
    ConceptAttributeV1,
    ConceptCitationV1,
    ConceptEntityTypeV1,
    ConceptModelProposalV1,
    ConceptRelationshipTypeV1,
    ConceptTerminologyV1,
    ConceptValueKind,
)
from ace.core import ResolvedApprovalReceiptV1, canonical_hash
from ace.intelligence import CanonicalJsonValueV1Alpha1

SOURCE_APPROVAL = "approval:world-ai-builder-sources"
CONCEPT_APPROVAL = "approval:world-ai-builder-concepts"
WATCH_APPROVAL = "approval:world-ai-builder-watches"


@dataclass(frozen=True, slots=True)
class WorldAISourceMaterial:
    option_id: str
    display_name: str
    source_ref: str
    evidence_digest: str
    development_stage: str
    source_lineage: str
    observed_at: datetime
    as_of: datetime


class ExactWorldBuilderAuthority:
    """Resolve only the three explicit human approvals in this demonstration."""

    def __init__(self, *, approved: tuple[str, ...]) -> None:
        self.approved = frozenset(approved)

    async def resolve_approval(self, **request) -> ResolvedApprovalReceiptV1:
        if request["receipt_ref"] not in self.approved:
            raise PermissionError("World AI builder approval is not admitted")
        return ResolvedApprovalReceiptV1(
            receipt_ref=request["receipt_ref"],
            product_id=request["product_id"],
            subject_ref=request["subject_ref"],
            actor_ref=request["actor_ref"],
            receipt_hash=canonical_hash(
                {
                    **request,
                    "effective_at": request["effective_at"].isoformat(),
                }
            ),
            approved_at=request["effective_at"],
        )

    async def resolve_grant(self, **_request):
        raise PermissionError("World AI builder strategy resolves no grants")


class WorldAIRecordedSourceProvider:
    """Expose exact recorded source shapes through the registered provider seam."""

    def __init__(self, materials: tuple[WorldAISourceMaterial, ...]) -> None:
        self.materials = {item.option_id: item for item in materials}
        effects = (ConnectionEffect.CONNECTION_TEST, ConnectionEffect.BOUNDED_SAMPLE)
        connector_digest = f"sha256:{canonical_hash('world-ai-recorded-source-provider-v1')}"
        self._catalog = SourceOptionCatalogV1(
            provider_ref="provider:world-ai-recorded-official-sources",
            provider_digest=f"sha256:{canonical_hash('world-ai-recorded-provider-v1')}",
            options=tuple(
                SourceOptionV1(
                    option_id=item.option_id,
                    display_name=item.display_name,
                    connector_ref=f"connector:{item.option_id}",
                    connector_digest=connector_digest,
                    source_type_ref="source_type:official_ai_policy_record",
                    source_ref=item.source_ref,
                    permission_options=("read_public_record",),
                    scope_options=("development_stage", "source_lineage"),
                    allowed_effects=effects,
                    maximum_sample_records=1,
                )
                for item in materials
            ),
        )
        self.sample_calls = 0

    async def catalog(self) -> SourceOptionCatalogV1:
        return SourceOptionCatalogV1.model_validate(self._catalog.model_dump(mode="python"))

    async def test_and_sample(self, proposal: SourceScopeProposalV1) -> tuple[SourceSampleV1, ...]:
        self.sample_calls += 1
        options = {item.option_id: item for item in self._catalog.options}
        fields = (
            SourceFieldProfileV1(
                field_path="/development_stage",
                value_kind=SourceValueKind.STRING,
                nullable=False,
                observed_count=1,
                confidence=1.0,
            ),
            SourceFieldProfileV1(
                field_path="/source_lineage",
                value_kind=SourceValueKind.STRING,
                nullable=False,
                observed_count=1,
                confidence=1.0,
            ),
        )
        return tuple(
            SourceSampleV1(
                option_id=selection.option_id,
                connector_ref=options[selection.option_id].connector_ref,
                connector_digest=options[selection.option_id].connector_digest,
                source_ref=self.materials[selection.option_id].source_ref,
                scope_proposal_id=str(proposal.proposal_id),
                scope_proposal_digest=str(proposal.proposal_digest),
                permissions=selection.permissions,
                scopes=selection.scopes,
                effects_performed=selection.effects,
                sample_records=selection.sample_records,
                fields=fields,
                evidence_digest=self.materials[selection.option_id].evidence_digest,
                observed_at=self.materials[selection.option_id].observed_at,
            )
            for selection in proposal.selections
        )


class WorldAIConceptStrategy:
    async def propose(self, *, session, source_profile, user_intent, organization_terminology, created_at):
        citations: list[ConceptCitationV1] = []
        by_field: dict[str, list[str]] = {"/development_stage": [], "/source_lineage": []}
        for sample in source_profile.samples:
            for field in sample.fields:
                citation_id = f"{sample.option_id}_{field.field_path.removeprefix('/')}"
                citations.append(
                    ConceptCitationV1(
                        citation_id=citation_id,
                        source_profile_proposal_id=str(source_profile.proposal_id),
                        source_profile_proposal_digest=str(source_profile.proposal_digest),
                        source_sample_id=str(sample.sample_id),
                        source_sample_digest=str(sample.sample_digest),
                        source_ref=sample.source_ref,
                        field_path=field.field_path,
                        evidence_digest=sample.evidence_digest,
                    )
                )
                by_field[field.field_path].append(citation_id)
        all_citations = tuple(item.citation_id for item in citations)
        return ConceptModelProposalV1(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            goal_ref=session.goal_ref,
            user_intent=user_intent,
            source_profile_proposal_id=str(source_profile.proposal_id),
            source_profile_proposal_digest=str(source_profile.proposal_digest),
            revision=1,
            citations=tuple(citations),
            entity_types=(
                ConceptEntityTypeV1(
                    type_id="ai_policy_record",
                    display_name="AI policy record",
                    definition="An admitted official record describing one stage of an AI policy initiative.",
                    aliases=("official AI policy publication",),
                    attributes=(
                        ConceptAttributeV1(
                            attribute_id="development_stage",
                            display_name="Development stage",
                            value_kind=ConceptValueKind.STRING,
                            required=True,
                            citation_ids=tuple(by_field["/development_stage"]),
                            confidence=1.0,
                        ),
                        ConceptAttributeV1(
                            attribute_id="source_lineage",
                            display_name="Source lineage",
                            value_kind=ConceptValueKind.STRING,
                            required=True,
                            citation_ids=tuple(by_field["/source_lineage"]),
                            confidence=1.0,
                        ),
                    ),
                    citation_ids=all_citations,
                    confidence=0.98,
                ),
            ),
            relationship_types=(
                ConceptRelationshipTypeV1(
                    type_id="implements",
                    display_name="Implements",
                    definition="A later official record reports implementation of an earlier policy directive.",
                    from_type_id="ai_policy_record",
                    to_type_id="ai_policy_record",
                    aliases=("reports implementation of",),
                    citation_ids=tuple(by_field["/source_lineage"]),
                    confidence=0.9,
                ),
            ),
            terminology=(
                ConceptTerminologyV1(
                    term_id="policy_progression",
                    preferred_term="Policy progression",
                    definition="Movement from an official directive to a reported implementation milestone.",
                ),
            ),
            exclusions=("No organization, source, watch, or activation authority is created by this proposal.",),
            unknowns=("The two records do not independently verify downstream implementation outcomes.",),
            confidence=0.95,
            created_at=created_at,
        )


def _json(value: str) -> CanonicalJsonValueV1Alpha1:
    return CanonicalJsonValueV1Alpha1(value_json=value)


def _citation(citation_id: str, observation: AuthorizedObservationV1, field_path: str) -> IntelligenceCitationV1:
    return IntelligenceCitationV1(
        citation_id=citation_id,
        observation_id=str(observation.observation_id),
        observation_digest=str(observation.observation_digest),
        source_ref=observation.source_ref,
        evidence_digest=observation.evidence_digest,
        field_path=field_path,
    )


class WorldAIIntelligenceStrategy:
    async def propose(
        self,
        *,
        session,
        concept_model,
        concept_disposition,
        observations,
        user_intent,
        audience_constraints,
        cadence_constraints,
        created_at,
    ):
        baseline, current = tuple(sorted(observations.observations, key=lambda item: item.as_of))
        citations = (
            _citation("federal_register_stage", baseline, "/development_stage"),
            _citation("federal_register_lineage", baseline, "/source_lineage"),
            _citation("white_house_stage", current, "/development_stage"),
            _citation("white_house_lineage", current, "/source_lineage"),
        )
        stage_citations = ("federal_register_stage", "white_house_stage")
        lineage_citations = ("federal_register_lineage", "white_house_lineage")
        cadence = cadence_constraints[0] if cadence_constraints else ProposedCadence.DAILY
        return IntelligenceModelProposalV1(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            goal_ref=session.goal_ref,
            user_intent=user_intent,
            concept_model_proposal_id=str(concept_model.proposal_id),
            concept_model_proposal_digest=str(concept_model.proposal_digest),
            concept_model_disposition_id=str(concept_disposition.disposition_id),
            concept_model_disposition_digest=str(concept_disposition.disposition_digest),
            observation_set_id=str(observations.observation_set_id),
            observation_set_digest=str(observations.observation_set_digest),
            audience_constraints=audience_constraints,
            cadence_constraints=cadence_constraints,
            revision=1,
            citations=citations,
            watch_targets=(
                WatchTargetV1(
                    target_id="ai_policy_stage",
                    target_kind=WatchTargetKind.ATTRIBUTE,
                    entity_type_id="ai_policy_record",
                    member_id="development_stage",
                    citation_ids=stage_citations,
                ),
                WatchTargetV1(
                    target_id="ai_policy_implementation",
                    target_kind=WatchTargetKind.RELATIONSHIP,
                    entity_type_id="ai_policy_record",
                    member_id="implements",
                    citation_ids=lineage_citations,
                ),
            ),
            baselines=(
                BaselineProposalV1(
                    baseline_id="directive_stage_baseline",
                    target_id="ai_policy_stage",
                    value=_json('"directive_issued"'),
                    as_of=baseline.as_of,
                    citation_ids=("federal_register_stage",),
                ),
            ),
            detectors=(
                DetectorProposalV1(
                    detector_id="implementation_progression",
                    target_id="ai_policy_stage",
                    strategy=DetectorStrategyKind.CATEGORICAL_TRANSITION,
                    configuration=_json('{"allowed_transitions":["directive_issued->implementation_reported"]}'),
                    citation_ids=stage_citations,
                ),
            ),
            materiality_rules=(
                MaterialityRuleV1(
                    rule_id="official_implementation_milestone",
                    detector_id="implementation_progression",
                    minimum_change=1.0,
                    minimum_confidence=0.8,
                    rationale="A later official implementation report materially changes the policy picture.",
                    citation_ids=stage_citations,
                ),
            ),
            audiences=(
                AudienceProposalV1(
                    audience_id="ai_executive",
                    display_name="AI executive",
                    purpose=audience_constraints[0] if audience_constraints else "Track material AI policy movement.",
                ),
            ),
            routes=(
                RoutingCadenceProposalV1(
                    route_id="ai_policy_briefing",
                    audience_ids=("ai_executive",),
                    target_ids=("ai_policy_stage", "ai_policy_implementation"),
                    cadence=cadence,
                    minimum_confidence=0.8,
                ),
            ),
            suppression_grouping_rules=(
                SuppressionGroupingRuleV1(
                    rule_id="group_policy_progression",
                    target_ids=("ai_policy_stage", "ai_policy_implementation"),
                    group_by=("subject_ref",),
                    suppress_below_confidence=0.8,
                    rationale="Group the exact policy progression and suppress weakly supported movement.",
                ),
            ),
            epistemic_statements=(
                EpistemicStatementV1(
                    statement_id="official_stages_observed",
                    classification=EpistemicClassification.OBSERVATION,
                    statement="Two admitted official records describe directive and implementation-report stages.",
                    citation_ids=stage_citations,
                    confidence=1.0,
                ),
                EpistemicStatementV1(
                    statement_id="implementation_progression_claim",
                    classification=EpistemicClassification.CLAIM,
                    statement="The later White House release reports an implementation milestone tied to the directive.",
                    citation_ids=stage_citations,
                    confidence=0.95,
                ),
                EpistemicStatementV1(
                    statement_id="executive_attention_inference",
                    classification=EpistemicClassification.INFERENCE,
                    statement="The reported progression warrants executive review of implementation exposure.",
                    citation_ids=stage_citations,
                    confidence=0.82,
                ),
                EpistemicStatementV1(
                    statement_id="evidence_role_difference",
                    classification=EpistemicClassification.DISAGREEMENT,
                    statement="The two official lineages support different evidentiary roles and do not independently corroborate the same fact.",
                    citation_ids=lineage_citations,
                    confidence=0.9,
                ),
                EpistemicStatementV1(
                    statement_id="implementation_outcome_unknown",
                    classification=EpistemicClassification.UNKNOWN,
                    statement="Downstream implementation outcomes are not established by the two admitted records.",
                    citation_ids=lineage_citations,
                    confidence=0.6,
                ),
            ),
            conflicts=(
                IntelligenceConflictV1(
                    conflict_id="different_evidence_roles",
                    description="The legal directive and implementation announcement cannot substitute for independent outcome evidence.",
                    citation_ids=lineage_citations,
                    blocks_proposal=False,
                ),
            ),
            unknowns=("Independent evidence of implementation outcomes remains outside the admitted closure.",),
            exclusions=("No autonomous monitoring, delivery, publication, action, or activation authority.",),
            confidence=0.94,
            created_at=created_at,
        )


class WorldAIBriefingStrategy:
    async def synthesize(
        self,
        *,
        session,
        concept_model,
        concept_disposition,
        intelligence_model,
        intelligence_disposition,
        observations,
        generated_at,
    ):
        as_of = max(item.as_of for item in observations.observations)
        derivation = BriefingDerivationV1(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            concept_model_proposal_id=str(concept_model.proposal_id),
            concept_model_proposal_digest=str(concept_model.proposal_digest),
            concept_model_disposition_id=str(concept_disposition.disposition_id),
            concept_model_disposition_digest=str(concept_disposition.disposition_digest),
            intelligence_model_proposal_id=str(intelligence_model.proposal_id),
            intelligence_model_proposal_digest=str(intelligence_model.proposal_digest),
            intelligence_model_disposition_id=str(intelligence_disposition.disposition_id),
            intelligence_model_disposition_digest=str(intelligence_disposition.disposition_digest),
            observation_set_id=str(observations.observation_set_id),
            observation_set_digest=str(observations.observation_set_digest),
        )
        return FirstBriefingPreviewV1(
            derivation=derivation,
            title="AI policy moved from directive to reported implementation",
            executive_summary=(
                "Two admitted official lineages show Executive Order 14409 followed by a White House report of "
                "GOLD EAGLE implementation. The evidence supports a material policy progression, while independent "
                "implementation outcomes remain unknown."
            ),
            items=(
                BriefingItemV1(
                    item_id="official_policy_stages",
                    item_kind=BriefingItemKind.CURRENT_STATE,
                    title="Two official stages are admitted",
                    summary="The record closure contains an official directive and a later official implementation report.",
                    why_it_matters="The progression is grounded in two distinct first-party publication lineages.",
                    epistemic_classification=EpistemicClassification.OBSERVATION,
                    statement_ids=("official_stages_observed",),
                    citation_ids=("federal_register_stage", "white_house_stage"),
                    confidence=1.0,
                    uncertainty="First-party records establish what was issued and reported, not downstream outcomes.",
                ),
                BriefingItemV1(
                    item_id="reported_implementation_shift",
                    item_kind=BriefingItemKind.SHIFT,
                    title="Implementation milestone reported",
                    summary="The later White House release reports GOLD EAGLE implementation tied to the directive.",
                    why_it_matters="Executives can now distinguish a directive from a reported implementation milestone.",
                    epistemic_classification=EpistemicClassification.CLAIM,
                    statement_ids=("implementation_progression_claim",),
                    citation_ids=("federal_register_stage", "white_house_stage"),
                    confidence=0.95,
                    uncertainty="The implementation report is a first-party claim and is not independent outcome evidence.",
                    recommended_attention="Review operational exposure and seek independent outcome evidence.",
                    decision_question="Which implementation dependencies now affect the organization?",
                    materiality_rule_id="official_implementation_milestone",
                ),
                BriefingItemV1(
                    item_id="executive_review_signal",
                    item_kind=BriefingItemKind.SIGNAL,
                    title="Executive review is warranted",
                    summary="The policy progression may change implementation and cybersecurity planning assumptions.",
                    why_it_matters="It routes attention without creating a decision or external action.",
                    epistemic_classification=EpistemicClassification.INFERENCE,
                    statement_ids=("executive_attention_inference",),
                    citation_ids=("federal_register_stage", "white_house_stage"),
                    confidence=0.82,
                    uncertainty="The admitted closure does not establish organization-specific exposure.",
                    materiality_rule_id="official_implementation_milestone",
                ),
                BriefingItemV1(
                    item_id="evidence_roles_differ",
                    item_kind=BriefingItemKind.DISAGREEMENT,
                    title="The sources do not corroborate the same fact",
                    summary="The Federal Register establishes the directive; the White House release reports implementation.",
                    why_it_matters="Neither source should be presented as independent validation of the other.",
                    epistemic_classification=EpistemicClassification.DISAGREEMENT,
                    statement_ids=("evidence_role_difference",),
                    citation_ids=("federal_register_lineage", "white_house_lineage"),
                    counterevidence_citation_ids=("federal_register_lineage",),
                    confidence=0.9,
                    uncertainty="The evidence-role difference is explicit; it is not proof that either publication is false.",
                ),
                BriefingItemV1(
                    item_id="outcomes_remain_unknown",
                    item_kind=BriefingItemKind.UNKNOWN,
                    title="Implementation outcomes remain unknown",
                    summary="The two admitted records do not establish downstream effectiveness, adoption, or incidents.",
                    why_it_matters="ACE keeps the first picture useful without filling evidence gaps with inference.",
                    epistemic_classification=EpistemicClassification.UNKNOWN,
                    statement_ids=("implementation_outcome_unknown",),
                    citation_ids=("white_house_lineage",),
                    confidence=0.6,
                    uncertainty="Independent operational evidence has not been admitted.",
                    decision_question="Which independent source could close the outcome gap?",
                ),
            ),
            citations=intelligence_model.citations,
            as_of=as_of,
            freshness_statement=f"Recorded evidence current through {as_of.isoformat()}.",
            generated_at=generated_at,
        )


def _source_material(option_id: str, display_name: str, observation) -> WorldAISourceMaterial:
    payload = observation.payload.parsed_value()
    return WorldAISourceMaterial(
        option_id=option_id,
        display_name=display_name,
        source_ref=str(observation.source_ref),
        evidence_digest=str(observation.resource_digest),
        development_stage=payload["development_stage"],
        source_lineage=payload["source_lineage_id"],
        observed_at=observation.observed_at,
        as_of=observation.as_of,
    )


def _authorized_observations(*, session, source_profile, materials, admitted_at):
    material_by_ref = {item.source_ref: item for item in materials}
    observations = []
    for sample in source_profile.samples:
        material = material_by_ref[sample.source_ref]
        observations.append(
            AuthorizedObservationV1(
                source_profile_proposal_id=str(source_profile.proposal_id),
                source_profile_proposal_digest=str(source_profile.proposal_digest),
                source_sample_id=str(sample.sample_id),
                source_sample_digest=str(sample.sample_digest),
                source_ref=sample.source_ref,
                evidence_digest=sample.evidence_digest,
                subject_ref="entity:ai-policy/executive-order-14409",
                entity_type_id="ai_policy_record",
                attributes=_json(
                    f'{{"development_stage":"{material.development_stage}","source_lineage":"{material.source_lineage}"}}'
                ),
                observed_at=material.observed_at,
                admitted_at=admitted_at,
                as_of=admitted_at,
                confidence=1.0,
                unknown_fields=("implementation_outcomes",),
            )
        )
    return AuthorizedObservationSetV1(
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        source_profile_proposal_id=str(source_profile.proposal_id),
        source_profile_proposal_digest=str(source_profile.proposal_digest),
        observations=tuple(observations),
        closure_complete=True,
        admitted_at=admitted_at,
    )


async def run_world_ai_builder_journey(*, environment, baseline, current, started_at: datetime):
    """Run and reopen exact Connect -> Map -> Watch -> first Brief state."""

    materials = (
        _source_material("federal_register_ai_policy", "Federal Register AI policy record", baseline.observation),
        _source_material("white_house_ai_policy", "White House AI policy release", current.observation),
    )
    authority = ExactWorldBuilderAuthority(approved=(SOURCE_APPROVAL, CONCEPT_APPROVAL, WATCH_APPROVAL))
    sessions = IntelligenceBuilderSessionService(store=environment.store)
    provider = WorldAIRecordedSourceProvider(materials)
    connection = ConnectionAgent(sessions=sessions, authority=authority, provider=provider)
    actor = environment.context.actor_ref
    started = await sessions.start(
        product_id=environment.context.product_id,
        correlation_id="correlation:world-ai-command-center-onboarding",
        goal_ref="goal:track-material-ai-change",
        actor_ref=actor,
        occurred_at=started_at,
    )
    catalog = await connection.discover()
    selections = tuple(
        SourceScopeSelectionV1(
            option_id=option.option_id,
            permissions=("read_public_record",),
            scopes=("development_stage", "source_lineage"),
            effects=(ConnectionEffect.CONNECTION_TEST, ConnectionEffect.BOUNDED_SAMPLE),
            sample_records=1,
        )
        for option in catalog.options
    )
    scope = await connection.propose_scope(
        started.revision,
        catalog=catalog,
        selections=selections,
        actor_ref="agent:world-ai-connection",
        occurred_at=started_at + timedelta(seconds=1),
    )
    connected = await connection.connect(
        scope.session.revision,
        proposal=scope.proposal,
        approval_receipt_ref=SOURCE_APPROVAL,
        actor_ref=actor,
        occurred_at=started_at + timedelta(seconds=2),
    )
    if not connected.connected or connected.profile is None:
        raise AssertionError("World AI Connection Agent did not reach sources_ready")

    ontology = OntologyAgent(sessions=sessions, authority=authority, strategy=WorldAIConceptStrategy())
    mapped = await ontology.propose(
        connected.session.revision,
        source_profile=connected.profile,
        user_intent="Track material AI policy progression across distinct official source roles.",
        actor_ref="agent:world-ai-ontology",
        occurred_at=started_at + timedelta(seconds=3),
    )
    if not mapped.proposed or mapped.proposal is None:
        raise AssertionError("World AI Ontology Agent did not produce a concept proposal")
    concept = await ontology.approve(
        mapped.proposal.session.revision,
        proposal=mapped.proposal.proposal,
        approval_receipt_ref=CONCEPT_APPROVAL,
        actor_ref=actor,
        occurred_at=started_at + timedelta(seconds=4),
    )

    evidence = _authorized_observations(
        session=concept.session.revision,
        source_profile=connected.profile,
        materials=materials,
        admitted_at=started_at + timedelta(seconds=5),
    )
    intelligence = IntelligenceAgent(
        sessions=sessions,
        authority=authority,
        strategy=WorldAIIntelligenceStrategy(),
    )
    await intelligence.admit_observations(
        concept.session.revision,
        concept_model=mapped.proposal.proposal,
        concept_disposition=concept.disposition,
        source_profile=connected.profile,
        observations=evidence,
        occurred_at=started_at + timedelta(seconds=5),
    )
    proposed = await intelligence.propose(
        concept.session.revision,
        concept_model=mapped.proposal.proposal,
        concept_disposition=concept.disposition,
        observations=evidence,
        user_intent="Watch official AI policy progression and keep evidence-role limits visible.",
        audience_constraints=("Orient an executive without treating first-party claims as independent validation.",),
        cadence_constraints=(ProposedCadence.DAILY,),
        actor_ref="agent:world-ai-intelligence",
        occurred_at=started_at + timedelta(seconds=6),
    )
    if not proposed.proposed or proposed.proposal is None:
        raise AssertionError("World AI Intelligence Agent did not produce a watch proposal")
    watch = await intelligence.approve(
        proposed.proposal.session.revision,
        proposal=proposed.proposal.proposal,
        approval_receipt_ref=WATCH_APPROVAL,
        actor_ref=actor,
        occurred_at=started_at + timedelta(seconds=7),
    )
    briefing = await BriefingAgent(sessions=sessions, strategy=WorldAIBriefingStrategy()).create_first_brief(
        watch.session.revision,
        concept_model=mapped.proposal.proposal,
        concept_disposition=concept.disposition,
        intelligence_model=watch.proposal,
        intelligence_disposition=watch.disposition,
        observations=evidence,
        actor_ref="agent:world-ai-briefing",
        occurred_at=started_at + timedelta(seconds=8),
    )
    if not briefing.ready or briefing.briefing is None:
        raise AssertionError("World AI Briefing Agent did not produce the first Brief preview")
    reopened = await IntelligenceBuilderSessionService(store=environment.store).load_latest(
        product_id=environment.context.product_id,
        session_id=briefing.briefing.session.revision.session_id,
        available_at=started_at + timedelta(seconds=9),
    )
    if reopened != briefing.briefing.session.revision:
        raise AssertionError("World AI builder session did not reopen exactly")
    return briefing.briefing


__all__ = ["run_world_ai_builder_journey"]
