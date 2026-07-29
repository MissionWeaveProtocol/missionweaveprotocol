# Registry Identifier Validation Design

**Status:** Approved design; awaiting written-spec review

**Task revision:** `MW-V1-2026-07-29-R1`

**Date:** 2026-07-29

## Decision summary

MissionWeaveProtocol will own negative cryptography evaluations for malformed identifiers in
complete Registry evidence. The protocol reference validator and every SDK must validate the
Registry `organizationId`, every binding `keyId`, and every binding `principal.id` as absolute RFC
3986 URIs before selecting `signature.keyId`.

The protocol's test-only Registry fixture Schema will validate bounded JSON structure, not URI
semantics. This allows deliberately malformed identifier fixtures to reach signed-document
verification stage 4. Runtime verification remains responsible for the normative identifier rule.

Python, TypeScript, Go, and Rust require runtime fixes. Java and C++ already apply the required
validation before key selection and should require only bundle synchronization unless the new
evaluations expose a regression. All six SDKs will vendor and pin the same updated bundle.

## Evidence baseline

The current protocol specification requires every identifier to be an absolute RFC 3986 URI and
requires complete Organization-scoped Registry evidence to be validated before key selection.
Fresh probes against current checkouts established this behavior:

| Implementation | Non-URI `organizationId` | Selected Agent Card service `principal.id` | Unrelated `principal.id` | Unrelated `keyId` |
| --- | --- | --- | --- | --- |
| Protocol reference validator | Accepted behind fixture prevalidation | Accepted behind fixture prevalidation | Accepted behind fixture prevalidation | Accepted behind fixture prevalidation |
| Python | Accepted | Accepted | Accepted | Accepted |
| TypeScript | Accepted | Accepted | Accepted | Accepted |
| Go | Accepted | Accepted | Accepted | Accepted |
| Rust | Accepted | Accepted | Accepted | Accepted |
| Java | Rejected at key resolution | Rejected at key resolution | Rejected at key resolution | Rejected at key resolution |
| C++ | Rejected at key resolution | Rejected at key resolution | Rejected at key resolution | Rejected at key resolution |

The existing Registry fixture Schema requires URI-form identifiers. Cryptography runners validate
fixtures against that Schema before calling the codec, so malformed identifiers cannot currently
exercise the runtime stage-4 path. This is a coverage defect in addition to the four runtime
defects in Python, TypeScript, Go, and Rust, and it also hides the protocol reference validator's
equivalent omission.

## Requirements

1. Registry identifier validation must use the protocol's existing absolute RFC 3986 URI rules:
   visible ASCII only, an absolute scheme, complete-string consumption, valid URI grammar, and
   valid percent escapes.
2. `example:` and other valid absolute URIs with an empty hierarchical part must remain valid.
3. Implementations must not normalize identifiers. Comparisons remain byte-for-byte.
4. Runtime validation must not inherit the fixture Schema's 512-character test-artifact bound; the
   protocol does not define that bound for deployed Registry evidence.
5. The complete Registry must be validated before unknown-key handling, signer matching, or any
   other selection-dependent decision. An invalid unrelated binding must fail verification.
6. Each malformed Registry identifier must fail at `key-resolution` with wire code
   `AUTH_INVALID_SIGNATURE`. Protected diagnostics may identify the invalid field and reason.
7. All SDKs must execute the same protocol-owned cryptography evaluations and pin the same protocol
   commit and artifact digest.

## Non-goals

This slice does not standardize a deployed Registry wire artifact, transport, freshness proof,
authorization proof, or cryptographic completeness proof. It does not implement First-Admission
Records, historical-trust validation, Command freshness, signer authorization, Mission lifecycle
state machines, or the larger V1 behavioral conformance bundle. Those remain subsequent V1 work.

This slice also does not add identifier normalization, a new public identifier type, or a new wire
error code.

## Protocol bundle design

### Registry fixture contract

`cryptography/registry-fixture.schema.json` will remain a test-only structure contract. Its three
identifier locations will reference a renamed structural definition, `$defs.identifierCandidate`,
with these constraints:

- JSON string;
- at least one character;
- at most 512 characters for bounded test artifacts;
- no `format: uri` assertion and no absolute-URI pattern.

The cryptography README will state explicitly that fixture validation proves shape and bounds only.
Identifier validity belongs to stage 4 and must be evaluated by the codec. This change does not
weaken any normative durable-object Schema.

### Negative evaluations

Four generated Registry fixtures will be added to the existing
`reject.key-resolution.matrix` case. Each fixture changes exactly one field from a valid Registry:

| Fault ID | Signed profile | Mutated location | Invalid class | Expected result |
| --- | --- | --- | --- | --- |
| `registry-organization-id-relative-reference` | Command | `organizationId` | Relative reference such as `organizations/acme` | `key-resolution` / `AUTH_INVALID_SIGNATURE` |
| `registry-selected-service-principal-id-iri-only` | Agent Card | Selected Organization Registry service `principal.id` | Raw non-ASCII IRI spelling | `key-resolution` / `AUTH_INVALID_SIGNATURE` |
| `registry-unrelated-principal-id-malformed-percent` | Command | Unselected binding `principal.id` | Malformed percent escape such as `%GG` | `key-resolution` / `AUTH_INVALID_SIGNATURE` |
| `registry-unrelated-key-id-trailing-line-feed` | Command | Unselected binding `keyId` | Otherwise absolute identifier with a trailing line feed | `key-resolution` / `AUTH_INVALID_SIGNATURE` |

The Agent Card evaluation is necessary because its stage-4 signer rule requires a service
Principal but does not compare that Principal's ID with a signed-document field. It therefore
isolates selected-Principal URI validation instead of failing incidentally on signer mismatch.

No new case family or signed document is required. The deterministic bundle totals become:

- 22 cases;
- 62 evaluations;
- 12 complete and 50 rejected evaluations;
- 24 key-resolution evaluations;
- 98 digest-protected artifacts.

Generation, validation, README counts, manifest digest, and every count assertion must move
together.

### Protocol reference validator

The protocol validator will expose one internal absolute-identifier predicate used both by schema
format handling and stage-4 Registry parsing. It will combine:

1. non-empty visible-ASCII validation;
2. an absolute RFC 3986 scheme prefix;
3. the standards URI-format checker;
4. explicit complete-string and percent-escape checks where the underlying checker is permissive.

`_resolve_key` will call this predicate for the root `organizationId`, each `keyId`, and each
Principal `id` while scanning all bindings. No binding may enter uniqueness indexes or selection
until its identifiers are valid.

## SDK design

### Python

`schema_formats.py` will provide one internal `is_protocol_uri` predicate shared by SchemaCatalog
and signed-document verification. It will strengthen the current format check with explicit
visible-ASCII and whole-string rules, including rejection of a trailing line feed. `_resolve_key`
and Principal parsing will apply it to all three Registry identifier locations before uniqueness
or selection logic.

### TypeScript

The existing RFC 3986 predicate in `schema-catalog.ts` will move to an internal module that is not
re-exported from the package entry point. SchemaCatalog and `signed-document-codec.ts` will share
that predicate. Snapshot parsing and binding normalization will reject invalid identifiers before
building uniqueness maps.

### Go

`schema.go` will own a package-private `isProtocolURI` predicate. It will use one immutable,
lazily compiled JSON Schema validator containing the same URI syntax assertions used by the
normative schemas, excluding their durable-object `maxLength`, rather than relying on `net/url`
alone. Registry parsing will validate the root identifier and every binding identifier before
indexing or selection.

### Rust

`schema.rs` will own a crate-private `is_protocol_uri` predicate backed by one lazily constructed
`jsonschema` validator plus explicit visible-ASCII and absolute-scheme checks, without applying a
durable-object length limit. The Registry parser will use it for all three identifier locations
before indexing or selection.

### Java and C++

No runtime change is planned. Both implementations already share their protocol URI predicate with
Registry parsing and validate all bindings before selection. They will ingest the new bundle and
run the new evaluations. A runtime change is permitted only if that evidence reveals a concrete
failure.

### Bundle synchronization

After the protocol bundle commit exists, Python, TypeScript, Go, Rust, Java, and C++ will all:

- vendor the updated cryptography assets;
- update `PROTOCOL_PIN.json` to the new protocol commit;
- update cryptography source commit, artifact digest, artifact count, and evaluation count;
- update generated embedded assets and hard-coded count assertions;
- update localized documentation wherever bundle counts or pin links are stated.

Schema and structural-conformance digests remain unchanged unless deterministic generation proves
otherwise. The cryptography digest must change.

## Verification data flow

For each signed-document verification, the required order is:

1. parse and validate the signed document;
2. validate the signature envelope;
3. obtain explicitly Organization-wide Registry evidence;
4. strictly parse the Registry;
5. validate the root identifier and every binding's identifiers, shape, key material, timestamps,
   retained history, and Organization-wide uniqueness invariants;
6. only then select `signature.keyId` and apply signer and validity rules;
7. canonicalize and verify the signature.

Fixture-schema validation belongs to bundle preflight and is not a substitute for step 5.

## Error handling

All four new failures are authentication failures at stage 4. Public callers receive the existing
generic `AUTH_INVALID_SIGNATURE` wire behavior. Protected diagnostics should name the location,
for example `Registry bindings[3].principal.id is not a protocol URI`, without exposing Registry
contents or changing public error types.

The implementation must fail on the first invalid field encountered by the deterministic complete
scan. Tests must not depend on a particular binding index unless the fixture generator owns and
asserts that ordering.

## TDD and verification strategy

Implementation will follow a protocol-first RED/GREEN sequence:

1. Add the four generated fixtures and evaluations, loosen only the test fixture Schema, and update
   protocol count assertions. The protocol reference runner must fail until stage-4 URI validation
   is implemented.
2. Implement the protocol reference predicate and make deterministic generation plus all protocol
   validators pass.
3. Synchronize the new bundle into one affected SDK at a time. Each SDK must first demonstrate RED
   on the new protocol-owned evaluations, then add focused local URI-edge tests and the runtime fix.
4. Synchronize Java and C++ and demonstrate that the new evaluations pass without speculative code
   changes.
5. Run full repository checks, package/install smoke tests, and independent Spec and Standards
   reviews before publication.

Focused local tests in each affected SDK will cover all three identifier positions and at least:

- relative references;
- invalid or missing schemes;
- trailing whitespace or control characters;
- raw non-ASCII IRI spellings;
- malformed percent escapes and invalid authority syntax;
- valid empty-hier-part URIs such as `example:`;
- long valid identifiers, proving no accidental 512-character runtime limit.

The protocol repository must pass policy, protocol validation, cryptography validation, and a
second deterministic regeneration with no diff. Each SDK must pass its complete native test,
format, lint/static-analysis, documentation, bundle-integrity, packaging, installed-consumer, and
CLI checks. Java completion requires exact-commit CI evidence if a local JDK remains unavailable.

## Delivery sequence

1. Land the protocol bundle and reference-validator change.
2. Land runtime fixes and bundle pins for Python, TypeScript, Go, and Rust.
3. Land bundle-only compatibility updates for Java and C++, unless their new evaluations require a
   bounded runtime correction.
4. Verify that all six SDK pins identify the same protocol commit and cryptography digest.
5. Record cross-language evidence in the protocol issue or release tracking artifact.
6. Continue with the next V1 behavioral-contract subproject only after this slice is complete.

## Acceptance criteria

This slice is complete only when all of the following are true:

- the protocol manifest owns and validates the four negative Registry-identifier evaluations;
- the protocol reference validator rejects all four at `key-resolution` with
  `AUTH_INVALID_SIGNATURE`;
- Python, TypeScript, Go, and Rust reject all four through their public codec verification paths;
- Java and C++ pass the same evaluations through their public codec verification paths;
- every implementation validates unrelated bindings before key selection;
- all six SDKs execute 62 evaluations with 12 complete and 50 rejected;
- all six SDKs pin the same protocol commit, cryptography digest, artifact count, and evaluation
  count;
- complete repository and package-consumer verification passes with no unreported skips or stale
  generated assets;
- independent Spec and Standards reviews find no unresolved issue.
