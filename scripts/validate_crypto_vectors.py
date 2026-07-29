#!/usr/bin/env python3
"""Validate the MissionWeaveProtocol signed-document cryptography bundle.

The validator deliberately keeps bundle-integrity failures separate from the
normative verification stages.  An expected vector failure may only consume a
``SemanticFailure`` raised at the first applicable stage; programming errors
and malformed bundle metadata fail the complete run.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import math
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import total_ordering
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urldefrag, urljoin

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from jsonschema import FormatChecker, ValidationError
from jsonschema.validators import extend, validator_for
from referencing import Registry, Resource
from referencing import exceptions as referencing_exceptions


ROOT = Path(__file__).resolve().parents[1]
CRYPTO_ROOT = ROOT / "cryptography"
KEY_ROOT = CRYPTO_ROOT / "keys"
VECTOR_ROOT = CRYPTO_ROOT / "vectors"
SCHEMA_ROOT = ROOT / "schemas"
MANIFEST_PATH = CRYPTO_ROOT / "manifest.json"
MANIFEST_SCHEMA_PATH = CRYPTO_ROOT / "manifest.schema.json"
REGISTRY_FIXTURE_SCHEMA_PATH = CRYPTO_ROOT / "registry-fixture.schema.json"
SIGNING_KEY_FIXTURE_SCHEMA_PATH = CRYPTO_ROOT / "signing-key-fixture.schema.json"
README_PATH = CRYPTO_ROOT / "README.md"

MANIFEST_SCHEMA_ID = (
    "https://missionweaveprotocol.dev/cryptography/0.1/manifest.schema.json"
)
REGISTRY_FIXTURE_SCHEMA_ID = (
    "https://missionweaveprotocol.dev/cryptography/0.1/registry-fixture.schema.json"
)
SIGNING_KEY_FIXTURE_SCHEMA_ID = (
    "https://missionweaveprotocol.dev/cryptography/0.1/signing-key-fixture.schema.json"
)
EXPECTED_FIXTURE_SCHEMAS = {
    "registry": "cryptography/registry-fixture.schema.json",
    "signingKey": "cryptography/signing-key-fixture.schema.json",
}
SCHEMA_ID_BASE = "https://missionweaveprotocol.dev/schemas/0.1/"
PROFILE_ID = "missionweaveprotocol.signed-document-verification.v0.1"
SEMANTIC_STAGES = (
    "parse",
    "schema",
    "signature-envelope",
    "key-resolution",
    "canonicalization",
    "signature",
    "complete",
)
FAILURE_WIRE_CODES = {
    "parse": "PROTOCOL_VIOLATION",
    "schema": "SCHEMA_VALIDATION_FAILED",
    "signature-envelope": "AUTH_INVALID_SIGNATURE",
    "key-resolution": "AUTH_INVALID_SIGNATURE",
    "canonicalization": "PROTOCOL_VIOLATION",
    "signature": "AUTH_INVALID_SIGNATURE",
}
EXPECTED_FAILURE_HISTOGRAM = {
    "parse": 4,
    "schema": 5,
    "signature-envelope": 11,
    "key-resolution": 24,
    "canonicalization": 2,
    "signature": 4,
}
EXPECTED_FAULT_SURFACES = {
    "duplicate-decoded-member": "document",
    "invalid-utf8": "document",
    "utf8-bom": "document",
    "trailing-data": "document",
    "unsupported-algorithm": "document",
    "timestamp-leap-second": "document",
    "timestamp-unknown-local-offset": "document",
    "timestamp-year-zero": "document",
    "padded-signature-base64url": "document",
    "signature-nonzero-unused-pad-bits": "document",
    "signature-wrong-length": "document",
    "signature-r-noncanonical": "document",
    "signature-r-y-equals-p": "document",
    "signature-r-off-curve": "document",
    "signature-r-negative-zero": "document",
    "signature-r-small-order": "document",
    "signature-r-mixed-order": "document",
    "signature-s-out-of-range": "document",
    "protected-time-not-utc-z": "document",
    "protected-time-created-at-mismatch": "document",
    "unknown-key": "document",
    "key-id-alias": "document-and-registry",
    "public-key-wrong-length": "registry",
    "registry-organization-id-relative-reference": "registry",
    "registry-selected-service-principal-id-iri-only": "registry",
    "registry-unrelated-principal-id-malformed-percent": "registry",
    "registry-unrelated-key-id-trailing-line-feed": "registry",
    "key-not-yet-valid": "registry",
    "valid-until-equality": "registry",
    "revoked-at-equality": "registry",
    "agent-card-signer-not-service": "document",
    "artifact-signer-not-producer": "document",
    "cross-principal-public-key-reuse": "registry",
    "public-key-identity": "document-and-registry",
    "public-key-off-curve": "registry",
    "public-key-negative-zero": "registry",
    "public-key-y-equals-p": "registry",
    "public-key-small-order": "document-and-registry",
    "public-key-mixed-order": "document-and-registry",
    "public-key-noncanonical-encoding": "document-and-registry",
    "public-key-padded-base64url": "registry",
    "public-key-nonzero-unused-pad-bits": "registry",
    "wrong-principal-binding": "registry",
    "public-key-rebinding": "registry",
    "number-outside-finite-binary64": "document",
    "unpaired-unicode-surrogate": "document",
    "payload-tamper": "document",
    "identity-r-equation-mismatch": "document",
    "payload-nested-signature-tamper": "document",
    "extension-nested-signature-tamper": "document",
}
EXPECTED_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "profileId": "agent-card",
        "schema": "schemas/agent-card.schema.json",
        "protectedTimePointer": "/issuedAt",
        "expectedSigner": {"rule": "service-principal"},
    },
    {
        "profileId": "approval",
        "schema": "schemas/approval.schema.json",
        "protectedTimePointer": "/occurredAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/approver"},
    },
    {
        "profileId": "artifact",
        "schema": "schemas/artifact.schema.json",
        "protectedTimePointer": "/createdAt",
        "expectedSigner": {"rule": "agent-id", "idPointer": "/producer/agentId"},
    },
    {
        "profileId": "command",
        "schema": "schemas/command.schema.json",
        "protectedTimePointer": "/issuedAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/actor"},
    },
    {
        "profileId": "context-package",
        "schema": "schemas/context-package.schema.json",
        "protectedTimePointer": "/generatedAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/generatedBy"},
    },
    {
        "profileId": "event",
        "schema": "schemas/event.schema.json",
        "protectedTimePointer": "/occurredAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/acceptedBy"},
    },
    {
        "profileId": "evidence",
        "schema": "schemas/evidence.schema.json",
        "protectedTimePointer": "/createdAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/generatedBy"},
    },
    {
        "profileId": "extension-profile",
        "schema": "schemas/extension-profile.schema.json",
        "protectedTimePointer": "/approvedAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/approvedBy"},
    },
    {
        "profileId": "group-snapshot",
        "schema": "schemas/group-snapshot.schema.json",
        "protectedTimePointer": "/createdAt",
        "expectedSigner": {"rule": "principal-object", "pointer": "/createdBy"},
    },
)
EXPECTED_SIGNED_SCHEMAS = frozenset(profile["schema"] for profile in EXPECTED_PROFILES)
BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
ASCII_PATH_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
RFC3339_RE = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"[Tt](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]+))?"
    r"(?P<offset>[Zz]|[+-][0-9]{2}:[0-9]{2})$"
)
ED25519_FIELD = 2**255 - 19
ED25519_ORDER = 2**252 + 27742317777372353535851937790883648493
ED25519_D = (-121665 * pow(121666, ED25519_FIELD - 2, ED25519_FIELD)) % ED25519_FIELD
ED25519_SQRT_M1 = pow(2, (ED25519_FIELD - 1) // 4, ED25519_FIELD)
ED25519_IDENTITY = (0, 1, 1, 0)


JsonValue = Any


class BundleValidationError(RuntimeError):
    """The conformance bundle or its metadata is internally inconsistent."""


class StrictJsonError(ValueError):
    """Raw bytes are not exactly one strict UTF-8 JSON value."""


class SemanticFailure(Exception):
    """An intentional failure at one normative verification stage."""

    def __init__(self, stage: str, detail: str) -> None:
        super().__init__(detail)
        self.stage = stage
        self.wire_code = FAILURE_WIRE_CODES[stage]
        self.detail = detail


@dataclass(frozen=True)
class EnvelopeResult:
    protected_time: str
    protected_instant: Rfc3339Instant
    key_id: str
    signature_text: str
    signature_bytes: bytes
    exact_principal: dict[str, str] | None
    service_principal: bool


@dataclass(frozen=True)
class ResolvedKey:
    organization_id: str
    key_id: str
    principal: dict[str, str]
    algorithm: str
    public_key_text: str
    public_key_bytes: bytes
    valid_from: Rfc3339Instant
    valid_until: Rfc3339Instant | None
    revoked_at: Rfc3339Instant | None


@dataclass(frozen=True)
class VerifiedResult:
    document: dict[str, Any]
    envelope: EnvelopeResult
    key: ResolvedKey
    signing_bytes: bytes
    signing_hash: str


@dataclass(frozen=True)
class ExtremeJsonNumber:
    """A valid JSON number whose exponent is outside libmpdec's range.

    Such a token is still a stage-1 JSON number.  Its exponent is necessarily
    many orders of magnitude beyond any coefficient that can fit in a vector,
    so binary64 conversion is deterministically overflow or signed underflow.
    """

    token: str
    negative: bool
    underflow: bool

    @property
    def is_integer(self) -> bool:
        return not self.underflow

    def _compare_to_finite(self, other: object) -> int | None:
        if isinstance(other, bool) or not isinstance(other, (int, float, Decimal)):
            return None
        other_decimal = Decimal(str(other))
        if self.underflow:
            if self.negative:
                return -1 if other_decimal >= 0 else 1
            return 1 if other_decimal <= 0 else -1
        return -1 if self.negative else 1

    def __lt__(self, other: object) -> bool:
        comparison = self._compare_to_finite(other)
        if comparison is None:
            return NotImplemented
        return comparison < 0

    def __le__(self, other: object) -> bool:
        comparison = self._compare_to_finite(other)
        if comparison is None:
            return NotImplemented
        return comparison <= 0

    def __gt__(self, other: object) -> bool:
        comparison = self._compare_to_finite(other)
        if comparison is None:
            return NotImplemented
        return comparison > 0

    def __ge__(self, other: object) -> bool:
        comparison = self._compare_to_finite(other)
        if comparison is None:
            return NotImplemented
        return comparison >= 0


@total_ordering
@dataclass(frozen=True)
class Rfc3339Instant:
    """An RFC 3339 instant with arbitrary fractional-second precision."""

    epoch_second: int
    fraction: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rfc3339Instant):
            return NotImplemented
        return (
            self.epoch_second == other.epoch_second and self.fraction == other.fraction
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Rfc3339Instant):
            return NotImplemented
        if self.epoch_second != other.epoch_second:
            return self.epoch_second < other.epoch_second
        width = max(len(self.fraction), len(other.fraction))
        return self.fraction.ljust(width, "0") < other.fraction.ljust(width, "0")


def _bundle_error(message: str) -> BundleValidationError:
    return BundleValidationError(message)


def _semantic(stage: str, message: str) -> SemanticFailure:
    return SemanticFailure(stage, message)


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _reject_json_constant(value: str) -> None:
    raise StrictJsonError(f"non-JSON numeric constant {value!r}")


def _parse_json_number(token: str) -> Decimal | ExtremeJsonNumber:
    try:
        return Decimal(token)
    except InvalidOperation:
        coefficient = token
        exponent_sign = ""
        if "e" in token.lower():
            coefficient, exponent = re.split("[eE]", token, maxsplit=1)
            exponent_sign = exponent[:1] if exponent[:1] in {"+", "-"} else "+"
        digits = coefficient.lstrip("-").replace(".", "")
        if not digits or set(digits) == {"0"}:
            return Decimal("-0" if token.startswith("-") else "0")
        return ExtremeJsonNumber(
            token=token,
            negative=token.startswith("-"),
            underflow=exponent_sign == "-",
        )


def _object_without_duplicate_names(
    pairs: list[tuple[str, JsonValue]],
) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for name, value in pairs:
        if name in result:
            raise StrictJsonError(f"duplicate decoded object member {name!r}")
        result[name] = value
    return result


def _strict_json(raw: bytes, *, label: str, preserve_numbers: bool = True) -> JsonValue:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictJsonError(f"{label} starts with a UTF-8 byte-order mark")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise StrictJsonError(f"{label} is not strict UTF-8: {error}") from error
    try:
        options: dict[str, Any] = {
            "parse_constant": _reject_json_constant,
            "object_pairs_hook": _object_without_duplicate_names,
        }
        if preserve_numbers:
            options.update(parse_float=_parse_json_number, parse_int=_parse_json_number)
        return json.loads(text, **options)
    except StrictJsonError:
        raise
    except json.JSONDecodeError as error:
        raise StrictJsonError(
            f"{label} is not exactly one JSON value: {error.msg} at byte-character "
            f"offset {error.pos}"
        ) from error


def _load_fixed_json(path: Path, *, label: str) -> JsonValue:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise _bundle_error(f"cannot read {label}: {error}") from error
    try:
        return _strict_json(raw, label=label, preserve_numbers=False)
    except StrictJsonError as error:
        raise _bundle_error(str(error)) from error


def _is_json_number(_checker: Any, instance: object) -> bool:
    if isinstance(instance, bool):
        return False
    if isinstance(instance, Decimal):
        return instance.is_finite()
    if isinstance(instance, ExtremeJsonNumber):
        return True
    if isinstance(instance, float):
        return math.isfinite(instance)
    return isinstance(instance, int)


def _is_json_integer(_checker: Any, instance: object) -> bool:
    if isinstance(instance, bool):
        return False
    if isinstance(instance, Decimal):
        return instance.is_finite() and instance == instance.to_integral_value()
    if isinstance(instance, ExtremeJsonNumber):
        return instance.is_integer
    if isinstance(instance, float):
        return math.isfinite(instance) and instance.is_integer()
    return isinstance(instance, int)


def _extended_validator(
    schema: Mapping[str, Any], *, registry: Registry | None = None
) -> Any:
    base_type = validator_for(schema)
    type_checker = base_type.TYPE_CHECKER.redefine("number", _is_json_number).redefine(
        "integer", _is_json_integer
    )
    validator_type = extend(base_type, type_checker=type_checker)
    options: dict[str, Any] = {"format_checker": PROTOCOL_FORMAT_CHECKER}
    if registry is not None:
        options["registry"] = registry
    return validator_type(schema, **options)


def _format_validation_error(error: ValidationError) -> str:
    location = "/" + "/".join(str(part) for part in error.absolute_path)
    if location == "/":
        location = "<root>"
    return f"{location}: {error.message}"


def _validate_instance(
    instance: JsonValue,
    schema: Mapping[str, Any],
    *,
    label: str,
    registry: Registry | None = None,
) -> None:
    try:
        validator = _extended_validator(schema, registry=registry)
        errors = sorted(
            validator.iter_errors(instance), key=lambda item: list(item.absolute_path)
        )
    except (
        referencing_exceptions.Unresolvable,
        referencing_exceptions.NoSuchResource,
        referencing_exceptions.Unretrievable,
    ) as error:
        raise _bundle_error(
            f"{label} Schema reference cannot be resolved: {error}"
        ) from error
    if errors:
        raise _bundle_error(
            f"{label} failed Schema validation: {_format_validation_error(errors[0])}"
        )


def _number_to_binary64(value: Decimal | ExtremeJsonNumber) -> float:
    if isinstance(value, ExtremeJsonNumber):
        if value.underflow:
            return -0.0 if value.negative else 0.0
        raise ValueError(f"number {value.token} is outside the finite binary64 domain")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"number {value!s} is outside the binary64 domain") from error
    if not math.isfinite(converted):
        raise ValueError(f"number {value!s} is outside the finite binary64 domain")
    return converted


def _jcs_input(value: JsonValue) -> JsonValue:
    if isinstance(value, (Decimal, ExtremeJsonNumber)):
        return _number_to_binary64(value)
    if isinstance(value, list):
        return [_jcs_input(item) for item in value]
    if isinstance(value, dict):
        return {key: _jcs_input(item) for key, item in value.items()}
    return value


def _jcs_bytes(value: JsonValue) -> bytes:
    return rfc8785.dumps(_jcs_input(value))


def _repository_path(
    value: object,
    *,
    allowed_roots: Sequence[Path],
    label: str,
) -> Path:
    if not isinstance(value, str) or not value:
        raise _bundle_error(f"{label} must be a non-empty repository path")
    if "\x00" in value or "\\" in value:
        raise _bundle_error(
            f"{label} is not a canonical POSIX repository path: {value!r}"
        )
    if not value.isascii() or value != value.lower():
        raise _bundle_error(f"{label} must use lower-case ASCII: {value!r}")
    if value.startswith("/") or value.endswith("/"):
        raise _bundle_error(f"{label} must be relative and name a file: {value!r}")

    raw_parts = value.split("/")
    if any(
        not part or part in {".", ".."} or not ASCII_PATH_SEGMENT_RE.fullmatch(part)
        for part in raw_parts
    ):
        raise _bundle_error(f"{label} has an unsafe path segment: {value!r}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or tuple(relative.parts) != tuple(raw_parts):
        raise _bundle_error(f"{label} is not a canonical repository path: {value!r}")

    candidate = ROOT.joinpath(*raw_parts)
    current = ROOT
    try:
        for part in raw_parts:
            current = current / part
            if current.is_symlink():
                raise _bundle_error(f"{label} traverses a symbolic link: {value!r}")
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise _bundle_error(f"{label} does not exist: {value!r}") from error
    except OSError as error:
        raise _bundle_error(f"cannot resolve {label} {value!r}: {error}") from error

    resolved_roots = [root.resolve(strict=True) for root in allowed_roots]
    if not any(resolved.is_relative_to(root) for root in resolved_roots):
        allowed = ", ".join(str(root.relative_to(ROOT)) for root in allowed_roots)
        raise _bundle_error(
            f"{label} is outside its allowed roots ({allowed}): {value!r}"
        )
    try:
        mode = resolved.stat().st_mode
    except OSError as error:
        raise _bundle_error(f"cannot stat {label} {value!r}: {error}") from error
    if not stat.S_ISREG(mode):
        raise _bundle_error(f"{label} is not a regular file: {value!r}")
    return resolved


def _read_artifacts(manifest: Mapping[str, Any]) -> dict[str, bytes]:
    artifacts = manifest["artifacts"]
    paths = [item["path"] for item in artifacts]
    if paths != sorted(paths):
        raise _bundle_error("manifest artifacts must be sorted by path")
    if len(paths) != len(set(paths)):
        raise _bundle_error("manifest contains duplicate artifact paths")
    folded = [path.casefold() for path in paths]
    if len(folded) != len(set(folded)):
        raise _bundle_error("manifest artifact paths collide after case folding")

    cache: dict[str, bytes] = {}
    for index, item in enumerate(artifacts):
        repository_path = _repository_path(
            item["path"],
            allowed_roots=(CRYPTO_ROOT, SCHEMA_ROOT),
            label=f"artifacts[{index}].path",
        )
        try:
            raw = repository_path.read_bytes()
        except OSError as error:
            raise _bundle_error(
                f"cannot read artifact {item['path']}: {error}"
            ) from error
        if len(raw) != int(item["byteLength"]):
            raise _bundle_error(
                f"artifact {item['path']} byteLength mismatch: expected "
                f"{item['byteLength']}, got {len(raw)}"
            )
        digest = _sha256(raw)
        if digest != item["sha256"]:
            raise _bundle_error(
                f"artifact {item['path']} digest mismatch: expected {item['sha256']}, "
                f"got {digest}"
            )
        cache[item["path"]] = raw

    for path in CRYPTO_ROOT.rglob("*"):
        if path.is_symlink():
            raise _bundle_error(
                f"cryptography bundle contains a symbolic link: {path.relative_to(ROOT)}"
            )
    exceptions = {MANIFEST_PATH.resolve(), README_PATH.resolve()}
    disk_crypto_files = {
        path.resolve().relative_to(ROOT).as_posix()
        for path in CRYPTO_ROOT.rglob("*")
        if path.is_file() and path.resolve() not in exceptions
    }
    listed_crypto_files = {path for path in cache if path.startswith("cryptography/")}
    if disk_crypto_files != listed_crypto_files:
        missing = sorted(disk_crypto_files - listed_crypto_files)
        absent = sorted(listed_crypto_files - disk_crypto_files)
        details: list[str] = []
        if missing:
            details.append("unlisted cryptography files: " + ", ".join(missing))
        if absent:
            details.append("listed files outside disk closure: " + ", ".join(absent))
        raise _bundle_error("; ".join(details))
    return cache


def _schema_artifacts(cache: Mapping[str, bytes]) -> dict[str, Mapping[str, Any]]:
    schemas: dict[str, Mapping[str, Any]] = {}
    for path in sorted(cache):
        if not path.startswith("schemas/") or not path.endswith(".json"):
            continue
        document = _parse_cached_json(cache, path, label="Schema artifact")
        if not isinstance(document, dict):
            raise _bundle_error(f"Schema artifact is not an object: {path}")
        schemas[path] = document
    return schemas


def _index_schema_resource_ids(
    value: JsonValue,
    *,
    base_uri: str,
    path: str,
    index: dict[str, str],
) -> None:
    if isinstance(value, dict):
        local_base = base_uri
        identifier = value.get("$id")
        if isinstance(identifier, str):
            try:
                local_base = urljoin(base_uri, identifier)
            except ValueError as error:
                raise _bundle_error(
                    f"Schema artifact {path} has an invalid $id {identifier!r}: {error}"
                ) from error
            resource_uri, _fragment = urldefrag(local_base)
            existing = index.get(resource_uri)
            if existing is not None and existing != path:
                raise _bundle_error(
                    f"Schema resource ID {resource_uri!r} is defined by both "
                    f"{existing} and {path}"
                )
            index[resource_uri] = path
        for child in value.values():
            _index_schema_resource_ids(
                child, base_uri=local_base, path=path, index=index
            )
    elif isinstance(value, list):
        for child in value:
            _index_schema_resource_ids(child, base_uri=base_uri, path=path, index=index)


def _schema_references(
    value: JsonValue, *, base_uri: str, label: str
) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []

    def visit(node: JsonValue, current_base: str) -> None:
        if isinstance(node, dict):
            local_base = current_base
            identifier = node.get("$id")
            if isinstance(identifier, str):
                try:
                    local_base = urljoin(current_base, identifier)
                except ValueError as error:
                    raise _bundle_error(
                        f"{label} has an invalid $id {identifier!r}: {error}"
                    ) from error
            for keyword in ("$ref", "$dynamicRef"):
                reference = node.get(keyword)
                if isinstance(reference, str):
                    references.append((local_base, reference))
            for child in node.values():
                visit(child, local_base)
        elif isinstance(node, list):
            for child in node:
                visit(child, current_base)

    visit(value, base_uri)
    return references


def _artifact_references(
    manifest: Mapping[str, Any], cache: Mapping[str, bytes]
) -> set[str]:
    referenced = {
        "cryptography/manifest.schema.json",
        *manifest["fixtureSchemas"].values(),
    }
    schema_queue: list[str] = []
    for profile in manifest["profiles"]:
        schema_queue.append(profile["schema"])
        referenced.add(profile["schema"])

    for case in manifest["cases"]:
        for evaluation in case["evaluations"]:
            if case["kind"] == "canonicalization":
                referenced.update((evaluation["input"], evaluation["expectedJcs"]))
                continue
            referenced.update((evaluation["document"], evaluation["registry"]))
            signing_key = evaluation.get("signingKey")
            if signing_key is not None:
                referenced.add(signing_key)
            verified = evaluation["expect"].get("verified")
            if verified is not None:
                referenced.add(verified["signingBytes"])

    schema_documents = _schema_artifacts(cache)
    resource_paths: dict[str, str] = {}
    for path, schema in schema_documents.items():
        retrieval_uri = f"{SCHEMA_ID_BASE}{PurePosixPath(path).name}"
        resource_paths.setdefault(retrieval_uri, path)
        _index_schema_resource_ids(
            schema,
            base_uri=retrieval_uri,
            path=path,
            index=resource_paths,
        )

    seen_schemas: set[str] = set()
    while schema_queue:
        schema_path = schema_queue.pop()
        if schema_path in seen_schemas:
            continue
        seen_schemas.add(schema_path)
        schema = schema_documents.get(schema_path)
        if schema is None:
            raise _bundle_error(
                f"profile or Schema $ref is not indexed as an artifact: {schema_path}"
            )
        base_uri = schema.get("$id")
        if not isinstance(base_uri, str):
            base_uri = f"{SCHEMA_ID_BASE}{PurePosixPath(schema_path).name}"
        for reference_base, reference in _schema_references(
            schema, base_uri=base_uri, label=schema_path
        ):
            try:
                resolved = urljoin(reference_base, reference)
            except ValueError as error:
                raise _bundle_error(
                    f"Schema reference from {schema_path} is invalid: "
                    f"{reference!r}: {error}"
                ) from error
            resource_uri, _fragment = urldefrag(resolved)
            if not resource_uri:
                resource_uri, _fragment = urldefrag(reference_base)
            target = resource_paths.get(resource_uri)
            if target is None:
                raise _bundle_error(
                    f"Schema reference from {schema_path} resolves to unindexed resource "
                    f"{resource_uri!r}"
                )
            if target not in referenced:
                referenced.add(target)
                schema_queue.append(target)

    listed = set(cache)
    if referenced != listed:
        unreferenced = sorted(listed - referenced)
        unindexed = sorted(referenced - listed)
        details = []
        if unreferenced:
            details.append("unreferenced artifacts: " + ", ".join(unreferenced))
        if unindexed:
            details.append(
                "referenced artifacts absent from index: " + ", ".join(unindexed)
            )
        raise _bundle_error("; ".join(details))
    return referenced


def _validate_artifact_digest(manifest: Mapping[str, Any]) -> None:
    digest_input = copy.deepcopy(dict(manifest))
    digest_input.pop("artifactDigest", None)
    try:
        digest = _sha256(_jcs_bytes(digest_input))
    except (
        rfc8785.CanonicalizationError,
        UnicodeError,
        ValueError,
        OverflowError,
    ) as error:
        raise _bundle_error(
            f"cannot canonicalize manifest for artifactDigest: {error}"
        ) from error
    if digest != manifest["artifactDigest"]:
        raise _bundle_error(
            f"artifactDigest mismatch: expected {manifest['artifactDigest']}, got {digest}"
        )


def _parse_cached_json(
    cache: Mapping[str, bytes], path: str, *, label: str
) -> JsonValue:
    try:
        raw = cache[path]
    except KeyError as error:
        raise _bundle_error(f"{label} is not in the artifact cache: {path}") from error
    try:
        return _strict_json(raw, label=path, preserve_numbers=False)
    except StrictJsonError as error:
        raise _bundle_error(str(error)) from error


def _validate_profiles(
    manifest: Mapping[str, Any], cache: Mapping[str, bytes]
) -> tuple[dict[str, Mapping[str, Any]], Registry]:
    profiles = manifest["profiles"]
    if profiles != list(EXPECTED_PROFILES):
        raise _bundle_error(
            "profiles must exactly match the nine ordered v0.1 Signed Document profiles"
        )

    schemas: dict[str, Mapping[str, Any]] = {}
    resources: list[tuple[str, Resource[Any]]] = []
    schema_documents = _schema_artifacts(cache)
    required_schemas = EXPECTED_SIGNED_SCHEMAS | {"schemas/common.schema.json"}
    absent_required = sorted(required_schemas - set(schema_documents))
    if absent_required:
        raise _bundle_error(
            "required Signed Document Schema artifacts are absent: "
            + ", ".join(absent_required)
        )
    for schema_path, schema in sorted(schema_documents.items()):
        validator_type = validator_for(schema)
        try:
            validator_type.check_schema(schema)
        except Exception as error:
            raise _bundle_error(
                f"invalid normative Schema {schema_path}: {error}"
            ) from error
        expected_id = f"{SCHEMA_ID_BASE}{PurePosixPath(schema_path).name}"
        if schema.get("$id") != expected_id:
            raise _bundle_error(
                f"Schema ID mismatch in {schema_path}: expected {expected_id!r}, "
                f"got {schema.get('$id')!r}"
            )
        schemas[schema_path] = schema
        try:
            resource = Resource.from_contents(schema)
        except referencing_exceptions.CannotDetermineSpecification as error:
            raise _bundle_error(
                f"cannot determine JSON Schema dialect for {schema_path}: {error}"
            ) from error
        resources.append((expected_id, resource))

    signed_on_disk: set[str] = set()
    for path in sorted(SCHEMA_ROOT.glob("*.json")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in cache:
            try:
                document = _strict_json(
                    cache[relative], label=relative, preserve_numbers=False
                )
            except StrictJsonError as error:
                raise _bundle_error(str(error)) from error
        else:
            document = _load_fixed_json(path, label=relative)
        if isinstance(document, dict) and "signature" in document.get("required", []):
            signed_on_disk.add(relative)
    if signed_on_disk != EXPECTED_SIGNED_SCHEMAS:
        missing = sorted(signed_on_disk - EXPECTED_SIGNED_SCHEMAS)
        stale = sorted(EXPECTED_SIGNED_SCHEMAS - signed_on_disk)
        details = []
        if missing:
            details.append(
                "Signed Document schemas missing profiles: " + ", ".join(missing)
            )
        if stale:
            details.append(
                "profiles whose schemas no longer require signature: "
                + ", ".join(stale)
            )
        raise _bundle_error("; ".join(details))

    try:
        registry = Registry().with_resources(resources).crawl()
    except (
        referencing_exceptions.Unresolvable,
        referencing_exceptions.NoSuchResource,
        referencing_exceptions.Unretrievable,
    ) as error:
        raise _bundle_error(
            f"cannot build closed Schema resource registry: {error}"
        ) from error

    for schema_path, schema in sorted(schema_documents.items()):
        base_uri = schema.get("$id")
        if not isinstance(base_uri, str):
            base_uri = f"{SCHEMA_ID_BASE}{PurePosixPath(schema_path).name}"
        for reference_base, reference in _schema_references(
            schema, base_uri=base_uri, label=schema_path
        ):
            try:
                registry.resolver(reference_base).lookup(reference)
            except (referencing_exceptions.Unresolvable, ValueError) as error:
                try:
                    resolved = urljoin(reference_base, reference)
                except ValueError:
                    resolved = reference
                raise _bundle_error(
                    f"Schema reference from {schema_path} cannot be resolved: "
                    f"{resolved!r}: {error}"
                ) from error

    return schemas, registry


def _evaluation_index(
    manifest: Mapping[str, Any],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    index: dict[tuple[str, str], Mapping[str, Any]] = {}
    for case in manifest["cases"]:
        if case["kind"] == "canonicalization":
            continue
        for evaluation in case["evaluations"]:
            if evaluation["expect"]["stage"] != "complete":
                continue
            key = (case["id"], evaluation["profileId"])
            if key in index:
                raise _bundle_error(f"duplicate complete evaluation basis {key!r}")
            index[key] = evaluation
    return index


def _validate_case_matrix(manifest: Mapping[str, Any]) -> None:
    cases = manifest["cases"]
    case_ids = [case["id"] for case in cases]
    if case_ids != sorted(case_ids):
        raise _bundle_error("manifest cases must be sorted by id")
    if len(case_ids) != len(set(case_ids)):
        raise _bundle_error("manifest contains duplicate case IDs")

    profile_ids = [profile["profileId"] for profile in manifest["profiles"]]
    basis_index = _evaluation_index(manifest)
    fault_ids: set[str] = set()
    accept_cases = 0
    reject_cases = 0
    complete_evaluations = 1  # the pure canonicalization evaluation
    rejected_evaluations = 0
    failure_histogram: Counter[str] = Counter()
    kind_histogram: Counter[str] = Counter(case["kind"] for case in cases)

    if kind_histogram["canonicalization"] != 1:
        raise _bundle_error("manifest must contain exactly one canonicalization case")
    if kind_histogram["profile-matrix"] != 1:
        raise _bundle_error("manifest must contain exactly one profile-matrix case")
    if kind_histogram["failure-matrix"] != 6:
        raise _bundle_error("manifest must contain exactly six failure-matrix cases")

    for case in cases:
        evaluations = case["evaluations"]
        if case["kind"] == "canonicalization":
            accept_cases += 1
            continue
        stages = [evaluation["expect"]["stage"] for evaluation in evaluations]
        all_complete = all(stage == "complete" for stage in stages)
        all_rejected = all(stage != "complete" for stage in stages)
        if not (all_complete or all_rejected):
            raise _bundle_error(
                f"case {case['id']!r} mixes complete and rejected evaluations"
            )
        if all_complete:
            accept_cases += 1
        else:
            reject_cases += 1

        if case["kind"] == "single" and len(evaluations) != 1:
            raise _bundle_error(
                f"single case {case['id']!r} must have exactly one evaluation"
            )
        if case["kind"] == "profile-matrix":
            actual_profiles = [evaluation["profileId"] for evaluation in evaluations]
            if actual_profiles != profile_ids or not all_complete:
                raise _bundle_error(
                    "profile-matrix must contain one ordered complete evaluation for every profile"
                )
        if case["kind"] == "failure-matrix":
            expected_matrix = {
                "reject.parse.byte-level-matrix": (3, "parse"),
                "reject.schema.validation-matrix": (4, "schema"),
                "reject.signature-envelope.ed25519-encoding-matrix": (
                    8,
                    "signature-envelope",
                ),
                "reject.key-resolution.matrix": (19, "key-resolution"),
                "reject.canonicalization.data-model-matrix": (
                    2,
                    "canonicalization",
                ),
                "reject.signature.equation-matrix": (2, "signature"),
            }.get(case["id"])
            if expected_matrix is None:
                raise _bundle_error(f"unknown failure matrix {case['id']!r}")
            expected_count, expected_stage = expected_matrix
            if len(evaluations) != expected_count or not all_rejected:
                raise _bundle_error(
                    f"failure matrix {case['id']!r} must contain exactly "
                    f"{expected_count} rejected evaluations"
                )
            if any(stage != expected_stage for stage in stages):
                raise _bundle_error(
                    f"failure matrix {case['id']!r} must fail at {expected_stage!r}"
                )

        for evaluation in evaluations:
            expected = evaluation["expect"]
            stage = expected["stage"]
            if stage == "complete":
                complete_evaluations += 1
                if evaluation["fault"] is not None or expected["wireCode"] is not None:
                    raise _bundle_error(
                        "complete evaluations must have null fault and wireCode"
                    )
                continue

            rejected_evaluations += 1
            failure_histogram[stage] += 1
            fault = evaluation["fault"]
            if fault["id"] in fault_ids:
                raise _bundle_error(f"fault ID is reused: {fault['id']}")
            fault_ids.add(fault["id"])
            basis_key = (fault["basis"]["caseId"], fault["basis"]["profileId"])
            basis = basis_index.get(basis_key)
            if basis is None:
                raise _bundle_error(
                    f"fault {fault['id']!r} does not name a complete evaluation basis"
                )
            if evaluation["profileId"] != fault["basis"]["profileId"]:
                raise _bundle_error(
                    f"fault {fault['id']!r} changes profileId relative to its basis"
                )
            document_changed = evaluation["document"] != basis["document"]
            registry_changed = evaluation["registry"] != basis["registry"]
            actual_surface = (
                "document-and-registry"
                if document_changed and registry_changed
                else "document"
                if document_changed
                else "registry"
                if registry_changed
                else "none"
            )
            expected_surface = EXPECTED_FAULT_SURFACES.get(fault["id"])
            if expected_surface is not None and actual_surface != expected_surface:
                raise _bundle_error(
                    f"fault {fault['id']!r} must change {expected_surface}, not {actual_surface}"
                )

    if len(cases) != 22:
        raise _bundle_error(f"expected 22 cases, found {len(cases)}")
    if accept_cases != 4 or reject_cases != 18:
        raise _bundle_error(
            f"expected 4 accept and 18 reject cases, found {accept_cases} and {reject_cases}"
        )
    if complete_evaluations != 12 or rejected_evaluations != 50:
        raise _bundle_error(
            "expected 62 evaluations (12 complete and 50 rejected), found "
            f"{complete_evaluations + rejected_evaluations} "
            f"({complete_evaluations} complete and {rejected_evaluations} rejected)"
        )
    if dict(failure_histogram) != EXPECTED_FAILURE_HISTOGRAM:
        raise _bundle_error(
            f"reject stage histogram mismatch: expected {EXPECTED_FAILURE_HISTOGRAM}, "
            f"got {dict(failure_histogram)}"
        )
    expected_fault_ids = set(EXPECTED_FAULT_SURFACES)
    if fault_ids != expected_fault_ids:
        missing = sorted(expected_fault_ids - fault_ids)
        unknown = sorted(fault_ids - expected_fault_ids)
        details = []
        if missing:
            details.append("missing registered faults: " + ", ".join(missing))
        if unknown:
            details.append("unknown faults: " + ", ".join(unknown))
        raise _bundle_error("; ".join(details))


def _validate_timestamp_profile_coverage(
    manifest: Mapping[str, Any], cache: Mapping[str, bytes]
) -> None:
    cases = {case["id"]: case for case in manifest["cases"]}

    alternate_case = cases.get("accept.command.alternate-json-serialization")
    if alternate_case is None or len(alternate_case["evaluations"]) != 1:
        raise _bundle_error(
            "alternate-serialization case must contain one timestamp-profile evaluation"
        )
    alternate_evaluation = alternate_case["evaluations"][0]
    alternate_document = _parse_cached_json(
        cache,
        alternate_evaluation["document"],
        label="lowercase-t alternate Command",
    )
    if not isinstance(alternate_document, dict):
        raise _bundle_error("lowercase-t alternate Command is not an object")
    protected_time = alternate_document.get("issuedAt")
    signature = alternate_document.get("signature")
    if protected_time != "2026-07-15t00:00:00Z" or not isinstance(signature, dict):
        raise _bundle_error(
            "alternate Command does not exercise lowercase t with uppercase Z"
        )
    if signature.get("createdAt") != protected_time:
        raise _bundle_error("alternate Command protected timestamps are not byte-equal")
    alternate_raw = cache[alternate_evaluation["document"]]
    if not alternate_raw.startswith(b'\n{"signature":'):
        raise _bundle_error(
            "alternate Command no longer uses the declared alternate JSON serialization"
        )

    alternate_registry = _parse_cached_json(
        cache,
        alternate_evaluation["registry"],
        label="timestamp casing and offset Registry",
    )
    if not isinstance(alternate_registry, dict):
        raise _bundle_error("timestamp casing and offset Registry is not an object")
    alternate_bindings = [
        binding
        for binding in alternate_registry.get("bindings", [])
        if isinstance(binding, dict)
        and binding.get("keyId") == alternate_evaluation["expect"]["verified"]["keyId"]
    ]
    if len(alternate_bindings) != 1:
        raise _bundle_error(
            "timestamp casing and offset Registry does not contain one selected binding"
        )
    alternate_binding = alternate_bindings[0]
    histories = alternate_binding.get("validityHistory")
    if not isinstance(histories, list) or len(histories) != 1:
        raise _bundle_error(
            "timestamp casing and offset binding must contain one validity record"
        )
    history = histories[0]
    if (
        alternate_binding.get("validFrom") != "2026-07-14T00:01:00-23:59"
        or not isinstance(history, dict)
        or history.get("recordedAt") != "2026-07-01t00:00:00z"
        or history.get("validUntil") != "2026-07-15T23:59:01+23:59"
    ):
        raise _bundle_error(
            "timestamp casing and offset Registry no longer covers lowercase z and full offsets"
        )
    valid_from = _parse_rfc3339_value(alternate_binding["validFrom"])
    protected_instant = _parse_rfc3339_value(protected_time)
    valid_until = _parse_rfc3339_value(history["validUntil"])
    _parse_rfc3339_value(history["recordedAt"])
    if valid_from != protected_instant or not protected_instant < valid_until:
        raise _bundle_error(
            "timestamp casing and full-offset fixtures do not establish the intended interval"
        )

    profile_case = cases.get("accept.profile-matrix.all-nine")
    if profile_case is None:
        raise _bundle_error("all-profile case is absent")
    command_evaluations = [
        evaluation
        for evaluation in profile_case["evaluations"]
        if evaluation["profileId"] == "command"
    ]
    if len(command_evaluations) != 1:
        raise _bundle_error(
            "all-profile case must contain one fractional-precision Command"
        )
    fractional_evaluation = command_evaluations[0]
    fractional_document = _parse_cached_json(
        cache,
        fractional_evaluation["document"],
        label="fractional-precision Command",
    )
    fractional_registry = _parse_cached_json(
        cache,
        fractional_evaluation["registry"],
        label="fractional-precision Registry",
    )
    if not isinstance(fractional_document, dict) or not isinstance(
        fractional_registry, dict
    ):
        raise _bundle_error("fractional-precision fixtures are not objects")
    fractional_protected = fractional_document.get("issuedAt")
    fractional_signature = fractional_document.get("signature")
    if not isinstance(fractional_protected, str) or not isinstance(
        fractional_signature, dict
    ):
        raise _bundle_error("fractional-precision Command has no protected timestamp")
    if fractional_signature.get("createdAt") != fractional_protected:
        raise _bundle_error(
            "fractional-precision protected timestamps are not byte-equal"
        )
    fractional_bindings = [
        binding
        for binding in fractional_registry.get("bindings", [])
        if isinstance(binding, dict)
        and binding.get("keyId") == fractional_evaluation["expect"]["verified"]["keyId"]
    ]
    if len(fractional_bindings) != 1:
        raise _bundle_error(
            "fractional-precision Registry does not contain one selected binding"
        )
    fractional_history = fractional_bindings[0].get("validityHistory")
    if not isinstance(fractional_history, list) or len(fractional_history) != 1:
        raise _bundle_error(
            "fractional-precision binding must contain one validity record"
        )
    fractional_until = fractional_history[0].get("validUntil")
    if not isinstance(fractional_until, str):
        raise _bundle_error("fractional-precision binding has no validUntil")
    protected_fraction = fractional_protected.split(".", 1)[-1].removesuffix("Z")
    until_fraction = fractional_until.split(".", 1)[-1].removesuffix("Z")
    differences = [
        index
        for index, (left, right) in enumerate(
            zip(protected_fraction, until_fraction, strict=True)
        )
        if left != right
    ]
    if (
        len(protected_fraction) <= 6
        or protected_fraction[:6] != until_fraction[:6]
        or not differences
        or differences[0] < 6
        or not _parse_rfc3339_value(fractional_protected)
        < _parse_rfc3339_value(fractional_until)
    ):
        raise _bundle_error(
            "fractional-precision fixtures do not order on a digit after microseconds"
        )

    schema_case = cases.get("reject.schema.validation-matrix")
    expected_invalid = {
        "timestamp-leap-second": "2026-06-30T23:59:60Z",
        "timestamp-unknown-local-offset": "2026-07-15T00:00:00-00:00",
        "timestamp-year-zero": "0000-01-01T00:00:00Z",
    }
    if schema_case is None or schema_case.get("kind") != "failure-matrix":
        raise _bundle_error("timestamp schema validation matrix is absent")
    timestamp_evaluations = {
        evaluation["fault"]["id"]: evaluation
        for evaluation in schema_case["evaluations"]
        if evaluation["fault"]["id"].startswith("timestamp-")
    }
    if set(timestamp_evaluations) != set(expected_invalid):
        raise _bundle_error(
            "timestamp schema validation matrix does not contain the required faults"
        )
    for fault_id, value in expected_invalid.items():
        evaluation = timestamp_evaluations[fault_id]
        if evaluation["expect"] != {
            "stage": "schema",
            "wireCode": "SCHEMA_VALIDATION_FAILED",
        }:
            raise _bundle_error(f"{fault_id} does not fail first at schema stage")
        document = _parse_cached_json(cache, evaluation["document"], label=fault_id)
        if (
            not isinstance(document, dict)
            or document.get("issuedAt") != value
            or not isinstance(document.get("signature"), dict)
            or document["signature"].get("createdAt") != value
        ):
            raise _bundle_error(
                f"{fault_id} does not isolate a byte-equal protected timestamp"
            )
        try:
            _parse_rfc3339_value(value)
        except ValueError:
            pass
        else:
            raise _bundle_error(f"{fault_id} is accepted by the timestamp parser")


def _json_pointer(document: JsonValue, pointer: str, *, stage: str) -> JsonValue:
    if not pointer.startswith("/"):
        raise _semantic(stage, f"invalid trusted JSON pointer {pointer!r}")
    current = document
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise _semantic(stage, f"trusted JSON pointer {pointer!r} does not resolve")
    return current


def _is_gregorian_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_from_civil(year: int, month: int, day: int) -> int:
    adjusted_year = year - (1 if month <= 2 else 0)
    era = adjusted_year // 400
    year_of_era = adjusted_year - era * 400
    adjusted_month = month + (-3 if month > 2 else 9)
    day_of_year = (153 * adjusted_month + 2) // 5 + day - 1
    day_of_era = year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    return era * 146097 + day_of_era - 719468


def _parse_rfc3339_value(value: str) -> Rfc3339Instant:
    match = RFC3339_RE.fullmatch(value)
    if match is None:
        raise ValueError("not an RFC 3339 timestamp")

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    if year == 0:
        raise ValueError("year 0000 is not supported")
    if month < 1 or month > 12:
        raise ValueError("month is outside 01 through 12")
    month_lengths = [
        31,
        29 if _is_gregorian_leap_year(year) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    if day < 1 or day > month_lengths[month - 1]:
        raise ValueError("day is invalid for the Gregorian month")
    if hour > 23 or minute > 59:
        raise ValueError("time is outside 00:00 through 23:59")
    if second > 59:
        raise ValueError("leap-second spellings are not supported in v0.1")

    offset_text = match.group("offset")
    if offset_text == "-00:00":
        raise ValueError("unknown-local-offset spelling -00:00 is not an instant")
    offset_seconds = 0
    if offset_text not in {"Z", "z"}:
        offset_hour = int(offset_text[1:3])
        offset_minute = int(offset_text[4:6])
        if offset_hour > 23 or offset_minute > 59:
            raise ValueError("numeric offset is outside RFC 3339 bounds")
        direction = 1 if offset_text[0] == "+" else -1
        offset_seconds = direction * (offset_hour * 3600 + offset_minute * 60)

    local_second = (
        _days_from_civil(year, month, day) * 86400 + hour * 3600 + minute * 60 + second
    )
    fraction = (match.group("fraction") or "").rstrip("0")
    return Rfc3339Instant(
        epoch_second=local_second - offset_seconds,
        fraction=fraction,
    )


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


def _validate_protocol_uri_contract() -> None:
    accepted = (
        "example:",
        "example:/path",
        "urn:example:%E2%82%AC",
        "https://[2001:db8::1]/path",
        "https://example.com/" + "a" * 513,
    )
    rejected = (
        "",
        "relative/path",
        "1example:path",
        "https://例え.テスト/",
        "urn:example:%GG",
        "example:/path\n",
        "https://[not-an-ip]/",
    )
    for value in accepted:
        if not _is_protocol_uri(value):
            raise _bundle_error(f"protocol URI predicate rejects {value!r}")
    for value in rejected:
        if _is_protocol_uri(value):
            raise _bundle_error(f"protocol URI predicate accepts {value!r}")


@PROTOCOL_FORMAT_CHECKER.checks("date-time")
def _is_protocol_rfc3339(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        _parse_rfc3339_value(value)
    except ValueError:
        return False
    return True


def _parse_rfc3339_instant(value: object, *, stage: str, label: str) -> Rfc3339Instant:
    if not isinstance(value, str):
        raise _semantic(stage, f"{label} is not an RFC 3339 instant")
    try:
        return _parse_rfc3339_value(value)
    except ValueError as error:
        raise _semantic(
            stage, f"{label} is not an RFC 3339 instant: {error}"
        ) from error


def _canonical_base64url(value: object, *, stage: str, label: str) -> bytes:
    if not isinstance(value, str) or not BASE64URL_RE.fullmatch(value):
        raise _semantic(stage, f"{label} is not unpadded base64url")
    if len(value) % 4 == 1:
        raise _semantic(stage, f"{label} has an impossible base64url length")
    try:
        decoded = base64.b64decode(
            value + "=" * ((-len(value)) % 4), altchars=b"-_", validate=True
        )
    except (binascii.Error, ValueError) as error:
        raise _semantic(stage, f"{label} cannot be decoded as base64url") from error
    canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if canonical != value:
        raise _semantic(
            stage, f"{label} has nonzero unused pad bits or noncanonical spelling"
        )
    return decoded


def _ed25519_point_add(
    left: tuple[int, int, int, int], right: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = left
    x2, y2, z2, t2 = right
    a = (y1 - x1) * (y2 - x2) % ED25519_FIELD
    b = (y1 + x1) * (y2 + x2) % ED25519_FIELD
    c = 2 * ED25519_D * t1 * t2 % ED25519_FIELD
    d = 2 * z1 * z2 % ED25519_FIELD
    e = (b - a) % ED25519_FIELD
    f = (d - c) % ED25519_FIELD
    g = (d + c) % ED25519_FIELD
    h = (b + a) % ED25519_FIELD
    return (
        e * f % ED25519_FIELD,
        g * h % ED25519_FIELD,
        f * g % ED25519_FIELD,
        e * h % ED25519_FIELD,
    )


def _ed25519_scalar_multiply(
    point: tuple[int, int, int, int], scalar: int
) -> tuple[int, int, int, int]:
    result = ED25519_IDENTITY
    addend = point
    while scalar:
        if scalar & 1:
            result = _ed25519_point_add(result, addend)
        addend = _ed25519_point_add(addend, addend)
        scalar >>= 1
    return result


def _ed25519_is_identity(point: tuple[int, int, int, int]) -> bool:
    x, y, z, _t = point
    return x % ED25519_FIELD == 0 and (y - z) % ED25519_FIELD == 0


def _strict_ed25519_point(
    encoded: bytes, *, stage: str, label: str, allow_identity: bool
) -> tuple[int, int, int, int]:
    if len(encoded) != 32:
        raise _semantic(stage, f"{label} does not encode a 32-byte Ed25519 point")
    compressed = int.from_bytes(encoded, "little")
    x_sign = compressed >> 255
    y = compressed & ((1 << 255) - 1)
    if y >= ED25519_FIELD:
        raise _semantic(stage, f"{label} is not a canonical Ed25519 point encoding")

    y_squared = y * y % ED25519_FIELD
    numerator = (y_squared - 1) % ED25519_FIELD
    denominator = (ED25519_D * y_squared + 1) % ED25519_FIELD
    x_squared = (
        numerator * pow(denominator, ED25519_FIELD - 2, ED25519_FIELD)
    ) % ED25519_FIELD
    x = pow(x_squared, (ED25519_FIELD + 3) // 8, ED25519_FIELD)
    if (x * x - x_squared) % ED25519_FIELD:
        x = x * ED25519_SQRT_M1 % ED25519_FIELD
    if (x * x - x_squared) % ED25519_FIELD:
        raise _semantic(stage, f"{label} does not decode to an Edwards25519 point")
    if x == 0 and x_sign:
        raise _semantic(stage, f"{label} uses a noncanonical negative-zero encoding")
    if (x & 1) != x_sign:
        x = ED25519_FIELD - x

    point = (x, y, 1, x * y % ED25519_FIELD)
    identity = _ed25519_is_identity(point)
    if identity and not allow_identity:
        raise _semantic(stage, f"{label} encodes the Ed25519 identity point")
    if not _ed25519_is_identity(_ed25519_scalar_multiply(point, ED25519_ORDER)):
        raise _semantic(stage, f"{label} is not in the prime-order Ed25519 subgroup")
    return point


def _parse_document(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        document = _strict_json(raw, label=label)
    except StrictJsonError as error:
        raise _semantic("parse", str(error)) from error
    if not isinstance(document, dict):
        # The normative schema will give the externally visible classification.
        return document  # type: ignore[return-value]
    return document


def _schema_stage(
    document: JsonValue,
    *,
    schema: Mapping[str, Any],
    registry: Registry,
) -> None:
    try:
        validator = _extended_validator(schema, registry=registry)
        errors = sorted(
            validator.iter_errors(document), key=lambda item: list(item.absolute_path)
        )
    except (
        referencing_exceptions.Unresolvable,
        referencing_exceptions.NoSuchResource,
        referencing_exceptions.Unretrievable,
    ) as error:
        raise _bundle_error(
            f"normative Schema reference cannot be resolved: {error}"
        ) from error
    if errors:
        raise _semantic("schema", _format_validation_error(errors[0]))


def _signature_envelope(
    document: Mapping[str, Any], profile: Mapping[str, Any]
) -> EnvelopeResult:
    signature = document["signature"]
    protected_time = _json_pointer(
        document, profile["protectedTimePointer"], stage="signature-envelope"
    )
    created_at = signature["createdAt"]
    protected_instant = _parse_rfc3339_instant(
        protected_time,
        stage="signature-envelope",
        label="protected signed time",
    )
    _parse_rfc3339_instant(
        created_at,
        stage="signature-envelope",
        label="signature.createdAt",
    )
    if not protected_time.endswith("Z") or not created_at.endswith("Z"):
        raise _semantic(
            "signature-envelope",
            "protected time and signature.createdAt must use uppercase Z",
        )
    if protected_time != created_at:
        raise _semantic(
            "signature-envelope",
            "protected time and signature.createdAt are not byte-equal",
        )

    selector = profile["expectedSigner"]
    exact_principal: dict[str, str] | None = None
    service_principal = False
    if selector["rule"] == "principal-object":
        selected = _json_pointer(
            document, selector["pointer"], stage="signature-envelope"
        )
        if not isinstance(selected, dict):
            raise _semantic(
                "signature-envelope", "expected signer is not a Principal object"
            )
        exact_principal = dict(selected)
    elif selector["rule"] == "agent-id":
        selected = _json_pointer(
            document, selector["idPointer"], stage="signature-envelope"
        )
        if not isinstance(selected, str):
            raise _semantic(
                "signature-envelope", "expected Agent signer ID is not a string"
            )
        exact_principal = {"type": "agent", "id": selected}
    elif selector["rule"] == "service-principal":
        service_principal = True
    else:  # Profiles are trusted and checked byte-for-byte during bundle preflight.
        raise _bundle_error(f"unknown expected signer rule: {selector['rule']!r}")

    signature_bytes = _canonical_base64url(
        signature["value"], stage="signature-envelope", label="signature.value"
    )
    if len(signature_bytes) != 64:
        raise _semantic(
            "signature-envelope", "signature.value does not decode to 64 bytes"
        )
    _strict_ed25519_point(
        signature_bytes[:32],
        stage="signature-envelope",
        label="signature R",
        allow_identity=True,
    )
    signature_scalar = int.from_bytes(signature_bytes[32:], "little")
    if signature_scalar >= ED25519_ORDER:
        raise _semantic(
            "signature-envelope", "signature S is outside the Ed25519 scalar range"
        )
    return EnvelopeResult(
        protected_time=protected_time,
        protected_instant=protected_instant,
        key_id=signature["keyId"],
        signature_text=signature["value"],
        signature_bytes=signature_bytes,
        exact_principal=exact_principal,
        service_principal=service_principal,
    )


def _exact_keys(
    value: object,
    *,
    required: set[str],
    optional: set[str],
    stage: str,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise _semantic(stage, f"{label} is not an object")
    keys = set(value)
    missing = required - keys
    unknown = keys - required - optional
    if missing or unknown:
        details = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unknown " + ", ".join(sorted(unknown)))
        raise _semantic(stage, f"{label} has invalid fields ({'; '.join(details)})")
    return value


def _principal(value: object, *, stage: str, label: str) -> dict[str, str]:
    principal = _exact_keys(
        value, required={"type", "id"}, optional=set(), stage=stage, label=label
    )
    if principal["type"] not in {"agent", "human", "service"}:
        raise _semantic(stage, f"{label}.type is unsupported")
    if not isinstance(principal["id"], str):
        raise _semantic(stage, f"{label}.id is not a string")
    if not _is_protocol_uri(principal["id"]):
        raise _semantic(stage, f"{label}.id is not a protocol URI")
    return {"type": principal["type"], "id": principal["id"]}


def _positive_integer(value: object, *, stage: str, label: str) -> int:
    if not _is_json_integer(None, value):
        raise _semantic(stage, f"{label} is not an integer")
    if isinstance(value, ExtremeJsonNumber):
        raise _semantic(stage, f"{label} is outside the positive safe-integer range")
    try:
        integer = int(value)  # type: ignore[arg-type]
    except (OverflowError, TypeError, ValueError) as error:
        raise _semantic(
            stage, f"{label} is outside the positive safe-integer range"
        ) from error
    if integer < 1 or integer > 9007199254740991:
        raise _semantic(stage, f"{label} is outside the positive safe-integer range")
    return integer


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


def _validate_fixture_structures(
    manifest: Mapping[str, Any], cache: Mapping[str, bytes]
) -> None:
    fixture_schema_ids = {
        "registry": REGISTRY_FIXTURE_SCHEMA_ID,
        "signingKey": SIGNING_KEY_FIXTURE_SCHEMA_ID,
    }
    fixture_schemas: dict[str, Mapping[str, Any]] = {}
    for fixture_kind, path in manifest["fixtureSchemas"].items():
        schema = _parse_cached_json(cache, path, label=f"{fixture_kind} fixture Schema")
        if not isinstance(schema, dict):
            raise _bundle_error(f"{fixture_kind} fixture Schema is not an object")
        if schema.get("$id") != fixture_schema_ids[fixture_kind]:
            raise _bundle_error(f"{fixture_kind} fixture Schema has the wrong $id")
        try:
            validator_for(schema).check_schema(schema)
        except Exception as error:
            raise _bundle_error(
                f"invalid {fixture_kind} fixture Schema: {error}"
            ) from error
        fixture_schemas[fixture_kind] = schema

    registry_paths: set[str] = set()
    signing_key_paths: set[str] = set()
    for case in manifest["cases"]:
        if case["kind"] == "canonicalization":
            continue
        for evaluation in case["evaluations"]:
            registry_paths.add(evaluation["registry"])
            signing_key = evaluation.get("signingKey")
            if signing_key is not None:
                signing_key_paths.add(signing_key)

    for path in sorted(registry_paths):
        try:
            document = _strict_json(cache[path], label=path)
            _validate_instance(
                document,
                fixture_schemas["registry"],
                label=f"Registry fixture {path}",
            )
            registry = _exact_keys(
                document,
                required={"organizationId", "bindings"},
                optional=set(),
                stage="key-resolution",
                label=path,
            )
            if not isinstance(registry["organizationId"], str):
                raise _semantic(
                    "key-resolution", f"{path}.organizationId is not a string"
                )
            if not isinstance(registry["bindings"], list) or not registry["bindings"]:
                raise _semantic(
                    "key-resolution", f"{path}.bindings is not a non-empty array"
                )
            for binding_index, raw_binding in enumerate(registry["bindings"]):
                prefix = f"{path}.bindings[{binding_index}]"
                binding = _exact_keys(
                    raw_binding,
                    required={
                        "keyId",
                        "principal",
                        "algorithm",
                        "publicKey",
                        "validFrom",
                        "validityHistory",
                    },
                    optional=set(),
                    stage="key-resolution",
                    label=prefix,
                )
                for field in ("keyId", "algorithm", "publicKey", "validFrom"):
                    if not isinstance(binding[field], str):
                        raise _semantic(
                            "key-resolution", f"{prefix}.{field} is not a string"
                        )
                principal = _exact_keys(
                    binding["principal"],
                    required={"type", "id"},
                    optional=set(),
                    stage="key-resolution",
                    label=f"{prefix}.principal",
                )
                if not isinstance(principal["type"], str) or not isinstance(
                    principal["id"], str
                ):
                    raise _semantic(
                        "key-resolution", f"{prefix}.principal fields are not strings"
                    )
                history = binding["validityHistory"]
                if not isinstance(history, list):
                    raise _semantic(
                        "key-resolution", f"{prefix}.validityHistory is not an array"
                    )
                for status_index, raw_status in enumerate(history):
                    status_label = f"{prefix}.validityHistory[{status_index}]"
                    status_record = _exact_keys(
                        raw_status,
                        required={"sequence", "recordedAt"},
                        optional={"validUntil", "revokedAt"},
                        stage="key-resolution",
                        label=status_label,
                    )
                    _positive_integer(
                        status_record["sequence"],
                        stage="key-resolution",
                        label=f"{status_label}.sequence",
                    )
                    for field in ("recordedAt", "validUntil", "revokedAt"):
                        if field in status_record and not isinstance(
                            status_record[field], str
                        ):
                            raise _semantic(
                                "key-resolution",
                                f"{status_label}.{field} is not a string",
                            )
        except StrictJsonError as error:
            raise _bundle_error(f"invalid Registry fixture: {error}") from error
        except SemanticFailure as error:
            raise _bundle_error(
                f"invalid Registry fixture structure: {error.detail}"
            ) from error

    for path in sorted(signing_key_paths):
        try:
            document = _strict_json(cache[path], label=path)
            _validate_instance(
                document,
                fixture_schemas["signingKey"],
                label=f"signing-key fixture {path}",
            )
            signing_key = _exact_keys(
                document,
                required={"testOnly", "keyId", "algorithm", "seed", "publicKey"},
                optional=set(),
                stage="key-resolution",
                label=path,
            )
            if signing_key["testOnly"] is not True:
                raise _semantic("key-resolution", f"{path}.testOnly is not true")
            for field in ("keyId", "algorithm", "seed", "publicKey"):
                if not isinstance(signing_key[field], str):
                    raise _semantic("key-resolution", f"{path}.{field} is not a string")
        except StrictJsonError as error:
            raise _bundle_error(f"invalid signing-key fixture: {error}") from error
        except SemanticFailure as error:
            raise _bundle_error(
                f"invalid signing-key fixture structure: {error.detail}"
            ) from error


def _resolve_key(raw: bytes, envelope: EnvelopeResult, *, label: str) -> ResolvedKey:
    try:
        registry_document = _strict_json(raw, label=label)
    except StrictJsonError as error:
        raise _semantic("key-resolution", str(error)) from error
    registry_object = _exact_keys(
        registry_document,
        required={"organizationId", "bindings"},
        optional=set(),
        stage="key-resolution",
        label="Registry fixture",
    )
    if not isinstance(registry_object["organizationId"], str):
        raise _semantic("key-resolution", "Registry organizationId is not a string")
    organization_id = registry_object["organizationId"]
    if not _is_protocol_uri(organization_id):
        raise _semantic(
            "key-resolution", "Registry organizationId is not a protocol URI"
        )
    if (
        not isinstance(registry_object["bindings"], list)
        or not registry_object["bindings"]
    ):
        raise _semantic("key-resolution", "Registry bindings is not a non-empty array")

    normalized: dict[str, dict[str, Any]] = {}
    public_key_owners: dict[bytes, tuple[str, str, str]] = {}
    tuple_ids: dict[tuple[str, str, str, bytes], str] = {}
    for binding_index, raw_binding in enumerate(registry_object["bindings"]):
        prefix = f"Registry bindings[{binding_index}]"
        binding = _exact_keys(
            raw_binding,
            required={
                "keyId",
                "principal",
                "algorithm",
                "publicKey",
                "validFrom",
                "validityHistory",
            },
            optional=set(),
            stage="key-resolution",
            label=prefix,
        )
        key_id = binding["keyId"]
        if not isinstance(key_id, str):
            raise _semantic("key-resolution", f"{prefix}.keyId is not a string")
        if not _is_protocol_uri(key_id):
            raise _semantic(
                "key-resolution", f"{prefix}.keyId is not a protocol URI"
            )
        principal = _principal(
            binding["principal"], stage="key-resolution", label=f"{prefix}.principal"
        )
        if binding["algorithm"] != "Ed25519":
            raise _semantic("key-resolution", f"{prefix}.algorithm is not Ed25519")
        public_key_text = binding["publicKey"]
        public_key_bytes = _canonical_base64url(
            public_key_text, stage="key-resolution", label=f"{prefix}.publicKey"
        )
        if len(public_key_bytes) != 32:
            raise _semantic(
                "key-resolution", f"{prefix}.publicKey does not decode to 32 bytes"
            )
        _strict_ed25519_point(
            public_key_bytes,
            stage="key-resolution",
            label=f"{prefix}.publicKey",
            allow_identity=False,
        )
        valid_from = _parse_rfc3339_instant(
            binding["validFrom"], stage="key-resolution", label=f"{prefix}.validFrom"
        )
        history = binding["validityHistory"]
        if not isinstance(history, list):
            raise _semantic(
                "key-resolution", f"{prefix}.validityHistory is not an array"
            )

        immutable = (principal["type"], principal["id"], "Ed25519", public_key_bytes)
        existing = normalized.get(key_id)
        if existing is not None:
            if (
                existing["immutable"] != immutable
                or existing["validFrom"] != valid_from
            ):
                raise _semantic(
                    "key-resolution",
                    f"key ID {key_id!r} is reused for another immutable binding",
                )
        else:
            normalized[key_id] = {
                "immutable": immutable,
                "principal": principal,
                "algorithm": "Ed25519",
                "publicKey": public_key_text,
                "publicKeyBytes": public_key_bytes,
                "validFrom": valid_from,
                "history": {},
            }
            existing = normalized[key_id]

        owner = public_key_owners.get(public_key_bytes)
        owner_tuple = (key_id, principal["type"], principal["id"])
        if owner is not None and owner != owner_tuple:
            raise _semantic(
                "key-resolution",
                "the same public key is registered under another Principal or key ID",
            )
        public_key_owners[public_key_bytes] = owner_tuple
        principal_key = (
            principal["type"],
            principal["id"],
            "Ed25519",
            public_key_bytes,
        )
        alias = tuple_ids.get(principal_key)
        if alias is not None and alias != key_id:
            raise _semantic(
                "key-resolution",
                "a Principal, algorithm, and public-key tuple has a key-ID alias",
            )
        tuple_ids[principal_key] = key_id

        for history_index, raw_status in enumerate(history):
            status_label = f"{prefix}.validityHistory[{history_index}]"
            status = _exact_keys(
                raw_status,
                required={"sequence", "recordedAt"},
                optional={"validUntil", "revokedAt"},
                stage="key-resolution",
                label=status_label,
            )
            sequence = _positive_integer(
                status["sequence"],
                stage="key-resolution",
                label=f"{status_label}.sequence",
            )
            normalized_status: dict[str, Any] = {
                "sequence": sequence,
                "recordedAt": _parse_rfc3339_instant(
                    status["recordedAt"],
                    stage="key-resolution",
                    label=f"{status_label}.recordedAt",
                ),
            }
            for boundary in ("validUntil", "revokedAt"):
                if boundary in status:
                    normalized_status[boundary] = _parse_rfc3339_instant(
                        status[boundary],
                        stage="key-resolution",
                        label=f"{status_label}.{boundary}",
                    )
            previous = existing["history"].get(sequence)
            if previous is not None and previous != normalized_status:
                raise _semantic(
                    "key-resolution",
                    f"{status_label} rewrites an earlier status sequence",
                )
            existing["history"][sequence] = normalized_status

    for key_id, binding in normalized.items():
        statuses = [binding["history"][number] for number in sorted(binding["history"])]
        sequences = [status["sequence"] for status in statuses]
        if sequences != list(range(1, len(sequences) + 1)):
            raise _semantic(
                "key-resolution",
                f"key {key_id!r} validity history is not contiguous from sequence 1",
            )
        recorded_at: Rfc3339Instant | None = None
        effective_until: Rfc3339Instant | None = None
        effective_revoked: Rfc3339Instant | None = None
        for status_record in statuses:
            if recorded_at is not None and status_record["recordedAt"] < recorded_at:
                raise _semantic(
                    "key-resolution",
                    f"key {key_id!r} validity history is not append ordered",
                )
            recorded_at = status_record["recordedAt"]
            for field, current in (
                ("validUntil", effective_until),
                ("revokedAt", effective_revoked),
            ):
                if field not in status_record:
                    continue
                candidate = status_record[field]
                if current is not None and candidate > current:
                    raise _semantic(
                        "key-resolution",
                        f"key {key_id!r} moves {field} later in history",
                    )
                if field == "validUntil":
                    effective_until = candidate
                else:
                    effective_revoked = candidate
        binding["validUntil"] = effective_until
        binding["revokedAt"] = effective_revoked

    selected = normalized.get(envelope.key_id)
    if selected is None:
        raise _semantic("key-resolution", "signature.keyId is unknown")
    principal = selected["principal"]
    if envelope.service_principal:
        if principal["type"] != "service":
            raise _semantic(
                "key-resolution", "Agent Card signer is not a service Principal"
            )
    elif principal != envelope.exact_principal:
        raise _semantic(
            "key-resolution", "resolved key is bound to the wrong Principal"
        )

    protected = envelope.protected_instant
    if protected < selected["validFrom"]:
        raise _semantic(
            "key-resolution", "signing key is not yet valid at the protected time"
        )
    if selected["validUntil"] is not None and protected >= selected["validUntil"]:
        raise _semantic(
            "key-resolution", "signing key is expired at the protected time"
        )
    if selected["revokedAt"] is not None and protected >= selected["revokedAt"]:
        raise _semantic(
            "key-resolution", "signing key is revoked at the protected time"
        )
    return ResolvedKey(
        organization_id=organization_id,
        key_id=envelope.key_id,
        principal=principal,
        algorithm=selected["algorithm"],
        public_key_text=selected["publicKey"],
        public_key_bytes=selected["publicKeyBytes"],
        valid_from=selected["validFrom"],
        valid_until=selected["validUntil"],
        revoked_at=selected["revokedAt"],
    )


def _canonicalization_stage(document: Mapping[str, Any]) -> tuple[bytes, str]:
    unsigned = dict(document)
    unsigned.pop("signature", None)
    try:
        signing_bytes = _jcs_bytes(unsigned)
    except (
        rfc8785.CanonicalizationError,
        UnicodeError,
        ValueError,
        OverflowError,
    ) as error:
        raise _semantic(
            "canonicalization", f"document is outside the JCS/I-JSON domain: {error}"
        ) from error
    return signing_bytes, _sha256(signing_bytes)


def _signature_stage(
    signing_bytes: bytes, envelope: EnvelopeResult, key: ResolvedKey
) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(key.public_key_bytes).verify(
            envelope.signature_bytes, signing_bytes
        )
    except InvalidSignature as error:
        raise _semantic("signature", "Ed25519 signature does not verify") from error


def _validate_signing_key(
    raw: bytes,
    *,
    result: VerifiedResult,
    label: str,
) -> None:
    try:
        document = _strict_json(raw, label=label)
    except StrictJsonError as error:
        raise _bundle_error(str(error)) from error
    if not isinstance(document, dict) or set(document) != {
        "testOnly",
        "keyId",
        "algorithm",
        "seed",
        "publicKey",
    }:
        raise _bundle_error(f"{label} is not an exact test-only signing-key fixture")
    if document["testOnly"] is not True:
        raise _bundle_error(f"{label} must declare testOnly: true")
    if document["keyId"] != result.key.key_id or document["algorithm"] != "Ed25519":
        raise _bundle_error(f"{label} does not identify the verified Ed25519 key")
    try:
        seed = _canonical_base64url(
            document["seed"], stage="key-resolution", label=f"{label}.seed"
        )
        fixture_public = _canonical_base64url(
            document["publicKey"], stage="key-resolution", label=f"{label}.publicKey"
        )
    except SemanticFailure as error:
        raise _bundle_error(error.detail) from error
    if len(seed) != 32 or len(fixture_public) != 32:
        raise _bundle_error(f"{label} seed and publicKey must each decode to 32 bytes")
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    derived_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if (
        derived_public != fixture_public
        or fixture_public != result.key.public_key_bytes
    ):
        raise _bundle_error(f"{label} seed, public key, and Registry binding disagree")
    if private_key.sign(result.signing_bytes) != result.envelope.signature_bytes:
        raise _bundle_error(f"{label} does not reproduce the document signature")


def _compare_verified(
    expected: Mapping[str, Any],
    *,
    result: VerifiedResult,
    cache: Mapping[str, bytes],
    case_id: str,
) -> None:
    actual_scalars = {
        "keyId": result.key.key_id,
        "principal": result.key.principal,
        "protectedTime": result.envelope.protected_time,
        "signingHash": result.signing_hash,
        "signature": result.envelope.signature_text,
    }
    for field, actual in actual_scalars.items():
        if expected[field] != actual:
            raise _bundle_error(
                f"case {case_id!r} verified.{field} mismatch: expected {expected[field]!r}, "
                f"got {actual!r}"
            )
    expected_signing_bytes = cache[expected["signingBytes"]]
    if expected_signing_bytes != result.signing_bytes:
        raise _bundle_error(
            f"case {case_id!r} signing bytes differ from expected artifact"
        )
    try:
        signed_document_bytes = _jcs_bytes(result.document)
    except (
        rfc8785.CanonicalizationError,
        UnicodeError,
        ValueError,
        OverflowError,
    ) as error:
        raise _bundle_error(
            f"case {case_id!r} complete document cannot be canonicalized: {error}"
        ) from error
    signed_document_hash = _sha256(signed_document_bytes)
    if expected["signedDocumentHash"] != signed_document_hash:
        raise _bundle_error(
            f"case {case_id!r} signedDocumentHash mismatch: expected "
            f"{expected['signedDocumentHash']}, got {signed_document_hash}"
        )


def _run_signed_evaluation(
    evaluation: Mapping[str, Any],
    *,
    case_id: str,
    profiles: Mapping[str, Mapping[str, Any]],
    schemas: Mapping[str, Mapping[str, Any]],
    schema_registry: Registry,
    cache: Mapping[str, bytes],
) -> bool:
    expected = evaluation["expect"]
    expected_stage = expected["stage"]
    expected_wire = expected["wireCode"]
    profile = profiles[evaluation["profileId"]]
    try:
        document = _parse_document(
            cache[evaluation["document"]], label=evaluation["document"]
        )
        _schema_stage(
            document, schema=schemas[profile["schema"]], registry=schema_registry
        )
        envelope = _signature_envelope(document, profile)
        key = _resolve_key(
            cache[evaluation["registry"]], envelope, label=evaluation["registry"]
        )
        signing_bytes, signing_hash = _canonicalization_stage(document)
        _signature_stage(signing_bytes, envelope, key)
    except SemanticFailure as failure:
        if expected_stage == "complete":
            raise _bundle_error(
                f"case {case_id!r} expected complete but failed at {failure.stage}: "
                f"{failure.detail}"
            ) from failure
        if failure.stage != expected_stage:
            raise _bundle_error(
                f"case {case_id!r} expected stage {expected_stage!r} but first failed at "
                f"{failure.stage!r}: {failure.detail}"
            ) from failure
        if failure.wire_code != expected_wire:
            raise _bundle_error(
                f"case {case_id!r} expected wireCode {expected_wire!r} but produced "
                f"{failure.wire_code!r}"
            ) from failure
        return False

    if expected_stage != "complete":
        raise _bundle_error(
            f"case {case_id!r} expected failure at {expected_stage!r} but verification completed"
        )
    result = VerifiedResult(
        document=document,
        envelope=envelope,
        key=key,
        signing_bytes=signing_bytes,
        signing_hash=signing_hash,
    )
    _validate_signing_key(
        cache[evaluation["signingKey"]],
        result=result,
        label=evaluation["signingKey"],
    )
    _compare_verified(expected["verified"], result=result, cache=cache, case_id=case_id)
    return True


def _run_canonicalization_case(
    case: Mapping[str, Any], *, cache: Mapping[str, bytes]
) -> None:
    evaluation = case["evaluations"][0]
    try:
        value = _strict_json(cache[evaluation["input"]], label=evaluation["input"])
    except StrictJsonError as error:
        raise _bundle_error(
            f"canonicalization case {case['id']!r} input is invalid: {error}"
        ) from error
    try:
        actual = _jcs_bytes(value)
    except (
        rfc8785.CanonicalizationError,
        UnicodeError,
        ValueError,
        OverflowError,
    ) as error:
        raise _bundle_error(
            f"canonicalization case {case['id']!r} cannot produce JCS: {error}"
        ) from error
    expected = cache[evaluation["expectedJcs"]]
    if actual != expected:
        raise _bundle_error(
            f"canonicalization case {case['id']!r} differs from its expected JCS artifact"
        )
    actual_hash = _sha256(actual)
    if actual_hash != evaluation["sha256"]:
        raise _bundle_error(
            f"canonicalization case {case['id']!r} hash mismatch: expected "
            f"{evaluation['sha256']}, got {actual_hash}"
        )


def _run_cases(
    manifest: Mapping[str, Any],
    *,
    cache: Mapping[str, bytes],
    schemas: Mapping[str, Mapping[str, Any]],
    schema_registry: Registry,
) -> None:
    profiles = {profile["profileId"]: profile for profile in manifest["profiles"]}
    completed = 0
    rejected = 0
    evaluations = 0
    for case in manifest["cases"]:
        if case["kind"] == "canonicalization":
            _run_canonicalization_case(case, cache=cache)
            completed += 1
            evaluations += 1
            continue
        for evaluation in case["evaluations"]:
            evaluations += 1
            if _run_signed_evaluation(
                evaluation,
                case_id=case["id"],
                profiles=profiles,
                schemas=schemas,
                schema_registry=schema_registry,
                cache=cache,
            ):
                completed += 1
            else:
                rejected += 1
    if (evaluations, completed, rejected) != (62, 12, 50):
        raise _bundle_error(
            f"runner count mismatch: got {evaluations} evaluations, {completed} complete, "
            f"and {rejected} rejected"
        )
    print(
        "Validated 9 signed-document profiles, 22 cases, 62 evaluations, "
        f"12 complete and 50 rejected; artifact digest {manifest['artifactDigest']}."
    )


def _load_and_validate_bundle() -> tuple[
    Mapping[str, Any],
    dict[str, bytes],
    dict[str, Mapping[str, Any]],
    Registry,
]:
    _validate_protocol_uri_contract()
    manifest_schema = _load_fixed_json(
        MANIFEST_SCHEMA_PATH, label="cryptography/manifest.schema.json"
    )
    if not isinstance(manifest_schema, dict):
        raise _bundle_error("cryptography/manifest.schema.json is not an object")
    if manifest_schema.get("$id") != MANIFEST_SCHEMA_ID:
        raise _bundle_error("cryptography manifest Schema has the wrong $id")
    try:
        validator_for(manifest_schema).check_schema(manifest_schema)
    except Exception as error:
        raise _bundle_error(f"invalid cryptography manifest Schema: {error}") from error

    manifest = _load_fixed_json(MANIFEST_PATH, label="cryptography/manifest.json")
    if not isinstance(manifest, dict):
        raise _bundle_error("cryptography manifest is not an object")
    _validate_instance(manifest, manifest_schema, label="cryptography manifest")
    if manifest["manifestVersion"] != 1 or manifest["protocolVersion"] != "0.1":
        raise _bundle_error("manifest version constants do not identify protocol 0.1")
    if manifest["profileId"] != PROFILE_ID:
        raise _bundle_error(
            "manifest profileId is not the v0.1 Signed Document profile"
        )
    if tuple(manifest["semanticStages"]) != SEMANTIC_STAGES:
        raise _bundle_error(
            "manifest semanticStages are not the normative ordered stages"
        )
    if manifest["fixtureSchemas"] != EXPECTED_FIXTURE_SCHEMAS:
        raise _bundle_error(
            "manifest fixtureSchemas are not the v0.1 fixture contracts"
        )

    cache = _read_artifacts(manifest)
    try:
        cached_manifest_schema = _strict_json(
            cache["cryptography/manifest.schema.json"],
            label="cryptography/manifest.schema.json",
            preserve_numbers=False,
        )
    except StrictJsonError as error:
        raise _bundle_error(str(error)) from error
    if cached_manifest_schema != manifest_schema:
        raise _bundle_error(
            "manifest Schema changed while the artifact cache was being built"
        )
    _validate_artifact_digest(manifest)
    _artifact_references(manifest, cache)
    schemas, schema_registry = _validate_profiles(manifest, cache)
    _validate_case_matrix(manifest)
    _validate_timestamp_profile_coverage(manifest, cache)
    _validate_registry_identifier_faults(manifest, cache)
    _validate_fixture_structures(manifest, cache)
    return manifest, cache, schemas, schema_registry


def main() -> int:
    try:
        manifest, cache, schemas, schema_registry = _load_and_validate_bundle()
        _run_cases(
            manifest,
            cache=cache,
            schemas=schemas,
            schema_registry=schema_registry,
        )
    except BundleValidationError as error:
        print(f"Cryptography vector validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
