"""Explicitly enabled, credential-free HTTPS transport for the reviewed source.

The source adapter remains the validator and canonicalizer.  This module owns only
the network boundary: public-address resolution, a pinned direct TLS connection,
bounded retrieval, and transport attestation.  It deliberately does not consult
ambient proxy settings, cookie jars, netrc files, or credential stores.
"""

from __future__ import annotations

import asyncio
import http.client
import socket
import ssl
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from urllib.parse import urlsplit

from ace.core import validate_public_ip_literal

from ace_world_federal_register_source.adapter import (
    FEDERAL_REGISTER_DOCUMENT_URI,
    FEDERAL_REGISTER_LOCATOR,
    FEDERAL_REGISTER_SOURCE_TYPE,
    FederalRegisterRetrievalRequest,
    FederalRegisterRetrievalResult,
)

DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_TIMEOUT_SECONDS = 30.0
USER_AGENT = "ACE-World-Intelligence/0.9 public-source-capture"


class FederalRegisterNetworkTransportError(RuntimeError):
    """The opt-in transport could not produce a bounded exact retrieval."""


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to one validated IP while preserving hostname TLS verification."""

    def __init__(self, host: str, address: str, *, timeout: float) -> None:
        super().__init__(
            host,
            port=443,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._address = address

    def connect(self) -> None:
        raw = socket.create_connection((self._address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


ConnectionFactory = Callable[[str, str, float], http.client.HTTPSConnection]
Resolver = Callable[[str, int], Sequence[str]]
Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _resolve_public_addresses(host: str, port: int) -> tuple[str, ...]:
    values = socket.getaddrinfo(
        host,
        port,
        family=socket.AF_UNSPEC,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    addresses = sorted({str(item[4][0]) for item in values})
    if not addresses:
        raise FederalRegisterNetworkTransportError("DNS returned no addresses")
    try:
        return tuple(
            validate_public_ip_literal(address, name="resolved_ip_address")
            for address in addresses
        )
    except ValueError as exc:
        raise FederalRegisterNetworkTransportError(
            "DNS returned a non-public or otherwise prohibited address"
        ) from exc


def _connection(host: str, address: str, timeout: float) -> http.client.HTTPSConnection:
    return _PinnedHTTPSConnection(host, address, timeout=timeout)


class OptInFederalRegisterNetworkTransport:
    """Retrieve the one reviewed Federal Register URI through a direct pinned socket.

    ``enabled=True`` must be supplied by the caller for every constructed transport.
    This is intentionally not controlled by a permissive global default.
    """

    def __init__(
        self,
        *,
        enabled: bool,
        authorized_uri: str = FEDERAL_REGISTER_DOCUMENT_URI,
        source_type_ref: str = FEDERAL_REGISTER_SOURCE_TYPE,
        locator: str = FEDERAL_REGISTER_LOCATOR,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        resolver: Resolver = _resolve_public_addresses,
        connection_factory: ConnectionFactory = _connection,
        clock: Clock = _utc_now,
    ) -> None:
        if type(enabled) is not bool or enabled is not True:
            raise FederalRegisterNetworkTransportError(
                "public network capture requires explicit enabled=True opt-in"
            )
        if (
            type(timeout_seconds) not in {int, float}
            or isinstance(timeout_seconds, bool)
            or not 0 < float(timeout_seconds) <= MAX_TIMEOUT_SECONDS
        ):
            raise FederalRegisterNetworkTransportError(
                f"timeout_seconds must be greater than zero and at most {MAX_TIMEOUT_SECONDS:g}"
            )
        parsed = urlsplit(authorized_uri)
        if (
            type(authorized_uri) is not str
            or parsed.scheme != "https"
            or parsed.hostname != "www.federalregister.gov"
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or not parsed.path.startswith("/api/v1/documents/")
            or not parsed.path.endswith(".json")
        ):
            raise FederalRegisterNetworkTransportError(
                "authorized_uri must be one exact credential-free Federal Register API document"
            )
        if type(source_type_ref) is not str or not source_type_ref:
            raise FederalRegisterNetworkTransportError(
                "source_type_ref must be non-empty text"
            )
        if type(locator) is not str or not locator.startswith("json-pointer:/"):
            raise FederalRegisterNetworkTransportError(
                "locator must be one explicit JSON pointer"
            )
        self._authorized_uri = authorized_uri
        self._source_type_ref = source_type_ref
        self._locator = locator
        self._timeout = float(timeout_seconds)
        self._resolver = resolver
        self._connection_factory = connection_factory
        self._clock = clock
        self.calls = 0

    async def retrieve(
        self,
        request: FederalRegisterRetrievalRequest,
    ) -> FederalRegisterRetrievalResult:
        return await asyncio.to_thread(self._retrieve, request)

    def _retrieve(
        self,
        request: FederalRegisterRetrievalRequest,
    ) -> FederalRegisterRetrievalResult:
        if type(request) is not FederalRegisterRetrievalRequest:
            raise FederalRegisterNetworkTransportError(
                "network transport requires the exact retrieval request contract"
            )
        if (
            request.source_type_ref != self._source_type_ref
            or request.requested_uri != self._authorized_uri
            or request.credentials_allowed is not False
            or request.redirects_allowed is not False
            or request.public_network_only is not True
            or request.dns_rebinding_protection_required is not True
        ):
            raise FederalRegisterNetworkTransportError(
                "network request crossed the reviewed source or security policy"
            )
        if (
            type(request.max_response_chars) is not int
            or not 1 <= request.max_response_chars <= 32_768
        ):
            raise FederalRegisterNetworkTransportError(
                "max_response_chars crossed the reviewed 1..32768 bound"
            )

        parsed = urlsplit(request.requested_uri)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "www.federalregister.gov"
            or parsed.port is not None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise FederalRegisterNetworkTransportError(
                "reviewed source URI must remain exact credential-free HTTPS"
            )
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        addresses = tuple(self._resolver(parsed.hostname, 443))
        if not addresses:
            raise FederalRegisterNetworkTransportError("DNS returned no addresses")
        try:
            validated = tuple(
                validate_public_ip_literal(address, name="resolved_ip_address")
                for address in addresses
            )
        except ValueError as exc:
            raise FederalRegisterNetworkTransportError(
                "DNS returned a non-public or otherwise prohibited address"
            ) from exc
        if len(set(validated)) != len(validated):
            raise FederalRegisterNetworkTransportError("DNS returned duplicate addresses")

        self.calls += 1
        errors: list[str] = []
        for address in sorted(validated):
            connection = self._connection_factory(parsed.hostname, address, self._timeout)
            try:
                observed_at = self._clock()
                connection.request(
                    "GET",
                    path,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "identity",
                        "Connection": "close",
                        "User-Agent": USER_AGENT,
                    },
                )
                response = connection.getresponse()
                content_encoding = (
                    response.getheader("Content-Encoding") or "identity"
                ).lower()
                if content_encoding not in {"", "identity"}:
                    raise FederalRegisterNetworkTransportError(
                        "compressed response crossed the bounded identity encoding policy"
                    )
                maximum_bytes = request.max_response_chars * 4
                content_length = response.getheader("Content-Length")
                if content_length is not None:
                    try:
                        declared_length = int(content_length)
                    except ValueError as exc:
                        raise FederalRegisterNetworkTransportError(
                            "response Content-Length was not an integer"
                        ) from exc
                    if declared_length < 0 or declared_length > maximum_bytes:
                        raise FederalRegisterNetworkTransportError(
                            "response exceeded the bounded byte limit"
                        )
                body_bytes = response.read(maximum_bytes + 1)
                if len(body_bytes) > maximum_bytes:
                    raise FederalRegisterNetworkTransportError(
                        "response exceeded the bounded byte limit"
                    )
                try:
                    body = body_bytes.decode("utf-8", errors="strict")
                except UnicodeDecodeError as exc:
                    raise FederalRegisterNetworkTransportError(
                        "response was not strict UTF-8"
                    ) from exc
                if len(body) > request.max_response_chars:
                    raise FederalRegisterNetworkTransportError(
                        "response exceeded the bounded character limit"
                    )
                captured_at = self._clock()
                media_type = (
                    (response.getheader("Content-Type") or "")
                    .split(";", 1)[0]
                    .strip()
                    .lower()
                )
                return FederalRegisterRetrievalResult(
                    source_type_ref=request.source_type_ref,
                    requested_uri=request.requested_uri,
                    effective_uri=request.requested_uri,
                    status_code=response.status,
                    media_type=media_type,
                    response_body=body,
                    redirect_chain=(),
                    # The transport validates every DNS candidate, selects one,
                    # connects directly to it, and attests only that selected path.
                    resolved_ip_addresses=(address,),
                    connected_ip_addresses=(address,),
                    dns_rebinding_protection_applied=True,
                    credentials_used=False,
                    locator=self._locator,
                    observed_at=observed_at,
                    captured_at=captured_at,
                )
            except (
                OSError,
                http.client.HTTPException,
                FederalRegisterNetworkTransportError,
            ) as exc:
                errors.append(f"{address}: {exc}")
            finally:
                connection.close()
        summary = ", ".join(errors) if errors else "no connection attempt completed"
        raise FederalRegisterNetworkTransportError(
            f"all validated public source addresses failed: {summary}"
        )


__all__ = [
    "FederalRegisterNetworkTransportError",
    "OptInFederalRegisterNetworkTransport",
]
