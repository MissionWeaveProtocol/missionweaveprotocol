#!/usr/bin/env python3
"""Validate the MissionWeaveProtocol First-Admission conformance bundle."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema.validators import validator_for
from referencing import Registry, Resource

from validate_crypto_vectors import (
    BundleValidationError,
    Rfc3339Instant,
    SemanticFailure,
    StrictJsonError,
    VerifiedResult,
    _jcs_bytes,
    _load_and_validate_bundle as _load_crypto_bundle,
    _parse_rfc3339_value,
    _repository_path,
    _sha256,
    _strict_json,
    _validate_instance,
    verify_signed_document_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
ADMISSION_ROOT = ROOT / "admission"
SCHEMA_ROOT = ROOT / "schemas"
MANIFEST_PATH = ADMISSION_ROOT / "manifest.json"
MANIFEST_SCHEMA_PATH = ADMISSION_ROOT / "manifest.schema.json"

MANIFEST_SCHEMA_ID = (
    "https://missionweaveprotocol.dev/admission/0.1/manifest.schema.json"
)
PROFILE_ID = "missionweaveprotocol.first-admission-historical-trust.v0.1"
CRYPTOGRAPHY_DIGEST = (
    "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
)
EXPECTED_TOP_LEVEL_FIELDS = {
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
    "cases",
}
EXPECTED_INVALID_RECORD_FIELDS = {
    "accepted-by-non-service": "acceptedBy",
    "document-kind-mismatch": "documentKind",
    "key-id-mismatch": "keyId",
    "organization-mismatch": "organizationId",
    "principal-mismatch": "principal",
    "signing-hash-mismatch": "signingHash",
}
EXPECTED_PROFILE_IDS = (
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
REQUIRED_PUBLIC_PATHS = {
    "first-admission.command",
    "trusted-time-equal-valid-until",
    "key-id-mismatch",
    "historical-replay.later-revocation",
    "admission-log-indeterminate",
}
EXPECTED_ARTIFACTS = 19
EXPECTED_CASES = 5
EXPECTED_EVALUATIONS = 30
EXPECTED_COMPLETE = 12
EXPECTED_REJECTED = 18


class AdmissionFailure(Exception):
    """An intentional failure in the Admission semantic stage."""

    stage = "admission"
    wire_code = "AUTH_INVALID_SIGNATURE"

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class AuthenticatedRecord:
    record_bytes: bytes
    authenticated_service: dict[str, str]


@dataclass(frozen=True)
class LookupResult:
    found: AuthenticatedRecord | None
    authoritative_absence: bool
    reason: str


@dataclass(frozen=True)
class AdmissionBundle:
    manifest: Mapping[str, Any]
    artifacts: Mapping[str, bytes]
    crypto_manifest: Mapping[str, Any]
    crypto_artifacts: Mapping[str, bytes]
    profiles: Mapping[str, Mapping[str, Any]]
    schemas: Mapping[str, Mapping[str, Any]]
    schema_registry: Registry
    record_schema: Mapping[str, Any]

    def read(self, path: str) -> bytes:
        if path in self.artifacts:
            return self.artifacts[path]
        if path in self.crypto_artifacts:
            return self.crypto_artifacts[path]
        raise BundleValidationError(f"referenced fixture is not protected: {path}")


def _load_fixed_json(path: Path, *, label: str) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BundleValidationError(f"cannot read {label}: {error}") from error
    try:
        return _strict_json(raw, label=label, preserve_numbers=False)
    except StrictJsonError as error:
        raise BundleValidationError(str(error)) from error


def _read_admission_artifacts(manifest: Mapping[str, Any]) -> dict[str, bytes]:
    artifacts = manifest["artifacts"]
    paths = [artifact["path"] for artifact in artifacts]
    if paths != sorted(paths):
        raise BundleValidationError("Admission artifacts must be sorted by path")
    if len(paths) != len(set(paths)):
        raise BundleValidationError("Admission artifact paths must be unique")
    if len({path.casefold() for path in paths}) != len(paths):
        raise BundleValidationError("Admission artifact paths collide after case folding")
    if len(paths) != EXPECTED_ARTIFACTS:
        raise BundleValidationError(
            f"expected {EXPECTED_ARTIFACTS} Admission artifacts, found {len(paths)}"
        )

    cache: dict[str, bytes] = {}
    for index, artifact in enumerate(artifacts):
        path = artifact["path"]
        resolved = _repository_path(
            path,
            allowed_roots=(ADMISSION_ROOT, SCHEMA_ROOT),
            label=f"Admission artifacts[{index}].path",
        )
        try:
            raw = resolved.read_bytes()
        except OSError as error:
            raise BundleValidationError(f"cannot read artifact {path}: {error}") from error
        if len(raw) != int(artifact["byteLength"]):
            raise BundleValidationError(
                f"artifact {path} byteLength mismatch: expected "
                f"{artifact['byteLength']}, got {len(raw)}"
            )
        digest = _sha256(raw)
        if digest != artifact["sha256"]:
            raise BundleValidationError(
                f"artifact {path} digest mismatch: expected "
                f"{artifact['sha256']}, got {digest}"
            )
        cache[path] = raw
    return cache


def _record_registry(
    record_schema: Mapping[str, Any], crypto_registry: Registry
) -> Registry:
    try:
        validator_for(record_schema).check_schema(record_schema)
        resource = Resource.from_contents(record_schema)
        return crypto_registry.with_resource(record_schema["$id"], resource).crawl()
    except Exception as error:
        raise BundleValidationError(
            f"cannot build First-Admission Record Schema registry: {error}"
        ) from error


def _parse_artifact_json(
    artifacts: Mapping[str, bytes], path: str, *, label: str
) -> Any:
    try:
        raw = artifacts[path]
    except KeyError as error:
        raise BundleValidationError(f"{label} is not indexed: {path}") from error
    try:
        return _strict_json(raw, label=path, preserve_numbers=False)
    except StrictJsonError as error:
        raise BundleValidationError(str(error)) from error


def _validate_record_fixtures(
    artifacts: Mapping[str, bytes],
    *,
    record_schema: Mapping[str, Any],
    schema_registry: Registry,
) -> None:
    valid_paths = {
        f"admission/records/valid/{profile_id}.json" for profile_id in EXPECTED_PROFILE_IDS
    }
    invalid_paths = {
        f"admission/records/invalid/{name}.json"
        for name in EXPECTED_INVALID_RECORD_FIELDS
    }
    actual_paths = {
        path for path in artifacts if path.startswith("admission/records/")
    }
    expected_paths = valid_paths | invalid_paths
    if actual_paths != expected_paths:
        raise BundleValidationError(
            "Admission record fixture set mismatch: "
            f"missing={sorted(expected_paths - actual_paths)!r}, "
            f"unexpected={sorted(actual_paths - expected_paths)!r}"
        )

    valid_records: dict[str, Mapping[str, Any]] = {}
    for profile_id in EXPECTED_PROFILE_IDS:
        path = f"admission/records/valid/{profile_id}.json"
        record = _parse_artifact_json(artifacts, path, label="valid record")
        if not isinstance(record, dict):
            raise BundleValidationError(f"valid record is not an object: {path}")
        _validate_instance(
            record,
            record_schema,
            registry=schema_registry,
            label=path,
        )
        if record["documentKind"] != profile_id:
            raise BundleValidationError(f"{path} does not bind its profile ID")
        try:
            _parse_rfc3339_value(record["trustedAcceptedAt"])
        except ValueError as error:
            raise BundleValidationError(
                f"{path} has an invalid trustedAcceptedAt: {error}"
            ) from error
        valid_records[profile_id] = record

    command = valid_records["command"]
    for name, expected_field in EXPECTED_INVALID_RECORD_FIELDS.items():
        path = f"admission/records/invalid/{name}.json"
        record = _parse_artifact_json(artifacts, path, label="invalid record")
        if not isinstance(record, dict):
            raise BundleValidationError(f"invalid record is not an object: {path}")
        changed = {
            field
            for field in command.keys() | record.keys()
            if command.get(field) != record.get(field)
        }
        if changed != {expected_field}:
            raise BundleValidationError(
                f"{path} must change only {expected_field}, changed {sorted(changed)!r}"
            )
        schema_failed = False
        try:
            _validate_instance(
                record,
                record_schema,
                registry=schema_registry,
                label=path,
            )
        except BundleValidationError:
            schema_failed = True
        if schema_failed != (name == "accepted-by-non-service"):
            raise BundleValidationError(
                f"{path} has the wrong declared Schema-validity fault shape"
            )


def _validate_matrix(
    manifest: Mapping[str, Any],
    *,
    admission_paths: set[str],
    crypto_paths: set[str],
) -> None:
    cases = manifest["cases"]
    case_ids = [case["id"] for case in cases]
    if case_ids != sorted(case_ids) or len(case_ids) != len(set(case_ids)):
        raise BundleValidationError("Admission case IDs must be sorted and unique")
    if len(cases) != EXPECTED_CASES:
        raise BundleValidationError(
            f"expected {EXPECTED_CASES} Admission cases, found {len(cases)}"
        )

    evaluations = [evaluation for case in cases for evaluation in case["evaluations"]]
    evaluation_ids = [evaluation["id"] for evaluation in evaluations]
    if len(evaluation_ids) != len(set(evaluation_ids)):
        raise BundleValidationError("Admission evaluation IDs must be unique")
    if len(evaluations) != EXPECTED_EVALUATIONS:
        raise BundleValidationError(
            f"expected {EXPECTED_EVALUATIONS} evaluations, found {len(evaluations)}"
        )
    missing_public = REQUIRED_PUBLIC_PATHS - set(evaluation_ids)
    if missing_public:
        raise BundleValidationError(
            f"required public Admission paths are missing: {sorted(missing_public)!r}"
        )

    complete = 0
    rejected = 0
    references = {
        manifest["cryptography"]["manifest"],
        *manifest["fixtureSchemas"].values(),
    }
    for evaluation in evaluations:
        references.update((evaluation["document"], evaluation["registry"]))
        for outcome_name in ("lookup", "append", "expect"):
            outcome = evaluation[outcome_name]
            if isinstance(outcome, dict) and "record" in outcome:
                references.add(outcome["record"])
        expectation = evaluation["expect"]
        if expectation["stage"] == "complete":
            complete += 1
            if expectation["wireCode"] is not None:
                raise BundleValidationError(
                    f"complete evaluation {evaluation['id']} has a wire code"
                )
        else:
            rejected += 1
            if expectation["stage"] != "admission" or expectation["wireCode"] != (
                "AUTH_INVALID_SIGNATURE"
            ):
                raise BundleValidationError(
                    f"rejected evaluation {evaluation['id']} has the wrong failure contract"
                )
    if (complete, rejected) != (EXPECTED_COMPLETE, EXPECTED_REJECTED):
        raise BundleValidationError(
            f"expected {EXPECTED_COMPLETE} complete and {EXPECTED_REJECTED} rejected, "
            f"found {complete} and {rejected}"
        )

    protected_paths = admission_paths | crypto_paths | {"cryptography/manifest.json"}
    unprotected = sorted(references - protected_paths)
    if unprotected:
        raise BundleValidationError(
            f"Admission manifest references unprotected files: {unprotected!r}"
        )


def _load_and_validate_bundle() -> AdmissionBundle:
    manifest_schema = _load_fixed_json(
        MANIFEST_SCHEMA_PATH, label="admission/manifest.schema.json"
    )
    if not isinstance(manifest_schema, dict):
        raise BundleValidationError("Admission manifest Schema is not an object")
    if manifest_schema.get("$id") != MANIFEST_SCHEMA_ID:
        raise BundleValidationError("Admission manifest Schema has the wrong $id")
    try:
        validator_for(manifest_schema).check_schema(manifest_schema)
    except Exception as error:
        raise BundleValidationError(f"invalid Admission manifest Schema: {error}") from error

    manifest = _load_fixed_json(MANIFEST_PATH, label="admission/manifest.json")
    if not isinstance(manifest, dict):
        raise BundleValidationError("Admission manifest is not an object")
    _validate_instance(manifest, manifest_schema, label="Admission manifest")
    if set(manifest) != EXPECTED_TOP_LEVEL_FIELDS:
        raise BundleValidationError("Admission manifest top-level fields are not exact")
    if (
        manifest["manifestVersion"] != 1
        or manifest["protocolVersion"] != "0.1"
        or manifest["profileId"] != PROFILE_ID
        or manifest["semanticStage"] != "admission"
        or manifest["wireCode"] != "AUTH_INVALID_SIGNATURE"
    ):
        raise BundleValidationError("Admission manifest constants are not v0.1")

    crypto_manifest, crypto_artifacts, schemas, crypto_registry = (
        _load_crypto_bundle()
    )
    if (
        manifest["cryptography"]["artifactDigest"] != CRYPTOGRAPHY_DIGEST
        or crypto_manifest["artifactDigest"] != CRYPTOGRAPHY_DIGEST
    ):
        raise BundleValidationError("Admission cryptography digest does not match the pin")

    artifacts = _read_admission_artifacts(manifest)
    digest_input = copy.deepcopy(dict(manifest))
    digest_input.pop("artifactDigest", None)
    computed_digest = _sha256(_jcs_bytes(digest_input))
    if computed_digest != manifest["artifactDigest"]:
        raise BundleValidationError(
            f"Admission artifactDigest mismatch: expected {manifest['artifactDigest']}, "
            f"got {computed_digest}"
        )

    record_path = manifest["fixtureSchemas"]["record"]
    record_schema = _parse_artifact_json(
        artifacts, record_path, label="First-Admission Record Schema"
    )
    if not isinstance(record_schema, dict):
        raise BundleValidationError("First-Admission Record Schema is not an object")
    schema_registry = _record_registry(record_schema, crypto_registry)
    _validate_record_fixtures(
        artifacts,
        record_schema=record_schema,
        schema_registry=schema_registry,
    )
    _validate_matrix(
        manifest,
        admission_paths=set(artifacts),
        crypto_paths=set(crypto_artifacts),
    )

    profiles = {
        profile["profileId"]: profile for profile in crypto_manifest["profiles"]
    }
    return AdmissionBundle(
        manifest=manifest,
        artifacts=artifacts,
        crypto_manifest=crypto_manifest,
        crypto_artifacts=crypto_artifacts,
        profiles=profiles,
        schemas=schemas,
        schema_registry=schema_registry,
        record_schema=record_schema,
    )


class FixtureStore:
    def __init__(self, bundle: AdmissionBundle) -> None:
        self.bundle = bundle
        self.lookup_calls = 0
        self.trusted_context_calls = 0
        self.append_calls = 0

    def verify(self, evaluation: Mapping[str, Any]) -> VerifiedResult:
        profile = self.bundle.profiles[evaluation["profileId"]]
        try:
            return verify_signed_document_bytes(
                profile=profile,
                document_bytes=self.bundle.read(evaluation["document"]),
                registry_bytes=self.bundle.read(evaluation["registry"]),
                schemas=self.bundle.schemas,
                schema_registry=self.bundle.schema_registry,
                document_label=evaluation["document"],
                registry_label=evaluation["registry"],
            )
        except SemanticFailure as error:
            raise BundleValidationError(
                f"Admission evaluation {evaluation['id']} failed during the frozen "
                f"six-stage verifier at {error.stage}: {error.detail}"
            ) from error

    def _authenticated_record(
        self,
        evaluation: Mapping[str, Any],
        outcome: Mapping[str, Any],
    ) -> AuthenticatedRecord:
        if (
            evaluation["profileId"] == "event"
            and outcome["record"] == evaluation["document"]
        ):
            raise AdmissionFailure(
                "event-self-anchoring",
                "a Signed Event cannot authenticate its own First-Admission Record",
            )
        return AuthenticatedRecord(
            record_bytes=self.bundle.read(outcome["record"]),
            authenticated_service=dict(outcome["authenticatedService"]),
        )

    def lookup(
        self, evaluation: Mapping[str, Any], verified: VerifiedResult
    ) -> LookupResult:
        self.lookup_calls += 1
        outcome = evaluation["lookup"]
        status = outcome["status"]
        if status == "found":
            return LookupResult(
                found=self._authenticated_record(evaluation, outcome),
                authoritative_absence=False,
                reason="record-missing",
            )
        if status == "authoritative-absence":
            return LookupResult(None, True, "record-missing")
        reasons = {
            "unauthenticated": "log-authentication-failed",
            "integrity-failed": "log-authentication-failed",
            "unavailable": "log-unavailable",
            "indeterminate": "log-indeterminate",
        }
        return LookupResult(None, False, reasons[status])

    def trusted_context(self, evaluation: Mapping[str, Any]) -> Mapping[str, Any]:
        self.trusted_context_calls += 1
        context = evaluation["trustedContext"]
        if not isinstance(context, dict):
            raise BundleValidationError(
                f"evaluation {evaluation['id']} has no trusted context"
            )
        return context

    def append_or_return_existing(
        self, evaluation: Mapping[str, Any], candidate_bytes: bytes
    ) -> AuthenticatedRecord:
        self.append_calls += 1
        outcome = evaluation["append"]
        if not isinstance(outcome, dict):
            raise BundleValidationError(
                f"evaluation {evaluation['id']} has no append outcome"
            )
        status = outcome["status"]
        if status in {"committed", "existing"}:
            authenticated = self._authenticated_record(evaluation, outcome)
            if status == "committed" and authenticated.record_bytes != candidate_bytes:
                raise BundleValidationError(
                    f"evaluation {evaluation['id']} committed bytes differ from candidate"
                )
            return authenticated
        reasons = {
            "conflict": "record-conflict",
            "unauthenticated": "log-authentication-failed",
            "integrity-failed": "append-integrity-not-established",
            "unavailable": "log-unavailable",
            "indeterminate": "log-indeterminate",
        }
        raise AdmissionFailure(reasons[status], f"append outcome was {status}")


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


def _prepare_first_admission(
    verified: VerifiedResult, trusted_context: Mapping[str, Any]
) -> bytes:
    trusted_text = trusted_context["trustedAcceptedAt"]
    try:
        accepted = _parse_rfc3339_value(trusted_text)
    except ValueError as error:
        raise AdmissionFailure("malformed-trusted-time", str(error)) from error
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

    record = {
        "protocolVersion": "0.1",
        "admissionRecordId": trusted_context["admissionRecordId"],
        "organizationId": verified.key.organization_id,
        "documentKind": verified.document_kind,
        "signingHash": verified.signing_hash,
        "keyId": verified.key.key_id,
        "principal": copy.deepcopy(verified.key.principal),
        "trustedAcceptedAt": trusted_text,
        "acceptedBy": copy.deepcopy(trusted_context["acceptedBy"]),
    }
    encoded = json.dumps(
        record,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    return (encoded + "\n").encode("utf-8")


def admit_first(
    evaluation: Mapping[str, Any], fixtures: FixtureStore
) -> dict[str, Any]:
    verified = fixtures.verify(evaluation)
    lookup = fixtures.lookup(evaluation, verified)
    if lookup.found is not None:
        return _validate_committed_record(
            lookup.found,
            verified,
            record_schema=fixtures.bundle.record_schema,
            schema_registry=fixtures.bundle.schema_registry,
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
        record_schema=fixtures.bundle.record_schema,
        schema_registry=fixtures.bundle.schema_registry,
    )


def verify_historical_admission(
    evaluation: Mapping[str, Any],
    fixtures: FixtureStore,
) -> dict[str, Any]:
    verified = fixtures.verify(evaluation)
    lookup = fixtures.lookup(evaluation, verified)
    if lookup.found is None:
        reason = "record-missing" if lookup.authoritative_absence else lookup.reason
        raise AdmissionFailure(reason, "historical replay requires a record")
    return _validate_committed_record(
        lookup.found,
        verified,
        record_schema=fixtures.bundle.record_schema,
        schema_registry=fixtures.bundle.schema_registry,
    )


def _expected_calls(evaluation: Mapping[str, Any]) -> tuple[int, int, int]:
    if evaluation["mode"] == "historical-replay":
        return (1, 0, 0)
    if evaluation["lookup"]["status"] != "authoritative-absence":
        return (1, 0, 0)
    return (1, 1, int(evaluation["append"] is not None))


def _assert_calls(evaluation: Mapping[str, Any], fixtures: FixtureStore) -> None:
    actual = (
        fixtures.lookup_calls,
        fixtures.trusted_context_calls,
        fixtures.append_calls,
    )
    expected = _expected_calls(evaluation)
    if actual != expected:
        raise BundleValidationError(
            f"evaluation {evaluation['id']} call counts {actual!r} do not match "
            f"expected {expected!r}"
        )


def _expected_record(bundle: AdmissionBundle, path: str) -> Mapping[str, Any]:
    try:
        value = _strict_json(bundle.read(path), label=path, preserve_numbers=False)
    except StrictJsonError as error:
        raise BundleValidationError(str(error)) from error
    if not isinstance(value, dict):
        raise BundleValidationError(f"expected record is not an object: {path}")
    return value


def _run_evaluation(
    evaluation: Mapping[str, Any], bundle: AdmissionBundle
) -> bool:
    fixtures = FixtureStore(bundle)
    expected = evaluation["expect"]
    try:
        if evaluation["mode"] == "first-admission":
            record = admit_first(evaluation, fixtures)
        else:
            record = verify_historical_admission(evaluation, fixtures)
    except AdmissionFailure as failure:
        if expected["stage"] == "complete":
            raise BundleValidationError(
                f"evaluation {evaluation['id']} expected complete but failed: "
                f"{failure.reason}: {failure.detail}"
            ) from failure
        if (
            failure.stage != expected["stage"]
            or failure.wire_code != expected["wireCode"]
            or failure.reason != expected["reason"]
        ):
            raise BundleValidationError(
                f"evaluation {evaluation['id']} expected {expected!r} but produced "
                f"stage={failure.stage!r}, wireCode={failure.wire_code!r}, "
                f"reason={failure.reason!r}"
            ) from failure
        _assert_calls(evaluation, fixtures)
        return False

    if expected["stage"] != "complete":
        raise BundleValidationError(
            f"evaluation {evaluation['id']} expected rejection but completed"
        )
    if record != _expected_record(bundle, expected["record"]):
        raise BundleValidationError(
            f"evaluation {evaluation['id']} returned the wrong admitted record"
        )
    _assert_calls(evaluation, fixtures)
    return True


def _run_cases(bundle: AdmissionBundle) -> None:
    completed = 0
    rejected = 0
    exercised: set[str] = set()
    for case in bundle.manifest["cases"]:
        for evaluation in case["evaluations"]:
            exercised.add(evaluation["id"])
            if _run_evaluation(evaluation, bundle):
                completed += 1
            else:
                rejected += 1
    if REQUIRED_PUBLIC_PATHS - exercised:
        raise BundleValidationError("the runner did not exercise all public paths")
    if (completed, rejected) != (EXPECTED_COMPLETE, EXPECTED_REJECTED):
        raise BundleValidationError(
            f"runner produced {completed} complete and {rejected} rejected evaluations"
        )
    print(
        "Validated Admission bundle: 19 artifacts, 5 cases, 30 evaluations, "
        "12 complete and 18 rejected; cryptography digest "
        f"{bundle.crypto_manifest['artifactDigest']}."
    )


def main() -> int:
    try:
        bundle = _load_and_validate_bundle()
        _run_cases(bundle)
    except BundleValidationError as error:
        print(f"Admission vector validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
