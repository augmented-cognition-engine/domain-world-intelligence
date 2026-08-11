"""Exact Federal Register adapter for one public AI-policy document."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Protocol

from ace.core import CapabilityArtifactIdentityV1Alpha1, canonical_json, validate_exact_https_uri
from ace.intelligence import CapturedSourceMaterialV1Alpha1, SourceAdapterCaptureRequestV1Alpha1

from .adapter import (
    ADAPTER_CAPABILITY,
    ADAPTER_CONTRACT,
    LEGAL_STATUS_NOTICE,
    VERIFICATION_REFERENCE,
    FederalRegisterRetrievalRequest,
    FederalRegisterRetrievalResult,
    _aware_utc,
    _reject_constant,
    _text,
    _unique_object,
    _validated_addresses,
)

AI_POLICY_IMPLEMENTATION_ID = "world_ai_policy_federal_register_source"
AI_POLICY_IMPLEMENTATION_VERSION = "0.1.0"
AI_POLICY_SOURCE_TYPE = "federal_register_ai_policy_document"
AI_POLICY_DOCUMENT_NUMBER = "2026-11415"
AI_POLICY_EXECUTIVE_ORDER_NUMBER = "14409"
AI_POLICY_PUBLICATION_DATE = "2026-06-05"
AI_POLICY_AGENCY_NAME = "Executive Office of the President"
AI_POLICY_DOCUMENT_TYPE = "Presidential Document"
AI_POLICY_TITLE = "Promoting Advanced Artificial Intelligence Innovation and Security"
AI_POLICY_DOCUMENT_URI = (
    "https://www.federalregister.gov/api/v1/documents/2026-11415.json"
)
AI_POLICY_HTML_URI = (
    "https://www.federalregister.gov/documents/2026/06/05/2026-11415/"
    "promoting-advanced-artificial-intelligence-innovation-and-security"
)
AI_POLICY_OFFICIAL_PDF_URI = (
    "https://www.govinfo.gov/content/pkg/FR-2026-06-05/pdf/2026-11415.pdf"
)
AI_POLICY_LOCATOR = "json-pointer:/document_number"
AI_POLICY_LINEAGE_ID = "federal_register:2026-11415"
AI_POLICY_LINKED_POLICY_REF = "executive_order:14409"
MAX_RESPONSE_BODY_CHARS = 32_768


class AIPolicyFederalRegisterSourceAdapterError(ValueError):
    """The AI-policy retrieval failed the exact reviewed adapter contract."""


class AIPolicyFederalRegisterTransport(Protocol):
    async def retrieve(
        self,
        request: FederalRegisterRetrievalRequest,
    ) -> FederalRegisterRetrievalResult: ...


def _fail(message: str) -> AIPolicyFederalRegisterSourceAdapterError:
    return AIPolicyFederalRegisterSourceAdapterError(message)


def _ai_text(value: object, *, name: str, maximum: int) -> str:
    try:
        return _text(value, name=name, maximum=maximum)
    except ValueError as exc:
        raise _fail(str(exc)) from exc


def _ai_addresses(values: object, *, name: str) -> tuple[str, ...]:
    try:
        return _validated_addresses(values, name=name)
    except ValueError as exc:
        raise _fail(str(exc)) from exc


def _ai_time(value: object, *, name: str):
    try:
        return _aware_utc(value, name=name)
    except ValueError as exc:
        raise _fail(str(exc)) from exc


def _canonical_ai_policy_payload(response_body: object, *, max_chars: int) -> str:
    if type(response_body) is not str:
        raise _fail("AI-policy response body must be text")
    if not response_body or len(response_body) > max_chars:
        raise _fail("AI-policy response body exceeded its exact character bound")
    try:
        payload = json.loads(
            response_body,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except AIPolicyFederalRegisterSourceAdapterError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise _fail("AI-policy response is not unambiguous bounded JSON") from exc
    if type(payload) is not dict:
        raise _fail("AI-policy response must be one JSON object")

    title = _ai_text(payload.get("title"), name="title", maximum=1_000)
    document_number = _ai_text(
        payload.get("document_number"), name="document_number", maximum=32
    )
    executive_order_number = _ai_text(
        payload.get("executive_order_number"),
        name="executive_order_number",
        maximum=32,
    )
    document_type = _ai_text(payload.get("type"), name="type", maximum=128)
    publication_date = _ai_text(
        payload.get("publication_date"), name="publication_date", maximum=10
    )
    html_url = _ai_text(payload.get("html_url"), name="html_url", maximum=2_048)
    pdf_url = _ai_text(payload.get("pdf_url"), name="pdf_url", maximum=2_048)
    agencies = payload.get("agencies")
    if type(agencies) is not list or len(agencies) != 1 or type(agencies[0]) is not dict:
        raise _fail("agencies must contain exactly one agency object")
    agency_name = _ai_text(
        agencies[0].get("name"), name="agencies[0].name", maximum=256
    )

    exact = {
        "title": (title, AI_POLICY_TITLE),
        "document_number": (document_number, AI_POLICY_DOCUMENT_NUMBER),
        "executive_order_number": (
            executive_order_number,
            AI_POLICY_EXECUTIVE_ORDER_NUMBER,
        ),
        "document_type": (document_type, AI_POLICY_DOCUMENT_TYPE),
        "publication_date": (publication_date, AI_POLICY_PUBLICATION_DATE),
        "agency_name": (agency_name, AI_POLICY_AGENCY_NAME),
        "federal_register_url": (html_url, AI_POLICY_HTML_URI),
        "official_pdf_url": (pdf_url, AI_POLICY_OFFICIAL_PDF_URI),
    }
    for name, (actual, expected) in exact.items():
        if actual != expected:
            raise _fail(f"{name} crossed the exact reviewed AI-policy document scope")
    validate_exact_https_uri(html_url, name="html_url")
    validate_exact_https_uri(pdf_url, name="pdf_url")

    return canonical_json(
        {
            "agency_name": agency_name,
            "document_number": document_number,
            "document_title": title,
            "document_type": document_type,
            "development_stage": "directive_issued",
            "executive_order_number": executive_order_number,
            "federal_register_url": html_url,
            "initiative_name": "Executive Order 14409",
            "legal_status_notice": LEGAL_STATUS_NOTICE,
            "linked_policy_ref": AI_POLICY_LINKED_POLICY_REF,
            "official_pdf_url": pdf_url,
            "policy_status": "issued",
            "policy_topic": "artificial_intelligence",
            "publication_date": publication_date,
            "source_lineage_id": AI_POLICY_LINEAGE_ID,
            "source_uri": html_url,
            "verification_reference": VERIFICATION_REFERENCE,
        }
    )


class AIPolicyFederalRegisterSourceAdapter:
    """Validate one exact AI-policy retrieval and return inert canonical material."""

    def __init__(
        self,
        *,
        transport: AIPolicyFederalRegisterTransport,
        artifact_digest: str,
    ) -> None:
        self._transport = transport
        self.artifact_identity = CapabilityArtifactIdentityV1Alpha1(
            capability=ADAPTER_CAPABILITY,
            contract=ADAPTER_CONTRACT,
            implementation_id=AI_POLICY_IMPLEMENTATION_ID,
            implementation_version=AI_POLICY_IMPLEMENTATION_VERSION,
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
        if validated.source_type_ref != AI_POLICY_SOURCE_TYPE:
            raise _fail("source-adapter request names an unsupported AI-policy source type")
        if validated.requested_uri != AI_POLICY_DOCUMENT_URI:
            raise _fail("source-adapter request crossed the exact AI-policy URI")
        validate_exact_https_uri(validated.requested_uri, name="requested_uri")

        transport_request = FederalRegisterRetrievalRequest(
            source_type_ref=validated.source_type_ref,
            requested_uri=validated.requested_uri,
            max_response_chars=min(validated.max_payload_chars, MAX_RESPONSE_BODY_CHARS),
        )
        self.capture_calls += 1
        result = await self._transport.retrieve(transport_request)
        if type(result) is not FederalRegisterRetrievalResult:
            raise _fail("transport returned an unsupported retrieval-result type")
        if any(
            type(value) is not str
            for value in (
                result.source_type_ref,
                result.requested_uri,
                result.effective_uri,
                result.media_type,
                result.response_body,
                result.locator,
            )
        ):
            raise _fail("retrieval result scalar text fields must use exact string types")
        if type(result.status_code) is not int:
            raise _fail("retrieval result status_code must use the exact integer type")
        if type(result.redirect_chain) is not tuple or result.redirect_chain != ():
            raise _fail("retrieval result redirect_chain must be exactly an empty tuple")
        if type(result.credentials_used) is not bool or result.credentials_used is not False:
            raise _fail("retrieval result must attest exact false credentials_used")
        if (
            type(result.dns_rebinding_protection_applied) is not bool
            or result.dns_rebinding_protection_applied is not True
        ):
            raise _fail("retrieval result must attest exact true DNS-rebinding protection")
        if (
            result.source_type_ref != AI_POLICY_SOURCE_TYPE
            or result.requested_uri != AI_POLICY_DOCUMENT_URI
            or result.effective_uri != AI_POLICY_DOCUMENT_URI
        ):
            raise _fail("retrieval result crossed AI-policy source type or exact URI scope")
        if result.locator != AI_POLICY_LOCATOR:
            raise _fail("retrieval result does not bind the exact AI-policy locator")
        if result.status_code != 200 or result.media_type != "application/json":
            raise _fail("retrieval result must be exact HTTP 200 application/json material")

        resolved = _ai_addresses(
            result.resolved_ip_addresses, name="resolved_ip_addresses"
        )
        connected = _ai_addresses(
            result.connected_ip_addresses, name="connected_ip_addresses"
        )
        if connected != resolved:
            raise _fail("every resolved and connected address must remain exactly attested")
        observed_at = _ai_time(result.observed_at, name="observed_at")
        captured_at = _ai_time(result.captured_at, name="captured_at")
        if observed_at < validated.started_at or captured_at < observed_at:
            raise _fail("retrieval observation/capture times fall outside the exact operation")

        payload_json = _canonical_ai_policy_payload(
            result.response_body,
            max_chars=transport_request.max_response_chars,
        )
        payload_digest = "sha256:" + hashlib.sha256(
            payload_json.encode("utf-8")
        ).hexdigest()
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
            captured_payload_digest=payload_digest,
            locator=AI_POLICY_LOCATOR,
            source_published_at=datetime(2026, 6, 5, tzinfo=UTC),
            event_effective_at=None,
            observed_at=observed_at,
            captured_at=captured_at,
        )


__all__ = [
    "AI_POLICY_AGENCY_NAME",
    "AI_POLICY_DOCUMENT_NUMBER",
    "AI_POLICY_DOCUMENT_URI",
    "AI_POLICY_EXECUTIVE_ORDER_NUMBER",
    "AI_POLICY_HTML_URI",
    "AI_POLICY_IMPLEMENTATION_ID",
    "AI_POLICY_IMPLEMENTATION_VERSION",
    "AI_POLICY_LOCATOR",
    "AI_POLICY_OFFICIAL_PDF_URI",
    "AI_POLICY_PUBLICATION_DATE",
    "AI_POLICY_SOURCE_TYPE",
    "AI_POLICY_TITLE",
    "AIPolicyFederalRegisterSourceAdapter",
    "AIPolicyFederalRegisterSourceAdapterError",
]
