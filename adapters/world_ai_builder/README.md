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
stable HTTP request/result. The adapter consumes `AuthorizedIntelligenceBuild`
through Core's public `ace.application.intelligence_build_execution` contract; it
never imports `core.engine` internals. A trusted host supplies a `WorldAIRecordedContextProvider`
that binds the already-admitted recorded evidence and a separate `observe_read`
authority for the returned resource page.

The distribution registers `WorldAIBuilderExecutor` only through the dedicated
`ace.intelligence_builders` entry-point group. It declares the one exact
`intelligence_onboarding_profile:world-ai-command-center` profile. Core discovers
the executor without treating the inert Domain Pack as executable code. The
application host still supplies the trusted recorded context; absent that host
binding the executor fails closed before admitting evidence.

The temporary `ace-core>=0.8.2` lower bound permits candidate-wheel integration
before Core assigns the release version; importing and discovering this adapter
additionally requires the public build contract from Core PR #154 and the dedicated
registry from Core PR #159. Tighten the lower bound to the released Core version
before publishing this distribution.
