# ACE World AI Builder executor

This separately packaged, trusted application adapter translates Core's generic,
already-authorized Intelligence build request into the recorded World AI Command
Center journey. It is executable Python by design and is therefore **not** part
of the inert `ace-domain-world-intelligence` Domain Pack.

The adapter accepts only the AI Command Center onboarding profile, the exact
reviewed `official_records` source group, supported outcome lenses, and declared
cadences. It runs no network capture, claims no network freshness, and does not
turn proposed catalog sources into admitted evidence.

Core still owns authentication, build authority, persistence primitives, and the
stable HTTP request/result. The adapter consumes that authorized material through
the structural, domain-neutral `AuthorizedIntelligenceBuildPort`; it never imports
`core.engine` internals. A trusted host supplies a `WorldAIRecordedContextProvider`
that binds the already-admitted recorded evidence and a separate `observe_read`
authority for the returned resource page.

The current Core candidate exposes the executor protocol but not an installed
executor registry. Until that domain-neutral registry lands, a host must construct
`WorldAIBuilderExecutor` explicitly and inject it into `IntelligenceBuildHttpRuntime`.
This distribution deliberately declares no `ace.extensions` entry point that
current Core would silently ignore or mis-register.

The temporary `ace-core>=0.8.2` lower bound permits candidate-wheel integration
before Core assigns the release version; importing this adapter additionally
requires the `AuthorizedIntelligenceBuild` API introduced by Core PR #154. Tighten
the lower bound to the released Core version before publishing this distribution.
