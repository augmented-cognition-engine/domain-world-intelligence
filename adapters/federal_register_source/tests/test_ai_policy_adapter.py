from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import SourceAdapterCaptureRequestV1Alpha1

from ace_world_federal_register_source import (
    AI_POLICY_DOCUMENT_URI,
    AI_POLICY_HTML_URI,
    AI_POLICY_LOCATOR,
    AI_POLICY_OFFICIAL_PDF_URI,
    AI_POLICY_SOURCE_TYPE,
    AI_POLICY_TITLE,
    AIPolicyFederalRegisterSourceAdapter,
    AIPolicyFederalRegisterSourceAdapterError,
    FederalRegisterRetrievalResult,
)

ARTIFACT_DIGEST = "sha256:" + "a" * 64
STARTED = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def _body(**changes: object) -> str:
    payload: dict[str, object] = {
        "title": AI_POLICY_TITLE,
        "document_number": "2026-11415",
        "executive_order_number": "14409",
        "type": "Presidential Document",
        "publication_date": "2026-06-05",
        "agencies": [{"name": "Executive Office of the President", "id": 538}],
        "html_url": AI_POLICY_HTML_URI,
        "pdf_url": AI_POLICY_OFFICIAL_PDF_URI,
        "abstract": "Unmapped source text remains outside the canonical payload.",
    }
    payload.update(changes)
    return json.dumps(payload, separators=(",", ":"))


class _Transport:
    def __init__(self, result: FederalRegisterRetrievalResult) -> None:
        self.result = result
        self.calls = 0

    async def retrieve(self, request):
        self.calls += 1
        return self.result


def _result(**changes: object) -> FederalRegisterRetrievalResult:
    base = FederalRegisterRetrievalResult(
        source_type_ref=AI_POLICY_SOURCE_TYPE,
        requested_uri=AI_POLICY_DOCUMENT_URI,
        effective_uri=AI_POLICY_DOCUMENT_URI,
        status_code=200,
        media_type="application/json",
        response_body=_body(),
        redirect_chain=(),
        resolved_ip_addresses=("1.1.1.1",),
        connected_ip_addresses=("1.1.1.1",),
        dns_rebinding_protection_applied=True,
        credentials_used=False,
        locator=AI_POLICY_LOCATOR,
        observed_at=STARTED + timedelta(seconds=1),
        captured_at=STARTED + timedelta(seconds=2),
    )
    return replace(base, **changes)


def _adapter_and_request(**changes: object):
    transport = _Transport(_result(**changes))
    adapter = AIPolicyFederalRegisterSourceAdapter(
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id="product:world-ai-watch",
        actor_ref="actor:world-ai-analyst",
        authentication_receipt_ref="authentication_receipt:ai-policy",
        authentication_receipt_digest="sha256:" + "b" * 64,
        authenticated_at=STARTED - timedelta(minutes=1),
        expires_at=STARTED + timedelta(minutes=10),
    )
    request = SourceAdapterCaptureRequestV1Alpha1(
        product_id=context.product_id,
        authenticated_context=context,
        use_subject_ref="live_source_ingress_request:ai-policy",
        use_subject_digest="sha256:" + "c" * 64,
        source_definition_ref="source_definition:ai-policy-eo-14409",
        source_type_ref=AI_POLICY_SOURCE_TYPE,
        requested_uri=AI_POLICY_DOCUMENT_URI,
        adapter_artifact=adapter.artifact_identity,
        configuration_ref="config:ai-policy-eo-14409",
        configuration_digest="sha256:" + "d" * 64,
        started_at=STARTED,
        max_payload_chars=32_768,
    )
    return adapter, transport, request


@pytest.mark.asyncio
async def test_ai_policy_document_becomes_closed_attributable_metadata() -> None:
    adapter, transport, request = _adapter_and_request()
    capture = await adapter.capture(request)
    assert json.loads(capture.captured_payload_json) == {
        "agency_name": "Executive Office of the President",
        "document_number": "2026-11415",
        "document_title": AI_POLICY_TITLE,
        "document_type": "Presidential Document",
        "development_stage": "directive_issued",
        "executive_order_number": "14409",
        "federal_register_url": AI_POLICY_HTML_URI,
        "initiative_name": "Executive Order 14409",
        "legal_status_notice": "FederalRegister.gov is not the official legal edition.",
        "linked_policy_ref": "executive_order:14409",
        "official_pdf_url": AI_POLICY_OFFICIAL_PDF_URI,
        "policy_status": "issued",
        "policy_topic": "artificial_intelligence",
        "publication_date": "2026-06-05",
        "source_lineage_id": "federal_register:2026-11415",
        "source_uri": AI_POLICY_HTML_URI,
        "verification_reference": ("The govinfo.gov PDF is the official-format verification reference."),
    }
    assert "abstract" not in capture.captured_payload_json
    assert capture.requested_uri == capture.effective_uri == AI_POLICY_DOCUMENT_URI
    assert capture.source_published_at == datetime(2026, 6, 5, tzinfo=UTC)
    assert adapter.capture_calls == transport.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status_code": 404}, "HTTP 200"),
        ({"media_type": "text/html"}, "application/json"),
        ({"effective_uri": AI_POLICY_DOCUMENT_URI + "?other=1"}, "URI scope"),
        ({"credentials_used": True}, "false credentials"),
        ({"resolved_ip_addresses": ("127.0.0.1",)}, "globally routable"),
        ({"connected_ip_addresses": ("8.8.8.8",)}, "exactly attested"),
        ({"locator": "json-pointer:/title"}, "AI-policy locator"),
        ({"response_body": _body(document_number="2026-00001")}, "document_number"),
        ({"response_body": _body(executive_order_number="1")}, "executive_order_number"),
        ({"response_body": _body(title="Different")}, "title"),
        ({"response_body": _body(agencies=[])}, "exactly one agency"),
        ({"captured_at": STARTED}, "observation/capture times"),
    ],
)
async def test_ai_policy_adapter_fails_closed(
    changes: dict[str, object],
    message: str,
) -> None:
    adapter, _, request = _adapter_and_request(**changes)
    with pytest.raises(AIPolicyFederalRegisterSourceAdapterError, match=message):
        await adapter.capture(request)
