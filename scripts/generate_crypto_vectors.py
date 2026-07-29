#!/usr/bin/env python3
"""Generate deterministic MissionWeaveProtocol v0.1 cryptography vectors.

The committed files under ``cryptography/keys`` and ``cryptography/vectors``
are generated artifacts.  This script intentionally has no third-party runtime
dependency so the golden Ed25519/JCS values can be reproduced during review.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CRYPTO_ROOT = ROOT / "cryptography"
KEY_ROOT = CRYPTO_ROOT / "keys"
VECTOR_ROOT = CRYPTO_ROOT / "vectors"
CANONICAL_ROOT = VECTOR_ROOT / "canonicalization"
VALID_ROOT = VECTOR_ROOT / "signed-documents" / "valid"
INVALID_ROOT = VECTOR_ROOT / "signed-documents" / "invalid"
MANIFEST_PATH = CRYPTO_ROOT / "manifest.json"

PROFILE_ID = "missionweaveprotocol.signed-document-verification.v0.1"
ORGANIZATION_ID = "urn:missionweaveprotocol:organization:acme"
GOLDEN_KEY_ID = "urn:missionweaveprotocol:key:crypto-vector-rfc8032-1"
GOLDEN_SEED = "nWGxne_9WmC6hEr0kuwsxERJxWl7MmkZcDusAxyuf2A"
GOLDEN_PUBLIC_KEY = "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"
GOLDEN_SIGNING_HASH = (
    "sha256:6655c5d67ae3ecc19a4ed04bda7f1372aeaafc7adf939a77715de96ef2100695"
)
GOLDEN_SIGNATURE = (
    "PMeeKgpw-HlGNwHbQbEMrfAxbw1815fBdFhOSTHy31ss90eTcuQ4rWeRZbmqFFtH"
    "gLKzd0gNm67-HenzwGVhAg"
)
GOLDEN_DOCUMENT_HASH = (
    "sha256:1d17d0bd5379e554d48d14a6b328671f12860c6c3278bc1e7ca4e1163a74353f"
)


# Minimal, deterministic Ed25519 implementation derived from RFC 8032's
# formulas.  It is used only for public test fixtures.
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _x_recover(y: int) -> int:
    xx = (y * y - 1) * pow(_D * y * y + 1, _Q - 2, _Q) % _Q
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q:
        x = x * _I % _Q
    if x & 1:
        x = _Q - x
    return x


_BASE_Y = 4 * pow(5, _Q - 2, _Q) % _Q
_BASE_X = _x_recover(_BASE_Y)
_BASE = (_BASE_X, _BASE_Y, 1, _BASE_X * _BASE_Y % _Q)
_IDENTITY = (0, 1, 1, 0)


def _point_add(
    left: tuple[int, int, int, int], right: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = left
    x2, y2, z2, t2 = right
    a = (y1 - x1) * (y2 - x2) % _Q
    b = (y1 + x1) * (y2 + x2) % _Q
    c = 2 * _D * t1 * t2 % _Q
    d = 2 * z1 * z2 % _Q
    e = (b - a) % _Q
    f = (d - c) % _Q
    g = (d + c) % _Q
    h = (b + a) % _Q
    return e * f % _Q, g * h % _Q, f * g % _Q, e * h % _Q


def _scalar_multiply(
    point: tuple[int, int, int, int], scalar: int
) -> tuple[int, int, int, int]:
    result = _IDENTITY
    addend = point
    while scalar:
        if scalar & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        scalar >>= 1
    return result


def _encode_point(point: tuple[int, int, int, int]) -> bytes:
    x, y, z, _ = point
    inverse_z = pow(z, _Q - 2, _Q)
    affine_x = x * inverse_z % _Q
    affine_y = y * inverse_z % _Q
    return (affine_y | ((affine_x & 1) << 255)).to_bytes(32, "little")


def _secret_scalar(seed: bytes) -> tuple[int, bytes]:
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def _ed25519_public_key(seed: bytes) -> bytes:
    scalar, _ = _secret_scalar(seed)
    return _encode_point(_scalar_multiply(_BASE, scalar))


def _ed25519_sign(message: bytes, seed: bytes, public_key: bytes) -> bytes:
    scalar, prefix = _secret_scalar(seed)
    nonce = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _L
    encoded_r = _encode_point(_scalar_multiply(_BASE, nonce))
    challenge = (
        int.from_bytes(
            hashlib.sha512(encoded_r + public_key + message).digest(), "little"
        )
        % _L
    )
    encoded_s = ((nonce + challenge * scalar) % _L).to_bytes(32, "little")
    return encoded_r + encoded_s


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _with_nonzero_unused_pad_bits(value: str) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    final_value = alphabet.index(value[-1])
    unused_bit_count = (4 - (len(value) % 4)) % 4 * 2
    if unused_bit_count == 0:
        raise ValueError("base64url value has no unused pad bits")
    unused_mask = (1 << unused_bit_count) - 1
    if final_value & unused_mask:
        raise ValueError("base64url value already has nonzero unused pad bits")
    return value[:-1] + alphabet[final_value + 1]


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _serialize_number(value: int | float) -> str:
    if isinstance(value, bool):
        raise TypeError("booleans are not numbers")
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        raise ValueError("JCS requires a finite IEEE 754 binary64 number")
    if value == 0:
        return "0"

    # The generated signed fixtures use only the binary64 spellings covered
    # here: integral values, 1e+30, and 1e-7.  The RFC 8785 general-purpose
    # number example is committed verbatim below and checked independently.
    rendered = repr(value).lower()
    if "e" not in rendered:
        return rendered
    significand, exponent = rendered.split("e", 1)
    sign = ""
    if exponent.startswith(("+", "-")):
        sign, exponent = exponent[0], exponent[1:]
    exponent = exponent.lstrip("0") or "0"
    return f"{significand}e{sign}{exponent}"


def _jcs(value: Any) -> bytes:
    def utf16_sort_key(member_name: str) -> bytes:
        return member_name.encode("utf-16-be")

    def serialize(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, (int, float)):
            return _serialize_number(item)
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, list):
            return "[" + ",".join(serialize(entry) for entry in item) + "]"
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise TypeError("JCS object keys must be strings")
            members = []
            for key in sorted(item, key=utf16_sort_key):
                members.append(
                    json.dumps(key, ensure_ascii=False, separators=(",", ":"))
                    + ":"
                    + serialize(item[key])
                )
            return "{" + ",".join(members) + "}"
        raise TypeError(f"unsupported JCS value: {type(item).__name__}")

    return serialize(value).encode("utf-8")


def _write_bytes(relative: str, content: bytes) -> str:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return relative


def _write_json(relative: str, document: Any) -> str:
    content = (
        json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    return _write_bytes(relative, content)


def _read_conformance_fixture(name: str) -> dict[str, Any]:
    path = ROOT / "conformance" / "vectors" / "valid" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _test_key(
    label: str, key_id: str, principal: dict[str, str], seed: bytes
) -> dict[str, Any]:
    public_key = _ed25519_public_key(seed)
    return {
        "label": label,
        "keyId": key_id,
        "principal": principal,
        "seedBytes": seed,
        "seed": _b64url(seed),
        "publicKeyBytes": public_key,
        "publicKey": _b64url(public_key),
    }


def _make_keys() -> dict[str, dict[str, Any]]:
    definitions = [
        (
            "organization-registry",
            "urn:missionweaveprotocol:key:crypto-vector-organization-registry",
            {
                "type": "service",
                "id": "urn:missionweaveprotocol:service:organization-registry",
            },
            None,
        ),
        (
            "mission-owner",
            "urn:missionweaveprotocol:key:crypto-vector-mission-owner",
            {"type": "human", "id": "urn:missionweaveprotocol:human:mission-owner"},
            None,
        ),
        (
            "developer-one",
            "urn:missionweaveprotocol:key:crypto-vector-developer-one",
            {"type": "agent", "id": "urn:missionweaveprotocol:agent:developer-one"},
            None,
        ),
        (
            "coordinator",
            GOLDEN_KEY_ID,
            {
                "type": "agent",
                "id": "urn:missionweaveprotocol:agent:crypto-vector-coordinator",
            },
            _b64url_decode(GOLDEN_SEED),
        ),
        (
            "group-authority",
            "urn:missionweaveprotocol:key:crypto-vector-group-authority",
            {
                "type": "service",
                "id": "urn:missionweaveprotocol:service:group-authority",
            },
            None,
        ),
        (
            "test-reviewer",
            "urn:missionweaveprotocol:key:crypto-vector-test-reviewer",
            {"type": "agent", "id": "urn:missionweaveprotocol:agent:test-reviewer"},
            None,
        ),
        (
            "security-owner",
            "urn:missionweaveprotocol:key:crypto-vector-security-owner",
            {"type": "human", "id": "urn:missionweaveprotocol:human:security-owner"},
            None,
        ),
    ]

    keys: dict[str, dict[str, Any]] = {}
    for label, key_id, principal, seed in definitions:
        if seed is None:
            seed = hashlib.sha256(
                f"MissionWeaveProtocol 0.1 cryptography vector key: {label}".encode()
            ).digest()
        keys[label] = _test_key(label, key_id, principal, seed)
    if keys["coordinator"]["publicKey"] != GOLDEN_PUBLIC_KEY:
        raise RuntimeError("the RFC 8032 coordinator public key changed")
    return keys


def _public_key_fixture(key: dict[str, Any]) -> dict[str, Any]:
    return {
        "testOnly": True,
        "keyId": key["keyId"],
        "algorithm": "Ed25519",
        "seed": key["seed"],
        "publicKey": key["publicKey"],
    }


def _binding(
    key: dict[str, Any], *, valid_from: str = "2026-07-01T00:00:00Z"
) -> dict[str, Any]:
    return {
        "keyId": key["keyId"],
        "principal": copy.deepcopy(key["principal"]),
        "algorithm": "Ed25519",
        "publicKey": key["publicKey"],
        "validFrom": valid_from,
        "validityHistory": [],
    }


def _make_registry(keys: dict[str, dict[str, Any]]) -> dict[str, Any]:
    bindings = []
    for label in sorted(keys):
        key = keys[label]
        if label == "coordinator":
            binding = _binding(key, valid_from="2026-07-15T08:00:00+08:00")
            binding["validityHistory"] = [
                {
                    "sequence": 1,
                    "recordedAt": "2026-07-16T00:00:00Z",
                    "validUntil": "2026-07-16T00:00:00Z",
                }
            ]
        else:
            binding = _binding(key)
        bindings.append(binding)
    return {"organizationId": ORGANIZATION_ID, "bindings": bindings}


def _find_binding(registry: dict[str, Any], key_id: str) -> dict[str, Any]:
    matches = [entry for entry in registry["bindings"] if entry["keyId"] == key_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one binding for {key_id}, found {len(matches)}")
    return matches[0]


def _sign_document(
    unsigned_document: dict[str, Any], key: dict[str, Any], protected_time: str
) -> tuple[dict[str, Any], bytes]:
    signing_bytes = _jcs(unsigned_document)
    signature = _ed25519_sign(signing_bytes, key["seedBytes"], key["publicKeyBytes"])
    signed = copy.deepcopy(unsigned_document)
    signed["signature"] = {
        "algorithm": "Ed25519",
        "keyId": key["keyId"],
        "createdAt": protected_time,
        "value": _b64url(signature),
    }
    return signed, signing_bytes


def _golden_unsigned_command() -> dict[str, Any]:
    return {
        "protocolVersion": "0.1",
        "actionId": "urn:uuid:11111111-2222-4333-8444-555555555555",
        "actor": {
            "type": "agent",
            "id": "urn:missionweaveprotocol:agent:crypto-vector-coordinator",
        },
        "sessionEpoch": 7,
        "membershipEpoch": 3,
        "coordinatorEpoch": 4,
        "groupId": "urn:missionweaveprotocol:group:crypto-vector",
        "conversationId": "urn:missionweaveprotocol:conversation:crypto-review",
        "workItemId": "urn:missionweaveprotocol:work-item:crypto-review",
        "kind": "mission.submit_for_approval",
        "expectedRevision": 42,
        "correlationId": "urn:uuid:aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        "causedByEventId": "urn:uuid:99999999-8888-4777-8666-555555555555",
        "issuedAt": "2026-07-15T00:00:00Z",
        "payload": {
            "artifactHashes": ["sha256:" + "a" * 64],
            "signature": "payload-signature-must-be-covered",
        },
        "extensions": {
            "urn:missionweaveprotocol:extension:crypto-vector": {
                "version": "1.0.0",
                "critical": False,
                "data": {
                    "array": [3, 2, 1],
                    "enabled": True,
                    "large": 1e30,
                    "maxSafeInteger": 9007199254740991,
                    "negativeZero": -0.0,
                    "nested": {
                        "signature": "nested-signature-must-be-covered",
                        "text": "Résumé 東京 🚀",
                    },
                    "nothing": None,
                    "tiny": 1e-7,
                    "\ue000": "bmp-private-use",
                    "😀": "supplementary-plane",
                },
            }
        },
    }


def _prepare_unsigned_documents(
    keys: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    agent_card = _read_conformance_fixture("agent-card")
    agent_card.pop("signature")
    agent_card["publicKeys"] = [
        {
            "keyId": keys["developer-one"]["keyId"],
            "algorithm": "Ed25519",
            "publicKey": keys["developer-one"]["publicKey"],
            "validFrom": "2026-07-01T00:00:00Z",
        }
    ]

    approval = _read_conformance_fixture("approval")
    approval.pop("signature")

    artifact = _read_conformance_fixture("artifact")
    artifact.pop("signature")

    context_package = _read_conformance_fixture("context-package")
    context_package.pop("signature")
    context_package["generatedBy"] = copy.deepcopy(keys["coordinator"]["principal"])

    event = _read_conformance_fixture("event")
    event.pop("signature")

    evidence = _read_conformance_fixture("evidence")
    evidence.pop("signature")

    extension_profile = _read_conformance_fixture("extension-profile")
    extension_profile.pop("signature")

    group_snapshot = _read_conformance_fixture("group-snapshot")
    group_snapshot.pop("signature")

    return {
        "agent-card": agent_card,
        "approval": approval,
        "artifact": artifact,
        "command": _golden_unsigned_command(),
        "context-package": context_package,
        "event": event,
        "evidence": evidence,
        "extension-profile": extension_profile,
        "group-snapshot": group_snapshot,
    }


PROFILE_CONFIG = {
    "agent-card": {
        "schema": "schemas/agent-card.schema.json",
        "timePointer": "/issuedAt",
        "timeField": "issuedAt",
        "signer": {"rule": "service-principal"},
        "key": "organization-registry",
    },
    "approval": {
        "schema": "schemas/approval.schema.json",
        "timePointer": "/occurredAt",
        "timeField": "occurredAt",
        "signer": {"rule": "principal-object", "pointer": "/approver"},
        "key": "mission-owner",
    },
    "artifact": {
        "schema": "schemas/artifact.schema.json",
        "timePointer": "/createdAt",
        "timeField": "createdAt",
        "signer": {"rule": "agent-id", "idPointer": "/producer/agentId"},
        "key": "developer-one",
    },
    "command": {
        "schema": "schemas/command.schema.json",
        "timePointer": "/issuedAt",
        "timeField": "issuedAt",
        "signer": {"rule": "principal-object", "pointer": "/actor"},
        "key": "coordinator",
    },
    "context-package": {
        "schema": "schemas/context-package.schema.json",
        "timePointer": "/generatedAt",
        "timeField": "generatedAt",
        "signer": {"rule": "principal-object", "pointer": "/generatedBy"},
        "key": "coordinator",
    },
    "event": {
        "schema": "schemas/event.schema.json",
        "timePointer": "/occurredAt",
        "timeField": "occurredAt",
        "signer": {"rule": "principal-object", "pointer": "/acceptedBy"},
        "key": "group-authority",
    },
    "evidence": {
        "schema": "schemas/evidence.schema.json",
        "timePointer": "/createdAt",
        "timeField": "createdAt",
        "signer": {"rule": "principal-object", "pointer": "/generatedBy"},
        "key": "test-reviewer",
    },
    "extension-profile": {
        "schema": "schemas/extension-profile.schema.json",
        "timePointer": "/approvedAt",
        "timeField": "approvedAt",
        "signer": {"rule": "principal-object", "pointer": "/approvedBy"},
        "key": "security-owner",
    },
    "group-snapshot": {
        "schema": "schemas/group-snapshot.schema.json",
        "timePointer": "/createdAt",
        "timeField": "createdAt",
        "signer": {"rule": "principal-object", "pointer": "/createdBy"},
        "key": "group-authority",
    },
}


def _verified(
    document: dict[str, Any],
    signing_bytes_path: str,
    signing_bytes: bytes,
    key: dict[str, Any],
    protected_time: str,
) -> dict[str, Any]:
    return {
        "keyId": key["keyId"],
        "principal": copy.deepcopy(key["principal"]),
        "protectedTime": protected_time,
        "signingBytes": signing_bytes_path,
        "signingHash": _sha256(signing_bytes),
        "signature": document["signature"]["value"],
        "signedDocumentHash": _sha256(_jcs(document)),
    }


def _complete_evaluation(
    profile_id: str,
    document_path: str,
    registry_path: str,
    signing_key_path: str,
    document: dict[str, Any],
    signing_bytes_path: str,
    signing_bytes: bytes,
    key: dict[str, Any],
) -> dict[str, Any]:
    time_field = PROFILE_CONFIG[profile_id]["timeField"]
    return {
        "profileId": profile_id,
        "document": document_path,
        "registry": registry_path,
        "signingKey": signing_key_path,
        "fault": None,
        "expect": {
            "stage": "complete",
            "wireCode": None,
            "verified": _verified(
                document,
                signing_bytes_path,
                signing_bytes,
                key,
                document[time_field],
            ),
        },
    }


def _failure_evaluation(
    *,
    fault_id: str,
    document_path: str,
    registry_path: str,
    stage: str,
    wire_code: str,
    profile_id: str = "command",
    basis_case_id: str = "accept.command.golden",
    basis_profile_id: str = "command",
) -> dict[str, Any]:
    return {
        "profileId": profile_id,
        "document": document_path,
        "registry": registry_path,
        "fault": {
            "id": fault_id,
            "basis": {
                "caseId": basis_case_id,
                "profileId": basis_profile_id,
            },
        },
        "expect": {"stage": stage, "wireCode": wire_code},
    }


def _duplicate_payload_bytes(document: dict[str, Any]) -> bytes:
    members: list[str] = []
    for key, value in document.items():
        serialized = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
        serialized = serialized.replace("\n", "\n  ")
        members.append(f"  {json.dumps(key)}: {serialized}")
        if key == "payload":
            members.append(f'  "pay\\u006coad": {serialized}')
    return ("{\n" + ",\n".join(members) + "\n}\n").encode("utf-8")


def _profiles() -> list[dict[str, Any]]:
    return [
        {
            "profileId": profile_id,
            "schema": config["schema"],
            "protectedTimePointer": config["timePointer"],
            "expectedSigner": copy.deepcopy(config["signer"]),
        }
        for profile_id, config in sorted(PROFILE_CONFIG.items())
    ]


def _artifact_index() -> list[dict[str, Any]]:
    schema_paths = [
        CRYPTO_ROOT / "manifest.schema.json",
        CRYPTO_ROOT / "registry-fixture.schema.json",
        CRYPTO_ROOT / "signing-key-fixture.schema.json",
        ROOT / "schemas" / "common.schema.json",
        *[
            ROOT / PROFILE_CONFIG[profile_id]["schema"]
            for profile_id in sorted(PROFILE_CONFIG)
        ],
    ]
    paths = schema_paths + sorted(KEY_ROOT.rglob("*")) + sorted(VECTOR_ROOT.rglob("*"))
    files = sorted({path.resolve() for path in paths if path.is_file()})
    artifacts = []
    for path in files:
        content = path.read_bytes()
        artifacts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "byteLength": len(content),
                "sha256": _sha256(content),
            }
        )
    return artifacts


def generate() -> None:
    if not (CRYPTO_ROOT / "manifest.schema.json").is_file():
        raise RuntimeError(
            "cryptography/manifest.schema.json must exist before generation"
        )

    shutil.rmtree(KEY_ROOT, ignore_errors=True)
    shutil.rmtree(VECTOR_ROOT, ignore_errors=True)
    for directory in (KEY_ROOT, CANONICAL_ROOT, VALID_ROOT, INVALID_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    keys = _make_keys()
    signing_key_paths: dict[str, str] = {}
    for label, key in sorted(keys.items()):
        signing_key_paths[label] = _write_json(
            f"cryptography/keys/signing-{label}.json", _public_key_fixture(key)
        )

    registry = _make_registry(keys)
    registry_path = _write_json("cryptography/keys/registry-valid.json", registry)

    registry_organization_id_relative_reference = copy.deepcopy(registry)
    registry_organization_id_relative_reference["organizationId"] = (
        "organizations/acme"
    )
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

    registry_timestamp_casing_offsets = copy.deepcopy(registry)
    timestamp_casing_binding = _find_binding(
        registry_timestamp_casing_offsets, GOLDEN_KEY_ID
    )
    timestamp_casing_binding["validFrom"] = "2026-07-14T00:01:00-23:59"
    timestamp_casing_binding["validityHistory"][0] = {
        "sequence": 1,
        "recordedAt": "2026-07-01t00:00:00z",
        "validUntil": "2026-07-15T23:59:01+23:59",
    }
    registry_timestamp_casing_offsets_path = _write_json(
        "cryptography/keys/registry-timestamp-casing-and-offset-bounds.json",
        registry_timestamp_casing_offsets,
    )

    registry_fractional_precision = copy.deepcopy(registry)
    _find_binding(registry_fractional_precision, GOLDEN_KEY_ID)["validityHistory"][0][
        "validUntil"
    ] = "2026-07-15T00:00:00.1234560000000000002Z"
    registry_fractional_precision_path = _write_json(
        "cryptography/keys/registry-timestamp-fractional-precision.json",
        registry_fractional_precision,
    )

    registry_not_yet = copy.deepcopy(registry)
    _find_binding(registry_not_yet, GOLDEN_KEY_ID)["validFrom"] = "2026-07-15T00:00:01Z"
    registry_not_yet_path = _write_json(
        "cryptography/keys/registry-key-not-yet-valid.json", registry_not_yet
    )

    registry_valid_until = copy.deepcopy(registry)
    _find_binding(registry_valid_until, GOLDEN_KEY_ID)["validityHistory"][0][
        "validUntil"
    ] = "2026-07-15T08:00:00+08:00"
    registry_valid_until_path = _write_json(
        "cryptography/keys/registry-valid-until-equality.json", registry_valid_until
    )

    registry_revoked = copy.deepcopy(registry)
    _find_binding(registry_revoked, GOLDEN_KEY_ID)["validityHistory"].append(
        {
            "sequence": 2,
            "recordedAt": "2026-07-16T00:00:01Z",
            "revokedAt": "2026-07-15T08:00:00+08:00",
        }
    )
    registry_revoked_path = _write_json(
        "cryptography/keys/registry-revoked-at-equality.json", registry_revoked
    )

    registry_alias = copy.deepcopy(registry)
    alias_binding = copy.deepcopy(_find_binding(registry_alias, GOLDEN_KEY_ID))
    alias_key_id = "urn:missionweaveprotocol:key:crypto-vector-rfc8032-1-alias"
    alias_binding["keyId"] = alias_key_id
    registry_alias["bindings"].append(alias_binding)
    registry_alias["bindings"].sort(key=lambda entry: entry["keyId"])
    registry_alias_path = _write_json(
        "cryptography/keys/registry-key-alias.json", registry_alias
    )

    registry_short_key = copy.deepcopy(registry)
    _find_binding(registry_short_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        keys["coordinator"]["publicKeyBytes"][:31]
    )
    registry_short_key_path = _write_json(
        "cryptography/keys/registry-public-key-wrong-length.json", registry_short_key
    )

    registry_padded_key = copy.deepcopy(registry)
    _find_binding(registry_padded_key, GOLDEN_KEY_ID)["publicKey"] += "="
    registry_padded_key_path = _write_json(
        "cryptography/keys/registry-public-key-padded.json", registry_padded_key
    )

    registry_nonzero_pad_bits = copy.deepcopy(registry)
    selected_nonzero_pad_bits = _find_binding(registry_nonzero_pad_bits, GOLDEN_KEY_ID)
    selected_nonzero_pad_bits["publicKey"] = _with_nonzero_unused_pad_bits(
        selected_nonzero_pad_bits["publicKey"]
    )
    registry_nonzero_pad_bits_path = _write_json(
        "cryptography/keys/registry-public-key-nonzero-unused-pad-bits.json",
        registry_nonzero_pad_bits,
    )

    identity_public_key = b"\x01" + b"\x00" * 31
    off_curve_point = b"\x02" + b"\x00" * 31
    negative_zero_point = b"\x01" + b"\x00" * 30 + b"\x80"
    mixed_order_point = bytes.fromhex(
        "9599999999999999999999999999999999999999999999999999999999999999"
    )
    noncanonical_y_equal_p = _Q.to_bytes(32, "little")
    registry_identity_key = copy.deepcopy(registry)
    _find_binding(registry_identity_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        identity_public_key
    )
    registry_identity_key_path = _write_json(
        "cryptography/keys/registry-public-key-identity.json", registry_identity_key
    )

    registry_off_curve_key = copy.deepcopy(registry)
    _find_binding(registry_off_curve_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        off_curve_point
    )
    registry_off_curve_key_path = _write_json(
        "cryptography/keys/registry-public-key-off-curve.json",
        registry_off_curve_key,
    )

    registry_negative_zero_key = copy.deepcopy(registry)
    _find_binding(registry_negative_zero_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        negative_zero_point
    )
    registry_negative_zero_key_path = _write_json(
        "cryptography/keys/registry-public-key-negative-zero.json",
        registry_negative_zero_key,
    )

    registry_y_equal_p_key = copy.deepcopy(registry)
    _find_binding(registry_y_equal_p_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        noncanonical_y_equal_p
    )
    registry_y_equal_p_key_path = _write_json(
        "cryptography/keys/registry-public-key-y-equals-p.json",
        registry_y_equal_p_key,
    )

    registry_small_order_key = copy.deepcopy(registry)
    _find_binding(registry_small_order_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        (_Q - 1).to_bytes(32, "little")
    )
    registry_small_order_key_path = _write_json(
        "cryptography/keys/registry-public-key-small-order.json",
        registry_small_order_key,
    )

    registry_mixed_order_key = copy.deepcopy(registry)
    _find_binding(registry_mixed_order_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        mixed_order_point
    )
    registry_mixed_order_key_path = _write_json(
        "cryptography/keys/registry-public-key-mixed-order.json",
        registry_mixed_order_key,
    )

    registry_noncanonical_key = copy.deepcopy(registry)
    _find_binding(registry_noncanonical_key, GOLDEN_KEY_ID)["publicKey"] = _b64url(
        (_Q + 1).to_bytes(32, "little")
    )
    registry_noncanonical_key_path = _write_json(
        "cryptography/keys/registry-public-key-noncanonical.json",
        registry_noncanonical_key,
    )

    registry_cross_principal_reuse = copy.deepcopy(registry)
    reused_binding = copy.deepcopy(
        _find_binding(registry_cross_principal_reuse, GOLDEN_KEY_ID)
    )
    reused_binding["keyId"] = (
        "urn:missionweaveprotocol:key:crypto-vector-cross-principal-reuse"
    )
    reused_binding["principal"] = {
        "type": "agent",
        "id": "urn:missionweaveprotocol:agent:crypto-vector-impostor",
    }
    registry_cross_principal_reuse["bindings"].append(reused_binding)
    registry_cross_principal_reuse["bindings"].sort(key=lambda entry: entry["keyId"])
    registry_cross_principal_reuse_path = _write_json(
        "cryptography/keys/registry-public-key-cross-principal-reuse.json",
        registry_cross_principal_reuse,
    )

    registry_wrong_principal = copy.deepcopy(registry)
    _find_binding(registry_wrong_principal, GOLDEN_KEY_ID)["principal"] = {
        "type": "agent",
        "id": "urn:missionweaveprotocol:agent:crypto-vector-impostor",
    }
    registry_wrong_principal_path = _write_json(
        "cryptography/keys/registry-wrong-principal.json", registry_wrong_principal
    )

    registry_rebinding = copy.deepcopy(registry)
    rebound = copy.deepcopy(_find_binding(registry_rebinding, GOLDEN_KEY_ID))
    decoy_seed = hashlib.sha256(
        b"MissionWeaveProtocol 0.1 cryptography vector decoy public key"
    ).digest()
    rebound["publicKey"] = _b64url(_ed25519_public_key(decoy_seed))
    registry_rebinding["bindings"].append(rebound)
    registry_rebinding_path = _write_json(
        "cryptography/keys/registry-public-key-rebinding.json", registry_rebinding
    )

    rfc_input = (
        "{\n"
        '  "numbers": [333333333.33333329, 1E30, 4.50,\n'
        "              2e-3, 0.000000000000000000000000001],\n"
        '  "string": "\\u20ac$\\u000F\\u000aA\'\\u0042\\u0022\\u005c\\\\\\"\\/",\n'
        '  "literals": [null, true, false]\n'
        "}\n"
    ).encode("utf-8")
    rfc_expected = (
        '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,'
        '0.002,1e-27],"string":"€$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}'
    ).encode("utf-8")
    rfc_input_path = _write_bytes(
        "cryptography/vectors/canonicalization/rfc8785-section-3.2.2-input.json",
        rfc_input,
    )
    rfc_expected_path = _write_bytes(
        "cryptography/vectors/canonicalization/rfc8785-section-3.2.2.jcs",
        rfc_expected,
    )

    unsigned_documents = _prepare_unsigned_documents(keys)
    signed_documents: dict[str, dict[str, Any]] = {}
    signing_bytes_by_profile: dict[str, bytes] = {}
    document_paths: dict[str, str] = {}
    signing_bytes_paths: dict[str, str] = {}

    for profile_id in sorted(PROFILE_CONFIG):
        config = PROFILE_CONFIG[profile_id]
        unsigned = unsigned_documents[profile_id]
        key = keys[config["key"]]
        protected_time = unsigned[config["timeField"]]
        signed, signing_bytes = _sign_document(unsigned, key, protected_time)
        signed_documents[profile_id] = signed
        signing_bytes_by_profile[profile_id] = signing_bytes
        document_paths[profile_id] = _write_json(
            f"cryptography/vectors/signed-documents/valid/{profile_id}.json", signed
        )
        signing_bytes_paths[profile_id] = _write_bytes(
            f"cryptography/vectors/canonicalization/{profile_id}.signing.jcs",
            signing_bytes,
        )

    golden = signed_documents["command"]
    golden_signing_bytes = signing_bytes_by_profile["command"]
    if _sha256(golden_signing_bytes) != GOLDEN_SIGNING_HASH:
        raise RuntimeError("golden Command signing hash changed")
    if golden["signature"]["value"] != GOLDEN_SIGNATURE:
        raise RuntimeError("golden Command signature changed")
    if _sha256(_jcs(golden)) != GOLDEN_DOCUMENT_HASH:
        raise RuntimeError("golden signed-document hash changed")

    fractional_unsigned = copy.deepcopy(unsigned_documents["command"])
    fractional_unsigned["issuedAt"] = "2026-07-15T00:00:00.1234560000000000001Z"
    fractional_signed, fractional_signing_bytes = _sign_document(
        fractional_unsigned,
        keys["coordinator"],
        fractional_unsigned["issuedAt"],
    )
    fractional_document_path = _write_json(
        "cryptography/vectors/signed-documents/valid/"
        "command-timestamp-fractional-precision.json",
        fractional_signed,
    )
    fractional_signing_bytes_path = _write_bytes(
        "cryptography/vectors/canonicalization/"
        "command-timestamp-fractional-precision.signing.jcs",
        fractional_signing_bytes,
    )

    lowercase_unsigned = copy.deepcopy(unsigned_documents["command"])
    lowercase_unsigned["issuedAt"] = "2026-07-15t00:00:00Z"
    lowercase_signed, lowercase_signing_bytes = _sign_document(
        lowercase_unsigned,
        keys["coordinator"],
        lowercase_unsigned["issuedAt"],
    )
    if lowercase_signed["signature"]["createdAt"] != lowercase_unsigned["issuedAt"]:
        raise RuntimeError("lowercase-t protected timestamps are not byte-equal")
    alternate = {key: lowercase_signed[key] for key in reversed(list(lowercase_signed))}
    alternate_bytes = (
        "\n"
        + json.dumps(
            alternate,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    alternate_path = _write_bytes(
        "cryptography/vectors/signed-documents/valid/command-alternate-json-serialization.json",
        alternate_bytes,
    )
    lowercase_signing_bytes_path = _write_bytes(
        "cryptography/vectors/canonicalization/"
        "command-lowercase-t-alternate-serialization.signing.jcs",
        lowercase_signing_bytes,
    )
    standard_lowercase_serialization = (
        json.dumps(lowercase_signed, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    if alternate_bytes == standard_lowercase_serialization:
        raise RuntimeError("alternate Command serialization is not distinct")

    invalid_paths: dict[str, str] = {}
    golden_json = (
        json.dumps(golden, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    invalid_paths["bom"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-utf8-bom.json",
        b"\xef\xbb\xbf" + golden_json,
    )
    invalid_paths["trailing-data"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-trailing-data.json",
        golden_json + b"{}\n",
    )
    invalid_paths["duplicate"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-duplicate-decoded-member.json",
        _duplicate_payload_bytes(golden),
    )

    invalid_utf8 = bytearray((ROOT / document_paths["command"]).read_bytes())
    marker = b"payload-signature-must-be-covered"
    marker_offset = invalid_utf8.index(marker)
    invalid_utf8[marker_offset] = 0x80
    invalid_paths["invalid-utf8"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-invalid-utf8.bin",
        bytes(invalid_utf8),
    )

    unsupported = copy.deepcopy(golden)
    unsupported["signature"]["algorithm"] = "Ed448"
    invalid_paths["unsupported"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-unsupported-algorithm.json",
        unsupported,
    )

    invalid_timestamp_values = {
        "timestamp-leap-second": "2026-06-30T23:59:60Z",
        "timestamp-unknown-local-offset": "2026-07-15T00:00:00-00:00",
        "timestamp-year-zero": "0000-01-01T00:00:00Z",
    }
    for fault_id, timestamp in sorted(invalid_timestamp_values.items()):
        invalid_timestamp_unsigned = copy.deepcopy(unsigned_documents["command"])
        invalid_timestamp_unsigned["issuedAt"] = timestamp
        invalid_timestamp_signed, _ = _sign_document(
            invalid_timestamp_unsigned,
            keys["coordinator"],
            timestamp,
        )
        if invalid_timestamp_signed["signature"]["createdAt"] != timestamp:
            raise RuntimeError(f"{fault_id} signature time is not byte-equal")
        invalid_paths[fault_id] = _write_json(
            "cryptography/vectors/signed-documents/invalid/"
            f"command-{fault_id.removeprefix('timestamp-')}.json",
            invalid_timestamp_signed,
        )

    padded = copy.deepcopy(golden)
    padded["signature"]["value"] += "=="
    invalid_paths["padded"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-padded-signature.json",
        padded,
    )

    nonzero_pad_bits = copy.deepcopy(golden)
    signature_value = nonzero_pad_bits["signature"]["value"]
    nonzero_pad_bits["signature"]["value"] = _with_nonzero_unused_pad_bits(
        signature_value
    )
    invalid_paths["nonzero-pad-bits"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-nonzero-unused-pad-bits.json",
        nonzero_pad_bits,
    )

    wrong_signature_length = copy.deepcopy(golden)
    wrong_signature_length["signature"]["value"] = _b64url(
        _b64url_decode(GOLDEN_SIGNATURE)[:63]
    )
    invalid_paths["signature-length"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-wrong-length.json",
        wrong_signature_length,
    )

    golden_signature_bytes = _b64url_decode(GOLDEN_SIGNATURE)
    noncanonical_signature_r = copy.deepcopy(golden)
    noncanonical_signature_r["signature"]["value"] = _b64url(
        (_Q + 1).to_bytes(32, "little") + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-noncanonical"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-noncanonical.json",
        noncanonical_signature_r,
    )

    y_equal_p_signature_r = copy.deepcopy(golden)
    y_equal_p_signature_r["signature"]["value"] = _b64url(
        noncanonical_y_equal_p + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-y-equals-p"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-y-equals-p.json",
        y_equal_p_signature_r,
    )

    off_curve_signature_r = copy.deepcopy(golden)
    off_curve_signature_r["signature"]["value"] = _b64url(
        off_curve_point + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-off-curve"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-off-curve.json",
        off_curve_signature_r,
    )

    negative_zero_signature_r = copy.deepcopy(golden)
    negative_zero_signature_r["signature"]["value"] = _b64url(
        negative_zero_point + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-negative-zero"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-negative-zero.json",
        negative_zero_signature_r,
    )

    small_order_signature_r = copy.deepcopy(golden)
    small_order_signature_r["signature"]["value"] = _b64url(
        (_Q - 1).to_bytes(32, "little") + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-small-order"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-small-order.json",
        small_order_signature_r,
    )

    mixed_order_signature_r = copy.deepcopy(golden)
    mixed_order_signature_r["signature"]["value"] = _b64url(
        mixed_order_point + golden_signature_bytes[32:]
    )
    invalid_paths["signature-r-mixed-order"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-r-mixed-order.json",
        mixed_order_signature_r,
    )

    out_of_range_signature_s = copy.deepcopy(golden)
    out_of_range_signature_s["signature"]["value"] = _b64url(
        golden_signature_bytes[:32] + _L.to_bytes(32, "little")
    )
    invalid_paths["signature-s-out-of-range"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-signature-s-out-of-range.json",
        out_of_range_signature_s,
    )

    offset_unsigned = copy.deepcopy(unsigned_documents["command"])
    offset_unsigned["issuedAt"] = "2026-07-15T08:00:00+08:00"
    offset_signed, _ = _sign_document(
        offset_unsigned, keys["coordinator"], offset_unsigned["issuedAt"]
    )
    invalid_paths["non-utc-z"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-protected-time-not-utc-z.json",
        offset_signed,
    )

    time_mismatch = copy.deepcopy(golden)
    time_mismatch["signature"]["createdAt"] = "2026-07-15T00:00:01Z"
    invalid_paths["time-mismatch"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-created-at-mismatch.json",
        time_mismatch,
    )

    unknown_key = copy.deepcopy(golden)
    unknown_key["signature"]["keyId"] = (
        "urn:missionweaveprotocol:key:crypto-vector-missing"
    )
    invalid_paths["unknown-key"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-unknown-key.json",
        unknown_key,
    )

    alias_document = copy.deepcopy(golden)
    alias_document["signature"]["keyId"] = alias_key_id
    invalid_paths["key-alias"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-key-alias.json",
        alias_document,
    )

    jcs_domain = (ROOT / document_paths["command"]).read_bytes()
    old_number = b'"large": 1e+30'
    if jcs_domain.count(old_number) != 1:
        raise RuntimeError("cannot isolate golden large-number token")
    jcs_domain = jcs_domain.replace(old_number, b'"large": 1e400')
    invalid_paths["jcs-domain"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-number-1e400.json",
        jcs_domain,
    )

    unpaired_surrogate = copy.deepcopy(golden)
    unpaired_surrogate["extensions"][
        "urn:missionweaveprotocol:extension:crypto-vector"
    ]["data"]["unpairedSurrogate"] = "\ud800"
    invalid_paths["unpaired-surrogate"] = _write_bytes(
        "cryptography/vectors/signed-documents/invalid/command-unpaired-surrogate.json",
        (
            json.dumps(
                unpaired_surrogate,
                ensure_ascii=True,
                indent=2,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8"),
    )

    wrong_agent_card_signer, _ = _sign_document(
        unsigned_documents["agent-card"],
        keys["coordinator"],
        unsigned_documents["agent-card"][PROFILE_CONFIG["agent-card"]["timeField"]],
    )
    invalid_paths["agent-card-wrong-signer"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/agent-card-wrong-signer.json",
        wrong_agent_card_signer,
    )

    wrong_artifact_signer, _ = _sign_document(
        unsigned_documents["artifact"],
        keys["coordinator"],
        unsigned_documents["artifact"][PROFILE_CONFIG["artifact"]["timeField"]],
    )
    invalid_paths["artifact-wrong-signer"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/artifact-wrong-signer.json",
        wrong_artifact_signer,
    )

    weak_key_forgery = copy.deepcopy(golden)
    weak_key_forgery["signature"]["value"] = _b64url(identity_public_key + b"\x00" * 32)
    invalid_paths["weak-key-forgery"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-weak-key-forgery.json",
        weak_key_forgery,
    )

    payload_tamper = copy.deepcopy(golden)
    payload_tamper["payload"]["artifactHashes"][0] = "sha256:" + "b" * 64
    invalid_paths["payload-tamper"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-payload-tamper.json",
        payload_tamper,
    )

    payload_signature_tamper = copy.deepcopy(golden)
    payload_signature_tamper["payload"]["signature"] = "payload-signature-was-tampered"
    invalid_paths["payload-signature-tamper"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-payload-signature-tamper.json",
        payload_signature_tamper,
    )

    extension_signature_tamper = copy.deepcopy(golden)
    extension_signature_tamper["extensions"][
        "urn:missionweaveprotocol:extension:crypto-vector"
    ]["data"]["nested"]["signature"] = "nested-signature-was-tampered"
    invalid_paths["extension-signature-tamper"] = _write_json(
        "cryptography/vectors/signed-documents/invalid/command-extension-signature-tamper.json",
        extension_signature_tamper,
    )

    golden_evaluation = _complete_evaluation(
        "command",
        document_paths["command"],
        registry_path,
        signing_key_paths["coordinator"],
        golden,
        signing_bytes_paths["command"],
        golden_signing_bytes,
        keys["coordinator"],
    )
    alternate_evaluation = _complete_evaluation(
        "command",
        alternate_path,
        registry_timestamp_casing_offsets_path,
        signing_key_paths["coordinator"],
        lowercase_signed,
        lowercase_signing_bytes_path,
        lowercase_signing_bytes,
        keys["coordinator"],
    )

    profile_evaluations = []
    for profile_id in sorted(PROFILE_CONFIG):
        key_label = PROFILE_CONFIG[profile_id]["key"]
        if profile_id == "command":
            profile_evaluations.append(
                _complete_evaluation(
                    profile_id,
                    fractional_document_path,
                    registry_fractional_precision_path,
                    signing_key_paths[key_label],
                    fractional_signed,
                    fractional_signing_bytes_path,
                    fractional_signing_bytes,
                    keys[key_label],
                )
            )
            continue
        profile_evaluations.append(
            _complete_evaluation(
                profile_id,
                document_paths[profile_id],
                registry_path,
                signing_key_paths[key_label],
                signed_documents[profile_id],
                signing_bytes_paths[profile_id],
                signing_bytes_by_profile[profile_id],
                keys[key_label],
            )
        )

    def reject_case(
        case_id: str,
        fault_id: str,
        document_path: str,
        stage: str,
        wire_code: str,
        selected_registry: str = registry_path,
    ) -> dict[str, Any]:
        return {
            "id": case_id,
            "kind": "single",
            "evaluations": [
                _failure_evaluation(
                    fault_id=fault_id,
                    document_path=document_path,
                    registry_path=selected_registry,
                    stage=stage,
                    wire_code=wire_code,
                )
            ],
        }

    cases: list[dict[str, Any]] = [
        {
            "id": "accept.canonicalization.rfc8785-section-3.2.2",
            "kind": "canonicalization",
            "evaluations": [
                {
                    "input": rfc_input_path,
                    "expectedJcs": rfc_expected_path,
                    "sha256": _sha256(rfc_expected),
                }
            ],
        },
        {
            "id": "accept.command.golden",
            "kind": "single",
            "evaluations": [golden_evaluation],
        },
        {
            "id": "accept.command.alternate-json-serialization",
            "kind": "single",
            "evaluations": [alternate_evaluation],
        },
        {
            "id": "accept.profile-matrix.all-nine",
            "kind": "profile-matrix",
            "evaluations": profile_evaluations,
        },
        reject_case(
            "reject.parse.duplicate-decoded-member",
            "duplicate-decoded-member",
            invalid_paths["duplicate"],
            "parse",
            "PROTOCOL_VIOLATION",
        ),
        {
            "id": "reject.parse.byte-level-matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
                    _failure_evaluation(
                        fault_id="invalid-utf8",
                        document_path=invalid_paths["invalid-utf8"],
                        registry_path=registry_path,
                        stage="parse",
                        wire_code="PROTOCOL_VIOLATION",
                    ),
                    _failure_evaluation(
                        fault_id="utf8-bom",
                        document_path=invalid_paths["bom"],
                        registry_path=registry_path,
                        stage="parse",
                        wire_code="PROTOCOL_VIOLATION",
                    ),
                    _failure_evaluation(
                        fault_id="trailing-data",
                        document_path=invalid_paths["trailing-data"],
                        registry_path=registry_path,
                        stage="parse",
                        wire_code="PROTOCOL_VIOLATION",
                    ),
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        {
            "id": "reject.schema.validation-matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
                    _failure_evaluation(
                        fault_id="unsupported-algorithm",
                        document_path=invalid_paths["unsupported"],
                        registry_path=registry_path,
                        stage="schema",
                        wire_code="SCHEMA_VALIDATION_FAILED",
                    ),
                    *[
                        _failure_evaluation(
                            fault_id=fault_id,
                            document_path=invalid_paths[fault_id],
                            registry_path=registry_path,
                            stage="schema",
                            wire_code="SCHEMA_VALIDATION_FAILED",
                        )
                        for fault_id in sorted(invalid_timestamp_values)
                    ],
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        reject_case(
            "reject.schema.padded-signature-base64url",
            "padded-signature-base64url",
            invalid_paths["padded"],
            "schema",
            "SCHEMA_VALIDATION_FAILED",
        ),
        reject_case(
            "reject.signature-envelope.nonzero-unused-pad-bits",
            "signature-nonzero-unused-pad-bits",
            invalid_paths["nonzero-pad-bits"],
            "signature-envelope",
            "AUTH_INVALID_SIGNATURE",
        ),
        {
            "id": "reject.signature-envelope.ed25519-encoding-matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
                    _failure_evaluation(
                        fault_id="signature-wrong-length",
                        document_path=invalid_paths["signature-length"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-noncanonical",
                        document_path=invalid_paths["signature-r-noncanonical"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-y-equals-p",
                        document_path=invalid_paths["signature-r-y-equals-p"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-off-curve",
                        document_path=invalid_paths["signature-r-off-curve"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-negative-zero",
                        document_path=invalid_paths["signature-r-negative-zero"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-small-order",
                        document_path=invalid_paths["signature-r-small-order"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-r-mixed-order",
                        document_path=invalid_paths["signature-r-mixed-order"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="signature-s-out-of-range",
                        document_path=invalid_paths["signature-s-out-of-range"],
                        registry_path=registry_path,
                        stage="signature-envelope",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        reject_case(
            "reject.signature-envelope.protected-time-not-utc-z",
            "protected-time-not-utc-z",
            invalid_paths["non-utc-z"],
            "signature-envelope",
            "AUTH_INVALID_SIGNATURE",
        ),
        reject_case(
            "reject.signature-envelope.created-at-mismatch",
            "protected-time-created-at-mismatch",
            invalid_paths["time-mismatch"],
            "signature-envelope",
            "AUTH_INVALID_SIGNATURE",
        ),
        reject_case(
            "reject.key-resolution.unknown-key",
            "unknown-key",
            invalid_paths["unknown-key"],
            "key-resolution",
            "AUTH_INVALID_SIGNATURE",
        ),
        reject_case(
            "reject.key-resolution.key-id-alias",
            "key-id-alias",
            invalid_paths["key-alias"],
            "key-resolution",
            "AUTH_INVALID_SIGNATURE",
            registry_alias_path,
        ),
        reject_case(
            "reject.key-resolution.public-key-wrong-length",
            "public-key-wrong-length",
            document_paths["command"],
            "key-resolution",
            "AUTH_INVALID_SIGNATURE",
            registry_short_key_path,
        ),
        {
            "id": "reject.key-resolution.matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
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
                    _failure_evaluation(
                        fault_id="key-not-yet-valid",
                        document_path=document_paths["command"],
                        registry_path=registry_not_yet_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="valid-until-equality",
                        document_path=document_paths["command"],
                        registry_path=registry_valid_until_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="revoked-at-equality",
                        document_path=document_paths["command"],
                        registry_path=registry_revoked_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="agent-card-signer-not-service",
                        profile_id="agent-card",
                        basis_case_id="accept.profile-matrix.all-nine",
                        basis_profile_id="agent-card",
                        document_path=invalid_paths["agent-card-wrong-signer"],
                        registry_path=registry_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="artifact-signer-not-producer",
                        profile_id="artifact",
                        basis_case_id="accept.profile-matrix.all-nine",
                        basis_profile_id="artifact",
                        document_path=invalid_paths["artifact-wrong-signer"],
                        registry_path=registry_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="cross-principal-public-key-reuse",
                        document_path=document_paths["command"],
                        registry_path=registry_cross_principal_reuse_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-identity",
                        document_path=invalid_paths["weak-key-forgery"],
                        registry_path=registry_identity_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-off-curve",
                        document_path=document_paths["command"],
                        registry_path=registry_off_curve_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-negative-zero",
                        document_path=document_paths["command"],
                        registry_path=registry_negative_zero_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-y-equals-p",
                        document_path=document_paths["command"],
                        registry_path=registry_y_equal_p_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-small-order",
                        document_path=invalid_paths["weak-key-forgery"],
                        registry_path=registry_small_order_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-mixed-order",
                        document_path=invalid_paths["weak-key-forgery"],
                        registry_path=registry_mixed_order_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-noncanonical-encoding",
                        document_path=invalid_paths["weak-key-forgery"],
                        registry_path=registry_noncanonical_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-padded-base64url",
                        document_path=document_paths["command"],
                        registry_path=registry_padded_key_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="public-key-nonzero-unused-pad-bits",
                        document_path=document_paths["command"],
                        registry_path=registry_nonzero_pad_bits_path,
                        stage="key-resolution",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        reject_case(
            "reject.key-resolution.wrong-principal",
            "wrong-principal-binding",
            document_paths["command"],
            "key-resolution",
            "AUTH_INVALID_SIGNATURE",
            registry_wrong_principal_path,
        ),
        reject_case(
            "reject.key-resolution.public-key-rebinding",
            "public-key-rebinding",
            document_paths["command"],
            "key-resolution",
            "AUTH_INVALID_SIGNATURE",
            registry_rebinding_path,
        ),
        {
            "id": "reject.canonicalization.data-model-matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
                    _failure_evaluation(
                        fault_id="number-outside-finite-binary64",
                        document_path=invalid_paths["jcs-domain"],
                        registry_path=registry_path,
                        stage="canonicalization",
                        wire_code="PROTOCOL_VIOLATION",
                    ),
                    _failure_evaluation(
                        fault_id="unpaired-unicode-surrogate",
                        document_path=invalid_paths["unpaired-surrogate"],
                        registry_path=registry_path,
                        stage="canonicalization",
                        wire_code="PROTOCOL_VIOLATION",
                    ),
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        {
            "id": "reject.signature.equation-matrix",
            "kind": "failure-matrix",
            "evaluations": sorted(
                [
                    _failure_evaluation(
                        fault_id="payload-tamper",
                        document_path=invalid_paths["payload-tamper"],
                        registry_path=registry_path,
                        stage="signature",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                    _failure_evaluation(
                        fault_id="identity-r-equation-mismatch",
                        document_path=invalid_paths["weak-key-forgery"],
                        registry_path=registry_path,
                        stage="signature",
                        wire_code="AUTH_INVALID_SIGNATURE",
                    ),
                ],
                key=lambda evaluation: evaluation["fault"]["id"],
            ),
        },
        reject_case(
            "reject.signature.payload-nested-signature-tamper",
            "payload-nested-signature-tamper",
            invalid_paths["payload-signature-tamper"],
            "signature",
            "AUTH_INVALID_SIGNATURE",
        ),
        reject_case(
            "reject.signature.extension-nested-signature-tamper",
            "extension-nested-signature-tamper",
            invalid_paths["extension-signature-tamper"],
            "signature",
            "AUTH_INVALID_SIGNATURE",
        ),
    ]

    cases.sort(key=lambda case: case["id"])
    if len(cases) != 22:
        raise RuntimeError(f"expected 22 cases, generated {len(cases)}")
    evaluations = sum(len(case["evaluations"]) for case in cases)
    if evaluations != 62:
        raise RuntimeError(f"expected 62 evaluations, generated {evaluations}")

    manifest_without_digest = {
        "$schema": "https://missionweaveprotocol.dev/cryptography/0.1/manifest.schema.json",
        "manifestVersion": 1,
        "protocolVersion": "0.1",
        "profileId": PROFILE_ID,
        "semanticStages": [
            "parse",
            "schema",
            "signature-envelope",
            "key-resolution",
            "canonicalization",
            "signature",
            "complete",
        ],
        "fixtureSchemas": {
            "registry": "cryptography/registry-fixture.schema.json",
            "signingKey": "cryptography/signing-key-fixture.schema.json",
        },
        "profiles": _profiles(),
        "artifacts": _artifact_index(),
        "cases": cases,
    }
    manifest = copy.deepcopy(manifest_without_digest)
    manifest["artifactDigest"] = _sha256(_jcs(manifest_without_digest))
    _write_json("cryptography/manifest.json", manifest)

    print(
        "Generated MissionWeaveProtocol cryptography bundle: "
        f"{len(cases)} cases, {evaluations} evaluations, "
        f"{len(manifest['artifacts'])} artifacts."
    )


if __name__ == "__main__":
    generate()
