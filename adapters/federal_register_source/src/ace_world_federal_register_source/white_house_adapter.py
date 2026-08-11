"""Exact read-only adapter for one official White House AI-policy release."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol

from ace.core import CapabilityArtifactIdentityV1Alpha1, canonical_json, validate_exact_https_uri
from ace.intelligence import CapturedSourceMaterialV1Alpha1, SourceAdapterCaptureRequestV1Alpha1

from .adapter import (
    ADAPTER_CAPABILITY,
    ADAPTER_CONTRACT,
    _aware_utc,
    _validated_addresses,
)
from .ai_policy_adapter import (
    AI_POLICY_EXECUTIVE_ORDER_NUMBER,
    AI_POLICY_HTML_URI,
    AI_POLICY_LINKED_POLICY_REF,
    AI_POLICY_OFFICIAL_PDF_URI,
)

WHITE_HOUSE_IMPLEMENTATION_ID = "world_ai_policy_white_house_source"
WHITE_HOUSE_IMPLEMENTATION_VERSION = "0.1.0"
WHITE_HOUSE_SOURCE_TYPE = "white_house_ai_policy_release"
WHITE_HOUSE_RELEASE_URI = (
    "https://www.whitehouse.gov/releases/2026/07/"
    "white-house-launches-gold-eagle-initiative-for-unprecedented-"
    "cybersecurity-vulnerability-coordination/"
)
WHITE_HOUSE_RELEASE_TITLE = (
    "White House Launches Gold Eagle Initiative for Unprecedented "
    "Cybersecurity Vulnerability Coordination"
)
WHITE_HOUSE_RELEASE_DATE = "2026-07-14"
WHITE_HOUSE_RELEASE_IDENTIFIER = "white-house-release-2026-07-14-gold-eagle"
WHITE_HOUSE_LINEAGE_ID = "white_house_release:gold_eagle_2026_07_14"
WHITE_HOUSE_LOCATOR = "css:article"
WHITE_HOUSE_LEGAL_STATUS_NOTICE = (
    "WhiteHouse.gov announces implementation; it is not the legal edition of Executive Order 14409."
)
WHITE_HOUSE_VERIFICATION_REFERENCE = (
    "The release names Executive Order 14409; the govinfo PDF remains the official-format order reference."
)
MAX_RESPONSE_BODY_CHARS = 512_000


class WhiteHouseSourceAdapterError(ValueError):
    """The White House retrieval failed the exact reviewed adapter contract."""


@dataclass(frozen=True, slots=True)
class WhiteHouseRetrievalRequest:
    source_type_ref: str
    requested_uri: str
    max_response_chars: int
    credentials_allowed: bool = False
    redirects_allowed: bool = False
    public_network_only: bool = True
    dns_rebinding_protection_required: bool = True


@dataclass(frozen=True, slots=True)
class WhiteHouseRetrievalResult:
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


class WhiteHouseTransport(Protocol):
    async def retrieve(
        self,
        request: WhiteHouseRetrievalRequest,
    ) -> WhiteHouseRetrievalResult: ...


def _fail(message: str) -> WhiteHouseSourceAdapterError:
    return WhiteHouseSourceAdapterError(message)


class _ReleaseHTML(HTMLParser):
    """Extract only reviewed metadata and bounded visible source text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metadata: dict[str, str] = {}
        self.canonical_uri: str | None = None
        self.visible: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value is not None}
        if tag in {"script", "style", "template", "noscript"}:
            self._ignored_depth += 1
        if tag == "meta":
            key = values.get("property") or values.get("name")
            content = values.get("content")
            if key in {"og:title", "article:published_time"} and content is not None:
                if key in self.metadata:
                    raise _fail(f"duplicate reviewed White House metadata: {key}")
                self.metadata[key] = content
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            if self.canonical_uri is not None:
                raise _fail("duplicate reviewed White House canonical URI")
            self.canonical_uri = values.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            normalized = " ".join(data.split())
            if normalized:
                self.visible.append(normalized)


def _canonical_release_payload(response_body: object, *, max_chars: int) -> str:
    if type(response_body) is not str:
        raise _fail("White House response body must be text")
    if not response_body or len(response_body) > max_chars:
        raise _fail("White House response body exceeded its exact character bound")
    parser = _ReleaseHTML()
    try:
        parser.feed(response_body)
        parser.close()
    except WhiteHouseSourceAdapterError:
        raise
    except (TypeError, ValueError) as exc:
        raise _fail("White House response is not bounded parseable HTML") from exc

    if parser.metadata.get("og:title") != WHITE_HOUSE_RELEASE_TITLE:
        raise _fail("White House title crossed the exact reviewed release scope")
    published = parser.metadata.get("article:published_time", "")
    if not published.startswith(WHITE_HOUSE_RELEASE_DATE):
        raise _fail("White House publication date crossed the exact reviewed release scope")
    if parser.canonical_uri != WHITE_HOUSE_RELEASE_URI:
        raise _fail("White House canonical URI crossed the exact reviewed release scope")
    validate_exact_https_uri(parser.canonical_uri, name="canonical_uri")

    visible = " ".join(parser.visible)
    required_statements = (
        "GOLD EAGLE",
        "Executive Order 14409",
        "has already begun to intake and prioritize identified cybersecurity vulnerabilities",
    )
    if any(statement not in visible for statement in required_statements):
        raise _fail("White House release omitted exact reviewed implementation statements")

    return canonical_json(
        {
            "agency_name": "The White House",
            "development_stage": "implementation_reported",
            "document_number": WHITE_HOUSE_RELEASE_IDENTIFIER,
            "document_title": WHITE_HOUSE_RELEASE_TITLE,
            "document_type": "Official Release",
            "executive_order_number": AI_POLICY_EXECUTIVE_ORDER_NUMBER,
            "federal_register_url": AI_POLICY_HTML_URI,
            "initiative_name": "GOLD EAGLE",
            "legal_status_notice": WHITE_HOUSE_LEGAL_STATUS_NOTICE,
            "linked_policy_ref": AI_POLICY_LINKED_POLICY_REF,
            "official_pdf_url": AI_POLICY_OFFICIAL_PDF_URI,
            "policy_status": "implementation_reported",
            "policy_topic": "artificial_intelligence",
            "publication_date": WHITE_HOUSE_RELEASE_DATE,
            "source_lineage_id": WHITE_HOUSE_LINEAGE_ID,
            "source_uri": WHITE_HOUSE_RELEASE_URI,
            "verification_reference": WHITE_HOUSE_VERIFICATION_REFERENCE,
        }
    )


class WhiteHouseAIPolicySourceAdapter:
    """Validate one exact release retrieval and return inert canonical material."""

    def __init__(self, *, transport: WhiteHouseTransport, artifact_digest: str) -> None:
        self._transport = transport
        self.artifact_identity = CapabilityArtifactIdentityV1Alpha1(
            capability=ADAPTER_CAPABILITY,
            contract=ADAPTER_CONTRACT,
            implementation_id=WHITE_HOUSE_IMPLEMENTATION_ID,
            implementation_version=WHITE_HOUSE_IMPLEMENTATION_VERSION,
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
        if validated.source_type_ref != WHITE_HOUSE_SOURCE_TYPE:
            raise _fail("source-adapter request names an unsupported White House source type")
        if validated.requested_uri != WHITE_HOUSE_RELEASE_URI:
            raise _fail("source-adapter request crossed the exact White House URI")
        validate_exact_https_uri(validated.requested_uri, name="requested_uri")

        transport_request = WhiteHouseRetrievalRequest(
            source_type_ref=validated.source_type_ref,
            requested_uri=validated.requested_uri,
            max_response_chars=min(validated.max_payload_chars, MAX_RESPONSE_BODY_CHARS),
        )
        self.capture_calls += 1
        result = await self._transport.retrieve(transport_request)
        if type(result) is not WhiteHouseRetrievalResult:
            raise _fail("transport returned an unsupported White House retrieval-result type")
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
            raise _fail("White House retrieval scalar fields must use exact string types")
        if type(result.status_code) is not int:
            raise _fail("White House retrieval status_code must use the exact integer type")
        if type(result.redirect_chain) is not tuple or result.redirect_chain != ():
            raise _fail("White House retrieval redirect_chain must be exactly an empty tuple")
        if type(result.credentials_used) is not bool or result.credentials_used is not False:
            raise _fail("White House retrieval must attest exact false credentials_used")
        if (
            type(result.dns_rebinding_protection_applied) is not bool
            or result.dns_rebinding_protection_applied is not True
        ):
            raise _fail("White House retrieval must attest exact true DNS-rebinding protection")
        if (
            result.source_type_ref != WHITE_HOUSE_SOURCE_TYPE
            or result.requested_uri != WHITE_HOUSE_RELEASE_URI
            or result.effective_uri != WHITE_HOUSE_RELEASE_URI
        ):
            raise _fail("White House retrieval crossed source type or exact URI scope")
        if result.locator != WHITE_HOUSE_LOCATOR:
            raise _fail("White House retrieval does not bind the exact release locator")
        if result.status_code != 200 or result.media_type != "text/html":
            raise _fail("White House retrieval must be exact HTTP 200 text/html material")

        try:
            resolved = _validated_addresses(
                result.resolved_ip_addresses,
                name="resolved_ip_addresses",
            )
            connected = _validated_addresses(
                result.connected_ip_addresses,
                name="connected_ip_addresses",
            )
            observed_at = _aware_utc(result.observed_at, name="observed_at")
            captured_at = _aware_utc(result.captured_at, name="captured_at")
        except ValueError as exc:
            raise _fail(str(exc)) from exc
        if connected != resolved:
            raise _fail("every resolved and connected White House address must remain exactly attested")
        if observed_at < validated.started_at or captured_at < observed_at:
            raise _fail("White House observation/capture times fall outside the exact operation")

        payload_json = _canonical_release_payload(
            result.response_body,
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
            locator=WHITE_HOUSE_LOCATOR,
            source_published_at=datetime(2026, 7, 14, tzinfo=UTC),
            event_effective_at=None,
            observed_at=observed_at,
            captured_at=captured_at,
        )


__all__ = [
    "WHITE_HOUSE_IMPLEMENTATION_ID",
    "WHITE_HOUSE_IMPLEMENTATION_VERSION",
    "WHITE_HOUSE_LINEAGE_ID",
    "WHITE_HOUSE_LOCATOR",
    "WHITE_HOUSE_RELEASE_DATE",
    "WHITE_HOUSE_RELEASE_IDENTIFIER",
    "WHITE_HOUSE_RELEASE_TITLE",
    "WHITE_HOUSE_RELEASE_URI",
    "WHITE_HOUSE_SOURCE_TYPE",
    "WhiteHouseAIPolicySourceAdapter",
    "WhiteHouseRetrievalRequest",
    "WhiteHouseRetrievalResult",
    "WhiteHouseSourceAdapterError",
    "WhiteHouseTransport",
]
