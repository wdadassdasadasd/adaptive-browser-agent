# 数据流、事件流与状态机

状态：**APPROVED（设计）** · 实施未授权 · 当前链路的事实证据见 [Gate 0](10_CURRENT_STATE_AUDIT.md) · 字段与路由以[契约核对](04_DATA_AND_API_CONTRACTS.md)为准。

图中实线标 `VERIFIED` 当前代码路径；明确写 `PROPOSED` 的字段/展示均尚未实现。每个图以括号指出数据所有者。六图不把 SQLite trace 当成事件溯源系统，也不把重启终结画成断点恢复。

## DFD-01：完整研究任务主链路

```mermaid
flowchart LR
  U["用户目标<br/>所有者: 用户"] --> V["Vue 表单"]
  V -->|goal 1..4000 字| API["POST /api/research<br/>FastAPI 校验"]
  API --> S["ResearchService"]
  S -->|task_queued + task row<br/>同事务| DB[("SQLite<br/>所有者: Persistence")]
  S --> M["TaskManager<br/>最多两个活动槽"]
  M --> L["AgentLoop<br/>ResearchState 所有者"]
  L --> P["Planner<br/>PlanDecision"]
  P --> T["ToolRouter<br/>ToolResult"]
  T --> E["Evaluator<br/>EvaluationResult"]
  E --> R["StateReducer<br/>ResearchState"]
  R -->|新 ResearchState| L
  L -->|AgentEvent 回调| S
  S -->|step/fact/trace 事务| DB
  L --> Report["Reporter<br/>ResearchReport"]
  Report -->|task_finished + 报告<br/>同事务| DB
  DB -->|GET /任务与轨迹| API
  API --> V
```

输入是目标文本；AgentLoop 持有 `ResearchState`，Reducer 返回新状态，AgentLoop 执行事件回调和后续 Reporter 调用；Persistence 独占 SQLite。`Reporter` 只使用已准入事实；报告保存于终态 trace JSON 并由 GET 重建。创建时持久化先于调度。**VERIFIED** 运行期异常由执行路径尝试终结；**PROPOSED** 提交调度在 queued 已提交之后若抛错，应补写真实终态，当前 `ResearchService.create` 没有本地补偿，须作回归测试。

## DFD-02：单轮 Agent Loop

```mermaid
flowchart TD
  O["Observe<br/>BrowserUseAdapter 新鲜页面观察<br/>异步 I/O"] --> C["Build Context<br/>状态 + 最多五条 trace<br/>当前视图 12000 字符"]
  C --> P["Plan<br/>DeepSeek 结构化调用<br/>异步 I/O"]
  P --> V{"Validate Decision<br/>子目标 / 工具动作 / 参数"}
  V -->|无效，一次纠正仍失败| F["标准化结构化失败<br/>不执行工具；终态处理"]
  V -->|有效| T["Execute Tool<br/>GitHub HTTP 或 browser-use<br/>异步 I/O"]
  T --> E["Evaluate<br/>技术检查后按需语义 LLM"]
  F --> Rep
  E --> R["Reduce State<br/>纯同步计算"]
  R --> PE["Persist Event<br/>AsyncSession 事务"]
  PE --> Stop{"Check Stop<br/>步数/时间/Token/取消/无进展/目标"}
  Stop -->|未停止；技术故障至多一次重试或语义失败重观察| O
  Stop -->|终止| Rep["Reporter + task_finished"]
```

当前 [AgentLoop](../../adaptive_agent/agent_loop.py#L254)在 Planner 前调用 ContextManager，[Planner](../../adaptive_agent/planner.py#L62)又构造并拼接上下文；这是 **VERIFIED 重复构造**，具体 Token 影响 **INFERRED**。每轮 `PlanDecision` 仅一个主动作；技术工具失败可有一次有界重试，语义/信息不足回到观察与重规划，不原样无限重试。`StateReducer` 不作 I/O；`ResearchService` 回调提交事件后才唤醒 SSE。

## DFD-03：事件持久化与 SSE

```mermaid
sequenceDiagram
  participant L as AgentLoop
  participant S as ResearchService
  participant P as PersistenceService
  participant DB as SQLite trace/task
  participant M as TaskManager 队列
  participant API as GET /events
  participant UI as EventSource
  UI->>API: 订阅，可带 Last-Event-ID
  API->>DB: 先查 Last-Event-ID 对应 trace 游标；未知返回 422
  API->>M: 生成器登记 maxsize=1 唤醒队列
  API->>DB: 按游标补读已提交事件
  DB-->>API: 已提交的有序事件
  API-->>UI: id/event/data SSE 帧
  L->>S: AgentEvent
  S->>P: record_event
  P->>DB: 事务写 step/fact/trace 与必要状态
  DB-->>P: commit
  P-->>S: 已持久化
  S->>M: publish 唤醒
  M-->>API: 有新数据
  API->>DB: 按 trace ID 补读
  DB-->>API: 新事件，包括 task_finished
  API-->>UI: SSE；终态后关闭
  UI--xAPI: 断线
  API->>M: finally 取消此订阅
```

`AgentEvent.event_id` 是公开 SSE ID；数据库 `agent_trace.id` 是补读游标，两者并不相同。内存队列不承载可靠消息，慢订阅者可重连补读；未知 `Last-Event-ID` 当前返回 422。断线只释放订阅，不取消任务。`task_finished` 与任务终态在一个数据库事务；终态流关闭不等于丢失历史。

## DFD-04：失败、取消与重启

```mermaid
flowchart TD
  X["当前步骤 / 任务"] --> Kind{"故障或停止条件"}
  Kind -->|网络、429、5xx| Retry["Provider 单次技术重试<br/>计入预算"]
  Retry -->|仍失败| ProviderEnd["LLMError → token_budget 或 execution_error<br/>终态处理，不进入 Evaluator"]
  Kind -->|工具失败 / 空结果| ToolRetry["工具技术故障至多一次重试"]
  ToolRetry --> Eval["Evaluator 评估 ToolResult"]
  Kind -->|目标不符 / 信息不足 / 无效动作| Reobserve["重新观察、评估、改计划<br/>不原样重复"]
  Eval --> Reobserve
  Reobserve --> Limit{"预算与无进展上限"}
  Limit -->|仍可继续| X
  Limit -->|步数、Token、时间或无进展耗尽| Terminal["有事实 partial<br/>无事实 failed"]
  Kind -->|用户取消| Cancel["queued 事务终结<br/>running 软取消并清理"]
  Cancel --> CEnd["cancelled + task_finished"]
  Kind -->|进程重启| Restart["启动时查 persisted queued/running"]
  Restart --> REnd["有事实 partial / 无事实 failed<br/>server_restart；不续跑"]
  Kind -->|未处理异常 / 清理失败| Error["failed + 脱敏原因"]
  Terminal --> Persist["终态事件与状态同事务"]
  ProviderEnd --> Persist
  CEnd --> Persist
  REnd --> Persist
  Error --> Persist
```

`AgentLoop` 的停止优先级与完整枚举沿用 [V1 Contracts](../contracts/V1_CONTRACTS.md)。`PROPOSED` 对每类技术失败记录可重复的诊断码；不要把所有 `execution_error` 归为外部网络问题。取消竞态要以终态不变和最多一个 `task_finished` 为验收，不保证取消瞬时完成。

## DFD-05：事实与报告数据链

```mermaid
flowchart LR
  TR["ToolResult<br/>content / source_url"] --> EV["候选 Evidence<br/>页面片段或 GitHub 响应"]
  EV --> RF["ResearchFact<br/>id/content/source_title/source_url<br/>可选 verbatim evidence/subject"]
  RF --> Val{"Evaluator<br/>来源观察与主体校验"}
  Val -->|证据拒绝| Diag["PROPOSED 步骤级数量与原因码<br/>不保存拒绝正文或入事实表"]
  Val -->|通过校验| Reducer{"StateReducer<br/>来源不变量与去重"}
  Reducer -->|重复| Ignore["不新增 fact<br/>不计入证据拒绝"]
  Reducer -->|新事实| State["ResearchState.facts"]
  State --> Rep["ResearchReport<br/>Finding.supporting_fact_ids<br/>source_urls"]
  State --> DB[("research_fact")]
  Diag -.-> StepTrace[("step_evaluated trace JSON")]
  Rep --> Trace[("task_finished trace JSON")]
  DB --> API["GET 任务 / traces"]
  Trace --> API
  StepTrace -.-> API
  API --> UI["报告 + 证据卡片<br/>PROPOSED UI"]
```

当前 `ToolResult` 未设单独 Evidence 模型；图中的“候选 Evidence”是工具返回内容/URL及可选 `ResearchFact.evidence` 的**逻辑节点**，不是新表。Evaluator 已核对片段与同次工具内容；目标版本聚焦真实误拒诊断、混合结果的步骤级拒绝数量/原因码及 Reducer 边界一致性，不把现有片段检查当作新增功能。历史缺片段时显示“未保存原文”。事实 ID、来源 URL 和最终 Finding 的 `supporting_fact_ids` 构成可追踪链；拒绝摘要不含候选正文、只进入 step trace，不进入事实表或报告。UI 证据卡只从准入事实与报告映射派生；不得伪造证据。

## DFD-06：LLM Token 与成本流

```mermaid
flowchart LR
  Init["Planner.initialize"] --> Meter["_MeteredProvider<br/>累计 prompt/completion"]
  Plan["Planner.next_step"] --> Meter
  Eval["Evaluator 语义调用"] --> Meter
  Repair["DeepSeek 结构化修复<br/>最多一次；独立 attempt"] --> Meter
  Report["Reporter 可选分组调用"] --> Meter
  Meter --> Budget{"AgentLoop<br/>40k Token / 900 秒 / 30 步"}
  Budget -->|可继续| Next["下一轮"]
  Budget -->|耗尽| End["token_budget / time_limit 等"]
  Meter --> Current["当前：ResearchState 总用量<br/>event 用量增量"]
  Meter -.-> Proposed["PROPOSED：每请求安全计量<br/>阶段已知 Token + 未知调用数"]
  Current --> DB[("trace / 任务重建")]
  Proposed -.-> DB
```

`VERIFIED` provider 成功响应和结构化修复的用量会合并累加，[`ResearchState`](../../adaptive_agent/state.py#L136)仅持有**已报告**总 prompt/completion；当前没有每请求/每阶段持久计量。`PROPOSED` 内部 attempt 计量把首次、技术重试、修复分开，修复阶段与父阶段互斥，避免双计。支持 attempt 记录时，事件记录已知 Token 下界和未知用量调用数；不支持的 Provider 省略阶段分布，不能从总用量推算调用次数。未知调用使完整 Token/实际费用不可验证，UI 显示 `null`/未知而不是 0。40k 是已报告值和请求前估计的运行预算，不能证明实际计费硬上限；突发进程死亡还可能丢失尚未落到事件边界的 attempt 样本。不保存 prompt、密钥、完整网页或外部价格于新增诊断字段。精确字段和对账规则见[04 契约](04_DATA_AND_API_CONTRACTS.md#4-事件-payload事务与重启)。

## 状态机：任务与子目标

```mermaid
stateDiagram-v2
  [*] --> queued: create + task_queued
  queued --> running: 获得槽位 + task_started
  queued --> cancelled: 排队取消 + task_finished
  queued --> failed: 重启且无事实 / 启动异常
  queued --> partial: 重启且有事实
  running --> completed: 所有必需证据和数量达成
  running --> partial: 有事实但预算/信息不足/重启
  running --> failed: 无可用事实或未处理异常
  running --> cancelled: 用户软取消完成
  completed --> [*]
  partial --> [*]
  failed --> [*]
  cancelled --> [*]
```

**不变量**：只允许 `queued→running`、`queued/running→terminal`；终态不可变。`task_finished` 每任务只落库一次；Reducer 拒绝错误 task ID、重复 step、无效 payload 与终态后事件。并发取消与完成由数据库条件更新裁决；已完成/部分/失败任务的取消返回 `cancelled=false`，已取消返回 `true` 而不改记录。子目标 `pending→in_progress→completed` 需已验证证据，任务终止仍未满足则 `failed`；`depends_on` DAG 不执行。当前重启行为只重建终态报告，不恢复 Agent Loop。事务和 SSE 补读测试见[测试方案](05_TEST_AND_EVALUATION.md)。
