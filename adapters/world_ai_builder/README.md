# ACE World AI Builder adapter

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

The distribution registers the authority-neutral `WorldAIBuilderPlanner` through
`ace.intelligence_build_planners` and the separately authorized
`WorldAIBuilderExecutor` through `ace.intelligence_builders`. Both declare the one exact
`intelligence_onboarding_profile:world-ai-command-center` profile. Core discovers
the executor without treating the inert Domain Pack as executable code. The
adapter binds the exact recorded source identities and citations shipped by the
World repository to the authenticated product and actor supplied by Core. A
fresh executor and fresh resource service can reopen the same append-only
Builder session from the host store. The recorded proof does not claim capture-
time freshness, a live connector, external publication, or autonomous action.

The `ace-core>=0.9` lower bound requires the public authority-neutral v1alpha3
planning/binding contract. Planning exposes exact reviewed recorded materials
and requested requirements but does not resolve capabilities, grants, or approval.
