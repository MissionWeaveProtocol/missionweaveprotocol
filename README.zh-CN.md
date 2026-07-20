[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="MissionWeaveProtocol 图标">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">官方网站与文档</a></strong>
</p>

MissionWeaveProtocol 是一种面向群组的协作协议，适用于在同一 Organization 内工作的自治
Agent。每个 Agent 都可以同时参与多个 Mission Group，与对等方交换全双工 Message，接收明确
分派的 WorkItem，将其加入各 Group 的队列，并依据自身的本地策略跨 Group 调度工作。

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
- [覆盖 Signed Document Verification Profile 中 9 种 Schema 验证配置、包含 22 个用例的
  密码学测试包](cryptography/README.md)；
- [品牌资源](assets/brand/)。

实现必须固定使用某个已发布的协议版本或 commit。实现可以内置 JSON Schema 和测试向量以供
离线验证，但这些副本不具有规范性。

## 实现

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) — 官方
  Python 参考实现、Agent 运行时、Group 网关、符合性测试运行器和 POC。
- [MissionWeaveProtocol Go SDK](https://github.com/missionweaveprotocol/go-sdk) — 官方 Go 协议
  SDK，提供协议绑定以及 Schema 与测试向量符合性能力。
- [MissionWeaveProtocol TypeScript SDK](https://github.com/missionweaveprotocol/typescript-sdk) —
  官方 TypeScript 协议 SDK，提供协议绑定以及 Schema 与测试向量符合性能力。
- [MissionWeaveProtocol Java SDK](https://github.com/missionweaveprotocol/java-sdk) — 官方 Java
  协议 SDK，提供协议绑定以及 Schema 与测试向量符合性能力。
- [MissionWeaveProtocol Rust SDK](https://github.com/missionweaveprotocol/rust-sdk) — 官方 Rust
  协议 SDK，提供协议绑定以及 Schema 与测试向量符合性能力。
- [MissionWeaveProtocol C++ SDK](https://github.com/missionweaveprotocol/cpp-sdk) — 官方 C++ 协议
  SDK，提供协议绑定以及 Schema 与测试向量符合性能力。

协议发布与实现发布采用独立版本。实现必须发布明确的兼容性声明，而不能因为版本号相同就
假定二者兼容。

Python 是完整的参考运行时。Go、TypeScript、Java、Rust 和 C++ SDK 当前专注于协议绑定以及
Schema 与测试向量符合性，并不声明完整的运行时行为符合性。

## 符合性

manifest 当前包含 56 个测试用例：26 个预期有效的文档和 30 个预期无效的文档。结构性的
JSON Schema 符合性是必要条件，但并不充分；实现还必须执行协议说明中的状态机、排序、
epoch、lease、budget、层级、签名和授权规则。

独立的密码学 manifest 包含 22 个用例，覆盖 Signed Document Verification Profile 中全部 9
种 Schema 验证配置。通过该测试包可表明实现符合第 6.4 节六阶段密码学验证中已声明的评估项；
它不能证明 First-Admission Record（首次接纳记录）或历史信任验证、Command 新鲜度或时钟
偏差约束，也不能证明依据签名者角色和适用策略进行的授权。

Python 实现可以直接运行本仓库的测试向量：

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

也可以在本仓库内执行验证：

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: \
  -r requirements-cryptography.lock
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
python scripts/validate_crypto_vectors.py
```

## 许可证

协议说明、JSON Schema、符合性与密码学测试向量和品牌资源均采用 [Apache-2.0](LICENSE) 许可证。该
许可证不授予任何商标权。
