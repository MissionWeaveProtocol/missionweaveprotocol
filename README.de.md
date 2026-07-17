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
Mission Group teilnehmen, Vollduplex-Message mit Peers austauschen, ausdrückliche
WorkItem in Group-spezifische Warteschlangen aufnehmen und Arbeit gemäß ihrer
eigenen lokalen Richtlinie über mehrere Group hinweg planen.

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
- [21 JSON Schemas](schemas/README.md);
- [gültige und ungültige Konformitätsvektoren](conformance/manifest.json);
- [Markenressourcen](assets/brand/).

Implementierungen müssen eine veröffentlichte Protokollversion oder einen Commit
pinnen. Sie dürfen die Schemas und Vektoren für die Offline-Validierung
einbetten, doch diese Kopien sind nicht normativ.

## Implementierungen

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk)
  — offizielle Python-Referenzimplementierung, Agent Runtime, Group Gateway,
  Konformitäts-Runner und POC.

Protokoll- und Implementierungs-Releases werden unabhängig voneinander
versioniert. Eine Implementierung muss eine ausdrückliche
Kompatibilitätserklärung veröffentlichen, statt aus gleichen Versionsnummern
Kompatibilität abzuleiten.

## Konformität

Das Manifest enthält derzeit 52 Fälle: 25 erwartbar gültige Dokumente und 27
erwartbar ungültige Dokumente. Strukturelle Schema-Konformität ist notwendig,
aber nicht ausreichend; Implementierungen müssen außerdem die Regeln der
Spezifikation zu Zustandsmaschine, Reihenfolge, Epoch, Lease, Budget, Hierarchie,
Signatur und Autorisierung durchsetzen.

Die Python-Implementierung kann die Vektoren dieses Repository direkt ausführen:

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

Eine Repository-lokale Validierung ist ebenfalls verfügbar:

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## Lizenz

Spezifikation, Schemas, Konformitätsvektoren und Markenressourcen sind unter
[Apache-2.0](LICENSE) lizenziert. Die Lizenz gewährt keine Markenrechte.
