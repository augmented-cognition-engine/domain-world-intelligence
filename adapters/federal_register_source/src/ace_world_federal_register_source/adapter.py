"""Credential-free adapter for one exact Federal Register document."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from ace.core import (
    CapabilityArtifactIdentityV1Alpha1,
    canonical_json,
    validate_exact_https_uri,
    validate_public_ip_literal,
)
from ace.intelligence import (
    CapturedSourceMaterialV1Alpha1,
    SourceAdapterCaptureRequestV1Alpha1,
)

ADAPTER_CAPABILITY = "source_snapshot"
ADAPTER_CONTRACT = "ace.source.snapshot/v1alpha1"
ADAPTER_IMPLEMENTATION_ID = "world_federal_register_source"
ADAPTER_IMPLEMENTATION_VERSION = "0.1.0"

FEDERAL_REGISTER_SOURCE_TYPE = "federal_register_document"
DOCUMENT_NUMBER = "2026-16197"
FEDERAL_REGISTER_DOCUMENT_URI = "https://www.federalregister.gov/api/v1/documents/2026-16197.json"
FEDERAL_REGISTER_HTML_URI = (
    "https://www.federalregister.gov/documents/2026/08/07/2026-16197/"
    "protecting-against-national-security-threats-to-the-communications-supply-chain-through-the"
)
OFFICIAL_PDF_URI = "https://www.govinfo.gov/content/pkg/FR-2026-08-07/pdf/2026-16197.pdf"
FEDERAL_REGISTER_LOCATOR = "json-pointer:/document_number"
PUBLICATION_DATE = "2026-08-07"
AGENCY_NAME = "Federal Communications Commission"
DOCUMENT_TYPE = "Proposed Rule"
DOCUMENT_TITLE = (
    "Protecting Against National Security Threats to the Communications Supply "
    "Chain Through the Equipment Authorization Program"
)

LEGAL_STATUS_NOTICE = "FederalRegister.gov is not the official legal edition."
VERIFICATION_REFERENCE = "The govinfo.gov PDF is the official-format verification reference."

MAX_RESPONSE_BODY_CHARS = 32_768
MAX_TITLE_CHARS = 1_000


class FederalRegisterSourceAdapterError(ValueError):
    """The injected retrieval result failed the adapter contract."""


@dataclass(frozen=True, slots=True)
class FederalRegisterRetrievalRequest:
    """Bounded request presented to a separately reviewed transport."""

    source_type_ref: str
    requested_uri: str
    max_response_chars: int
    credentials_allowed: bool = False
    redirects_allowed: bool = False
    public_network_only: bool = True
    dns_rebinding_protection_required: bool = True


@dataclass(frozen=True, slots=True)
class FederalRegisterRetrievalResult:
    """Transport attestation plus untrusted response material."""

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


class FederalRegisterTransport(Protocol):
    """Host-supplied network boundary; this package ships no implementation."""

    async def retrieve(
        self,
        request: FederalRegisterRetrievalRequest,
    ) -> FederalRegisterRetrievalResult: ...


def _fail(message: str) -> FederalRegisterSourceAdapterError:
    return FederalRegisterSourceAdapterError(message)


def _aware_utc(value: object, *, name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _fail(f"{name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _fail(f"duplicate Federal Register field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise _fail(f"non-finite JSON token is not allowed: {value}")


def _text(value: object, *, name: str, maximum: int) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        raise _fail(f"{name} must be text with length 1..{maximum}")
    if any(
        ord(character) < 0x20 or ord(character) == 0x7F or 0xD800 <= ord(character) <= 0xDFFF for character in value
    ):
        raise _fail(f"{name} contains controls, DEL, or a lone surrogate")
    return value


@dataclass(frozen=True, slots=True)
class FederalRegisterDocumentProfile:
    """Exact reviewed identity for one credential-free Federal Register record."""

    document_number: str
    title: str
    document_type: str
    publication_date: str
    agency_name: str
    document_uri: str
    html_uri: str
    official_pdf_uri: str


DEFAULT_DOCUMENT_PROFILE = FederalRegisterDocumentProfile(
    document_number=DOCUMENT_NUMBER,
    title=DOCUMENT_TITLE,
    document_type=DOCUMENT_TYPE,
    publication_date=PUBLICATION_DATE,
    agency_name=AGENCY_NAME,
    document_uri=FEDERAL_REGISTER_DOCUMENT_URI,
    html_uri=FEDERAL_REGISTER_HTML_URI,
    official_pdf_uri=OFFICIAL_PDF_URI,
)


def _canonical_document_payload(
    response_body: object,
    *,
    max_chars: int,
    profile: FederalRegisterDocumentProfile = DEFAULT_DOCUMENT_PROFILE,
) -> str:
    if type(response_body) is not str:
        raise _fail("Federal Register response body must be text")
    if not response_body or len(response_body) > max_chars:
        raise _fail("Federal Register response body exceeded its exact character bound")
    try:
        payload = json.loads(
            response_body,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except FederalRegisterSourceAdapterError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise _fail("Federal Register response is not unambiguous bounded JSON") from exc
    if type(payload) is not dict:
        raise _fail("Federal Register response must be one JSON object")

    title = _text(payload.get("title"), name="title", maximum=MAX_TITLE_CHARS)
    document_number = _text(payload.get("document_number"), name="document_number", maximum=32)
    document_type = _text(payload.get("type"), name="type", maximum=128)
    publication_date = _text(payload.get("publication_date"), name="publication_date", maximum=10)
    html_url = _text(payload.get("html_url"), name="html_url", maximum=2_048)
    official_pdf_url = _text(payload.get("pdf_url"), name="pdf_url", maximum=2_048)
    agencies = payload.get("agencies")
    if type(agencies) is not list or len(agencies) != 1 or type(agencies[0]) is not dict:
        raise _fail("agencies must contain exactly one agency object")
    agency_name = _text(agencies[0].get("name"), name="agencies[0].name", maximum=256)

    exact = {
        "title": (title, profile.title),
        "document_number": (document_number, profile.document_number),
        "document_type": (document_type, profile.document_type),
        "publication_date": (publication_date, profile.publication_date),
        "agency_name": (agency_name, profile.agency_name),
        "federal_register_url": (html_url, profile.html_uri),
        "official_pdf_url": (official_pdf_url, profile.official_pdf_uri),
    }
    for name, (actual, expected) in exact.items():
        if actual != expected:
            raise _fail(f"{name} crossed the exact reviewed document scope")
    validate_exact_https_uri(html_url, name="html_url")
    validate_exact_https_uri(official_pdf_url, name="pdf_url")

    return canonical_json(
        {
            "agency_name": agency_name,
            "document_number": document_number,
            "document_type": document_type,
            "federal_register_url": html_url,
            "legal_status_notice": LEGAL_STATUS_NOTICE,
            "official_pdf_url": official_pdf_url,
            "publication_date": publication_date,
            "title": title,
            "verification_reference": VERIFICATION_REFERENCE,
        }
    )


def _validated_addresses(values: object, *, name: str) -> tuple[str, ...]:
    if type(values) is not tuple or not 1 <= len(values) <= 32:
        raise _fail(f"{name} must attest 1..32 addresses")
    try:
        normalized = tuple(validate_public_ip_literal(value, name=name) for value in values if type(value) is str)
    except ValueError as exc:
        raise _fail(f"{name} must contain globally routable unicast literals") from exc
    if len(normalized) != len(values) or len(set(normalized)) != len(normalized):
        raise _fail(f"{name} must contain unique exact IP literals")
    return tuple(sorted(normalized))


class FederalRegisterSourceAdapter:
    """Validate injected retrievals against an explicit reviewed document allowlist."""

    def __init__(
        self,
        *,
        transport: FederalRegisterTransport,
        artifact_digest: str,
        profiles: tuple[FederalRegisterDocumentProfile, ...] = (DEFAULT_DOCUMENT_PROFILE,),
        implementation_id: str = ADAPTER_IMPLEMENTATION_ID,
        implementation_version: str = ADAPTER_IMPLEMENTATION_VERSION,
    ) -> None:
        if not profiles or len({item.document_uri for item in profiles}) != len(profiles):
            raise _fail("document profiles must be a non-empty exact URI allowlist")
        for profile in profiles:
            validate_exact_https_uri(profile.document_uri, name="profile.document_uri")
            validate_exact_https_uri(profile.html_uri, name="profile.html_uri")
            validate_exact_https_uri(profile.official_pdf_uri, name="profile.official_pdf_uri")
        self._transport = transport
        self._profiles = {item.document_uri: item for item in profiles}
        self.artifact_identity = CapabilityArtifactIdentityV1Alpha1(
            capability=ADAPTER_CAPABILITY,
            contract=ADAPTER_CONTRACT,
            implementation_id=implementation_id,
            implementation_version=implementation_version,
            artifact_digest=artifact_digest,
        )
        self.capture_calls = 0

    async def capture(
        self,
        request: SourceAdapterCaptureRequestV1Alpha1,
    ) -> CapturedSourceMaterialV1Alpha1:
        try:
            validated = SourceAdapterCaptureRequestV1Alpha1.model_validate(request.model_dump(mode="python"))
        except (AttributeError, TypeError, ValueError) as exc:
            raise _fail("source-adapter request failed exact public-contract revalidation") from exc
        if validated.adapter_artifact != self.artifact_identity:
            raise _fail("source-adapter request names a different installed artifact")
        if validated.source_type_ref != FEDERAL_REGISTER_SOURCE_TYPE:
            raise _fail("source-adapter request names an unsupported source type")
        profile = self._profiles.get(validated.requested_uri)
        if profile is None:
            raise _fail("source-adapter request crossed the exact Federal Register URI")
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
            result.source_type_ref != validated.source_type_ref
            or result.requested_uri != profile.document_uri
            or result.effective_uri != profile.document_uri
        ):
            raise _fail("retrieval result crossed source type or exact URI scope")
        if result.locator != FEDERAL_REGISTER_LOCATOR:
            raise _fail("retrieval result does not bind the exact extraction locator")
        if result.status_code != 200 or result.media_type != "application/json":
            raise _fail("retrieval result must be exact HTTP 200 application/json material")

        resolved = _validated_addresses(result.resolved_ip_addresses, name="resolved_ip_addresses")
        connected = _validated_addresses(result.connected_ip_addresses, name="connected_ip_addresses")
        if connected != resolved:
            raise _fail("every resolved and connected address must remain exactly attested")

        observed_at = _aware_utc(result.observed_at, name="observed_at")
        captured_at = _aware_utc(result.captured_at, name="captured_at")
        if observed_at < validated.started_at or captured_at < observed_at:
            raise _fail("retrieval observation/capture times fall outside the exact operation")

        payload_json = _canonical_document_payload(
            result.response_body,
            max_chars=transport_request.max_response_chars,
            profile=profile,
        )
        payload_digest = "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
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
            locator=FEDERAL_REGISTER_LOCATOR,
            source_published_at=None,
            event_effective_at=None,
            observed_at=observed_at,
            captured_at=captured_at,
        )


__all__ = [
    "ADAPTER_CAPABILITY",
    "ADAPTER_CONTRACT",
    "ADAPTER_IMPLEMENTATION_ID",
    "ADAPTER_IMPLEMENTATION_VERSION",
    "DEFAULT_DOCUMENT_PROFILE",
    "DOCUMENT_NUMBER",
    "FEDERAL_REGISTER_DOCUMENT_URI",
    "FEDERAL_REGISTER_LOCATOR",
    "FEDERAL_REGISTER_SOURCE_TYPE",
    "OFFICIAL_PDF_URI",
    "FederalRegisterDocumentProfile",
    "FederalRegisterRetrievalRequest",
    "FederalRegisterRetrievalResult",
    "FederalRegisterSourceAdapter",
    "FederalRegisterSourceAdapterError",
    "FederalRegisterTransport",
]
