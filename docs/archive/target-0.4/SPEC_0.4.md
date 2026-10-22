# Adaptive Research Agent — 0.4 目标规格

**状态：APPROVED — Gate 2 目标设计；尚未实施。** 日期：2026-10-18。用户审阅产品、架构、容量、备份和评测修订后明确回复“批准 0.4 并切换权威指针”。本文件是以后**明确授权的 Gate 2 任务**的目标设计；未被该任务取代的已实现 V1 行为仍以 [V1 规格](docs/specs/V1_SPEC.md)和[契约](docs/contracts/V1_CONTRACTS.md)为准。[0.3 设计索引](docs/design/00_DESIGN_INDEX.md)保留为已批准的历史版本。本批准不授权业务实现、付费运行或发布。[PLANS.md](PLANS.md)是配套执行顺序；[现状审计](docs/audits/PREDEV_BASELINE_2026-10-18.md)区分源码事实与运行证据，[AI Coding 公开实践研究](docs/research/AI_CODING_WORKFLOWS.md)解释工作台配置取舍。

## 1. 目标、用户与范围

面向开发者与约 20 人的可信内网团队，把技术调研目标转成可观察、可追溯且可核验的研究任务。团队成员以各自账户登录，只能读取和取消自己的任务；管理员负责账户创建、停用与密码重置。目标是在**一台 Windows 11 主机**上支持约 20 人同时访问、至少 8 个任务已提交或排队；真实并行执行数由容量测试确定，初始上限保持 2。这台主机为 i7-12700H、16 GB RAM，约 170 GB 可用磁盘；8 个浏览器任务同时运行不是已批准的容量承诺。服务只要求工作时段在线，主机休眠/关机可中断；重新开机后恢复服务并诚实终结中断任务。服务端统一持有 DeepSeek/GitHub 凭据，按任务拥有者记录已报告及未知用量。三类任务共享同一 Agent、证据链、报告和状态机：

| 场景 | 用户需要与成功报告的分析建议 | 固定回归 |
| --- | --- | --- |
| 开源项目发现与技术选型 | 两个候选项目的仓库、许可证、安装方法及官方来源；按任务目标给出可追溯的选型建议、适用条件和理由 | B01 |
| 官方文档对比 | 两个框架的路由、异步支持、安装方法及精确官方页面；按明确的使用条件给出框架建议和取舍依据 | B02 |
| Release / Changelog 研究 | 最新公开版本、日期、两项变更及官方发布页；给出有条件的升级/暂缓建议、适用前提和风险，不在缺少当前部署版本时虚构兼容性结论 | B03 |

公开预注册 G01–G03 分别检验相同三类任务在不同项目上的泛化；它们已公开，**不称盲测或保密留出集**。B01–B03 原始题面和既有固定字段保持原样；建议及依据作为所有六题的**额外成功条件**单独核验，不改写历史字段分母。推荐是基于已核实事实和写明的使用条件作出的判断，不把判断伪装为官方原文；证据不足时只能给出有条件的建议并披露缺口。固定原文和字段见[评测协议](docs/evaluation/G2_EVAL_PROTOCOL.json)。FR-008 模板与 Markdown 导出是 P1；不挤占核心闭环。RAG、向量库、MCP、视觉、多 Agent 运行时、模型路由、LangGraph、Redis/Celery、PostgreSQL、WebSocket 和 LLM-as-Judge 本版不实施；多用户 schema 升级需要可重复迁移，是否采用 Alembic 在迁移任务中定案。

## 2. 现状与目标的证据级别

`CURRENT` 仅表示源码路径存在，不能推出真实业务成功；`TARGET` 表示本版已批准、尚待逐项授权实施的目标；`UNVERIFIED` 表示缺少实际运行或边界证据。历史 r12 的真实任务仍为 **No-Go**：18 次 benchmark 尝试各组完整成功率均 0，另三次独立 UI 任务均失败；原始记录和旧评分保持原样，详见[交付报告](docs/audits/V1_DELIVERY_REPORT.md)。

| 项目 | CURRENT | TARGET / UNVERIFIED |
| --- | --- | --- |
| 接口与状态 | 六路研究 API、六种任务状态、四张 SQLite 表、六类事件已存在；没有账户和任务拥有者 | 六路研究 API 保持语义，新增认证/账户管理边界、拥有者过滤和数据迁移；真实并发仍需验证 |
| Agent | DeepSeek、Planner、Evaluator、Reducer、Reporter、GitHubTool 与 BrowserUseAdapter 已接通 | 调用级失败定位、有效重规划和事实证据路径待修；成功率未达标 |
| 用量 | 仅汇总供应商已报告 Token | 逐调用阶段、重试和结构化修复计量；缺失值不得填零 |
| 证据与 UI | 已有事实、报告、来源和时间线 | 步骤级拒绝摘要、事实证据卡和诊断视图待实施 |
| 生命周期 | 排队后进程内调度、取消、重启终结与持久 SSE 有代码路径 | `submit` 失败后的排队补偿、跨进程认领/取消/唤醒、竞态和资源释放待验证 |

## 3. 架构重评与责任

**CURRENT** 是单进程模块化单体，进程内 `TaskManager` 持有任务和 SSE 唤醒队列。它没有账户身份、任务拥有者或跨进程取消；`GET /api/research` 当前列出全部任务。0.3 对本机单用户选择此方案有依据，但不满足新增的团队隔离目标。**APPROVED TARGET（未实施）** 是同一 Windows 主机上的模块化单体代码库、独立 API 进程和研究 Worker 进程。Worker 隔离浏览器/模型长任务与登录/API/SSE，并从 SQLite 持久队列原子认领任务；这不是 LangGraph 或分布式集群。保留 DeepSeek 主 Provider、BrowserUseAdapter、六路**研究** API 和既有领域事件。新增认证与管理员 API、用户/会话/任务归属持久化和可重复 schema 迁移；当前“四张表”仅描述 V1 事实，不能继续作为团队版目标。权衡见[ADR-0002](docs/design/adr/0002-team-runtime.md)，0.3 [ADR-0001](docs/design/adr/0001-target-architecture.md)保留历史。

```text
团队浏览器 → HTTPS 代理 → Vue / FastAPI（身份、授权、六路研究 API）
                                      ↓ 任务入队 / 查询 / SSE 补读
                                同机 SQLite（任务认领、事件、归属、会话）
                                      ↑ 原子认领 / 已提交事件 / 取消信号
研究 Worker → AgentLoop → Planner / ContextManager / Evaluator / StateReducer / Reporter
                         → ToolRouter → GitHubTool / BrowserUseAdapter → 外部 API / browser-use
```

ResearchService 连接 API 与持久化；Worker 调度器持有执行槽，但任务认领、租约/心跳、取消请求和终态必须持久化，不能依赖 Worker 内存。AgentLoop 仍持有循环与停止决策；Planner/Evaluator 不管理数据库或浏览器；ToolRouter 派发动作；BrowserUseAdapter 管理浏览器执行。Persistence 独占原子写入，已提交的 SQLite trace 是 SSE 事实来源；API 以有界轮询/通知补读跨进程提交，不把原有内存队列当作唯一通知。Worker 崩溃后不得并发重放浏览器副作用；失效认领按持久事实终结并可显式重新提交新任务，默认不透明续跑。`browser-use/` 是上游基础设施，不容纳研究策略。`ResearchState` 只保存可序列化领域状态；重要状态变化经 `AgentEvent → StateReducer → ResearchState`，Reducer 保持纯函数。领域、API DTO 与 ORM 模型分开；V1 不是事件溯源。

SQLite 使用同机文件与短事务；WAL 可让读写并行，但[官方文档](https://www.sqlite.org/wal.html)明确同时仍只有一个 writer，且不支持网络文件系统。20 人在线/至少 8 个待处理任务是设计容量目标，写入锁竞争、SSE 延迟和可运行浏览器数须在指定 Windows 主机实测。达到不了目标时保持团队版 No-Go，并以数据决定是否提高资源、降低运行槽或另立数据库 ADR，不预先把 SQLite 扩容能力当事实。

## 4. 数据流与对外契约

1. 管理员创建/停用账户并重置密码；成员经 HTTPS 登录，服务端验证会话和账户状态。密码只存自适应哈希，浏览器使用 `Secure`、`HttpOnly`、合适 `SameSite` 属性的会话 Cookie；状态变更请求须防 CSRF，登录须限速，注销/停用使会话失效。内网 IP 的证书由内部 CA 签发，管理员统一在团队客户端安装信任；API/Worker 只监听受限接口。身份与权限不得信任客户端传来的 owner ID。
2. 已认证成员提交 1–4000 字目标；FastAPI 校验；ResearchService 同事务持久化 `owner_id`、`research_task` 和 `task_queued`。Worker 原子认领可见的 queued 任务并取得运行槽。入队/认领失败必须得到可解释终态或继续安全排队，不能永久遗留且不得双重执行。六路研究 API 的列表、详情、trace、SSE、取消全部按拥有者过滤；他人 ID 返回无泄漏的不可见结果。历史 V1 无 owner 记录迁移后仅管理员可审计，不可默认归给任意成员。
3. AgentLoop 初始化子目标，观察页面，构建上下文，规划一个有效动作，经 ToolRouter 使用 GitHubTool 或 BrowserUseAdapter；Evaluator 核验候选事实，Reducer 更新状态。技术故障有界重试；目标不符或信息不足回到观察、评估、改计划。统一 Provider 凭据留在 Worker/服务端；每次已报告与未知用量按 task owner 汇总，不因缺失值填零。
4. AgentEvent 回调先经 Persistence 原子写入状态、步骤、准入事实和 trace；API 从已提交 trace 补读 SSE，可用有界轮询唤醒。SQLite trace 是事实来源；旧进程内队列仅能优化同进程通知。SSE 重连用 `Last-Event-ID` 补读，终态关闭流；Vue 释放订阅。取消由 API 写持久请求，Worker 在有界延迟内观察并传播到 AgentLoop；进程故障时按认领租约和已保存事实终结，不重放有副作用的浏览器步骤。
5. Reporter 只使用已接纳事实，Finding 关联 fact ID 和官方来源。成功报告另含明确的建议、适用条件、支持与反对理由、所用 fact ID；建议是可检查的推论而非网页原文。终态报告存在 `task_finished` trace 中。GET 从已存 trace 重建报告。取消、异常、预算、无进展和重启都必须有诚实、唯一且不可逆的终态；重启终结未完成任务，**不**断点续跑。

| 类别 | 0.4 已批准目标契约 | 当前与变更边界 |
| --- | --- | --- |
| API | 六路研究 API 保持路径；另需登录/注销/会话及管理员账户管理接口 | 身份和 owner 过滤是破坏性安全边界；不新增事实 CRUD；旧客户端须升级后方能访问 |
| 状态 | `queued`、`running`、`completed`、`partial`、`failed`、`cancelled` | `completed` 不能仅凭工具成功；终态不可逆 |
| 事件 | `task_queued`、`task_started`、`subgoals_initialized`、`step_evaluated`、`cancel_requested`、`task_finished` | 可在既有事件增加安全的可选诊断字段；旧 trace 仍可读 |
| 表 | V1 的 `research_task`、`research_step`、`research_fact`、`agent_trace`；团队版新增用户和服务端会话持久化，任务增加归属/认领/取消状态 | 需要可重复、可回滚的数据迁移与历史记录隔离；最终列和索引在 G2-10/11 契约冻结；报告仍在终态 trace |

详细字段及当前路由行为由[0.3 数据/API 契约](docs/design/04_DATA_AND_API_CONTRACTS.md)提供历史设计上下文，实际 V1 行为以源码和 V1 契约为准。**研究事件**的 0.4 目标增量仍限于既有事件的可选 `usage_by_stage` 和 `fact_rejection_summary`：每次 Provider attempt（包括技术重试及独立结构化修复）只计一次已报告用量；有未知用量时完整总量为 `null`，已知下界单列，未知调用数如无请求记录也保持未知。拒绝摘要只记录数量和原因码，不保存候选正文。

团队版新增契约属 **APPROVED TARGET，未修改当前 API/ORM**：

| 边界 | 0.4 目标契约 | 失败与兼容行为 |
| --- | --- | --- |
| 认证 API | `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/auth/me`、`POST /api/auth/change-password`；管理员专用 `POST /api/admin/users`、`GET /api/admin/users`、`POST /api/admin/users/{id}/disable`、`POST /api/admin/users/{id}/reset-password` | 登录错误不暴露账户是否存在；管理员创建/重置只发临时凭据，成员首次登录须改密码；停用撤销全部会话；无自助注册或邮件找回 |
| 会话/授权 | 服务端随机会话令牌只以哈希保存；Cookie 为 `Secure`、`HttpOnly`、`SameSite`，设置绝对过期；登录限速，所有有副作用的 Cookie 请求防 CSRF；`GET /api/auth/me` 返回最少身份/角色数据 | 所有研究路由先认证再按 `owner_id` 限定；对他人任务统一不可见，不通过 403/404 差异泄漏 ID；管理员只管理账户，不默认读取成员研究内容 |
| 持久化 | 新增 `app_user`（唯一登录名、密码哈希、角色、停用/首次改密状态）、`auth_session`（用户 ID、令牌哈希、到期/撤销）；`research_task` 增 `owner_id`、认领者/租约到期与取消请求字段，相关索引；新任务必须有 owner | 旧四表原件保留，历史 `owner_id=NULL` 仅能由本机管理维护路径审计；schema 迁移先备份，重复执行和回滚测试，不用 `create_all` 静默补列 |
| 研究报告 | 保留现有 findings/sources/markdown；新增可选结构化 `recommendation`：`text`、`use_conditions`、`supporting_fact_ids`、`official_source_urls`、`tradeoffs_or_unknowns` | 旧报告缺该字段仍可读；0.4 新任务只有建议和依据完整时才可判业务 full；对 B/G 的建议审核单列，不改原题 10/5 字段 |
| 任务认领与事件 | Worker 对 queued 行进行条件更新与租约记录，同一任务仅一个有效认领；已提交 `agent_trace` 供 API/SSE 补读；取消请求写库，Worker 有界轮询；失效租约经事实重建终结 | 不依赖内存 `TaskManager` 跨进程共享；崩溃后不自动重放有副作用步骤；重复启动/取消/终态保持幂等；运行槽初始 2 |

会话凭据、密码哈希、重置凭据、原始 Cookie 和 CSRF 秘密不得进入 Agent Prompt、trace、报告或评测原件。具体 DTO、索引、迁移版本与状态码由 G2-10/11 在实施前更新契约并附越权/旧数据兼容测试；上述安全语义与六路研究路径不可在任务中自行放松。

## 5. 失败、安全与资源边界

- 单任务默认上限沿用 30 步、900 秒、40,000 已报告 Token、连续 5 次无进展；上限不能被未知 usage 解释为实际费用硬上限。初始运行槽为 2，至少 8 个任务可安全排队；调高运行槽先通过该主机的内存、CPU、SQLite 写入和 API/SSE 延迟测试。每次尝试记录运行环境、拥有者、用量已知/未知、重复操作、耗时和停止原因。
- 临时网络、429、5xx、工具技术失败按当前契约有界重试；语义不匹配、证据不足、无效动作应重新观察、评估与规划。异常或取消时释放浏览器、HTTP、任务和 SSE 资源；终态写入与 `task_finished` 同事务。
- DeepSeek/GitHub 密钥只在服务端环境变量，已配置秘密在日志/事件/报告中脱敏；页面和工具输出是不可信数据，不能覆盖指令。已存在的 step trace 可能保存有界页面内容，因此团队版仅处理可信成员提交的公开技术资料。认证、对象级授权、会话撤销、密码重置、登录限速、CSRF、防越权的 SSE/trace 和管理接口必须在团队接入前完成；禁止跨用户暴露目标、事实、Token 和原始 trace。[OWASP 密码存储](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)建议 Argon2id 等自适应哈希，[会话管理](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)要求保护会话秘密。
- 显式导航的 HTTP(S) 公有地址校验已有代码路径；DNS 重绑定、重定向、点击、弹窗和子资源的事前拦截尚未得到充分验证，**不**宣称完整 SSRF 防护。新诊断元数据不复制 Prompt、页面正文或密钥。目标部署使用同机 Caddy 作为 HTTPS 代理，在内网 IP 上签发内部 CA 证书并由管理员统一向约 20 台客户端分发信任；[Caddy 官方文档](https://caddyserver.com/docs/automatic-https)说明 IP 可启用内部 HTTPS，[Windows 服务文档](https://caddyserver.com/docs/running)说明自启方式。代理只暴露 HTTPS，API/Worker/SQLite 不对内网直接开放；证书轮换、服务自启与失效恢复均需验证。不得公开部署为无边界多用户服务。
- 每日对 SQLite 与恢复所需配置做一致性加密备份，放在由管理员提供路径的团队内网共享存储；密钥与备份文件分开保管，限制读取权限，保留 30 天并按月做一次可审计恢复演练。共享存储路径、凭据、容量和保管责任在实际部署前确认；没有可用异机备份则团队版保持 No-Go。备份不包含明文 Provider/会话秘密，不以复制运行中的 SQLite 主文件冒充一致性快照。

## 6. 需求、追踪与验收

| Requirement | 目标与优先级 | Task | Acceptance |
| --- | --- | --- | --- |
| FR-001 | P0 创建、排队、历史与六态 | G2-05、G2-06 | AC-001 |
| FR-002 | P0 动态规划、工具路由、有界重规划 | G2-01、G2-03、G2-06 | AC-002 |
| FR-003 | P0 事实准入、归属、去重与追溯 | G2-04、G2-07 | AC-003 |
| FR-004 | P0 只用已核实事实生成报告 | G2-04、G2-06、G2-09 | AC-004 |
| FR-005 | P0 持久事件、SSE 补读、历史 UI | G2-05、G2-07 | AC-005 |
| FR-006 | P0 取消、异常、重启与唯一终态 | G2-05 | AC-006 |
| FR-007 | P0 用量、失败与耗时诊断 | G2-01、G2-02、G2-07 | AC-007 |
| FR-008 | P1 可编辑模板与 Markdown 导出 | 后续单独排期 | AC-008 |
| FR-009 | P0 本地账户、会话、任务归属与逐对象授权 | G2-10、G2-07 | AC-009 |
| FR-010 | P0 三类场景成功报告的可核源建议和适用条件 | G2-04、G2-07、G2-09 | AC-010 |
| NFR-001 | P0 有界运行和资源一致性 | G2-03、G2-05 | AC-N01 |
| NFR-002 | P0 成本与性能证据 | G2-02、G2-09 | AC-N02 |
| NFR-003 | P0 本机安全边界 | G2-05、G2-08 | AC-N03 |
| NFR-004 | P0 失败可复盘 | G2-01、G2-02、G2-07 | AC-N04 |
| NFR-005 | P0 小步可维护交付 | G2-08 | AC-N05 |
| NFR-006 | P0 可重复本机运行 | G2-05、G2-08 | AC-N06 |
| NFR-007 | P0 单机团队并发、持久任务认领与跨进程事件 | G2-11、G2-12 | AC-N07 |
| NFR-008 | P0 内网 HTTPS、会话与数据隔离 | G2-10、G2-12 | AC-N08 |
| NFR-009 | P0 工作时段可恢复与异机加密备份 | G2-12、G2-08 | AC-N09 |

`AC-001`：202/422/503、持久 queued 与并发上限可验证；`AC-002`：Fake 回归和真实轨迹证明规划/工具/评估与失败分流；`AC-003`：无来源、错归属或未观察事实不进入报告，拒绝摘要可复盘；`AC-004`：报告事实 ID、终态和官方来源一致；`AC-005`：跨进程提交后 SSE 补读不丢、不重、断开释放；`AC-006`：取消/完成/Worker 故障/重启竞态只产生唯一终态；`AC-007`：各阶段和独立 attempt 用量对账，缺失显式为未知且可按拥有者统计；`AC-008`：若另获批准，模板/导出不改变固定任务；`AC-009`：未认证请求被拒，成员对他人任务的列表/详情/trace/SSE/取消无读取或操作权，停用与注销撤销会话，管理员账户操作受角色限制，迁移前任务默认不可由普通成员读取；`AC-010`：每个判为完整成功的报告包含明确建议、适用条件、至少一个支持依据及可核验的 fact ID/官方来源，若取舍受未知条件影响必须说明，不能把判断写成来源事实。

`AC-N01`：预算与资源清理有边界；`AC-N02`：逐次记录 Token、调用、重复 URL、耗时和失败；`AC-N03`：公开资料浏览安全边界与残余风险经测试披露；`AC-N04`：task/event/run ID 可重建失败；`AC-N05`：影响范围内离线检查与 scoped Diff 审查通过；`AC-N06`：按 README 启动 API、Worker、HTTPS 代理，重启历史可读；`AC-N07`：指定 Windows 11/i7-12700H/16 GB 主机上约 20 个并发在线会话和至少 8 个已提交任务可正常排队，实际运行槽数经资源测试确定，API/SSE 响应、任务认领唯一性和崩溃处理有记录；`AC-N08`：内网 IP 的 HTTPS 证书由团队设备信任，明文入口不可传凭据，跨账户越权、会话撤销/CSRF/密码重置和服务自启经验证；`AC-N09`：工作时段冷启动后历史可读且中断任务终态诚实，每日加密一致性备份落到异机共享存储并保留 30 天，按月从备份恢复账户/任务/trace 的演练留证；共享存储不可用时显示告警并阻断团队版放行。每项验收须带实际命令、结果或运行 ID；Mock 成功不替代真实任务成功。任务顺序和各 AC 的验证层级见[PLANS.md](PLANS.md)。

## 7. 新版业务放行协议（已批准目标，尚未执行）

开发中每类先运行一次 B01、B02、B03 诊断；诊断结果不混入正式批次。代码冻结、协议预注册且获得**另行付费授权**后，正式 full-system 批次运行 B01–B03 各三次（九次）和公开 G01–G03 各一次（三次），每次独立 task ID。所有尝试和失败都计入分母、保留原件，不因站点漂移、费用或失败而换题、删样本或补分。

每个 B 案例至少 2/3 **完整成功**；G 三例至少 2/3 完整成功。完整成功同时要求持久终态 `completed`、`completion_level=full`、该案例**每个必需字段在这一次报告中**有明确值与相应官方来源、所有实质结论可由准入事实和官方页面核验、**可核源的建议/理由/适用条件**、UI/API/SQLite/SSE 一致，且报告与 trace 仅对任务拥有者可见。建议的事实依据须人工核源；建议本身作为明确标注的分析判断审核，不伪称官方推荐。`partial`、缺字段、无源、无依据建议、矛盾或来源无法人工确认均不能计成功。每次单独报告字段覆盖 `x/n`（B01/B02/G01/G02 为 10，B03/G03 为 5）；建议审核单列，不改变原题或字段分母。失败尝试仍保留字段分数，但**不再设九次汇总 68/75 放行阈值**。该条与历史 0.3 的 [05](docs/design/05_TEST_AND_EVALUATION.md)及[06](docs/design/06_ACCEPTANCE_AND_RELEASE.md)明确冲突；0.4 获批准后按本条执行未来获授权评测。旧 r12 可作对照，不是新版放行条件。

官方核源由人工逐条记录页面、访问时间、支持的字段/结论和冲突；离线校验器只验证协议与记录结构，不能自动证明网页真伪、真实模型表现或站点未漂移。缺少正式运行、核源或任何门槛失败则维持 **No-Go**。小样本结果仅说明预注册六题的表现，不推断总体成功率。

## 8. 版本决策与变更边界

0.4 已批准的目标改变单次覆盖和 Go/No-Go 口径、公开泛化集称谓、成功报告的建议要求、可信团队账户/隔离与同机 API/Worker 目标，以及工作台追踪入口；这已超出 0.3 的单用户单进程前提。0.3 文档、V1 合同、r12 原始数据和旧 scorer 保留历史，不回写为新版成绩。仓库[设计索引](docs/design/00_DESIGN_INDEX.md)与[AGENTS.md](AGENTS.md)已将后续明确授权的 Gate 2 目标路由到 0.4；业务实施、付费评测和部署仍分别授权。当前代码和真实任务结论并未因设计批准而变为 Go。
