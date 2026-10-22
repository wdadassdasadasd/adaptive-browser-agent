# Gate 0 现状审计与风险登记

状态：**APPROVED（审计记录）** · 审计基线：`dbacdc02fb119f70bc65a14608ab1bede75c0622`（2026-10-17） · 范围：当前 checkout；不表示当前业务可交付

本文件的 `VERIFIED` 仅表示已查到相应源码、配置或保存的运行记录；不表示本轮重新运行通过。`INFERRED` 是待调用级验证的机制假设，`PROPOSED` 是尚未实现的建议，`UNVERIFIED` 表示证据不足。冻结的 [V1 Spec](../specs/V1_SPEC.md)、[契约](../contracts/V1_CONTRACTS.md)和[交付报告](../audits/V1_DELIVERY_REPORT.md)保持原样。

## 1. 审计边界与能力清单

- **VERIFIED（设计文件创建前的 Gate 0 快照）** 主仓库 HEAD 为 `dbacdc02`、分支 `main`；当时 `git status --short --branch --ignore-submodules=all` 显示无主仓库改动。现有 `docs/design/` 为本任务新增的未跟踪设计文件，不能再将当前工作区称为无改动。完整 `git status` 访问 `.git/modules/browser-use` 被拒，子模块清洁状态 **UNVERIFIED**。目标设计仅引用本地适配器源码与锁定 gitlink，不改上游。
- **VERIFIED** Vue [App.vue](../../frontend/src/App.vue) 从 [api.ts](../../frontend/src/api.ts) 使用六路 API，显示目标、近期任务、状态、时间线与报告；尚无独立证据卡、分阶段 Token/失败诊断视图。
- **VERIFIED** [FastAPI 路由](../../backend/api/research.py) 经 `ResearchService` 到进程内 [TaskManager](../../adaptive_agent/runtime/task_manager.py)，任务经 [AgentLoop](../../adaptive_agent/agent_loop.py) 调用 Planner、ContextManager、ToolRouter、Evaluator、StateReducer 和 Reporter。GitHub HTTP 工具及 browser-use 只在工具/适配器边界接入；静态导入检查未见 `adaptive_agent → backend` 反向导入。
- **VERIFIED** [ResearchState](../../adaptive_agent/state.py) 为可序列化领域状态；[事件](../../adaptive_agent/events.py)经 [Reducer](../../adaptive_agent/state_reducer.py) 应用。SQLite 四表、异步 Session、任务/步骤/事实/轨迹写入见 [ORM](../../backend/db/models.py)与[持久化](../../backend/services/persistence.py)。`task_finished` 与终态任务状态同事务，SSE 从数据库补读、内存队列仅唤醒。
- **VERIFIED** AgentLoop 有步数、时间、Token、无进展和取消停止条件，DeepSeek 有一次技术请求重试与单次结构化修复；浏览器适配器关闭资源并使动作后的旧观察失效。相关行为有 fake/provider 集成与单元测试，但这些测试不证明真实任务完成。
- **VERIFIED** [CI](../../.github/workflows/ci.yml) 已含 Python 3.12/3.13、`uv --locked`、Ruff、pytest、编译检查及前端 Node 22 的安装、类型检查、测试、构建。当前远端 Actions 结果 **UNVERIFIED**。

## 2. 源码确认的运行链路

1. `App.vue` 的 `start()` 调 `POST /api/research`；[ResearchService.create](../../backend/services/research.py)先持久化任务与 `task_queued`，再交 `TaskManager.submit`。缺 DeepSeek key 时返回 503，不创建任务。
2. 管理器获取最多两个并发槽后执行 `ResearchService._execute`；AgentLoop 构造 provider、Planner、Evaluator、Reporter，发 `task_started`、初始化子目标，然后每轮观察、构造上下文、计划、执行、评估并发 `step_evaluated`。
3. `ResearchService` 的事件回调先让 `PersistenceService.record_event` 提交数据，再调用 `TaskManager.publish`。`step_evaluated` 的 step、已准入事实和 trace 同事务；发布到订阅者的队列仅表示“有新数据”。
4. `GET /events` 先订阅唤醒队列，再按数据库 trace ID 补读；`Last-Event-ID` 映射为持久化游标，未知 ID 返回 422；终态 `task_finished` 后关闭流，断线时移除单个订阅者。前端 `EventSource`、状态轮询和 trace 重载用于重连与去重。
5. AgentLoop 生成带来源报告并发一次终态事件；取消中的 queued 任务可直接事务性终结，running 任务使用软取消。服务重启对存量 queued/running 按有无事实标为 partial/failed，`stop_reason=server_restart`，不恢复执行。

## 3. r12 真实失败：症状与调查顺序

[r12 原始汇总](../../data/benchmark/20261016T152251931497Z-3de75ed5/summary.json)与 [D7 报告](../audits/V1_DELIVERY_REPORT.md)显示：B01–B03 × baseline/full/browser-only × 两次共 18 次真实尝试，三组完整完成率均为 **0%**；full 字段覆盖平均 13.3%，browser-only/baseline 为 0%。另三次 [UI 验收](../audits/V1_UI_ACCEPTANCE.json)均未完成且没有合格引用报告：B01/B02 为 `token_budget`，B03 为 `no_progress`。baseline 六次用量缺失、`budget_parity=mismatched`；更少步数来自早停，不能声称效率提升。两次重复不支持显著性结论。上述是 **VERIFIED 记录结果**，不是本轮重跑。

| 级别 / 状态 | 证据及当前行为 | 风险与候选原因 | Gate 2 建议及验证 |
|---|---|---|---|
| P0 · VERIFIED 代码、INFERRED 成本影响 | [AgentLoop:266](../../adaptive_agent/agent_loop.py#L266) 已建上下文，[Planner:62](../../adaptive_agent/planner.py#L62)再从相同状态和观察构造并拼接 | 同轮状态/观察可能重复进入 prompt；r12 的实际 Token 增量未归因 | 先记录每调用的阶段、输入长度、用量与修复次数；对同一冻结输入比较去重前后 prompt 和决策质量 |
| P0 · VERIFIED 规则、INFERRED 误拒 | [Evaluator:127](../../adaptive_agent/evaluator.py#L127)采用证据字符串和来源 URL 严格匹配 | 合法改写、页面片段变化可能丢失事实，进而导致子目标无进展；不能直接归咎 r12 | 从失败 trace 抽取候选事实/原始观察重放，按真实支持/误拒/无来源分类；先写回归再调整 |
| P0 · VERIFIED 症状 | [AgentLoop](../../adaptive_agent/agent_loop.py)聚合用量；[ResearchState](../../adaptive_agent/state.py#L136)只留总 prompt/completion Token | 缺分阶段和修复调用成本，无法定位预算消耗 | 设计安全、受限的事件元数据；逐轮记录初始化/规划/评估/修复/报告用量与耗时，不写 prompt、密钥或完整网页 |
| P1 · VERIFIED 实现 | [API _response](../../backend/api/research.py#L27)逐任务读完整 trace；列表最多 50 条 | trace 增长时列表读放大；当前没有性能测量 | 在明确慢查询证据后，只取每任务最新终态 trace，保持响应形状不变；加列表规模基准 |
| P1 · VERIFIED 实现 | [Persistence](../../backend/services/persistence.py#L322)按任务扫描 trace 找事件 UUID | SSE 重连游标查询可能随历史增长 | 以大任务 trace 数据测量后决定索引/辅助列；变更前先保护历史 SQLite |
| P1 · VERIFIED 实现 | [ORM](../../backend/db/models.py#L25)有 `error_message`，终态写入未填它 | UI 错误解释主要依赖 stop_reason/报告，技术失败详情不足 | 定义脱敏失败分类与诊断字段；测试异常、取消、报告失败及重启 |
| 安全阻断 · VERIFIED 前后检查、INFERRED 窗口 | [BrowserUseAdapter](../../adaptive_agent/adapters/browser_use_adapter.py#L309)校验目标 DNS，并在导航后检查最终 URL | 重定向目标可能在事后检查前被请求；未证明网络隔离 | 本机受控重定向/私有地址烟测与外呼阻断验证前，维持可信本机演示，不开放公网 |
| P1 · VERIFIED 契约 | `POST /api/research` 每次重试会创建新任务；仅取消与终态写入幂等 | 客户端断线重试可能生成重复任务 | 先决定是否有真实重复创建痛点；若需要幂等键，另列兼容 API 提案与测试，不在当前设计中假装已有 |

## 4. 保留、修复、替换、删除、暂缓建议

| 决策 | 模块 | 理由 |
|---|---|---|
| 保留 | AgentLoop、StateReducer、TaskManager、ResearchService、PersistenceService、六路 API、SQLite/SSE | 职责和基本事务边界已形成；当前失败不构成全面重写证据 |
| 定点修复 | Planner 上下文、Evaluator 证据准入、预算诊断、报告失败解释和必要查询性能 | 与真实 No-Go 症状关联，需先取得调用级证据 |
| 可替换边界保留 | DeepSeek Provider、ToolRouter、BrowserUseAdapter | 用现有接口注入 fake 测试；不在 Gate 1 更换提供方或上游 |
| 删除 | **本轮无已证实应删除的生产模块** | 未使用模块或重复逻辑需实际引用分析和回归证据，不能凭文件名删除 |
| 暂缓 | 独立 Worker、LangGraph、RAG、MCP、向量库、数据库迁移、公开部署 | 现有 P0 是真实任务成功与证据完整性；新增基础设施不能替代根因修复 |

## 5. 设计约束

现行 V1 规范仍是当前行为契约。Gate 1 新要求已作为目标设计冻结，但代码尚未实现；G2-00 另获执行授权后，才以单独小改动为 [Spec](../specs/V1_SPEC.md)、[Contracts](../contracts/V1_CONTRACTS.md)和[测试矩阵](../testing/V1_TEST_MATRIX.md)添加版本指针，历史 D7 审计与原始记录不改。总开发能力按四周 40–60 小时；优先保证真实 B01–B03 闭环。模型费用需另行授权。所有公网安全与远端 CI、分支保护结论在获得实证前保持 `UNVERIFIED`。

## 6. 外部项目对照（截至本次查阅）

| 参考项目 → 具体来源 | 优点 | 是否适用与采用方式 | 不采用部分 |
|---|---|---|---|
| [browser-use Python Agent/Tools](https://github.com/browser-use/browser-use) | 浏览器动作、工具注册与会话运行 | 适用；维持其作为浏览器执行设施，本项目通过 Adapter 接入 | 不将研究状态和业务报告迁入上游 |
| [Skyvern Tasks/Workflows](https://github.com/Skyvern-AI/skyvern) | 区分单次任务和组合流程，能展示任务终态 | 部分适用；借鉴任务生命周期和用户可见失败解释 | 不引入其服务化/视觉工作流栈 |
| [Stagehand observe/act/extract](https://github.com/browserbase/stagehand) | 观察、动作、结构化提取边界明确 | 部分适用；审视现有 BrowserUseAdapter 的观察新鲜度与提取结果 | 不替换 browser-use 或增加第二套浏览器 SDK |
| [LangGraph durable execution](https://docs.langchain.com/oss/javascript/langgraph/thinking-in-langgraph) | 节点级 checkpoint 和恢复模型清晰 | 仅参考状态/恢复语义作方案 C 比较 | 当前无断点续跑需求，不重构运行时 |
| [Dify 工作流运行日志](https://docs.dify.ai/en/guides/application-orchestrate/creating-an-application) | 节点调试与结果可见 | 借鉴执行诊断视图，展示真实事件和失败原因 | 不引入可视化编排平台、RAG 或其部署栈 |

上表是第一轮高层对照；五个项目的当前官方源码/文档、锁定 browser-use commit、用量与安全边界的第二轮核对见[详细参考研究](12_REFERENCE_RESEARCH.md)。外部页面反映查阅时的公开版本，不等于本仓库锁定 `browser-use` 子模块的 API；适配器契约仍须依据 checkout 本地源码与测试核对。
