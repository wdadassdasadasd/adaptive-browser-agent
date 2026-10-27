# 现行目标契约（PREP-BASELINE-v4.3，目标分阶段实施中）

2026-10-27 文档落地；实际同步审查见 [任务记录](../features/DECISION-001/tasks.md)。[ADR-0008](../design/adr/0008-m1-engineering-baseline.md)局部替代 ADR7；以下旧六路与正式门槛不变，V2 的新目标不表示已实现。

本文是 [现行规格](../../SPEC.md)与[现行计划](../../PLANS.md)的业务开发目标边界，真实验收以[现行评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)为准。[V1 契约](V1_CONTRACTS.md)描述保留的默认入口；P-01 独立开发入口的已实现差异、验证及剩余项见[任务记录](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)。[旧目标契约](0.5_TARGET_CONTRACTS.md)和[原目标规格归档](../archive/target-2026-10-18/SPEC.md)仅供历史核对。代码实现必须通过迁移/兼容测试才能从 V1 切到本文。本契约不声明目标已经全部实现或上线。

## API 与身份

研究提交 DTO 增加可选 `memory_mode: "off" | "source_hints"`，省略时为 `off`，不改变六路研究 API、六态和旧请求的语义。V3 另增加可选 `decision_context`，其精确定义见下节；它仍是目标契约，已提交切片的实施与验收状态见[DECISION-001 任务表](../features/DECISION-001/tasks.md)。P-03 增加 owner-scoped 来源线索接口：`POST /api/memories/import`、`GET /api/memories`、`DELETE /api/memories/{memory_id}`。owner 只能从已认证会话取得；导入须校验原任务归属、报告快照 SHA-256、人工官方核源工件及 fact ID，失败原子回滚。列表不泄露他人线索；撤销后不再检索，过期线索不得注入。具体 DTO/状态码随 P-03 兼容测试固定。

保持六路研究 API 与当前请求/响应核心语义：`POST /api/research`、`GET /api/research`、`GET /api/research/{task_id}`、`GET /api/research/{task_id}/traces`、`GET /api/research/{task_id}/events`、`POST /api/research/{task_id}/cancel`。`/traces` 为源码实际路径；旧目标契约的 `/trace` 是历史笔误，不作为兼容别名。任务状态继续为 `queued | running | completed | partial | failed | cancelled`，终态不可逆。提交返回持久排队任务，列表仅含当前 owner 的任务。

### DECISION-001 可选输入与兼容语义（目标契约，真实研究未验收）

`POST /api/research` 保留现有必填 `goal`（去首尾空白后 1–4,000 字符）。`decision_context` 可省略或为 `null`，均等同旧请求；非空时必须是对象，包含非空 `use_case`（去首尾空白后 1–1,000 字符），并可含以下数组，省略时为空数组：`must_have`（0–12 条）、`preferences`（0–12 条）、`candidate_projects`（0–8 条）。每条去首尾空白后 1–200 字符；未知字段、错误类型、超限、空白条目或同一数组经去首尾空白与不区分大小写比较后的重复条目返回 HTTP 422，且不创建任务。`must_have` 是用户硬条件，`preferences` 是非硬性偏好；不得从网页、模型输出或系统默认推断为用户已指定条件。空候选数组允许 Agent 发现候选；非空数组保留每个用户给定标识及原始输入顺序，检索发现者必须另标来源，不得暗中替换用户候选。`candidate_projects` 是待核验标识，不表示项目身份已证实；拒绝将其当工具命令或可信 URL。输入限制属于新目标；旧仅含 `goal` 的请求和六路 API 的原有字段、状态与取消／SSE 语义保持兼容。

服务端在任务提交事务中持久化规范化后的决策上下文，并随同一 owner 的任务交给 Worker；恢复后读取同一快照，不从后续页面重建用户条件。已存在的 `Idempotency-Key` 对同一 owner 仅在 `goal`、`memory_mode` 和完整规范化决策上下文均相同时返回既有任务；任一项不同返回 HTTP 409，不创建新任务。旧请求的缺省值参与规范化比较。API 对未授权者仍按既有逐对象不可见语义处理；上下文不得包含凭据，日志与事件只存安全摘要，不把用户原文无界复制到调用轨迹。输入长度校验在调用任何模型或工具前完成。

新增 `POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/auth/me`，以及管理员开通、停用、重置本地账户的接口；管理员接口统一位于 `/api/admin/accounts`，对应创建、列表、按账户 ID 更新状态和重置凭据。正式产品提供完整管理员账户界面和个人任务界面；M1 先两真实成员账户及本地 CLI 开通/停用/重置，不开放自助注册。具体 DTO 与状态码在 P-03 的 API 兼容测试中固定。上限五账户**包含初始管理员**。管理员只管理账户，不默认读取其他人的研究任务。

所有研究路由先验证会话，列表按 owner 过滤；详情、traces、SSE 和取消逐对象授权。对于不存在和他人任务都返回同一不可见结果，且在 SSE 建立连接或解析 `Last-Event-ID` 前完成授权。注销/停用撤销会话；密码自适应哈希，服务端会话随机生成、存哈希，Cookie 用 HttpOnly、合适的 SameSite 与过期时间；本机 HTTP 演示不得暗示 Secure Cookie/LAN HTTPS 已通过。Cookie 写操作防 CSRF，登录限速。凭据、会话、CSRF 秘密不得进入 Prompt、trace、事件或报告。

## 持久事实、报告与事件

Windows API 和独立 Worker 共用 WSL PostgreSQL 应用表，拥有账户/会话、owner-scoped 任务、执行尝试/租约、取消请求、准入事实和来源、社区补充、建议/报告、费用与单调编号的用户事件。Worker 用短事务租约认领并递增 fencing token；每次写事实、事件、报告、费用或终态须核对当前 token，过期 Worker 的迟到结果只能作为隔离诊断，不得覆盖新代次。任务状态和对应事件在同一事务提交；SSE 按已提交事件 ID 补读，通知只唤醒，丢失后仍可查询补读。每任务最多一个有效认领与一个终态；取消、租约过期、恢复和终态以事务裁决。AgentLoop 保持现行执行器；若后续采用 LangGraph，检查点只辅助可序列化执行恢复，不拥有账户授权、用户可见事件或业务终态。P-01 假任务先验证这些边界。

容量为两运行槽加八排队槽；数据库原子容量检查在满额时返回 HTTP 429 和重试提示，**不创建任务**。排队任务按提交顺序认领，排队取消立即释放槽位。API 接收运行中取消请求后在 1 秒内确认持久化请求，响应 DTO 以 `cancellation_requested` 表示取消中，不新增第七种任务状态；Worker 异步停止可取消调用并清理，终态以唯一写入裁决。数据库失联时提交/取消返回服务不可用，不确认未提交的写入；Worker 停止新认领，恢复连接后按应用账本对账。

关键事实至少有 fact ID、subject、claim、官方来源 URL、官方身份依据、最小证据片段、页面定位、抓取时间、机器准入状态、人工官方核实状态和复核时间。机器准入只表示工具观察与主体、片段等规则相符，不等于已经证明网页官方身份；仅经人工打开官方仓库、文档或发布页核实的事实可支撑正式评测中的关键结论。社区材料独立标为 `community_supplement`，记录 URL、人工核验时间和局限，不单独支持关键结论。建议记录适用条件、理由、supporting fact IDs、取舍和未知项；报告把事实、补充与分析分层，不冒充官方原话。应用内 `completed/full` 是字段齐全、机器准入事实支撑的候选报告，界面标为待人工核实；正式 full 成功还须人工官方核源。事实不足写 `partial` 或 `failed` 及缺口，不虚构成功。

DECISION-001 的报告目标是在原报告字段之外增设可选 `decision` 对象；非选型旧任务可为 `null`，读取旧报告不得因缺少此字段失败。`decision` 包含提交时的用途与用户条件快照、候选列表（`candidate_id`、用户给定／Agent 发现的来源标识及已核实主体）、逐候选 × 逐条件的矩阵行、冲突／未知项、`recommendation`（可为 `null`）、改变建议的条件及无法推荐原因。矩阵行至少记录稳定的 `candidate_id`、条件类型（`must_have | preference`）、原条件文本、判断 `satisfied | not_satisfied | unknown | conflicting`、支持与反证 fact ID 列表及简明理由。每个引用的 fact ID 必须归属本任务、已机器准入，并与候选主体、官方来源、最小片段和抓取时间对应；来源冲突不得通过选择性丢弃事实改成已满足。没有证据时判断为 `unknown` 且证据列表为空，不能填造 fact ID。应用内建议写明适用条件、取舍、支持的矩阵行和 fact ID，并标“待人工核实”；不能以加权总分代替证据。正式成功仍按人工逐结论官方核源判定。

无硬条件或关键约束不明确时，可说明假设并输出多个条件化选择，但不得声称唯一无条件赢家；任一候选违反已证实硬条件、所有候选均不满足、决定性来源冲突或关键硬条件缺证时，对受影响候选不得给出无条件推荐，并写明缺口与可改变结论的条件。仅有 `goal` 的旧请求允许保留旧报告格式和语义；决策字段未能形成时，不把完整排版视为成功。任务失败、取消、失租或预算停线沿用六态及现有调用账本，保留已提交事实和未知费用，不以矩阵为空伪装完成。

每次模型/工具调用前持久写 `started` 与调用 ID，返回后写 `completed` 或 `failed`、已知用量和费用；崩溃空档记 `unknown_outcome`，不推断成功或零费用。调用级诊断另保存阶段、输入输出的安全摘要、时间、失败类型、重试/重规划原因、provider 已报告用量及未知调用数；不得记录秘密或敏感页面。费用按模型、计价版本、币种、单价和已知用量计算，未知费用单列为 `null`。每次真实尝试的轨迹、核源及哈希要求见评测协议；应用表保存新任务记录，r12 和旧 SQLite 原件保持只读且不导入新 UI。

AgentLoop 延用结构化 `PlanDecision` → `ToolRouter` → 浏览器/GitHub 的链路。规划记录当前子目标、预期结果、执行结果和重规划理由；工具参数、重复动作、失效浏览器观察和错误类型进入可脱敏调用轨迹。ContextManager 裁剪后须优先保留当前子目标、最新观察、引用中的关键 fact ID/来源及最近失败线索；任务用量只采用 provider 报告，未知请求不得按零计算。P-02 的离线质量/用量对照验证 AC-002、AC-007，不以裁剪字符数代替 Token 统计。

评测工件按 `current-3` 协议：每次尝试保存独立报告快照哈希，离线人工复核文件以同一 SHA-256 绑定核验事实与结论；无报告时工件为 `null`。调用级已知费用与尝试已知费用相等，无未知费用时总费用也相等。项目总账逐次计入 pilot、诊断、中断、重跑、正式批次和机动，引用原始证据及授权；费用未知即停线并记 No-Go。P-02 pilot 的账户访问检查可为 `null`（尚未验证），不能当成功；正式批次必须为实际布尔检查，full 成功要求全部为 true。离线文件只用于验收复核，不作为应用内核源后台。

## 上下文、记忆、模型与工具目标

工作上下文是针对 Planner、Evaluator、Reporter 的有界投影；PostgreSQL 应用表仍保存已接受事实、来源、需求状态、调用和事件，裁剪不能删除原证据。相关性选择保留 fact ID、来源、矛盾和失败线索，确定性压缩后可按 ID 回取；模型摘要默认关闭，若启用须在成功持久化后才替换投影并单独计费。跨任务线索仅携带同 owner 显式导入的已核源来源定位，默认关闭，导入起绝对有效期 7 天、每次最多检索 5 条、读取不续期，撤销/过期先过滤再排名；必须重新观察来源，不能将线索直接变成本次事实。正式评测关闭跨任务复用且逐尝试隔离。

Gateway 对模型请求显式携带 `stage`、任务截止时间和最大输出 Token；响应保存 provider 实际输入/输出、缓存用量、停止原因和延迟。任务总上限 40,000 Token，报告预留 4,096；规划、评估、报告单次输出分别至多 1,024、2,048、4,096 且不得越过剩余额度。输入估算与实际用量分开，未知 usage/金额为 `null` 并停线。规划、评估、JSON 修复、重试及未来摘要每次单独记 call ID 和费用；并发初始 1，排队等待计入截止时间。429 可按明确幂等边界有限重试，网络结果不明不得盲目重发。

工具描述须从同一 schema 生成动作指引、参数校验和执行边界。P-03 使用已锁定 MCP Python SDK 2.1.1 的本地 stdio 客户端，只暴露仓库元数据与发布记录读取；记录协商协议版本，非法参数不触达子进程，超时/断连/`is_error`/取消均清理资源。现有结构化 `PlanDecision` 与 MCP 适配是两个边界，模型原生 `tool_calls` 仍未实现。

## 故障、边界与放行

本机启动器维护 WSL 前台保活、确认 PostgreSQL 在线，然后启动 API/Worker，并监测与自动重启 Worker；WSL/数据库失联时不自动宣称恢复，而是失败关闭并待人工恢复后对账。Worker 进程故障后同一任务至多重新认领一次：从应用已提交事实与调用账本恢复，重建浏览器，重新观察并规划；结果不明的动作不原样重放。第二次故障以 `partial` 或 `failed` 终结并留下原因。取消写入持久请求；已进入终态则不再改写。成功、失败、取消都关闭浏览器及其他资源。P-01 假任务故障注入要求 Worker ≤60 秒重启、任务 ≤120 秒重新认领或诚实终结，真实浏览器恢复耗时单独记录。进程重启后的处理与 V1 `server_restart` 终结行为存在目标差异，须以明确迁移及回归测试实现。

首版入口只在本机开放，不宣称 LAN 可用。公开输入、浏览器外联与工具输出按不可信处理；LAN 的 HTTPS、DNS/重定向/弹窗/子资源私网阻断需另立实证验收。两运行八排队只作模拟与资源记录；假任务期间常规 API p95 ≤1 秒，已提交 SSE 事件补读 ≤2 秒，无丢失、双认领或 OOM，记录 CPU/内存峰值。一次加密可断开介质备份/独立目录恢复必须有密文、解密恢复、任务/事实/事件及必要证据工件的完整性和哈希证据，原件不受损；这不等于持续异机灾备。

正式业务放行依 [评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)的 15 次独立尝试、人工官方核源和固定阈值，另须五账户隔离、容量模拟、一次安全恢复及一次加密离线备份恢复通过。离线测试、结构校验和 mock 不证明真实研究成功。

## 验收证据索引

下列 AC 与[规格中的需求映射](../../SPEC.md#需求阶段验收)对应，均以可复查的测试/尝试记录判定；未执行标 `UNVERIFIED`，不自动算通过。

| AC | 必备证据 |
| --- | --- |
| AC-001、AC-002 | 假任务与真实任务的持久状态/历史；观察、规划、结构化工具动作、上下文裁剪和重规划的调用轨迹 |
| AC-003、AC-004 | 伪造来源/错归属拒绝用例；机器准入与人工官方核实分层；最小片段、官方身份依据及 fact ID→字段/报告结论映射 |
| AC-005、AC-006 | 事件事务与断线补读；取消竞争、一次恢复、二次故障和唯一终态 |
| AC-007 | 持久调用尝试时线、`unknown_outcome`、失败原因、上下文/工具决策、已知/未知用量和费用依据 |
| AC-008 | 延期，无首版放行义务；若实施须另定验收 |
| AC-009、AC-010 | 五账户含管理员、完整管理员界面和逐对象隔离；建议条件、事实和社区补充分层 |
| DEC-AC-01–07 | 兼容旧请求、上下文验证与幂等比较、候选 × 条件事实矩阵、硬条件约束、变化条件、提示注入边界和独立决策质量复核；不改变正式协议 |
| AC-011 | 线索导入的 owner/报告哈希/核源工件校验、7 天过期与撤销；跨账户检索为零、恢复后 fact ID 可回取、正式评测记忆隔离 |
| AC-012 | 本地真实 stdio 子进程完成 MCP 协商/列工具/调用；非法参数不触达、错误/断连/超时/取消清理测试 |
| AC-N01、AC-N02 | 超时/取消资源释放；调用→尝试→批次→项目费用对账、预算上限、未知费用及停止记录 |
| AC-N03、AC-N04 | 本机绑定与公开输入约束；失败轨迹、事实/事件复盘 |
| AC-N05、AC-N06 | 配置 Diff/命令/退出码、原件哈希、启动恢复说明及演示包；API/Worker 重启、一次安全恢复、数据库失联后对账 |
| AC-N07、AC-N08 | 两运行八排队及第 11 个 429 不落库的本机模拟、资源/延迟记录；跨账户 API/SSE/取消和会话/CSRF 测试 |
| AC-N09 | 一次加密离线介质备份、解密恢复及原件/恢复数据哈希 |
| AC-N10 | 假供应商替换、阶段输出限额、429/网络结果不明/缺失 usage/JSON 修复/预算不足测试；每个 call ID 的 Token 与费用对账 |

## V2：交互式决策会话契约（2026-10-26 已批准，尚未实现）

本节基础对应 [ADR-0007](../design/adr/0007-interactive-evidence-decision-sessions.md) 的方案 B `ARCH-20261026-v3.1`，现由 ADR-0008/PREP-BASELINE-v4.3 对通用候选、M1真实账户、记忆、上下文、资金和请求审计的条款优先细化；对应 [DEC-AC-08–16](../features/DECISION-001/spec.md)。本轮只授权文档同步，不执行迁移或新实现。前文六路研究 API、DTO 限制、六态、旧报告引用规则、正式评测和账户目标保持有效；以下新命名空间单独实现，不把“已批准目标”写为当前能力。

### V2-1 对象、真相及接口

PostgreSQL 应用表拥有 DecisionSession（owner、session_version、active_turn_id）、不可变 InputRevision（用户已接受条件及出处）、DecisionTurn（输入、revision、operation task、结果）、不可变 ReportSnapshot 和 SessionEvidenceRef。表／字段名在具体实施任务固定，不另增队列或存储服务。会话可以草稿／等待用户而没有运行任务；每次已接受轮次对应一个有限 PgTask。会话和输入版本是不同概念：session_version 单调推进，input_revision_id 指向不可变条件快照，不能用一个值替代另一个。

| 接口 | 目标语义 |
| --- | --- |
| `POST /api/decision-sessions` | 建立本机 owner 的草稿，不触发模型；返回会话及初始条件版本。 |
| `GET /api/decision-sessions`、`GET /api/decision-sessions/{session_id}` | owner-scoped 列表／详情及当前版本；不返回其他 owner 对象。 |
| `GET /api/decision-sessions/{session_id}/turns`、`.../{session_id}/reports` | 分页历史及不可变报告；游标绑定同 owner／session，不能任意跨对象回取。 |
| `POST /api/decision-sessions/{session_id}/turns` | 输入 expected_session_version、input_revision_id、content、action=`discuss|research`，可带用户明确接受／编辑的结构化条件 patch；同一 Idempotency-Key 规范化 body 重发返回原轮次。 |
| `GET /api/decision-sessions/{session_id}/turns/{turn_id}/events` | 逐对象验证后，按持久事件 ID SSE 补读；只发送本轮事件。 |
| `POST /api/decision-sessions/{session_id}/turns/{turn_id}/cancel` | 原子持久化取消；重复取消幂等，排队取消即终态，运行中返回取消中，终态不改写。 |

所有澄清／解释／研究／组合报告均由 Worker 执行并计入轮次调用账本；API 不直接调模型。讨论轮输出 clarification 或 explanation；研究轮可输出 decision，但任务 `completed` 不等于研究质量成功或旧协议 full。新澄清提议只关联原 user turn，用户主动接受／编辑后才在下一提交事务成为条件；网页、旧报告、模型分析不能隐式新增 must_have 或 preference。允许未知继续，不强制用户填写未确定条件。新输入正文沿用去空白 1–4,000 字符、拒绝未知字段和秘密的输入原则；具体 DTO 固定时不得借机放宽旧接口。

### V2-2 原子提交、并发和终态

同 owner／session 幂等键先于版本 CAS 查询：键和规范化完整 body（含 action、基准版本、revision 和 patch）相同即返回原结果，即使会话版本后来已前进；键相同而 body 不同 409。新键再验证 expected_session_version、input_revision_id 和 session 归属。一个 session 只允许一个未终结轮次；运行／排队期间新输入返回 409。用户想改条件须先取消、等待终态再提交，不隐式取消或分叉。

固定锁顺序为全局 scheduler guard → session → task → 附属记录。原子容量检查计入 legacy_research 与 decision_turn 两种任务；两运行＋八排队上界不扩张。新输入、被接受的条件 revision、turn、task、queued event、active_turn_id、版本推进同事务提交；429、409、存储错误均不得留下孤立输入、revision 或任务。取消、容量与终态竞争用同一顺序和 fencing 规则，不能靠进程内锁保证。

终态事务核对租约 fencing token、原 revision 与预期 session 状态，再一起发布 assistant response／报告引用、任务唯一终态、终态事件、active 指针释放和会话版本推进。**所有终结路径**均遵守，包括排队取消、排队截止、正常完成、异常、超时、预算停线、失租回收及第二次 Worker 故障；不只在成功回调释放。旧报告只追加新快照，不覆盖、删改或重贴新核源标签。等待用户时没有 running task、租约或浏览器。提交／取消未持久时失败关闭，不向 UI 确认成功。

### V2-3 候选、组合、事实和跨轮引用

候选具有稳定 candidate_id、用户显式接受的通用 `role_id`（单选可无角色分组）、subject_kind=`repo|model|cloud_service`，不能以展示名作唯一身份。保存官方主体依据及具体仓库／模型／供应商标识、版本、地域、来源日期与观测时间。缺版本／地域时标未知；不同地域、模型、版本不得混用结论。旧 generic ResearchFact 的 subject_kind 可以为 None，不要求历史事实改形；新准入与匹配器单独支持模型和云服务，不把服务硬凑 GitHub 项目。

单选每轮 active set 至多 4 个；组合至多 3 个用户接受角色、每角色 2 个候选、合计至多 6 个，输出至多 3 个组合。会话历史可保留其他候选，由用户明确激活或分批研究，不悄悄丢弃候选，也不承诺穷举最优。组合逐项列组件、接口／数据流兼容依据、硬条件、偏好、费用假设与未知。组件各自可用不意味着组合端到端可用；没有集成实测就明确未经验证。未知／冲突／不满足沿用旧矩阵语义，无证据不写满足，不虚构权重总分或技术效果。

新观察仍归当轮 task，事实与对应 step event 同事务准入，旧研究报告每个 fact ID 必须归本任务的规则不变。跨轮只用 SessionEvidenceRef `{origin_task_id, fact_id, content_sha256}` 及来源定位；服务端校验原 task、fact 与当前 turn 同 owner 且属于同一 session、准入及哈希一致。不得用只知道 fact_id 跨对象读取，不把历史事实复制为本轮新事实或刷新时间。老任务／其他 session 的材料不自动导入。

历史事实只作为有界只读 reference background 与缺口目标注入，不混进当前 AgentState.facts；保留当前 task 的事实／事件重放相等约束。报告引用区分本轮新观察与合格历史引用，保存原时间、版本／地域、内容哈希、机器准入和人工核源快照。人工核源绑定原报告／事实快照，不自动转移到新观察或新报告。解释旧报告可使用其带日期证据；生成当前建议时，价格、版本和可用性等时效字段必须重新访问查证，不以无条件 TTL 当新鲜。刷新失败保持旧报告，当前项写未知／partial；身份或地域不匹配时不得沿用。持久证据不因上下文裁剪删除。

上下文仅投影当前已接受条件、相关候选／事实引用、有限最近轮次和失败／缺口；投影版本与内容哈希可复查，不整段累积所有聊天。不新增向量库、自动长期偏好或程序规则；显式同 owner 跨任务来源线索进入 M1（V2-7），仍须重新核验，正式评测继续关闭复用且独立尝试隔离。

ASR／TTS／对话官方说明属于声明证据，不能推断老人声音、方言、噪声、自然度、准确率或总时延。区分官方声明、系统分析及实际测量；本项目初版无音频／组件实测。组件价格记录币种、单位、地域、日期、用量假设和未知，不与 Agent 的已发生调用开销混算，不许用不同计价单位直接得出最便宜结论。许可证正文、模型权重条款与云服务条款分别核对，不给法律结论。

### V2-4 统一轮次执行上下文与恢复

仅新 operation_kind=`decision_turn` 使用 TurnExecutionContext；默认 legacy_research 执行不变。上下文唯一拥有 provider、recorder、meter 和原始提交／截止时间，所有允许阶段的每个物理请求只记录一次；新研究最终决策阶段禁止 JSON 修复、technical retry 和润色，旧阶段获准修复/重试仍逐次计入；不得外层与 provider 重复记账。无模型调用绕过上下文。默认整轮从 queued 起 ≤900 秒、累计 ≤40,000 Token，研究最终报告预留 4,096。澄清／规划输出 ≤1,024，解释／评估 ≤2,048，最终组合报告 ≤4,096，均再受真实剩余额度限制；缺实际 usage／未知费用停线。

上下文持久状态至少含 schema_version、task／turn／session／input_revision 标识、输入／引用／投影哈希、提交和原截止时间、累计用量及未知覆盖、max／report reserve、阶段／检查点／call coverage。AgentLoop 接收注入上下文和 research-only／phase-only 策略，不重置 recorder／meter／起点，也不关闭共享 provider。Loop 只清理自己的 GitHub／browser 资源，最外层关闭 provider 一次。研究阶段确定性导出事实，不先调一次旧 LLM 报告再重复调组合报告。内层结束转换为 V2 research_phase_finished，不触发旧 Worker 的任务 finished handler。

阶段前进前持久化结构化、校验通过的输出和状态，以及已覆盖 physical call IDs／usage；不存原始 Prompt 或无界 provider body 充当恢复材料。恢复先核对条件／证据／投影哈希和事件重放，沿用原截止时间、累计调用用量及额度，至多重新认领一次。无完整检查点不假装阶段可安全跳过：

- started 但没有可知结果：保留 unknown_outcome 与未知费用，停止新增调用，不盲重试。
- call 已 completed 且用量已知，但阶段输出未提交：保留完成状态与已知费用，确定性终结 partial／failed，reason=`phase_output_not_committed`；不得自动重调，也不得把 completed 改为 unknown。
- 阶段／step 输出及覆盖账本均已提交且校验通过：可从该检查点继续；不重放结果不明的外部动作。

### V2-5 旧接口、迁移协议和回滚

现有六路 API／DTO／六态、同 task 事实和旧事件集合保持。旧 AgentEvent 七种为 task_queued、task_requeued、task_started、subgoals_initialized、step_evaluated、cancel_requested、task_finished；service_unavailable 是 SSE 传输消息，不是第八种领域事件。V2 使用独立事件 schema 及路由，不扩大旧闭合集合；旧列表／详情不暴露 decision_turn。新 operation_kind 不能在任意客户端输入中降级为 legacy_research，旧写路径也不能改写新 kind。

旧 claim_next 不按 kind 过滤且旧 Worker 无握手，因此启动器检查本身不够。未来 additive migration 须在 decision_turn 的 INSERT／UPDATE 增加数据库兼容护栏：事务 current_setting('app.execution_protocol', true) **IS DISTINCT FROM** 'decision-v2' 时拒绝，包含 missing／NULL；禁止通过改 kind 绕过。新写事务 SET LOCAL，连接池不能使用 session／role／database 默认 setting；所有正常和终态写入口都遵守，事务结束不泄漏 setting。此 setting 只隔离旧二进制协议，不是认证，也不防持有数据库凭据的恶意进程；不扩权，若常规迁移权限不足创建函数／trigger 则停下另议。

先受控停止全部旧 API／Worker，再运行 additive migration，核对 schema／能力版本，最后启动兼容版本并打开新路由。未经确认不能混跑旧进程与新任务。回滚只到同样理解护栏与 operation_kind 的兼容基础版本，关闭新入口，保留新增表、轮次和数据；不 destructive downgrade、不恢复不理解新任务的旧二进制。迁移只作为后续任务计划，本轮不执行。

### V2-6 本机边界和资金关闭

新命名空间全部接口（含 GET／SSE）在对象读取、游标解析和流建立前验证精确配置的 loopback Host，不接受任意子域或模糊后缀。写接口还校验明确许可的本机 Origin 及 application/json；缺失 Origin、null、跨站拒绝 403，无通配 CORS。GET／SSE 不必要求 Origin，但仍验 Host 和对象链。M1 owner 从服务端已认证的真实成员账户取得，不能由请求指定；旧本机合成身份目标被本版替代；session／turn／report／ref／cursor 都验证同 owner／session。本机 Host/Origin 检查与真实账户授权同时生效，不代表正式五账户或 LAN 安全已通过。

网页／引用／渲染均不可信：只研究公开 HTTP(S)，不含凭据，不下载或执行任意代码，不把网页升级为指令／权限；链接和文本安全转义，不加载任意主动内容。新入口不解决原有浏览器 DNS／重定向／私网阻断未验证项，不接入私有项目、老人录音或医疗数据。

**新付费模式保持关闭**，无论 discuss 或 research；本轮不授权真实模型调用。旧 pilot 额度与记录仅沿用原用途，不能声称是新会话通用资金。DEC-T12 按已批准 F1 设计另获具体实现授权后落实服务端 grant reference／任务与阶段范围／金额、计价快照、项目 ledger checkpoint、旧库已知／未知和在途预留、跨库不重复／不漏计规则；未解决不得开启新付费路径。grant 不由客户端、聊天、页面或模型声明生效；单次运行另需原有明确授权。原 49／30／200／20、合计 299 元上界不改，未知费用不能按零。假供应商离线实现不构成真实质量证据。


## V2-7：M1 记忆、上下文与报告执行约束

| 对象 | 权威及准入/读取 | 生命周期/隔离/验证 |
| --- | --- | --- |
| 已接受条件 | InputRevision，仅用户接受/编辑写入，调用绑定版本 | 不可变，新版本覆盖当前选择，原报告不修改；网页/摘要不得覆盖 |
| 同会话引用 | SessionEvidenceRef 验 owner/session/origin_task/fact/hash | 原观测与人工核源快照不刷新，解释旧报告可沿用带日期资料，当前动态建议须新查 |
| 跨任务来源线索 | 显式导入同 owner 已人工核源报告（报告hash/工件/fact校验）；默认off | 导入起7天，读不续期，每次最多5，先排除expired/revoked再相关排序/去重；来源线索非事实 |
| 临时投影 | 从当前条件、完整eligible事实索引、历史ref、最近失败确定性生成 | 输入哈希/策略/排序/选择/裁剪/回取原因可追；裁剪不删除原证据，不是恢复真相 |
| 执行检查点 | Pg阶段提交/call coverage/fencing | 不拥有费用、事实和终态，不通过检查点反向重发completed/unknown |

线索保存 origin_observed_at、human_reviewed_at、imported_at、expires_at、revoked_at、owner、来源/报告/内容哈希和版本。import不复制当前结论；读取及发送前检查生命周期，冲突并列、身份不符拒绝；价格/版本/可用性重新访问。不同owner/session的原事实不可靠fact_id猜测访问，跨任务只有显式线索路径，不能暗导入旧SQLite研究UI。撤销保留审计但停止后续准入。恢复后撤销高水位未核对前停止线索注入。

C0 保留近窗简单基线；C1 在完整合格索引上确定性相关选择；C2 在裁剪前建立当前revision下已识别支持/反证/冲突/限定语/最近失败的保护集合，再按预算选择。记录候选、fact/ref ID、来源时间、关联理由、容量与丢弃项；未识别、未绑定、被裁剪分开统计，机器关联不等于语义正确。最低证据无法容纳则分批或partial/unknown，不能丢反证换完整外观。确定性按ID回取且记录原因，研究缺口由用户明确新轮补查；M1不用模型摘要，不隐含摘要/检索调用。

研究阶段产出已准入事实，最终决策仅一次物理模型请求，确定性schema/引用校验和渲染；不先运行旧LLM Reporter，不允许repair/technical retry/润色。非法schema/引用不符诚实failed或有足够证据的partial，不能修饰为完整成功。讨论/规划/评估等阶段仍按各自有界策略与账本执行；“一次决策”不表示整个Agent只调一次模型。

## V2-8：逐物理请求 admission 与资金 F1

所有旧新付费入口共用单一活动 Pg authority；项目、分配、grant、call reservation/settlement 同权威原子事务，旧库只读核对导入以稳定调用身份去重，冲突拒绝且不产生双权威。每个物理请求持久生成一个单次不可复用 admission，绑定精确编译请求哈希、owner/session/turn/input_revision、引用及线索版本、恢复代次、grant和价格快照。不得用同admission修复/重试/换body/换阶段/重复发送。每次发送有唯一attempt；传输后未知结果保留在途预留、unknown/null和停线，不做网络自动重试。

锁序扩展既有 scheduler→session→task：先锁资金权威/项目控制行，再 scheduler→session→task→grant→按ID排序的hint控制行及附属记录；所有需要多对象的路径遵循同一全局序，缺项跳过，禁止反向获取。revoke与admit必须锁相同hint控制行且遵循该序，不能只用进程锁/时间戳；金额预留/条件/引用/有效性校验与admission同事务提交。提交前不可发送；提交结果不确定则不发送，待数据库对账。数据库本地事务重试只允许在物理发送前，成功admission不能二次发。revoke先提交则之后admit拒绝；admit先提交只准其已绑定在途请求并保留撤销前准入证据，不承诺撤回已发送请求；随后所有准入重检。

grant由服务端离线操作录入负责人明确逐次授权，绑定代码、模型、用途/阶段、任务/轮数/尝试数、金额、计价快照、owner及generation；聊天/客户端/页面/模型不是grant生成器。预算天花板、供应商余额、已授权金额、实际可用额、在途预留分开；known/null费用均保留，不凭0值放行。49/30/200/20合计299元上界不变，不能挪用途自动加调用。

恢复生成新generation且paid_disabled，旧登录与grant失效；先停旧authority，核对独立于旧备份保存的最新ledger/grant/revocation高水位、供应商/备份后发生/未知及在途账后才能提升authority和另授权付费。旧SQLite、恢复副本和旧worker不能消费资金；没有最新权威证据保持关闭，不以“备份内部一致”替代最新性。来源线索亦须撤销对账后才可注入。新付费实现目前尚无，不得用设计文字宣称已防超支。

## V2-9：请求审计 A 与 Token 资格

保存完整**有界编译输入**、准确模板/schema文本、实际配置/默认值/模型参数/输出限额/排列顺序、全部投影/失败材料及哈希、可取得的冻结编译器/依赖工件与版本，供确定性重建。保存最终 canonical JSON哈希和发送字节哈希（不额外持久化compiled body）；无法捕获精确字节或缺工件则相应标不可验证/不可回放，不能把canonical语义一致冒充字节一致，更不能证明provider Token一致。旧允许repair阶段还需有界首次响应片段等输入依赖。请求审计不充当业务状态/checkpoint，不重发completed/unknown调用。

上述材料可重建完整内容，按owner隔离及受控导出、加密备份；存储和发送前检查秘密，拒绝而不写入凭据/headers/key。审计trace只存安全摘要与工件ref，工件访问同样逐对象授权。模板/用户文本/工具输出按信任级别分隔，字面特殊token不能提权为模板控制token。

模型容量、每轮累计40000及CNY三道约束互不替代；完整输入含system/schema/tools/投影，实际usage含输入输出及缓存命中/未命中，未知分开。官方deepseek-recipe固定版本只做M1离线影子资格：中文/英文/混合代码、JSON/tool schema、特殊token、模板/别名映射及可取得线上usage偏差，记录完整输入哈希/版本/误差；不自动替换当前硬准入，不额外真实请求。OpenCode chars/4与15%预留只作参考，不复制为硬资金界。未安装/未运行的tokenizer不能写验证通过。
