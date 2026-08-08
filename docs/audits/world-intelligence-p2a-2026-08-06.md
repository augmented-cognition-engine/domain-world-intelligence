# World Intelligence P2A compiler audit

**Date:** 2026-08-06  
**Result:** passed for the inert pack and unchanged-compiler falsification slice  
**Not claimed:** event/claim runtime semantics, LIVE sources, delivery, external action, or political analysis

## Outcome

The first independently packaged World Intelligence Domain Pack compiles through the existing ACE
Core + Intelligence `v1alpha1` pack compiler without a platform schema or implementation change.
The pack is JSON-only. It declares World vocabulary and policy while ACE retains all generic
compiler, graph, detector, routing, synthesis, authority, persistence, and replay machinery.

## Exact pack

- Pack: `world_intelligence` version `0.1.0`
- Compiled Pack: `pack_ir:683de57a71669814e507d07d65a109db`
- Pack digest: `sha256:683de57a71669814e507d07d65a109db49abfd2f2d800d89c5faa281bccdbfb1`
- Modules: ontology, source mapping, numeric detection, personas/routing, ordered synthesis
- Entity types: `9`
- Relation types: `11`
- Personas: general reader and public researcher
- Brief: `reality_change_brief`
- Epistemic statuses: observed, attributed claim, corroborated, disputed, inferred, unknown, scenario

The alpha detection contract currently exposes numeric deltas only. P2A therefore declares one
factual `public_indicator_change` rule. Categorical, semantic, and structural strategies are
explicitly deferred generic gaps; the World pack does not hide private detector code or encode
claim truth as a numeric score.

## Negative boundary

Five mutations fail closed:

1. imperative control flow in the manifest;
2. an unresolved relation endpoint;
3. a source mapping targeting an undeclared `truth_score` attribute;
4. a private categorical-detector field outside the public contract; and
5. an executable Python source adapter embedded in the pack.

## Verification

| Check | Result |
|---|---:|
| World P2A conformance suite | 7 passed |
| Acceptance and test lint | passed |
| Pack compilation through unchanged ACE | passed |
| Installed World wheel with ACE and Market | passed |

Artifact pins:

- ACE Core `ace_core-0.3.0-py3-none-any.whl`:
  `49214a347ce4d4e9d8aa65aca430f3278b2d8079dfaa7c9cba9edfc7fdfeabb5`
- Market `ace_ext_b2b_marketing-0.1.0-py3-none-any.whl`:
  `3ea4af28dce17207ff9151d4e5b346033b4561f2595ca6374db64137c6ed786a`
- World `ace_ext_world_intelligence-0.1.0-py3-none-any.whl`:
  `38b5d8baccae41bdd31affeb496e890bb4c9d37540ac5024db934cc2d69a5f99`
- Installed probe environment: `/private/tmp/ace-p1f-probe-final`

The isolated probe loaded Market and World resources from installed wheels and compiled both
through one installed ACE distribution. It reproduced Market
`pack_ir:19de6d59b28095f7bd7600364c3b4de7` and World
`pack_ir:683de57a71669814e507d07d65a109db` without either pack importing the other. The final World
wheel contains only the inert manifest, five JSON modules, four JSON conformance artifacts, and
package metadata—no tests or executable adapter code.

## Next gate

P2B adds the hermetic 72-hour public-issue scenario. It must model event state, attributed claims,
source derivation families, contradiction, correction, inference, unknowns, and watchpoints using
public ACE contracts. Any required generic contract change must first be documented as a
falsification finding and preserve Market compatibility.
