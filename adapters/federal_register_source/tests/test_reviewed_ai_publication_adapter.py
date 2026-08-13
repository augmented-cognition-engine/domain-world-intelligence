from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from ace.core import AuthenticatedRuntimeContextV1Alpha1
from ace.intelligence import SourceAdapterCaptureRequestV1Alpha1

from ace_world_federal_register_source import (
    OPENAI_GPT_56_PROFILE,
    REVIEWED_AI_PUBLICATION_LOCATOR,
    REVIEWED_AI_PUBLICATION_PROFILES,
    REVIEWED_AI_PUBLICATION_SOURCE_TYPE,
    ReviewedAIPublicationRetrievalResult,
    ReviewedAIPublicationSourceAdapter,
    ReviewedAIPublicationSourceAdapterError,
)

STARTED = datetime(2026, 8, 13, 17, 0, tzinfo=UTC)
ARTIFACT_DIGEST = "sha256:" + "a" * 64


def _body(profile, **changes: object) -> str:
    payload = {
        "publisher": profile.publisher,
        "publication_date": profile.publication_date,
        "source_uri": profile.source_uri,
        "title": profile.title,
        "source_text": " | ".join(profile.required_markers),
    }
    payload.update(changes)
    return json.dumps(payload, separators=(",", ":"))


class _Transport:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = 0

    async def retrieve(self, request):
        self.calls += 1
        assert request.requested_uri == self.result.requested_uri
        return self.result


def _adapter_and_request(profile=OPENAI_GPT_56_PROFILE, **changes: object):
    result = ReviewedAIPublicationRetrievalResult(
        source_type_ref=REVIEWED_AI_PUBLICATION_SOURCE_TYPE,
        requested_uri=profile.source_uri,
        effective_uri=profile.source_uri,
        status_code=200,
        media_type="application/json",
        response_body=_body(profile),
        redirect_chain=(),
        resolved_ip_addresses=("1.1.1.1",),
        connected_ip_addresses=("1.1.1.1",),
        dns_rebinding_protection_applied=True,
        credentials_used=False,
        locator=REVIEWED_AI_PUBLICATION_LOCATOR,
        observed_at=STARTED + timedelta(seconds=1),
        captured_at=STARTED + timedelta(seconds=2),
    )
    transport = _Transport(replace(result, **changes))
    adapter = ReviewedAIPublicationSourceAdapter(
        profile=profile,
        transport=transport,
        artifact_digest=ARTIFACT_DIGEST,
    )
    context = AuthenticatedRuntimeContextV1Alpha1(
        product_id="product:world-ai-command-center",
        actor_ref="actor:world-ai-analyst",
        authentication_receipt_ref="authentication_receipt:world-ai-wave-1",
        authentication_receipt_digest="sha256:" + "b" * 64,
        authenticated_at=STARTED - timedelta(minutes=1),
        expires_at=STARTED + timedelta(minutes=10),
    )
    request = SourceAdapterCaptureRequestV1Alpha1(
        product_id=context.product_id,
        authenticated_context=context,
        use_subject_ref="live_source_ingress_request:world-ai-wave-1",
        use_subject_digest="sha256:" + "c" * 64,
        source_definition_ref=f"source_definition:{profile.source_id}",
        source_type_ref=REVIEWED_AI_PUBLICATION_SOURCE_TYPE,
        requested_uri=profile.source_uri,
        adapter_artifact=adapter.artifact_identity,
        configuration_ref=f"configuration:{profile.source_id}",
        configuration_digest="sha256:" + "d" * 64,
        started_at=STARTED,
        max_payload_chars=64_000,
    )
    return adapter, transport, request


@pytest.mark.asyncio
@pytest.mark.parametrize("profile", REVIEWED_AI_PUBLICATION_PROFILES)
async def test_reviewed_ai_publication_profiles_emit_one_common_attributable_envelope(profile) -> None:
    adapter, transport, request = _adapter_and_request(profile)
    capture = await adapter.capture(request)
    payload = json.loads(capture.captured_payload_json)

    assert payload == {
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
    assert capture.source_published_at.date().isoformat() == profile.publication_date
    assert adapter.capture_calls == transport.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"status_code": 404}, "boundary"),
        ({"credentials_used": True}, "boundary"),
        ({"effective_uri": OPENAI_GPT_56_PROFILE.source_uri + "?copy=1"}, "boundary"),
        (
            {"response_body": _body(OPENAI_GPT_56_PROFILE, publisher="Other")},
            "publisher",
        ),
        (
            {"response_body": _body(OPENAI_GPT_56_PROFILE, source_text="GPT-5.6 only")},
            "required source marker",
        ),
        (
            {
                "response_body": _body(OPENAI_GPT_56_PROFILE)[:-1]
                + ',"publisher":"OpenAI"}'
            },
            "JSON object",
        ),
    ],
)
async def test_reviewed_publication_adapter_fails_closed(changes, message) -> None:
    adapter, _, request = _adapter_and_request(**changes)
    with pytest.raises(ReviewedAIPublicationSourceAdapterError, match=message):
        await adapter.capture(request)
