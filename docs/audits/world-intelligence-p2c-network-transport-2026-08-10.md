# World Intelligence P2C opt-in network transport audit — 2026-08-10

## Accepted boundary

The Federal Register source package now contains an explicit opt-in transport for its one exact
reviewed API URI. The transport performs no model call and creates no ACE intelligence resource.
It owns only credential-free source retrieval and returns the pre-existing inert retrieval-result
contract to the separately reviewed adapter.

Security properties exercised in the 31-test connector suite:

- construction fails unless the caller supplies `enabled=True`;
- the exact HTTPS hostname, URI, source type, and request policy are revalidated;
- every DNS candidate must be a globally routable address before any connection is attempted;
- the selected address is connected directly while TLS verifies the reviewed hostname;
- ambient proxy, cookie, netrc, and credential discovery are not used;
- redirects are not followed, identity encoding is requested, and bytes, characters, time, and
  content decoding are bounded;
- the selected resolved and connected address, credential posture, and DNS-rebinding posture are
  returned as transport attestations for adapter validation.

## External retrieval observation

One retrieval completed on 2026-08-10 America/Los_Angeles (2026-08-11 UTC):

| Field | Observed value |
|---|---|
| URI | `https://www.federalregister.gov/api/v1/documents/2026-16197.json` |
| HTTP / media type | `200` / `application/json` |
| Body | 4,227 characters |
| Body SHA-256 | `62e5f5da8f712542926093e897366cb49916afd92c4233e12d2a791581cf6571` |
| Selected public address | `75.2.36.59` |
| Credentials used | `false` |
| DNS-rebinding protection | `true` |

The current external body digest is observation evidence, not a permanent source identity. A later
capture is expected to differ if the publisher changes its response.

## Verification

- Federal Register adapter and transport suite: **31 passed**.
- Complete World Intelligence conformance suite: **81 passed**.
- Ruff over the connector source and new test: **passed**.
- Diff whitespace validation: **passed** before this audit record was appended and must be rerun at
  final closeout.

## Honest limit

This closes only the separately reviewed network-transport implementation and one acquisition
observation. The frozen P2C governed admission still uses its recorded response so identities remain
deterministic. No claim is made that the external retrieval was admitted through ACE, independently
corroborated, interpreted, converted into a Signal or Shift, added to a Case, synthesized into a
Brief, or used for a legal conclusion or external action.

Next is an AI command-center topic pack with two independent official-source lineages. That packet
must distinguish a new development from republication and preserve conflicting statements rather
than averaging them away.
