# World Intelligence 0.10.0 measured-intelligence release work packet (v1)

**Status:** bounded release candidate; does not itself prove public installation or close ACE Core issue #38

**Date:** 2026-08-11

## Objective

Publish one independently versioned, inert World Intelligence Domain Pack that reproduces ACE
Core 0.6.0's domain-neutral measured-impact boundary through the public-data journey:

```text
Observation → Shift → Signal → Brief → Decision → reviewed Action
  → observed Outcome → governed feedback
```

The packet succeeds only if the exact public Core and World artifacts reproduce the frozen World
results without importing either repository checkout at runtime.

## Frozen source identities

- Core release tag: `v0.6.0`, commit `1e383e1e265e59290478eef6483c2565a0d3dbbc`.
- World release base: merged `main` commit `b6571a7595063c7c3db93bd35daff91d06a2b1fa`.
- Intended root distribution: `ace-domain-world-intelligence==0.10.0` with
  `ace-core>=0.6.0,<0.7`.
- Separate source-adapter distribution: `ace-ext-world-federal-register-source==0.3.0` under the
  same Core window. It is not part of the root wheel or its dependency closure.

The final release commit, tag, archive hashes, workflow runs, registry upload times, and clean
installation belong in a later immutable released-artifact record.

## Ownership boundary

- Core continues to own durable identity, immutable records, authority, Decisions, Actions,
  Outcomes, and append-only evaluation/proposal receipts.
- Intelligence continues to own domain-neutral Observation, Shift, Signal, Brief, Case, monitor,
  criteria, matching, classification, and feedback machinery.
- World owns public-issue nouns, reviewed source profiles, source mapping, materiality, scoring
  policy, frozen controls, fixtures, and product evidence.
- The root distribution remains JSON-only and inert. Executable source adapters remain separately
  packaged host software and gain no extension entry point or implicit install path.

## Acceptance

1. The root wheel contains exactly the declared Domain Pack JSON resources and no executable code,
   adapter package, tests, entry point, or install hook.
2. The root package and separate adapter declare the exact Core 0.6 compatibility window; the
   locked environment resolves public `ace-core==0.6.0` without a Git or path override.
3. The complete World and source-adapter suites pass, including P2C3–P2C10 and the convergence
   projection, from Python 3.12.
4. Root wheel and source archive build reproducibly at the final source epoch and pass strict
   metadata inspection.
5. A clean environment installs only the public Core and World root artifacts, resolves pack data
   from `site-packages`, and leaves the optional World source adapter absent.
6. A second public-artifact harness may install explicitly attached, independently packaged action
   and source adapters to replay the recorded World journey. Neither adapter becomes a root runtime
   dependency.
7. Exact useful classifications remain bounded to their declared criteria. The explicit rejection
   disposition preserves evaluation history, applies no proposal, and changes no effective head.

## Exclusions and non-claims

This packet does not claim causal effect, general human benefit, population calibration, live
network freshness, continuous monitoring, autonomous publication, political persuasion, automatic
promotion, distributed exactly-once effects, or untrusted-code isolation. Recorded official-source
transport proves exact reviewed material, not current network state. NASA and ESA remain separate
claimant publication roots, not proven independent measurements.

## Rollback and deletion criteria

Before publication, a failed identity, dependency, package-content, replay, or public-install gate
blocks the tag. After publication, immutable artifacts are not replaced silently: a material defect
requires an explicit follow-up release and a public limitation record. This work packet may be
deleted only if the 0.10.0 release line is abandoned before publication; point-in-time evidence is
otherwise retained.
