# ACE World Federal Register source adapter

This separately versioned package implements the public ACE source-adapter contract for one
reviewed Federal Register API document. It is executable host software, not Domain Pack content,
and it has no ACE extension entry point.

The adapter contains no network client. A host must inject a reviewed transport that performs one
credential-free request to the exact configured HTTPS URI, denies redirects, bounds the response,
validates every resolved and connected address as globally routable throughout the request, and
prevents DNS rebinding. The host must also bind the installed adapter artifact digest into the
governed activation.

The adapter emits inert canonical JSON for document `2026-16197`. It preserves the Federal Register
page and the corresponding `govinfo.gov` PDF. FederalRegister.gov is an informational service and
not the official legal edition; the govinfo PDF is retained as the official-format verification
reference. The adapter does not decide what the document means, create Signals, Shifts or Briefs,
publish anything, or grant authority.

## License

Apache-2.0 under the repository [`LICENSE`](../../LICENSE) and [`NOTICE`](../../NOTICE).
