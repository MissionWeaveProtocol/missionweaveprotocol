[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol 图标">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">官方网站与文档</a></strong>
</p>

MissionWeaveProtocol 是一种面向群组的协作协议，适用于在同一 Organization 内工作的自治
Agent。每个 Agent 都可以同时参与多个 Mission Group，与对等方交换全双工 Message，将明确
的 WorkItem 接收后加入各 Group 的队列，并依据自身的本地策略跨 Group 调度工作。

本仓库定义 **MissionWeaveProtocol 0.1**。其稳定的线协议命名空间为
`missionweaveprotocol`：协议标识符使用 `urn:missionweaveprotocol:*`，内置扩展类型使用
`ext.missionweaveprotocol.*`。

MissionWeaveProtocol 不是 Agent-to-Agent RPC、物理对等路由、联邦协议或分布式共识协议。
一个受信任的 Organization 负责提供身份、策略、授权、持久化的 Group 顺序和人类问责机制。

## 规范性产物

本仓库是版本化协议产物包的唯一权威来源：

- [规范性协议说明](spec/PROTOCOL.md)；
- [协议术语表](CONTEXT.md)；
- [21 个 JSON Schema](schemas/README.md)；
- [有效与无效的符合性测试向量](conformance/manifest.json)；
- [品牌资源](assets/brand/)。

实现必须固定使用某个已发布的协议版本或 commit。实现可以内置 JSON Schema 和测试向量以供
离线验证，但这些副本不具有规范性。

## 实现

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) — 官方
  Python 参考实现、Agent 运行时、Group 网关、符合性测试运行器和 POC。

协议发布与实现发布采用独立版本。实现必须发布明确的兼容性声明，而不能因为版本号相同就
假定二者兼容。

## 符合性

manifest 当前包含 52 个测试用例：25 个预期有效的文档和 27 个预期无效的文档。结构性的
JSON Schema 符合性是必要条件，但并不充分；实现还必须执行协议说明中的状态机、排序、
epoch、lease、budget、层级、签名和授权规则。

Python 实现可以直接运行本仓库的测试向量：

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

也可以在本仓库内执行验证：

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## 许可证

协议说明、JSON Schema、符合性测试向量和品牌资源均采用 [Apache-2.0](LICENSE) 许可证。该
许可证不授予任何商标权。
