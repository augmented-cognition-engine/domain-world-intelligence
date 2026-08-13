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
never imports `core.engine` internals. Core invokes the executor with
`IntelligenceBuildHostServices`: a product-scoped durable record store and a
Core-owned resource-page port with a separate `observe_read` authority. The
adapter writes the reviewed Builder artifacts to that durable store and never
manufactures a read grant or an in-memory-only result page.

The distribution registers `WorldAIBuilderExecutor` only through the dedicated
`ace.intelligence_builders` entry-point group. It declares the one exact
`intelligence_onboarding_profile:world-ai-command-center` profile. Core discovers
the executor without treating the inert Domain Pack as executable code. The
adapter binds the exact recorded source identities and citations shipped by the
World repository to the authenticated product and actor supplied by Core. A
fresh executor and fresh resource service can reopen the same append-only
Builder session from the host store. The recorded proof does not claim capture-
time freshness, a live connector, external publication, or autonomous action.

The temporary `ace-core>=0.8.2` lower bound permits candidate-wheel integration
before Core assigns the release version; importing and discovering this adapter
additionally requires the public Builder request and durable executor/host-
services registry merged on Core main at
`0948db68af3f3915132baed35b40549e305a35ea`. Tighten the lower bound to the
released Core version before publishing this distribution.
