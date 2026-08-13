"""Bounded adapter for reviewed public AI publications.

The adapter is intentionally profile-driven.  Each profile names one exact
publisher URI and the minimum statements a recorded capture must preserve.
It emits a common inert payload for the World AI ontology; it never interprets
the publication as an independently verified conclusion.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from ace.core import CapabilityArtifactIdentityV1Alpha1, canonical_json, validate_exact_https_uri
from ace.intelligence import CapturedSourceMaterialV1Alpha1, SourceAdapterCaptureRequestV1Alpha1

from .adapter import (
    ADAPTER_CAPABILITY,
    ADAPTER_CONTRACT,
    _aware_utc,
    _reject_constant,
    _unique_object,
    _validated_addresses,
)

REVIEWED_AI_PUBLICATION_IMPLEMENTATION_VERSION = "0.1.0"
REVIEWED_AI_PUBLICATION_LOCATOR = "json-pointer:/source_uri"
REVIEWED_AI_PUBLICATION_SOURCE_TYPE = "reviewed_ai_publication"
MAX_RESPONSE_BODY_CHARS = 64_000


class ReviewedAIPublicationSourceAdapterError(ValueError):
    """A capture crossed its exact reviewed-publication boundary."""


@dataclass(frozen=True, slots=True)
class ReviewedAIPublicationProfile:
    source_id: str
    implementation_id: str
    publisher: str
    source_uri: str
    title: str
    publication_date: str
    watch_area: str
    evidence_role: str
    claim_summary: str
    required_markers: tuple[str, ...]

    @property
    def lineage_id(self) -> str:
        return f"reviewed_ai_publication:{self.source_id}:{self.publication_date}"


@dataclass(frozen=True, slots=True)
class ReviewedAIPublicationRetrievalRequest:
    source_type_ref: str
    requested_uri: str
    max_response_chars: int
    credentials_allowed: bool = False
    redirects_allowed: bool = False
    public_network_only: bool = True
    dns_rebinding_protection_required: bool = True


@dataclass(frozen=True, slots=True)
class ReviewedAIPublicationRetrievalResult:
    source_type_ref: str
    requested_uri: str
    effective_uri: str
    status_code: int
    media_type: str
    response_body: str
    redirect_chain: tuple[str, ...]
    resolved_ip_addresses: tuple[str, ...]
    connected_ip_addresses: tuple[str, ...]
    dns_rebinding_protection_applied: bool
    credentials_used: bool
    locator: str
    observed_at: datetime
    captured_at: datetime


class ReviewedAIPublicationTransport(Protocol):
    async def retrieve(
        self,
        request: ReviewedAIPublicationRetrievalRequest,
    ) -> ReviewedAIPublicationRetrievalResult: ...


OPENAI_GPT_56_PROFILE = ReviewedAIPublicationProfile(
    source_id="openai_gpt_5_6_release",
    implementation_id="world_ai_openai_gpt_5_6_publication",
    publisher="OpenAI",
    source_uri="https://openai.com/index/gpt-5-6/",
    title="GPT-5.6: Frontier intelligence that scales with your ambition",
    publication_date="2026-07-09",
    watch_area="models_and_capabilities",
    evidence_role="first_party_claim",
    claim_summary=(
        "OpenAI announced the GPT-5.6 model family and claimed stronger performance per dollar "
        "across coding, knowledge work, cybersecurity, and science."
    ),
    required_markers=("GPT-5.6", "performance per dollar", "cybersecurity", "science"),
)

ANTHROPIC_SONNET_5_PROFILE = ReviewedAIPublicationProfile(
    source_id="anthropic_claude_sonnet_5_release",
    implementation_id="world_ai_anthropic_sonnet_5_publication",
    publisher="Anthropic",
    source_uri="https://www.anthropic.com/news/claude-sonnet-5",
    title="Introducing Claude Sonnet 5",
    publication_date="2026-06-30",
    watch_area="models_and_capabilities",
    evidence_role="first_party_claim",
    claim_summary=(
        "Anthropic announced Claude Sonnet 5 and described it as a frontier model for coding, "
        "agents, and professional work at scale."
    ),
    required_markers=("Claude Sonnet 5", "coding", "agents", "professional work"),
)

DEEPMIND_MODEL_CARDS_PROFILE = ReviewedAIPublicationProfile(
    source_id="deepmind_gemini_3_6_model_cards",
    implementation_id="world_ai_deepmind_model_cards_publication",
    publisher="Google DeepMind",
    source_uri="https://deepmind.google/models/model-cards/",
    title="Model cards",
    publication_date="2026-07-21",
    watch_area="benchmarks_and_independent_evals",
    evidence_role="first_party_claim",
    claim_summary=(
        "Google DeepMind updated its model-card index for Gemini 3.6 Flash and Gemini 3.5 "
        "Flash-Lite, providing structured first-party evaluation disclosures."
    ),
    required_markers=("Gemini 3.6 Flash", "Gemini 3.5 Flash-Lite", "model card"),
)

NIST_AGENT_SECURITY_PROFILE = ReviewedAIPublicationProfile(
    source_id="nist_ai_agent_security_report",
    implementation_id="world_ai_nist_agent_security_publication",
    publisher="National Institute of Standards and Technology",
    source_uri=(
        "https://www.nist.gov/publications/summary-analysis-responses-request-information-"
        "regarding-security-considerations-ai"
    ),
    title=(
        "Summary Analysis of Responses to the Request for Information Regarding Security "
        "Considerations for AI Agents"
    ),
    publication_date="2026-05-18",
    watch_area="safety_security_and_incidents",
    evidence_role="authoritative_record",
    claim_summary=(
        "NIST reported broad agreement that AI agents introduce novel security threats and that "
        "existing cybersecurity practices require adaptation for secure adoption."
    ),
    required_markers=("AI agents", "novel security threats", "secure adoption", "NIST"),
)

NVIDIA_NAVER_INFRASTRUCTURE_PROFILE = ReviewedAIPublicationProfile(
    source_id="nvidia_naver_ai_factory_investment",
    implementation_id="world_ai_nvidia_naver_publication",
    publisher="NVIDIA",
    source_uri=(
        "https://nvidianews.nvidia.com/news/naver-nvidia-and-brookfield-to-expand-koreas-"
        "national-ai-factory-infrastructure-buildout"
    ),
    title="NAVER, NVIDIA and Brookfield to Expand Korea's National AI Factory Infrastructure Buildout",
    publication_date="2026-07-24",
    watch_area="capital_and_company_moves",
    evidence_role="first_party_claim",
    claim_summary=(
        "NVIDIA announced planned investment and financing for an expansion of NAVER's initial "
        "AI factory deployment from 55 megawatts to 200 megawatts by 2028."
    ),
    required_markers=("NAVER", "Brookfield", "200 megawatts", "2028", "$1 billion"),
)

REVIEWED_AI_PUBLICATION_PROFILES = (
    OPENAI_GPT_56_PROFILE,
    ANTHROPIC_SONNET_5_PROFILE,
    DEEPMIND_MODEL_CARDS_PROFILE,
    NIST_AGENT_SECURITY_PROFILE,
    NVIDIA_NAVER_INFRASTRUCTURE_PROFILE,
)


def _fail(message: str) -> ReviewedAIPublicationSourceAdapterError:
    return ReviewedAIPublicationSourceAdapterError(message)


def _canonical_payload(
    response_body: object,
    *,
    profile: ReviewedAIPublicationProfile,
    max_chars: int,
) -> str:
    if type(response_body) is not str or not response_body or len(response_body) > max_chars:
        raise _fail("reviewed publication body must be bounded text")
    try:
        payload = json.loads(
            response_body,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise _fail("reviewed publication body must be one JSON object") from exc
    if type(payload) is not dict or set(payload) != {
        "publisher",
        "publication_date",
        "source_uri",
        "title",
        "source_text",
    }:
        raise _fail("reviewed publication body crossed its exact five-field envelope")
    expected = {
        "publisher": profile.publisher,
        "publication_date": profile.publication_date,
        "source_uri": profile.source_uri,
        "title": profile.title,
    }
    for name, value in expected.items():
        if type(payload.get(name)) is not str or payload[name] != value:
            raise _fail(f"reviewed publication {name} crossed its exact profile")
    source_text = payload["source_text"]
    if type(source_text) is not str or not source_text or len(source_text) > 32_000:
        raise _fail("reviewed publication source_text is invalid or unbounded")
    if any(marker not in source_text for marker in profile.required_markers):
        raise _fail("reviewed publication omitted a required source marker")
    validate_exact_https_uri(profile.source_uri, name="source_uri")
    return canonical_json(
        {
            "claim_summary": profile.claim_summary,
            "evidence_role": profile.evidence_role,
            "publication_date": profile.publication_date,
            "publisher": profile.publisher,
            "source_id": profile.source_id,
            "source_lineage_id": profile.lineage_id,
            "source_title": profile.title,
            "source_uri": profile.source_uri,
            "topic_id": "artificial_intelligence",
            "watch_area": profile.watch_area,
        }
    )


class ReviewedAIPublicationSourceAdapter:
    """Validate one exact recorded public publication and emit inert material."""

    def __init__(
        self,
        *,
        profile: ReviewedAIPublicationProfile,
        transport: ReviewedAIPublicationTransport,
        artifact_digest: str,
    ) -> None:
        self.profile = profile
        self._transport = transport
        self.artifact_identity = CapabilityArtifactIdentityV1Alpha1(
            capability=ADAPTER_CAPABILITY,
            contract=ADAPTER_CONTRACT,
            implementation_id=profile.implementation_id,
            implementation_version=REVIEWED_AI_PUBLICATION_IMPLEMENTATION_VERSION,
            artifact_digest=artifact_digest,
        )
        self.capture_calls = 0

    async def capture(
        self,
        request: SourceAdapterCaptureRequestV1Alpha1,
    ) -> CapturedSourceMaterialV1Alpha1:
        try:
            validated = SourceAdapterCaptureRequestV1Alpha1.model_validate(
                request.model_dump(mode="python")
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise _fail("source-adapter request failed exact public-contract revalidation") from exc
        if validated.adapter_artifact != self.artifact_identity:
            raise _fail("source-adapter request names a different installed artifact")
        if validated.source_type_ref != REVIEWED_AI_PUBLICATION_SOURCE_TYPE:
            raise _fail("source-adapter request names an unsupported reviewed source type")
        if validated.requested_uri != self.profile.source_uri:
            raise _fail("source-adapter request crossed the exact reviewed URI")

        transport_request = ReviewedAIPublicationRetrievalRequest(
            source_type_ref=validated.source_type_ref,
            requested_uri=validated.requested_uri,
            max_response_chars=min(validated.max_payload_chars, MAX_RESPONSE_BODY_CHARS),
        )
        self.capture_calls += 1
        result = await self._transport.retrieve(transport_request)
        if type(result) is not ReviewedAIPublicationRetrievalResult:
            raise _fail("transport returned an unsupported reviewed-publication result")
        if (
            result.source_type_ref != REVIEWED_AI_PUBLICATION_SOURCE_TYPE
            or result.requested_uri != self.profile.source_uri
            or result.effective_uri != self.profile.source_uri
            or result.status_code != 200
            or result.media_type != "application/json"
            or result.locator != REVIEWED_AI_PUBLICATION_LOCATOR
            or result.redirect_chain != ()
            or result.credentials_used is not False
            or result.dns_rebinding_protection_applied is not True
        ):
            raise _fail("retrieval result crossed the exact reviewed-publication boundary")
        resolved = _validated_addresses(result.resolved_ip_addresses, name="resolved_ip_addresses")
        connected = _validated_addresses(result.connected_ip_addresses, name="connected_ip_addresses")
        if connected != resolved:
            raise _fail("resolved and connected addresses must remain exactly attested")
        observed_at = _aware_utc(result.observed_at, name="observed_at")
        captured_at = _aware_utc(result.captured_at, name="captured_at")
        if observed_at < validated.started_at or captured_at < observed_at:
            raise _fail("retrieval times fall outside the exact operation")
        payload_json = _canonical_payload(
            result.response_body,
            profile=self.profile,
            max_chars=transport_request.max_response_chars,
        )
        return CapturedSourceMaterialV1Alpha1(
            capture_request_ref=str(validated.request_id),
            capture_request_digest=str(validated.request_digest),
            source_type_ref=validated.source_type_ref,
            requested_uri=validated.requested_uri,
            effective_uri=result.effective_uri,
            redirect_chain=(),
            resolved_ip_addresses=resolved,
            dns_rebinding_protection_applied=True,
            captured_payload_json=payload_json,
            captured_payload_digest=(
                "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            ),
            locator=REVIEWED_AI_PUBLICATION_LOCATOR,
            source_published_at=datetime.fromisoformat(self.profile.publication_date).replace(tzinfo=UTC),
            event_effective_at=None,
            observed_at=observed_at,
            captured_at=captured_at,
        )
