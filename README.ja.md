[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol アイコン">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">公式ウェブサイトとドキュメント</a></strong>
</p>

MissionWeaveProtocol は、単一の Organization 内で活動する自律型 Agent のための、
Group 指向の協働プロトコルです。Agent は複数の Mission Group に参加し、全二重の
ピア間 Message を交換し、明示的な WorkItem を Group ごとのキューに受け入れ、
自身のローカルポリシーに従って複数の Group にまたがる作業をスケジュールできます。

本リポジトリでは **MissionWeaveProtocol 0.1** を定義します。安定したワイヤ名前空間は
`missionweaveprotocol` です。プロトコル識別子には `urn:missionweaveprotocol:*` を、
組み込み拡張の種別には `ext.missionweaveprotocol.*` を使用します。

MissionWeaveProtocol は、Agent-to-Agent RPC、物理的なピアツーピアルーティング、
フェデレーション、分散合意プロトコルのいずれでもありません。信頼された単一の
Organization が、アイデンティティ、ポリシー、認可、永続的な Group の順序付け、
および人による説明責任を提供します。

## 規範成果物

本リポジトリは、バージョン管理されたプロトコル成果物バンドルの信頼できる唯一の情報源です。

- [規範仕様](spec/PROTOCOL.md)
- [プロトコル用語集](CONTEXT.md)
- [21 個の JSON Schema](schemas/README.md)
- [妥当および不妥当な適合性ベクトル](conformance/manifest.json)
- [ブランドアセット](assets/brand/)

実装は、リリース済みのプロトコルバージョンまたはコミットを固定しなければなりません。
オフライン検証のために Schema とベクトルを同梱できますが、それらの複製は規範ではありません。

## 実装

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) — 公式の
  Python リファレンス実装、Agent ランタイム、Group ゲートウェイ、適合性ランナー、および POC。

プロトコルのリリースと実装のリリースは、それぞれ独立してバージョン管理されます。実装は、
同じバージョン番号なら互換性があると仮定せず、明示的な互換性宣言を公開しなければなりません。

## 適合性

現在のマニフェストには 52 件のケースが含まれます。内訳は、妥当と期待される文書 25 件と、
不妥当と期待される文書 27 件です。構造上の Schema 適合性は必要条件ですが、十分条件では
ありません。実装は、仕様に定める状態機械、順序付け、エポック、リース、予算、階層、署名、
および認可の規則も適用しなければなりません。

Python 実装から、本リポジトリのベクトルを直接実行できます。

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

リポジトリ内での検証も利用できます。

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## ライセンス

仕様、Schema、適合性ベクトル、およびブランドアセットには、
[Apache-2.0](LICENSE) が適用されます。このライセンスは商標権を付与しません。
