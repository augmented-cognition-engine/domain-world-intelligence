# ACE World Federal Register source adapter

This separately versioned package implements the public ACE source-adapter contract for exact
reviewed AI Command Center sources: Federal Register API documents and one White House official
release. It is executable host software, not Domain Pack content, and it has no ACE extension entry
point.

Version 0.2.0 adds an explicitly enabled network transport for the one reviewed URI. It performs a
direct TLS connection to a validated public address, preserves hostname certificate validation,
does not consult ambient proxies or credential stores, follows no redirects, requests identity
encoding, and bounds the response before the adapter validates it. Construction requires
`enabled=True`; the default test and conformance path remains recorded and network-free. The host
must still bind the installed adapter artifact digest into the governed activation.

The adapter emits inert canonical JSON for document `2026-16197`. It preserves the Federal Register
page and the corresponding `govinfo.gov` PDF. FederalRegister.gov is an informational service and
not the official legal edition; the govinfo PDF is retained as the official-format verification
reference. The adapter does not decide what the document means, create Signals, Shifts or Briefs,
publish anything, or grant authority.

A successful network retrieval proves source acquisition at that moment. It does not by itself
prove governed ACE admission, interpretation, or downstream intelligence.

The package also contains a separately identified, exact White House HTML adapter for the
2026-07-14 GOLD EAGLE implementation release. It accepts only the reviewed canonical URI, title,
publication date, and implementation statements, emits inert canonical JSON, and has its own
artifact identity. Its accepted command-center conformance transport is recorded and network-free;
no White House network transport is enabled by this package. The source is a publication lineage
independent of the Federal Register API record, but it is not independent non-government
corroboration.

P2D adds exact recorded-transport profiles for two NASA and two ESA planetary-defense pages about
asteroid 2024 YR4. The adapter accepts only the four reviewed canonical URIs, titles, publication
dates, claimant types, target date, and probability statements. Decimal estimates remain exact text
at the capture boundary and are converted to numeric attributes only by the inert source-mapping
declaration. These profiles have no enabled network transport. NASA and ESA are separate official
claimant publication roots; the connector does not claim their underlying observations or models
are independent.

## License

Apache-2.0 under the repository [`LICENSE`](../../LICENSE) and [`NOTICE`](../../NOTICE).
