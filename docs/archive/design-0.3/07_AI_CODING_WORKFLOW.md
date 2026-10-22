# AI Coding 工作流与工程配置审计

> 状态：**APPROVED（Gate 1 设计）** · 冻结版 0.3。2026-10-18 的 G2-00 授权使本文的任务路由和开发流程成为本机 Codex 工作规则；其余 Gate 2 业务实施、付费评测及外部 GitHub 设置仍需各自授权。

> **2026-10-19 现行路由**：执行新任务只读[现行规格](../../SPEC.md)、[计划](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)和[评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)的相关部分。下方配置矩阵是 0.3 冻结时点快照，原文关于 Skill、模板、旧 `AGENTS.md` 行号和版本的说法不代表当前工作区。[此前目标](../archive/target-2026-10-18/SPEC.md)与 0.4 规格/计划均归档。本文件的风险分级流程仍可用；业务实施、依赖安装、付费评测与部署各需授权。

## 1. 审计边界与证据

以下矩阵保留 Gate 1 冻结时的审计快照；当前迁移结果以本文件后续执行规则、[设计索引](00_DESIGN_INDEX.md)和本轮实际 Diff/验证报告为准。`VERIFIED` 表示直接读取当前 checkout 或执行无副作用命令；`UNVERIFIED` 表示不能从本机文件推断。`codex --version` 曾返回 `codex-cli 0.155.1`，但桌面应用版本、远端 CI、GitHub 分支保护和用户级配置的生效合并结果仍 **UNVERIFIED**。审计没有记录密钥值。Codex 配置与 `AGENTS.md` 的规则依据[官方配置说明](https://learn.chatgpt.com/docs/config-file/config-basic)、[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)和[AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

| 配置项 | 当前证据与状态 | 作用 | 实际缺口 | 必需性与建议 | 验证方法 |
|---|---|---|---|---|---|
| 仓库 `AGENTS.md` | **VERIFIED**：已有 V1 权威来源、模块边界、状态、回归测试、`browser-use` 限制、禁止自动提交等规则（`AGENTS.md:16-124`） | 为代理提供仓库规则 | 获批目标设计与 V1 现行权威的生效范围尚未说明 | **G2-00 必需**：只补简短版本规则和对应 V1 前瞻指针，范围见[索引](00_DESIGN_INDEX.md)；不重复现有开发规范 | 新会话核对加载的指令；人工对照索引与 V1 附录 |
| 用户级 Codex 配置 | **VERIFIED**：`~/.codex/config.toml` 可读取，存在 `model`、`model_reasoning_effort` 和 MCP 表；未输出值。生效权限仍 **UNVERIFIED** | 用户个人默认设置 | 无可证明的项目缺口 | **不修改**；不把未出现的键解释为缺失或弱安全性 | 用户自行检查有效配置与当前会话权限 |
| 项目 `.codex/config.toml` | **VERIFIED**：当前不存在 | 可为可信项目覆盖部分用户配置 | 本项目无必须覆盖的 Codex 设置 | **不新建**；不在仓库强制模型、权限、MCP 或审批字段 | 若未来提出具体配置，先对照官方参考和有效权限，再新会话测试 |
| Skills | **VERIFIED**：仓库 `.agents/skills/` 不存在；当前会话提供系统及已安装通用技能。用户级技能全量清单 **UNVERIFIED** | 重复流程复用 | 尚无反复执行且稳定的专用流程证据 | **不新增**；候选条件见 §5 | 两次以上同型任务后评估复用收益，人工检查输出 |
| MCP | **VERIFIED**：用户配置有 MCP 表；服务名、权限及可用性未审计。项目无 MCP 配置 | 外部数据或工具接入 | Gate 2 本地开发无必需 MCP | **不新增项目 MCP**；官方文档可用网页核验，GitHub 设置仍需单独授权 | 具体任务再检查所需工具、权限和最小范围 |
| `.codex-workflow/` | **VERIFIED**：已有 2026-10-05 初始化及 2026-10-08 Day 01 的 brief、review、verification、evidence 记录 | 历史开发证据 | 不是自动执行的当前质量门禁；旧交付结论不代表当前 V1 可交付 | **保留引用**；后续按 Task ID 写新证据，不改写历史记录 | 核对每项声称与原始命令输出、时间及 commit 对应 |
| Python 工具链 | **VERIFIED**：`pyproject.toml:6,19-24,36-40` 为 Python `>=3.12,<3.14`、uv 开发依赖、默认排除 browser smoke；`uv.lock` 存在 | 锁定环境与选择测试 | 无直接配置缺口 | **复用**；本机用 `uv sync --locked --dev`，检查用 `uv run --offline --locked`（缓存允许时） | `uv lock --check --offline`；Ruff、pytest 实际输出 |
| 前端工具链 | **VERIFIED**：`frontend/package.json` 有 `type-check`、`test`、`build`，`package-lock.json` 存在 | 类型、交互和构建检查 | 无直接配置缺口 | **复用** `npm ci --prefix frontend` 及三项脚本 | 保存命令退出码和摘要 |
| GitHub Actions | **VERIFIED**：`.github/workflows/ci.yml:3-61` 在 push/PR 运行 Python 3.12/3.13、uv 锁定安装、配置、Ruff、compileall、离线 pytest，以及 Node 22 的 `npm ci`、类型检查、构建、测试；顶层 `contents: read` | PR 基础门禁 | 未自动运行 opt-in browser smoke；远端 CI 成败 **UNVERIFIED** | **现有离线 CI 必需且足够保留**；browser smoke 用受控环境手动/按需触发，不将付费真实 benchmark 加入每个 PR | 在实际 PR 中读取两项 Job 结果；另记录受控 smoke 环境输出 |
| PR / Bug 模板 | **VERIFIED**：`.github/PULL_REQUEST_TEMPLATE.md`、`.github/ISSUE_TEMPLATE/` 不存在 | 提醒范围、证据、风险、验收 ID | 交付记录格式不统一 | **后续实施授权后可选**最小模板，见 §6；不是运行时阻断 | 用试验 PR/Issue 确认模板呈现并检查必填信息 |
| 密钥与本地数据 | **VERIFIED**：`.env.example:2-9` 为留空凭据示例；`.gitignore:1,13-17` 忽略 `.env`、SQLite 和 benchmark 数据 | 避免误提交 | 不能仅凭 ignore 证明历史无泄漏；公网安全防线未通过 | **维持可信本机边界**；PR 检查 staged diff 的密钥与数据，不将 `.env` 作为 CI 输入 | `git diff --cached --check`、精确文件审查及必要的仓库密钥扫描 |
| 分支、Review、保护规则 | **VERIFIED**：仓库规则禁止自动 commit，要求有证据的 Review；远端保护和 Required Checks **UNVERIFIED** | 控制变更合入 | 无法从本地认定远端设置 | **建议**将现有两个 CI Job 设为 Required Checks、要求至少一次 Review；实际设置需用户授权 | 授权后在 GitHub 仓库设置页核验，不在本文声称已设置 |

当前 CI 的成功只能通过实际 GitHub run 证明；本次读取 YAML 不等于运行通过。`pyproject.toml`、lockfile、CI 和用户配置均未改动。浏览器 smoke 默认由 pytest marker 排除，真实 benchmark 不属于离线 CI。

## 2. 按风险选择开发闭环

先按变更可能触及的契约和失败后果分类，以最高风险级别为准；只读诊断可停在 Evidence 和 Plan。简单任务不强制创建单独计划文件，已有 `.codex-workflow/lifecycle/` 只作可复用的历史记录格式。

| 级别 | 触发条件 | 最小流程与产物 |
|---|---|---|
| Level 1 | 文档、注释、小 UI 调整或不改变 API/状态契约的明确局部 Bug | `Inspect → Edit → Focused Test → Diff Review → Deliver`；在交付中记录范围、实际检查与风险 |
| Level 2 | 普通功能、跨模块 Bug、Planner/Evaluator、FastAPI、Vue 业务、SSE 或工具集成行为 | `Issue → Evidence → Plan → Test → Implement → Review → Verify → Acceptance`；记录 Task/Requirement ID、影响模块、变更、测试证据和未解决风险 |
| Level 3 | AgentLoop 停止行为、ResearchState/AgentEvent、SQLite 事务、并发/取消、Benchmark 评分、安全或架构变更 | `Design Impact → Approval Gate → Plan → Regression Tests → Implement → Independent Review → Integration/E2E → Acceptance`；先记录兼容性/数据流影响，必要时 ADR；第二遍独立视角审查实际 Diff，不强制使用子代理 |

Level 2/3 的共同执行步骤：

1. **Issue**：写明 FR/NFR、用户影响、现状、完成标准和范围；故障包含可复现输入与实际输出。
2. **Evidence**：读取相关源码、现行契约、日志、测试和真实记录。标注 `VERIFIED / INFERRED / PROPOSED`；不把历史设计、Mock 或未运行的检查当作真实成功。
3. **Design / Plan**：确定最小变更、模块责任、输入输出、失败模式、依赖、回滚与小 PR 边界。架构或冻结契约改变先分析影响、取得批准，必要时写 ADR。
4. **Test**：行为变更先加能复现故障或证明需求的最小测试；重点覆盖状态非法转换、结构化输出、预算、证据链、取消竞态、持久化和 SSE 补读。避免镜像实现的无效测试。
5. **Implement**：只修改批准的 Task ID 范围，保护工作区和 `browser-use` 子模块；浏览器会话、异步任务与数据库连接的所有权写清楚。
6. **Review**：针对确定的 diff 核查正确性、数据一致性、异步资源、安全、架构、回归、兼容与成本；引用文件与行号。Level 3 至少进行与实现过程分开的第二遍审查。独立只读角色仅在有效权限可验证时用于隔离；否则由主代理重新审查，不声称隔离。发现问题先核实再修复。
7. **Verify**：运行受影响的最小充分检查，报告命令、退出码、结果与未运行项。普通 PR 跑离线检查；浏览器变化加本地可控页面 smoke；真实模型评测另经费用授权，保留全部尝试。
8. **Acceptance**：按需求 ID、实际测试与证据判定 `PLANNED`、`IMPLEMENTED_UNVERIFIED`、`VERIFIED`、`BLOCKED` 或 `FAILED_ACCEPTANCE`。实现完成不自动成为已验收。PR 写目的、行为、风险、回滚与未验证项；提交、推送、建 PR、合并与部署另按授权执行。

### 按修改范围加载上下文

先查[现行规格](../../SPEC.md)、[计划](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)和[评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)的相关部分，再读当前源码与测试；V1 未被授权任务替代的部分仍读相应 [Spec](../specs/V1_SPEC.md) 与 [Contracts](../contracts/V1_CONTRACTS.md)。下表属于 0.3 历史设计的审查线索，不能代替现行要求，也不要求每次运行所有检查。

| 修改范围 | 目标设计与当前契约 | 优先检查 |
|---|---|---|
| AgentLoop / Planner / ContextManager | [02 架构](02_SYSTEM_ARCHITECTURE.md)、[03 Loop 与 Token](03_DATA_FLOW_AND_STATE.md)、[04 契约](04_DATA_AND_API_CONTRACTS.md) | 预算、裁剪、重复调用、无进展、停止、取消与超时 |
| Evaluator / ResearchFact | [01 事实需求](01_PRODUCT_REQUIREMENTS.md)、[03 事实链](03_DATA_FLOW_AND_STATE.md)、[04 事实契约](04_DATA_AND_API_CONTRACTS.md) | 来源、拒绝原因、主体归属、去重、状态一致性 |
| StateReducer / Persistence | [03 状态机](03_DATA_FLOW_AND_STATE.md)、[04 事务契约](04_DATA_AND_API_CONTRACTS.md) | 事件合法性、唯一终态、原子写入、重启与旧数据 |
| TaskManager / SSE | [03 事件与失败流](03_DATA_FLOW_AND_STATE.md)、[04 HTTP/SSE](04_DATA_AND_API_CONTRACTS.md) | 并发、取消竞态、补读、重连、终态通知和清理 |
| BrowserUseAdapter / ToolRouter | [02 边界](02_SYSTEM_ARCHITECTURE.md)、[04 工具契约](04_DATA_AND_API_CONTRACTS.md)、当前检出的 `browser-use` API | 动作参数、URL/不可信页面、浏览器所有权和有界失败 |
| Vue | [01 UI 需求](01_PRODUCT_REQUIREMENTS.md)、[04 API](04_DATA_AND_API_CONTRACTS.md)、相关前端组件/测试 | API 映射、SSE 生命周期、错误/部分状态、取消、未知用量 |
| Benchmark | [旧协议](../benchmark/BENCHMARK_PROTOCOL.md)、[05 新评测](05_TEST_AND_EVALUATION.md)、[06 验收](06_ACCEPTANCE_AND_RELEASE.md)、历史记录与 Runner | 样本隔离、分母、来源、复算；Agent Bug 不靠放宽评分修复 |

### 按影响选择测试

| 变更 | 最低验证 |
|---|---|
| 文档/配置 | 解析、相对链接、实际 Diff 与范围 |
| Python 局部行为 | 定向 pytest 与 Ruff；行为变化需有意义的回归 |
| 状态 / API / SQLite | 状态单测及相关 AgentLoop、API、Persistence 集成 |
| Tool / Adapter | Fake/Mock 测试；浏览器变化按需运行受控本地 smoke |
| Vue | Type Check、相关 Vitest、Build |
| 高风险跨模块 | 完整离线检查、对应集成/E2E 和第二遍 Diff Review |
| 正式 Agent Eval | 单独费用与协议授权；固定版本、全部真实尝试和核源证据 |

可复用的本机命令与 CI 对齐：

```powershell
uv lock --check --offline
uv run --offline --locked ruff check adaptive_agent backend benchmark tests
uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests
uv run --offline --locked pytest -q
npm run type-check --prefix frontend
npm run test --prefix frontend
npm run build --prefix frontend
```

运行前须先有锁定依赖与前端依赖；离线命令是否可执行取决于缓存。额外验证仅按影响范围加入，不能把未运行的命令列为通过。CLI 版本只证明当前 `codex-cli`，不推导桌面客户端能力。[Codex 配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)列有权限设置，但当前会话的实际批准与沙盒由运行环境控制，不能靠文档片段证明已生效。

## 3. Review 与验收记录格式

每项 Review 结论记录：`Review ID、Git 基线/明确路径、差异指纹、要求、发现及文件行号、严重级别、核实结果、修复或接受的风险`。按 `BLOCKER / HIGH / MEDIUM / LOW` 排序；真实发现须写触发条件、影响、修复建议和验证方式，避免纯样式意见。不得把审查角色名当成只读权限证明。若隔离审查无法读取 Git 元数据，应由主代理提供 scoped diff、基线 commit/blob ID、SHA-256、验收标准与实际测试输出；资料不足标 `NEEDS_CONTEXT`。

每项验证记录：`Task ID、Requirement ID、命令/环境、退出码、实际结果、证据位置、跳过原因、残余风险`。只有真实运行的业务任务与来源核验可以支持业务成功声明；Mock 测试支持代码行为，不支持真实任务完成率。CI、人工 Review 和用户 Acceptance 各自独立记录。

Level 2/3 的 `VERIFIED` 要求：需求或故障明确、范围符合授权、架构/数据契约保持一致或已获批准、关键异常路径有覆盖、适用测试实际通过、Review 无未解决阻断问题、敏感信息未进入 Diff，且验收证据支持结论。缺一项则标 `IMPLEMENTED_UNVERIFIED`、`BLOCKED` 或 `FAILED_ACCEPTANCE` 并说明原因。交付同时列出修改文件、验证命令、Review 发现、残留风险与回滚方式。

## 4. 常驻规则与版本指针

根 [`AGENTS.md`](../../AGENTS.md) 只保留稳定的现行入口、架构边界、安全和交付要求；本文件的历史配置矩阵不定义当前目标。[索引](00_DESIGN_INDEX.md)记录设计版本与归档关系。[官方 AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)支持根与嵌套指令，本项目当前无需嵌套文件。

## 5. Skills 决策

先复用当前会话已有的诊断、TDD、Research、Code Review、OpenAI Docs 等通用 Skills；仓库级 Skill 不是本轮交付。若后续出现重复且稳定的工作，再按[官方 Skills 格式](https://learn.chatgpt.com/docs/build-skills)提出独立 Task ID：

| 候选 | 触发与输入 | 预期步骤与输出 | 验证及边界 | 决策 |
|---|---|---|---|---|
| `agent-failure-analysis` | 两次以上同型真实任务失败；输入为 task ID、trace、事件、模型用量、源码版本 | 对齐调用时间线、分类症状与候选根因，输出证据表和可复现实验 | 源记录可回溯；不自动修复、不把相关性当因果 | 暂缓，先按本文人工执行 |
| `agent-eval` | 新版独立评测协议获批准且反复运行；输入为固定任务集、环境、预算与评分规则 | 保存每次尝试、核验来源、按指标汇总，不丢失败 | 原始记录、代码指纹和评分可复算；真实调用需费用授权 | 暂缓到评测协议稳定 |
| `project-delivery` | 多次正式交付重复遗漏；输入为批准基线、PR、CI、Eval、验收证据 | 生成交付核对清单与未验证项 | 人工逐项核对；不能替用户批准或发布 | 暂缓，不增流程复杂度 |

## 6. 模板与外部设置

本轮新增的 [PR 模板](../../.github/PULL_REQUEST_TEMPLATE.md)和[Bug 模板](../../.github/ISSUE_TEMPLATE/bug_report.md)只提示需求、行为、复现、实际验证与风险；不因模板存在而自动授权提交或外部写入。项目 `.codex/config.toml` 没有已证实的覆盖需求，不创建；用户级模型与权限不复制到仓库。Skills/MCP 保持按需，非开发闭环的必需条件。

GitHub 分支保护建议只在用户授权并确认仓库协作人数后设置：要求 `.github/workflows/ci.yml` 的 Python 与 frontend Job、至少一次人工 Review、禁止未通过检查合入。浏览器 smoke 和真实 benchmark 应有受控环境及显式触发；当前没有证据表明需要扩大 Actions 权限、添加 MCP、CI 密钥或复杂发布流水线。

