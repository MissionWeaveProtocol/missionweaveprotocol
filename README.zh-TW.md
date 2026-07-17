[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol 圖示">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">官方網站與文件</a></strong>
</p>

MissionWeaveProtocol 是一種面向群組的協作協定，適用於在同一 Organization 內工作的自治
Agent。每個 Agent 都可以同時參與多個 Mission Group，與對等方交換全雙工 Message，將明確
的 WorkItem 接收後加入各 Group 的佇列，並依據自身的本機策略跨 Group 排程工作。

本儲存庫定義 **MissionWeaveProtocol 0.1**。其穩定的 wire namespace（線路命名空間）為
`missionweaveprotocol`：協定識別碼使用 `urn:missionweaveprotocol:*`，內建擴充類型使用
`ext.missionweaveprotocol.*`。

MissionWeaveProtocol 不是 Agent-to-Agent RPC、物理對等路由、聯邦機制或分散式共識協定。
一個受信任的 Organization 負責提供身分、策略、授權、持久化的 Group 順序和人類課責機制。

## 規範性產出物

本儲存庫是版本化協定產出物包的唯一權威來源：

- [規範性協定規格](spec/PROTOCOL.md)；
- [協定術語表](CONTEXT.md)；
- [21 個 JSON Schema](schemas/README.md)；
- [有效與無效的符合性測試向量](conformance/manifest.json)；
- [品牌資源](assets/brand/)。

實作必須固定使用某個已發布的協定版本或 commit。實作可以內建 JSON Schema 和測試向量以供
離線驗證，但這些副本不具有規範性。

## 實作

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) — 官方
  Python 參考實作、Agent runtime、Group gateway、符合性測試執行器和 POC。

協定發布與實作發布採用獨立版本。實作必須發布明確的相容性宣告，而不能因為版本號相同就
假定二者相容。

## 符合性

manifest 目前包含 43 個測試案例：22 個預期有效的文件和 21 個預期無效的文件。結構性的
JSON Schema 符合性是必要條件，但並不充分；實作還必須執行協定規格中的狀態機、排序、
epoch、lease、budget、層級、簽名和授權規則。

Python 實作可以直接執行本儲存庫的測試向量：

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

也可以在本儲存庫內執行驗證：

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## 授權條款

協定規格、JSON Schema、符合性測試向量和品牌資源均採用 [Apache-2.0](LICENSE) 授權條款。
此授權不授予任何商標權。
