# Atrium AI Command Center demo v1

Atrium is the ACE command center. World Intelligence supplies the configured
AI topic, ontology, source definitions, transition detector, synthesis policy,
personas, and admitted evidence. It does not ship a competing dashboard.

The flagship topic is artificial intelligence because it changes quickly and
crosses product, economic, security, policy, capital, and adoption decisions.
The source universe organizes onboarding around twelve watch areas:

1. models and capabilities;
2. benchmarks and independent evaluations;
3. economics and pricing;
4. reliability and platform health;
5. open ecosystem and research;
6. safety, security, and incidents;
7. policy, regulation, and governance;
8. capital and company moves;
9. compute, chips, and infrastructure;
10. talent, patents, and research;
11. adoption, procurement, and outcomes; and
12. narratives, executives, and public attention.

The companion
[`onboarding_profile.json`](../../domain_packs/world_intelligence_ai/onboarding_profile.json)
keeps first use outcome-led. It asks whether the user needs to choose AI, set strategy, track the
frontier, manage risk, understand competition, or build a custom picture; then recommends a bounded
subset of these watch areas, intelligence products, and cadence. The profile is declarative and
non-authorizing. It does not connect a source or activate a monitor.

The portfolio is declarative and reviewed. Its `connected` sources describe
implemented source definitions. Its `proposed` sources are onboarding choices,
not evidence, connections, corroboration, or freshness claims. Atrium counts
only captures admitted through the governed resource plane.

## What makes the demonstration intelligence

The experience should not ask leaders to read more feeds. It should combine
otherwise separate evidence into decision-relevant shifts:

- capability-per-dollar frontier movement;
- provider claims versus independent evaluation and observed reliability;
- research-to-product diffusion;
- capital-to-capability conversion;
- compute, energy, and grid bottlenecks;
- policy announcement versus implementation and procurement;
- strategy visible in hiring, patents, grants, permits, and spending before announcement;
- executive commitments versus later funding, delivery, revision, or abandonment; and
- adoption growth versus trust, safety, reliability, and measured outcomes.

The first demonstrable resource page uses the accepted two-lineage AI policy
journey:

`Federal Register + White House -> Observation -> Shift -> Signal -> Case -> cited Brief`

Generate the exact Atrium input from the paired Core and World candidate checkouts:

```bash
export CORE=/path/to/ace-core
PYTHONPATH="$PWD:$CORE" uv run python -m scripts.atrium_ai_command_center_demo
```

Released World 0.10.0 still pins Core 0.6, while the new profile/session projection is stacked on
the current Core checkout. Installed-artifact reproduction remains a landing gate; this source
command is not a public package compatibility claim.

The resulting `artifacts/atrium-demo/world-ai-resource-page.json` is the public
Intelligence resource-plane page Atrium consumes. It contains no new UI-specific
claims. It now includes one real owner-scoped Monitor and one record-only
Subscription over the activated AI policy detector. The `demo` metadata preserves
the current boundaries: recorded transport, no network-freshness claim, and no
autonomous publication.

## Demo journey

1. Choose an AI decision context and accept or edit ACE's recommended watch system.
2. Review the public evidence roles, proposed connections, concepts, watches, and cadence before
   activation.
3. See the onboarding agents assemble one inspectable `Connect -> Map -> Watch -> Brief` story.
4. Open Atrium oriented to `World AI Command Center` with the first cited briefing already present.
5. See the twelve-area coverage model, two admitted source roots, and one active watch.
6. Inspect the detected policy progression and exact evidence lineage.
7. Ask ACE a question and receive only answers supported by the visible resource plane.
8. Open a downstream investigation without allowing the domain to act autonomously.

## Candidate live Builder trace

The candidate now projects the declarative profile through Core's non-authorizing presentation
contract and runs the public Builder services through eight durable revisions:

`goal selected -> sources connecting -> sources ready -> concepts proposed -> concepts approved -> watches proposed -> watches approved -> first Brief ready`

World owns the registered recorded-source provider plus the concept, watch, and briefing
strategies. Core owns session identity, exact artifact handoffs, approval resolution, persistence,
replay, and the resource projection. The two source samples point to the same already-admitted
Federal Register and White House source snapshots used by the Reality Brief. The Briefing Agent
states that these first-party lineages support different evidence roles and do not independently
establish downstream outcomes.

Next, reproduce the paired candidates from installed wheels, add one governed primary connection
in each remaining watch area, and replace recorded captures with opt-in refresh while retaining the
frozen page as a deterministic fallback.
