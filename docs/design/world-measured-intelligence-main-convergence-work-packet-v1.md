# World measured-intelligence main-convergence work packet (v1)

**Status:** bounded direct-to-main integration candidate. This packet does not merge or close any
existing stacked pull request, publish World or Core, close ACE Core issue
[#38](https://github.com/augmented-cognition-engine/core/issues/38), pass SI4, or complete ACE
0.6.0.

**Frozen base:** World `main` commit `8de1027c4c995582b42c4a1f936a72e2c42878a0`, including the
LIVE AI Command Center lineage proof from World PR #14.

**Executable candidate:** World commit `87625d55c717a9c649d4f44a06d1767b52fed255` with Core
measured-impact commit `433e3d16c5458c975557dcd1552824fb959d4d12`.

## Objective

Reproduce the P2C3-P2C10 measured-intelligence stack and its artifact-convergence packet directly
on live World `main` without rewriting or merging the existing review branches. The result must
show that the newly landed AI Command Center lineage proof and the measured-feedback journey can
coexist under the same Domain Pack boundary and release gates.

## Method and acceptance

The packet must:

1. replay the thirteen existing candidate commits onto an isolated branch from exact live `main`;
2. preserve both sides of the one documentation overlap and encounter no code conflict;
3. use the repository-locked formatter for inherited live-main files and prove no expected outcome
   or public identity changed;
4. rebuild the exact World and Federal Register source-adapter wheels twice with a fixed source
   epoch and require byte-identical wheel output;
5. install exact Core, action-adapter, source-adapter, and World wheels in a fresh Python 3.12
   environment outside every declared Core checkout;
6. reproduce the canonical P2C10 result byte-for-byte from two fresh workspace roots;
7. run the combined AI Command Center plus P2C3-P2C10 focused checks, the complete World suite,
   adapter suite, release contract, Ruff, formatting, and whitespace gates; and
8. retain proposal-only authority and every prior claim limitation.

## Ownership and exclusions

World continues to own source translation, BLS/FCC/AI-policy fixtures, product rules, controls, and
the canonical artifact. Core owns durable identities, provenance, authority, Decision, Action,
Outcome, and append-only replay. Intelligence owns only domain-neutral evaluation and proposal
machinery.

This packet adds no Core or Intelligence contract, domain noun, network acquisition, proposal
application, package version, schema, CLI, MCP tool, publication authority, or release claim. It
does not establish causality, live-monitoring performance, statistical validity, population
benefit, general source independence, or human benefit.

## Owned files and rollback

- the isolated direct-main branch and its mechanically replayed history;
- eight locked-format live-main files in one explicit hygiene commit;
- `artifacts/measured-intelligence/convergence-v1.json` regenerated from the exact new source;
- this work packet and its point-in-time audit; and
- restrained README and roadmap references.

Rollback closes the direct-main draft and removes its additive audit references. The original
stacked drafts remain unchanged and recoverable. No released artifact or durable ACE history is
rewritten.

## External release gates

Core issue #49 F1, F3, and F5 remain open 0.6 release gates. This World integration packet does not
implement, waive, defer, resolve, or re-date them. Final merged-source Core verification, version
decisions, final artifact hashes, public-index installation, and publication also remain outside
this packet.
