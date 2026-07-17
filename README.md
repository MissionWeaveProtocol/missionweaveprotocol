# MissionWeave Protocol

<p align="center">
  <img src="assets/brand/missionweave-icon.svg" width="160" alt="MissionWeave icon">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">Official website and documentation</a></strong>
</p>

MissionWeave is a group-oriented cooperation protocol for autonomous Agents working inside one
Organization. Agents can participate in many Mission Groups, exchange full-duplex peer Messages,
accept explicit WorkItems into per-Group queues, and schedule work across Groups under their own
local policy.

This repository defines **MissionWeave Protocol 0.1**. Its stable wire namespace is
`missionweave`: protocol identifiers use `urn:missionweave:*`, and built-in extension kinds use
`ext.missionweave.*`.

MissionWeave is not Agent-to-Agent RPC, physical peer-to-peer routing, federation, or a distributed
consensus protocol. One trusted Organization supplies identity, policy, authorization, durable
Group ordering, and human accountability.

## Normative artifacts

This repository is the source of truth for the versioned protocol artifact bundle:

- [normative specification](spec/PROTOCOL.md);
- [protocol glossary](CONTEXT.md);
- [21 JSON Schemas](schemas/README.md);
- [valid and invalid conformance vectors](conformance/manifest.json);
- [brand assets](assets/brand/).

Implementations must pin a released protocol version or commit. They may vendor the schemas and
vectors for offline validation, but those copies are not normative.

## Implementations

- [MissionWeave Python SDK](https://github.com/missionweaveprotocol/python-sdk) — official
  Python reference implementation, Agent runtime, Group gateway, conformance runner, and POC.

Protocol releases and implementation releases are versioned independently. An implementation
must publish an explicit compatibility declaration instead of assuming that equal version numbers
mean compatibility.

## Conformance

The manifest currently contains 43 cases: 22 expected-valid documents and 21 expected-invalid
documents. Structural schema conformance is necessary but not sufficient; implementations must
also enforce the state-machine, ordering, epoch, lease, budget, hierarchy, signature, and
authorization rules in the specification.

The Python implementation can run this repository's vectors directly:

```bash
uv run --project ../python-sdk missionweave-conformance --root .
```

Repository-local validation is also available:

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## License

The specification, schemas, conformance vectors, and brand assets are licensed under
[Apache-2.0](LICENSE). The license does not grant trademark rights.
