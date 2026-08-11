from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from ace_world_federal_register_source import (
    FEDERAL_REGISTER_DOCUMENT_URI,
    FEDERAL_REGISTER_LOCATOR,
    FEDERAL_REGISTER_SOURCE_TYPE,
    FederalRegisterNetworkTransportError,
    FederalRegisterRetrievalRequest,
    OptInFederalRegisterNetworkTransport,
)


class _Response:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self._body = body
        self._headers = {key.lower(): value for key, value in (headers or {}).items()}

    def getheader(self, name: str):
        return self._headers.get(name.lower())

    def read(self, amount: int) -> bytes:
        return self._body[:amount]


class _Connection:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.requests: list[tuple[str, str, dict[str, str]]] = []
        self.closed = False

    def request(self, method: str, path: str, *, headers: dict[str, str]) -> None:
        self.requests.append((method, path, headers))

    def getresponse(self) -> _Response:
        return self.response

    def close(self) -> None:
        self.closed = True


def _request(*, max_response_chars: int = 32_768) -> FederalRegisterRetrievalRequest:
    return FederalRegisterRetrievalRequest(
        source_type_ref=FEDERAL_REGISTER_SOURCE_TYPE,
        requested_uri=FEDERAL_REGISTER_DOCUMENT_URI,
        max_response_chars=max_response_chars,
    )


def _body() -> bytes:
    return json.dumps({"document_number": "2026-16197"}).encode()


def test_transport_requires_explicit_opt_in() -> None:
    with pytest.raises(
        FederalRegisterNetworkTransportError,
        match="explicit enabled=True",
    ):
        OptInFederalRegisterNetworkTransport(enabled=False)


def test_transport_requires_an_exact_reviewed_federal_register_endpoint() -> None:
    with pytest.raises(FederalRegisterNetworkTransportError, match="authorized_uri"):
        OptInFederalRegisterNetworkTransport(
            enabled=True,
            authorized_uri="https://example.com/api/v1/documents/2026-11415.json",
        )
    with pytest.raises(FederalRegisterNetworkTransportError, match="JSON pointer"):
        OptInFederalRegisterNetworkTransport(enabled=True, locator="document_number")


@pytest.mark.asyncio
async def test_transport_pins_public_address_and_sends_no_credentials() -> None:
    response = _Response(
        _body(),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(_body())),
        },
    )
    connection = _Connection(response)
    factory_calls: list[tuple[str, str, float]] = []

    def factory(host: str, address: str, timeout: float):
        factory_calls.append((host, address, timeout))
        return connection

    times = iter(
        [
            datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
            datetime(2026, 8, 10, 12, 0, 1, tzinfo=UTC),
        ]
    )
    transport = OptInFederalRegisterNetworkTransport(
        enabled=True,
        resolver=lambda host, port: ("8.8.8.8", "1.1.1.1"),
        connection_factory=factory,
        clock=lambda: next(times),
    )

    result = await transport.retrieve(_request())

    assert factory_calls == [("www.federalregister.gov", "1.1.1.1", 15.0)]
    assert result.resolved_ip_addresses == ("1.1.1.1",)
    assert result.connected_ip_addresses == ("1.1.1.1",)
    assert result.locator == FEDERAL_REGISTER_LOCATOR
    assert result.dns_rebinding_protection_applied is True
    assert result.credentials_used is False
    assert connection.requests == [
        (
            "GET",
            "/api/v1/documents/2026-16197.json",
            {
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "Connection": "close",
                "User-Agent": "ACE-World-Intelligence/0.9 public-source-capture",
            },
        )
    ]
    assert connection.closed is True


@pytest.mark.asyncio
async def test_transport_rejects_private_resolution_before_connection() -> None:
    factory_calls: list[object] = []
    transport = OptInFederalRegisterNetworkTransport(
        enabled=True,
        resolver=lambda host, port: ("8.8.8.8", "127.0.0.1"),
        connection_factory=lambda *args: factory_calls.append(args),
    )
    with pytest.raises(FederalRegisterNetworkTransportError, match="non-public"):
        await transport.retrieve(_request())
    assert factory_calls == []
    assert transport.calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (_Response(b"x" * 17), "bounded byte limit"),
        (
            _Response(b"{}", headers={"Content-Encoding": "gzip"}),
            "identity encoding",
        ),
        (_Response(b"\xff"), "strict UTF-8"),
    ],
)
async def test_transport_fails_closed_on_ambiguous_material(
    response: _Response,
    message: str,
) -> None:
    connection = _Connection(response)
    transport = OptInFederalRegisterNetworkTransport(
        enabled=True,
        resolver=lambda host, port: ("1.1.1.1",),
        connection_factory=lambda host, address, timeout: connection,
        clock=lambda: datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
    )
    with pytest.raises(FederalRegisterNetworkTransportError, match=message):
        await transport.retrieve(_request(max_response_chars=4))
    assert connection.closed is True


@pytest.mark.asyncio
async def test_transport_rejects_policy_drift_before_dns() -> None:
    calls: list[object] = []
    transport = OptInFederalRegisterNetworkTransport(
        enabled=True,
        resolver=lambda *args: calls.append(args),
    )
    request = _request()
    drifted = FederalRegisterRetrievalRequest(
        source_type_ref=request.source_type_ref,
        requested_uri=request.requested_uri,
        max_response_chars=request.max_response_chars,
        credentials_allowed=True,
    )
    with pytest.raises(FederalRegisterNetworkTransportError, match="security policy"):
        await transport.retrieve(drifted)
    assert calls == []


@pytest.mark.asyncio
async def test_transport_reuses_security_boundary_for_another_exact_document() -> None:
    ai_uri = "https://www.federalregister.gov/api/v1/documents/2026-11415.json"
    connection = _Connection(_Response(b"{}", headers={"Content-Type": "application/json"}))
    transport = OptInFederalRegisterNetworkTransport(
        enabled=True,
        authorized_uri=ai_uri,
        source_type_ref="federal_register_ai_policy_document",
        locator="json-pointer:/document_number",
        resolver=lambda host, port: ("1.1.1.1",),
        connection_factory=lambda host, address, timeout: connection,
        clock=lambda: datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
    )
    result = await transport.retrieve(
        FederalRegisterRetrievalRequest(
            source_type_ref="federal_register_ai_policy_document",
            requested_uri=ai_uri,
            max_response_chars=32_768,
        )
    )
    assert result.requested_uri == result.effective_uri == ai_uri
    assert connection.requests[0][1] == "/api/v1/documents/2026-11415.json"
