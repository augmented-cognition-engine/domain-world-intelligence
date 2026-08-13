# Atrium AI Command Center demo v1

Atrium is the ACE command center. World Intelligence supplies the configured
AI topic, ontology, source definitions, transition detector, synthesis policy,
personas, and admitted evidence. It does not ship a competing dashboard.

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
claims. The `demo` metadata preserves the current boundaries: recorded transport,
no network-freshness claim, and no autonomous publication.

## Demo journey

1. Open Atrium oriented to `World AI Command Center`.
2. See source coverage and the current cited Reality Brief.
3. Inspect the detected policy progression and exact evidence lineage.
4. Ask ACE a question and receive only answers supported by the visible resource plane.
5. Open a downstream investigation without allowing the domain to act autonomously.

## Next increment

Add an admitted monitor/subscription plus onboarding-agent records so the same
screen can demonstrate `Connect -> Map -> Watch -> Brief` from an empty install.
Then replace recorded captures with an opt-in refresh while retaining the frozen
page as a deterministic fallback.
