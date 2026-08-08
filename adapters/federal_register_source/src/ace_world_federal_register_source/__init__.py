"""Public API for the World Intelligence Federal Register source adapter."""

from .adapter import (
    ADAPTER_CAPABILITY,
    ADAPTER_CONTRACT,
    ADAPTER_IMPLEMENTATION_ID,
    ADAPTER_IMPLEMENTATION_VERSION,
    DOCUMENT_NUMBER,
    FEDERAL_REGISTER_DOCUMENT_URI,
    FEDERAL_REGISTER_LOCATOR,
    FEDERAL_REGISTER_SOURCE_TYPE,
    OFFICIAL_PDF_URI,
    FederalRegisterRetrievalRequest,
    FederalRegisterRetrievalResult,
    FederalRegisterSourceAdapter,
    FederalRegisterSourceAdapterError,
    FederalRegisterTransport,
)

__all__ = [
    "ADAPTER_CAPABILITY",
    "ADAPTER_CONTRACT",
    "ADAPTER_IMPLEMENTATION_ID",
    "ADAPTER_IMPLEMENTATION_VERSION",
    "DOCUMENT_NUMBER",
    "FEDERAL_REGISTER_DOCUMENT_URI",
    "FEDERAL_REGISTER_LOCATOR",
    "FEDERAL_REGISTER_SOURCE_TYPE",
    "OFFICIAL_PDF_URI",
    "FederalRegisterRetrievalRequest",
    "FederalRegisterRetrievalResult",
    "FederalRegisterSourceAdapter",
    "FederalRegisterSourceAdapterError",
    "FederalRegisterTransport",
]
