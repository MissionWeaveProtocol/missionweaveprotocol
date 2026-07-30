# First-Admission and Historical-Trust Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a normative First-Admission Record, a deterministic 30-evaluation Admission bundle, and equivalent first-admission and historical-replay APIs to all six SDKs without changing the existing six-stage cryptographic verification contract.

**Architecture:** The protocol repository owns the record Schema, structural vectors, Admission manifest, deterministic generator, and executable reference validator. Admission remains a layer above Signed Document verification: every public orchestration path first obtains immutable six-stage evidence, then consults a trusted Admission Log adapter, validates the returned record and authenticated service, and only then returns admitted evidence. After the protocol change is merged, every SDK vendors the same merged Admission tree, pins its digest beside the unchanged cryptography digest, and executes all 30 evaluations through its public Admission API. Protocol validation uses a hash-locked Python environment outside the worktree so the repository policy scanner sees only repository content.

**Tech Stack:** Python 3.12/jsonschema/uv; TypeScript 5.9/Ajv/Vitest/npm; Go 1.24/santhosh-tekuri jsonschema; Rust 1.85/jsonschema/cargo; Java 21/Jackson/Maven/JUnit; C++20/jsoncons/OpenSSL/CMake/Ninja; GitHub CLI and GitHub Actions.

---

## Task revision and execution contract

- Active revision: MW-V1-2026-07-30-R1.
- Approved design: docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md at commit 3df7d5c58c9825e43620691e6f8a69e29404bbe1.
- Protocol base before this slice: origin/main at 27c9f5c80cdcc1bd2179aae6247426f59e833525.
- Existing cryptography identity is frozen: profile missionweaveprotocol.signed-document-verification.v0.1, digest sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3, 98 artifacts, 22 cases, 62 evaluations, 12 complete, and 50 rejected.
- Existing structural baseline is 21 schemas and 56 vectors. This slice changes it to 22 schemas and 58 vectors.
- The Admission bundle contract in this plan is 19 digest-protected artifacts, 5 cases, 30 evaluations, 12 complete, and 18 rejected.
- The root agent owns the only write lane. Spawned agents may perform independent read-only review, testing, or evidence gathering only.
- Before every push, merge, issue creation, or other externally visible action, re-read the task revision and confirm that the only active objective is First-Admission and historical-trust validation.
- Preserve every existing worktree. Do not remove branches or worktrees during this slice.
- Do not add Command freshness, signer authorization, portable log proofs, state-machine transitions, Event creation, or caller-provided trust booleans.
- A successful adapter return is the deployment assertion of authenticated service identity, authorized writes, and append-only integrity. Failures are typed adapter errors, not public boolean flags.
- First admission is not complete until append-or-return-existing succeeds and the returned record is validated again.
- Historical replay always reruns the six cryptographic stages and never creates a missing record.

## Shared semantic contract

The six SDKs may use idiomatic naming, but each implementation must expose the following semantic units:

~~~text
prepareFirstAdmission(
    verified,
    trustedContext
) -> PreparedFirstAdmission

admitFirst(
    kind,
    documentBytes,
    admissionCurrentRegistry,
    admissionLog,
    trustedContext
) -> AdmittedSignedDocument

verifyHistoricalAdmission(
    kind,
    documentBytes,
    historicalRegistry,
    admissionLog
) -> AdmittedSignedDocument
~~~

`admissionCurrentRegistry` is a distinct public adapter contract whose method name asserts that the complete Registry evidence is current and applicable to a new admission. `historicalRegistry` uses the existing historical `KeyResolver` contract. Each SDK task below defines the exact idiomatic interface and the internal adapter that lets the unchanged six-stage verifier consume the current-evidence contract; no caller-provided trust boolean is introduced.

The trusted context is a deployment seam invoked only after authoritative absence. It returns exactly:

~~~json
{
  "admissionRecordId": "urn:missionweaveprotocol:admission-record:command",
  "trustedAcceptedAt": "2026-07-15T00:05:00Z",
  "acceptedBy": {
    "type": "service",
    "id": "urn:missionweaveprotocol:service:admission"
  }
}
~~~

The Admission Log has two operations:

~~~text
lookup(organizationId, signingHash)
  -> found authenticated record
  -> authoritative absence
  -> typed adapter failure

appendOrReturnExisting(organizationId, signingHash, candidateBytes)
  -> committed authenticated record
  -> concurrently existing authenticated record
  -> typed adapter failure
~~~

Unavailable, indeterminate, unauthenticated, integrity-failed, conflict, and commit-failed outcomes are typed failures. No SDK API accepts isTrusted, integrityVerified, authenticated, or an equivalent caller boolean.

Every Admission failure exposes:

~~~text
wireCode = AUTH_INVALID_SIGNATURE
protected stage = admission
protected reason = one stable reason identifier
~~~

The stable reasons used by the protocol bundle are:

~~~text
record-missing
record-binding-mismatch
trusted-time-outside-key-interval
malformed-trusted-time
record-conflict
record-schema-invalid
log-authentication-failed
append-integrity-not-established
log-unavailable
log-indeterminate
commit-failed
event-self-anchoring
~~~

## File map

### Protocol repository

Implementation worktree:

/Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-impl

Create:

- schemas/first-admission-record.schema.json
- conformance/vectors/valid/first-admission-record.json
- conformance/vectors/invalid/first-admission-record-with-signature.json
- admission/README.md
- admission/manifest.schema.json
- admission/manifest.json
- admission/records/valid/agent-card.json
- admission/records/valid/approval.json
- admission/records/valid/artifact.json
- admission/records/valid/command.json
- admission/records/valid/context-package.json
- admission/records/valid/event.json
- admission/records/valid/evidence.json
- admission/records/valid/extension-profile.json
- admission/records/valid/group-snapshot.json
- admission/records/invalid/signing-hash-mismatch.json
- admission/records/invalid/key-id-mismatch.json
- admission/records/invalid/principal-mismatch.json
- admission/records/invalid/organization-mismatch.json
- admission/records/invalid/document-kind-mismatch.json
- admission/records/invalid/accepted-by-non-service.json
- admission/registries/registry-later-revocation.json
- scripts/generate_admission_vectors.py
- scripts/validate_admission_vectors.py

Modify:

- conformance/manifest.json
- scripts/validate_protocol.py
- scripts/validate_crypto_vectors.py
- schemas/README.md
- conformance/README.md
- cryptography/README.md
- spec/PROTOCOL.md
- README.md
- README.de.md
- README.es.md
- README.fr.md
- README.ja.md
- README.zh-CN.md
- README.zh-TW.md
- .github/workflows/validate.yml

### SDK repositories

Authoritative starting commits:

- Python: 623eadb11ca9a0a17aa527d93035ba3a07ff4666
- TypeScript: 69d5b3056aa80cf208121e04ef7c2be67b86b2d7
- Go: 351c7ed0f6e5e71f2814bb0da7f33a6d82a0e218
- Rust: 39ddee963a1d33d0f73e3217210ff4628f140ffa
- Java: 8157f24f4a7455483f234db4143dccdc7d4462cf
- C++: d838a57d9407eecf506324fa32993c10b559c95e

Every SDK modifies PROTOCOL_PIN.json, vendors the merged schemas/conformance/admission trees, preserves the byte-identical cryptography tree, adds Admission bundle verification, packages admission/, updates localized documentation, and adds an installed-consumer public-API smoke test.

### Task 1: Create the isolated protocol implementation lane

**Files:**

- Read: docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md
- Read: docs/superpowers/plans/2026-07-30-first-admission-historical-trust.md
- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-impl

- [ ] **Step 1: Load the execution and worktree skills**

Read superpowers:executing-plans and superpowers:using-git-worktrees completely before creating or editing the implementation worktree.

- [ ] **Step 2: Verify the design checkout and active revision**

Run:

~~~bash
git -C /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-design status --short --branch
git -C /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-design log -2 --oneline
rg -n "MW-V1-2026-07-30-R1|Status: Approved" /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-design/docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md
~~~

Expected: the branch is design/first-admission-historical-trust, the approved spec and plan are present, and there are no unrelated changes.

- [ ] **Step 3: Fetch the protocol remote without changing the design checkout**

Run:

~~~bash
git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin
git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main
~~~

Expected before implementation begins: 27c9f5c80cdcc1bd2179aae6247426f59e833525. If origin/main has advanced, inspect the new commits and rebase the design branch only after confirming they do not change this task's approved semantics.

- [ ] **Step 4: Create the implementation worktree from the design branch**

Run:

~~~bash
git -C /Users/lionelmbp/repos/missionweaveprotocol worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-impl \
  -b feat/first-admission-historical-trust \
  design/first-admission-historical-trust
~~~

Expected: the new worktree contains the approved spec and plan and is on feat/first-admission-historical-trust.

- [ ] **Step 5: Create the external hash-locked validation environment if it is absent**

Run from the implementation worktree:

~~~bash
MW_CRYPTO_VENV=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
test -x "$MW_CRYPTO_VENV/bin/python" || uv venv --python 3.12.13 "$MW_CRYPTO_VENV"
test "$("$MW_CRYPTO_PYTHON" -c 'import platform; print(platform.python_version())')" = "3.12.13"
uv pip install --python "$MW_CRYPTO_PYTHON" --require-hashes --no-deps \
  --only-binary :all: --strict --requirements requirements-cryptography.lock
~~~

Expected: the interpreter assertion confirms exact Python 3.12.13 and dependency installation completes from the committed lock file. Do not create the venv inside the worktree: `scripts/check_repository_policy.py` intentionally scans every worktree file and does not apply Git ignore rules.

- [ ] **Step 6: Establish the unchanged baseline**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/check_repository_policy.py
"$MW_CRYPTO_PYTHON" scripts/validate_protocol.py
"$MW_CRYPTO_PYTHON" scripts/generate_crypto_vectors.py
git diff --exit-code -- cryptography
"$MW_CRYPTO_PYTHON" scripts/validate_crypto_vectors.py
git status --short --branch
~~~

Expected: repository policy passes, protocol validation reports 21 schemas and 56 vectors, cryptography reports 22 cases and 62 evaluations, and only the approved spec/plan commits differ from origin/main.

### Task 2: Add the normative record Schema and prove 58 structural vectors

**Files:**

- Create: schemas/first-admission-record.schema.json
- Create: conformance/vectors/valid/first-admission-record.json
- Create: conformance/vectors/invalid/first-admission-record-with-signature.json
- Modify: conformance/manifest.json
- Modify: scripts/validate_protocol.py
- Modify: schemas/README.md
- Modify: conformance/README.md

- [ ] **Step 1: Write the valid First-Admission Record vector**

Create conformance/vectors/valid/first-admission-record.json with:

~~~json
{
  "protocolVersion": "0.1",
  "admissionRecordId": "urn:missionweaveprotocol:admission-record:command",
  "organizationId": "urn:missionweaveprotocol:organization:acme",
  "documentKind": "command",
  "signingHash": "sha256:6655c5d67ae3ecc19a4ed04bda7f1372aeaafc7adf939a77715de96ef2100695",
  "keyId": "urn:missionweaveprotocol:key:crypto-vector-rfc8032-1",
  "principal": {
    "type": "agent",
    "id": "urn:missionweaveprotocol:agent:crypto-vector-coordinator"
  },
  "trustedAcceptedAt": "2026-07-15T00:05:00Z",
  "acceptedBy": {
    "type": "service",
    "id": "urn:missionweaveprotocol:service:admission"
  }
}
~~~

- [ ] **Step 2: Write the invalid vector with the forbidden signature**

Create conformance/vectors/invalid/first-admission-record-with-signature.json as the exact valid object plus:

~~~json
"signature": {
  "algorithm": "Ed25519",
  "keyId": "urn:missionweaveprotocol:key:crypto-vector-rfc8032-1",
  "createdAt": "2026-07-15T00:05:00Z",
  "value": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
}
~~~

Keep all otherwise-valid fields unchanged so the single intended fault is the forbidden top-level member.

- [ ] **Step 3: Register both vectors before the Schema exists**

Append these entries to conformance/manifest.json in the existing logical grouping:

~~~json
{
  "name": "valid First-Admission Record",
  "schema": "schemas/first-admission-record.schema.json",
  "instance": "conformance/vectors/valid/first-admission-record.json",
  "valid": true
},
{
  "name": "First-Admission Record cannot contain a signature",
  "schema": "schemas/first-admission-record.schema.json",
  "instance": "conformance/vectors/invalid/first-admission-record-with-signature.json",
  "valid": false
}
~~~

- [ ] **Step 4: Run structural validation and prove RED**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/validate_protocol.py
~~~

Expected: FAIL because schemas/first-admission-record.schema.json does not exist or the schema count contract is still 21.

- [ ] **Step 5: Add the complete normative Schema**

Create schemas/first-admission-record.schema.json with:

~~~json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://missionweaveprotocol.dev/schemas/0.1/first-admission-record.schema.json",
  "title": "MissionWeaveProtocol 0.1 First-Admission Record",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "protocolVersion",
    "admissionRecordId",
    "organizationId",
    "documentKind",
    "signingHash",
    "keyId",
    "principal",
    "trustedAcceptedAt",
    "acceptedBy"
  ],
  "properties": {
    "protocolVersion": {
      "$ref": "common.schema.json#/$defs/protocolVersion"
    },
    "admissionRecordId": {
      "$ref": "common.schema.json#/$defs/id"
    },
    "organizationId": {
      "$ref": "common.schema.json#/$defs/id"
    },
    "documentKind": {
      "enum": [
        "agent-card",
        "approval",
        "artifact",
        "command",
        "context-package",
        "event",
        "evidence",
        "extension-profile",
        "group-snapshot"
      ]
    },
    "signingHash": {
      "$ref": "common.schema.json#/$defs/sha256"
    },
    "keyId": {
      "$ref": "common.schema.json#/$defs/id"
    },
    "principal": {
      "$ref": "common.schema.json#/$defs/actor"
    },
    "trustedAcceptedAt": {
      "$ref": "common.schema.json#/$defs/timestamp"
    },
    "acceptedBy": {
      "allOf": [
        {
          "$ref": "common.schema.json#/$defs/actor"
        },
        {
          "properties": {
            "type": {
              "const": "service"
            }
          }
        }
      ]
    }
  }
}
~~~

- [ ] **Step 6: Update the exact schema and vector counts**

In scripts/validate_protocol.py, change the count contract and success line to:

~~~python
EXPECTED_SCHEMA_COUNT = 22
EXPECTED_VECTOR_COUNT = 58

if len(schema_paths) != EXPECTED_SCHEMA_COUNT:
    raise ProtocolValidationError(
        f"expected {EXPECTED_SCHEMA_COUNT} schemas, found {len(schema_paths)}"
    )

if len(manifest) != EXPECTED_VECTOR_COUNT:
    raise ProtocolValidationError(
        f"expected {EXPECTED_VECTOR_COUNT} conformance vectors, found {len(manifest)}"
    )

print(
    f"Validated {EXPECTED_SCHEMA_COUNT} schemas and "
    f"{EXPECTED_VECTOR_COUNT} conformance vectors."
)
~~~

Retain the existing unlisted-vector and duplicate-path checks.

- [ ] **Step 7: Run structural validation and prove GREEN**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/validate_protocol.py
~~~

Expected: Validated 22 schemas and 58 conformance vectors.

- [ ] **Step 8: Document the structural boundary**

Update schemas/README.md to state that there are 22 normative schemas and that First-Admission Record is durable metadata but not a Signed Document. Update conformance/README.md to state that there are 58 structural vectors and link admission/README.md for behavioral Admission evidence.

- [ ] **Step 9: Commit the structural slice**

Run:

~~~bash
git add schemas/first-admission-record.schema.json schemas/README.md \
  conformance/manifest.json conformance/README.md \
  conformance/vectors/valid/first-admission-record.json \
  conformance/vectors/invalid/first-admission-record-with-signature.json \
  scripts/validate_protocol.py
git commit -m "feat(protocol): define first-admission record"
~~~

### Task 3: Define and deterministically generate the independent Admission bundle

**Files:**

- Create: admission/manifest.schema.json
- Create: admission/manifest.json
- Create: admission/records/valid/*.json
- Create: admission/records/invalid/*.json
- Create: admission/registries/registry-later-revocation.json
- Create: scripts/generate_admission_vectors.py

- [ ] **Step 1: Add the Admission manifest identity and exact top-level contract**

Create admission/manifest.schema.json with these top-level fields and values:

~~~json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://missionweaveprotocol.dev/admission/0.1/manifest.schema.json",
  "title": "MissionWeaveProtocol 0.1 Admission Conformance Manifest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "$schema",
    "manifestVersion",
    "protocolVersion",
    "profileId",
    "semanticStage",
    "wireCode",
    "cryptography",
    "fixtureSchemas",
    "artifactDigest",
    "artifacts",
    "cases"
  ],
  "properties": {
    "$schema": {
      "const": "https://missionweaveprotocol.dev/admission/0.1/manifest.schema.json"
    },
    "manifestVersion": {
      "const": 1
    },
    "protocolVersion": {
      "const": "0.1"
    },
    "profileId": {
      "const": "missionweaveprotocol.first-admission-historical-trust.v0.1"
    },
    "semanticStage": {
      "const": "admission"
    },
    "wireCode": {
      "const": "AUTH_INVALID_SIGNATURE"
    },
    "cryptography": {
      "type": "object",
      "additionalProperties": false,
      "required": ["manifest", "artifactDigest"],
      "properties": {
        "manifest": {
          "const": "cryptography/manifest.json"
        },
        "artifactDigest": {
          "const": "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
        }
      }
    },
    "fixtureSchemas": {
      "type": "object",
      "additionalProperties": false,
      "required": ["record", "registry"],
      "properties": {
        "record": {
          "const": "schemas/first-admission-record.schema.json"
        },
        "registry": {
          "const": "cryptography/registry-fixture.schema.json"
        }
      }
    },
    "artifactDigest": {
      "$ref": "#/$defs/sha256"
    },
    "artifacts": {
      "type": "array",
      "minItems": 19,
      "maxItems": 19,
      "items": {
        "$ref": "#/$defs/artifact"
      }
    },
    "cases": {
      "type": "array",
      "minItems": 5,
      "maxItems": 5,
      "items": {
        "$ref": "#/$defs/case"
      }
    }
  }
}
~~~

Add complete definitions for repositoryPath, sha256, principal, trustedContext, lookupOutcome, appendOutcome, completeExpectation, rejectedExpectation, evaluation, artifact, and case. Use these exact enums:

~~~json
{
  "mode": ["first-admission", "historical-replay"],
  "lookupStatus": [
    "found",
    "authoritative-absence",
    "unauthenticated",
    "integrity-failed",
    "unavailable",
    "indeterminate"
  ],
  "appendStatus": [
    "committed",
    "existing",
    "conflict",
    "unauthenticated",
    "integrity-failed",
    "unavailable",
    "indeterminate"
  ],
  "expectedStage": ["complete", "admission"],
  "wireCode": [null, "AUTH_INVALID_SIGNATURE"]
}
~~~

Condition the Schema so found/committed/existing outcomes require record and authenticatedService, authoritative absence forbids them, first-admission evaluations may contain trustedContext, and historical-replay evaluations require trustedContext to be null.

- [ ] **Step 2: Add deterministic generator constants**

Start scripts/generate_admission_vectors.py with:

~~~python
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
CRYPTOGRAPHY_DIGEST = (
    "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
)
ACCEPTED_BY = {
    "type": "service",
    "id": "urn:missionweaveprotocol:service:admission",
}
PROFILE_IDS = (
    "agent-card",
    "approval",
    "artifact",
    "command",
    "context-package",
    "event",
    "evidence",
    "extension-profile",
    "group-snapshot",
)
EXPECTED_CASES = 5
EXPECTED_EVALUATIONS = 30
EXPECTED_COMPLETE = 12
EXPECTED_REJECTED = 18
EXPECTED_ARTIFACTS = 19
~~~

- [ ] **Step 3: Generate one valid record per Signed Document profile**

Build each record from the complete evaluation in cryptography/manifest.json, preserving the exact key ID, Principal, signing hash, and profile ID. Use deterministic IDs and accepted times:

~~~python
TRUSTED_ACCEPTED_AT = {
    "agent-card": "2026-07-01T00:05:00Z",
    "approval": "2026-07-15T04:05:00Z",
    "artifact": "2026-07-15T02:05:00Z",
    "command": "2026-07-15T00:05:00Z",
    "context-package": "2026-07-15T01:05:00Z",
    "event": "2026-07-15T03:05:00Z",
    "evidence": "2026-07-15T05:05:00Z",
    "extension-profile": "2026-07-15T06:05:00Z",
    "group-snapshot": "2026-07-15T07:05:00Z",
}

def _record(profile_id: str, verified: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": "0.1",
        "admissionRecordId": (
            f"urn:missionweaveprotocol:admission-record:crypto-vector-{profile_id}"
        ),
        "organizationId": "urn:missionweaveprotocol:organization:acme",
        "documentKind": profile_id,
        "signingHash": verified["signingHash"],
        "keyId": verified["keyId"],
        "principal": copy.deepcopy(verified["principal"]),
        "trustedAcceptedAt": TRUSTED_ACCEPTED_AT[profile_id],
        "acceptedBy": copy.deepcopy(ACCEPTED_BY),
    }
~~~

- [ ] **Step 4: Generate the six invalid record fixtures as single mutations**

Derive all six from admission/records/valid/command.json:

~~~python
invalid_mutations = {
    "signing-hash-mismatch": (
        "signingHash",
        "sha256:" + "0" * 64,
    ),
    "key-id-mismatch": (
        "keyId",
        "urn:missionweaveprotocol:key:other",
    ),
    "principal-mismatch": (
        "principal",
        {
            "type": "agent",
            "id": "urn:missionweaveprotocol:agent:other",
        },
    ),
    "organization-mismatch": (
        "organizationId",
        "urn:missionweaveprotocol:organization:other",
    ),
    "document-kind-mismatch": (
        "documentKind",
        "event",
    ),
    "accepted-by-non-service": (
        "acceptedBy",
        {
            "type": "human",
            "id": "urn:missionweaveprotocol:human:admission",
        },
    ),
}
~~~

Assert that each generated fixture differs from the valid Command record at exactly one top-level field.

- [ ] **Step 5: Generate the retained-history Registry fixture for later revocation**

Create admission/registries/registry-later-revocation.json by copying cryptography/keys/registry-valid.json and appending this status to the Command key:

~~~json
{
  "sequence": 2,
  "recordedAt": "2026-07-17T00:00:00Z",
  "revokedAt": "2026-07-15T01:00:00Z"
}
~~~

The existing sequence 1 validUntil boundary remains unchanged. The protected Command time and trusted acceptance time are both before the new revocation boundary.

- [ ] **Step 6: Generate the twelve success evaluations**

Create these cases:

~~~text
accept.first-admission.profile-matrix            9 evaluations
accept.first-admission.idempotent-retry          1 evaluation
accept.historical-replay.later-expiry            1 evaluation
accept.historical-replay.later-revocation        1 evaluation
~~~

The nine profile evaluations use authoritative absence followed by committed. Idempotent retry uses found and never calls append. Both historical evaluations use found and trustedContext null.

- [ ] **Step 7: Generate the eighteen rejected evaluations**

Use these exact evaluation IDs, modes, adapter points, and protected reasons:

~~~text
historical-record-missing                  historical-replay  lookup   record-missing
signing-hash-mismatch                     historical-replay  lookup   record-binding-mismatch
key-id-mismatch                           historical-replay  lookup   record-binding-mismatch
principal-mismatch                        historical-replay  lookup   record-binding-mismatch
organization-mismatch                     historical-replay  lookup   record-binding-mismatch
document-kind-mismatch                    historical-replay  lookup   record-binding-mismatch
trusted-time-before-valid-from            first-admission    prepare  trusted-time-outside-key-interval
trusted-time-equal-valid-until            first-admission    prepare  trusted-time-outside-key-interval
trusted-time-after-valid-until            first-admission    prepare  trusted-time-outside-key-interval
trusted-time-equal-revoked-at             first-admission    prepare  trusted-time-outside-key-interval
trusted-time-after-revoked-at             first-admission    prepare  trusted-time-outside-key-interval
malformed-trusted-time                    first-admission    prepare  malformed-trusted-time
conflicting-record                        first-admission    append   record-conflict
accepted-by-non-service                   historical-replay  lookup   record-schema-invalid
accepting-service-not-authenticated       historical-replay  lookup   log-authentication-failed
append-integrity-not-established          first-admission    append   append-integrity-not-established
admission-log-indeterminate               historical-replay  lookup   log-indeterminate
event-self-anchoring                      historical-replay  lookup   event-self-anchoring
~~~

Every rejected expectation is exactly:

The generator uses this exact reason map:

~~~python
REJECTED_REASONS = {
    "historical-record-missing": "record-missing",
    "signing-hash-mismatch": "record-binding-mismatch",
    "key-id-mismatch": "record-binding-mismatch",
    "principal-mismatch": "record-binding-mismatch",
    "organization-mismatch": "record-binding-mismatch",
    "document-kind-mismatch": "record-binding-mismatch",
    "trusted-time-before-valid-from": "trusted-time-outside-key-interval",
    "trusted-time-equal-valid-until": "trusted-time-outside-key-interval",
    "trusted-time-after-valid-until": "trusted-time-outside-key-interval",
    "trusted-time-equal-revoked-at": "trusted-time-outside-key-interval",
    "trusted-time-after-revoked-at": "trusted-time-outside-key-interval",
    "malformed-trusted-time": "malformed-trusted-time",
    "conflicting-record": "record-conflict",
    "accepted-by-non-service": "record-schema-invalid",
    "accepting-service-not-authenticated": "log-authentication-failed",
    "append-integrity-not-established": "append-integrity-not-established",
    "admission-log-indeterminate": "log-indeterminate",
    "event-self-anchoring": "event-self-anchoring",
}

protected_reason = REJECTED_REASONS[evaluation_id]
expectation = {
    "stage": "admission",
    "wireCode": "AUTH_INVALID_SIGNATURE",
    "reason": protected_reason,
}
~~~

Assert `set(REJECTED_REASONS) == set(rejected_evaluation_ids)` and that every mapped value belongs to the stable reason set before writing the manifest.

- [ ] **Step 8: Build the 19-entry artifact index and digest**

The artifact index contains:

~~~text
admission/manifest.schema.json
admission/records/valid/*.json                       9 files
admission/records/invalid/*.json                     6 files
admission/registries/registry-later-revocation.json  1 file
schemas/common.schema.json
schemas/first-admission-record.schema.json
~~~

Sort paths lexically. For each entry store path, byteLength, and sha256:<lowercase hex>. Compute artifactDigest by deleting only the top-level artifactDigest member, serializing with RFC 8785 JCS, and hashing those bytes.

- [ ] **Step 9: Assert exact counts and write the manifest**

Add:

~~~python
case_count = len(cases)
evaluation_count = sum(len(case["evaluations"]) for case in cases)
complete_count = sum(
    evaluation["expect"]["stage"] == "complete"
    for case in cases
    for evaluation in case["evaluations"]
)
rejected_count = evaluation_count - complete_count

actual = (
    len(artifacts),
    case_count,
    evaluation_count,
    complete_count,
    rejected_count,
)
expected = (
    EXPECTED_ARTIFACTS,
    EXPECTED_CASES,
    EXPECTED_EVALUATIONS,
    EXPECTED_COMPLETE,
    EXPECTED_REJECTED,
)
if actual != expected:
    raise RuntimeError(f"Admission bundle counts {actual!r} do not match {expected!r}")
~~~

- [ ] **Step 10: Run the generator twice and prove determinism**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git diff -- admission schemas/first-admission-record.schema.json > /tmp/mw-admission-first.diff
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git diff -- admission schemas/first-admission-record.schema.json > /tmp/mw-admission-second.diff
cmp /tmp/mw-admission-first.diff /tmp/mw-admission-second.diff
~~~

Expected: cmp exits 0 and the generated manifest reports 19 artifacts, 5 cases, and 30 evaluations.

- [ ] **Step 11: Commit the generated Admission bundle**

Run:

~~~bash
git add admission scripts/generate_admission_vectors.py
git commit -m "feat(protocol): add admission conformance bundle"
~~~

### Task 4: Add the executable reference Admission validator with RED/GREEN evidence

**Files:**

- Modify: scripts/validate_crypto_vectors.py
- Create: scripts/validate_admission_vectors.py

- [ ] **Step 1: Extract one reusable six-stage reference function without changing behavior**

In scripts/validate_crypto_vectors.py, add the selected profile ID to the immutable reference result:

~~~python
@dataclass(frozen=True)
class VerifiedResult:
    document: dict[str, Any]
    document_kind: str
    envelope: EnvelopeResult
    key: ResolvedKey
    signing_bytes: bytes
    signing_hash: str
~~~

Then add:

~~~python
def verify_signed_document_bytes(
    *,
    profile: Mapping[str, Any],
    document_bytes: bytes,
    registry_bytes: bytes,
    schemas: Mapping[str, Mapping[str, Any]],
    schema_registry: Registry,
    document_label: str,
    registry_label: str,
) -> VerifiedResult:
    document = _parse_document(document_bytes, label=document_label)
    _schema_stage(
        document,
        schema=schemas[profile["schema"]],
        registry=schema_registry,
    )
    envelope = _signature_envelope(document, profile)
    key = _resolve_key(registry_bytes, envelope, label=registry_label)
    signing_bytes, signing_hash = _canonicalization_stage(document)
    _signature_stage(signing_bytes, envelope, key)
    return VerifiedResult(
        document=document,
        document_kind=profile["profileId"],
        envelope=envelope,
        key=key,
        signing_bytes=signing_bytes,
        signing_hash=signing_hash,
    )
~~~

Change `_run_signed_evaluation` to assign `result = verify_signed_document_bytes(...)`, then pass that same result to `_validate_signing_key` and `_compare_verified`. The `document_kind` value is exactly the selected manifest profile's `profileId` (`agent-card` through `group-snapshot`); it is not inferred from document content. Do not change any stage, exception, reason, count, fixture, signing bytes, hash, or cryptography artifact.

- [ ] **Step 2: Rerun cryptography before writing Admission behavior**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/validate_crypto_vectors.py
git diff --exit-code -- cryptography
~~~

Expected: all 62 evaluations pass and the cryptography tree is unchanged.

- [ ] **Step 3: Add manifest, artifact, and matrix preflight to the Admission validator**

In scripts/validate_admission_vectors.py, validate:

~~~text
manifest Schema and exact top-level fields
cryptography artifact digest equality
19 sorted unique artifact paths
byte lengths and SHA-256 values
RFC 8785 artifactDigest
5 sorted unique case IDs
30 unique evaluation IDs
12 complete and 18 rejected
all rejected expectations are admission / AUTH_INVALID_SIGNATURE
all record fixtures satisfy their declared single-fault shape
all referenced files are indexed or protected by the pinned cryptography bundle
~~~

Use the protocol timestamp parser and six-stage function imported from validate_crypto_vectors.py; do not add a second timestamp or cryptographic implementation.

- [ ] **Step 4: Write RED assertions for the five public flow boundaries**

Before adding successful Admission behavior, make the runner attempt:

~~~python
REQUIRED_PUBLIC_PATHS = {
    "first-admission.command",
    "trusted-time-equal-valid-until",
    "key-id-mismatch",
    "historical-replay.later-revocation",
    "admission-log-indeterminate",
}
~~~

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
~~~

Expected: FAIL because the Admission flow functions are not defined.

- [ ] **Step 5: Add strict record parsing and Schema validation**

Implement:

~~~python
@dataclass(frozen=True)
class AuthenticatedRecord:
    record_bytes: bytes
    authenticated_service: dict[str, str]

def _parse_record(
    raw: bytes,
    *,
    record_schema: Mapping[str, Any],
    schema_registry: Registry,
) -> tuple[dict[str, Any], Rfc3339Instant]:
    try:
        value = _strict_json(raw, label="First-Admission Record")
        _validate_instance(
            value,
            record_schema,
            registry=schema_registry,
            label="First-Admission Record",
        )
    except (StrictJsonError, BundleValidationError) as error:
        raise AdmissionFailure("record-schema-invalid", str(error)) from error
    if not isinstance(value, dict):
        raise AdmissionFailure("record-schema-invalid", "record is not an object")
    try:
        instant = _parse_rfc3339_value(value["trustedAcceptedAt"])
    except ValueError as error:
        raise AdmissionFailure("malformed-trusted-time", str(error)) from error
    return value, instant
~~~

AdmissionFailure always reports stage admission and wire code AUTH_INVALID_SIGNATURE.

- [ ] **Step 6: Add exact binding and interval validation**

Implement:

~~~python
def _validate_committed_record(
    authenticated: AuthenticatedRecord,
    verified: VerifiedResult,
    *,
    record_schema: Mapping[str, Any],
    schema_registry: Registry,
) -> dict[str, Any]:
    record, accepted = _parse_record(
        authenticated.record_bytes,
        record_schema=record_schema,
        schema_registry=schema_registry,
    )
    expected = {
        "organizationId": verified.key.organization_id,
        "documentKind": verified.document_kind,
        "signingHash": verified.signing_hash,
        "keyId": verified.key.key_id,
        "principal": verified.key.principal,
    }
    for field, value in expected.items():
        if record[field] != value:
            raise AdmissionFailure(
                "record-binding-mismatch",
                f"{field} does not match six-stage evidence",
            )
    if record["acceptedBy"] != authenticated.authenticated_service:
        raise AdmissionFailure(
            "log-authentication-failed",
            "acceptedBy does not match the authenticated service",
        )
    if accepted < verified.key.valid_from:
        raise AdmissionFailure(
            "trusted-time-outside-key-interval",
            "trustedAcceptedAt precedes validFrom",
        )
    if verified.key.valid_until is not None and accepted >= verified.key.valid_until:
        raise AdmissionFailure(
            "trusted-time-outside-key-interval",
            "trustedAcceptedAt is at or after validUntil",
        )
    if verified.key.revoked_at is not None and accepted >= verified.key.revoked_at:
        raise AdmissionFailure(
            "trusted-time-outside-key-interval",
            "trustedAcceptedAt is at or after revokedAt",
        )
    return record
~~~

Use `verified.document_kind` added in Step 1. Do not derive the kind from record bytes and do not change signing bytes or hashes.

- [ ] **Step 7: Add first-admission orchestration**

Implement the exact order:

~~~python
def admit_first(evaluation: Mapping[str, Any], fixtures: FixtureStore) -> dict[str, Any]:
    verified = fixtures.verify(evaluation)
    lookup = fixtures.lookup(evaluation, verified)
    if lookup.found is not None:
        return _validate_committed_record(
            lookup.found,
            verified,
            record_schema=fixtures.record_schema,
            schema_registry=fixtures.schema_registry,
        )
    if not lookup.authoritative_absence:
        raise AdmissionFailure(lookup.reason, "lookup did not establish absence")
    prepared = _prepare_first_admission(
        verified,
        fixtures.trusted_context(evaluation),
    )
    committed = fixtures.append_or_return_existing(evaluation, prepared)
    return _validate_committed_record(
        committed,
        verified,
        record_schema=fixtures.record_schema,
        schema_registry=fixtures.schema_registry,
    )
~~~

The fixture store records lookup and append call counts. Successful profile admissions must call lookup once and append once; idempotent retry must call lookup once and append zero times.

- [ ] **Step 8: Add historical replay orchestration**

Implement:

~~~python
def verify_historical_admission(
    evaluation: Mapping[str, Any],
    fixtures: FixtureStore,
) -> dict[str, Any]:
    verified = fixtures.verify(evaluation)
    lookup = fixtures.lookup(evaluation, verified)
    if lookup.found is None:
        reason = (
            "record-missing"
            if lookup.authoritative_absence
            else lookup.reason
        )
        raise AdmissionFailure(reason, "historical replay requires a record")
    return _validate_committed_record(
        lookup.found,
        verified,
        record_schema=fixtures.record_schema,
        schema_registry=fixtures.schema_registry,
    )
~~~

Assert that historical replay never invokes trusted context or append.

- [ ] **Step 9: Detect Event self-anchoring before accepting record bytes**

If profileId is event and the adapter outcome identifies the Signed Event document itself as the record source, raise:

~~~python
raise AdmissionFailure(
    "event-self-anchoring",
    "a Signed Event cannot authenticate its own First-Admission Record",
)
~~~

- [ ] **Step 10: Run the Admission validator and prove GREEN**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
~~~

Expected:

~~~text
Validated Admission bundle: 19 artifacts, 5 cases, 30 evaluations, 12 complete and 18 rejected; cryptography digest sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3.
~~~

- [ ] **Step 11: Prove generator and both validators are jointly deterministic**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/generate_crypto_vectors.py
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git status --porcelain=v1 --untracked-files=all > /tmp/mw-generated-status
sed -n '1,200p' /tmp/mw-generated-status
"$MW_CRYPTO_PYTHON" scripts/validate_crypto_vectors.py
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
~~~

Expected: only intentional source/documentation changes appear; no generated artifact changes appear after regeneration.

- [ ] **Step 12: Commit the reference validator**

Run:

~~~bash
git add scripts/validate_crypto_vectors.py scripts/validate_admission_vectors.py
git commit -m "feat(protocol): validate admission semantics"
~~~

### Task 5: Document, wire CI, and fully verify the protocol repository

**Files:**

- Create: admission/README.md
- Modify: spec/PROTOCOL.md
- Modify: cryptography/README.md
- Modify: README.md
- Modify: README.de.md
- Modify: README.es.md
- Modify: README.fr.md
- Modify: README.ja.md
- Modify: README.zh-CN.md
- Modify: README.zh-TW.md
- Modify: .github/workflows/validate.yml

- [ ] **Step 1: Replace the Section 6.4 Admission prose with the normative record and flows**

In spec/PROTOCOL.md, define:

~~~text
the nine required First-Admission Record fields
the logical key (organizationId, signingHash)
the separate admission diagnostic stage
authoritative lookup and atomic append-or-return-existing
returned-record validation after append
first-admission current Registry evidence
historical replay with retained Registry history
exact Organization, kind, hash, key, Principal, and acceptedBy bindings
validFrom <= t, t < validUntil, and t < revokedAt
Event self-anchoring prohibition
AUTH_INVALID_SIGNATURE mapping for every admission failure
~~~

State explicitly that the record is not a Signed Document, has no signature, and does not authenticate itself.

- [ ] **Step 2: Update the schema/version and conformance sections**

Change the normative Schema count from 21 to 22, list first-admission-record.schema.json, change the structural vector total from 56 to 58, and add admission/manifest.json as an independent required behavioral bundle with 5 cases and 30 evaluations.

- [ ] **Step 3: Write admission/README.md**

Document:

~~~text
profileId and manifestVersion
19 artifacts / 5 cases / 30 evaluations
12 complete / 18 rejected
cryptography digest pin
adapter outcomes are test-harness metadata, not a deployed proof format
digest calculation
deterministic regeneration
reference validator command
scope exclusions
~~~

Include these exact commands:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git diff --exit-code -- admission
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
~~~

- [ ] **Step 4: Preserve the cryptography README boundary**

Update cryptography/README.md only to link the independent Admission bundle. Keep every cryptography count, digest rule, and six-stage success meaning unchanged.

- [ ] **Step 5: Update all seven root READMEs**

Each README must state:

~~~text
22 normative Schemas
58 structural vectors
22 cryptography cases / 62 evaluations
5 Admission cases / 30 evaluations
Admission is separate from cryptographic verification
Command freshness and signer authorization remain outside this slice
~~~

Preserve each file's existing language switcher and code fences.

- [ ] **Step 6: Add the Admission CI job**

Append to .github/workflows/validate.yml:

~~~yaml
  admission-artifacts:
    name: First-admission and historical-trust vectors
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12.13"
      - uses: astral-sh/setup-uv@v6
        with:
          version: "0.11.21"
          enable-cache: true
          cache-dependency-glob: requirements-cryptography.lock
      - run: >-
          uv pip install --system --require-hashes --no-deps --only-binary :all: --strict
          --requirements requirements-cryptography.lock
      - run: python scripts/generate_admission_vectors.py
      - run: git diff --exit-code -- admission
      - run: python scripts/validate_admission_vectors.py
~~~

- [ ] **Step 7: Run the complete protocol gate**

Run:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/check_repository_policy.py
"$MW_CRYPTO_PYTHON" scripts/validate_protocol.py
"$MW_CRYPTO_PYTHON" scripts/generate_crypto_vectors.py
git diff --exit-code -- cryptography
"$MW_CRYPTO_PYTHON" scripts/validate_crypto_vectors.py
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git diff --exit-code -- admission
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
git diff --check
~~~

Expected:

~~~text
repository policy passes
22 schemas / 58 structural vectors
22 cryptography cases / 62 evaluations / unchanged digest
19 Admission artifacts / 5 cases / 30 evaluations / 12 complete / 18 rejected
no whitespace errors
~~~

- [ ] **Step 8: Commit protocol documentation and CI**

Run:

~~~bash
git add admission/README.md spec/PROTOCOL.md cryptography/README.md \
  README.md README.de.md README.es.md README.fr.md README.ja.md \
  README.zh-CN.md README.zh-TW.md .github/workflows/validate.yml
git commit -m "docs(protocol): specify admission trust boundary"
~~~

### Task 6: Merge protocol first and derive the only valid SDK pin

**Files:**

- Read: all protocol changes
- Produce: /tmp/mw-first-admission-sdk-pin.json
- Produce: /tmp/mw-first-admission-protocol-archive-root.txt

- [ ] **Step 1: Reconfirm revision and inspect the exact feature diff**

Run:

~~~bash
rg -n "MW-V1-2026-07-30-R1" docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md
git status --short --branch
git diff --stat origin/main...HEAD
git log --oneline origin/main..HEAD
~~~

Expected: only the approved First-Admission and historical-trust slice is present and the worktree is clean.

- [ ] **Step 2: Push the protocol branch**

Run:

~~~bash
git push -u origin feat/first-admission-historical-trust
~~~

- [ ] **Step 3: Create the protocol pull request**

Run:

~~~bash
gh pr create \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat(protocol): add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1: normative First-Admission Record, 58 structural vectors, independent 30-evaluation Admission bundle, reference validation, and unchanged 62-evaluation cryptography semantics."
~~~

- [ ] **Step 4: Require exact feature-head CI**

Run:

~~~bash
PROTOCOL_FEATURE_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/missionweaveprotocol --watch
gh run list --repo MissionWeaveProtocol/missionweaveprotocol \
  --commit "$PROTOCOL_FEATURE_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Expected: Protocol validation succeeds for the exact feature SHA, including the new Admission job.

- [ ] **Step 5: Merge without deleting the worktree or branch**

Run:

~~~bash
PROTOCOL_PR=$(gh pr list --repo MissionWeaveProtocol/missionweaveprotocol \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$PROTOCOL_PR"
gh pr merge "$PROTOCOL_PR" --repo MissionWeaveProtocol/missionweaveprotocol --squash
PROTOCOL_MAIN_SHA=$(gh pr view "$PROTOCOL_PR" \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --json mergeCommit --jq .mergeCommit.oid)
git fetch origin
test "$PROTOCOL_MAIN_SHA" = "$(git rev-parse origin/main)"
~~~

Expected: the pull request is merged, the GitHub-reported squash merge commit equals `origin/main`, and the original implementation worktree remains present. Do not use feature-commit ancestry as proof because a squash merge does not preserve that ancestry.

- [ ] **Step 6: Require exact merged-main CI**

Run:

~~~bash
PROTOCOL_MAIN_SHA=$(git rev-parse origin/main)
PROTOCOL_RUN_ID=""
while test -z "$PROTOCOL_RUN_ID"
do
  PROTOCOL_RUN_ID=$(gh run list \
    --repo MissionWeaveProtocol/missionweaveprotocol \
    --branch main --commit "$PROTOCOL_MAIN_SHA" --event push --limit 20 \
    --json databaseId,headSha --jq '.[0].databaseId // empty')
  if test -z "$PROTOCOL_RUN_ID"; then sleep 10; fi
done
gh run watch "$PROTOCOL_RUN_ID" \
  --repo MissionWeaveProtocol/missionweaveprotocol --exit-status
gh run view "$PROTOCOL_RUN_ID" \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --json databaseId,headSha,status,conclusion,workflowName,event \
  > /tmp/mw-first-admission-protocol-main-ci.json
test "$PROTOCOL_MAIN_SHA" = "$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-protocol-main-ci.json"))["headSha"])')"
test "success" = "$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-protocol-main-ci.json"))["conclusion"])')"
~~~

Expected: the exact `PROTOCOL_MAIN_SHA` push run concludes `success`.

- [ ] **Step 7: Derive all pin values from merged origin/main**

Run:

~~~bash
PROTOCOL_MAIN_SHA=$(git rev-parse origin/main)
MW_PROTOCOL_ARCHIVE_ROOT=$(mktemp -d /tmp/mw-first-admission-protocol-main.XXXXXX)
export MW_PROTOCOL_ARCHIVE_ROOT PROTOCOL_MAIN_SHA
printf '%s\n' "$MW_PROTOCOL_ARCHIVE_ROOT" \
  > /tmp/mw-first-admission-protocol-archive-root.txt
git archive "$PROTOCOL_MAIN_SHA" | tar -x -C "$MW_PROTOCOL_ARCHIVE_ROOT"
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["MW_PROTOCOL_ARCHIVE_ROOT"])
commit = os.environ["PROTOCOL_MAIN_SHA"]


def json_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def tree_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


schema_paths = json_files(root / "schemas")
conformance_paths = json_files(root / "conformance")
cryptography_manifest = json.loads(
    (root / "cryptography/manifest.json").read_text(encoding="utf-8")
)
admission_manifest = json.loads(
    (root / "admission/manifest.json").read_text(encoding="utf-8")
)
cryptography_evaluations = sum(
    len(case["evaluations"]) for case in cryptography_manifest["cases"]
)
admission_evaluations = sum(
    len(case["evaluations"]) for case in admission_manifest["cases"]
)

pin = {
    "repository": "https://github.com/missionweaveprotocol/missionweaveprotocol",
    "commit": commit,
    "protocolVersion": "0.1",
    "wireNamespace": "missionweaveprotocol",
    "artifacts": {
        "schemas": {
            "path": "schemas",
            "files": len(schema_paths),
            "sha256": tree_digest(schema_paths),
        },
        "conformance": {
            "path": "conformance",
            "files": len(conformance_paths),
            "sha256": tree_digest(conformance_paths),
        },
    },
    "cryptography": {
        "path": "cryptography/manifest.json",
        "sourceCommit": commit,
        "profileId": cryptography_manifest["profileId"],
        "manifestVersion": cryptography_manifest["manifestVersion"],
        "artifactDigest": cryptography_manifest["artifactDigest"],
        "artifactCount": len(cryptography_manifest["artifacts"]),
        "caseCount": len(cryptography_manifest["cases"]),
        "evaluationCount": cryptography_evaluations,
    },
    "admission": {
        "path": "admission/manifest.json",
        "sourceCommit": commit,
        "profileId": admission_manifest["profileId"],
        "manifestVersion": admission_manifest["manifestVersion"],
        "cryptographyArtifactDigest": admission_manifest["cryptography"][
            "artifactDigest"
        ],
        "artifactDigest": admission_manifest["artifactDigest"],
        "artifactCount": len(admission_manifest["artifacts"]),
        "caseCount": len(admission_manifest["cases"]),
        "evaluationCount": admission_evaluations,
    },
    "bundleSha256": tree_digest(sorted(schema_paths + conformance_paths)),
}
assert pin["artifacts"]["schemas"]["files"] == 22
assert pin["artifacts"]["conformance"]["files"] == 59
assert pin["cryptography"]["artifactCount"] == 98
assert pin["cryptography"]["caseCount"] == 22
assert pin["cryptography"]["evaluationCount"] == 62
assert pin["admission"]["artifactCount"] == 19
assert pin["admission"]["caseCount"] == 5
assert pin["admission"]["evaluationCount"] == 30
assert pin["cryptography"]["sourceCommit"] == pin["commit"]
assert pin["admission"]["sourceCommit"] == pin["commit"]
assert (
    pin["admission"]["cryptographyArtifactDigest"]
    == pin["cryptography"]["artifactDigest"]
    == "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
)
Path("/tmp/mw-first-admission-sdk-pin.json").write_text(
    json.dumps(pin, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(pin, indent=2))
PY
~~~

The literal insertion order in `pin` is normative for this slice. Every SDK copies this file byte-for-byte; no SDK serializes or reorders the object independently. Do not derive an SDK pin from the feature or design commit.

- [ ] **Step 8: Record the authoritative protocol evidence**

Run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test -f "$MW_PROTOCOL_ARCHIVE_ROOT/admission/manifest.json"
python -m json.tool /tmp/mw-first-admission-sdk-pin.json
shasum -a 256 /tmp/mw-first-admission-sdk-pin.json
~~~

Expected: the complete SDK pin records one merged protocol commit, 22 Schema JSON files, 59 conformance JSON files containing 58 vectors, cryptography 98/22/62 with the unchanged digest, and Admission 19/5/30. The archive-root file names the exact extracted merged tree used by every SDK task.

### Task 7: Implement and publish the Python Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust
- Create: src/missionweaveprotocol/admission.py
- Create: tests/test_admission.py
- Create: tests/test_admission_conformance.py
- Modify: src/missionweaveprotocol/signed_documents.py
- Modify: src/missionweaveprotocol/__init__.py
- Modify: src/missionweaveprotocol/bundle.py
- Modify: tests/test_signed_documents.py
- Modify: tests/test_protocol_pin.py
- Modify: tests/test_package.py
- Modify: tests/test_localized_readmes.py
- Modify: pyproject.toml
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: README.md
- Modify: README.de.md
- Modify: README.es.md
- Modify: README.fr.md
- Modify: README.ja.md
- Modify: README.zh-CN.md
- Modify: README.zh-TW.md
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the Python worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/python-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/python-sdk rev-parse origin/main)" = \
  "623eadb11ca9a0a17aa527d93035ba3a07ff4666"
git -C /Users/lionelmbp/repos/python-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize merged protocol trees and the normalized pin**

From the Python worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
~~~

Do not edit `PROTOCOL_PIN.json` after the copy. The complete file, including member order, comes from Task 6 and must remain byte-identical across all six SDKs.

- [ ] **Step 3: Write the focused RED tests through the public API**

In tests/test_admission.py, add:

~~~python
@dataclass(frozen=True, slots=True)
class CurrentRegistryFixture:
    resolver: KeyResolver

    def resolve_current(self, request: KeyResolutionRequest) -> KeyRegistrySnapshot:
        return self.resolver.resolve(request)


@pytest.fixture
def current_registry(complete_registry: KeyResolver) -> AdmissionCurrentKeyResolver:
    return CurrentRegistryFixture(complete_registry)


def test_admit_first_returns_only_after_committed_record_validation(
    golden_command: bytes,
    current_registry: AdmissionCurrentKeyResolver,
    trusted_context: TrustedAdmissionContext,
) -> None:
    log = RecordingAdmissionLog.authoritative_absence_then_commit()
    admitted = AdmissionService().admit_first(
        SignedDocumentKind.COMMAND,
        golden_command,
        current_registry,
        log,
        trusted_context,
    )
    assert admitted.record.signing_hash == admitted.verified.signing_hash
    assert log.calls == ["lookup", "append_or_return_existing"]


def test_trusted_time_equal_to_valid_until_is_rejected(
    verified_command: VerifiedSignedDocument,
) -> None:
    context = FixedTrustedAdmissionContext(
        admission_record_id="urn:missionweaveprotocol:admission-record:boundary",
        trusted_accepted_at="2026-07-16T00:00:00Z",
        accepted_by=PrincipalEvidence(
            type="service",
            id="urn:missionweaveprotocol:service:admission",
        ),
    )
    with pytest.raises(AdmissionError) as captured:
        AdmissionService().prepare_first_admission(verified_command, context)
    assert captured.value.wire_error.code is ErrorCode.AUTH_INVALID_SIGNATURE
    assert captured.value.protected_error.stage is AdmissionStage.ADMISSION
    assert captured.value.protected_error.reason == "trusted-time-outside-key-interval"


def test_historical_replay_reruns_crypto_before_lookup(
    tampered_command: bytes,
    historical_registry: KeyResolver,
) -> None:
    log = RecordingAdmissionLog.with_existing_command_record()
    with pytest.raises(SignedDocumentVerificationError):
        AdmissionService().verify_historical_admission(
            SignedDocumentKind.COMMAND,
            tampered_command,
            historical_registry,
            log,
        )
    assert log.calls == []
~~~

The same RED file also defines these exact public-path cases before implementation:

~~~text
test_existing_record_binding_mismatch_is_admission_failure
  verify_historical_admission + key-id-mismatch record -> record-binding-mismatch
test_historical_replay_accepts_later_revocation_history
  verify_historical_admission + registry-later-revocation + valid record -> success, zero append calls
test_admit_first_fails_when_log_is_unavailable
  admit_first + unavailable lookup -> log-unavailable
~~~

Together with the valid first-admission and exclusive-boundary tests above, these are the five focused public API behaviors required by the approved TDD strategy.

- [ ] **Step 4: Run focused tests and prove RED**

Run:

~~~bash
uv run pytest tests/test_admission.py -q
~~~

Expected: collection fails because missionweaveprotocol.admission and the exported API do not exist.

- [ ] **Step 5: Retain exact and parsed key-validity evidence**

Change KeyValidityEvidence in src/missionweaveprotocol/signed_documents.py to:

~~~python
@dataclass(frozen=True, slots=True)
class KeyValidityEvidence:
    valid_from_text: str
    valid_from: ProtectedInstant
    valid_until_text: str | None
    valid_until: ProtectedInstant | None
    revoked_at_text: str | None
    revoked_at: ProtectedInstant | None
~~~

Carry the original Registry text into the selected evidence while retaining the exact existing parsed comparison behavior. Add tests asserting lowercase t/z and numerical-offset text are preserved byte-for-byte.

- [ ] **Step 6: Add the Python public types and separate error family**

In src/missionweaveprotocol/admission.py, define:

~~~python
class AdmissionStage(StrEnum):
    ADMISSION = "admission"


@dataclass(frozen=True, slots=True)
class ProtectedAdmissionError:
    stage: AdmissionStage
    reason: str


class AdmissionError(ValueError):
    def __init__(self, reason: str) -> None:
        self.wire_error = WireVerificationError(ErrorCode.AUTH_INVALID_SIGNATURE)
        self.protected_error = ProtectedAdmissionError(
            AdmissionStage.ADMISSION,
            reason,
        )
        super().__init__(
            f"{self.wire_error.code.value}: signed document admission rejected"
        )


@dataclass(frozen=True, slots=True)
class AdmissionContextValue:
    admission_record_id: str
    trusted_accepted_at: str
    accepted_by: PrincipalEvidence


@runtime_checkable
class TrustedAdmissionContext(Protocol):
    def issue(
        self,
        organization_id: str,
        signing_hash: str,
    ) -> AdmissionContextValue: ...


@runtime_checkable
class AdmissionCurrentKeyResolver(Protocol):
    def resolve_current(
        self,
        request: KeyResolutionRequest,
    ) -> KeyRegistrySnapshot: ...


@dataclass(frozen=True, slots=True)
class _CurrentResolverAdapter:
    resolver: AdmissionCurrentKeyResolver

    def resolve(self, request: KeyResolutionRequest) -> KeyRegistrySnapshot:
        return self.resolver.resolve_current(request)


@dataclass(frozen=True, slots=True)
class AuthenticatedAdmissionRecord:
    record_bytes: bytes
    authenticated_service: PrincipalEvidence


class AdmissionLookupStatus(StrEnum):
    FOUND = "found"
    AUTHORITATIVE_ABSENCE = "authoritative-absence"


@dataclass(frozen=True, slots=True)
class AdmissionLookup:
    status: AdmissionLookupStatus
    record: AuthenticatedAdmissionRecord | None = None


@runtime_checkable
class AdmissionLog(Protocol):
    def lookup(self, organization_id: str, signing_hash: str) -> AdmissionLookup: ...

    def append_or_return_existing(
        self,
        organization_id: str,
        signing_hash: str,
        candidate_bytes: bytes,
    ) -> AuthenticatedAdmissionRecord: ...
~~~

Adapter unavailability, indeterminate state, authentication failure, integrity failure, conflict, and commit failure are raised as AdmissionLogError with a stable reason. AdmissionService catches it and converts it to AdmissionError without exposing adapter text on the wire.

- [ ] **Step 7: Add immutable result values and service signatures**

Add:

~~~python
@dataclass(frozen=True, slots=True)
class FirstAdmissionRecord:
    protocol_version: str
    admission_record_id: str
    organization_id: str
    document_kind: SignedDocumentKind
    signing_hash: str
    key_id: str
    principal: PrincipalEvidence
    trusted_accepted_at: str
    trusted_accepted_instant: ProtectedInstant
    accepted_by: PrincipalEvidence
    raw_bytes: bytes


@dataclass(frozen=True, slots=True)
class PreparedFirstAdmission:
    verified: VerifiedSignedDocument
    record: FirstAdmissionRecord


@dataclass(frozen=True, slots=True)
class AdmittedSignedDocument:
    verified: VerifiedSignedDocument
    record: FirstAdmissionRecord


class AdmissionService:
    def prepare_first_admission(
        self,
        verified: VerifiedSignedDocument,
        trusted_context: TrustedAdmissionContext,
    ) -> PreparedFirstAdmission: ...

    def admit_first(
        self,
        kind: SignedDocumentKind,
        document_bytes: bytes,
        current_key_resolver: AdmissionCurrentKeyResolver,
        admission_log: AdmissionLog,
        trusted_context: TrustedAdmissionContext,
    ) -> AdmittedSignedDocument: ...

    def verify_historical_admission(
        self,
        kind: SignedDocumentKind,
        document_bytes: bytes,
        historical_key_resolver: KeyResolver,
        admission_log: AdmissionLog,
    ) -> AdmittedSignedDocument: ...
~~~

- [ ] **Step 8: Implement the minimal GREEN flow in the required order**

For `admit_first`, wrap `current_key_resolver` in `_CurrentResolverAdapter` and pass that adapter to `SignedDocumentCodec.verify`; this is the only bridge from admission-current evidence to the unchanged cryptographic `KeyResolver` input. For `verify_historical_admission`, pass `historical_key_resolver` directly. On found records, validate strict JSON, the normative Schema, exact bindings, acceptedBy equality, and the selected validity interval. On absence, call `trusted_context.issue`, prepare canonical UTF-8 JSON bytes preserving `trustedAcceptedAt` text, call `append_or_return_existing`, then validate the returned record again. Never return `AdmittedSignedDocument` from `prepare_first_admission`.

- [ ] **Step 9: Run the focused tests and prove GREEN**

Run:

~~~bash
uv run pytest tests/test_admission.py tests/test_signed_documents.py -q
~~~

Expected: the new Admission tests and all existing Signed Document tests pass.

- [ ] **Step 10: Execute all 30 protocol evaluations through AdmissionService**

In tests/test_admission_conformance.py, parse admission/manifest.json, map its explicit adapter outcomes to a test AdmissionLog, and call only:

~~~python
service.admit_first(...)
service.verify_historical_admission(...)
~~~

Assert:

~~~python
assert totals == {
    "evaluations": 30,
    "complete": 12,
    "rejected": 18,
    "admission_failures": 18,
}
~~~

For every rejection, assert stage admission, wire AUTH_INVALID_SIGNATURE, and the declared protected reason.

- [ ] **Step 11: Add and verify the Admission bundle pin**

Extend src/missionweaveprotocol/bundle.py with AdmissionPin, AdmissionBundleSummary, and verify_admission_bundle. Reuse the existing safe-path, strict-JSON, byte-length, SHA-256, and RFC 8785 machinery. Approved artifact roots are admission and schemas. Reject admission/README.md and admission/manifest.json as digest artifacts. Require the Admission manifest's cryptography digest to equal the cryptography pin.

- [ ] **Step 12: Package admission/ and test the built wheel**

Add to pyproject.toml:

~~~toml
"admission" = "missionweaveprotocol/admission"
~~~

Extend tests/test_package.py and the CI installed-wheel block to assert:

~~~python
from missionweaveprotocol import (
    AdmissionService,
    verify_admission_bundle,
)

summary = verify_admission_bundle()
assert summary.artifact_count == 19
assert summary.case_count == 5
assert summary.evaluation_count == 30
~~~

The installed consumer must load the packaged Command, Registry, and Admission record resources and complete one public admit_first call.

- [ ] **Step 13: Export and document the public API**

Export all public Admission types from src/missionweaveprotocol/__init__.py. Update all seven READMEs with one equivalent example and the merged protocol commit/digest. Extend tests/test_localized_readmes.py so every translation links admission/README.md and mentions 30 evaluations.

- [ ] **Step 14: Run the complete Python gate**

Run:

~~~bash
uv sync --extra dev --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run missionweaveprotocol-conformance --root .
uv build
uv run pytest tests/test_package.py -q
git diff --check
~~~

Expected: lint, format, typing, all tests, 58/58 structural conformance, wheel/sdist creation, packaged Admission verification, and public installed-consumer admission all pass.

- [ ] **Step 15: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/python-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 against the merged protocol Admission bundle; preserves six-stage verify semantics and executes all 30 Admission evaluations."
PYTHON_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/python-sdk --watch
gh run list --repo MissionWeaveProtocol/python-sdk --commit "$PYTHON_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Do not merge in this task; Task 14 merges all six SDKs after the cross-language branch-head audit.

### Task 8: Implement and publish the TypeScript Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust
- Create: src/admission.ts
- Create: tests/admission.test.ts
- Create: tests/admission-conformance.test.ts
- Modify: src/signed-document-codec.ts
- Modify: src/index.ts
- Modify: scripts/protocol-bundle.mjs
- Modify: scripts/check-protocol-pin.mjs
- Modify: scripts/check-docs.mjs
- Modify: scripts/smoke-package.mjs
- Modify: tests/protocol-bundle.test.mjs
- Modify: package.json
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: README.md
- Modify: README.de.md
- Modify: README.es.md
- Modify: README.fr.md
- Modify: README.ja.md
- Modify: README.zh-CN.md
- Modify: README.zh-TW.md
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the TypeScript worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/typescript-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/typescript-sdk rev-parse origin/main)" = \
  "69d5b3056aa80cf208121e04ef7c2be67b86b2d7"
git -C /Users/lionelmbp/repos/typescript-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize the merged bundle and normalized pin**

From the TypeScript worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
~~~

Then add `admission` to the `package.json` files array:

~~~json
"files": [
  "dist",
  "schemas",
  "conformance",
  "cryptography",
  "admission",
  "examples",
  "PROTOCOL_PIN.json",
  "LICENSE",
  "README*.md"
]
~~~

- [ ] **Step 3: Write the TypeScript RED tests**

In tests/admission.test.ts, add:

~~~typescript
const currentRegistryResolver: AdmissionCurrentKeyResolver = {
  resolveCurrent(request: KeyResolutionRequest): KeyRegistrySnapshot {
    return completeRegistryResolver.resolve(request);
  },
};

it("validates the committed record before returning admitted evidence", async () => {
  const log = RecordingAdmissionLog.authoritativeAbsenceThenCommit();
  const admitted = await new AdmissionService().admitFirst(
    SignedDocumentKind.Command,
    goldenCommand,
    currentRegistryResolver,
    log,
    fixedTrustedContext,
  );
  expect(admitted.record.signingHash).toBe(admitted.verified.signingHash);
  expect(log.calls).toEqual(["lookup", "appendOrReturnExisting"]);
});

it("rejects trusted acceptance at validUntil", async () => {
  await expect(
    new AdmissionService().prepareFirstAdmission(
      verifiedCommand,
      fixedContext("2026-07-16T00:00:00Z"),
    ),
  ).rejects.toMatchObject({
    wireCode: "AUTH_INVALID_SIGNATURE",
    auditDetail: {
      stage: "admission",
      reason: "trusted-time-outside-key-interval",
    },
  });
});
~~~

The RED suite also defines:

~~~text
"rejects an existing key-ID mismatch as record-binding-mismatch"
  verifyHistoricalAdmission + key-id-mismatch record
"accepts historical replay with retained later-revocation history"
  verifyHistoricalAdmission + registry-later-revocation + valid record; append count 0
"maps an unavailable Admission Log to log-unavailable"
  admitFirst + unavailable lookup
~~~

All three call `AdmissionService` directly and assert `wireCode: AUTH_INVALID_SIGNATURE` plus `auditDetail.stage: admission` on rejection.

- [ ] **Step 4: Run focused tests and prove RED**

Run:

~~~bash
npm ci
npx vitest run tests/admission.test.ts
~~~

Expected: FAIL because src/admission.ts and its exports do not exist.

- [ ] **Step 5: Preserve Registry boundary text in verified evidence**

Change ResolvedSigningKey to retain:

~~~typescript
export interface ResolvedSigningKey {
  readonly organizationId: string;
  readonly keyId: string;
  readonly principal: Principal;
  readonly algorithm: "Ed25519";
  readonly publicKey: string;
  readonly validFromText: string;
  readonly validFrom: Rfc3339Instant;
  readonly validUntilText: string | null;
  readonly validUntil: Rfc3339Instant | null;
  readonly revokedAtText: string | null;
  readonly revokedAt: Rfc3339Instant | null;
}
~~~

Carry the earliest effective boundary text with the parsed instant. Do not normalize or recreate text.

- [ ] **Step 6: Add public Admission interfaces and errors**

In src/admission.ts, define:

~~~typescript
export type AdmissionReason =
  | "record-missing"
  | "record-binding-mismatch"
  | "trusted-time-outside-key-interval"
  | "malformed-trusted-time"
  | "record-conflict"
  | "record-schema-invalid"
  | "log-authentication-failed"
  | "append-integrity-not-established"
  | "log-unavailable"
  | "log-indeterminate"
  | "commit-failed"
  | "event-self-anchoring";

export class AdmissionError extends Error {
  public readonly wireCode = "AUTH_INVALID_SIGNATURE" as const;
  public readonly auditDetail: {
    readonly stage: "admission";
    readonly reason: AdmissionReason;
  };
}

export interface AdmissionContextValue {
  readonly admissionRecordId: string;
  readonly trustedAcceptedAt: string;
  readonly acceptedBy: Principal;
}

export interface TrustedAdmissionContext {
  issue(
    organizationId: string,
    signingHash: string,
  ): Promise<AdmissionContextValue> | AdmissionContextValue;
}

export interface AdmissionCurrentKeyResolver {
  resolveCurrent(request: KeyResolutionRequest): KeyRegistrySnapshot;
}

class CurrentResolverAdapter implements KeyResolver {
  public constructor(
    private readonly current: AdmissionCurrentKeyResolver,
  ) {}

  public resolve(request: KeyResolutionRequest): KeyRegistrySnapshot {
    return this.current.resolveCurrent(request);
  }
}

export interface AuthenticatedAdmissionRecord {
  readonly recordBytes: Uint8Array;
  readonly authenticatedService: Principal;
}

export type AdmissionLookup =
  | {
      readonly status: "found";
      readonly record: AuthenticatedAdmissionRecord;
    }
  | {
      readonly status: "authoritative-absence";
    };

export interface AdmissionLog {
  lookup(
    organizationId: string,
    signingHash: string,
  ): Promise<AdmissionLookup>;

  appendOrReturnExisting(
    organizationId: string,
    signingHash: string,
    candidateBytes: Uint8Array,
  ): Promise<AuthenticatedAdmissionRecord>;
}
~~~

- [ ] **Step 7: Add immutable results and service signatures**

Add:

~~~typescript
export interface FirstAdmissionRecord {
  readonly protocolVersion: "0.1";
  readonly admissionRecordId: string;
  readonly organizationId: string;
  readonly documentKind: SignedDocumentKind;
  readonly signingHash: string;
  readonly keyId: string;
  readonly principal: Principal;
  readonly trustedAcceptedAt: string;
  readonly acceptedBy: Principal & { readonly type: "service" };
}

export interface PreparedFirstAdmission {
  readonly verified: VerifiedSignedDocument;
  readonly record: FirstAdmissionRecord;
  readonly recordBytes: Uint8Array;
}

export interface AdmittedSignedDocument {
  readonly verified: VerifiedSignedDocument;
  readonly record: FirstAdmissionRecord;
  readonly recordBytes: Uint8Array;
}

export class AdmissionService {
  public prepareFirstAdmission(
    verified: VerifiedSignedDocument,
    trustedContext: TrustedAdmissionContext,
  ): Promise<PreparedFirstAdmission>;

  public admitFirst(
    kind: SignedDocumentKind,
    documentBytes: Uint8Array,
    currentRegistry: AdmissionCurrentKeyResolver,
    admissionLog: AdmissionLog,
    trustedContext: TrustedAdmissionContext,
  ): Promise<AdmittedSignedDocument>;

  public verifyHistoricalAdmission(
    kind: SignedDocumentKind,
    documentBytes: Uint8Array,
    historicalRegistry: KeyResolver,
    admissionLog: AdmissionLog,
  ): Promise<AdmittedSignedDocument>;
}
~~~

- [ ] **Step 8: Implement the required order and strict record validation**

In `admitFirst`, construct `new CurrentResolverAdapter(currentRegistry)` and pass it to `SignedDocumentCodec.verify` synchronously before any awaitable Admission Log call. In `verifyHistoricalAdmission`, pass `historicalRegistry` directly to the unchanged verifier. Parse returned record bytes with the existing strict parser, validate `first-admission-record.schema.json` through `SchemaCatalog`, preserve `trustedAcceptedAt` text, compare parsed instants with `compareRfc3339Instants`, deep-freeze public objects, and return defensive `Uint8Array` copies.

- [ ] **Step 9: Run focused GREEN tests**

Run:

~~~bash
npx vitest run tests/admission.test.ts tests/signed-document-codec.test.ts
~~~

Expected: all focused Admission and existing Signed Document tests pass.

- [ ] **Step 10: Run all 30 manifest evaluations through the public service**

In tests/admission-conformance.test.ts, use an explicit fixture log and context, call only admitFirst or verifyHistoricalAdmission, and assert 30/12/18 plus the declared stage, wire code, reason, and call order.

- [ ] **Step 11: Verify and package the Admission bundle**

Extend scripts/protocol-bundle.mjs with verifyAdmissionBundle using the existing strict JSON, safe path, RFC 8785, and hash functions. Require 19/5/30 and cryptography digest equality. Extend tests/protocol-bundle.test.mjs, scripts/check-protocol-pin.mjs, and scripts/smoke-package.mjs. The packed npm consumer must import AdmissionService from the package root and complete one first admission using packaged artifacts.

- [ ] **Step 12: Export and document the API**

Export src/admission.ts from src/index.ts. Update all seven READMEs and scripts/check-docs.mjs with the merged commit, Admission digest, 30 evaluations, and one language-equivalent public example.

- [ ] **Step 13: Run the complete TypeScript gate**

Run:

~~~bash
npm run check
npm pack --dry-run
git diff --check
~~~

Expected: policy, pin, docs, ESLint, Prettier, type checks, all tests, build, publint, package smoke, and packed public Admission consumer pass.

- [ ] **Step 14: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/typescript-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 through the public asynchronous Admission API and all 30 protocol evaluations."
TYPESCRIPT_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/typescript-sdk --watch
gh run list --repo MissionWeaveProtocol/typescript-sdk --commit "$TYPESCRIPT_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Do not merge in this task.

### Task 9: Implement and publish the Go Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust
- Create: admission.go
- Create: admission_test.go
- Create: admission_conformance_test.go
- Create: scripts/smoke_external_consumer.sh
- Modify: signed_document_verification.go
- Modify: bundle.go
- Modify: bundle_test.go
- Modify: bundle_internal_test.go
- Modify: conformance_test.go
- Modify: internal/cmd/bundle-smoke/main.go
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: README.md
- Modify: README.de.md
- Modify: README.es.md
- Modify: README.fr.md
- Modify: README.ja.md
- Modify: README.zh-CN.md
- Modify: README.zh-TW.md
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the Go worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/go-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/go-sdk rev-parse origin/main)" = \
  "351c7ed0f6e5e71f2814bb0da7f33a6d82a0e218"
git -C /Users/lionelmbp/repos/go-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize the merged protocol trees and generated pin**

From the Go worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
git diff --exit-code -- go.mod go.sum
~~~

Do not edit `go.mod` or `go.sum` for bundle synchronization.

- [ ] **Step 3: Write Go RED tests for atomic completion and historical order**

In admission_test.go, add:

~~~go
func TestAdmitFirstValidatesCommittedRecordBeforeReturning(t *testing.T) {
	log := newRecordingAdmissionLog(authoritativeAbsenceThenCommit)
	admitted, err := NewAdmissionService().AdmitFirst(
		SignedDocumentCommand,
		goldenCommand(t),
		currentRegistry(t),
		log,
		fixedTrustedContext(),
	)
	if err != nil {
		t.Fatal(err)
	}
	if admitted.Record().SigningHash() != admitted.Verified().SigningHash() {
		t.Fatal("admitted record does not bind the six-stage signing hash")
	}
	wantCalls := []string{"lookup", "append-or-return-existing"}
	if !slices.Equal(wantCalls, log.calls) {
		t.Fatalf("unexpected call order: want %v, got %v", wantCalls, log.calls)
	}
}

func TestHistoricalReplayVerifiesBeforeLookup(t *testing.T) {
	log := newRecordingAdmissionLog(foundCommandRecord)
	_, err := NewAdmissionService().VerifyHistoricalAdmission(
		SignedDocumentCommand,
		tamperedCommand(t),
		historicalRegistry(t),
		log,
	)
	var verification *SignedDocumentVerificationError
	if !errors.As(err, &verification) {
		t.Fatalf("expected cryptographic failure, got %v", err)
	}
	if len(log.calls) != 0 {
		t.Fatalf("Admission Log was consulted before six-stage verification")
	}
}
~~~

Add these focused tests to `admission_test.go` before the RED run:

~~~text
TestHistoricalExistingRecordBindingMismatch
  VerifyHistoricalAdmission + key-id-mismatch record -> AdmissionRecordBindingMismatch
TestHistoricalReplayAcceptsLaterRevocationHistory
  VerifyHistoricalAdmission + registry-later-revocation + valid record -> success, zero append calls
TestAdmitFirstFailsWhenLogUnavailable
  AdmitFirst + unavailable lookup -> AdmissionLogUnavailable
TestTrustedTimeEqualValidUntilFailsAdmission
  PrepareFirstAdmission at validUntil -> AdmissionTrustedTimeOutsideKeyInterval
~~~

Each rejected test asserts `WireAuthInvalidSignature` and diagnostic stage `admission` through the public error accessors.

Import the standard-library `slices` package. Do not add `google/go-cmp` or any other comparison dependency.

- [ ] **Step 4: Run focused tests and prove RED**

Run:

~~~bash
go test ./... -run 'TestAdmitFirst|TestHistoricalReplay' -count=1
~~~

Expected: FAIL because AdmissionService is undefined.

- [ ] **Step 5: Retain exact Registry boundary text**

Extend ResolvedKeyEvidence:

~~~go
type ResolvedKeyEvidence struct {
	organizationID string
	keyID          string
	principal      Principal
	algorithm      string
	publicKeyText  string
	publicKeyBytes []byte
	validFromText  string
	validFrom      RFC3339Instant
	validUntilText *string
	validUntil     *RFC3339Instant
	revokedAtText  *string
	revokedAt      *RFC3339Instant
}

func (key ResolvedKeyEvidence) ValidFromText() string { return key.validFromText }

func (key ResolvedKeyEvidence) ValidUntilText() (string, bool) {
	if key.validUntilText == nil {
		return "", false
	}
	return *key.validUntilText, true
}

func (key ResolvedKeyEvidence) RevokedAtText() (string, bool) {
	if key.revokedAtText == nil {
		return "", false
	}
	return *key.revokedAtText, true
}
~~~

Retain the text belonging to the earliest effective boundary and deep-copy the text pointers in clone.

- [ ] **Step 6: Add an explicit current-Registry trust seam**

Define:

~~~go
type AdmissionCurrentKeyResolver interface {
	ResolveCurrent(request KeyResolutionRequest) (KeyRegistrySnapshot, error)
}

type currentResolverAdapter struct {
	resolver AdmissionCurrentKeyResolver
}

func (adapter currentResolverAdapter) Resolve(
	request KeyResolutionRequest,
) (KeyRegistrySnapshot, error) {
	return adapter.resolver.ResolveCurrent(request)
}
~~~

AdmitFirst accepts AdmissionCurrentKeyResolver. VerifyHistoricalAdmission continues to accept the existing KeyResolver. This method distinction is the trusted assertion that evidence is current and applicable; do not add a boolean field to KeyRegistrySnapshot.

- [ ] **Step 7: Add Go Admission types and errors**

In admission.go, define:

~~~go
type AdmissionReason string

const (
	AdmissionRecordMissing                 AdmissionReason = "record-missing"
	AdmissionRecordBindingMismatch         AdmissionReason = "record-binding-mismatch"
	AdmissionTrustedTimeOutsideKeyInterval AdmissionReason = "trusted-time-outside-key-interval"
	AdmissionMalformedTrustedTime          AdmissionReason = "malformed-trusted-time"
	AdmissionRecordConflict                AdmissionReason = "record-conflict"
	AdmissionRecordSchemaInvalid           AdmissionReason = "record-schema-invalid"
	AdmissionLogAuthenticationFailed       AdmissionReason = "log-authentication-failed"
	AdmissionAppendIntegrityNotEstablished AdmissionReason = "append-integrity-not-established"
	AdmissionLogUnavailable                AdmissionReason = "log-unavailable"
	AdmissionLogIndeterminate              AdmissionReason = "log-indeterminate"
	AdmissionCommitFailed                  AdmissionReason = "commit-failed"
	AdmissionEventSelfAnchoring            AdmissionReason = "event-self-anchoring"
)

type AdmissionDiagnostic struct {
	reason AdmissionReason
}

func (diagnostic AdmissionDiagnostic) Stage() string { return "admission" }
func (diagnostic AdmissionDiagnostic) Reason() AdmissionReason { return diagnostic.reason }

type AdmissionError struct {
	diagnostic AdmissionDiagnostic
}

func (failure *AdmissionError) Error() string {
	return "signed document admission failed: AUTH_INVALID_SIGNATURE"
}
func (failure *AdmissionError) WireCode() WireErrorCode {
	return WireAuthInvalidSignature
}
func (failure *AdmissionError) ProtectedDiagnostic() AdmissionDiagnostic {
	return failure.diagnostic
}
~~~

- [ ] **Step 8: Add adapters and immutable result accessors**

Define:

~~~go
type AdmissionContextValue struct {
	AdmissionRecordID string
	TrustedAcceptedAt string
	AcceptedBy        Principal
}

type TrustedAdmissionContext interface {
	Issue(organizationID, signingHash string) (AdmissionContextValue, error)
}

type AuthenticatedAdmissionRecord struct {
	RecordBytes          []byte
	AuthenticatedService Principal
}

type AdmissionLookup struct {
	Record               *AuthenticatedAdmissionRecord
	AuthoritativeAbsence bool
}

type AdmissionLog interface {
	Lookup(organizationID, signingHash string) (AdmissionLookup, error)
	AppendOrReturnExisting(
		organizationID string,
		signingHash string,
		candidateBytes []byte,
	) (AuthenticatedAdmissionRecord, error)
}
~~~

AdmissionLookup is constructed only by trusted adapters; reject both Record non-nil plus AuthoritativeAbsence true and Record nil plus false. Adapter failure types carry the specific protected reason. Do not expose authentication or integrity booleans.

Add FirstAdmissionRecord, PreparedFirstAdmission, and AdmittedSignedDocument with unexported fields, defensive byte copies, and exported accessors.

- [ ] **Step 9: Add AdmissionService methods**

Use these signatures:

~~~go
func (service *AdmissionService) PrepareFirstAdmission(
	verified *VerifiedSignedDocument,
	trustedContext TrustedAdmissionContext,
) (*PreparedFirstAdmission, error)

func (service *AdmissionService) AdmitFirst(
	kind SignedDocumentKind,
	documentBytes []byte,
	registry AdmissionCurrentKeyResolver,
	log AdmissionLog,
	trustedContext TrustedAdmissionContext,
) (*AdmittedSignedDocument, error)

func (service *AdmissionService) VerifyHistoricalAdmission(
	kind SignedDocumentKind,
	documentBytes []byte,
	registry KeyResolver,
	log AdmissionLog,
) (*AdmittedSignedDocument, error)
~~~

Implement strict JSON, Schema validation, exact binding checks, interval comparisons, returned-record validation, call-order assertions, and Event self-anchoring detection.

- [ ] **Step 10: Run focused tests and prove GREEN**

Run:

~~~bash
go test ./... -run 'TestAdmitFirst|TestHistoricalReplay|TestTrustedTime|TestAdmissionConflict' -count=1
~~~

Expected: all focused tests pass.

- [ ] **Step 11: Execute all 30 Admission evaluations**

In admission_conformance_test.go, read the embedded admission/manifest.json, map its outcome enums to fake adapters, call the public service, and assert:

~~~go
if evaluations != 30 || complete != 12 || rejected != 18 {
	t.Fatalf(
		"Admission totals are %d/%d/%d; want 30/12/18",
		evaluations,
		complete,
		rejected,
	)
}
~~~

- [ ] **Step 12: Embed and verify the Admission bundle**

Change the embed declaration to include admission:

~~~go
//go:embed PROTOCOL_PIN.json schemas/*.json conformance/manifest.json conformance/vectors/valid/*.json conformance/vectors/invalid/*.json cryptography admission
var embeddedProtocolBundle embed.FS
~~~

Add AdmissionPin to ProtocolPin, VerifyAdmissionBundle, AdmissionBundleSummary, safe admission/schema artifact routing, 19/5/30 checks, and cryptography digest equality. Extend ReadProtocolFile and bundle tests.

- [ ] **Step 13: Add a real external-module installed consumer**

Create scripts/smoke_external_consumer.sh. It must:

~~~text
create a mktemp directory
initialize a new Go module
replace github.com/missionweaveprotocol/go-sdk with the current checkout
compile a main package importing only the public module
verify both bundles
construct public test adapters
perform one public AdmitFirst call using embedded fixtures
run go mod tidy and go run .
remove only the mktemp directory on exit
~~~

Add the script to CI after go build ./....

- [ ] **Step 14: Update all seven READMEs**

Document the current-Registry seam for first admission, the historical KeyResolver path, 30 evaluations, merged pin, and one public example. Keep cryptographic Verify documentation unchanged.

- [ ] **Step 15: Run the complete Go gate**

Run:

~~~bash
go mod tidy
git diff --exit-code -- go.mod go.sum
go run ./internal/cmd/repository-policy
test -z "$(gofmt -l .)"
go vet ./...
go test -race -cover ./...
go run ./cmd/missionweaveprotocol-conformance
go run ./cmd/missionweaveprotocol-conformance --root .
go build ./...
scripts/smoke_external_consumer.sh
git diff --check
~~~

- [ ] **Step 16: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/go-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 with an explicit current-Registry seam, public Admission API, and all 30 evaluations."
GO_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/go-sdk --watch
gh run list --repo MissionWeaveProtocol/go-sdk --commit "$GO_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Do not merge in this task.

### Task 10: Implement and publish the Rust Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust
- Create: src/admission.rs
- Create: tests/admission.rs
- Modify: src/signed_document.rs
- Modify: src/lib.rs
- Modify: src/bundle.rs
- Modify: Cargo.toml
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: README.md
- Modify: README.de.md
- Modify: README.es.md
- Modify: README.fr.md
- Modify: README.ja.md
- Modify: README.zh-CN.md
- Modify: README.zh-TW.md
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the Rust worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/rust-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/rust-sdk rev-parse origin/main)" = \
  "39ddee963a1d33d0f73e3217210ff4628f140ffa"
git -C /Users/lionelmbp/repos/rust-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize the merged bundle and pin**

From the Rust worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
~~~

Add `admission/**` to the `Cargo.toml` include list. Keep `Cargo.lock` unchanged unless compilation proves a new dependency is necessary; the planned implementation uses existing `serde`, `serde_json`, `jsonschema`, and canonicalization dependencies.

- [ ] **Step 3: Write Rust RED integration tests**

In tests/admission.rs, add:

~~~rust
#[test]
fn first_admission_returns_only_the_validated_committed_record() {
    let log = RecordingAdmissionLog::authoritative_absence_then_commit();
    let admitted = AdmissionService::new()
        .admit_first(
            SignedDocumentKind::Command,
            &golden_command(),
            &current_registry(),
            &log,
            &fixed_trusted_context(),
        )
        .expect("first admission");
    assert_eq!(
        admitted.record().signing_hash(),
        admitted.verified().signing_hash()
    );
    assert_eq!(log.calls(), ["lookup", "append-or-return-existing"]);
}

#[test]
fn historical_replay_never_creates_a_missing_record() {
    let log = RecordingAdmissionLog::authoritative_absence();
    let error = AdmissionService::new()
        .verify_historical_admission(
            SignedDocumentKind::Command,
            &golden_command(),
            &historical_registry(),
            &log,
        )
        .expect_err("missing historical record must fail");
    assert_eq!(error.wire_code(), "AUTH_INVALID_SIGNATURE");
    assert_eq!(error.diagnostic().stage(), "admission");
    assert_eq!(error.diagnostic().reason(), AdmissionReason::RecordMissing);
    assert_eq!(log.append_calls(), 0);
}
~~~

Add these focused public-path tests to the same integration test before the RED run:

~~~text
existing_record_binding_mismatch_is_rejected
  verify_historical_admission + key-id-mismatch record -> AdmissionReason::RecordBindingMismatch
historical_replay_accepts_retained_later_revocation
  verify_historical_admission + registry-later-revocation + valid record -> success, zero append calls
unavailable_log_fails_first_admission
  admit_first + unavailable lookup -> AdmissionReason::LogUnavailable
trusted_time_equal_valid_until_is_rejected
  prepare_first_admission at validUntil -> AdmissionReason::TrustedTimeOutsideKeyInterval
~~~

Every rejected case asserts wire code `AUTH_INVALID_SIGNATURE` and stage `admission`.

- [ ] **Step 4: Run the test and prove RED**

Run:

~~~bash
cargo test --locked --test admission
~~~

Expected: compile failure because the Admission API is absent.

- [ ] **Step 5: Expose the stable Signed Document kind ID**

Add:

~~~rust
impl SignedDocumentKind {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::AgentCard => "agent-card",
            Self::Approval => "approval",
            Self::Artifact => "artifact",
            Self::Command => "command",
            Self::ContextPackage => "context-package",
            Self::Event => "event",
            Self::Evidence => "evidence",
            Self::ExtensionProfile => "extension-profile",
            Self::GroupSnapshot => "group-snapshot",
        }
    }
}
~~~

Do not change the existing private profile selection or verification stage enum. Rust already retains exact and parsed validity boundary evidence; add regression assertions instead of changing that representation.

- [ ] **Step 6: Add the current-Registry and Admission adapter traits**

In src/admission.rs, define:

~~~rust
pub trait AdmissionCurrentKeyResolver {
    fn resolve_current(
        &self,
        request: &KeyResolutionRequest,
    ) -> Result<KeyRegistrySnapshot, AdapterError>;
}

pub trait TrustedAdmissionContext {
    fn issue(
        &self,
        organization_id: &str,
        signing_hash: &str,
    ) -> Result<AdmissionContextValue, AdmissionAdapterError>;
}

pub trait AdmissionLog {
    fn lookup(
        &self,
        organization_id: &str,
        signing_hash: &str,
    ) -> Result<AdmissionLookup, AdmissionAdapterError>;

    fn append_or_return_existing(
        &self,
        organization_id: &str,
        signing_hash: &str,
        candidate_bytes: &[u8],
    ) -> Result<AuthenticatedAdmissionRecord, AdmissionAdapterError>;
}
~~~

AdmissionAdapterError carries one stable AdmissionReason and protected local detail. There are no public trust booleans.

- [ ] **Step 7: Add the public errors and values**

Define:

~~~rust
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdmissionReason {
    RecordMissing,
    RecordBindingMismatch,
    TrustedTimeOutsideKeyInterval,
    MalformedTrustedTime,
    RecordConflict,
    RecordSchemaInvalid,
    LogAuthenticationFailed,
    AppendIntegrityNotEstablished,
    LogUnavailable,
    LogIndeterminate,
    CommitFailed,
    EventSelfAnchoring,
}

#[derive(Debug, Error)]
#[error("signed document admission failed: AUTH_INVALID_SIGNATURE")]
pub struct AdmissionError {
    diagnostic: AdmissionDiagnostic,
}
~~~

Add immutable AdmissionContextValue, AuthenticatedAdmissionRecord, AdmissionLookup, FirstAdmissionRecord, PreparedFirstAdmission, and AdmittedSignedDocument. Use Arc<[u8]> for retained bytes and private fields with public accessors.

- [ ] **Step 8: Add AdmissionService**

Use:

~~~rust
pub struct AdmissionService {
    codec: SignedDocumentCodec,
    schemas: SchemaCatalog,
}

impl AdmissionService {
    pub fn new() -> Result<Self, AdmissionError>;

    pub fn prepare_first_admission(
        &self,
        verified: &VerifiedSignedDocument,
        trusted_context: &dyn TrustedAdmissionContext,
    ) -> Result<PreparedFirstAdmission, AdmissionError>;

    pub fn admit_first(
        &self,
        kind: SignedDocumentKind,
        document_bytes: &[u8],
        registry: &dyn AdmissionCurrentKeyResolver,
        log: &dyn AdmissionLog,
        trusted_context: &dyn TrustedAdmissionContext,
    ) -> Result<AdmittedSignedDocument, AdmissionError>;

    pub fn verify_historical_admission(
        &self,
        kind: SignedDocumentKind,
        document_bytes: &[u8],
        registry: &dyn KeyResolver,
        log: &dyn AdmissionLog,
    ) -> Result<AdmittedSignedDocument, AdmissionError>;
}
~~~

Add a private adapter implementing KeyResolver by delegating to resolve_current for the first-admission cryptographic pass.

- [ ] **Step 9: Implement strict record and interval validation**

Use parse_strict_json, SchemaCatalog, parse_rfc3339, existing Rfc3339Instant ordering, and canonical serialization. Require exact acceptedBy equality with the authenticated adapter service. Validate returned bytes after append even when the adapter says it committed the candidate.

- [ ] **Step 10: Run focused tests and prove GREEN**

Run:

~~~bash
cargo test --locked --test admission
cargo test --locked --test signed_document_codec
~~~

- [ ] **Step 11: Execute all 30 Admission evaluations**

Extend tests/admission.rs with a manifest runner using only public AdmissionService methods. Assert 30 evaluations, 12 successes, 18 rejected, and the exact declared reason for every failure.

- [ ] **Step 12: Embed and verify the Admission bundle**

In src/bundle.rs, add:

~~~rust
static ADMISSION: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/admission");
~~~

Add AdmissionPin to ProtocolPin, AdmissionBundleSummary, ProtocolBundle::verify_admission, ProtocolBundle::admission, safe routing for admission and schemas, exact 19/5/30 checks, and cryptography digest equality.

- [ ] **Step 13: Add packaged-crate and external-consumer evidence**

Extend CI so the extracted .crate runs the exact Admission bundle unit test and the 30-evaluation integration test. Then create a temporary consumer crate whose Cargo.toml depends on the extracted package path and whose main imports AdmissionService, verifies both bundles, and completes one first admission. Run it with a separate CARGO_TARGET_DIR.

- [ ] **Step 14: Export and document**

Add mod admission and public re-exports in src/lib.rs. Update all seven READMEs with the merged pin, 30 evaluations, current-Registry seam, and public API example.

- [ ] **Step 15: Run the complete Rust gate**

Run:

~~~bash
node scripts/check-repository-policy.mjs
cargo fmt --all --check
cargo clippy --locked --all-targets --all-features -- -D warnings
cargo test --locked --all-features
cargo run --locked --quiet --bin missionweaveprotocol-conformance
cargo package --locked
git diff --check
~~~

- [ ] **Step 16: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/rust-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 with immutable Admission evidence, current-Registry trust seam, and all 30 protocol evaluations."
RUST_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/rust-sdk --watch
gh run list --repo MissionWeaveProtocol/rust-sdk --commit "$RUST_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Do not merge in this task.
### Task 11: Implement and publish the Java Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionReason.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionDiagnostic.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionException.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionAdapterException.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionCurrentKeyResolver.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionContextValue.java
- Create: src/main/java/org/missionweaveprotocol/sdk/TrustedAdmissionContext.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AuthenticatedAdmissionRecord.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionLookup.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionLog.java
- Create: src/main/java/org/missionweaveprotocol/sdk/FirstAdmissionRecord.java
- Create: src/main/java/org/missionweaveprotocol/sdk/PreparedFirstAdmission.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmittedSignedDocument.java
- Create: src/main/java/org/missionweaveprotocol/sdk/AdmissionService.java
- Create: src/test/java/org/missionweaveprotocol/sdk/AdmissionServiceTest.java
- Create: src/test/java/org/missionweaveprotocol/sdk/AdmissionConformanceTest.java
- Modify: src/main/java/org/missionweaveprotocol/sdk/ResolvedKey.java
- Modify: src/main/java/org/missionweaveprotocol/sdk/ProtocolBundle.java
- Modify: src/test/java/org/missionweaveprotocol/sdk/ProtocolBundleTest.java
- Modify: src/test/java/org/missionweaveprotocol/sdk/ProtocolBundlePackagingIT.java
- Modify: src/main/resources/META-INF/missionweaveprotocol/protocol-bundle.index
- Modify: scripts/smoke_install.sh
- Modify: scripts/check_documentation.py
- Modify: docs/usage.md
- Modify: docs/conformance.md
- Modify: pom.xml
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: seven README files
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the Java worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/java-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/java-sdk rev-parse origin/main)" = \
  "8157f24f4a7455483f234db4143dccdc7d4462cf"
git -C /Users/lionelmbp/repos/java-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize the merged bundle and pin**

From the Java worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
~~~

Add `admission/**/*` to the first Maven resource block and add every Admission file plus the new Schema/vector paths to `protocol-bundle.index` in lexical order.

- [ ] **Step 3: Write Java RED tests**

In AdmissionServiceTest.java, add:

~~~java
@Test
void firstAdmissionReturnsOnlyAfterCommittedRecordValidation() throws Exception {
  var log = RecordingAdmissionLog.authoritativeAbsenceThenCommit();
  var admitted =
      new AdmissionService()
          .admitFirst(
              SignedDocumentKind.COMMAND,
              goldenCommand(),
              currentRegistry(),
              log,
              fixedTrustedContext());

  assertEquals(admitted.verified().signingHash(), admitted.record().signingHash());
  assertEquals(List.of("lookup", "appendOrReturnExisting"), log.calls());
}

@Test
void trustedAcceptanceEqualToValidUntilFailsAdmission() throws Exception {
  var error =
      assertThrows(
          AdmissionException.class,
          () ->
              new AdmissionService()
                  .prepareFirstAdmission(
                      verifiedCommand(),
                      fixedTrustedContext("2026-07-16T00:00:00Z")));

  assertEquals("AUTH_INVALID_SIGNATURE", error.wireCode());
  assertEquals("admission", error.diagnostic().stage());
  assertEquals(
      AdmissionReason.TRUSTED_TIME_OUTSIDE_KEY_INTERVAL,
      error.diagnostic().reason());
}
~~~

Add these focused methods to `AdmissionServiceTest` before running RED:

~~~text
existingRecordBindingMismatchFailsAdmission
  verifyHistoricalAdmission + key-id-mismatch record -> RECORD_BINDING_MISMATCH
historicalReplayAcceptsRetainedLaterRevocation
  verifyHistoricalAdmission + registry-later-revocation + valid record -> success, zero append calls
unavailableLogFailsFirstAdmission
  admitFirst + unavailable lookup -> LOG_UNAVAILABLE
~~~

Each rejected method asserts `AUTH_INVALID_SIGNATURE` and diagnostic stage `admission`; the valid and exclusive-boundary methods already shown complete the required five focused behaviors.

- [ ] **Step 4: Prove RED**

Run if Java 21 is available:

~~~bash
./mvnw -B -ntp -Dtest=AdmissionServiceTest test
~~~

Expected: compile failure because the Admission classes do not exist. If the local JDK is still unavailable, record java -version output and use the exact pull-request CI run as the RED/GREEN compiler and test boundary.

- [ ] **Step 5: Expose parsed instants from the selected ResolvedKey**

Add methods to ResolvedKey.java:

~~~java
public ExactInstant validFromInstant() {
  return ExactInstant.parse(validFrom);
}

public ExactInstant validUntilInstant() {
  return validUntil == null ? null : ExactInstant.parse(validUntil);
}

public ExactInstant revokedAtInstant() {
  return revokedAt == null ? null : ExactInstant.parse(revokedAt);
}
~~~

These methods parse retained selected evidence and do not perform a second Registry selection.

- [ ] **Step 6: Add a current-Registry resolver interface**

Create AdmissionCurrentKeyResolver.java:

~~~java
@FunctionalInterface
public interface AdmissionCurrentKeyResolver {
  KeyRegistrySnapshot resolveCurrent(KeyResolutionRequest request)
      throws KeyResolutionException;
}
~~~

AdmissionService adapts this interface to KeyResolver only for the first-admission six-stage pass. Historical replay accepts the existing KeyResolver.

- [ ] **Step 7: Add typed Admission failures**

AdmissionReason.java contains:

~~~java
public enum AdmissionReason {
  RECORD_MISSING("record-missing"),
  RECORD_BINDING_MISMATCH("record-binding-mismatch"),
  TRUSTED_TIME_OUTSIDE_KEY_INTERVAL("trusted-time-outside-key-interval"),
  MALFORMED_TRUSTED_TIME("malformed-trusted-time"),
  RECORD_CONFLICT("record-conflict"),
  RECORD_SCHEMA_INVALID("record-schema-invalid"),
  LOG_AUTHENTICATION_FAILED("log-authentication-failed"),
  APPEND_INTEGRITY_NOT_ESTABLISHED("append-integrity-not-established"),
  LOG_UNAVAILABLE("log-unavailable"),
  LOG_INDETERMINATE("log-indeterminate"),
  COMMIT_FAILED("commit-failed"),
  EVENT_SELF_ANCHORING("event-self-anchoring");
}
~~~

AdmissionException is a separate checked exception whose message contains only AUTH_INVALID_SIGNATURE and whose diagnostic returns stage admission plus the reason. AdmissionAdapterException carries a reason and access-controlled detail.

- [ ] **Step 8: Add sealed lookup and adapter contracts**

Create:

~~~java
public sealed interface AdmissionLookup
    permits AdmissionLookup.Found, AdmissionLookup.AuthoritativeAbsence {

  record Found(AuthenticatedAdmissionRecord record) implements AdmissionLookup {}

  record AuthoritativeAbsence() implements AdmissionLookup {}
}

@FunctionalInterface
public interface TrustedAdmissionContext {
  AdmissionContextValue issue(String organizationId, String signingHash)
      throws AdmissionAdapterException;
}

public interface AdmissionLog {
  AdmissionLookup lookup(String organizationId, String signingHash)
      throws AdmissionAdapterException;

  AuthenticatedAdmissionRecord appendOrReturnExisting(
      String organizationId,
      String signingHash,
      byte[] candidateBytes)
      throws AdmissionAdapterException;
}
~~~

AuthenticatedAdmissionRecord defensively copies bytes. There are no authentication or integrity boolean arguments.

- [ ] **Step 9: Add immutable records and AdmissionService**

Use:

~~~java
public final class AdmissionService {
  public PreparedFirstAdmission prepareFirstAdmission(
      VerifiedSignedDocument verified,
      TrustedAdmissionContext trustedContext)
      throws AdmissionException;

  public AdmittedSignedDocument admitFirst(
      SignedDocumentKind kind,
      byte[] documentBytes,
      AdmissionCurrentKeyResolver registry,
      AdmissionLog admissionLog,
      TrustedAdmissionContext trustedContext)
      throws SignedDocumentVerificationException, AdmissionException;

  public AdmittedSignedDocument verifyHistoricalAdmission(
      SignedDocumentKind kind,
      byte[] documentBytes,
      KeyResolver registry,
      AdmissionLog admissionLog)
      throws SignedDocumentVerificationException, AdmissionException;
}
~~~

Implement strict parsing with StrictJson, SchemaCatalog validation, exact binding checks, ExactInstant comparisons, candidate canonicalization with CanonicalJson, returned-record validation, and Event self-anchoring rejection.

- [ ] **Step 10: Prove focused GREEN**

Run when Java 21 is available:

~~~bash
./mvnw -B -ntp -Dtest=AdmissionServiceTest test
~~~

Expected: all focused tests pass.

- [ ] **Step 11: Execute all 30 Admission evaluations**

AdmissionConformanceTest reads packaged admission/manifest.json, maps adapter outcome enums to test adapters, calls only AdmissionService public methods, and asserts 30/12/18 plus declared reasons.

- [ ] **Step 12: Add Admission bundle verification and package integration**

Extend ProtocolBundle with Admission constants, pin record, manifest fields, verifyAdmissionBundle(Path), verifyPackagedAdmissionBundle(), and AdmissionVerification. Require 19/5/30 and cryptography digest equality. Extend ProtocolBundleTest and ProtocolBundlePackagingIT to verify every artifact in the isolated built JAR.

- [ ] **Step 13: Extend the installed Maven consumer**

In scripts/smoke_install.sh, add imports and code that:

~~~text
verifies the packaged Admission bundle
asserts 19 artifacts / 5 cases / 30 evaluations
loads the packaged Command, Registry, and valid Command Admission record
implements public current Registry, trusted context, and Admission Log adapters
calls AdmissionService.admitFirst
checks the admitted signing hash
~~~

The consumer must depend only on the installed Maven artifact.

- [ ] **Step 14: Update documentation and its checker**

Update docs/usage.md, docs/conformance.md, all seven READMEs, and scripts/check_documentation.py with the merged pin, 58 structural vectors, 62 unchanged cryptography evaluations, 30 Admission evaluations, and the current-Registry versus historical Registry APIs.

- [ ] **Step 15: Run available local checks**

Run:

~~~bash
python3 scripts/check_repository_policy.py
python3 scripts/check_documentation.py
sh -n scripts/smoke_install.sh
git diff --check
~~~

If Java 21 is installed, also run:

~~~bash
./mvnw -B -ntp verify
scripts/smoke_install.sh
~~~

Do not claim native or package success if the JDK remains unavailable.

- [ ] **Step 16: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/java-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 with separate Admission failures, current-Registry trust seam, packaged bundle verification, and all 30 evaluations."
JAVA_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/java-sdk --watch
gh run list --repo MissionWeaveProtocol/java-sdk --commit "$JAVA_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

The exact-head CI log must prove Maven verify, AdmissionConformanceTest, packaged JAR verification, and installed-consumer execution. Do not merge in this task.

### Task 12: Implement and publish the C++ Admission API

**Files:**

- Worktree: /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust
- Create: include/missionweaveprotocol/admission.hpp
- Create: src/admission.cpp
- Create: tests/admission_test.cpp
- Create: tests/admission_conformance_test.cpp
- Modify: include/missionweaveprotocol/signed_document.hpp
- Modify: include/missionweaveprotocol/bundle.hpp
- Modify: src/agent_registry_key_resolution.cpp
- Modify: src/bundle.cpp
- Modify: scripts/generate_embedded_assets.py
- Generate: src/embedded_assets.cpp
- Modify: CMakeLists.txt
- Modify: tests/CMakeLists.txt
- Modify: tests/bundle_test.cpp
- Modify: tests/package-consumer/main.cpp
- Modify: scripts/check_readmes.py
- Modify: .github/workflows/ci.yml
- Modify: PROTOCOL_PIN.json
- Modify: seven README files
- Vendor: schemas/, conformance/, cryptography/, admission/

- [ ] **Step 1: Create the C++ worktree from the exact reviewed baseline**

Run:

~~~bash
git -C /Users/lionelmbp/repos/cpp-sdk fetch origin
test "$(git -C /Users/lionelmbp/repos/cpp-sdk rev-parse origin/main)" = \
  "d838a57d9407eecf506324fa32993c10b559c95e"
git -C /Users/lionelmbp/repos/cpp-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust \
  -b feat/first-admission-historical-trust origin/main
~~~

- [ ] **Step 2: Synchronize the merged bundle and pin**

From the C++ worktree, run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
MW_PROTOCOL_COMMIT=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-pin.json"))["commit"])')
test -d "$MW_PROTOCOL_ARCHIVE_ROOT"
test "$MW_PROTOCOL_COMMIT" = \
  "$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/schemas/" schemas/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/conformance/" conformance/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography/" cryptography/
rsync -a --delete "$MW_PROTOCOL_ARCHIVE_ROOT/admission/" admission/
cp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
cmp /tmp/mw-first-admission-sdk-pin.json PROTOCOL_PIN.json
~~~

The copied `PROTOCOL_PIN.json` must remain byte-identical to every other SDK pin.

- [ ] **Step 3: Write C++ RED tests**

In tests/admission_test.cpp, add:

~~~cpp
void first_admission_validates_the_committed_record() {
  RecordingAdmissionLog log{Outcome::authoritative_absence_then_commit};
  const auto admitted = missionweaveprotocol::AdmissionService{}.admit_first(
      missionweaveprotocol::SignedDocumentKind::command, golden_command(),
      current_registry(), log, fixed_trusted_context());
  assert(admitted.record().signing_hash() == admitted.verified().signing_hash());
  assert((log.calls() == std::vector<std::string>{
                             "lookup", "append_or_return_existing"}));
}

void historical_replay_never_appends() {
  RecordingAdmissionLog log{Outcome::authoritative_absence};
  try {
    static_cast<void>(
        missionweaveprotocol::AdmissionService{}.verify_historical_admission(
            missionweaveprotocol::SignedDocumentKind::command, golden_command(),
            historical_registry(), log));
    assert(false);
  } catch (const missionweaveprotocol::AdmissionError& error) {
    assert(error.wire_code() == "AUTH_INVALID_SIGNATURE");
    assert(error.diagnostic().stage == "admission");
    assert(error.diagnostic().reason ==
           missionweaveprotocol::AdmissionReason::record_missing);
  }
  assert(log.append_calls() == 0);
}
~~~

Add these focused functions to `tests/admission_test.cpp` before running RED:

~~~text
existing_record_binding_mismatch_fails_admission
  verify_historical_admission + key-id-mismatch record -> AdmissionReason::record_binding_mismatch
historical_replay_accepts_retained_later_revocation
  verify_historical_admission + registry-later-revocation + valid record -> success, zero append calls
unavailable_log_fails_first_admission
  admit_first + unavailable lookup -> AdmissionReason::log_unavailable
trusted_time_equal_valid_until_fails_admission
  prepare_first_admission at validUntil -> AdmissionReason::trusted_time_outside_key_interval
~~~

Every rejected function asserts wire code `AUTH_INVALID_SIGNATURE` and stage `admission` through public accessors.

- [ ] **Step 4: Add the test target and prove RED**

Add missionweaveprotocol_admission_test to tests/CMakeLists.txt, then run:

~~~bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build --target missionweaveprotocol_admission_test
~~~

Expected: compile failure because admission.hpp is absent.

- [ ] **Step 5: Retain parsed selected validity evidence**

Extend ResolvedKey in signed_document.hpp:

~~~cpp
struct ResolvedKey {
  std::string organization_id;
  std::string key_id;
  Principal principal;
  std::string algorithm;
  std::string public_key;
  std::string valid_from;
  ExactInstant valid_from_instant;
  std::optional<std::string> valid_until;
  std::optional<ExactInstant> valid_until_instant;
  std::optional<std::string> revoked_at;
  std::optional<ExactInstant> revoked_at_instant;

  bool operator==(const ResolvedKey&) const = default;
};
~~~

Populate these from the already-selected internal Registry evidence in agent_registry_key_resolution.cpp. Do not reselect a key.

- [ ] **Step 6: Add current-Registry and Admission adapter interfaces**

In admission.hpp:

~~~cpp
class AdmissionCurrentKeyResolver {
public:
  virtual ~AdmissionCurrentKeyResolver() = default;
  [[nodiscard]] virtual KeyRegistrySnapshot
  resolve_current(const KeyResolutionRequest& request) const = 0;
};

class TrustedAdmissionContext {
public:
  virtual ~TrustedAdmissionContext() = default;
  [[nodiscard]] virtual AdmissionContextValue
  issue(std::string_view organization_id,
        std::string_view signing_hash) const = 0;
};

class AdmissionLog {
public:
  virtual ~AdmissionLog() = default;
  [[nodiscard]] virtual AdmissionLookup
  lookup(std::string_view organization_id,
         std::string_view signing_hash) const = 0;
  [[nodiscard]] virtual AuthenticatedAdmissionRecord
  append_or_return_existing(std::string_view organization_id,
                            std::string_view signing_hash,
                            AssetBytes candidate_bytes) const = 0;
};
~~~

Typed AdmissionAdapterError represents unavailable, indeterminate, authentication, integrity, conflict, and commit failures. Do not use trust booleans.

- [ ] **Step 7: Add errors, values, and service signatures**

Define AdmissionReason as an enum with all twelve stable reasons and add admission_reason_id. AdmissionError is separate from SignedDocumentVerificationError and always returns AUTH_INVALID_SIGNATURE.

Add:

~~~cpp
class AdmissionService final {
public:
  AdmissionService();

  [[nodiscard]] PreparedFirstAdmission
  prepare_first_admission(const VerifiedSignedDocument& verified,
                          const TrustedAdmissionContext& trusted_context) const;

  [[nodiscard]] AdmittedSignedDocument
  admit_first(SignedDocumentKind kind, AssetBytes document_bytes,
              const AdmissionCurrentKeyResolver& registry,
              const AdmissionLog& admission_log,
              const TrustedAdmissionContext& trusted_context) const;

  [[nodiscard]] AdmittedSignedDocument
  verify_historical_admission(SignedDocumentKind kind,
                              AssetBytes document_bytes,
                              const KeyResolver& registry,
                              const AdmissionLog& admission_log) const;
};
~~~

FirstAdmissionRecord retains trustedAcceptedAt text and ExactInstant. PreparedFirstAdmission cannot convert implicitly to AdmittedSignedDocument.

- [ ] **Step 8: Implement strict validation and required call order**

Use parse_json_bytes, SchemaCatalog, parse_protocol_instant, canonical_json, and existing exact evidence. Validate record Schema, Organization, kind, signing hash, key ID, Principal, acceptedBy, and interval. Always validate returned adapter bytes after append-or-return-existing. Historical replay invokes SignedDocumentCodec::verify before lookup and never appends.

- [ ] **Step 9: Build focused tests and prove GREEN**

Run:

~~~bash
cmake --build build --target missionweaveprotocol_admission_test
ctest --test-dir build -R admission --output-on-failure
~~~

- [ ] **Step 10: Add all 30 manifest evaluations**

Create tests/admission_conformance_test.cpp, add its CMake target, parse embedded admission/manifest.json, map outcomes to public test adapters, and assert 30/12/18 plus declared reasons and call counts.

- [ ] **Step 11: Embed and verify the Admission bundle**

Update generate_embedded_assets.py count contracts to:

~~~python
EXPECTED_SCHEMAS = 22
EXPECTED_CONFORMANCE_FILES = 59
EXPECTED_CRYPTOGRAPHY_FILES = 90
EXPECTED_ADMISSION_FILES = 19
~~~

Include PROTOCOL_PIN.json plus all four trees. Regenerate embedded_assets.cpp. Add AdmissionPin, AdmissionBundleSummary, ProtocolBundle::admission, and ProtocolBundle::verify_admission. Require 19/5/30 and cryptography digest equality.

- [ ] **Step 12: Update the installed CMake consumer**

tests/package-consumer/main.cpp must include admission.hpp, verify the Admission bundle, implement public adapters, load embedded fixtures, call AdmissionService::admit_first, and check the resulting signing hash. No private source header may be included.

- [ ] **Step 13: Update build and documentation gates**

Add src/admission.cpp to the library, add both test targets, update all seven READMEs, and extend scripts/check_readmes.py with the merged pin, 58/62/30 totals, and admission link.

- [ ] **Step 14: Run the complete C++ gate**

Run:

~~~bash
python3 scripts/check_repository_policy.py
python3 scripts/check_readmes.py
python3 scripts/generate_embedded_assets.py
git diff --exit-code -- src/embedded_assets.cpp
find include src tests -type f \( -name '*.cpp' -o -name '*.hpp' \) -print0 | \
  xargs -0 clang-format --dry-run --Werror
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DMISSIONWEAVEPROTOCOL_WARNINGS_AS_ERRORS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
build/missionweaveprotocol-conformance
MW_CPP_INSTALL=$(mktemp -d /tmp/mw-cpp-install.XXXXXX)
cmake --install build --prefix "$MW_CPP_INSTALL"
cmake -S tests/package-consumer -B build/consumer -G Ninja \
  -DCMAKE_PREFIX_PATH="$MW_CPP_INSTALL"
cmake --build build/consumer
build/consumer/consumer
"$MW_CPP_INSTALL/bin/missionweaveprotocol-conformance"
git diff --check
~~~

Expected: generated assets are deterministic, all native tests pass, 58/58 conformance passes, and the installed public consumer completes Admission.

- [ ] **Step 15: Commit, push, open the PR, and require exact-head CI**

Run:

~~~bash
git add .
git commit -m "feat: add first-admission historical trust"
git push -u origin feat/first-admission-historical-trust
gh pr create \
  --repo MissionWeaveProtocol/cpp-sdk \
  --base main \
  --head feat/first-admission-historical-trust \
  --title "feat: add first-admission historical trust" \
  --body "Implements MW-V1-2026-07-30-R1 through the installed public C++ Admission API and all 30 protocol evaluations."
CPP_HEAD_SHA=$(git rev-parse HEAD)
gh pr checks --repo MissionWeaveProtocol/cpp-sdk --watch
gh run list --repo MissionWeaveProtocol/cpp-sdk --commit "$CPP_HEAD_SHA" \
  --json databaseId,headSha,status,conclusion,workflowName
~~~

Do not merge in this task.

### Task 13: Audit all six SDK branch heads before merge

**Files:**

- Read: each SDK PROTOCOL_PIN.json
- Read: each SDK admission/, cryptography/, schemas/, and conformance/ tree
- Produce: /tmp/mw-first-admission-branch-head-audit.json

- [ ] **Step 1: Reconfirm the active revision**

Run:

~~~bash
rg -n "MW-V1-2026-07-30-R1" \
  /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-design/docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md
~~~

- [ ] **Step 2: Capture the six exact branch-head SHAs**

Run:

~~~bash
python - <<'PY'
import json
import subprocess
from pathlib import Path

roots = {
    "python": "/Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust",
    "typescript": "/Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust",
    "go": "/Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust",
    "rust": "/Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust",
    "java": "/Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust",
    "cpp": "/Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust",
}
heads = {
    language: subprocess.check_output(
        ["git", "-C", root, "rev-parse", "HEAD"],
        text=True,
    ).strip()
    for language, root in roots.items()
}
Path("/tmp/mw-first-admission-sdk-heads.json").write_text(
    json.dumps(heads, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(heads, indent=2))
PY
~~~

- [ ] **Step 3: Prove every SDK pin is byte-identical**

Run:

~~~bash
shasum -a 256 \
  /Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust/PROTOCOL_PIN.json \
  /Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust/PROTOCOL_PIN.json \
  /Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust/PROTOCOL_PIN.json \
  /Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust/PROTOCOL_PIN.json \
  /Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust/PROTOCOL_PIN.json \
  /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust/PROTOCOL_PIN.json
~~~

Expected: all six SHA-256 values are identical. This intentionally removes the pre-slice Java/C++ top-level member-order difference.

- [ ] **Step 4: Prove all vendored trees are byte-identical to merged protocol main**

Run:

~~~bash
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
for SDK_ROOT in \
  /Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust \
  /Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust \
  /Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust \
  /Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust \
  /Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust \
  /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust
do
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/admission" "$SDK_ROOT/admission"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/schemas" "$SDK_ROOT/schemas"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/conformance" "$SDK_ROOT/conformance"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography" "$SDK_ROOT/cryptography"
  cmp /tmp/mw-first-admission-sdk-pin.json "$SDK_ROOT/PROTOCOL_PIN.json"
done
~~~

Expected: no differences in any repository.

- [ ] **Step 5: Prove the shared semantic counts and digests**

Run:

~~~bash
python - <<'PY'
import json
from pathlib import Path

roots = {
    "python": Path("/Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust"),
    "typescript": Path("/Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/first-admission-historical-trust"),
    "go": Path("/Users/lionelmbp/.config/superpowers/worktrees/go-sdk/first-admission-historical-trust"),
    "rust": Path("/Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/first-admission-historical-trust"),
    "java": Path("/Users/lionelmbp/.config/superpowers/worktrees/java-sdk/first-admission-historical-trust"),
    "cpp": Path("/Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/first-admission-historical-trust"),
}
identities = set()
for language, root in roots.items():
    pin = json.loads((root / "PROTOCOL_PIN.json").read_text(encoding="utf-8"))
    assert pin["artifacts"]["schemas"]["files"] == 22
    assert pin["artifacts"]["conformance"]["files"] == 59
    assert len(list((root / "schemas").glob("*.json"))) == 22
    assert len(list((root / "conformance/vectors").rglob("*.json"))) == 58
    assert pin["cryptography"]["artifactDigest"] == (
        "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
    )
    assert pin["cryptography"]["sourceCommit"] == pin["commit"]
    assert pin["cryptography"]["artifactCount"] == 98
    assert pin["cryptography"]["caseCount"] == 22
    assert pin["cryptography"]["evaluationCount"] == 62
    assert pin["admission"]["sourceCommit"] == pin["commit"]
    assert pin["admission"]["cryptographyArtifactDigest"] == pin["cryptography"]["artifactDigest"]
    assert pin["admission"]["artifactCount"] == 19
    assert pin["admission"]["caseCount"] == 5
    assert pin["admission"]["evaluationCount"] == 30
    assert len([path for path in (root / "admission").rglob("*") if path.is_file()]) == 19
    identities.add((pin["commit"], pin["admission"]["artifactDigest"]))
    print(language, pin["commit"], pin["admission"]["artifactDigest"])
assert len(identities) == 1
PY
~~~

Expected: every SDK prints the same merged protocol commit and Admission digest.

- [ ] **Step 6: Audit public semantic equivalence**

For every SDK, verify from source and focused tests:

~~~text
existing verify remains cryptography-only
prepare returns PreparedFirstAdmission, never AdmittedSignedDocument
first admission uses a current-Registry trust seam
historical replay uses retained history and reruns verify before lookup
lookup distinguishes found from authoritative absence
append is atomic append-or-return-existing
returned record is validated after append
acceptedBy equals authenticated service
no trust boolean appears in public signatures
all Admission failures are separate and wire-safe
all 30 manifest evaluations use public orchestration paths
~~~

- [ ] **Step 7: Verify exact-head CI for every repository**

Run this exact repository-to-head mapping and persist the successful run evidence:

~~~bash
python - <<'PY'
import json
import subprocess
from pathlib import Path

heads = json.loads(
    Path("/tmp/mw-first-admission-sdk-heads.json").read_text(encoding="utf-8")
)
repositories = {
    "python": "MissionWeaveProtocol/python-sdk",
    "typescript": "MissionWeaveProtocol/typescript-sdk",
    "go": "MissionWeaveProtocol/go-sdk",
    "rust": "MissionWeaveProtocol/rust-sdk",
    "java": "MissionWeaveProtocol/java-sdk",
    "cpp": "MissionWeaveProtocol/cpp-sdk",
}
evidence = {}
for language, repository in repositories.items():
    head = heads[language]
    pulls = json.loads(
        subprocess.check_output(
            [
                "gh", "pr", "list",
                "--repo", repository,
                "--head", "feat/first-admission-historical-trust",
                "--state", "open",
                "--limit", "1",
                "--json", "number,headRefOid",
            ],
            text=True,
        )
    )
    assert len(pulls) == 1 and pulls[0]["headRefOid"] == head
    runs = json.loads(
        subprocess.check_output(
            [
                "gh", "run", "list",
                "--repo", repository,
                "--commit", head,
                "--limit", "20",
                "--json", "databaseId,headSha,status,conclusion,workflowName,event",
            ],
            text=True,
        )
    )
    exact_runs = [run for run in runs if run["headSha"] == head]
    assert exact_runs
    assert all(
        run["status"] == "completed" and run["conclusion"] == "success"
        for run in exact_runs
    )
    evidence[language] = {
        "repository": repository,
        "pullRequest": pulls[0]["number"],
        "headSha": head,
        "runs": exact_runs,
    }
Path("/tmp/mw-first-admission-head-ci.json").write_text(
    json.dumps(evidence, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(evidence, indent=2))
PY
~~~

If Java 21 remains unavailable locally, record that boundary in the review evidence, but do not weaken the exact-head Maven, package, and installed-consumer CI requirements.

- [ ] **Step 8: Write the branch-head audit JSON**

Generate `/tmp/mw-first-admission-branch-head-audit.json` from the captured files and vendored manifest:

~~~bash
python - <<'PY'
import json
from pathlib import Path

python_root = Path(
    "/Users/lionelmbp/.config/superpowers/worktrees/python-sdk/first-admission-historical-trust"
)
pin = json.loads((python_root / "PROTOCOL_PIN.json").read_text(encoding="utf-8"))
manifest = json.loads(
    (python_root / "admission/manifest.json").read_text(encoding="utf-8")
)
heads = json.loads(
    Path("/tmp/mw-first-admission-sdk-heads.json").read_text(encoding="utf-8")
)
head_ci = json.loads(
    Path("/tmp/mw-first-admission-head-ci.json").read_text(encoding="utf-8")
)
evaluations = [
    evaluation
    for case in manifest["cases"]
    for evaluation in case["evaluations"]
]
complete = sum(
    evaluation["expect"]["stage"] == "complete" for evaluation in evaluations
)
audit = {
    "taskRevision": "MW-V1-2026-07-30-R1",
    "protocolCommit": pin["commit"],
    "cryptographyDigest": pin["cryptography"]["artifactDigest"],
    "admissionDigest": pin["admission"]["artifactDigest"],
    "counts": {
        "schemas": pin["artifacts"]["schemas"]["files"],
        "structuralVectors": len(
            list((python_root / "conformance/vectors").rglob("*.json"))
        ),
        "cryptographyEvaluations": pin["cryptography"]["evaluationCount"],
        "admissionArtifacts": len(manifest["artifacts"]),
        "admissionCases": len(manifest["cases"]),
        "admissionEvaluations": len(evaluations),
        "admissionComplete": complete,
        "admissionRejected": len(evaluations) - complete,
    },
    "sdkHeads": heads,
    "headCi": head_ci,
}
assert audit["counts"] == {
    "schemas": 22,
    "structuralVectors": 58,
    "cryptographyEvaluations": 62,
    "admissionArtifacts": 19,
    "admissionCases": 5,
    "admissionEvaluations": 30,
    "admissionComplete": 12,
    "admissionRejected": 18,
}
Path("/tmp/mw-first-admission-branch-head-audit.json").write_text(
    json.dumps(audit, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps(audit, indent=2))
PY
~~~

### Task 14: Merge all six SDKs and require exact-main CI

**Files:**

- Read: six pull requests and CI runs
- Produce: six merged-main SHAs and run IDs

- [ ] **Step 1: Reconfirm task revision and all exact-head checks**

Run:

~~~bash
rg -n "MW-V1-2026-07-30-R1" \
  /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/first-admission-historical-trust-design/docs/superpowers/specs/2026-07-30-first-admission-historical-trust-design.md
python -m json.tool /tmp/mw-first-admission-branch-head-audit.json
~~~

Do not merge if any head SHA, digest, count, package smoke, or exact-head CI result is missing.

- [ ] **Step 2: Merge the Python pull request and capture the actual merge commit**

Run:

~~~bash
PYTHON_PR=$(gh pr list --repo MissionWeaveProtocol/python-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$PYTHON_PR"
gh pr merge "$PYTHON_PR" --repo MissionWeaveProtocol/python-sdk --squash
PYTHON_MAIN_SHA=$(gh pr view "$PYTHON_PR" --repo MissionWeaveProtocol/python-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/python-sdk fetch origin
test "$PYTHON_MAIN_SHA" = "$(git -C /Users/lionelmbp/repos/python-sdk rev-parse origin/main)"
~~~

- [ ] **Step 3: Merge TypeScript and capture the actual merge commit**

Run:

~~~bash
TYPESCRIPT_PR=$(gh pr list --repo MissionWeaveProtocol/typescript-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$TYPESCRIPT_PR"
gh pr merge "$TYPESCRIPT_PR" --repo MissionWeaveProtocol/typescript-sdk --squash
TYPESCRIPT_MAIN_SHA=$(gh pr view "$TYPESCRIPT_PR" \
  --repo MissionWeaveProtocol/typescript-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/typescript-sdk fetch origin
test "$TYPESCRIPT_MAIN_SHA" = \
  "$(git -C /Users/lionelmbp/repos/typescript-sdk rev-parse origin/main)"
~~~

- [ ] **Step 4: Merge Go and capture the actual merge commit**

Run:

~~~bash
GO_PR=$(gh pr list --repo MissionWeaveProtocol/go-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$GO_PR"
gh pr merge "$GO_PR" --repo MissionWeaveProtocol/go-sdk --squash
GO_MAIN_SHA=$(gh pr view "$GO_PR" --repo MissionWeaveProtocol/go-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/go-sdk fetch origin
test "$GO_MAIN_SHA" = \
  "$(git -C /Users/lionelmbp/repos/go-sdk rev-parse origin/main)"
~~~

- [ ] **Step 5: Merge Rust and capture the actual merge commit**

Run:

~~~bash
RUST_PR=$(gh pr list --repo MissionWeaveProtocol/rust-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$RUST_PR"
gh pr merge "$RUST_PR" --repo MissionWeaveProtocol/rust-sdk --squash
RUST_MAIN_SHA=$(gh pr view "$RUST_PR" --repo MissionWeaveProtocol/rust-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/rust-sdk fetch origin
test "$RUST_MAIN_SHA" = \
  "$(git -C /Users/lionelmbp/repos/rust-sdk rev-parse origin/main)"
~~~

- [ ] **Step 6: Merge Java and capture the actual merge commit**

Run:

~~~bash
JAVA_PR=$(gh pr list --repo MissionWeaveProtocol/java-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$JAVA_PR"
gh pr merge "$JAVA_PR" --repo MissionWeaveProtocol/java-sdk --squash
JAVA_MAIN_SHA=$(gh pr view "$JAVA_PR" --repo MissionWeaveProtocol/java-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/java-sdk fetch origin
test "$JAVA_MAIN_SHA" = \
  "$(git -C /Users/lionelmbp/repos/java-sdk rev-parse origin/main)"
~~~

- [ ] **Step 7: Merge C++ and capture the actual merge commit**

Run:

~~~bash
CPP_PR=$(gh pr list --repo MissionWeaveProtocol/cpp-sdk \
  --head feat/first-admission-historical-trust --state open \
  --limit 1 --json number --jq '.[0].number')
test -n "$CPP_PR"
gh pr merge "$CPP_PR" --repo MissionWeaveProtocol/cpp-sdk --squash
CPP_MAIN_SHA=$(gh pr view "$CPP_PR" --repo MissionWeaveProtocol/cpp-sdk \
  --json mergeCommit --jq .mergeCommit.oid)
git -C /Users/lionelmbp/repos/cpp-sdk fetch origin
test "$CPP_MAIN_SHA" = \
  "$(git -C /Users/lionelmbp/repos/cpp-sdk rev-parse origin/main)"
~~~

- [ ] **Step 8: Require exact merged-main CI in all six repositories**

Recapture the six verified `origin/main` SHAs, persist them, and wait for each exact push run:

~~~bash
PYTHON_MAIN_SHA=$(git -C /Users/lionelmbp/repos/python-sdk rev-parse origin/main)
TYPESCRIPT_MAIN_SHA=$(git -C /Users/lionelmbp/repos/typescript-sdk rev-parse origin/main)
GO_MAIN_SHA=$(git -C /Users/lionelmbp/repos/go-sdk rev-parse origin/main)
RUST_MAIN_SHA=$(git -C /Users/lionelmbp/repos/rust-sdk rev-parse origin/main)
JAVA_MAIN_SHA=$(git -C /Users/lionelmbp/repos/java-sdk rev-parse origin/main)
CPP_MAIN_SHA=$(git -C /Users/lionelmbp/repos/cpp-sdk rev-parse origin/main)
export PYTHON_MAIN_SHA TYPESCRIPT_MAIN_SHA GO_MAIN_SHA RUST_MAIN_SHA JAVA_MAIN_SHA CPP_MAIN_SHA
python - <<'PY'
import json
import os
from pathlib import Path

shas = {
    "python": os.environ["PYTHON_MAIN_SHA"],
    "typescript": os.environ["TYPESCRIPT_MAIN_SHA"],
    "go": os.environ["GO_MAIN_SHA"],
    "rust": os.environ["RUST_MAIN_SHA"],
    "java": os.environ["JAVA_MAIN_SHA"],
    "cpp": os.environ["CPP_MAIN_SHA"],
}
Path("/tmp/mw-first-admission-sdk-main-shas.json").write_text(
    json.dumps(shas, indent=2) + "\n",
    encoding="utf-8",
)
PY

require_main_ci() {
  SDK_REPO=$1
  MAIN_SHA=$2
  LABEL=$3
  RUN_ID=""
  while test -z "$RUN_ID"
  do
    RUN_ID=$(gh run list --repo "$SDK_REPO" --branch main \
      --commit "$MAIN_SHA" --event push --limit 20 \
      --json databaseId,headSha \
      --jq '.[0].databaseId // empty')
    if test -z "$RUN_ID"; then sleep 10; fi
  done
  gh run watch "$RUN_ID" --repo "$SDK_REPO" --exit-status
  gh run view "$RUN_ID" --repo "$SDK_REPO" \
    --json databaseId,headSha,status,conclusion,workflowName,event \
    > "/tmp/mw-first-admission-${LABEL}-main-ci.json"
  test "$MAIN_SHA" = "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["headSha"])' \
    "/tmp/mw-first-admission-${LABEL}-main-ci.json")"
  test "success" = "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["conclusion"])' \
    "/tmp/mw-first-admission-${LABEL}-main-ci.json")"
}

require_main_ci MissionWeaveProtocol/python-sdk "$PYTHON_MAIN_SHA" python
require_main_ci MissionWeaveProtocol/typescript-sdk "$TYPESCRIPT_MAIN_SHA" typescript
require_main_ci MissionWeaveProtocol/go-sdk "$GO_MAIN_SHA" go
require_main_ci MissionWeaveProtocol/rust-sdk "$RUST_MAIN_SHA" rust
require_main_ci MissionWeaveProtocol/java-sdk "$JAVA_MAIN_SHA" java
require_main_ci MissionWeaveProtocol/cpp-sdk "$CPP_MAIN_SHA" cpp
~~~

Every recorded run must be a successful push run whose `headSha` equals its captured merge SHA.

- [ ] **Step 9: Re-audit merged trees**

Run:

~~~bash
MW_MERGED_SDK_ARCHIVE_ROOT=$(mktemp -d /tmp/mw-first-admission-sdk-main.XXXXXX)
mkdir "$MW_MERGED_SDK_ARCHIVE_ROOT/python" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/typescript" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/go" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/rust" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/java" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/cpp"
PYTHON_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["python"])')
TYPESCRIPT_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["typescript"])')
GO_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["go"])')
RUST_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["rust"])')
JAVA_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["java"])')
CPP_MAIN_SHA=$(python -c 'import json; print(json.load(open("/tmp/mw-first-admission-sdk-main-shas.json"))["cpp"])')
git -C /Users/lionelmbp/repos/python-sdk archive "$PYTHON_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/python"
git -C /Users/lionelmbp/repos/typescript-sdk archive "$TYPESCRIPT_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/typescript"
git -C /Users/lionelmbp/repos/go-sdk archive "$GO_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/go"
git -C /Users/lionelmbp/repos/rust-sdk archive "$RUST_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/rust"
git -C /Users/lionelmbp/repos/java-sdk archive "$JAVA_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/java"
git -C /Users/lionelmbp/repos/cpp-sdk archive "$CPP_MAIN_SHA" | tar -x -C "$MW_MERGED_SDK_ARCHIVE_ROOT/cpp"
MW_PROTOCOL_ARCHIVE_ROOT=$(cat /tmp/mw-first-admission-protocol-archive-root.txt)
for SDK_ARCHIVE in \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/python" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/typescript" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/go" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/rust" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/java" \
  "$MW_MERGED_SDK_ARCHIVE_ROOT/cpp"
do
  cmp /tmp/mw-first-admission-sdk-pin.json "$SDK_ARCHIVE/PROTOCOL_PIN.json"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/admission" "$SDK_ARCHIVE/admission"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/schemas" "$SDK_ARCHIVE/schemas"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/conformance" "$SDK_ARCHIVE/conformance"
  diff -qr "$MW_PROTOCOL_ARCHIVE_ROOT/cryptography" "$SDK_ARCHIVE/cryptography"
done
export MW_MERGED_SDK_ARCHIVE_ROOT
python - <<'PY'
import json
import os
from pathlib import Path

archive_root = Path(os.environ["MW_MERGED_SDK_ARCHIVE_ROOT"])
for language in ("python", "typescript", "go", "rust", "java", "cpp"):
    root = archive_root / language
    pin = json.loads((root / "PROTOCOL_PIN.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / "admission/manifest.json").read_text(encoding="utf-8")
    )
    evaluations = [
        evaluation
        for case in manifest["cases"]
        for evaluation in case["evaluations"]
    ]
    complete = sum(
        evaluation["expect"]["stage"] == "complete"
        for evaluation in evaluations
    )
    assert len(list((root / "schemas").glob("*.json"))) == 22
    assert pin["artifacts"]["schemas"]["files"] == 22
    assert len(list((root / "conformance").rglob("*.json"))) == 59
    assert len(list((root / "conformance/vectors").rglob("*.json"))) == 58
    assert pin["artifacts"]["conformance"]["files"] == 59
    assert pin["cryptography"]["artifactCount"] == 98
    assert pin["cryptography"]["caseCount"] == 22
    assert pin["cryptography"]["evaluationCount"] == 62
    assert pin["cryptography"]["artifactDigest"] == (
        "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
    )
    assert len([path for path in (root / "admission").rglob("*") if path.is_file()]) == 19
    assert len(manifest["artifacts"]) == pin["admission"]["artifactCount"] == 19
    assert len(manifest["cases"]) == pin["admission"]["caseCount"] == 5
    assert len(evaluations) == pin["admission"]["evaluationCount"] == 30
    assert complete == 12
    assert len(evaluations) - complete == 18
    print(language, pin["commit"], pin["admission"]["artifactDigest"])
PY
~~~

- [ ] **Step 10: Preserve all implementation worktrees**

Run:

~~~bash
git -C /Users/lionelmbp/repos/missionweaveprotocol worktree list
git -C /Users/lionelmbp/repos/python-sdk worktree list
git -C /Users/lionelmbp/repos/typescript-sdk worktree list
git -C /Users/lionelmbp/repos/go-sdk worktree list
git -C /Users/lionelmbp/repos/rust-sdk worktree list
git -C /Users/lionelmbp/repos/java-sdk worktree list
git -C /Users/lionelmbp/repos/cpp-sdk worktree list
~~~

Expected: the design worktree, protocol implementation worktree, six SDK worktrees, and all older unrelated worktrees remain present.

### Task 15: Run fresh Spec and Standards reviews against exact merged commits

**Files:**

- Read: approved spec and plan
- Read: exact merged protocol and six SDK trees
- Produce: /tmp/mw-first-admission-spec-review.md
- Produce: /tmp/mw-first-admission-standards-review.md

- [ ] **Step 1: Start a fresh read-only Spec reviewer**

Provide only:

~~~text
TASK_REVISION: MW-V1-2026-07-30-R1
OBJECTIVE: review exact merged protocol and six SDK commits for complete coverage of the approved First-Admission and historical-trust specification.
COMPLETED FACTS: protocol and six SDK PRs are merged; exact commits and CI runs are provided in the evidence JSON.
EXACT NEXT ACTION: build a requirement-by-requirement matrix and report PASS or actionable gaps with file/line evidence.
PROHIBITED: no edits, commits, pushes, PRs, issues, or inferred scope expansion.
STOP: return after checking every acceptance criterion, all 30 evaluations, package paths, and exact-main CI.
~~~

- [ ] **Step 2: Require the Spec review matrix**

The review must separately cover:

~~~text
record Schema and no signature
58 structural vectors
separate six-stage cryptography
current Registry seam
atomic append-or-return-existing
returned-record validation
idempotent retry and conflict
historical rerun and no creation
same-key interval for both instants
adapter authentication/integrity failures
admission / AUTH_INVALID_SIGNATURE mapping
30 evaluations and exact histogram
six public APIs and packages
identical pins and trees
exact-head and exact-main CI
scope exclusions
~~~

The root write lane saves the reviewer's returned report verbatim to `/tmp/mw-first-admission-spec-review.md`. Its first two lines must identify the reviewer and state `Verdict: PASS` or `Verdict: BLOCKED`.

- [ ] **Step 3: Start a fresh read-only Standards reviewer**

Provide only:

~~~text
TASK_REVISION: MW-V1-2026-07-30-R1
OBJECTIVE: independently review trust boundaries, append-only semantics, timestamp handling, JSON/Schema behavior, API non-oracularity, and cross-language consistency at the captured merged commits.
COMPLETED FACTS: exact commits, digests, evaluation totals, and CI runs are supplied.
EXACT NEXT ACTION: identify standards, security, interoperability, or packaging defects; distinguish blockers from non-blocking hardening.
PROHIBITED: no edits or external mutations; do not reopen approved non-goals without concrete evidence.
STOP: return PASS or a bounded defect list with exact evidence.
~~~

The root write lane saves the reviewer's returned report verbatim to `/tmp/mw-first-admission-standards-review.md`. Its first two lines must identify the reviewer and state `Verdict: PASS` or `Verdict: BLOCKED`.

- [ ] **Step 4: Resolve every actionable review finding**

For each actionable defect:

~~~text
reproduce it at that repository's captured merge SHA
decide whether it violates the approved spec
create the smallest corrective branch in the affected repository
use RED/GREEN
rerun native/package/conformance gates
merge and recapture exact-main CI
rerun both reviews on the corrected exact commits
~~~

Do not act on preference-only hardening that is outside the approved slice; record it as non-blocking.

- [ ] **Step 5: Require final review verdicts**

Run:

~~~bash
rg -n '^Reviewer: .+' /tmp/mw-first-admission-spec-review.md
rg -n '^Verdict: PASS$' /tmp/mw-first-admission-spec-review.md
rg -n '^Reviewer: .+' /tmp/mw-first-admission-standards-review.md
rg -n '^Verdict: PASS$' /tmp/mw-first-admission-standards-review.md
~~~

A partial review, review against a branch head, or review without package/CI evidence is insufficient.

### Task 16: Publish one cross-language evidence issue

**Files:**

- Read: /tmp/mw-first-admission-branch-head-audit.json
- Read: /tmp/mw-first-admission-sdk-main-shas.json
- Read: /tmp/mw-first-admission-*-main-ci.json
- Read: /tmp/mw-first-admission-spec-review.md
- Read: /tmp/mw-first-admission-standards-review.md
- Produce: one MissionWeaveProtocol issue

- [ ] **Step 1: Reconfirm external-action scope**

Verify MW-V1-2026-07-30-R1 and confirm the only authorized external action is one cross-language evidence issue after every merge, main CI run, and review passes.

- [ ] **Step 2: Build the evidence body**

Generate the body from captured JSON and GitHub query results:

~~~bash
python - <<'PY'
import hashlib
import json
import re
import subprocess
from pathlib import Path

audit = json.loads(
    Path("/tmp/mw-first-admission-branch-head-audit.json").read_text(encoding="utf-8")
)
main_shas = json.loads(
    Path("/tmp/mw-first-admission-sdk-main-shas.json").read_text(encoding="utf-8")
)
protocol_ci = json.loads(
    Path("/tmp/mw-first-admission-protocol-main-ci.json").read_text(encoding="utf-8")
)
spec_review = Path("/tmp/mw-first-admission-spec-review.md").read_text(encoding="utf-8")
standards_review = Path(
    "/tmp/mw-first-admission-standards-review.md"
).read_text(encoding="utf-8")
pin_digest = hashlib.sha256(
    Path("/tmp/mw-first-admission-sdk-pin.json").read_bytes()
).hexdigest()

protocol_pulls = json.loads(
    subprocess.check_output(
        [
            "gh", "pr", "list",
            "--repo", "MissionWeaveProtocol/missionweaveprotocol",
            "--head", "feat/first-admission-historical-trust",
            "--state", "merged",
            "--limit", "1",
            "--json", "number,mergeCommit,url",
        ],
        text=True,
    )
)
assert len(protocol_pulls) == 1
protocol_pr = protocol_pulls[0]
assert protocol_pr["mergeCommit"]["oid"] == audit["protocolCommit"]
assert protocol_ci["headSha"] == audit["protocolCommit"]
assert protocol_ci["conclusion"] == "success"

repositories = {
    "python": "MissionWeaveProtocol/python-sdk",
    "typescript": "MissionWeaveProtocol/typescript-sdk",
    "go": "MissionWeaveProtocol/go-sdk",
    "rust": "MissionWeaveProtocol/rust-sdk",
    "java": "MissionWeaveProtocol/java-sdk",
    "cpp": "MissionWeaveProtocol/cpp-sdk",
}
rows = []
for language, repository in repositories.items():
    head = audit["headCi"][language]
    main_ci = json.loads(
        Path(f"/tmp/mw-first-admission-{language}-main-ci.json").read_text(
            encoding="utf-8"
        )
    )
    assert main_ci["headSha"] == main_shas[language]
    assert main_ci["conclusion"] == "success"
    head_runs = ", ".join(
        f"{run['databaseId']} ({run['workflowName']})"
        for run in head["runs"]
    )
    rows.append(
        "| "
        + " | ".join(
            [
                language,
                repository,
                str(head["pullRequest"]),
                main_shas[language],
                pin_digest,
                "full native gate passed in exact-head CI",
                "package/install public-consumer gate passed in exact-head CI",
                head_runs,
                f"{main_ci['databaseId']} ({main_ci['workflowName']})",
            ]
        )
        + " |"
    )

java_version = subprocess.run(
    ["java", "-version"],
    capture_output=True,
    text=True,
    check=False,
)
java_text = java_version.stdout + java_version.stderr
java_boundary_lines = []
if java_version.returncode != 0 or re.search(r'version "21(?:[.]|\")', java_text) is None:
    java_boundary_lines = [
        "",
        "Local boundary: Java 21 was unavailable locally; exact-head and exact-main CI supplied Maven verify, package inclusion, and installed-consumer proof.",
    ]

counts = audit["counts"]
lines = [
    "# Cross-language evidence: first-admission historical trust",
    "",
    f"- Task revision: `{audit['taskRevision']}`",
    "- Approved spec commit: `3df7d5c58c9825e43620691e6f8a69e29404bbe1`",
    f"- Protocol PR: #{protocol_pr['number']} ({protocol_pr['url']})",
    f"- Protocol merged commit: `{audit['protocolCommit']}`",
    f"- Protocol exact-main CI: `{protocol_ci['databaseId']}` ({protocol_ci['workflowName']})",
    f"- Cryptography digest: `{audit['cryptographyDigest']}`",
    f"- Admission digest: `{audit['admissionDigest']}`",
    f"- Structural totals: {counts['schemas']} schemas, {counts['structuralVectors']} vectors",
    (
        "- Admission totals: "
        f"{counts['admissionArtifacts']} artifacts, {counts['admissionCases']} cases, "
        f"{counts['admissionEvaluations']} evaluations, "
        f"{counts['admissionComplete']} complete, {counts['admissionRejected']} rejected"
    ),
    "",
    "| SDK | Repository | PR | Merged commit | Pin SHA-256 | Native gate | Package/install gate | Exact-head CI | Exact-main CI |",
    "| --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
    *rows,
    "",
    "Byte audit: all six `PROTOCOL_PIN.json` files and all vendored schemas, conformance, cryptography, and Admission trees were byte-identical to the merged protocol archive.",
    *java_boundary_lines,
    "",
    "## Spec review",
    "",
    spec_review.rstrip(),
    "",
    "## Standards review",
    "",
    standards_review.rstrip(),
    "",
    "## Explicit non-goals",
    "",
    "Command freshness, signer authorization, portable log-proof standardization, state-machine behavior, and worktree cleanup were not implemented.",
    "",
    "All existing design, protocol implementation, SDK implementation, and older unrelated worktrees were preserved.",
]
Path("/tmp/mw-first-admission-evidence.md").write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)
print(Path("/tmp/mw-first-admission-evidence.md").read_text(encoding="utf-8"))
PY
~~~

- [ ] **Step 3: Create the issue**

Run:

~~~bash
EVIDENCE_ISSUE_URL=$(gh issue create \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --title "Cross-language evidence: first-admission historical trust" \
  --body-file /tmp/mw-first-admission-evidence.md)
printf '%s\n' "$EVIDENCE_ISSUE_URL" \
  > /tmp/mw-first-admission-evidence-issue-url.txt
~~~

- [ ] **Step 4: Read the issue back**

Run:

~~~bash
EVIDENCE_ISSUE_URL=$(cat /tmp/mw-first-admission-evidence-issue-url.txt)
gh issue view "$EVIDENCE_ISSUE_URL" \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --json number,title,body,url,state
~~~

Expected: the issue is open and contains every required exact commit, digest, run, review verdict, and verification boundary.

### Task 17: Final acceptance and worktree preservation

**Files:**

- Read only: all exact merged repositories, CI evidence, reviews, and evidence issue

- [ ] **Step 1: Run the final protocol artifact checks from exact merged main**

Run in an archive or detached read-only checkout of the merged protocol commit:

~~~bash
MW_CRYPTO_PYTHON=/Users/lionelmbp/.config/superpowers/venvs/missionweaveprotocol-first-admission-historical-trust/bin/python
"$MW_CRYPTO_PYTHON" scripts/check_repository_policy.py
"$MW_CRYPTO_PYTHON" scripts/validate_protocol.py
"$MW_CRYPTO_PYTHON" scripts/generate_crypto_vectors.py
git diff --exit-code -- cryptography
"$MW_CRYPTO_PYTHON" scripts/validate_crypto_vectors.py
"$MW_CRYPTO_PYTHON" scripts/generate_admission_vectors.py
git diff --exit-code -- admission
"$MW_CRYPTO_PYTHON" scripts/validate_admission_vectors.py
~~~

- [ ] **Step 2: Confirm all acceptance facts**

Require:

~~~text
First-Admission Record is the twenty-second Schema
58 structural vectors include valid record and forbidden signature
cryptography remains 22 cases / 62 evaluations / unchanged digest
Admission is 19 artifacts / 5 cases / 30 evaluations / 12 complete / 18 rejected
every Admission rejection is admission / AUTH_INVALID_SIGNATURE
first admission validates atomic returned record
historical replay reruns crypto and never creates
both instants use the same selected interval
six SDK public APIs and packages pass
all pins and vendored trees are byte-identical
all exact-head and exact-main CI runs pass
both independent reviews pass
evidence issue readback passes
all worktrees remain present
~~~

- [ ] **Step 3: Report exact boundaries**

The completion report names:

~~~text
protocol merged commit and CI run
six SDK merged commits and CI runs
Admission and cryptography digests
22/58, 22/62, and 19/5/30/12/18 totals
review verdicts
evidence issue URL
any legitimate local-toolchain skip
confirmation that no worktree was removed
~~~

Do not claim Command freshness, signer authorization, portable log-proof verification, or state-machine acceptance.

## Plan self-check before execution

Before starting Task 1, the executor should verify:

- Every approved requirement maps to at least one numbered task.
- Every new public type used by a later task is defined in that SDK task.
- Admission-current Registry evidence is distinct from historical Registry evidence.
- The existing VerificationStage type is never extended with admission.
- Every SDK's initial RED suite covers valid first admission, an exclusive time boundary, an existing-record mismatch, later-revocation replay, and log unavailability through its public API.
- The pin is produced once from merged protocol main and copied byte-for-byte.
- The cryptography digest and 62-evaluation meaning never change.
- All code-producing steps have concrete signatures, fields, commands, and expected results.
- No destructive cleanup command appears.
- External actions occur only after the task revision is rechecked.
