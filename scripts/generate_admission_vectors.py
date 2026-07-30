#!/usr/bin/env python3
"""Generate deterministic MissionWeaveProtocol v0.1 Admission vectors."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import rfc8785


ROOT = Path(__file__).resolve().parents[1]
ADMISSION_ROOT = ROOT / "admission"
VALID_RECORD_ROOT = ADMISSION_ROOT / "records" / "valid"
INVALID_RECORD_ROOT = ADMISSION_ROOT / "records" / "invalid"
REGISTRY_ROOT = ADMISSION_ROOT / "registries"
CRYPTOGRAPHY_MANIFEST_PATH = ROOT / "cryptography" / "manifest.json"
CRYPTOGRAPHY_REGISTRY_PATH = ROOT / "cryptography" / "keys" / "registry-valid.json"
CRYPTOGRAPHY_DIGEST = (
    "sha256:5eade516e4bc5dcf04477727ebcccd11f33348b2d9135fb6fe0365c6e6cc2ea3"
)
ORGANIZATION_ID = "urn:missionweaveprotocol:organization:acme"
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

STABLE_REASONS = {
    "record-missing",
    "record-binding-mismatch",
    "trusted-time-outside-key-interval",
    "malformed-trusted-time",
    "record-conflict",
    "record-schema-invalid",
    "log-authentication-failed",
    "append-integrity-not-established",
    "log-unavailable",
    "log-indeterminate",
    "commit-failed",
    "event-self-anchoring",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(document: Any) -> bytes:
    content = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    return (content + "\n").encode("utf-8")


def _stage_file(target: Path, content: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.chmod(0o644)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def _write_files_atomically(files: dict[str, bytes]) -> None:
    manifest_path = "admission/manifest.json"
    ordered_paths = sorted(path for path in files if path != manifest_path)
    if manifest_path in files:
        ordered_paths.append(manifest_path)

    targets = {relative: ROOT / relative for relative in ordered_paths}
    originals = {
        relative: target.read_bytes() if target.is_file() else None
        for relative, target in targets.items()
    }
    staged: dict[str, Path] = {}
    try:
        for relative in ordered_paths:
            staged[relative] = _stage_file(targets[relative], files[relative])

        committed: list[str] = []
        try:
            for relative in ordered_paths:
                os.replace(staged[relative], targets[relative])
                committed.append(relative)
        except BaseException as error:
            rollback_errors = []
            for relative in reversed(committed):
                target = targets[relative]
                original = originals[relative]
                try:
                    if original is None:
                        target.unlink(missing_ok=True)
                    else:
                        replacement = _stage_file(target, original)
                        try:
                            os.replace(replacement, target)
                        finally:
                            replacement.unlink(missing_ok=True)
                except BaseException as rollback_error:
                    rollback_errors.append(f"{relative}: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(
                    "Admission output rollback failed: " + "; ".join(rollback_errors)
                ) from error
            raise
    finally:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _record(profile_id: str, verified: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocolVersion": "0.1",
        "admissionRecordId": (
            f"urn:missionweaveprotocol:admission-record:crypto-vector-{profile_id}"
        ),
        "organizationId": ORGANIZATION_ID,
        "documentKind": profile_id,
        "signingHash": verified["signingHash"],
        "keyId": verified["keyId"],
        "principal": copy.deepcopy(verified["principal"]),
        "trustedAcceptedAt": TRUSTED_ACCEPTED_AT[profile_id],
        "acceptedBy": copy.deepcopy(ACCEPTED_BY),
    }


def _trusted_context(
    record: dict[str, Any],
    *,
    trusted_accepted_at: str | None = None,
) -> dict[str, Any]:
    return {
        "admissionRecordId": record["admissionRecordId"],
        "trustedAcceptedAt": (
            record["trustedAcceptedAt"]
            if trusted_accepted_at is None
            else trusted_accepted_at
        ),
        "acceptedBy": copy.deepcopy(record["acceptedBy"]),
    }


def _found(record: str) -> dict[str, Any]:
    return {
        "status": "found",
        "record": record,
        "authenticatedService": copy.deepcopy(ACCEPTED_BY),
    }


def _committed(record: str) -> dict[str, Any]:
    return {
        "status": "committed",
        "record": record,
        "authenticatedService": copy.deepcopy(ACCEPTED_BY),
    }


def _complete(record: str) -> dict[str, Any]:
    return {
        "stage": "complete",
        "wireCode": None,
        "record": record,
    }


def _rejected(evaluation_id: str) -> dict[str, Any]:
    return {
        "stage": "admission",
        "wireCode": "AUTH_INVALID_SIGNATURE",
        "reason": REJECTED_REASONS[evaluation_id],
    }


def _profile_evaluations(
    cryptography_manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    evaluations = [
        evaluation
        for case in cryptography_manifest["cases"]
        for evaluation in case["evaluations"]
        if evaluation.get("expect", {}).get("stage") == "complete"
    ]
    selected: dict[str, dict[str, Any]] = {}
    for profile_id in PROFILE_IDS:
        expected_document = (
            f"cryptography/vectors/signed-documents/valid/{profile_id}.json"
        )
        candidates = [
            evaluation
            for evaluation in evaluations
            if evaluation.get("profileId") == profile_id
            and evaluation.get("document") == expected_document
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                f"expected one canonical complete evaluation for {profile_id}, "
                f"found {len(candidates)}"
            )
        selected[profile_id] = candidates[0]
    return selected


def _build_records(
    profile_evaluations: dict[str, dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, str],
    dict[str, bytes],
]:
    records: dict[str, dict[str, Any]] = {}
    valid_paths: dict[str, str] = {}
    generated_files: dict[str, bytes] = {}
    for profile_id in PROFILE_IDS:
        record = _record(profile_id, profile_evaluations[profile_id]["expect"]["verified"])
        records[profile_id] = record
        path = f"admission/records/valid/{profile_id}.json"
        valid_paths[profile_id] = path
        generated_files[path] = _json_bytes(record)

    command = records["command"]
    invalid_mutations: dict[str, tuple[str, Any]] = {
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

    invalid_paths: dict[str, str] = {}
    for name, (field, value) in invalid_mutations.items():
        invalid = copy.deepcopy(command)
        invalid[field] = value
        changed_fields = {
            key
            for key in command.keys() | invalid.keys()
            if command.get(key) != invalid.get(key)
        }
        if changed_fields != {field}:
            raise RuntimeError(
                f"invalid record {name} changed fields {sorted(changed_fields)!r}"
            )
        path = f"admission/records/invalid/{name}.json"
        invalid_paths[name] = path
        generated_files[path] = _json_bytes(invalid)

    return records, valid_paths, invalid_paths, generated_files


def _build_later_revocation_registry() -> tuple[str, bytes]:
    registry = copy.deepcopy(_load_json(CRYPTOGRAPHY_REGISTRY_PATH))
    if not isinstance(registry, dict):
        raise RuntimeError("cryptography Registry fixture is not an object")
    binding = next(
        (
            item
            for item in registry["bindings"]
            if item["keyId"]
            == "urn:missionweaveprotocol:key:crypto-vector-rfc8032-1"
        ),
        None,
    )
    if binding is None:
        raise RuntimeError("Command key is absent from cryptography Registry fixture")
    history = binding["validityHistory"]
    expected_first_status = {
        "sequence": 1,
        "recordedAt": "2026-07-16T00:00:00Z",
        "validUntil": "2026-07-16T00:00:00Z",
    }
    if history != [expected_first_status]:
        raise RuntimeError("Command key history no longer has the expected expiry boundary")
    history.append(
        {
            "sequence": 2,
            "recordedAt": "2026-07-17T00:00:00Z",
            "revokedAt": "2026-07-15T01:00:00Z",
        }
    )
    path = "admission/registries/registry-later-revocation.json"
    return path, _json_bytes(registry)


def _base_evaluation(
    *,
    evaluation_id: str,
    profile_id: str,
    mode: str,
    profile_evaluation: dict[str, Any],
    registry: str | None = None,
) -> dict[str, Any]:
    return {
        "id": evaluation_id,
        "profileId": profile_id,
        "mode": mode,
        "document": profile_evaluation["document"],
        "registry": (
            profile_evaluation["registry"] if registry is None else registry
        ),
        "trustedContext": None,
        "lookup": {"status": "authoritative-absence"},
        "append": None,
        "expect": _rejected(evaluation_id),
    }


def _build_cases(
    profile_evaluations: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
    valid_paths: dict[str, str],
    invalid_paths: dict[str, str],
    later_revocation_registry: str,
) -> list[dict[str, Any]]:
    profile_matrix = []
    for profile_id in PROFILE_IDS:
        source = profile_evaluations[profile_id]
        record_path = valid_paths[profile_id]
        profile_matrix.append(
            {
                "id": f"first-admission.{profile_id}",
                "profileId": profile_id,
                "mode": "first-admission",
                "document": source["document"],
                "registry": source["registry"],
                "trustedContext": _trusted_context(records[profile_id]),
                "lookup": {"status": "authoritative-absence"},
                "append": _committed(record_path),
                "expect": _complete(record_path),
            }
        )

    command_source = profile_evaluations["command"]
    command_record = records["command"]
    command_record_path = valid_paths["command"]
    event_source = profile_evaluations["event"]

    idempotent_retry = {
        "id": "first-admission.idempotent-retry",
        "profileId": "command",
        "mode": "first-admission",
        "document": command_source["document"],
        "registry": command_source["registry"],
        "trustedContext": None,
        "lookup": _found(command_record_path),
        "append": None,
        "expect": _complete(command_record_path),
    }

    later_expiry = {
        "id": "historical-replay.later-expiry",
        "profileId": "command",
        "mode": "historical-replay",
        "document": command_source["document"],
        "registry": command_source["registry"],
        "trustedContext": None,
        "lookup": _found(command_record_path),
        "append": None,
        "expect": _complete(command_record_path),
    }

    later_revocation = {
        "id": "historical-replay.later-revocation",
        "profileId": "command",
        "mode": "historical-replay",
        "document": command_source["document"],
        "registry": later_revocation_registry,
        "trustedContext": None,
        "lookup": _found(command_record_path),
        "append": None,
        "expect": _complete(command_record_path),
    }

    rejected: list[dict[str, Any]] = []

    historical_missing = _base_evaluation(
        evaluation_id="historical-record-missing",
        profile_id="command",
        mode="historical-replay",
        profile_evaluation=command_source,
    )
    rejected.append(historical_missing)

    for evaluation_id in (
        "signing-hash-mismatch",
        "key-id-mismatch",
        "principal-mismatch",
        "organization-mismatch",
        "document-kind-mismatch",
    ):
        evaluation = _base_evaluation(
            evaluation_id=evaluation_id,
            profile_id="command",
            mode="historical-replay",
            profile_evaluation=command_source,
        )
        evaluation["lookup"] = _found(invalid_paths[evaluation_id])
        rejected.append(evaluation)

    trusted_time_cases = (
        (
            "trusted-time-before-valid-from",
            command_source["registry"],
            "2026-07-14T23:59:59Z",
        ),
        (
            "trusted-time-equal-valid-until",
            command_source["registry"],
            "2026-07-16T00:00:00Z",
        ),
        (
            "trusted-time-after-valid-until",
            command_source["registry"],
            "2026-07-16T00:00:01Z",
        ),
        (
            "trusted-time-equal-revoked-at",
            later_revocation_registry,
            "2026-07-15T01:00:00Z",
        ),
        (
            "trusted-time-after-revoked-at",
            later_revocation_registry,
            "2026-07-15T01:00:01Z",
        ),
        (
            "malformed-trusted-time",
            command_source["registry"],
            "not-a-timestamp",
        ),
    )
    for evaluation_id, registry, trusted_time in trusted_time_cases:
        evaluation = _base_evaluation(
            evaluation_id=evaluation_id,
            profile_id="command",
            mode="first-admission",
            profile_evaluation=command_source,
            registry=registry,
        )
        evaluation["trustedContext"] = _trusted_context(
            command_record,
            trusted_accepted_at=trusted_time,
        )
        rejected.append(evaluation)

    conflicting_record = _base_evaluation(
        evaluation_id="conflicting-record",
        profile_id="command",
        mode="first-admission",
        profile_evaluation=command_source,
    )
    conflicting_record["trustedContext"] = _trusted_context(command_record)
    conflicting_record["append"] = {"status": "conflict"}
    rejected.append(conflicting_record)

    non_service = _base_evaluation(
        evaluation_id="accepted-by-non-service",
        profile_id="command",
        mode="historical-replay",
        profile_evaluation=command_source,
    )
    non_service["lookup"] = _found(invalid_paths["accepted-by-non-service"])
    rejected.append(non_service)

    unauthenticated = _base_evaluation(
        evaluation_id="accepting-service-not-authenticated",
        profile_id="command",
        mode="historical-replay",
        profile_evaluation=command_source,
    )
    unauthenticated["lookup"] = {"status": "unauthenticated"}
    rejected.append(unauthenticated)

    append_integrity = _base_evaluation(
        evaluation_id="append-integrity-not-established",
        profile_id="command",
        mode="first-admission",
        profile_evaluation=command_source,
    )
    append_integrity["trustedContext"] = _trusted_context(command_record)
    append_integrity["append"] = {"status": "integrity-failed"}
    rejected.append(append_integrity)

    indeterminate = _base_evaluation(
        evaluation_id="admission-log-indeterminate",
        profile_id="command",
        mode="historical-replay",
        profile_evaluation=command_source,
    )
    indeterminate["lookup"] = {"status": "indeterminate"}
    rejected.append(indeterminate)

    self_anchoring = _base_evaluation(
        evaluation_id="event-self-anchoring",
        profile_id="event",
        mode="historical-replay",
        profile_evaluation=event_source,
    )
    self_anchoring["lookup"] = _found(event_source["document"])
    rejected.append(self_anchoring)

    rejected_evaluation_ids = [evaluation["id"] for evaluation in rejected]
    if set(REJECTED_REASONS) != set(rejected_evaluation_ids):
        raise RuntimeError("rejected evaluation IDs do not match the protected reason map")
    if not set(REJECTED_REASONS.values()).issubset(STABLE_REASONS):
        raise RuntimeError("rejected evaluation reason is outside the stable reason set")

    cases = [
        {
            "id": "accept.first-admission.idempotent-retry",
            "evaluations": [idempotent_retry],
        },
        {
            "id": "accept.first-admission.profile-matrix",
            "evaluations": profile_matrix,
        },
        {
            "id": "accept.historical-replay.later-expiry",
            "evaluations": [later_expiry],
        },
        {
            "id": "accept.historical-replay.later-revocation",
            "evaluations": [later_revocation],
        },
        {
            "id": "reject.admission.failure-matrix",
            "evaluations": rejected,
        },
    ]
    case_ids = [case["id"] for case in cases]
    if case_ids != sorted(case_ids):
        raise RuntimeError("Admission case IDs are not lexically sorted")
    if len(case_ids) != len(set(case_ids)):
        raise RuntimeError("Admission case IDs are not unique")
    return cases


def _artifact_index(
    paths: list[str],
    generated_files: dict[str, bytes],
) -> list[dict[str, Any]]:
    normalized_paths = sorted(set(paths))
    if len(normalized_paths) != len(paths):
        raise RuntimeError("Admission artifact paths are not unique")
    artifacts = []
    for relative in normalized_paths:
        content = (
            generated_files[relative]
            if relative in generated_files
            else (ROOT / relative).read_bytes()
        )
        artifacts.append(
            {
                "path": relative,
                "byteLength": len(content),
                "sha256": _sha256(content),
            }
        )
    return artifacts


def _assert_fixture_closure(
    expected_paths: set[str],
    *,
    allow_missing: bool,
) -> None:
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for directory in (VALID_RECORD_ROOT, INVALID_RECORD_ROOT, REGISTRY_ROOT)
        for path in directory.rglob("*")
        if path.is_file()
    }
    unexpected = sorted(actual_paths - expected_paths)
    missing = sorted(expected_paths - actual_paths)
    if unexpected or (missing and not allow_missing):
        raise RuntimeError(
            "Admission generated fixture closure mismatch: "
            f"unexpected={unexpected!r}, missing={missing!r}"
        )


def generate() -> None:
    if not (ADMISSION_ROOT / "manifest.schema.json").is_file():
        raise RuntimeError("admission/manifest.schema.json must exist before generation")

    cryptography_manifest = _load_json(CRYPTOGRAPHY_MANIFEST_PATH)
    if not isinstance(cryptography_manifest, dict):
        raise RuntimeError("cryptography/manifest.json is not an object")
    cryptography_digest_input = copy.deepcopy(cryptography_manifest)
    claimed_cryptography_digest = cryptography_digest_input.pop(
        "artifactDigest",
        None,
    )
    computed_cryptography_digest = _sha256(rfc8785.dumps(cryptography_digest_input))
    if (
        claimed_cryptography_digest != CRYPTOGRAPHY_DIGEST
        or computed_cryptography_digest != CRYPTOGRAPHY_DIGEST
    ):
        raise RuntimeError("cryptography artifact digest does not match the frozen pin")

    profile_evaluations = _profile_evaluations(cryptography_manifest)
    records, valid_paths, invalid_paths, generated_files = _build_records(
        profile_evaluations
    )
    later_revocation_registry, later_revocation_bytes = (
        _build_later_revocation_registry()
    )
    generated_files[later_revocation_registry] = later_revocation_bytes
    expected_fixture_paths = {
        *valid_paths.values(),
        *invalid_paths.values(),
        later_revocation_registry,
    }
    _assert_fixture_closure(expected_fixture_paths, allow_missing=True)
    cases = _build_cases(
        profile_evaluations,
        records,
        valid_paths,
        invalid_paths,
        later_revocation_registry,
    )

    artifact_paths = [
        "admission/manifest.schema.json",
        *valid_paths.values(),
        *invalid_paths.values(),
        later_revocation_registry,
        "schemas/common.schema.json",
        "schemas/first-admission-record.schema.json",
    ]
    artifacts = _artifact_index(artifact_paths, generated_files)
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
        raise RuntimeError(
            f"Admission bundle counts {actual!r} do not match {expected!r}"
        )

    evaluation_ids = [
        evaluation["id"]
        for case in cases
        for evaluation in case["evaluations"]
    ]
    if len(evaluation_ids) != len(set(evaluation_ids)):
        raise RuntimeError("Admission evaluation IDs are not unique")

    manifest_without_digest = {
        "$schema": "https://missionweaveprotocol.dev/admission/0.1/manifest.schema.json",
        "manifestVersion": 1,
        "protocolVersion": "0.1",
        "profileId": "missionweaveprotocol.first-admission-historical-trust.v0.1",
        "semanticStage": "admission",
        "wireCode": "AUTH_INVALID_SIGNATURE",
        "cryptography": {
            "manifest": "cryptography/manifest.json",
            "artifactDigest": CRYPTOGRAPHY_DIGEST,
        },
        "fixtureSchemas": {
            "record": "schemas/first-admission-record.schema.json",
            "registry": "cryptography/registry-fixture.schema.json",
        },
        "artifacts": artifacts,
        "cases": cases,
    }
    manifest = copy.deepcopy(manifest_without_digest)
    manifest["artifactDigest"] = _sha256(rfc8785.dumps(manifest_without_digest))
    generated_files["admission/manifest.json"] = _json_bytes(manifest)
    _write_files_atomically(generated_files)

    print(
        "Generated MissionWeaveProtocol Admission bundle: "
        f"{case_count} cases, {evaluation_count} evaluations, "
        f"{len(artifacts)} artifacts."
    )


if __name__ == "__main__":
    generate()
