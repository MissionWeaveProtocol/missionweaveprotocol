#!/usr/bin/env python3
"""Validate normative schemas and every declared conformance vector."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import FormatChecker, ValidationError
from jsonschema.validators import validator_for
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"
VECTOR_ROOT = ROOT / "conformance" / "vectors"
MANIFEST_PATH = ROOT / "conformance" / "manifest.json"
SCHEMA_ID_BASE = "https://missionweaveprotocol.dev/schemas/0.1/"
EXPECTED_SCHEMA_COUNT = 22
EXPECTED_VECTOR_COUNT = 58


class ProtocolValidationError(RuntimeError):
    """Raised when the protocol artifact bundle is internally inconsistent."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProtocolValidationError(
            f"cannot load JSON from {path.relative_to(ROOT)}: {error}"
        ) from error


def _repository_path(value: object, *, parent: Path, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ProtocolValidationError(f"manifest field {field!r} must be a non-empty string")

    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ProtocolValidationError(
            f"manifest field {field!r} is not a safe repository path: {value}"
        )

    resolved = (ROOT / relative).resolve()
    if not resolved.is_relative_to(parent.resolve()):
        raise ProtocolValidationError(
            f"manifest field {field!r} escapes {parent.relative_to(ROOT)}: {value}"
        )
    if not resolved.is_file():
        raise ProtocolValidationError(f"manifest field {field!r} does not name a file: {value}")
    return resolved


def _load_schemas() -> tuple[dict[Path, dict[str, Any]], Registry]:
    schema_paths = sorted(SCHEMA_ROOT.glob("*.json"))
    if len(schema_paths) != EXPECTED_SCHEMA_COUNT:
        raise ProtocolValidationError(
            f"expected {EXPECTED_SCHEMA_COUNT} schemas, found {len(schema_paths)}"
        )

    schemas: dict[Path, dict[str, Any]] = {}
    resources: list[tuple[str, Resource[Any]]] = []
    identifiers: set[str] = set()

    for path in schema_paths:
        document = _load_json(path)
        if not isinstance(document, dict):
            raise ProtocolValidationError(f"schema is not an object: {path.relative_to(ROOT)}")

        validator_type = validator_for(document)
        validator_type.check_schema(document)

        identifier = document.get("$id")
        expected_identifier = f"{SCHEMA_ID_BASE}{path.name}"
        if identifier != expected_identifier:
            raise ProtocolValidationError(
                f"schema identifier mismatch in {path.relative_to(ROOT)}: "
                f"expected {expected_identifier!r}, got {identifier!r}"
            )
        if identifier in identifiers:
            raise ProtocolValidationError(f"duplicate schema identifier: {identifier}")

        identifiers.add(identifier)
        schemas[path.resolve()] = document
        resources.append((identifier, Resource.from_contents(document)))

    return schemas, Registry().with_resources(resources)


def _load_manifest() -> list[dict[str, Any]]:
    document = _load_json(MANIFEST_PATH)
    if not isinstance(document, list) or not document:
        raise ProtocolValidationError("conformance manifest must be a non-empty array")
    if not all(isinstance(item, dict) for item in document):
        raise ProtocolValidationError("every conformance manifest entry must be an object")
    return document


def _validate_vectors(schemas: dict[Path, dict[str, Any]], registry: Registry) -> None:
    manifest = _load_manifest()
    if len(manifest) != EXPECTED_VECTOR_COUNT:
        raise ProtocolValidationError(
            f"expected {EXPECTED_VECTOR_COUNT} conformance vectors, found {len(manifest)}"
        )

    names: set[str] = set()
    instances: set[Path] = set()

    for index, item in enumerate(manifest, start=1):
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ProtocolValidationError(f"manifest entry {index} has no non-empty name")
        if name in names:
            raise ProtocolValidationError(f"duplicate conformance case name: {name}")
        names.add(name)

        if type(item.get("valid")) is not bool:
            raise ProtocolValidationError(
                f"conformance case {name!r} has a non-boolean valid field"
            )
        expected_valid = item["valid"]

        schema_path = _repository_path(
            item.get("schema"), parent=SCHEMA_ROOT, field="schema"
        )
        instance_path = _repository_path(
            item.get("instance"), parent=VECTOR_ROOT, field="instance"
        )
        if instance_path in instances:
            raise ProtocolValidationError(
                f"conformance vector is listed more than once: {instance_path.relative_to(ROOT)}"
            )
        instances.add(instance_path)

        try:
            schema = schemas[schema_path]
        except KeyError as error:
            raise ProtocolValidationError(
                f"manifest references a non-normative schema: {schema_path.relative_to(ROOT)}"
            ) from error

        instance = _load_json(instance_path)
        validator_type = validator_for(schema)
        validator = validator_type(schema, registry=registry, format_checker=FormatChecker())

        try:
            validator.validate(instance)
            actual_valid = True
        except ValidationError:
            actual_valid = False

        if actual_valid != expected_valid:
            expectation = "valid" if expected_valid else "invalid"
            result = "valid" if actual_valid else "invalid"
            raise ProtocolValidationError(
                f"conformance case {name!r} expected {expectation} but was {result}"
            )

    vector_files = {path.resolve() for path in VECTOR_ROOT.rglob("*.json") if path.is_file()}
    unlisted = sorted(path.relative_to(ROOT) for path in vector_files - instances)
    missing = sorted(path.relative_to(ROOT) for path in instances - vector_files)
    if unlisted or missing:
        details = []
        if unlisted:
            details.append("unlisted vectors: " + ", ".join(map(str, unlisted)))
        if missing:
            details.append("missing vectors: " + ", ".join(map(str, missing)))
        raise ProtocolValidationError("; ".join(details))

    print(
        f"Validated {EXPECTED_SCHEMA_COUNT} schemas and "
        f"{EXPECTED_VECTOR_COUNT} conformance vectors."
    )


def main() -> int:
    try:
        schemas, registry = _load_schemas()
        _validate_vectors(schemas, registry)
    except ProtocolValidationError as error:
        print(f"Protocol validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
