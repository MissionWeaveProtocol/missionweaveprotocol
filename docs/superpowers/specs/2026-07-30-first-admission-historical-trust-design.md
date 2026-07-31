# First-Admission and Historical-Trust Design

**Status:** Approved design; awaiting written-spec review

**Task revision:** `MW-V1-2026-07-30-R1`

**Date:** 2026-07-30

## Decision summary

MissionWeaveProtocol will define a normative `FirstAdmissionRecord` JSON object and a separate
Admission layer above the existing six-stage Signed Document Verification Profile. The record will
bind one cryptographically verified document to its Organization-assigned trusted acceptance time,
resolved signing key, bound Principal, document kind, and authenticated accepting service.

The protocol will standardize the record fields and validation semantics, but it will not
standardize a database, transport, record signature, Merkle proof, or transparency-log protocol.
An Organization-provided Admission Log adapter remains the trusted deployment seam for accepting-
service authentication, authoritative absence, atomic append-or-return-existing behavior, and
append-only integrity. The SDK must still validate every returned record's normative Schema and
content; adapter trust never bypasses record validation.

First admission and historical replay remain separate from the six cryptographic stages. Existing
cryptographic verification APIs and the 62-evaluation cryptography bundle retain their current
meaning. A successful admission returns separate admission evidence. Command freshness and signer
authorization remain later V1 behavioral-contract slices.

## Context

Section 6.4 already distinguishes cryptographic verification from Organization admission:

- the six stages produce a signing hash and resolved Principal without requiring admission state;
- a First-Admission Record is authoritative metadata outside the Signed Document;
- first admission must validate the trusted acceptance time against the same key validity interval;
- historical replay must rerun all six stages and validate the existing record;
- later key expiry or revocation does not invalidate a historical signature whose protected signed
  time and trusted acceptance time were both valid; and
- admission failures are externally indistinguishable as `AUTH_INVALID_SIGNATURE`.

The current protocol has no normative First-Admission Record Schema, portable conformance bundle,
or cross-language Admission API. Every SDK stops after the six-stage result. That leaves the
backdating and historical-trust rules as prose without executable cross-language evidence.

## Requirements

1. Add one normative First-Admission Record schema without turning the record into a Signed
   Document or self-authenticating trust anchor.
2. Preserve the existing six cryptographic stages and their error classification.
3. Keep cryptographic verification usable independently from admission.
4. On first admission, require the trusted acceptance time to lie within the same effective key
   validity interval used by the verified binding.
5. Consider first admission complete only after an authenticated Admission Log successfully commits
   or returns an already committed compatible record.
6. Make retries idempotent under the logical key `(organizationId, signingHash)`.
7. On historical replay, rerun all six cryptographic stages before consulting the admission record.
8. Require the record's Organization, document kind, signing hash, key ID, and Principal to match
   the newly verified evidence exactly.
9. Preserve timestamp text and compare timestamp values as exact instants under the protocol
   timestamp profile; do not normalize the Signed Document or record before hashing or comparison.
10. Fail closed when the log is unavailable, cannot authenticate the accepting service, cannot
    establish authoritative absence, or cannot establish append-only integrity.
11. Map every admission failure to diagnostic stage `admission` and wire code
    `AUTH_INVALID_SIGNATURE`, while retaining a specific protected reason.
12. Make every SDK execute the same protocol-owned Admission evaluations and pin the same protocol
    commit and Admission artifact digest.

## Non-goals

This slice does not:

- define a database, Group-log implementation, Registry-log implementation, network transport, or
  replication protocol;
- standardize a signature envelope, Merkle inclusion proof, consistency proof, or portable
  transparency-log format for admission records;
- allow caller-provided booleans such as `isTrusted` or `integrityVerified` to substitute for a
  trusted Admission Log adapter;
- make First-Admission Records Signed Documents;
- let a Signed Event act as its own First-Admission Record or authenticate its own anchor;
- implement Command freshness or clock-skew policy;
- implement signer role or policy authorization;
- implement Mission or WorkItem state machines; or
- change the current cryptography artifact digest, evaluation count, or six-stage success meaning.

## Architecture and trust boundaries

### Cryptographic verification layer

The existing verifier continues to accept exact Signed Document bytes plus complete
Organization-scoped Registry evidence and to execute the six normative stages. It returns an
immutable `VerifiedSignedDocument`-equivalent result containing at least:

- Signed Document kind;
- Organization ID established by the Registry evidence;
- exact stage-5 signing bytes and signing hash;
- resolved key ID and bound Principal;
- protected signed-time text and parsed instant; and
- the selected key's effective `validFrom`, `validUntil`, and `revokedAt` evidence, with original
  timestamp text preserved and interval boundaries parsed as instants.

SDKs may expose the selected validity evidence directly or retain it in an opaque nested admission
evidence value. They must not require a second, potentially inconsistent key selection to validate
the admission time.

For a new admission decision, the Registry adapter must establish that its complete evidence is
current and applicable to the decision, as already required by Section 6.4. A superseded Registry
revision cannot produce admission-ready evidence for a new document.

### Admission layer

Admission is a separate module that consumes successful cryptographic evidence. Conceptual APIs are:

- `prepareFirstAdmission(verified, trustedContext)` to validate the admission inputs and create a
  candidate record;
- `admitFirst(documentBytes, registryAdapter, admissionLog, trustedContext)` as a safe orchestration
  API that runs verification, lookup, candidate creation, atomic append, returned-record
  validation, and result construction; and
- `verifyHistoricalAdmission(documentBytes, registryAdapter, admissionLog)` to rerun cryptographic
  verification and validate an existing record without creating one.

Exact language naming may follow SDK conventions, but the public separation and behavior must be
equivalent. Existing `verify` methods remain backward compatible and continue to return only
cryptographic evidence.

A successful admission returns an `AdmittedSignedDocument`-equivalent result containing the
cryptographic evidence plus the validated committed First-Admission Record. Constructing a
candidate record alone never returns this type. This result is local immutable SDK evidence, not a
new protocol wire object.

The trusted context supplies the Organization-assigned acceptance instant and the currently
authenticated accepting-service identity. Neither value is taken from the Signed Document or an
untrusted request field. MissionWeaveProtocol does not standardize the clock service or service-
authentication mechanism, but implementations must keep this input behind an explicit deployment
trust seam rather than exposing a convenience API that silently treats arbitrary caller data as
trusted context.

### Admission Log adapter

The Admission Log adapter is a trusted Organization deployment seam. It must provide operations
equivalent to:

- authoritative lookup by `(organizationId, signingHash)`;
- atomic append-or-return-existing under that logical key; and
- a returned authenticated service identity for a found or committed record.

The adapter contract must distinguish, for protected diagnostics, a found record, authoritative
absence, and unavailable or indeterminate state. Only authoritative absence permits creation of a
new candidate. Unavailable or indeterminate state fails closed.

Successful adapter return is the assertion that the accepting service was authenticated, writes
were restricted to authorized Organization services, and append-only integrity was established by
the deployment. The SDK compares the authenticated service identity with `record.acceptedBy` and
validates the record bytes. It does not accept public booleans that claim those properties and does
not attempt to verify an unspecified portable proof format.

## Normative First-Admission Record

The protocol repository will add `schemas/first-admission-record.schema.json`. It is a durable
protocol object but not a Signed Document and therefore has no top-level `signature`.

The object has `additionalProperties: false` and exactly these required fields:

| Field | Constraint | Purpose |
| --- | --- | --- |
| `protocolVersion` | `common.schema.json#/$defs/protocolVersion` | Protocol compatibility |
| `admissionRecordId` | absolute protocol identifier | Stable audit and Event-reference identity |
| `organizationId` | absolute protocol identifier | Organization trust-domain binding |
| `documentKind` | one of the nine v0.1 Signed Document profile IDs | Prevent cross-profile reuse |
| `signingHash` | `sha256:<64 lowercase hex>` | Bind exact stage-5 signing bytes |
| `keyId` | absolute protocol identifier | Bind the stage-4 resolved key |
| `principal` | exact common actor shape | Bind the Principal authenticated by the key |
| `trustedAcceptedAt` | RFC 3339 plus protocol timestamp profile | Organization-assigned acceptance instant |
| `acceptedBy` | common actor with `type: service` | Bind the authenticated accepting service |

The nine `documentKind` values are `agent-card`, `approval`, `artifact`, `command`,
`context-package`, `event`, `evidence`, `extension-profile`, and `group-snapshot`.

The record ID makes the record referenceable but does not authenticate it. The lexical spelling of
`trustedAcceptedAt` is retained. Unlike the protected Signed Document time, the record timestamp is
not required to use uppercase `Z`; it must satisfy the protocol timestamp profile and is compared
as an instant.

## Record invariants

Within one Organization, `(organizationId, signingHash)` is the logical uniqueness key.

- At most one authoritative First-Admission Record may exist for that key.
- One `admissionRecordId` must not identify records under different logical uniqueness keys.
- A retry that finds a valid compatible record is idempotent and returns that committed record.
- A record under the same key with a different document kind, key ID, or Principal is a conflict
  and fails admission; it is never replaced or repaired.
- The record's signing hash must be recomputed from the exact stage-5 bytes of the current
  cryptographic verification.
- The record key ID and Principal must equal the selected stage-4 binding exactly.
- The record Organization must equal the Organization scope of the Registry evidence.
- `trustedAcceptedAt` must satisfy `validFrom <= t`, with `t < validUntil` when present and
  `t < revokedAt` when present, using the earliest effective historical boundaries.
- A record cannot be reused for the same unsigned content under a different key or Principal.
- `acceptedBy` must equal the service identity authenticated by the Admission Log adapter.
- A Signed Event cannot be used as the record for its own signing hash.

`admissionRecordId` and `trustedAcceptedAt` may differ from a losing concurrent candidate when the
adapter atomically returns the record committed by another caller. The returned record is accepted
only if all normative bindings and interval rules pass.

## First-admission flow

1. Strictly verify the Signed Document through all six cryptographic stages using complete,
   admission-current Registry evidence.
2. Query the Admission Log by `(organizationId, signingHash)`.
3. If the adapter returns a record, validate its Schema, authenticated service, append-integrity
   assertion, exact bindings, and trusted acceptance interval. Return it as an idempotent success.
4. If the adapter reports authoritative absence, obtain the Organization's trusted acceptance time
   and authenticated accepting service from trusted context.
5. Validate the trusted acceptance time against the selected key's effective validity interval.
6. Create a candidate record with a new admission record ID and the exact verified bindings.
7. Call atomic append-or-return-existing.
8. Validate the returned committed record again. This covers concurrent winners and prevents an
   adapter result from bypassing protocol semantics.
9. Return admitted evidence only after the committed record passes every check.

Candidate generation must not append an Event, execute a state transition, or imply admission.
Those actions remain downstream of successful admission and later signer authorization.

## Historical-replay flow

1. Rerun the complete six-stage cryptographic verification against authoritative Registry history.
2. Query the Admission Log by the newly recomputed `(organizationId, signingHash)`.
3. Require an authenticated, integrity-protected record. Missing, unavailable, or indeterminate
   state fails; historical replay never creates a record.
4. Validate the record Schema and exact Organization, document kind, signing hash, key ID,
   Principal, and accepting-service bindings.
5. Require both the protected signed time and the trusted acceptance time to lie in the same
   selected key's effective validity interval.
6. Return admitted historical evidence.

A later expiry or revocation is compatible with historical replay only when the retained history
shows that both relevant instants preceded the earliest effective boundary. Rewriting, clearing, or
moving a prior boundary later remains forbidden by the existing Registry rules.

## Error model

Admission adds a semantic diagnostic stage named `admission`; it does not renumber or extend the
six cryptographic stages. Admission APIs use a separate exception/result family so callers cannot
mistake cryptographic completion for Organization admission.

All of the following fail closed at stage `admission` and map to wire code
`AUTH_INVALID_SIGNATURE`:

- malformed or schema-invalid First-Admission Record;
- missing record during historical replay;
- non-authoritative absence, unavailable log, or indeterminate lookup;
- accepting-service authentication or append-integrity failure;
- Organization, document kind, signing hash, key ID, Principal, or accepting-service mismatch;
- malformed trusted acceptance timestamp;
- trusted acceptance time outside the selected key interval;
- conflicting duplicate record;
- failure to atomically commit or return an existing record; and
- Signed Event self-anchoring.

Protected diagnostics retain a stable internal reason such as `record-missing`, `record-conflict`,
`log-unavailable`, `log-authentication-failed`, `record-binding-mismatch`, or
`trusted-time-outside-key-interval`. Untrusted callers receive only the generic wire failure.

Signer authorization remains a later step. Once implemented, it will run only after successful
admission and will continue to map policy denial to `AUTH_FORBIDDEN`.

## Admission conformance bundle

The protocol will add an independent `admission/` bundle rather than adding admission state to the
cryptography manifest. This preserves the exact meaning of the existing six-stage bundle and its
62 evaluations.

`admission/manifest.json` will:

- identify its own manifest version and artifact digest;
- pin the cryptography artifact digest whose Signed Documents and Registry evidence it reuses;
- identify each evaluation mode as `first-admission` or `historical-replay`;
- describe test-only adapter outcomes for authenticated record, authoritative absence,
  unauthenticated result, invalid append integrity, conflict, and unavailable state; and
- require every rejected evaluation to report stage `admission` and wire code
  `AUTH_INVALID_SIGNATURE`.

The adapter-outcome metadata is test harness input, not a normative deployed log-proof format.

The bundle contains exactly 30 evaluations.

### Twelve successful evaluations

1. First admission of Agent Card.
2. First admission of Approval.
3. First admission of Artifact manifest.
4. First admission of Command.
5. First admission of Context Package.
6. First admission of Event with a distinct external record.
7. First admission of Evidence.
8. First admission of Extension Profile.
9. First admission of Group Snapshot.
10. Idempotent retry returning the existing compatible record.
11. Historical replay after a later effective key expiry, with both protected and accepted times
    before the boundary.
12. Historical replay after a later effective key revocation, with both protected and accepted
    times before the boundary.

### Eighteen rejected evaluations

1. Historical record missing.
2. Signing-hash mismatch.
3. Key-ID mismatch.
4. Principal mismatch.
5. Organization mismatch.
6. Document-kind mismatch.
7. Trusted acceptance time before `validFrom`.
8. Trusted acceptance time equal to `validUntil`.
9. Trusted acceptance time after `validUntil`.
10. Trusted acceptance time equal to `revokedAt`.
11. Trusted acceptance time after `revokedAt`.
12. Malformed trusted acceptance timestamp.
13. Conflicting record under the same logical uniqueness key.
14. Non-service `acceptedBy`.
15. Accepting service not authenticated by the adapter.
16. Append-only integrity not established.
17. Admission Log unavailable or indeterminate.
18. Signed Event attempts to use itself as its First-Admission Record.

The generator and validator will assert the exact totals, expected histogram, single-fault fixture
shape, deterministic regeneration, and artifact digest. The nine profile admissions must use the
same public SDK path rather than schema-only tests.

## Protocol and SDK bundle changes

The normative schema count increases from 21 to 22. The protocol adds one valid and one invalid
structural vector for the new record, increasing structural conformance from 56 to 58 cases while
leaving the existing 56 cases unchanged. The invalid structural vector adds a forbidden top-level
`signature`, proving that the record is not a Signed Document. The 22-case/62-evaluation
cryptography bundle remains independently versioned and unchanged unless a concrete defect is
discovered.

Each SDK `PROTOCOL_PIN.json` will add an `admission` object equivalent to the existing cryptography
identity, including:

- manifest path and version;
- source protocol commit;
- artifact digest and artifact count;
- case count; and
- evaluation count, fixed at 30.

Every SDK must vendor the exact protocol `admission/` tree, include it in source and binary package
artifacts, expose the same semantic public API, and execute every manifest evaluation. Public API
naming and idiomatic result types may vary, but behavior, failure classification, and retained
evidence must not.

## Delivery sequence

1. Land the protocol specification clarification, First-Admission Record Schema, Admission bundle,
   generator, validator, README changes, and deterministic package contract.
2. Merge protocol and derive the only valid SDK pin from the merged `main` commit and generated
   Admission manifest; do not pin a design or feature commit.
3. Implement the Python reference Admission layer with public-path RED/GREEN tests.
4. Synchronize and implement TypeScript, Go, Rust, Java, and C++ against the exact merged bundle.
5. Run each repository's complete native, formatting, static-analysis, package, installed-consumer,
   and conformance gates.
6. Verify that all six SDK pins, Admission manifests, artifacts, and cryptography digest references
   are byte-identical.
7. Require successful PR-head CI and exact merged-main CI for every repository.
8. Run independent Spec and Standards reviews against exact final commits.
9. Publish one cross-language evidence issue with exact commits, digests, evaluation totals, PRs,
   CI runs, review results, and any legitimate local-toolchain skips.

All existing worktrees are preserved. Cleanup is outside this slice unless explicitly requested.

## TDD and verification strategy

The protocol owns the behavior first. Protocol fixtures, the reference Admission validator, and
manifest contracts establish the cross-language RED condition before SDK implementation.

Each SDK must demonstrate focused RED/GREEN through its public Admission API for at least:

- a valid first admission;
- a trusted acceptance time at an exclusive validity boundary;
- a mismatched existing record;
- historical replay after later revocation; and
- log unavailability.

The full gate for each repository includes:

- repository policy and generated-file determinism;
- Schema and manifest validation;
- all 30 Admission evaluations;
- all pre-existing structural and cryptography suites;
- formatter, linter, type checker, compiler, and static analysis as applicable;
- source-package and built-package bundle verification;
- an installed consumer using the public Admission API; and
- exact-commit CI evidence.

Local inspection or a passing private helper is insufficient. Java may use exact-commit CI for the
JDK-dependent gate only if a local JDK remains unavailable; the CI log must prove Maven verification,
package inclusion, and installed-consumer execution. C++ must exercise the installed CMake consumer
and public Admission API rather than a private helper.

## Acceptance criteria

This slice is complete only when all of the following are true:

- the normative First-Admission Record Schema is present and validated as the twenty-second schema;
- structural conformance contains 58 cases, including one valid and one invalid record vector;
- the record cannot contain a signature or act as its own trust anchor;
- the protocol owns exactly 30 deterministic Admission evaluations with 12 successes and 18
  rejections;
- every rejected evaluation maps to `admission` / `AUTH_INVALID_SIGNATURE`;
- first admission is complete only after atomic append-or-return-existing and returned-record
  validation;
- historical replay reruns all six cryptographic stages and never auto-creates a record;
- both protected and trusted acceptance instants are checked against the same effective key
  interval;
- retries are idempotent and conflicting records fail closed;
- all six SDKs expose equivalent public Admission semantics and execute all 30 evaluations;
- all six SDKs pin one merged protocol commit and identical Admission artifacts;
- all pre-existing cryptography behavior and the 62-evaluation bundle remain green;
- native, package/install, exact-head CI, exact-main CI, independent review, and cross-language
  evidence gates pass; and
- Command freshness, signer authorization, log-proof standardization, and state-machine behavior
  remain explicitly outside the delivered scope.
