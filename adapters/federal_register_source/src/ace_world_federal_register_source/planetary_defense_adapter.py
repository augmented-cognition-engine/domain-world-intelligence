"""Exact read-only adapters for frozen NASA and ESA planetary-defense pages."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol

from ace.core import CapabilityArtifactIdentityV1Alpha1, canonical_json, validate_exact_https_uri
from ace.intelligence import CapturedSourceMaterialV1Alpha1, SourceAdapterCaptureRequestV1Alpha1

from .adapter import ADAPTER_CAPABILITY, ADAPTER_CONTRACT, _aware_utc, _validated_addresses

NASA_PLANETARY_DEFENSE_IMPLEMENTATION_ID = "world_nasa_planetary_defense_source"
ESA_PLANETARY_DEFENCE_IMPLEMENTATION_ID = "world_esa_planetary_defence_source"
PLANETARY_DEFENSE_IMPLEMENTATION_VERSION = "0.1.0"
NASA_PLANETARY_DEFENSE_SOURCE_TYPE = "nasa_planetary_defense_publication"
ESA_PLANETARY_DEFENCE_SOURCE_TYPE = "esa_planetary_defence_publication"
PLANETARY_DEFENSE_LOCATOR = "css:article"
PLANETARY_DEFENSE_OBJECT = "2024 YR4"
PLANETARY_DEFENSE_TARGET_DATE = "2032-12-22"
MAX_RESPONSE_BODY_CHARS = 512_000

NASA_INITIAL_URI = (
    "https://science.nasa.gov/blogs/planetary-defense/2025/02/07/"
    "nasa-continues-to-monitor-orbit-of-near-earth-asteroid-2024-yr4/"
)
NASA_INITIAL_TITLE = "NASA Continues to Monitor Orbit of Near-Earth Asteroid 2024 YR4"
NASA_REVISED_URI = (
    "https://science.nasa.gov/blogs/planetary-defense/2025/02/24/"
    "latest-calculations-conclude-asteroid-2024-yr4-now-poses-no-significant-"
    "threat-to-earth-in-2032-and-beyond/"
)
NASA_REVISED_TITLE = (
    "Latest Calculations Conclude Asteroid 2024 YR4 Now Poses No Significant Threat to Earth in 2032 and Beyond"
)
ESA_INITIAL_URI = (
    "https://blogs.esa.int/rocketscience/2025/02/06/2024-yr4-flyby-geometry-or-1-8-of-what/comment-page-1/"
)
ESA_INITIAL_TITLE = "2024 YR4 flyby geometry, or 1.8% of What?"
ESA_REVISED_URI = "https://www.esa.int/ESA_Multimedia/Images/2025/02/Asteroid_2024_YR4_impact_risk_rises_and_falls"
ESA_REVISED_TITLE = "Asteroid 2024 YR4 impact risk rises and falls"


class PlanetaryDefenseSourceAdapterError(ValueError):
    """An official planetary-defense retrieval crossed its reviewed scope."""


@dataclass(frozen=True, slots=True)
class PlanetaryDefensePublicationProfile:
    source_type_ref: str
    requested_uri: str
    title: str
    publication_date: str
    claimant_org: str
    claimant_office: str
    probability_percent: float
    estimate_status: str
    source_lineage_id: str
    predecessor_lineage_id: str
    assessment_note: str
    required_statements: tuple[str, ...]


NASA_INITIAL_PROFILE = PlanetaryDefensePublicationProfile(
    source_type_ref=NASA_PLANETARY_DEFENSE_SOURCE_TYPE,
    requested_uri=NASA_INITIAL_URI,
    title=NASA_INITIAL_TITLE,
    publication_date="2025-02-07",
    claimant_org="NASA",
    claimant_office="Planetary Defense Coordination Office / JPL Center for Near-Earth Object Studies",
    probability_percent=2.3,
    estimate_status="earlier_estimate",
    source_lineage_id="nasa_pdco:2024_yr4:2025-02-07",
    predecessor_lineage_id="none",
    assessment_note=(
        "NASA reported a 2.3% Earth-impact probability for 22 December 2032 and said the "
        "estimate could change as observations accumulated."
    ),
    required_statements=("2.3%", "Dec. 22, 2032", "impact probability"),
)
NASA_REVISED_PROFILE = PlanetaryDefensePublicationProfile(
    source_type_ref=NASA_PLANETARY_DEFENSE_SOURCE_TYPE,
    requested_uri=NASA_REVISED_URI,
    title=NASA_REVISED_TITLE,
    publication_date="2025-02-24",
    claimant_org="NASA",
    claimant_office="Planetary Defense Coordination Office / JPL Center for Near-Earth Object Studies",
    probability_percent=0.004,
    estimate_status="revised_estimate",
    source_lineage_id="nasa_pdco:2024_yr4:2025-02-24",
    predecessor_lineage_id=NASA_INITIAL_PROFILE.source_lineage_id,
    assessment_note=(
        "NASA reported an updated 0.004% Earth-impact probability for 22 December 2032 and "
        "no significant impact potential for the next century."
    ),
    required_statements=("0.004%", "Dec. 22, 2032", "no significant potential"),
)
ESA_INITIAL_PROFILE = PlanetaryDefensePublicationProfile(
    source_type_ref=ESA_PLANETARY_DEFENCE_SOURCE_TYPE,
    requested_uri=ESA_INITIAL_URI,
    title=ESA_INITIAL_TITLE,
    publication_date="2025-02-06",
    claimant_org="ESA",
    claimant_office="Planetary Defence Office",
    probability_percent=1.8,
    estimate_status="earlier_estimate",
    source_lineage_id="esa_pdo:2024_yr4:2025-02-06",
    predecessor_lineage_id="none",
    assessment_note=(
        "ESA reported a 1.8% Earth-impact risk for 22 December 2032 and expected the numerical "
        "value to evolve with additional observations."
    ),
    required_statements=("1.8%", "22 December 2032", "expected to evolve"),
)
ESA_REVISED_PROFILE = PlanetaryDefensePublicationProfile(
    source_type_ref=ESA_PLANETARY_DEFENCE_SOURCE_TYPE,
    requested_uri=ESA_REVISED_URI,
    title=ESA_REVISED_TITLE,
    publication_date="2025-02-25",
    claimant_org="ESA",
    claimant_office="Planetary Defence Office",
    probability_percent=0.001,
    estimate_status="revised_estimate",
    source_lineage_id="esa_pdo:2024_yr4:2025-02-25",
    predecessor_lineage_id=ESA_INITIAL_PROFILE.source_lineage_id,
    assessment_note=(
        "ESA reported a 0.001% Earth-impact risk for 22 December 2032, down from estimates "
        "published during the preceding days."
    ),
    required_statements=("0.001%", "22 December 2032", "down from"),
)

NASA_PLANETARY_DEFENSE_PROFILES = (NASA_INITIAL_PROFILE, NASA_REVISED_PROFILE)
ESA_PLANETARY_DEFENCE_PROFILES = (ESA_INITIAL_PROFILE, ESA_REVISED_PROFILE)


@dataclass(frozen=True, slots=True)
class PlanetaryDefenseRetrievalRequest:
    source_type_ref: str
    requested_uri: str
    max_response_chars: int
    credentials_allowed: bool = False
    redirects_allowed: bool = False
    public_network_only: bool = True
    dns_rebinding_protection_required: bool = True


@dataclass(frozen=True, slots=True)
class PlanetaryDefenseRetrievalResult:
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


class PlanetaryDefenseTransport(Protocol):
    async def retrieve(
        self,
        request: PlanetaryDefenseRetrievalRequest,
    ) -> PlanetaryDefenseRetrievalResult: ...


def _fail(message: str) -> PlanetaryDefenseSourceAdapterError:
    return PlanetaryDefenseSourceAdapterError(message)


class _PublicationHTML(HTMLParser):
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
                    raise _fail(f"duplicate reviewed planetary-defense metadata: {key}")
                self.metadata[key] = content
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            if self.canonical_uri is not None:
                raise _fail("duplicate reviewed planetary-defense canonical URI")
            self.canonical_uri = values.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "template", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            normalized = " ".join(data.split())
            if normalized:
                self.visible.append(normalized)


def _canonical_publication_payload(
    response_body: object,
    *,
    profile: PlanetaryDefensePublicationProfile,
    max_chars: int,
) -> str:
    if type(response_body) is not str:
        raise _fail("planetary-defense response body must be text")
    if not response_body or len(response_body) > max_chars:
        raise _fail("planetary-defense response body exceeded its exact character bound")
    parser = _PublicationHTML()
    try:
        parser.feed(response_body)
        parser.close()
    except PlanetaryDefenseSourceAdapterError:
        raise
    except (TypeError, ValueError) as exc:
        raise _fail("planetary-defense response is not bounded parseable HTML") from exc
    if parser.metadata.get("og:title") != profile.title:
        raise _fail("planetary-defense title crossed the exact reviewed publication scope")
    published = parser.metadata.get("article:published_time", "")
    if not published.startswith(profile.publication_date):
        raise _fail("planetary-defense publication date crossed the exact reviewed scope")
    if parser.canonical_uri != profile.requested_uri:
        raise _fail("planetary-defense canonical URI crossed the exact reviewed scope")
    validate_exact_https_uri(parser.canonical_uri, name="canonical_uri")
    visible = " ".join(parser.visible)
    if any(statement not in visible for statement in profile.required_statements):
        raise _fail("planetary-defense page omitted an exact reviewed estimate statement")
    return canonical_json(
        {
            "assessment_note": profile.assessment_note,
            "assessment_subject": "earth_impact_probability",
            "claimant_office": profile.claimant_office,
            "claimant_org": profile.claimant_org,
            "estimate_status": profile.estimate_status,
            "impact_probability_percent": format(profile.probability_percent, "g"),
            "object_name": PLANETARY_DEFENSE_OBJECT,
            "predecessor_lineage_id": profile.predecessor_lineage_id,
            "publication_date": profile.publication_date,
            "source_lineage_id": profile.source_lineage_id,
            "source_uri": profile.requested_uri,
            "target_date": PLANETARY_DEFENSE_TARGET_DATE,
        }
    )


class PlanetaryDefenseSourceAdapter:
    """Validate one agency's exact reviewed publications and emit inert JSON."""

    def __init__(
        self,
        *,
        transport: PlanetaryDefenseTransport,
        artifact_digest: str,
        source_type_ref: str,
    ) -> None:
        if source_type_ref == NASA_PLANETARY_DEFENSE_SOURCE_TYPE:
            implementation_id = NASA_PLANETARY_DEFENSE_IMPLEMENTATION_ID
            profiles = NASA_PLANETARY_DEFENSE_PROFILES
        elif source_type_ref == ESA_PLANETARY_DEFENCE_SOURCE_TYPE:
            implementation_id = ESA_PLANETARY_DEFENCE_IMPLEMENTATION_ID
            profiles = ESA_PLANETARY_DEFENCE_PROFILES
        else:
            raise _fail("unsupported planetary-defense source type")
        self.source_type_ref = source_type_ref
        self.profiles = {profile.requested_uri: profile for profile in profiles}
        self._transport = transport
        self.artifact_identity = CapabilityArtifactIdentityV1Alpha1(
            capability=ADAPTER_CAPABILITY,
            contract=ADAPTER_CONTRACT,
            implementation_id=implementation_id,
            implementation_version=PLANETARY_DEFENSE_IMPLEMENTATION_VERSION,
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
        if validated.source_type_ref != self.source_type_ref:
            raise _fail("source-adapter request names a different claimant source type")
        profile = self.profiles.get(validated.requested_uri)
        if profile is None:
            raise _fail("source-adapter request crossed the exact reviewed URI set")
        validate_exact_https_uri(validated.requested_uri, name="requested_uri")

        transport_request = PlanetaryDefenseRetrievalRequest(
            source_type_ref=validated.source_type_ref,
            requested_uri=validated.requested_uri,
            max_response_chars=min(validated.max_payload_chars, MAX_RESPONSE_BODY_CHARS),
        )
        self.capture_calls += 1
        result = await self._transport.retrieve(transport_request)
        if type(result) is not PlanetaryDefenseRetrievalResult:
            raise _fail("transport returned an unsupported planetary-defense result type")
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
            raise _fail("planetary-defense retrieval scalar fields must use exact string types")
        if type(result.status_code) is not int:
            raise _fail("planetary-defense status_code must use the exact integer type")
        if type(result.redirect_chain) is not tuple or result.redirect_chain != ():
            raise _fail("planetary-defense redirect_chain must be exactly an empty tuple")
        if type(result.credentials_used) is not bool or result.credentials_used is not False:
            raise _fail("planetary-defense retrieval must attest exact false credentials_used")
        if (
            type(result.dns_rebinding_protection_applied) is not bool
            or result.dns_rebinding_protection_applied is not True
        ):
            raise _fail("planetary-defense retrieval must attest exact true DNS-rebinding protection")
        if (
            result.source_type_ref != self.source_type_ref
            or result.requested_uri != profile.requested_uri
            or result.effective_uri != profile.requested_uri
        ):
            raise _fail("planetary-defense retrieval crossed source type or exact URI scope")
        if result.locator != PLANETARY_DEFENSE_LOCATOR:
            raise _fail("planetary-defense retrieval does not bind the exact article locator")
        if result.status_code != 200 or result.media_type != "text/html":
            raise _fail("planetary-defense retrieval must be exact HTTP 200 text/html material")
        try:
            resolved = _validated_addresses(result.resolved_ip_addresses, name="resolved_ip_addresses")
            connected = _validated_addresses(result.connected_ip_addresses, name="connected_ip_addresses")
            observed_at = _aware_utc(result.observed_at, name="observed_at")
            captured_at = _aware_utc(result.captured_at, name="captured_at")
        except ValueError as exc:
            raise _fail(str(exc)) from exc
        if connected != resolved:
            raise _fail("every resolved and connected planetary-defense address must remain exactly attested")
        if observed_at < validated.started_at or captured_at < observed_at:
            raise _fail("planetary-defense observation/capture times fall outside the exact operation")

        payload_json = _canonical_publication_payload(
            result.response_body,
            profile=profile,
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
            captured_payload_digest="sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
            locator=PLANETARY_DEFENSE_LOCATOR,
            source_published_at=datetime.fromisoformat(profile.publication_date).replace(tzinfo=UTC),
            event_effective_at=None,
            observed_at=observed_at,
            captured_at=captured_at,
        )


__all__ = [
    "ESA_INITIAL_PROFILE",
    "ESA_INITIAL_TITLE",
    "ESA_INITIAL_URI",
    "ESA_PLANETARY_DEFENCE_IMPLEMENTATION_ID",
    "ESA_PLANETARY_DEFENCE_PROFILES",
    "ESA_PLANETARY_DEFENCE_SOURCE_TYPE",
    "ESA_REVISED_PROFILE",
    "ESA_REVISED_TITLE",
    "ESA_REVISED_URI",
    "NASA_INITIAL_PROFILE",
    "NASA_INITIAL_TITLE",
    "NASA_INITIAL_URI",
    "NASA_PLANETARY_DEFENSE_IMPLEMENTATION_ID",
    "NASA_PLANETARY_DEFENSE_PROFILES",
    "NASA_PLANETARY_DEFENSE_SOURCE_TYPE",
    "NASA_REVISED_PROFILE",
    "NASA_REVISED_TITLE",
    "NASA_REVISED_URI",
    "PLANETARY_DEFENSE_IMPLEMENTATION_VERSION",
    "PLANETARY_DEFENSE_LOCATOR",
    "PLANETARY_DEFENSE_OBJECT",
    "PLANETARY_DEFENSE_TARGET_DATE",
    "PlanetaryDefensePublicationProfile",
    "PlanetaryDefenseRetrievalRequest",
    "PlanetaryDefenseRetrievalResult",
    "PlanetaryDefenseSourceAdapter",
    "PlanetaryDefenseSourceAdapterError",
    "PlanetaryDefenseTransport",
]
