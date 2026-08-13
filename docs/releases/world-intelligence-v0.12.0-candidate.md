# World Intelligence 0.12.0 AI onboarding release candidate

Status: **candidate — World review, CI, and public-index gates pending**

## Promise

World Intelligence 0.12.0 is the installable Artificial Intelligence experience for ACE's generic
Intelligence Catalog. A person can choose World Intelligence, start with a decision-oriented AI
question, review grouped source choices, and continue through the existing governed Builder flow.

## Coordinates

- source base: World main merge `d2cf648b5b87abfb388bcd506459854aa538811b`;
- release branch: `codex/v0.12.0-ai-onboarding-release`;
- candidate distribution: `ace-domain-world-intelligence==0.12.0`;
- required Core line: `ace-core>=0.8.2,<0.9`;
- exact public Core release: [`v0.8.2`](https://github.com/augmented-cognition-engine/core/releases/tag/v0.8.2), clean-installed from PyPI;
- latest published predecessor: World 0.11.0 with Core 0.8.1.

## Included change

- domain label: World Intelligence;
- flagship topic: Artificial intelligence;
- three starter questions for executive orientation, risk/opportunity, and emerging advantage;
- six evidence groups containing 32 exact source IDs;
- owned/private evidence is opt-in;
- every profile source ID resolves to the existing World AI source catalog.

## Acceptance before publication

- Core 0.8.2 exists on the public index and installs without a checkout;
- the frozen World lock contains no Core Git or path override;
- the complete root, adapter, release-contract, package, and reproducible-build gates pass;
- an isolated install admits the 0.12.0 profile through Core 0.8.2's unchanged resource plane;
- profile selection grants no connection, monitoring, activation, effect, or publication authority.

## Candidate verification

- the frozen lock resolves public `ace-core==0.8.2` with no Git or path override;
- the complete source suite passes with `141 passed, 1 skipped` in an isolated Python 3.12 environment;
- both root artifacts build and pass strict Twine metadata validation;
- final immutable hashes and checkout-free World installation remain publication closeout gates.

## Boundaries

This candidate does not claim live refresh, source independence merely from publisher count,
neutrality by averaging, autonomous fact checking, arbitrary web access, general causal accuracy,
or general beneficial impact. Recorded transports remain labeled and proposed sources remain
non-evidence until separately admitted.
