[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | **Deutsch**

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol-Symbol">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">Offizielle Website und Dokumentation</a></strong>
</p>

MissionWeaveProtocol ist ein Group-orientiertes Kooperationsprotokoll für
autonome Agent, die innerhalb einer Organization arbeiten. Agent können an vielen
Mission Groups teilnehmen, Vollduplex-Message mit Peers austauschen, ausdrückliche
WorkItem in Group-spezifische Warteschlangen aufnehmen und Arbeit gemäß ihrer
eigenen lokalen Richtlinie über mehrere Groups hinweg planen.

Dieses Repository definiert **MissionWeaveProtocol 0.1**. Sein stabiler
Wire-Namespace lautet `missionweaveprotocol`: Protokollkennungen verwenden
`urn:missionweaveprotocol:*`, integrierte Erweiterungsarten verwenden
`ext.missionweaveprotocol.*`.

MissionWeaveProtocol ist weder Agent-to-Agent RPC noch physisches
Peer-to-Peer-Routing, Föderation oder ein verteiltes Konsensprotokoll. Eine
vertrauenswürdige Organization stellt Identität, Richtlinien, Autorisierung,
dauerhafte Group-Reihenfolge und menschliche Verantwortlichkeit bereit.

## Normative Artefakte

Dieses Repository ist die maßgebliche Quelle für das versionierte
Protokollartefakt-Bündel:

- [normative Spezifikation](spec/PROTOCOL.md);
- [Protokollglossar](CONTEXT.md);
- [22 normative JSON-Schemata](schemas/README.md);
- [gültige und ungültige Konformitätsvektoren](conformance/manifest.json);
- [Kryptografiebündel mit 22 Fällen für die neun Schemaprofile des Signed Document Verification
  Profile](cryptography/README.md);
- [First-Admission- und Historical-Trust-Bündel mit 5 Fällen und 30
  Auswertungen](admission/README.md);
- [Markenressourcen](assets/brand/).

Implementierungen müssen eine veröffentlichte Protokollversion oder einen Commit
pinnen. Sie dürfen die Schemas und Vektoren für die Offline-Validierung
einbetten, doch diese Kopien sind nicht normativ.

## Implementierungen

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk)
  — offizielle Python-Referenzimplementierung, Agent-Runtime, Group-Gateway,
  Konformitäts-Runner und POC.
- [MissionWeaveProtocol Go SDK](https://github.com/missionweaveprotocol/go-sdk)
  — offizielles Go-Protokoll-SDK mit Protokoll-Bindings sowie Schema- und
  Vektorkonformität.
- [MissionWeaveProtocol TypeScript SDK](https://github.com/missionweaveprotocol/typescript-sdk)
  — offizielles TypeScript-Protokoll-SDK mit Protokoll-Bindings sowie Schema-
  und Vektorkonformität.
- [MissionWeaveProtocol Java SDK](https://github.com/missionweaveprotocol/java-sdk)
  — offizielles Java-Protokoll-SDK mit Protokoll-Bindings sowie Schema- und
  Vektorkonformität.
- [MissionWeaveProtocol Rust SDK](https://github.com/missionweaveprotocol/rust-sdk)
  — offizielles Rust-Protokoll-SDK mit Protokoll-Bindings sowie Schema- und
  Vektorkonformität.
- [MissionWeaveProtocol C++ SDK](https://github.com/missionweaveprotocol/cpp-sdk)
  — offizielles C++-Protokoll-SDK mit Protokoll-Bindings sowie Schema- und
  Vektorkonformität.

Protokoll- und Implementierungs-Releases werden unabhängig voneinander
versioniert. Eine Implementierung muss eine ausdrückliche
Kompatibilitätserklärung veröffentlichen, statt aus gleichen Versionsnummern
Kompatibilität abzuleiten.

Python ist die vollständige Referenz-Runtime. Die SDKs für Go, TypeScript, Java,
Rust und C++ konzentrieren sich derzeit auf Protokoll-Bindings sowie Schema- und
Vektorkonformität; sie beanspruchen keine vollständige verhaltensbezogene
Runtime-Konformität.

## Konformität

Das strukturelle Manifest enthält 58 Vektoren: 27 als gültig erwartete Dokumente und 31
als ungültig erwartete Dokumente. Strukturelle Schema-Konformität ist notwendig,
aber nicht ausreichend; Implementierungen müssen außerdem die Regeln der
Spezifikation zu Zustandsmaschine, Reihenfolge, Epoch, Lease, Budget, Hierarchie,
Signatur und Autorisierung durchsetzen.

Das unabhängige Kryptografie-Manifest enthält 22 Fälle und 62 Auswertungen für die neun
Schemaprofile des Signed Document Verification Profile. Sein Bestehen weist die Konformität mit den
deklarierten Auswertungen über die sechs kryptografischen Prüfschritte aus Abschnitt 6.4 nach.

Das getrennte Admission-Manifest enthält 5 Fälle und 30 Auswertungen für First-Admission Record und
historisches Vertrauen oberhalb der kryptografischen Verifikation. Admission bleibt von den sechs
kryptografischen Prüfschritten getrennt. Weder dieses noch das Kryptografiebündel weist die
Aktualitäts- oder Uhrabweichungsprüfung für Command oder die Autorisierung des Unterzeichners nach;
diese Prüfungen liegen außerhalb dieses Slices.

Die Python-Implementierung kann die Vektoren dieses Repositorys direkt ausführen:

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

Eine Repository-lokale Validierung ist ebenfalls verfügbar:

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: \
  -r requirements-cryptography.lock
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
python scripts/validate_crypto_vectors.py
python scripts/validate_admission_vectors.py
```

## Lizenz

Spezifikation, Schemas, Konformitäts-, Kryptografie- und Admission-Vektoren sowie Markenressourcen
sind unter [Apache-2.0](LICENSE) lizenziert. Die Lizenz gewährt keine Markenrechte.
