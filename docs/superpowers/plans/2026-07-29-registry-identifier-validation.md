# Registry Identifier Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the protocol reference validator and all six SDKs enforce the same absolute RFC 3986 URI rule for every complete-Registry identifier before key selection, backed by four protocol-owned negative evaluations and one shared authoritative bundle pin.

**Architecture:** The protocol repository first makes the test-only Registry fixture Schema structural, generates four single-fault Registry fixtures, and teaches the reference validator to share one strict URI predicate between Schema format handling and stage-4 Registry parsing. After that change is merged, Python, TypeScript, Go, and Rust synchronize the exact merged bundle, demonstrate protocol-owned RED failures, and add their runtime fixes; Java and C++ synchronize the same bundle and prove their existing runtime paths already pass it. Every SDK derives the protocol commit and cryptography digest from the merged protocol `origin/main`, never from a feature commit or a reconstructed value.

**Tech Stack:** Python 3.12/jsonschema/uv; TypeScript/Ajv/Vitest/npm; Go 1.24/santhosh-tekuri jsonschema; Rust 1.85/jsonschema/cargo; Java 21/Maven/JUnit; C++20/CMake/Ninja/jsoncons/OpenSSL; GitHub CLI and GitHub Actions.

---

## Task revision and execution contract

- Active revision: `MW-V1-2026-07-29-R1`.
- Approved design: `docs/superpowers/specs/2026-07-29-registry-identifier-validation-design.md` at local commit `831d439e0f5ef391b7e22e2793fa0b5ce1277917`.
- Execution uses `superpowers:executing-plans`; the root agent owns the only write lane. Subagents may perform independent read-only review, testing, or evidence gathering only.
- Before every push, merge, issue creation, or other externally visible action, re-check the active task revision and objective.
- Use `superpowers:using-git-worktrees` before creating implementation worktrees. Preserve the existing C++ worktree at `/Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence`; its tree matches remote squash commit `357085afd1d586e6bb4162858f1045ebf92503cc`, but its ancestry is not authoritative for new work.
- Do not pin protocol design commit `831d439`, a protocol feature-branch commit, or a locally reconstructed digest. The only valid pin is the merged `origin/main` commit whose tree contains the regenerated cryptography bundle.
- Runtime URI semantics are: non-empty visible ASCII, an absolute RFC 3986 scheme, complete-string consumption, valid URI grammar and percent escapes, `example:` accepted, byte-for-byte retention, and no runtime 512-character limit.
- Final bundle contract: 98 digest-protected artifacts, 22 cases, 62 evaluations, 12 complete, 50 rejected, and 24 `key-resolution` failures.

## File map

### Protocol repository: `/Users/lionelmbp/repos/missionweaveprotocol`

- Modify `cryptography/registry-fixture.schema.json`: test-only bounded structural identifier candidates.
- Modify `scripts/generate_crypto_vectors.py`: generate four Registry fixtures/evaluations and update deterministic counts.
- Modify `scripts/validate_crypto_vectors.py`: shared URI predicate, fixture metadata preflight, stage-4 checks, count contracts, and predicate edge checks.
- Modify `cryptography/README.md`: 62/12/50 counts and the fixture-schema/runtime-semantics boundary.
- Generate `cryptography/manifest.json` and four new `cryptography/keys/registry-*.json` fixtures.

### Python SDK: `/Users/lionelmbp/repos/python-sdk`

- Modify `src/missionweaveprotocol/schema_formats.py`: internal `is_protocol_uri` predicate.
- Modify `src/missionweaveprotocol/signed_documents.py`: validate root, key, and Principal identifiers before indexing.
- Modify `tests/test_conformance.py`, `tests/test_signed_documents.py`, `tests/test_protocol_pin.py`, and `tests/test_package.py`.
- Modify `.github/workflows/ci.yml`, `src/missionweaveprotocol/bundle.py`, `PROTOCOL_PIN.json`, seven localized READMEs, and vendored `cryptography/`.

### TypeScript SDK: `/Users/lionelmbp/repos/typescript-sdk`

- Create `src/protocol-uri.ts`: internal shared predicate; do not export it from `src/index.ts`.
- Modify `src/schema-catalog.ts`, `src/signed-document-codec.ts`, `tests/uri-format.test.ts`, and `tests/signed-document-codec.test.ts`.
- Modify `scripts/protocol-bundle.mjs`, `tests/protocol-bundle.test.mjs`, `PROTOCOL_PIN.json`, seven localized READMEs, and vendored `cryptography/`.

### Go SDK: `/Users/lionelmbp/repos/go-sdk`

- Create `schema_internal_test.go`.
- Modify `schema.go`, `signed_document_verification.go`, `signed_document_codec_test.go`, and `signed_document_conformance_test.go`.
- Modify `bundle.go`, `bundle_test.go`, `PROTOCOL_PIN.json`, seven localized READMEs, and vendored `cryptography/`.
- Keep `go.mod`, `go.sum`, and the schema/conformance-only `JSONFiles == 79` assertion unchanged unless deterministic verification proves unrelated drift.

### Rust SDK: `/Users/lionelmbp/repos/rust-sdk`

- Modify `src/schema.rs`, `src/signed_document.rs`, `tests/signed_document_codec.rs`, and `src/bundle.rs`.
- Modify `PROTOCOL_PIN.json`, seven localized READMEs, and vendored `cryptography/`.
- Keep `Cargo.toml` and `Cargo.lock` unchanged.

### Java SDK: `/Users/lionelmbp/repos/java-sdk`

- Modify `PROTOCOL_PIN.json`, `src/main/java/org/missionweaveprotocol/sdk/ProtocolBundle.java`, `src/test/java/org/missionweaveprotocol/sdk/SignedDocumentCodecTest.java`, `docs/conformance.md`, `scripts/check_documentation.py`, seven localized READMEs, and vendored `cryptography/`.
- Do not change Registry runtime code unless the synchronized evaluations expose a concrete failure.

### C++ SDK: `MissionWeaveProtocol/cpp-sdk`

- Modify `PROTOCOL_PIN.json`, `src/bundle.cpp`, `tests/bundle_test.cpp`, `tests/signed_document_test.cpp`, `scripts/generate_embedded_assets.py`, generated `src/embedded_assets.cpp`, `scripts/check_readmes.py`, seven localized READMEs, and vendored `cryptography/`.
- Do not change Registry runtime code unless the synchronized evaluations expose a concrete failure.

### Cross-repository evidence

- Verify all six `PROTOCOL_PIN.json` files agree on protocol commit, cryptography source commit, artifact digest, artifact count, case count, and evaluation count.
- Record merged PRs, exact commits, native verification, installed-consumer checks, and exact-commit CI in one MissionWeaveProtocol tracking issue.

### Task 1: Create the isolated protocol implementation lane

**Files:**
- Read: `docs/superpowers/specs/2026-07-29-registry-identifier-validation-design.md`
- Read: `docs/superpowers/plans/2026-07-29-registry-identifier-validation.md`
- Worktree: `/Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/registry-identifier-validation-impl`

- [ ] **Step 1: Load the execution and worktree skills**

Read `superpowers:executing-plans` and `superpowers:using-git-worktrees` completely before creating or editing any implementation worktree.

- [ ] **Step 2: Verify the design checkout is clean and contains the approved spec and plan**

Run:

```bash
git -C /Users/lionelmbp/repos/missionweaveprotocol status --short --branch
git -C /Users/lionelmbp/repos/missionweaveprotocol log -2 --oneline
```

Expected: branch `design/registry-identifier-validation`, no worktree changes, and the latest two documentation commits are the approved design plus this implementation plan.

- [ ] **Step 3: Fetch without changing the design checkout**

Run:

```bash
git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin
git -C /Users/lionelmbp/repos/missionweaveprotocol status --short --branch
```

Expected: fetch succeeds and the design checkout remains clean.

- [ ] **Step 4: Create the protocol implementation worktree from the design branch**

Run:

```bash
git -C /Users/lionelmbp/repos/missionweaveprotocol worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/missionweaveprotocol/registry-identifier-validation-impl \
  -b fix/registry-identifier-validation \
  design/registry-identifier-validation
```

Expected: the new worktree is on `fix/registry-identifier-validation`, includes the approved spec and plan, and the original checkout remains on the design branch.

- [ ] **Step 5: Establish the protocol baseline**

Run from the new worktree:

```bash
.venv-cryptography/bin/python scripts/check_repository_policy.py
.venv-cryptography/bin/python scripts/validate_protocol.py
.venv-cryptography/bin/python scripts/validate_crypto_vectors.py
git status --short --branch
```

Expected: all three checks pass against the old 94-artifact/58-evaluation bundle and the worktree is clean. If `.venv-cryptography` is absent, create the hash-locked environment exactly as documented in `cryptography/README.md` before rerunning.

### Task 2: Add the protocol-owned Registry identifier vectors and prove RED

**Files:**
- Modify: `cryptography/registry-fixture.schema.json`
- Modify: `scripts/generate_crypto_vectors.py:686-687,1519-1638,1717-1753`
- Modify: `scripts/validate_crypto_vectors.py:85-140,957-1107,2271-2309`
- Generate: `cryptography/manifest.json`
- Create: `cryptography/keys/registry-organization-id-relative-reference.json`
- Create: `cryptography/keys/registry-selected-service-principal-id-iri-only.json`
- Create: `cryptography/keys/registry-unrelated-principal-id-malformed-percent.json`
- Create: `cryptography/keys/registry-unrelated-key-id-trailing-line-feed.json`

- [ ] **Step 1: Make the fixture Schema structural instead of semantic**

Replace all three `$defs.absoluteId` references with `$defs.identifierCandidate`, and replace the definition with:

```json
"identifierCandidate": {
  "type": "string",
  "minLength": 1,
  "maxLength": 512
}
```

Do not change any file under `schemas/`; the 512-character bound remains a test-artifact bound only.

- [ ] **Step 2: Generate four single-field Registry mutations**

Insert immediately after `registry-valid.json` is written:

```python
registry_organization_id_relative_reference = copy.deepcopy(registry)
registry_organization_id_relative_reference["organizationId"] = "organizations/acme"
registry_organization_id_relative_reference_path = _write_json(
    "cryptography/keys/registry-organization-id-relative-reference.json",
    registry_organization_id_relative_reference,
)

registry_selected_service_principal_id_iri_only = copy.deepcopy(registry)
_find_binding(
    registry_selected_service_principal_id_iri_only,
    keys["organization-registry"]["keyId"],
)["principal"]["id"] = "https://例え.テスト/services/organization-registry"
registry_selected_service_principal_id_iri_only_path = _write_json(
    "cryptography/keys/registry-selected-service-principal-id-iri-only.json",
    registry_selected_service_principal_id_iri_only,
)

registry_unrelated_principal_id_malformed_percent = copy.deepcopy(registry)
_find_binding(
    registry_unrelated_principal_id_malformed_percent,
    keys["security-owner"]["keyId"],
)["principal"]["id"] = "urn:missionweaveprotocol:human:security-owner%GG"
registry_unrelated_principal_id_malformed_percent_path = _write_json(
    "cryptography/keys/registry-unrelated-principal-id-malformed-percent.json",
    registry_unrelated_principal_id_malformed_percent,
)

registry_unrelated_key_id_trailing_line_feed = copy.deepcopy(registry)
_find_binding(
    registry_unrelated_key_id_trailing_line_feed,
    keys["security-owner"]["keyId"],
)["keyId"] += "\n"
registry_unrelated_key_id_trailing_line_feed_path = _write_json(
    "cryptography/keys/registry-unrelated-key-id-trailing-line-feed.json",
    registry_unrelated_key_id_trailing_line_feed,
)
```

The `security-owner` binding is unrelated to the Command's selected coordinator key. Keep key-based lookup; do not use array indexes.

- [ ] **Step 3: Add the four evaluations to `reject.key-resolution.matrix`**

Add these entries to the sorted evaluation list:

```python
_failure_evaluation(
    fault_id="registry-organization-id-relative-reference",
    document_path=document_paths["command"],
    registry_path=registry_organization_id_relative_reference_path,
    stage="key-resolution",
    wire_code="AUTH_INVALID_SIGNATURE",
),
_failure_evaluation(
    fault_id="registry-selected-service-principal-id-iri-only",
    profile_id="agent-card",
    basis_case_id="accept.profile-matrix.all-nine",
    basis_profile_id="agent-card",
    document_path=document_paths["agent-card"],
    registry_path=registry_selected_service_principal_id_iri_only_path,
    stage="key-resolution",
    wire_code="AUTH_INVALID_SIGNATURE",
),
_failure_evaluation(
    fault_id="registry-unrelated-principal-id-malformed-percent",
    document_path=document_paths["command"],
    registry_path=registry_unrelated_principal_id_malformed_percent_path,
    stage="key-resolution",
    wire_code="AUTH_INVALID_SIGNATURE",
),
_failure_evaluation(
    fault_id="registry-unrelated-key-id-trailing-line-feed",
    document_path=document_paths["command"],
    registry_path=registry_unrelated_key_id_trailing_line_feed_path,
    stage="key-resolution",
    wire_code="AUTH_INVALID_SIGNATURE",
),
```

- [ ] **Step 4: Update the generator and manifest contracts**

Change the generator's evaluation assertion from 58 to 62. In `scripts/validate_crypto_vectors.py`:

- change `EXPECTED_FAILURE_HISTOGRAM["key-resolution"]` from 20 to 24;
- register each new fault in `EXPECTED_FAULT_SURFACES` with value `"registry"`;
- change `reject.key-resolution.matrix` size from 15 to 19;
- change total/rejected contracts from `58/12/46` to `62/12/50`;
- change the runner tuple and success text to 62 evaluations, 12 complete, and 50 rejected.

- [ ] **Step 5: Add a preflight that proves each fixture has exactly one declared mutation**

Add this helper and call it beside `_validate_timestamp_profile_coverage` before `_validate_fixture_structures`:

```python
def _validate_registry_identifier_faults(
    manifest: Mapping[str, Any], cache: Mapping[str, bytes]
) -> None:
    valid_path = "cryptography/keys/registry-valid.json"
    valid = _parse_cached_json(cache, valid_path, label=valid_path)
    if not isinstance(valid, dict):
        raise _bundle_error("valid Registry fixture is not an object")

    expected_fixtures: dict[str, tuple[str, Mapping[str, Any]]] = {}

    organization = copy.deepcopy(valid)
    organization["organizationId"] = "organizations/acme"
    expected_fixtures["registry-organization-id-relative-reference"] = (
        "cryptography/keys/registry-organization-id-relative-reference.json",
        organization,
    )

    selected = copy.deepcopy(valid)
    selected_binding = next(
        binding
        for binding in selected["bindings"]
        if binding["keyId"]
        == "urn:missionweaveprotocol:key:crypto-vector-organization-registry"
    )
    selected_binding["principal"]["id"] = (
        "https://例え.テスト/services/organization-registry"
    )
    expected_fixtures["registry-selected-service-principal-id-iri-only"] = (
        "cryptography/keys/registry-selected-service-principal-id-iri-only.json",
        selected,
    )

    principal = copy.deepcopy(valid)
    principal_binding = next(
        binding
        for binding in principal["bindings"]
        if binding["keyId"]
        == "urn:missionweaveprotocol:key:crypto-vector-security-owner"
    )
    principal_binding["principal"]["id"] = (
        "urn:missionweaveprotocol:human:security-owner%GG"
    )
    expected_fixtures["registry-unrelated-principal-id-malformed-percent"] = (
        "cryptography/keys/registry-unrelated-principal-id-malformed-percent.json",
        principal,
    )

    key_id = copy.deepcopy(valid)
    key_binding = next(
        binding
        for binding in key_id["bindings"]
        if binding["keyId"]
        == "urn:missionweaveprotocol:key:crypto-vector-security-owner"
    )
    key_binding["keyId"] += "\n"
    expected_fixtures["registry-unrelated-key-id-trailing-line-feed"] = (
        "cryptography/keys/registry-unrelated-key-id-trailing-line-feed.json",
        key_id,
    )

    matrix = next(
        case
        for case in manifest["cases"]
        if case["id"] == "reject.key-resolution.matrix"
    )
    evaluations = {
        evaluation["fault"]["id"]: evaluation
        for evaluation in matrix["evaluations"]
        if evaluation["fault"]["id"] in expected_fixtures
    }
    if set(evaluations) != set(expected_fixtures):
        raise _bundle_error("Registry identifier evaluations are incomplete")

    for fault_id, (fixture_path, expected_fixture) in expected_fixtures.items():
        actual_fixture = _parse_cached_json(cache, fixture_path, label=fixture_path)
        if actual_fixture != expected_fixture:
            raise _bundle_error(
                f"fault {fault_id!r} is not the declared single-field mutation"
            )
        evaluation = evaluations[fault_id]
        expected_profile = (
            "agent-card"
            if fault_id == "registry-selected-service-principal-id-iri-only"
            else "command"
        )
        expected_document = (
            "cryptography/vectors/signed-documents/valid/agent-card.json"
            if expected_profile == "agent-card"
            else "cryptography/vectors/signed-documents/valid/command.json"
        )
        expected_basis = (
            {"caseId": "accept.profile-matrix.all-nine", "profileId": "agent-card"}
            if expected_profile == "agent-card"
            else {"caseId": "accept.command.golden", "profileId": "command"}
        )
        if (
            evaluation["profileId"] != expected_profile
            or evaluation["document"] != expected_document
            or evaluation["registry"] != fixture_path
            or evaluation["fault"]["basis"] != expected_basis
            or evaluation["expect"]
            != {"stage": "key-resolution", "wireCode": "AUTH_INVALID_SIGNATURE"}
        ):
            raise _bundle_error(f"fault {fault_id!r} metadata is incorrect")
```

- [ ] **Step 6: Regenerate the bundle**

Run:

```bash
.venv-cryptography/bin/python scripts/generate_crypto_vectors.py
```

Expected:

```text
Generated MissionWeaveProtocol cryptography bundle: 22 cases, 62 evaluations, 98 artifacts.
```

- [ ] **Step 7: Run the reference validator and capture the required RED**

Run:

```bash
.venv-cryptography/bin/python scripts/validate_crypto_vectors.py
```

Expected: non-zero exit with:

```text
Cryptography vector validation failed: case 'reject.key-resolution.matrix' expected failure at 'key-resolution' but verification completed
```

Do not weaken the fixtures or change the expected stage to make this pass.

- [ ] **Step 8: Commit the protocol-owned RED contract**

Run:

```bash
git add cryptography/registry-fixture.schema.json \
  cryptography/manifest.json \
  cryptography/keys/registry-organization-id-relative-reference.json \
  cryptography/keys/registry-selected-service-principal-id-iri-only.json \
  cryptography/keys/registry-unrelated-principal-id-malformed-percent.json \
  cryptography/keys/registry-unrelated-key-id-trailing-line-feed.json \
  scripts/generate_crypto_vectors.py \
  scripts/validate_crypto_vectors.py
git commit -m "test(crypto): add Registry identifier failure vectors"
```

Expected: commit succeeds, and the branch intentionally remains RED only until Task 3.

### Task 3: Implement the protocol reference URI predicate and make the vectors GREEN

**Files:**
- Modify: `scripts/validate_crypto_vectors.py:1387-1400,1647-1655,1826-1870`

- [ ] **Step 1: Add the shared predicate and direct edge contract**

Use a separate standards checker so the custom `uri` registration cannot recurse:

```python
_PROTOCOL_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_INVALID_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")

_STANDARD_FORMAT_CHECKER = FormatChecker()
PROTOCOL_FORMAT_CHECKER = FormatChecker()


@PROTOCOL_FORMAT_CHECKER.checks("uri")
def _is_protocol_uri(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and all(0x21 <= ord(character) <= 0x7E for character in value)
        and _PROTOCOL_URI_SCHEME_RE.match(value) is not None
        and _INVALID_PERCENT_ESCAPE_RE.search(value) is None
        and _STANDARD_FORMAT_CHECKER.conforms(value, "uri")
    )
```

Add a validator contract that accepts `example:`, `example:/path`, `urn:example:%E2%82%AC`, a valid IPv6 authority, and a valid URI longer than 512 characters; reject empty, relative, invalid-scheme, raw non-ASCII, malformed-percent, trailing-line-feed, and malformed-authority values.

- [ ] **Step 2: Validate the Registry root before allocating uniqueness maps**

Immediately after the root string check, add:

```python
organization_id = registry_object["organizationId"]
if not _is_protocol_uri(organization_id):
    raise _semantic(
        "key-resolution", "Registry organizationId is not a protocol URI"
    )
```

Use `organization_id` in the returned `ResolvedKey`; do not normalize it.

- [ ] **Step 3: Validate every binding key ID before Principal parsing or indexing**

Immediately after the binding `keyId` string check, add:

```python
if not _is_protocol_uri(key_id):
    raise _semantic(
        "key-resolution", f"{prefix}.keyId is not a protocol URI"
    )
```

- [ ] **Step 4: Validate every Principal ID in `_principal`**

After the existing string check, add:

```python
if not _is_protocol_uri(principal["id"]):
    raise _semantic(stage, f"{label}.id is not a protocol URI")
```

This applies to every binding, including unselected bindings, before any uniqueness-map insertion.

- [ ] **Step 5: Run the focused predicate and bundle checks**

Run:

```bash
.venv-cryptography/bin/python scripts/validate_crypto_vectors.py
```

Expected: all four new evaluations reject at `key-resolution` with `AUTH_INVALID_SIGNATURE`, the long URI and `example:` contract pass, and the final line reports 22 cases, 62 evaluations, 12 complete, 50 rejected, and a generated digest.

- [ ] **Step 6: Commit the runtime fix**

Run:

```bash
git add scripts/validate_crypto_vectors.py
git commit -m "fix(crypto): validate complete Registry identifiers"
```

Expected: commit succeeds and the protocol validator is GREEN.

### Task 4: Document and fully verify the protocol bundle

**Files:**
- Modify: `cryptography/README.md:3-9,23-27,58-64`

- [ ] **Step 1: Update the cryptography bundle contract**

Change the README to state:

- 22 cases and 62 evaluations;
- 12 complete and 50 rejected;
- the four exact Registry identifier faults fail at stage 4;
- the Registry fixture Schema proves JSON shape and a 1–512 character test-artifact bound only;
- runtime validation owns URI semantics for all Registry identifiers, performs no normalization, and applies no 512-character runtime limit.

- [ ] **Step 2: Commit the documentation**

Run:

```bash
git add cryptography/README.md
git commit -m "docs(crypto): document Registry identifier coverage"
```

- [ ] **Step 3: Run every protocol gate**

Run:

```bash
.venv-cryptography/bin/python scripts/check_repository_policy.py
.venv-cryptography/bin/python scripts/validate_protocol.py
.venv-cryptography/bin/python scripts/validate_crypto_vectors.py
.venv-cryptography/bin/python scripts/generate_crypto_vectors.py
git diff --exit-code -- cryptography/manifest.json cryptography/keys cryptography/vectors
git status --short --branch
```

Expected: all checks pass, the second generation produces no diff, and the only branch difference from its base is the intended spec/plan/vector/runtime/documentation commit series.

- [ ] **Step 4: Audit the generated manifest counts directly**

Run:

```bash
jq -r '
[
  (.artifacts | length),
  (.cases | length),
  ([.cases[].evaluations[]] | length),
  ([.cases[] as $case | $case.evaluations[]
    | select($case.kind == "canonicalization" or .expect.stage == "complete")] | length),
  ([.cases[] as $case | $case.evaluations[]
    | select($case.kind != "canonicalization" and .expect.stage != "complete")] | length),
  ([.cases[].evaluations[] | select(.expect.stage == "key-resolution")] | length)
] | @tsv
' cryptography/manifest.json
```

Expected:

```text
98	22	62	12	50	24
```

### Task 5: Land the protocol change and capture the only authoritative pin

**Files:**
- Read: `cryptography/manifest.json`
- Remote: `MissionWeaveProtocol/missionweaveprotocol`

- [ ] **Step 1: Reconfirm the task revision, clean tree, and exact outgoing commits**

Run:

```bash
git status --short --branch
git log --oneline origin/main..HEAD
```

Expected: clean `fix/registry-identifier-validation` branch containing only the approved design, plan, vector, runtime, and documentation commits.

- [ ] **Step 2: Push and create the protocol PR**

Run:

```bash
git push -u origin fix/registry-identifier-validation
gh pr create \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Validate complete Registry identifiers before key selection" \
  --body "Adds four protocol-owned Registry identifier failures, keeps the test-only fixture Schema structural, validates every complete-Registry identifier at key resolution, and deterministically moves the bundle to 98 artifacts and 62 evaluations."
```

Expected: the push and PR creation succeed and return one PR URL.

- [ ] **Step 3: Wait for the protocol PR checks and inspect failures instead of guessing**

Run:

```bash
gh pr checks --repo MissionWeaveProtocol/missionweaveprotocol --watch
```

Expected: repository policy, protocol artifacts, and cryptography artifacts all pass. If any check fails, inspect its exact logs, make only the scoped correction, rerun local gates, commit, and push before continuing.

- [ ] **Step 4: Merge the protocol PR and fetch the merged branch**

Run:

```bash
gh pr merge \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --squash
git fetch origin main
```

Expected: PR is merged and `origin/main` advances to a commit whose tree contains the verified bundle.

- [ ] **Step 5: Derive and validate the authoritative bundle facts**

Run in one shell session for the remaining tasks:

```bash
PROTOCOL_COMMIT="$(git rev-parse origin/main)"
CRYPTO_MANIFEST="$(git show "$PROTOCOL_COMMIT:cryptography/manifest.json")"
CRYPTO_DIGEST="$(jq -r '.artifactDigest' <<<"$CRYPTO_MANIFEST")"
CRYPTO_ARTIFACTS="$(jq '.artifacts | length' <<<"$CRYPTO_MANIFEST")"
CRYPTO_CASES="$(jq '.cases | length' <<<"$CRYPTO_MANIFEST")"
CRYPTO_EVALUATIONS="$(jq '[.cases[].evaluations[]] | length' <<<"$CRYPTO_MANIFEST")"
test "$CRYPTO_ARTIFACTS" = 98
test "$CRYPTO_CASES" = 22
test "$CRYPTO_EVALUATIONS" = 62
git show "$PROTOCOL_COMMIT:cryptography/registry-fixture.schema.json" | \
  jq -e '."$defs".identifierCandidate == {"type":"string","minLength":1,"maxLength":512}'
```

Expected: every assertion passes. Preserve these exact shell variables or re-derive them from `origin/main` at the start of every SDK task.

- [ ] **Step 6: Verify the merged `main` workflow at the exact merged commit**

Run:

```bash
gh run list \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --commit "$PROTOCOL_COMMIT" \
  --workflow "Protocol validation" \
  --limit 1 \
  --json databaseId,headSha,status,conclusion
```

Expected: `headSha` equals `$PROTOCOL_COMMIT` and the run concludes `success` before any SDK pin is changed.

### Task 6: Fix and land the Python SDK

**Files:**
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/python-sdk/registry-identifier-validation`
- Modify: `src/missionweaveprotocol/schema_formats.py`
- Modify: `src/missionweaveprotocol/signed_documents.py`
- Modify: `tests/test_conformance.py`
- Modify: `tests/test_signed_documents.py`
- Modify: `tests/test_protocol_pin.py`
- Modify: `tests/test_package.py`
- Modify: `src/missionweaveprotocol/bundle.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `PROTOCOL_PIN.json`
- Modify: `README.md`, `README.zh-CN.md`, `README.zh-TW.md`, `README.ja.md`, `README.es.md`, `README.fr.md`, `README.de.md`
- Replace: `cryptography/`

- [ ] **Step 1: Create a clean SDK worktree from current remote main**

Run:

```bash
git -C /Users/lionelmbp/repos/python-sdk fetch origin
git -C /Users/lionelmbp/repos/python-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/python-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main
```

Expected: clean worktree based on `origin/main`; do not reuse or modify `/Users/lionelmbp/repos/python-sdk/main` directly.

- [ ] **Step 2: Re-derive the authoritative protocol facts and vendor only that merged tree**

Run:

```bash
git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: the vendored manifest reports 98 artifacts, 22 cases, and 62 evaluations; `$PROTOCOL_COMMIT` is the merged protocol `origin/main` commit.

- [ ] **Step 3: Update bundle pins and count assertions without changing schema/conformance digests**

Using `apply_patch`, put the exact `$PROTOCOL_COMMIT` in both `commit` and `cryptography.sourceCommit`, the exact `$CRYPTO_DIGEST` in `artifactDigest`, and set artifact/case/evaluation counts to `98/22/62` in:

- `PROTOCOL_PIN.json`;
- `src/missionweaveprotocol/bundle.py`;
- `tests/test_protocol_pin.py`.

In `tests/test_signed_documents.py`, assert 22 cases, 62 evaluations, 12 complete, and 50 rejected. Preserve the existing schema digest, conformance digest, `bundleSha256`, lockfile, and dependency versions; fail if deterministic verification says any of those changed.

- [ ] **Step 4: Prove the synchronized protocol-owned evaluations are RED**

Run before changing runtime code:

```bash
uv run pytest \
  tests/test_signed_documents.py::test_executes_all_protocol_owned_cryptography_evaluations
```

Expected: FAIL because one or more of the four new rejected evaluations completes successfully. Preserve this output as RED evidence.

- [ ] **Step 5: Add focused predicate tests and prove the trailing-line-feed gap**

Add to `tests/test_conformance.py`:

```python
from jsonschema.exceptions import FormatError

from missionweaveprotocol.schema_formats import protocol_format_checker


@pytest.mark.parametrize(
    "value",
    [
        "organizations/acme",
        "1example:value",
        "urn:missionweaveprotocol:key:value\n",
        "https://agents.example/注册表",
        "example:%GG",
        "http://[zzz]",
    ],
)
def test_protocol_uri_checker_rejects_invalid_values(value: str) -> None:
    with pytest.raises(FormatError):
        protocol_format_checker().check(value, "uri")


@pytest.mark.parametrize(
    "value",
    [
        "example:",
        "https://agents.example/" + "a" * 600,
    ],
)
def test_protocol_uri_checker_accepts_valid_values(value: str) -> None:
    protocol_format_checker().check(value, "uri")
```

Run:

```bash
uv run pytest tests/test_conformance.py -k protocol_uri_checker
```

Expected RED: the trailing-line-feed case reports `DID NOT RAISE FormatError`.

- [ ] **Step 6: Add public-codec tests for all three identifier locations and unrelated bindings**

Add this helper to `tests/test_signed_documents.py`:

```python
def _assert_registry_identifier_rejected(
    kind: SignedDocumentKind,
    document_path: str,
    registry: dict[str, object],
    diagnostic: str,
) -> None:
    resolver = AgentRegistryKeyResolver(
        json.dumps(registry, ensure_ascii=False, separators=(",", ":")).encode()
    )
    with pytest.raises(SignedDocumentVerificationError) as rejected:
        SignedDocumentCodec().verify(
            kind,
            (ROOT / document_path).read_bytes(),
            resolver,
        )

    assert rejected.value.protected_error.stage is VerificationStage.KEY_RESOLUTION
    assert rejected.value.wire_error.code.value == "AUTH_INVALID_SIGNATURE"
    assert diagnostic in rejected.value.protected_error.reason
```

Add four named tests that deep-copy `cryptography/keys/registry-valid.json` and perform these exact mutations:

```python
registry["organizationId"] = "organizations/acme"

selected = next(
    binding
    for binding in registry["bindings"]
    if binding["keyId"]
    == "urn:missionweaveprotocol:key:crypto-vector-organization-registry"
)
selected["principal"]["id"] = "https://agents.example/注册表"

unrelated = next(
    binding
    for binding in registry["bindings"]
    if binding["keyId"]
    == "urn:missionweaveprotocol:key:crypto-vector-developer-one"
)
unrelated["principal"]["id"] = "example:%GG"

unrelated = next(
    binding
    for binding in registry["bindings"]
    if binding["keyId"]
    == "urn:missionweaveprotocol:key:crypto-vector-developer-one"
)
unrelated["keyId"] += "\n"
```

Use Command for the root and unrelated mutations, Agent Card for the selected service Principal mutation, and assert diagnostic suffixes `organizationId is not a protocol URI`, `.principal.id is not a protocol URI`, and `.keyId is not a protocol URI`. Add a positive test whose `organizationId` is a valid URI longer than 512 characters and assert `resolved_key.organization_id` retains the exact value.

Run:

```bash
uv run pytest tests/test_signed_documents.py -k registry_identifier
```

Expected RED: all four rejection tests report `DID NOT RAISE SignedDocumentVerificationError`; the long valid identifier remains accepted.

- [ ] **Step 7: Implement the shared Python predicate**

In `src/missionweaveprotocol/schema_formats.py`, replace the current private URI checker with:

```python
_STANDARD_FORMAT_CHECKER = FormatChecker()
_ABSOLUTE_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_MALFORMED_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def is_protocol_uri(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        return False
    if _ABSOLUTE_SCHEME.match(value) is None:
        return False
    try:
        _STANDARD_FORMAT_CHECKER.check(value, "uri")
    except FormatError:
        return False
    return _MALFORMED_PERCENT_ESCAPE.search(value) is None
```

Register `is_protocol_uri` in `protocol_format_checker()`. Keep it internal to `schema_formats.py`; do not export it from package `__init__.py`.

- [ ] **Step 8: Apply the predicate before any Registry index insertion**

Import `is_protocol_uri` in `signed_documents.py`. Validate the root immediately after reading it:

```python
if not isinstance(organization_id, str) or not is_protocol_uri(organization_id):
    _verification_failure(
        VerificationStage.KEY_RESOLUTION,
        "Registry organizationId is not a protocol URI",
    )
```

Validate every binding key ID before uniqueness-map insertion:

```python
if not isinstance(key_id, str) or not is_protocol_uri(key_id):
    _verification_failure(
        VerificationStage.KEY_RESOLUTION,
        f"{label}.keyId is not a protocol URI",
    )
```

In `_principal`, after the current type/string checks, add:

```python
if not is_protocol_uri(principal_id):
    _verification_failure(stage, f"{label}.id is not a protocol URI")
```

Preserve byte-for-byte values and the existing `key-resolution`/`AUTH_INVALID_SIGNATURE` mapping.

- [ ] **Step 9: Make focused and protocol-owned tests GREEN**

Run:

```bash
uv run pytest \
  tests/test_conformance.py \
  tests/test_signed_documents.py \
  tests/test_protocol_pin.py \
  tests/test_package.py
```

Expected: all selected tests pass; the manifest runner executes 62 evaluations with 12 complete and 50 rejected.

- [ ] **Step 10: Update packaged-resource smoke and localized documentation**

In the installed-wheel CI block, verify the packaged cryptography bundle outside the checkout:

```python
from missionweaveprotocol import verify_cryptography_bundle

summary = verify_cryptography_bundle()
assert summary.artifact_count == 98
assert summary.case_count == 22
assert summary.evaluation_count == 62
```

Update all seven localized README protocol-commit links to `$PROTOCOL_COMMIT`, link `cryptography/README.md` beside `PROTOCOL_PIN.json`, and state that the wheel packages both conformance and cryptography resources. Do not change public API exports.

- [ ] **Step 11: Run the complete Python gates**

Run:

```bash
uv sync --extra dev --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run missionweaveprotocol-conformance --root .
uv build
```

Expected: Ruff passes, formatting is clean, mypy reports no issues, all tests pass with only the two known PostgreSQL skips when the CI database is absent, conformance reports `56/56`, and the wheel/sdist contain the pin plus all 98 cryptography artifacts.

- [ ] **Step 12: Commit the green Python changes in reviewable units**

Run:

```bash
git add src/missionweaveprotocol/schema_formats.py \
  src/missionweaveprotocol/signed_documents.py \
  tests/test_conformance.py \
  tests/test_signed_documents.py
git commit -m "fix(crypto): validate Registry identifiers before key selection"

git add PROTOCOL_PIN.json \
  src/missionweaveprotocol/bundle.py \
  tests/test_protocol_pin.py \
  tests/test_package.py \
  cryptography
git commit -m "chore(protocol): sync Registry identifier cryptography bundle"

git add .github/workflows/ci.yml README.md README.*.md
git commit -m "docs(packaging): describe pinned cryptography resources"
```

Expected: clean worktree and all three commits are GREEN together.

- [ ] **Step 13: Push, merge, and verify Python remote state**

Run:

```bash
git push -u origin fix/registry-identifier-validation
gh pr create \
  --repo MissionWeaveProtocol/python-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Validate complete Registry identifier URIs" \
  --body "Pins the merged 62-evaluation protocol bundle, validates every Registry identifier before selection, and verifies packaged cryptography resources."
gh pr checks --repo MissionWeaveProtocol/python-sdk --watch
gh pr merge --repo MissionWeaveProtocol/python-sdk --squash
git fetch origin main
```

Expected: PR checks pass, PR merges, and remote `main` contains the exact `$PROTOCOL_COMMIT`, `$CRYPTO_DIGEST`, 98 artifacts, and 62 evaluations.

### Task 7: Fix and land the TypeScript SDK

**Files:**
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/registry-identifier-validation`
- Create: `src/protocol-uri.ts`
- Modify: `src/schema-catalog.ts`
- Modify: `src/signed-document-codec.ts`
- Modify: `tests/uri-format.test.ts`
- Modify: `tests/signed-document-codec.test.ts`
- Modify: `scripts/protocol-bundle.mjs`
- Modify: `tests/protocol-bundle.test.mjs`
- Modify: `PROTOCOL_PIN.json`
- Modify: seven localized READMEs
- Replace: `cryptography/`

- [ ] **Step 1: Create a clean TypeScript worktree and synchronize the authoritative bundle**

Run:

```bash
git -C /Users/lionelmbp/repos/typescript-sdk fetch origin
git -C /Users/lionelmbp/repos/typescript-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/typescript-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main

git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: clean SDK branch plus the exact merged 98-artifact/62-evaluation bundle.

- [ ] **Step 2: Update pins, bundle constants, and manifest counts**

Using `apply_patch`, put `$PROTOCOL_COMMIT`, `$CRYPTO_DIGEST`, and `98/22/62` in `PROTOCOL_PIN.json`, `scripts/protocol-bundle.mjs`, and `tests/protocol-bundle.test.mjs`. In `tests/signed-document-codec.test.ts`, update:

- total evaluations `58` to `62`;
- signed-document evaluations `57` to `61` because canonicalization remains separate;
- complete signed evaluations at `11`;
- `key-resolution` histogram `20` to `24`;
- rejected total `46` to `50` where asserted.

Keep schema/conformance digests, `bundleSha256`, `package.json`, `package-lock.json`, and committed `dist/` unchanged.

- [ ] **Step 3: Prove the synchronized protocol-owned evaluations are RED**

Run before changing runtime code:

```bash
npx vitest run tests/signed-document-codec.test.ts -t "stops at key resolution"
```

Expected: 24 selected evaluations, with the existing 20 passing and the four new identifier evaluations failing because verification did not throw.

- [ ] **Step 4: Add direct predicate and public-codec RED tests**

Extend `tests/uri-format.test.ts` with relative references, missing/invalid schemes, trailing LF/tab/space, raw non-ASCII, `%`, `%2`, `%GG`, invalid IPv6 authority, `example:`, and a valid 600-character URI.

In `tests/signed-document-codec.test.ts`, add:

```ts
type MutableRegistry = {
  bindings: Array<{
    keyId: string;
    principal: { id: string; type: string };
  }>;
  organizationId: string;
};
```

Use a table with these exact mutations:

```ts
registry.organizationId = "organizations/acme";

const selected = registry.bindings.find(
  ({ keyId }) =>
    keyId ===
    "urn:missionweaveprotocol:key:crypto-vector-organization-registry",
);
if (!selected) throw new TypeError("Expected selected service binding");
selected.principal.id = "urn:missionweaveprotocol:service:组织-registry";

const unrelatedPrincipal = registry.bindings.find(
  ({ keyId }) =>
    keyId === "urn:missionweaveprotocol:key:crypto-vector-developer-one",
);
if (!unrelatedPrincipal) throw new TypeError("Expected unrelated binding");
unrelatedPrincipal.principal.id = "urn:missionweaveprotocol:agent:%GG";

const unrelatedKey = registry.bindings.find(
  ({ keyId }) =>
    keyId === "urn:missionweaveprotocol:key:crypto-vector-developer-one",
);
if (!unrelatedKey) throw new TypeError("Expected unrelated binding");
unrelatedKey.keyId += "\n";
```

For every mutation, call the public codec with an Organization-wide snapshot and assert `SignedDocumentVerificationError`, `auditDetail.stage === "key-resolution"`, and `wireCode === "AUTH_INVALID_SIGNATURE"`. Add positive cases for `example:` and a valid identifier longer than 512 characters.

Run:

```bash
npx vitest run tests/uri-format.test.ts tests/signed-document-codec.test.ts -t "Registry identifier|protocol URI"
```

Expected RED: the malformed Registry cases are accepted and at least the permissive trailing-line-feed URI case fails the predicate expectation.

- [ ] **Step 5: Create the internal shared predicate**

Create `src/protocol-uri.ts`:

```ts
import * as formatsNamespace from "ajv-formats";
import type { FormatsPlugin } from "ajv-formats";

const addFormats = formatsNamespace.default as unknown as FormatsPlugin;
const ajvFullUriFormat: unknown = addFormats.get("uri", "full");
const nonVisibleAsciiCharacter = /[^\x21-\x7e]/u;
const absoluteSchemePrefix = /^[A-Za-z][A-Za-z0-9+.-]*:/u;
const malformedPercentEscape = /%(?![0-9A-Fa-f]{2})/u;
const emptyHierPartUri =
  /^[A-Za-z][A-Za-z0-9+.-]*:(?:\?(?:[A-Za-z0-9._~!$&'()*+,;=:@/?-]|%[0-9A-Fa-f]{2})*)?(?:#(?:[A-Za-z0-9._~!$&'()*+,;=:@/?-]|%[0-9A-Fa-f]{2})*)?$/u;

export function isProtocolUri(value: string): boolean {
  if (
    value.length === 0 ||
    nonVisibleAsciiCharacter.test(value) ||
    !absoluteSchemePrefix.test(value) ||
    malformedPercentEscape.test(value)
  ) {
    return false;
  }
  return matchesFormat(ajvFullUriFormat, value) || emptyHierPartUri.test(value);
}

function matchesFormat(format: unknown, value: string): boolean {
  if (format instanceof RegExp) {
    format.lastIndex = 0;
    const matches = format.test(value);
    format.lastIndex = 0;
    return matches;
  }
  if (typeof format === "function") {
    return Boolean((format as (input: string) => boolean)(value));
  }
  if (typeof format === "object" && format !== null && "validate" in format) {
    return matchesFormat(
      (format as { readonly validate: unknown }).validate,
      value,
    );
  }
  throw new TypeError(
    "ajv-formats did not provide a synchronous URI validator",
  );
}
```

Do not re-export this helper from `src/index.ts`.

- [ ] **Step 6: Share the predicate with SchemaCatalog and complete Registry parsing**

In `src/schema-catalog.ts`, register:

```ts
ajv.addFormat("uri", {
  type: "string",
  validate: isProtocolUri,
});
```

In `resolveSnapshot()`, validate the root before constructing maps:

```ts
const organizationId = snapshot["organizationId"];
if (
  typeof organizationId !== "string" ||
  !Array.isArray(snapshot["bindings"]) ||
  snapshot["bindings"].length === 0
) {
  verificationFailure("key-resolution", "Invalid Agent Registry snapshot");
}
if (!isProtocolUri(organizationId)) {
  verificationFailure(
    "key-resolution",
    "Agent Registry organizationId is not a protocol URI",
  );
}
```

In `normalizeBinding()`, validate before public-key/history normalization and before any uniqueness map sees the binding:

```ts
if (!isProtocolUri(keyId)) {
  verificationFailure(
    "key-resolution",
    `Registry binding ${index} keyId is not a protocol URI`,
  );
}
const principal = principalFromValue(
  rawBinding["principal"],
  "key-resolution",
  `Registry binding ${index} Principal`,
);
if (!isProtocolUri(principal.id)) {
  verificationFailure(
    "key-resolution",
    `Registry binding ${index} Principal.id is not a protocol URI`,
  );
}
```

Return the validated `organizationId` variable and preserve every identifier byte-for-byte.

- [ ] **Step 7: Make focused and bundle tests GREEN**

Run:

```bash
npx vitest run \
  tests/uri-format.test.ts \
  tests/signed-document-codec.test.ts \
  tests/protocol-bundle.test.mjs
```

Expected: all three files pass; all 24 key-resolution evaluations reject correctly; bundle verification reports 98 artifacts, 22 cases, and 62 evaluations.

- [ ] **Step 8: Update localized protocol links and cryptography wording**

Replace the old protocol commit in all seven READMEs with `$PROTOCOL_COMMIT`, update any 58-evaluation statement to 62, and link the vendored `cryptography/README.md`. Keep code fences and link targets synchronized across translations.

- [ ] **Step 9: Run the complete TypeScript gates**

Run separately so failures retain clear boundaries:

```bash
npm run format:check
npm run lint
npm run typecheck
npm run typecheck:examples
npm run check:pin
npm run test
npm run build
npm run package:check
npm run package:smoke
npm run check
```

Expected: every command exits zero; `check:pin` reports 98 cryptography artifacts, 22 cases, and 62 evaluations; package smoke works outside the checkout; `publint` reports no errors.

- [ ] **Step 10: Commit, push, merge, and verify TypeScript remote state**

Run:

```bash
git add src/protocol-uri.ts src/schema-catalog.ts src/signed-document-codec.ts \
  tests/uri-format.test.ts tests/signed-document-codec.test.ts
git commit -m "fix(crypto): validate Registry identifier URIs"

git add PROTOCOL_PIN.json scripts/protocol-bundle.mjs \
  tests/protocol-bundle.test.mjs cryptography README.md README.*.md
git commit -m "chore(protocol): pin Registry identifier evaluations"

git push -u origin fix/registry-identifier-validation
gh pr create \
  --repo MissionWeaveProtocol/typescript-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Validate complete Registry identifier URIs" \
  --body "Shares one internal RFC 3986 predicate between Ajv and Registry parsing, then pins the merged 62-evaluation bundle."
gh pr checks --repo MissionWeaveProtocol/typescript-sdk --watch
gh pr merge --repo MissionWeaveProtocol/typescript-sdk --squash
git fetch origin main
```

Expected: clean merged remote `main` with the exact authoritative protocol SHA/digest and no generated `dist/` drift.

### Task 8: Fix and land the Go SDK

**Files:**
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/go-sdk/registry-identifier-validation`
- Create: `schema_internal_test.go`
- Modify: `schema.go`
- Modify: `signed_document_verification.go`
- Modify: `signed_document_codec_test.go`
- Modify: `signed_document_conformance_test.go`
- Modify: `bundle.go`
- Modify: `bundle_test.go`
- Modify: `PROTOCOL_PIN.json`
- Modify: seven localized READMEs
- Replace: `cryptography/`

- [ ] **Step 1: Create a clean Go worktree and synchronize the authoritative bundle**

Run:

```bash
git -C /Users/lionelmbp/repos/go-sdk fetch origin
git -C /Users/lionelmbp/repos/go-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/go-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main

git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: clean branch from Go remote main plus the merged 98-artifact/62-evaluation cryptography tree.

- [ ] **Step 2: Update pin constants and count assertions**

Using `apply_patch`, set the exact `$PROTOCOL_COMMIT`, `$CRYPTO_DIGEST`, and `98/22/62` values in `PROTOCOL_PIN.json`, `bundle.go`, and `bundle_test.go`. Change `signed_document_conformance_test.go` from `58/12/46` to `62/12/50`, and add an explicit `keyResolution == 24` assertion:

```go
keyResolution := 0
// inside the evaluation loop
if evaluation.Expect.Stage == "key-resolution" {
	keyResolution++
}
// after the loop
if evaluations != 62 || completed != 12 || rejected != 50 || keyResolution != 24 {
	t.Fatalf(
		"cryptography counts = %d evaluations, %d complete, %d rejected, %d key-resolution; want 62/12/50/24",
		evaluations,
		completed,
		rejected,
		keyResolution,
	)
}
```

Keep the `JSONFiles == 79` assertion, `go.mod`, `go.sum`, schema/conformance digests, and `bundleSha256` unchanged.

- [ ] **Step 3: Prove the synchronized protocol-owned evaluations are RED**

Run before runtime changes:

```bash
go test . -run '^TestSignedDocumentCodecPassesAllCryptographyEvaluations$' -count=1
```

Expected RED: four new evaluations report that a `SignedDocumentVerificationError` was expected but `nil` was returned.

- [ ] **Step 4: Add the package-private predicate test and prove RED**

Create `schema_internal_test.go`:

```go
package missionweaveprotocol

import (
	"strings"
	"testing"
)

func TestIsProtocolURI(t *testing.T) {
	tests := []struct {
		name  string
		value string
		want  bool
	}{
		{"empty hierarchical part", "example:", true},
		{"ordinary absolute URI", "urn:missionweaveprotocol:organization:acme", true},
		{"long identifier", "urn:example:" + strings.Repeat("a", 600), true},
		{"relative reference", "organizations/acme", false},
		{"missing scheme", "//example.test/path", false},
		{"invalid scheme", "1example:value", false},
		{"trailing line feed", "https://example.test/path\n", false},
		{"raw IRI", "https://例え.テスト/path", false},
		{"malformed percent escape", "urn:example:%GG", false},
		{"invalid IPv6 authority", "https://[::gg]/", false},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := isProtocolURI(test.value); got != test.want {
				t.Fatalf("isProtocolURI(%q) = %v; want %v", test.value, got, test.want)
			}
		})
	}
}
```

Run:

```bash
go test . -run '^TestIsProtocolURI$' -count=1
```

Expected RED: build failure containing `undefined: isProtocolURI`.

- [ ] **Step 5: Add public-codec tests that locate unrelated bindings by key ID**

Add to `signed_document_codec_test.go`:

```go
func registryBindingByKeyID(
	t *testing.T,
	registry map[string]any,
	keyID string,
) map[string]any {
	t.Helper()
	for _, raw := range registry["bindings"].([]any) {
		binding := raw.(map[string]any)
		if binding["keyId"] == keyID {
			return binding
		}
	}
	t.Fatalf("Registry binding %q was not found", keyID)
	return nil
}
```

Create one table test with these exact mutations:

```go
registry["organizationId"] = "organizations/acme"

registryBindingByKeyID(
	t,
	registry,
	"urn:missionweaveprotocol:key:crypto-vector-organization-registry",
)["principal"].(map[string]any)["id"] = "https://例え.テスト/service"

registryBindingByKeyID(
	t,
	registry,
	"urn:missionweaveprotocol:key:crypto-vector-developer-one",
)["principal"].(map[string]any)["id"] = "urn:example:%GG"

unrelated := registryBindingByKeyID(
	t,
	registry,
	"urn:missionweaveprotocol:key:crypto-vector-developer-one",
)
unrelated["keyId"] = unrelated["keyId"].(string) + "\n"
```

Marshal the mutated Registry, call the public codec, and assert:

```go
var failure *missionweaveprotocol.SignedDocumentVerificationError
if !errors.As(err, &failure) {
	t.Fatalf("expected SignedDocumentVerificationError, got %T: %v", err, err)
}
if failure.ProtectedDiagnostic().Stage() != missionweaveprotocol.VerificationKeyResolution ||
	failure.WireCode() != missionweaveprotocol.WireAuthInvalidSignature {
	t.Fatalf(
		"failure = %s/%s: %s",
		failure.ProtectedDiagnostic().Stage(),
		failure.WireCode(),
		failure.ProtectedDiagnostic().Reason(),
	)
}
```

Use Command except for the selected service Principal case, which uses Agent Card. Add a positive test with a valid `organizationId` longer than 512 characters and assert `verified.ResolvedKey().OrganizationID()` is byte-identical.

- [ ] **Step 6: Implement one immutable, lazily compiled URI Schema**

In `schema.go`, add `sync` and:

```go
const protocolURISchemaID = "https://missionweaveprotocol.dev/internal/protocol-uri.schema.json"

var protocolURISchema = sync.OnceValue(func() *jsonschema.Schema {
	compiler := jsonschema.NewCompiler()
	compiler.DefaultDraft(jsonschema.Draft2020)
	compiler.AssertFormat()
	compiler.UseRegexpEngine(compileECMAScript)

	definition := map[string]any{
		"$id":     protocolURISchemaID,
		"type":    "string",
		"format":  "uri",
		"pattern": "^[A-Za-z][A-Za-z0-9+.-]*:",
		"not": map[string]any{
			"pattern": `[^A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]`,
		},
	}
	if err := compiler.AddResource(protocolURISchemaID, definition); err != nil {
		panic(err)
	}
	return compiler.MustCompile(protocolURISchemaID)
})

func isProtocolURI(value string) bool {
	return protocolURISchema().Validate(value) == nil
}
```

Do not add `maxLength`; runtime evidence is not capped at the fixture Schema's 512 characters.

- [ ] **Step 7: Validate every Registry identifier before map writes**

Immediately after reading `organizationID`:

```go
if !isProtocolURI(organizationID) {
	return ResolvedKeyEvidence{}, verificationFailure(
		VerificationKeyResolution,
		"Registry organizationId is not a protocol URI",
	)
}
```

Immediately after reading each `keyID`:

```go
if !isProtocolURI(keyID) {
	return ResolvedKeyEvidence{}, verificationFailure(
		VerificationKeyResolution,
		label+".keyId is not a protocol URI",
	)
}
```

Immediately after parsing each Principal:

```go
if !isProtocolURI(principal.ID) {
	return ResolvedKeyEvidence{}, verificationFailure(
		VerificationKeyResolution,
		label+".principal.id is not a protocol URI",
	)
}
```

Leave key selection after the existing complete scan.

- [ ] **Step 8: Make focused and protocol-owned tests GREEN**

Run:

```bash
go test . -run '^(TestIsProtocolURI|TestSignedDocumentCodecRejectsMalformedRegistryIdentifiersBeforeSelection|TestSignedDocumentCodecDoesNotApplyFixtureOnlyIdentifierLengthLimit|TestSignedDocumentCodecPassesAllCryptographyEvaluations)$' -count=1
```

Expected: all selected tests pass and the public wire behavior remains `AUTH_INVALID_SIGNATURE`.

- [ ] **Step 9: Update seven READMEs and run all Go gates**

Replace the old protocol commit with `$PROTOCOL_COMMIT` and every 58-evaluation statement with 62 in all seven localized READMEs. Then run:

```bash
go mod tidy
git diff --exit-code -- go.mod go.sum
go run ./internal/cmd/repository-policy
test -z "$(gofmt -l .)"
go vet ./...
go test -race -cover ./...
go run ./cmd/missionweaveprotocol-conformance
go run ./cmd/missionweaveprotocol-conformance --root .
go build ./...
```

Expected: all commands pass and conformance remains `56/56`.

- [ ] **Step 10: Verify installed CLI and compiled embedded-bundle consumers**

Run:

```bash
mw_go_install_dir="$(mktemp -d)"
GOBIN="$mw_go_install_dir" go install ./cmd/missionweaveprotocol-conformance
(cd "$mw_go_install_dir" && ./missionweaveprotocol-conformance)

mw_go_smoke_dir="$(mktemp -d)"
go build -o "$mw_go_smoke_dir/bundle-smoke" ./internal/cmd/bundle-smoke
(cd "$mw_go_smoke_dir" && ./bundle-smoke)
```

Expected: conformance reports `56/56`, and bundle smoke identifies `$PROTOCOL_COMMIT` while verifying 98/22/62.

- [ ] **Step 11: Commit, push, merge, and verify Go remote state**

Run:

```bash
git add schema.go schema_internal_test.go signed_document_verification.go \
  signed_document_codec_test.go signed_document_conformance_test.go
git commit -m "fix(crypto): validate Registry identifier URIs"

git add PROTOCOL_PIN.json bundle.go bundle_test.go cryptography
git commit -m "chore(protocol): pin Registry identifier evaluations"

git add README.md README.*.md
git commit -m "docs: update cryptography evaluation counts"

git push -u origin fix/registry-identifier-validation
gh pr create \
  --repo MissionWeaveProtocol/go-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Validate complete Registry identifier URIs" \
  --body "Adds one shared lazy RFC 3986 validator, rejects malformed unrelated bindings before selection, and pins the merged 62-evaluation bundle."
gh pr checks --repo MissionWeaveProtocol/go-sdk --watch
gh pr merge --repo MissionWeaveProtocol/go-sdk --squash
git fetch origin main
```

Expected: Go remote main is green and pins the same authoritative protocol commit and digest.

### Task 9: Fix and land the Rust SDK

**Files:**
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/registry-identifier-validation`
- Modify: `src/schema.rs`
- Modify: `src/signed_document.rs`
- Modify: `tests/signed_document_codec.rs`
- Modify: `src/bundle.rs`
- Modify: `PROTOCOL_PIN.json`
- Modify: seven localized READMEs
- Replace: `cryptography/`

- [ ] **Step 1: Create a clean Rust worktree and synchronize the authoritative bundle**

Run:

```bash
git -C /Users/lionelmbp/repos/rust-sdk fetch origin
git -C /Users/lionelmbp/repos/rust-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/rust-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main

git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: clean Rust branch plus the authoritative 98-artifact/62-evaluation bundle.

- [ ] **Step 2: Update pins and count assertions**

Using `apply_patch`, put `$PROTOCOL_COMMIT`, `$CRYPTO_DIGEST`, and `98/22/62` in `PROTOCOL_PIN.json` and `src/bundle.rs`. Change the manifest assertion in `tests/signed_document_codec.rs` from `(22, 58, 12, 46)` to `(22, 62, 12, 50)`. Keep schema/conformance digests, `bundleSha256`, `Cargo.toml`, and `Cargo.lock` unchanged.

- [ ] **Step 3: Prove the synchronized manifest and focused Registry cases are RED**

Add public tests that locate bindings by key ID and mutate:

- root `organizationId` to `organizations/acme` for Command;
- selected Organization Registry service `principal.id` to `https://例.example/registry` for Agent Card;
- unrelated developer `principal.id` to `urn:missionweaveprotocol:agent:%GG` for Command;
- unrelated developer `keyId` by appending a line feed for Command.

Use this assertion helper:

```rust
fn assert_registry_identifier_rejected(
    case: &str,
    kind: SignedDocumentKind,
    document_path: &str,
    diagnostic_suffix: &str,
    mutate: impl FnOnce(&mut Value),
) {
    let mut registry = read_json("cryptography/keys/registry-valid.json");
    mutate(&mut registry);
    let resolver = FixtureKeyResolver {
        registry: serde_json::to_vec(&registry).expect("Registry JSON"),
    };
    let raw = read_bytes(document_path);

    let error = match SignedDocumentCodec::new()
        .expect("codec")
        .verify(kind, &raw, &resolver)
    {
        Err(error) => error,
        Ok(_) => panic!("{case}: malformed Registry identifier was accepted"),
    };

    assert_eq!(error.diagnostic().stage(), VerificationStage::KeyResolution);
    assert_eq!(error.wire_code(), WireErrorCode::AuthInvalidSignature);
    assert!(error.diagnostic().reason().ends_with(diagnostic_suffix));
    assert_eq!(error.to_string(), "AUTH_INVALID_SIGNATURE");
}
```

Run:

```bash
cargo test --locked --test signed_document_codec registry_identifier_ -- --nocapture
cargo test --locked --test signed_document_codec \
  satisfies_every_vendored_cryptography_manifest_evaluation -- --exact --nocapture
```

Expected RED: four focused tests panic with `malformed Registry identifier was accepted`, and the manifest test reports `negative vector should fail`.

- [ ] **Step 4: Add predicate unit tests**

Inside `src/schema.rs` tests, add:

```rust
use super::{SchemaCatalog, is_protocol_uri};

#[test]
fn protocol_uri_rejects_malformed_inputs() {
    for value in [
        "organizations/acme",
        "1example:value",
        "example:trailing ",
        "example:\n",
        "https://例.example/path",
        "example:%GG",
        "https://[not-an-ip]/",
    ] {
        assert!(!is_protocol_uri(value), "{value:?} should be rejected");
    }
}

#[test]
fn protocol_uri_accepts_empty_hier_part_and_long_values() {
    assert!(is_protocol_uri("example:"));
    let long = format!("example:{}", "a".repeat(600));
    assert!(long.len() > 512);
    assert!(is_protocol_uri(&long));
}
```

- [ ] **Step 5: Implement the shared Rust predicate and SchemaCatalog registration**

In `src/schema.rs`:

```rust
use std::{collections::BTreeMap, sync::LazyLock};

use jsonschema::{Draft, Registry};
use serde_json::{Value, json};

static PROTOCOL_URI_VALIDATOR: LazyLock<jsonschema::Validator> = LazyLock::new(|| {
    jsonschema::options()
        .with_draft(Draft::Draft202012)
        .should_validate_formats(true)
        .build(&json!({"type": "string", "format": "uri"}))
        .expect("protocol URI schema must compile")
});

pub(crate) fn is_protocol_uri(value: &str) -> bool {
    if !value.bytes().all(|byte| byte.is_ascii_graphic()) {
        return false;
    }

    let Some((scheme, _)) = value.split_once(':') else {
        return false;
    };
    let mut scheme = scheme.bytes();
    if !scheme
        .next()
        .is_some_and(|byte| byte.is_ascii_alphabetic())
        || !scheme.all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'+' | b'-' | b'.')
        })
    {
        return false;
    }

    PROTOCOL_URI_VALIDATOR.is_valid(&Value::String(value.to_owned()))
}
```

Register it before the date-time handler:

```rust
.with_format("uri", is_protocol_uri)
.with_format("date-time", crate::signed_document::is_protocol_rfc3339)
```

- [ ] **Step 6: Validate every Registry identifier before indexing**

Import `schema::is_protocol_uri` into `src/signed_document.rs` and add:

```rust
fn require_protocol_uri(
    value: &str,
    stage: VerificationStage,
    label: &str,
) -> Result<(), VerificationError> {
    if is_protocol_uri(value) {
        Ok(())
    } else {
        Err(VerificationError::at(
            stage,
            format!("{label} is not a protocol URI"),
        ))
    }
}
```

Call it immediately after reading root `organizationId`, each `keyId`, and each parsed `principal.id`:

```rust
require_protocol_uri(
    organization_id,
    VerificationStage::KeyResolution,
    "Registry organizationId",
)?;

require_protocol_uri(
    key_id,
    VerificationStage::KeyResolution,
    &format!("{label}.keyId"),
)?;

require_protocol_uri(
    principal.id(),
    VerificationStage::KeyResolution,
    &format!("{label}.principal.id"),
)?;
```

Perform these calls before the first `normalized`, public-key-owner, or tuple-ID insertion. Do not add normalization or a length check.

- [ ] **Step 7: Make focused, manifest, and bundle tests GREEN**

Run:

```bash
cargo test --locked --lib schema::tests::protocol_uri_ -- --nocapture
cargo test --locked --test signed_document_codec registry_identifier_ -- --nocapture
cargo test --locked --test signed_document_codec \
  satisfies_every_vendored_cryptography_manifest_evaluation -- --exact
cargo test --locked --lib \
  bundle::tests::verifies_exact_embedded_cryptography_bundle -- --exact
```

Expected: two predicate tests, four public-codec tests, all 62 manifest evaluations, and exact bundle integrity pass.

- [ ] **Step 8: Update localized commit references and run every Rust gate**

Replace the old protocol commit with `$PROTOCOL_COMMIT` and any 58-evaluation wording with 62 in all seven localized READMEs. Then run:

```bash
node scripts/check-repository-policy.mjs
cargo fmt --all --check
cargo clippy --locked --all-targets --all-features -- -D warnings
cargo test --locked --all-features
cargo run --locked --quiet --bin missionweaveprotocol-conformance
cargo package --locked
mw_rust_install_root="$(mktemp -d)"
cargo install --locked --path . --root "$mw_rust_install_root"
"$mw_rust_install_root/bin/missionweaveprotocol-conformance"
```

Expected: all commands pass; both conformance runs report `56/56`; the package contains the exact pin and cryptography tree.

- [ ] **Step 9: Commit, push, merge, and verify Rust remote state**

Run:

```bash
git add src/schema.rs src/signed_document.rs tests/signed_document_codec.rs
git commit -m "fix(crypto): validate Registry identifier URIs"

git add PROTOCOL_PIN.json src/bundle.rs cryptography
git commit -m "chore(protocol): pin Registry identifier evaluations"

git add README.md README.*.md
git commit -m "docs(protocol): refresh Registry bundle references"

git push -u origin fix/registry-identifier-validation
gh pr create \
  --repo MissionWeaveProtocol/rust-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Validate complete Registry identifier URIs" \
  --body "Shares one crate-private RFC 3986 predicate between SchemaCatalog and complete Registry parsing, then pins the merged 62-evaluation bundle."
gh pr checks --repo MissionWeaveProtocol/rust-sdk --watch
gh pr merge --repo MissionWeaveProtocol/rust-sdk --squash
git fetch origin main
```

Expected: Rust remote main is green and pins the same authoritative protocol commit and digest.

### Task 10: Synchronize and land the Java SDK without speculative runtime changes

**Files:**
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/java-sdk/registry-identifier-validation`
- Modify: `PROTOCOL_PIN.json`
- Modify: `src/main/java/org/missionweaveprotocol/sdk/ProtocolBundle.java`
- Modify: `src/test/java/org/missionweaveprotocol/sdk/SignedDocumentCodecTest.java`
- Modify: `docs/conformance.md`
- Modify: `scripts/check_documentation.py`
- Modify: seven localized READMEs
- Replace: `cryptography/`

- [ ] **Step 1: Create a clean Java worktree and synchronize the authoritative bundle**

Run:

```bash
git -C /Users/lionelmbp/repos/java-sdk fetch origin
git -C /Users/lionelmbp/repos/java-sdk worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/java-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main

git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: clean Java branch with the exact merged bundle.

- [ ] **Step 2: Update the Java pin, constants, and manifest totals**

Using `apply_patch`, replace the current protocol SHA literal in `ProtocolBundle.COMMIT` with the concrete value of `$PROTOCOL_COMMIT`; replace both current cryptography identity literals with `$PROTOCOL_COMMIT` and `$CRYPTO_DIGEST`; and set these numeric constants exactly:

```java
public static final int CRYPTOGRAPHY_ARTIFACT_COUNT = 98;
public static final int CRYPTOGRAPHY_CASE_COUNT = 22;
public static final int CRYPTOGRAPHY_EVALUATION_COUNT = 62;
```

Apply the same concrete SHA/digest/count values to `PROTOCOL_PIN.json`, then use the Step 6 `jq` assertion to prove the Java constants and pin represent the merged bundle. Preserve schema/conformance digests and `bundleSha256`.

In `SignedDocumentCodecTest.matchesAllSignedDocumentCryptographyEvaluations()`, change only:

```java
assertEquals(62, evaluations);
assertEquals(12, completed);
assertEquals(50, rejected);
assertEquals(1, canonicalizationEvaluations);
```

- [ ] **Step 3: Run the new evaluations before touching runtime code**

First check local Java availability:

```bash
java -version
```

If Java 21 is available, run:

```bash
./mvnw -B -ntp \
  -Dtest=SignedDocumentCodecTest,ProtocolBundleTest \
  test
```

Expected: GREEN with all 62 evaluations, including the four new `key-resolution` failures. If the host still has no JDK, record that boundary and continue to exact-commit GitHub CI in Step 8; do not infer runtime success from source inspection alone.

- [ ] **Step 4: Keep Java runtime code unchanged unless evidence fails**

Inspect `git diff -- src/main/java/org/missionweaveprotocol/sdk/SignedDocumentCodec.java src/main/java/org/missionweaveprotocol/sdk/SchemaCatalog.java`.

Expected: empty diff. A runtime edit is allowed only if Step 3 or exact-commit CI shows one of the four new evaluations failing; in that event, stop the bundle-only path, diagnose the exact Java URI seam, add a focused RED test, and make the smallest bounded correction.

- [ ] **Step 5: Update conformance and localized documentation**

In `docs/conformance.md`, replace 58/46 with 62/50 and state that every complete Registry identifier, including unrelated bindings, is validated before selection. Update all seven localized README commit links to `$PROTOCOL_COMMIT`, link `cryptography/README.md`, and state 62 evaluations. In `scripts/check_documentation.py`, replace the required old protocol commit with `$PROTOCOL_COMMIT` and add `62` or the exact phrase `62 cryptography evaluations` to the required synchronized facts.

- [ ] **Step 6: Run all locally available non-JDK checks**

Run:

```bash
python3 scripts/check_repository_policy.py
python3 scripts/check_documentation.py
jq -e \
  --arg commit "$PROTOCOL_COMMIT" \
  --arg digest "$CRYPTO_DIGEST" \
  '.commit == $commit
   and .cryptography.sourceCommit == $commit
   and .cryptography.artifactDigest == $digest
   and .cryptography.artifactCount == 98
   and .cryptography.caseCount == 22
   and .cryptography.evaluationCount == 62' \
  PROTOCOL_PIN.json
```

Expected: all checks pass.

- [ ] **Step 7: Commit and push the Java bundle-only change**

Run:

```bash
git add PROTOCOL_PIN.json \
  src/main/java/org/missionweaveprotocol/sdk/ProtocolBundle.java \
  src/test/java/org/missionweaveprotocol/sdk/SignedDocumentCodecTest.java \
  docs/conformance.md \
  scripts/check_documentation.py \
  README.md README.*.md \
  cryptography
git commit -m "chore(protocol): pin Registry identifier evaluations"
JAVA_BRANCH_SHA="$(git rev-parse HEAD)"
git push -u origin fix/registry-identifier-validation
JAVA_PR_URL="$(gh pr create \
  --repo MissionWeaveProtocol/java-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Pin Registry identifier cryptography evaluations" \
  --body "Synchronizes the merged 62-evaluation bundle and proves the existing complete-Registry Java path rejects all four malformed identifiers before key selection.")"
```

Expected: one clean commit, pushed branch, and one PR URL.

- [ ] **Step 8: Require exact-commit Java CI evidence**

Run:

```bash
gh pr checks "$JAVA_PR_URL" --repo MissionWeaveProtocol/java-sdk --watch
gh run list \
  --repo MissionWeaveProtocol/java-sdk \
  --commit "$JAVA_BRANCH_SHA" \
  --workflow CI \
  --limit 1 \
  --json databaseId,headSha,status,conclusion
```

Expected: CI `headSha` equals `$JAVA_BRANCH_SHA` and concludes `success`; `./mvnw -B -ntp verify` plus installed-consumer smoke pass. This is mandatory if local Java remains unavailable.

- [ ] **Step 9: Merge Java and verify the exact merged-main run**

Run:

```bash
gh pr merge "$JAVA_PR_URL" \
  --repo MissionWeaveProtocol/java-sdk \
  --squash
JAVA_MERGED_SHA="$(gh pr view "$JAVA_PR_URL" \
  --repo MissionWeaveProtocol/java-sdk \
  --json mergeCommit \
  --jq '.mergeCommit.oid')"
JAVA_RUN_ID="$(gh run list \
  --repo MissionWeaveProtocol/java-sdk \
  --commit "$JAVA_MERGED_SHA" \
  --workflow CI \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId')"
gh run watch "$JAVA_RUN_ID" \
  --repo MissionWeaveProtocol/java-sdk \
  --exit-status
```

Expected: the push-to-main workflow for `$JAVA_MERGED_SHA` succeeds. If the run has not appeared yet, yield a status update and repeat the read-only `gh run list` query; do not claim Java completion early.

### Task 11: Synchronize and land the C++ SDK without speculative runtime changes

**Files:**
- Preserve: `/Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence`
- Create worktree: `/Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/registry-identifier-validation`
- Modify: `PROTOCOL_PIN.json`
- Modify: `src/bundle.cpp`
- Modify: `tests/bundle_test.cpp`
- Modify: `tests/signed_document_test.cpp`
- Modify: `scripts/generate_embedded_assets.py`
- Generate: `src/embedded_assets.cpp`
- Modify: `scripts/check_readmes.py`
- Modify: seven localized READMEs
- Replace: `cryptography/`

- [ ] **Step 1: Verify and preserve the existing C++ evidence worktree**

Run:

```bash
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  status --short --branch
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  diff --exit-code 357085afd1d586e6bb4162858f1045ebf92503cc -- .
```

Expected: clean worktree and no tree diff from the authoritative prior squash commit. Do not remove or repurpose it.

- [ ] **Step 2: Fetch remote main and create a fresh authoritative C++ branch**

Run:

```bash
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  fetch origin main
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  worktree add \
  /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/registry-identifier-validation \
  -b fix/registry-identifier-validation \
  origin/main
```

Expected: new C++ worktree starts from current remote main rather than the stale `/Users/lionelmbp/repos/cpp-sdk` checkout or the preserved feature ancestry.

- [ ] **Step 3: Synchronize the merged protocol bundle**

Run in the new C++ worktree:

```bash
git -C /Users/lionelmbp/repos/missionweaveprotocol fetch origin main
PROTOCOL_COMMIT="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_COMMIT:cryptography/manifest.json" | jq -r '.artifactDigest')"
PROTOCOL_EXPORT="$(mktemp -d)"
git -C /Users/lionelmbp/repos/missionweaveprotocol archive \
  "$PROTOCOL_COMMIT" cryptography | tar -x -C "$PROTOCOL_EXPORT"
rsync -a --delete "$PROTOCOL_EXPORT/cryptography/" cryptography/
```

Expected: exact 98-artifact/62-evaluation bundle, including the four new Registry fixtures.

- [ ] **Step 4: Update C++ pins, counts, and generated-asset contract**

Using `apply_patch`, set `$PROTOCOL_COMMIT`, `$CRYPTO_DIGEST`, and `98/22/62` in:

- `PROTOCOL_PIN.json`;
- `src/bundle.cpp` embedded pin;
- `tests/bundle_test.cpp` pin and verified-summary assertions;
- `tests/signed_document_test.cpp` totals `62/12/50`.

Change `scripts/generate_embedded_assets.py` from 86 to 90 cryptography files:

```python
if len(cryptography) != 90:
    raise RuntimeError(
        f"expected 90 cryptography files, found {len(cryptography)}"
    )
```

Keep schema/conformance digests and `bundleSha256` unchanged unless deterministic verification proves otherwise.

- [ ] **Step 5: Regenerate embedded assets and prove the existing runtime path is GREEN**

Run:

```bash
python3 scripts/generate_embedded_assets.py
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DMISSIONWEAVEPROTOCOL_WARNINGS_AS_ERRORS=ON
cmake --build build --target \
  missionweaveprotocol_bundle_test \
  missionweaveprotocol_signed_document_test
ctest --test-dir build \
  -R 'bundle|signed_document$' \
  --output-on-failure
```

Expected: the regenerated `src/embedded_assets.cpp` contains four additional Registry assets, and the bundle plus all 62 signed-document evaluations pass without runtime source changes.

- [ ] **Step 6: Keep C++ runtime code unchanged unless the new evidence fails**

Run:

```bash
git diff --exit-code -- \
  include/missionweaveprotocol/signed_document.hpp \
  src/signed_document.cpp \
  src/agent_registry_key_resolution.cpp \
  src/schema.cpp
```

Expected: empty diff. If a new evaluation fails, stop the bundle-only path, diagnose the exact failure using the existing strict URI seam, add a focused RED test, and make only the bounded runtime correction required by evidence.

- [ ] **Step 7: Update localized README checks**

In all seven localized READMEs, replace the old protocol commit with `$PROTOCOL_COMMIT`, change `58 cryptography evaluations` to `62 cryptography evaluations`, and preserve the documented complete-Registry validation claim. In `scripts/check_readmes.py`, require the exact new commit, the unchanged `bundleSha256`, and `62 cryptography evaluations`.

- [ ] **Step 8: Run the complete C++ CI-equivalent gate**

Run:

```bash
python3 scripts/check_repository_policy.py
python3 scripts/check_readmes.py
python3 scripts/generate_embedded_assets.py
git diff --exit-code -- src/embedded_assets.cpp
cmake --build build --parallel
ctest --test-dir build --output-on-failure
build/missionweaveprotocol-conformance
mw_cpp_install_root="$(mktemp -d)"
cmake --install build --prefix "$mw_cpp_install_root"
cmake -S tests/package-consumer -B build/consumer -G Ninja \
  -DCMAKE_PREFIX_PATH="$mw_cpp_install_root"
cmake --build build/consumer
build/consumer/consumer
"$mw_cpp_install_root/bin/missionweaveprotocol-conformance"
```

Expected: all tests and both source/installed conformance runs pass at `56/56`; the installed consumer verifies the exact pin and 98/22/62 cryptography bundle.

- [ ] **Step 9: Commit, push, merge, and verify C++ remote state**

Run:

```bash
git add PROTOCOL_PIN.json src/bundle.cpp tests/bundle_test.cpp \
  tests/signed_document_test.cpp scripts/generate_embedded_assets.py \
  src/embedded_assets.cpp cryptography
git commit -m "chore(protocol): pin Registry identifier evaluations"

git add scripts/check_readmes.py README.md README.*.md
git commit -m "docs(protocol): refresh Registry bundle references"

git push -u origin fix/registry-identifier-validation
CPP_PR_URL="$(gh pr create \
  --repo MissionWeaveProtocol/cpp-sdk \
  --base main \
  --head fix/registry-identifier-validation \
  --title "Pin Registry identifier cryptography evaluations" \
  --body "Synchronizes the merged 62-evaluation bundle and proves the existing complete-Registry C++ validator rejects all four malformed identifiers before selection.")"
gh pr checks "$CPP_PR_URL" --repo MissionWeaveProtocol/cpp-sdk --watch
gh pr merge "$CPP_PR_URL" \
  --repo MissionWeaveProtocol/cpp-sdk \
  --squash
CPP_MERGED_SHA="$(gh pr view "$CPP_PR_URL" \
  --repo MissionWeaveProtocol/cpp-sdk \
  --json mergeCommit \
  --jq '.mergeCommit.oid')"
```

Expected: PR checks pass and C++ remote main contains the generated assets and exact authoritative pin. Verify the push-to-main CI for `$CPP_MERGED_SHA` before claiming completion.

### Task 12: Audit all six merged SDK pins and native evidence

**Files:**
- Read from remote `main`: six `PROTOCOL_PIN.json` files and six `cryptography/manifest.json` files
- Read: merged GitHub PRs and CI runs

- [ ] **Step 1: Fetch every remote main without changing local working branches**

Run:

```bash
git -C /Users/lionelmbp/repos/python-sdk fetch origin main
git -C /Users/lionelmbp/repos/typescript-sdk fetch origin main
git -C /Users/lionelmbp/repos/go-sdk fetch origin main
git -C /Users/lionelmbp/repos/rust-sdk fetch origin main
git -C /Users/lionelmbp/repos/java-sdk fetch origin main
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  fetch origin main
```

- [ ] **Step 2: Assert every remote pin is identical on the six required fields**

Run in zsh:

```bash
jq -s -e '
  map({
    commit,
    sourceCommit: .cryptography.sourceCommit,
    artifactDigest: .cryptography.artifactDigest,
    artifactCount: .cryptography.artifactCount,
    caseCount: .cryptography.caseCount,
    evaluationCount: .cryptography.evaluationCount
  }) as $pins
  | ($pins | map(.commit) | unique | length) == 1
    and ($pins | map(.sourceCommit) | unique | length) == 1
    and ($pins | map(.artifactDigest) | unique | length) == 1
    and ($pins | map(.artifactCount) | unique) == [98]
    and ($pins | map(.caseCount) | unique) == [22]
    and ($pins | map(.evaluationCount) | unique) == [62]
' \
  <(git -C /Users/lionelmbp/repos/python-sdk show origin/main:PROTOCOL_PIN.json) \
  <(git -C /Users/lionelmbp/repos/typescript-sdk show origin/main:PROTOCOL_PIN.json) \
  <(git -C /Users/lionelmbp/repos/go-sdk show origin/main:PROTOCOL_PIN.json) \
  <(git -C /Users/lionelmbp/repos/rust-sdk show origin/main:PROTOCOL_PIN.json) \
  <(git -C /Users/lionelmbp/repos/java-sdk show origin/main:PROTOCOL_PIN.json) \
  <(git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
    show origin/main:PROTOCOL_PIN.json)
```

Expected: exit zero. Also assert the unique commit equals the current protocol `origin/main` commit and the unique digest equals that merged manifest's `artifactDigest`.

- [ ] **Step 3: Assert every vendored cryptography manifest is byte-identical**

Run:

```bash
git -C /Users/lionelmbp/repos/python-sdk show origin/main:cryptography/manifest.json | shasum -a 256
git -C /Users/lionelmbp/repos/typescript-sdk show origin/main:cryptography/manifest.json | shasum -a 256
git -C /Users/lionelmbp/repos/go-sdk show origin/main:cryptography/manifest.json | shasum -a 256
git -C /Users/lionelmbp/repos/rust-sdk show origin/main:cryptography/manifest.json | shasum -a 256
git -C /Users/lionelmbp/repos/java-sdk show origin/main:cryptography/manifest.json | shasum -a 256
git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence \
  show origin/main:cryptography/manifest.json | shasum -a 256
```

Expected: all six SHA-256 values are identical.

- [ ] **Step 4: Verify the four fault entries and final histogram in every manifest**

Run:

```bash
check_registry_manifest() {
  git -C "$1" show origin/main:cryptography/manifest.json | jq -e '
    ([.cases[].evaluations[].fault.id?] | index("registry-organization-id-relative-reference")) != null
    and ([.cases[].evaluations[].fault.id?] | index("registry-selected-service-principal-id-iri-only")) != null
    and ([.cases[].evaluations[].fault.id?] | index("registry-unrelated-principal-id-malformed-percent")) != null
    and ([.cases[].evaluations[].fault.id?] | index("registry-unrelated-key-id-trailing-line-feed")) != null
    and ([.cases[].evaluations[] | select(.expect.stage == "key-resolution")] | length) == 24
  '
}

check_registry_manifest /Users/lionelmbp/repos/python-sdk
check_registry_manifest /Users/lionelmbp/repos/typescript-sdk
check_registry_manifest /Users/lionelmbp/repos/go-sdk
check_registry_manifest /Users/lionelmbp/repos/rust-sdk
check_registry_manifest /Users/lionelmbp/repos/java-sdk
check_registry_manifest \
  /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence
```

Expected: every SDK carries all four faults and exactly 24 key-resolution evaluations.

- [ ] **Step 5: Verify all exact-main CI runs are successful**

Run:

```bash
verify_main_ci() {
  repository="$1"
  commit="$2"
  gh run list \
    --repo "$repository" \
    --commit "$commit" \
    --workflow CI \
    --limit 1 \
    --json headSha,status,conclusion \
    | jq -e --arg commit "$commit" \
      'length == 1 and .[0].headSha == $commit and .[0].conclusion == "success"'
}

verify_main_ci MissionWeaveProtocol/python-sdk \
  "$(git -C /Users/lionelmbp/repos/python-sdk rev-parse origin/main)"
verify_main_ci MissionWeaveProtocol/typescript-sdk \
  "$(git -C /Users/lionelmbp/repos/typescript-sdk rev-parse origin/main)"
verify_main_ci MissionWeaveProtocol/go-sdk \
  "$(git -C /Users/lionelmbp/repos/go-sdk rev-parse origin/main)"
verify_main_ci MissionWeaveProtocol/rust-sdk \
  "$(git -C /Users/lionelmbp/repos/rust-sdk rev-parse origin/main)"
verify_main_ci MissionWeaveProtocol/java-sdk \
  "$(git -C /Users/lionelmbp/repos/java-sdk rev-parse origin/main)"
verify_main_ci MissionWeaveProtocol/cpp-sdk \
  "$(git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence rev-parse origin/main)"
```

Expected: all six assertions pass. Inspect the exact Java run for `./mvnw -B -ntp verify` plus installed-consumer smoke and the exact C++ run for generated-assets/build/test/install evidence; do not substitute PR summaries when the local toolchain was unavailable.

### Task 13: Run independent reviews, publish evidence, and close the slice

**Files:**
- Read-only review scope: protocol plus all six merged SDK branches
- External artifact: one MissionWeaveProtocol GitHub issue

- [ ] **Step 1: Dispatch a Spec review with no write authority**

Use a fresh read-only subagent with `fork_turns: "none"` and this exact objective:

```text
TASK_REVISION: MW-V1-2026-07-29-R1
ONLY ACTIVE OBJECTIVE: review the merged protocol and six SDK implementations against every requirement and acceptance criterion in docs/superpowers/specs/2026-07-29-registry-identifier-validation-design.md. Check complete-scan ordering, all three identifier locations, URI semantics, no normalization, no runtime 512 limit, error stage/wire code, bundle totals, and common pins. Return only evidence-backed gaps or PASS.
PROHIBITED ACTIONS: no edits, commits, pushes, PR comments, issue mutations, or credentials.
STOP CONDITION: return a requirement-by-requirement verdict with exact file/test evidence.
```

- [ ] **Step 2: Dispatch an independent Standards/quality review with no write authority**

Use another fresh read-only subagent with `fork_turns: "none"` and this exact objective:

```text
TASK_REVISION: MW-V1-2026-07-29-R1
ONLY ACTIVE OBJECTIVE: independently review the merged protocol and six SDKs for RFC 3986 edge correctness, whole-string/visible-ASCII handling, percent escapes, empty-hier-part support, long identifiers, generated-asset determinism, package inclusion, test quality, and stale pin/documentation risks. Return only actionable findings or PASS.
PROHIBITED ACTIONS: no edits, commits, pushes, PR comments, issue mutations, or credentials.
STOP CONDITION: return exact evidence and severity for each finding.
```

- [ ] **Step 3: Resolve every actionable finding through the root write lane**

For each valid finding, reproduce it, add a focused RED test where behavior changes, make the smallest in-scope fix, rerun the affected repository's full native/package gate, merge the corrective PR, and rerun Tasks 12 and 13 Steps 1–2. Do not mark review threads resolved or reply to comments unless explicitly requested.

- [ ] **Step 4: Build one exact cross-language evidence body from merged remote state**

Run:

```bash
PROTOCOL_SHA="$(git -C /Users/lionelmbp/repos/missionweaveprotocol rev-parse origin/main)"
PYTHON_SHA="$(git -C /Users/lionelmbp/repos/python-sdk rev-parse origin/main)"
TYPESCRIPT_SHA="$(git -C /Users/lionelmbp/repos/typescript-sdk rev-parse origin/main)"
GO_SHA="$(git -C /Users/lionelmbp/repos/go-sdk rev-parse origin/main)"
RUST_SHA="$(git -C /Users/lionelmbp/repos/rust-sdk rev-parse origin/main)"
JAVA_SHA="$(git -C /Users/lionelmbp/repos/java-sdk rev-parse origin/main)"
CPP_SHA="$(git -C /Users/lionelmbp/.config/superpowers/worktrees/cpp-sdk/fix-complete-registry-evidence rev-parse origin/main)"
CRYPTO_DIGEST="$(git -C /Users/lionelmbp/repos/missionweaveprotocol \
  show "$PROTOCOL_SHA:cryptography/manifest.json" | jq -r '.artifactDigest')"

EVIDENCE_BODY="$(jq -nr \
  --arg protocol "$PROTOCOL_SHA" \
  --arg python "$PYTHON_SHA" \
  --arg typescript "$TYPESCRIPT_SHA" \
  --arg go "$GO_SHA" \
  --arg rust "$RUST_SHA" \
  --arg java "$JAVA_SHA" \
  --arg cpp "$CPP_SHA" \
  --arg digest "$CRYPTO_DIGEST" '
  "Task revision: MW-V1-2026-07-29-R1\n\n" +
  "Protocol: `" + $protocol + "`\n" +
  "Python: `" + $python + "`\n" +
  "TypeScript: `" + $typescript + "`\n" +
  "Go: `" + $go + "`\n" +
  "Rust: `" + $rust + "`\n" +
  "Java: `" + $java + "`\n" +
  "C++: `" + $cpp + "`\n\n" +
  "Cryptography digest: `" + $digest + "`\n" +
  "Bundle: 98 artifacts, 22 cases, 62 evaluations, 12 complete, 50 rejected, 24 key-resolution failures.\n\n" +
  "All implementations reject relative organizationId, selected service Principal IRI text, unrelated Principal malformed percent escapes, and unrelated keyId trailing LF before key selection with AUTH_INVALID_SIGNATURE. Python, TypeScript, Go, and Rust received runtime fixes; Java and C++ passed bundle-only synchronization. Native tests, package/install consumers, exact pins, exact manifests, and exact-main CI were verified. Independent Spec and Standards reviews returned no unresolved findings."
')"
```

Expected: the body contains only exact merged SHAs and the authoritative digest.

- [ ] **Step 5: Create and read back the tracking issue**

Reconfirm `MW-V1-2026-07-29-R1`, then run:

```bash
EVIDENCE_ISSUE_URL="$(gh issue create \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --title "V1 Registry identifier validation cross-language evidence" \
  --body "$EVIDENCE_BODY")"
gh issue view "$EVIDENCE_ISSUE_URL" \
  --repo MissionWeaveProtocol/missionweaveprotocol \
  --json number,title,state,url,body
```

Expected: one open issue with the exact evidence body and no credentials or unverified claims.

- [ ] **Step 6: Perform final local and remote cleanliness checks**

Run `git status --short --branch` in the design checkout and every implementation worktree, then run:

```bash
for repository in \
  MissionWeaveProtocol/missionweaveprotocol \
  MissionWeaveProtocol/python-sdk \
  MissionWeaveProtocol/typescript-sdk \
  MissionWeaveProtocol/go-sdk \
  MissionWeaveProtocol/rust-sdk \
  MissionWeaveProtocol/java-sdk \
  MissionWeaveProtocol/cpp-sdk
do
  gh pr list \
    --repo "$repository" \
    --state open \
    --head fix/registry-identifier-validation \
    --json number,title,url
done
```

Expected: no uncommitted changes, all intended PRs merged, no stale delivery branch PRs open, all six SDK remote mains share the same pin, and both independent reviews have no unresolved issue.

- [ ] **Step 7: Mark the active goal complete only after every acceptance criterion is satisfied**

Use the goal completion mechanism only after Tasks 1–13 are fully verified. Report exact merged commits, the common cryptography digest, test/CI evidence, the tracking issue URL, any legitimate skips, and the final goal token usage returned by the completion tool.
