from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import SourceAdapterCaptureRequestV1Alpha1

from ace_world_federal_register_source import (
    FEDERAL_REGISTER_DOCUMENT_URI,
    FEDERAL_REGISTER_LOCATOR,
    FEDERAL_REGISTER_SOURCE_TYPE,
    OFFICIAL_PDF_URI,
    FederalRegisterDocumentProfile,
    FederalRegisterRetrievalResult,
    FederalRegisterSourceAdapter,
    FederalRegisterSourceAdapterError,
)

ARTIFACT_DIGEST = "sha256:" + "a" * 64
STARTED = datetime(2026, 8, 7, 18, 0, tzinfo=UTC)
HTML_URI = (
    "https://www.federalregister.gov/documents/2026/08/07/2026-16197/"
    "protecting-against-national-security-threats-to-the-communications-supply-chain-through-the"
)


def _body(**changes: object) -> str:
    payload: dict[str, object] = {
        "title": (
            "Protecting Against National Security Threats to the Communications "
            "Supply Chain Through the Equipment Authorization Program"
        ),
        "document_number": "2026-16197",
        "type": "Proposed Rule",
        "publication_date": "2026-08-07",
        "agencies": [{"name": "Federal Communications Commission", "id": 161}],
        "html_url": HTML_URI,
        "pdf_url": OFFICIAL_PDF_URI,
        "abstract": "Unmapped source text is intentionally excluded from the canonical payload.",
    }
    payload.update(changes)
    return json.dumps(payload, separators=(",", ":"))


class _Transport:
    def __init__(self, result: FederalRegisterRetrievalResult) -> None:
        self.result = result
        self.calls = 0
        self.requests = []

    async def retrieve(self, request):
        self.calls += 1
        self.requests.append(request)
        return self.result


def _result(**changes: object) -> FederalRegisterRetrievalResult:
    base = FederalRegisterRetrievalResult(
        source_type_ref=FEDERAL_REGISTER_SOURCE_TYPE,
        requested_uri=FEDERAL_REGISTER_DOCUMENT_URI,
        effective_uri=FEDERAL_REGISTER_DOCUMENT_URI,
        status_code=200,
        media_type="application/json",
        response_body=_body(),
        redirect_chain=(),
        resolved_ip_addresses=("1.1.1.1",),
        connected_ip_addresses=("1.1.1.1",),
        dns_rebinding_protection_applied=True,
        credentials_used=False,
        locator=FEDERAL_REGISTER_LOCATOR,
        observed_at=STARTED + timedelta(seconds=1),
        captured_at=STARTED + timedelta(seconds=2),
    )
    return replace(base, **changes)


def _adapter_and_request(**result_changes: object):
    transport = _Transport(_result(**result_changes))
    adapter = FederalRegisterSourceAdapter(
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id="product:world-watch",
        actor_ref="actor:world-analyst",
        authentication_receipt_ref="authentication_receipt:p2c",
        authentication_receipt_digest="sha256:" + "b" * 64,
        authenticated_at=STARTED - timedelta(minutes=1),
        expires_at=STARTED + timedelta(minutes=10),
    )
    request = SourceAdapterCaptureRequestV1Alpha1(
        product_id=context.product_id,
        authenticated_context=context,
        use_subject_ref="live_source_ingress_request:fixture",
        use_subject_digest="sha256:" + "c" * 64,
        source_definition_ref="source_definition:federal-register-2026-16197",
        source_type_ref=FEDERAL_REGISTER_SOURCE_TYPE,
        requested_uri=FEDERAL_REGISTER_DOCUMENT_URI,
        adapter_artifact=adapter.artifact_identity,
        configuration_ref="config:federal-register-2026-16197",
        configuration_digest="sha256:" + "d" * 64,
        started_at=STARTED,
        max_payload_chars=32_768,
    )
    return adapter, transport, request


@pytest.mark.asyncio
async def test_exact_document_becomes_closed_canonical_inert_payload() -> None:
    adapter, transport, request = _adapter_and_request()

    capture = await adapter.capture(request)
    payload = json.loads(capture.captured_payload_json)

    assert payload == {
        "agency_name": "Federal Communications Commission",
        "document_number": "2026-16197",
        "document_type": "Proposed Rule",
        "federal_register_url": HTML_URI,
        "legal_status_notice": "FederalRegister.gov is not the official legal edition.",
        "official_pdf_url": OFFICIAL_PDF_URI,
        "publication_date": "2026-08-07",
        "title": (
            "Protecting Against National Security Threats to the Communications "
            "Supply Chain Through the Equipment Authorization Program"
        ),
        "verification_reference": ("The govinfo.gov PDF is the official-format verification reference."),
    }
    assert "abstract" not in payload
    assert capture.requested_uri == capture.effective_uri == FEDERAL_REGISTER_DOCUMENT_URI
    assert capture.locator == FEDERAL_REGISTER_LOCATOR
    assert capture.redirect_chain == ()
    assert capture.source_published_at is None
    assert capture.event_effective_at is None
    assert adapter.capture_calls == transport.calls == 1
    transport_request = transport.requests[0]
    assert transport_request.credentials_allowed is False
    assert transport_request.redirects_allowed is False
    assert transport_request.public_network_only is True
    assert transport_request.dns_rebinding_protection_required is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status_code": 404}, "HTTP 200"),
        ({"status_code": True}, "exact integer type"),
        ({"media_type": "text/html"}, "application/json"),
        ({"effective_uri": FEDERAL_REGISTER_DOCUMENT_URI + "?other=1"}, "URI scope"),
        ({"redirect_chain": (FEDERAL_REGISTER_DOCUMENT_URI,)}, "empty tuple"),
        ({"credentials_used": True}, "false credentials"),
        ({"dns_rebinding_protection_applied": False}, "DNS-rebinding"),
        ({"resolved_ip_addresses": ("127.0.0.1",)}, "globally routable"),
        ({"connected_ip_addresses": ("8.8.8.8",)}, "exactly attested"),
        ({"locator": "json-pointer:/title"}, "extraction locator"),
        ({"response_body": "not-json"}, "unambiguous bounded JSON"),
        ({"response_body": "x" * 32_769}, "character bound"),
        ({"response_body": _body(document_number="2026-00001")}, "document_number"),
        ({"response_body": _body(title="Changed title")}, "title"),
        ({"response_body": _body(type="Rule")}, "document_type"),
        ({"response_body": _body(publication_date="2026-08-08")}, "publication_date"),
        ({"response_body": _body(agencies=[])}, "exactly one agency"),
        (
            {"response_body": _body(agencies=[{"name": "Other Agency"}])},
            "agency_name",
        ),
        ({"response_body": _body(html_url="https://example.com/doc")}, "federal_register_url"),
        (
            {"response_body": _body(pdf_url="https://example.com/document.pdf")},
            "official_pdf_url",
        ),
        ({"captured_at": STARTED}, "observation/capture times"),
        ({"observed_at": STARTED - timedelta(seconds=1)}, "observation/capture times"),
    ],
)
async def test_untrusted_transport_material_fails_closed(changes: dict[str, object], message: str) -> None:
    adapter, _, request = _adapter_and_request(**changes)
    with pytest.raises(FederalRegisterSourceAdapterError, match=message):
        await adapter.capture(request)


@pytest.mark.asyncio
async def test_duplicate_key_and_missing_required_field_fail_closed() -> None:
    duplicate = _body().replace(
        '"document_number":"2026-16197"',
        '"document_number":"2026-16197","document_number":"2026-16197"',
    )
    adapter, _, request = _adapter_and_request(response_body=duplicate)
    with pytest.raises(FederalRegisterSourceAdapterError, match="duplicate"):
        await adapter.capture(request)

    missing = json.loads(_body())
    del missing["pdf_url"]
    adapter, _, request = _adapter_and_request(response_body=json.dumps(missing))
    with pytest.raises(FederalRegisterSourceAdapterError, match="pdf_url"):
        await adapter.capture(request)


@pytest.mark.asyncio
async def test_forged_artifact_and_different_uri_reject_before_transport() -> None:
    adapter, transport, request = _adapter_and_request()
    forged_artifact = request.model_copy(
        update={
            "adapter_artifact": request.adapter_artifact.model_copy(update={"artifact_digest": "sha256:" + "e" * 64})
        }
    )
    with pytest.raises(FederalRegisterSourceAdapterError, match="revalidation"):
        await adapter.capture(forged_artifact)
    assert transport.calls == 0

    different_uri = request.model_copy(
        update={"requested_uri": "https://www.federalregister.gov/api/v1/documents/2026-16196.json"}
    )
    with pytest.raises(FederalRegisterSourceAdapterError, match="revalidation"):
        await adapter.capture(different_uri)
    assert transport.calls == 0


@pytest.mark.asyncio
async def test_reviewed_multi_document_profile_preserves_exact_allowlist() -> None:
    prior_uri = "https://www.federalregister.gov/api/v1/documents/2026-15932.json"
    prior_html = (
        "https://www.federalregister.gov/documents/2026/08/06/2026-15932/"
        "information-collection-being-reviewed-by-the-federal-communications-commission"
    )
    prior_pdf = "https://www.govinfo.gov/content/pkg/FR-2026-08-06/pdf/2026-15932.pdf"
    prior = FederalRegisterDocumentProfile(
        document_number="2026-15932",
        title="Information Collection Being Reviewed by the Federal Communications Commission",
        document_type="Notice",
        publication_date="2026-08-06",
        agency_name="Federal Communications Commission",
        document_uri=prior_uri,
        html_uri=prior_html,
        official_pdf_uri=prior_pdf,
    )
    response_body = _body(
        title="Information Collection Being Reviewed by the Federal Communications Commission",
        document_number=prior.document_number,
        type=prior.document_type,
        publication_date=prior.publication_date,
        html_url=prior.html_uri,
        pdf_url=prior.official_pdf_uri,
    )
    result = _result(
        requested_uri=prior_uri,
        effective_uri=prior_uri,
        response_body=response_body,
    )
    transport = _Transport(result)
    adapter = FederalRegisterSourceAdapter(
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
        profiles=(prior,),
        implementation_id="world_federal_register_monitor_source",
        implementation_version="0.2.0",
    )
    _, _, default_request = _adapter_and_request()
    request = SourceAdapterCaptureRequestV1Alpha1.model_validate(
        {
            **default_request.model_dump(mode="python", exclude={"request_id", "request_digest"}),
            "requested_uri": prior_uri,
            "source_definition_ref": "source_definition:federal-register-2026-15932",
            "configuration_ref": "config:federal-register-2026-15932",
            "adapter_artifact": adapter.artifact_identity,
        }
    )

    capture = await adapter.capture(request)

    assert json.loads(capture.captured_payload_json)["document_number"] == "2026-15932"
    assert capture.requested_uri == prior_uri
    assert transport.calls == 1

    outside_allowlist = SourceAdapterCaptureRequestV1Alpha1.model_validate(
        {
            **request.model_dump(mode="python", exclude={"request_id", "request_digest"}),
            "requested_uri": FEDERAL_REGISTER_DOCUMENT_URI,
        }
    )
    with pytest.raises(FederalRegisterSourceAdapterError, match="exact Federal Register URI"):
        await adapter.capture(outside_allowlist)
    assert transport.calls == 1
