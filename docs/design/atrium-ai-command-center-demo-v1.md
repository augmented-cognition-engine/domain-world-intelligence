# Atrium AI Command Center demo v1

Atrium is the ACE command center. World Intelligence supplies the configured
AI topic, ontology, source definitions, transition detector, synthesis policy,
personas, and admitted evidence. It does not ship a competing dashboard.

The flagship topic is artificial intelligence because it changes quickly and
crosses product, economic, security, policy, capital, and adoption decisions.
The v1 source portfolio therefore organizes onboarding around six watch areas:

1. models and capabilities;
2. economics and pricing;
3. safety and security;
4. policy and regulation;
5. capital and company moves; and
6. adoption and executive signals.

The portfolio is declarative and reviewed. Its `connected` sources describe
implemented source definitions. Its `proposed` sources are onboarding choices,
not evidence, connections, corroboration, or freshness claims. Atrium counts
only captures admitted through the governed resource plane.

The first demonstrable resource page uses the accepted two-lineage AI policy
journey:

`Federal Register + White House -> Observation -> Shift -> Signal -> Case -> cited Brief`

Generate the exact Atrium input with public ACE Core 0.8:

```bash
uv sync
uv pip install --no-deps "ace-core==0.8.0"
uv run --no-sync python -m scripts.atrium_ai_command_center_demo
```

The explicit Core replacement is temporary: released World 0.10.0 still pins
Core 0.6. The active compatibility packet will remove this extra step.

The resulting `artifacts/atrium-demo/world-ai-resource-page.json` is the public
Intelligence resource-plane page Atrium consumes. It contains no new UI-specific
claims. It now includes one real owner-scoped Monitor and one record-only
Subscription over the activated AI policy detector. The `demo` metadata preserves
the current boundaries: recorded transport, no network-freshness claim, and no
autonomous publication.

## Demo journey

1. Open Atrium oriented to `World AI Command Center`.
2. See the six-area coverage model, two admitted source roots, and one active watch.
3. Inspect the detected policy progression and exact evidence lineage.
4. Ask ACE a question and receive only answers supported by the visible resource plane.
5. Open a downstream investigation without allowing the domain to act autonomously.

## Next increment

Admit the onboarding-agent records so the same screen can demonstrate
`Connect -> Map -> Watch -> Brief` from an empty install. Add one governed primary
connection in each remaining watch area, then replace recorded captures with an
opt-in refresh while retaining the frozen page as a deterministic fallback.
