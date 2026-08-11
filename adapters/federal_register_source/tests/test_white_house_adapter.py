from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import SourceAdapterCaptureRequestV1Alpha1

from ace_world_federal_register_source import (
    WHITE_HOUSE_LOCATOR,
    WHITE_HOUSE_RELEASE_TITLE,
    WHITE_HOUSE_RELEASE_URI,
    WHITE_HOUSE_SOURCE_TYPE,
    WhiteHouseAIPolicySourceAdapter,
    WhiteHouseRetrievalResult,
    WhiteHouseSourceAdapterError,
)

ARTIFACT_DIGEST = "sha256:" + "6" * 64
STARTED = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)


def _body(**changes: str) -> str:
    title = changes.get("title", WHITE_HOUSE_RELEASE_TITLE)
    published = changes.get("published", "2026-07-14T12:00:00+00:00")
    canonical = changes.get("canonical", WHITE_HOUSE_RELEASE_URI)
    statement = changes.get(
        "statement",
        (
            "GOLD EAGLE, established in Executive Order 14409, has already begun "
            "to intake and prioritize identified cybersecurity vulnerabilities."
        ),
    )
    return (
        "<!doctype html><html><head>"
        f'<meta property="og:title" content="{title}">'
        f'<meta property="article:published_time" content="{published}">'
        f'<link rel="canonical" href="{canonical}">'
        f"</head><body><article><h1>{title}</h1><p>{statement}</p>"
        "</article></body></html>"
    )


class _Transport:
    def __init__(self, result: WhiteHouseRetrievalResult) -> None:
        self.result = result
        self.calls = 0

    async def retrieve(self, request):
        self.calls += 1
        return self.result


def _result(**changes: object) -> WhiteHouseRetrievalResult:
    base = WhiteHouseRetrievalResult(
        source_type_ref=WHITE_HOUSE_SOURCE_TYPE,
        requested_uri=WHITE_HOUSE_RELEASE_URI,
        effective_uri=WHITE_HOUSE_RELEASE_URI,
        status_code=200,
        media_type="text/html",
        response_body=_body(),
        redirect_chain=(),
        resolved_ip_addresses=("1.1.1.1",),
        connected_ip_addresses=("1.1.1.1",),
        dns_rebinding_protection_applied=True,
        credentials_used=False,
        locator=WHITE_HOUSE_LOCATOR,
        observed_at=STARTED + timedelta(seconds=1),
        captured_at=STARTED + timedelta(seconds=2),
    )
    return replace(base, **changes)


def _adapter_and_request(**changes: object):
    transport = _Transport(_result(**changes))
    adapter = WhiteHouseAIPolicySourceAdapter(
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id="product:world-ai-watch",
        actor_ref="actor:world-ai-analyst",
        authentication_receipt_ref="authentication_receipt:white-house-ai-policy",
        authentication_receipt_digest="sha256:" + "7" * 64,
        authenticated_at=STARTED - timedelta(minutes=1),
        expires_at=STARTED + timedelta(minutes=10),
    )
    request = SourceAdapterCaptureRequestV1Alpha1(
        product_id=context.product_id,
        authenticated_context=context,
        use_subject_ref="live_source_ingress_request:white-house-ai-policy",
        use_subject_digest="sha256:" + "8" * 64,
        source_definition_ref="source_definition:white-house-gold-eagle-2026-07-14",
        source_type_ref=WHITE_HOUSE_SOURCE_TYPE,
        requested_uri=WHITE_HOUSE_RELEASE_URI,
        adapter_artifact=adapter.artifact_identity,
        configuration_ref="config:white-house-gold-eagle-2026-07-14",
        configuration_digest="sha256:" + "9" * 64,
        started_at=STARTED,
        max_payload_chars=512_000,
    )
    return adapter, transport, request


@pytest.mark.asyncio
async def test_exact_white_house_release_becomes_closed_inert_material() -> None:
    adapter, transport, request = _adapter_and_request()
    capture = await adapter.capture(request)

    assert json.loads(capture.captured_payload_json) == {
        "agency_name": "The White House",
        "development_stage": "implementation_reported",
        "document_number": "white-house-release-2026-07-14-gold-eagle",
        "document_title": WHITE_HOUSE_RELEASE_TITLE,
        "document_type": "Official Release",
        "executive_order_number": "14409",
        "federal_register_url": (
            "https://www.federalregister.gov/documents/2026/06/05/2026-11415/"
            "promoting-advanced-artificial-intelligence-innovation-and-security"
        ),
        "initiative_name": "GOLD EAGLE",
        "legal_status_notice": (
            "WhiteHouse.gov announces implementation; it is not the legal edition of Executive Order 14409."
        ),
        "linked_policy_ref": "executive_order:14409",
        "official_pdf_url": ("https://www.govinfo.gov/content/pkg/FR-2026-06-05/pdf/2026-11415.pdf"),
        "policy_status": "implementation_reported",
        "policy_topic": "artificial_intelligence",
        "publication_date": "2026-07-14",
        "source_lineage_id": "white_house_release:gold_eagle_2026_07_14",
        "source_uri": WHITE_HOUSE_RELEASE_URI,
        "verification_reference": (
            "The release names Executive Order 14409; the govinfo PDF remains the official-format order reference."
        ),
    }
    assert capture.source_published_at == datetime(2026, 7, 14, tzinfo=UTC)
    assert capture.requested_uri == capture.effective_uri == WHITE_HOUSE_RELEASE_URI
    assert adapter.capture_calls == transport.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status_code": 404}, "HTTP 200"),
        ({"media_type": "application/json"}, "text/html"),
        ({"effective_uri": WHITE_HOUSE_RELEASE_URI + "?other=1"}, "URI scope"),
        ({"redirect_chain": (WHITE_HOUSE_RELEASE_URI,)}, "empty tuple"),
        ({"credentials_used": True}, "false credentials"),
        ({"resolved_ip_addresses": ("127.0.0.1",)}, "globally routable"),
        ({"connected_ip_addresses": ("8.8.8.8",)}, "exactly attested"),
        ({"locator": "css:h1"}, "release locator"),
        ({"response_body": _body(title="Different")}, "title"),
        ({"response_body": _body(published="2026-07-15")}, "publication date"),
        ({"response_body": _body(canonical="https://example.com/release")}, "canonical URI"),
        ({"response_body": _body(statement="GOLD EAGLE")}, "implementation statements"),
        ({"captured_at": STARTED}, "observation/capture times"),
    ],
)
async def test_white_house_adapter_fails_closed(
    changes: dict[str, object],
    message: str,
) -> None:
    adapter, _, request = _adapter_and_request(**changes)
    with pytest.raises(WhiteHouseSourceAdapterError, match=message):
        await adapter.capture(request)
