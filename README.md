**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol icon">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">Official website and documentation</a></strong>
</p>

MissionWeaveProtocol is a group-oriented cooperation protocol for autonomous Agents working inside
one Organization. Agents can participate in many Mission Groups, exchange full-duplex peer
Messages, accept explicit WorkItems into per-Group queues, and schedule work across Groups under
their own local policy.

This repository defines **MissionWeaveProtocol 0.1**. Its stable wire namespace is
`missionweaveprotocol`: protocol identifiers use `urn:missionweaveprotocol:*`, and built-in
extension kinds use `ext.missionweaveprotocol.*`.

MissionWeaveProtocol is not Agent-to-Agent RPC, physical peer-to-peer routing, federation, or a
distributed consensus protocol. One trusted Organization supplies identity, policy, authorization,
durable Group ordering, and human accountability.

## Normative artifacts

This repository is the source of truth for the versioned protocol artifact bundle:

- [normative specification](spec/PROTOCOL.md);
- [protocol glossary](CONTEXT.md);
- [21 JSON Schemas](schemas/README.md);
- [valid and invalid conformance vectors](conformance/manifest.json);
- [signed-document cryptography bundle covering nine schema profiles with 22
  cases](cryptography/README.md);
- [brand assets](assets/brand/).

Implementations must pin a released protocol version or commit. They may vendor the schemas and
vectors for offline validation, but those copies are not normative.

## Implementations

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) — official
  Python reference implementation, Agent runtime, Group gateway, conformance runner, and POC.
- [MissionWeaveProtocol Go SDK](https://github.com/missionweaveprotocol/go-sdk) — official Go
  protocol bindings with schema-and-vector conformance.
- [MissionWeaveProtocol TypeScript SDK](https://github.com/missionweaveprotocol/typescript-sdk) —
  official TypeScript protocol bindings with schema-and-vector conformance.
- [MissionWeaveProtocol Java SDK](https://github.com/missionweaveprotocol/java-sdk) — official Java
  protocol bindings with schema-and-vector conformance.
- [MissionWeaveProtocol Rust SDK](https://github.com/missionweaveprotocol/rust-sdk) — official Rust
  protocol bindings with schema-and-vector conformance.
- [MissionWeaveProtocol C++ SDK](https://github.com/missionweaveprotocol/cpp-sdk) — official C++
  protocol bindings with schema-and-vector conformance.

Protocol releases and implementation releases are versioned independently. An implementation
must publish an explicit compatibility declaration instead of assuming that equal version numbers
mean compatibility.

Python is the full reference runtime. The Go, TypeScript, Java, Rust, and C++ SDKs currently focus
on protocol bindings and schema-and-vector conformance; they do not claim full behavioral runtime
conformance.

## Conformance

The manifest currently contains 56 cases: 26 expected-valid documents and 30 expected-invalid
documents. Structural schema conformance is necessary but not sufficient; implementations must
also enforce the state-machine, ordering, epoch, lease, budget, hierarchy, signature, and
authorization rules in the specification.

The independent cryptography manifest contains 22 cases covering all nine schema profiles in the
Signed Document Verification Profile. Passing it demonstrates conformance to the declared
evaluations across the six cryptographic verification stages in Section 6.4; it does not prove
First-Admission Record or historical-trust validation, Command freshness or clock-skew
enforcement, or signer authorization under applicable role and policy.

The Python implementation can run this repository's vectors directly:

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

Repository-local validation is also available:

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: \
  -r requirements-cryptography.lock
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
python scripts/validate_crypto_vectors.py
```

## License

The specification, schemas, conformance and cryptography vectors, and brand assets are licensed
under [Apache-2.0](LICENSE). The license does not grant trademark rights.
