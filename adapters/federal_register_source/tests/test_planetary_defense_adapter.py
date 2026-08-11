from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import SourceAdapterCaptureRequestV1Alpha1

from ace_world_federal_register_source import (
    ESA_INITIAL_PROFILE,
    ESA_PLANETARY_DEFENCE_SOURCE_TYPE,
    ESA_REVISED_PROFILE,
    NASA_INITIAL_PROFILE,
    NASA_PLANETARY_DEFENSE_SOURCE_TYPE,
    NASA_REVISED_PROFILE,
    PLANETARY_DEFENSE_LOCATOR,
    PlanetaryDefenseRetrievalResult,
    PlanetaryDefenseSourceAdapter,
    PlanetaryDefenseSourceAdapterError,
)

ARTIFACT_DIGEST = "sha256:" + "6" * 64
STARTED = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
PROFILES = (
    NASA_INITIAL_PROFILE,
    NASA_REVISED_PROFILE,
    ESA_INITIAL_PROFILE,
    ESA_REVISED_PROFILE,
)


def _body(profile, **changes: str) -> str:
    title = changes.get("title", profile.title)
    published = changes.get("published", profile.publication_date + "T00:00:00+00:00")
    canonical = changes.get("canonical", profile.requested_uri)
    statement = changes.get("statement", " ".join(profile.required_statements))
    return (
        "<!doctype html><html><head>"
        f'<meta property="og:title" content="{title}">'
        f'<meta property="article:published_time" content="{published}">'
        f'<link rel="canonical" href="{canonical}">'
        f"</head><body><article><h1>{title}</h1><p>{statement}</p>"
        "</article></body></html>"
    )


class _Transport:
    def __init__(self, result: PlanetaryDefenseRetrievalResult) -> None:
        self.result = result
        self.calls = 0

    async def retrieve(self, request):
        assert request.requested_uri == self.result.requested_uri
        self.calls += 1
        return self.result


def _result(profile, **changes: object) -> PlanetaryDefenseRetrievalResult:
    base = PlanetaryDefenseRetrievalResult(
        source_type_ref=profile.source_type_ref,
        requested_uri=profile.requested_uri,
        effective_uri=profile.requested_uri,
        status_code=200,
        media_type="text/html",
        response_body=_body(profile),
        redirect_chain=(),
        resolved_ip_addresses=("1.1.1.1",),
        connected_ip_addresses=("1.1.1.1",),
        dns_rebinding_protection_applied=True,
        credentials_used=False,
        locator=PLANETARY_DEFENSE_LOCATOR,
        observed_at=STARTED + timedelta(seconds=1),
        captured_at=STARTED + timedelta(seconds=2),
    )
    return replace(base, **changes)


def _adapter_and_request(profile, **changes: object):
    transport = _Transport(_result(profile, **changes))
    adapter = PlanetaryDefenseSourceAdapter(
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
        source_type_ref=profile.source_type_ref,
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id="product:world-planetary-defense",
        actor_ref="actor:world-planetary-defense-researcher",
        authentication_receipt_ref="authentication_receipt:planetary-defense",
        authentication_receipt_digest="sha256:" + "7" * 64,
        authenticated_at=STARTED - timedelta(minutes=1),
        expires_at=STARTED + timedelta(minutes=10),
    )
    request = SourceAdapterCaptureRequestV1Alpha1(
        product_id=context.product_id,
        authenticated_context=context,
        use_subject_ref="live_source_ingress_request:planetary-defense",
        use_subject_digest="sha256:" + "8" * 64,
        source_definition_ref="source_definition:planetary-defense",
        source_type_ref=profile.source_type_ref,
        requested_uri=profile.requested_uri,
        adapter_artifact=adapter.artifact_identity,
        configuration_ref="config:planetary-defense",
        configuration_digest="sha256:" + "9" * 64,
        started_at=STARTED,
        max_payload_chars=512_000,
    )
    return adapter, transport, request


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", PROFILES, ids=lambda item: item.source_lineage_id)
async def test_exact_planetary_defense_publication_becomes_closed_inert_material(profile) -> None:
    adapter, transport, request = _adapter_and_request(profile)
    capture = await adapter.capture(request)
    payload = json.loads(capture.captured_payload_json)

    assert payload == {
        "assessment_note": profile.assessment_note,
        "assessment_subject": "earth_impact_probability",
        "claimant_office": profile.claimant_office,
        "claimant_org": profile.claimant_org,
        "estimate_status": profile.estimate_status,
        "impact_probability_percent": format(profile.probability_percent, "g"),
        "object_name": "2024 YR4",
        "predecessor_lineage_id": profile.predecessor_lineage_id,
        "publication_date": profile.publication_date,
        "source_lineage_id": profile.source_lineage_id,
        "source_uri": profile.requested_uri,
        "target_date": "2032-12-22",
    }
    assert capture.source_published_at == datetime.fromisoformat(profile.publication_date).replace(tzinfo=UTC)
    assert capture.requested_uri == capture.effective_uri == profile.requested_uri
    assert adapter.capture_calls == transport.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status_code": 404}, "HTTP 200"),
        ({"media_type": "application/json"}, "text/html"),
        ({"effective_uri": NASA_INITIAL_PROFILE.requested_uri + "?other=1"}, "URI scope"),
        ({"redirect_chain": (NASA_INITIAL_PROFILE.requested_uri,)}, "empty tuple"),
        ({"credentials_used": True}, "false credentials"),
        ({"resolved_ip_addresses": ("127.0.0.1",)}, "globally routable"),
        ({"connected_ip_addresses": ("8.8.8.8",)}, "exactly attested"),
        ({"locator": "css:h1"}, "article locator"),
        ({"response_body": _body(NASA_INITIAL_PROFILE, title="Different")}, "title"),
        ({"response_body": _body(NASA_INITIAL_PROFILE, published="2025-02-08")}, "publication date"),
        ({"response_body": _body(NASA_INITIAL_PROFILE, canonical="https://example.com")}, "canonical URI"),
        ({"response_body": _body(NASA_INITIAL_PROFILE, statement="2.3%")}, "estimate statement"),
        ({"captured_at": STARTED}, "observation/capture times"),
    ],
)
async def test_planetary_defense_adapter_fails_closed(
    changes: dict[str, object],
    message: str,
) -> None:
    adapter, _, request = _adapter_and_request(NASA_INITIAL_PROFILE, **changes)
    with pytest.raises(PlanetaryDefenseSourceAdapterError, match=message):
        await adapter.capture(request)


def test_planetary_defense_adapter_rejects_cross_claimant_source_type() -> None:
    with pytest.raises(PlanetaryDefenseSourceAdapterError, match="unsupported"):
        PlanetaryDefenseSourceAdapter(
            transport=object(),
            artifact_digest=ARTIFACT_DIGEST,
            source_type_ref="other",
        )
    assert NASA_PLANETARY_DEFENSE_SOURCE_TYPE != ESA_PLANETARY_DEFENCE_SOURCE_TYPE
