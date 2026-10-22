# Adaptive Research Agent 0.3 历史设计索引

**当前目标权威（2026-10-20）**：[现行规格](../../SPEC.md)、[现行计划](../../PLANS.md)、[现行契约](../contracts/CURRENT_CONTRACTS.md)和[现行评测协议 `current-3`](../evaluation/CURRENT_EVAL_PROTOCOL.json)是后续明确授权任务的唯一执行入口；[ADR-0005](adr/0005-windows-worker-wsl-postgres.md)记录 Windows Worker＋WSL PostgreSQL 的首版决定。[ADR-0004](adr/0004-portfolio-local-runtime.md)已被取代，保留作历史。现有行为仍以 V1 规格、契约及源码为准。P-00 离线配置已完成；业务实施、付费评测和部署仍分别需要授权。[P-01 开工包](../audits/PREDEV_P01_START_PACKAGE_2026-10-20.md)与[后续任务包](../audits/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)记录实施顺序和证据要求。

**归档**：[此前目标规格](../archive/target-2026-10-18/SPEC.md)、[计划](../archive/target-2026-10-18/PLANS.md)、[目标契约](../contracts/0.5_TARGET_CONTRACTS.md)、[G3 协议](../evaluation/G3_EVAL_PROTOCOL.json)与 ADR-0003 原样保留；0.4 快照及本目录 0.3 正文亦是历史记录，不作为当前任务要求。

**此前准备验证**：[2026-10-19 离线检查记录](../audits/PREDEV_0_5_VERIFICATION_2026-10-19.md)只证明当时材料的链接、映射和协议结构；本轮[最终设计记录](../audits/PREDEV_FINAL_DESIGN_REVIEW_2026-10-19.md)另记确认与待验证项。业务及局域网部署仍 No-Go。

**七项核心定稿（2026-10-20）**：[开发前定稿记录](../audits/PREDEV_SEVEN_CORE_FINALIZATION_2026-10-20.md)汇总 `current-3` 的费用、pilot、核源修正及实际离线验证；业务放行仍为 No-Go。

**本索引版本**：Gate 1 冻结版 `2026-10-18 / 0.3-APPROVED`（历史）

**0.4 历史版本说明（2026-10-18）**：[历史 SPEC](../../SPEC_0.4.md)、[历史计划](../../PLANS_0.4.md)、[开发前核验](../audits/PREDEV_BASELINE_2026-10-18.md)、[验证记录](../audits/PREDEV_VERIFICATION_2026-10-18.md)、[G2 评测协议](../evaluation/G2_EVAL_PROTOCOL.json)及[团队运行时 ADR](adr/0002-team-runtime.md)保留当时目标；不回写本目录 0.3 原始批准记录。

**本目录设计状态**：**APPROVED — Gate 1 design freeze，历史版本**。2026-10-18 用户另行授权 G2-00 工程配置与权威指针迁移；其余 Gate 2 业务任务、付费评测及发布未授权。

**代码审计基线**：主仓库 `dbacdc02fb119f70bc65a14608ab1bede75c0622`；子模块工作区清洁状态 **UNVERIFIED**。
**目标**：开发者自主技术选型调研与证据验证；开源项目发现为主，官方技术文档对比与 Release 研究为同一业务闭环的验收场景。

## 权威关系与批准记录

本目录是**已批准的 0.3 历史目标设计**，不是当前实现或当前目标。下述 Gate 2 路由描述 0.4 当时的授权时点，所指 [0.4 规格](../../SPEC_0.4.md)现为历史快照；当前路由见本文顶部与 [`AGENTS.md`](../../AGENTS.md)。现有行为以 [`V1_SPEC.md`](../specs/V1_SPEC.md) 和 [`V1_CONTRACTS.md`](../contracts/V1_CONTRACTS.md) 为准。[D7 交付报告](../audits/V1_DELIVERY_REPORT.md)、[UI 验收](../audits/V1_UI_ACCEPTANCE.json)和 r12 原件是不可改写的历史证据。`VERIFIED` 表示当前源码/记录可支持，`INFERRED` 表示有依据待验证，文中 `PROPOSED` 表示当时目标尚未实现，`UNVERIFIED` 表示证据不足。

| 版本 / 日期 | 内容 | 审批人 | 状态 |
|---|---|---|---|
| 0.1 / 2026-10-17 | Gate 0 审计、Gate 1 产品/架构/数据/测试/流程/路线图候选 | 待用户确认 | **Pending** |
| 0.2 / 2026-10-17 | 按深入复审修正事实拒绝、Provider 用量和安全验收；增加官方参考对照并拆分 NFR 测试 | 待用户确认 | **Pending** |
| 0.3 / 2026-10-18 | 冻结权威迁移、阶段用量、字段分母、泛化样本、故障/SSE 图及安全威胁；补明完整成功须 `completed/full`，G2-07..09 为 P0 放行依赖 | 用户明确回复“只批准冻结设计，暂不开发” | **APPROVED — design only** |
| 0.4 / 2026-10-18 | 逐次全字段与建议核源、公开泛化集、可信团队账户隔离、同机 Worker、内网 HTTPS、异机备份及约 120 小时计划 | 用户明确回复“批准 0.4 并切换权威指针” | **APPROVED — historical target, unimplemented** |
| 0.5 / 2026-10-18 | 五人局域网、LangGraph/PostgreSQL、一次恢复、O01–O03、十五次正式尝试 | 用户明确要求实施当时开发前准备计划 | **ARCHIVED TARGET — design only, unimplemented** |

用户当时仅批准本版的产品、架构、范围、数据、测试与工程配置**设计**。2026-10-18 的新请求单独授权 G2-00 的配置和 V1 前瞻指针，不授权业务代码、付费模型测试、提交、推送、PR 或部署。冻结后的实质设计变更应创建新版本和变更记录，不在 0.3 上静默改写门槛。当前业务仍为 No-Go。

本目录其他 0.3 文档中的“G2-00 尚未授权/迁移前”及“本轮只修改设计文档”是 Gate 1 冻结时的历史时点陈述；G2-00 的当前执行状态以本索引和实际配置 Diff 为准。这一状态更新不改变目标数据/API 契约，也不将其他 G2 任务视为已授权。

### Gate 1 决策审批表（冻结时记录）

| 决策 | 推荐方案 | 备选方案 | 理由 | 状态 |
|---|---|---|---|---|
| 产品定位 | 开发者技术选型调研为主，官方文档/Release 为另外两类场景 | 通用无边界研究 Agent；只做版本查询 | 三类业务共享证据研究闭环 | 设计批准；未实施 |
| 架构 | 单进程模块化单体定点优化（方案 A） | 独立 Worker（B）；LangGraph 重构（C） | 保留现有单进程边界 | 设计批准；未实施 |
| 功能范围 | FR-001..007 Must；FR-008 Should；复杂基础设施 Deferred | 同时加入模板、RAG、MCP 等 | 六路 API、六状态、SQLite 和三场景保持不变 | 设计批准；未实施 |
| 数据契约 | 保留六路 API/四表；既有事件可选请求阶段用量与步骤级拒绝摘要；已知 Token 下界与未知调用分开 | 新 API/新表或完整事件溯源 | 最小兼容扩展，保护历史 SQLite | 设计批准；未实施 |
| 测试验收 | B01–B03 每题三次至少两次完整成功、至少 68/75 字段；独立 G01–G03 至少 2/3；实质结论来源追溯和准确 100% | 降低样本/覆盖门槛；全面扩大任务集 | 同时验证回归和少量泛化，全部十二次保留 | 设计批准；未执行 |
| Codex 工程配置 | 复用现有 CI；获实施授权后补简短指令及按需模板；技能/MCP 按需 | 新建全套配置与多代理体系 | 现有离线门禁可复用 | 设计批准；配置未修改 |

## 文档地图

| 文件 | 内容与关系 | 状态 |
|---|---|---|
| [01 产品需求](01_PRODUCT_REQUIREMENTS.md) | 三类业务比较、FR/NFR、用户旅程、UI 行为、验收 | APPROVED 设计 |
| [02 系统架构](02_SYSTEM_ARCHITECTURE.md) | 当前/目标架构、方案 A/B/C、四张 Mermaid 图 | APPROVED 设计 |
| [03 数据流与状态](03_DATA_FLOW_AND_STATE.md) | 六张 DFD、任务状态机、取消/恢复/Token 链 | APPROVED 设计 |
| [04 数据与 API](04_DATA_AND_API_CONTRACTS.md) | 域/DTO/ORM、ER、六路 API、事务与兼容 | APPROVED 设计 |
| [05 测试与评测](05_TEST_AND_EVALUATION.md) | 测试矩阵、新版真实评测设计、证据口径 | APPROVED 设计 |
| [06 验收与发布](06_ACCEPTANCE_AND_RELEASE.md) | 工程、业务和质量三层门槛及 Go/No-Go | APPROVED 设计 |
| [07 AI Coding 流程](07_AI_CODING_WORKFLOW.md) | Codex/CI/PR/Review 审计与三档执行规则 | APPROVED 设计；G2-00 配置已授权 |
| [08 实施路线图](08_IMPLEMENTATION_ROADMAP.md) | 四周约 57 小时的 G2-00..09 小任务卡 | APPROVED 设计；仅 G2-00 配置获执行授权 |
| [09 双向追踪矩阵](09_TRACEABILITY_MATRIX.md) | FR/NFR→设计→代码/接口→测试→验收 | APPROVED 设计 |
| [10 当前状态审计](10_CURRENT_STATE_AUDIT.md) | Gate 0 能力、调用链、风险、r12 症状和开源对照 | APPROVED 审计记录 |
| [ADR-0001](adr/0001-target-architecture.md) | 唯一目标架构及备选、代价、冻结决定 | APPROVED 设计 |
| [11 设计复审](11_DESIGN_REVIEW.md) | 多轮复审发现、修正、剩余实施风险 | APPROVED 审查记录 |
| [12 高 Star 官方项目研究](12_REFERENCE_RESEARCH.md) | 五个官方项目的具体源码/文档、适用方式及证据限制 | APPROVED 参考记录 |

图形入口：[System Context、Container、Component、Module Dependency](02_SYSTEM_ARCHITECTURE.md#2-图-1system-context)；[研究主链路、单轮 Loop、SSE、失败、事实、Token、状态机](03_DATA_FLOW_AND_STATE.md)；[ER 图](04_DATA_AND_API_CONTRACTS.md#2-er-图verified-当前四表)。所有图是 GitHub Markdown Mermaid，不依赖外部设计工具。

## 与冻结 V1 的差异

| 项 | 当前 V1 | 已冻结 Gate 1 目标设计 |
|---|---|---|
| 项目目标 | 7–10 天展示 Agent 基础与可复现 benchmark | 四周定点提升真实业务成功率和可证明证据链；不修改历史评价 |
| 定位 | 通用研究型 Agent | 开发者技术选型调研为主，文档/版本研究为两类验收 |
| 诊断 | 已报告总 Token、状态、step trace | **PROPOSED** 在既有三类事件中增加安全的 `usage_by_stage` 可选字段；`step_evaluated` 增步骤级拒绝摘要；完整 Token 缺失时显示未知 |
| UI | 目标、状态、时间线、报告、近期任务 | 证据卡、失败与用量诊断；Markdown 导出/模板低优先级 |
| 放行 | V1 要求 3–5 代表任务可靠完成；D7 No-Go | 新版 B01–B03 每题三次至少两次完整成功、至少 68/75 字段；另设 G01–G03 留出任务至少 2/3，来源核验与各组覆盖独立统计 |
| 基础设施 | 单进程、SQLite、无 checkpoint | 保持；不增加 Worker/Redis/LangGraph/迁移框架 |

**G2-00 配置迁移（2026-10-18）**：本轮在 [`AGENTS.md`](../../AGENTS.md) 加入版本路由，并在 [V1 Spec](../specs/V1_SPEC.md)、[V1 Contracts](../contracts/V1_CONTRACTS.md)及[现有测试矩阵](../testing/V1_TEST_MATRIX.md)添加有日期的前瞻指针；执行流程见[07](07_AI_CODING_WORKFLOW.md)。历史 V1 正文、[V1_TASKS](../tasks/V1_TASKS.md)、D7 验收、r12 原始 JSON/计分和旧审计保持不变。这只完成权威路由和开发流程配置；影响 Agent/API/事件的后续 G2 行为修改仍须对应 Task ID 的执行授权、兼容测试和单独验收。

## Gate 1 设计冻结时的执行限制（历史记录）

仅设计文档与图发生变化。未修改 `adaptive_agent/`、`backend/`、`frontend/`、`benchmark/`、`browser-use/`、CI/Codex 配置、Lockfile 或 SQLite；未运行有费用的模型测试，也未提交、推送、建 PR 或部署。现有真实任务完成率为零，不能称业务已可交付。最终批准表和复审结论见 [06](06_ACCEPTANCE_AND_RELEASE.md)与[11](11_DESIGN_REVIEW.md)。
