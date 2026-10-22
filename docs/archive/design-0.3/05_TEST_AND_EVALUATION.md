# 测试与 Agent 评测基线

> 状态：**APPROVED（设计）**；实施与付费评测未授权。本文是后续验证方案，不表示任何计划测试已经通过。旧版 [V1 测试矩阵](../testing/V1_TEST_MATRIX.md)、[Benchmark 协议](../benchmark/BENCHMARK_PROTOCOL.md)和原始记录保留原样。

## 1. 当前证据与测试边界

**VERIFIED**：`tests/unit/` 覆盖状态、规划、评估、报告、工具与预算；`tests/integration/` 覆盖 AgentLoop、SQLite、HTTP/SSE；`tests/smoke/` 包含浏览器适配器；`frontend/src/App.test.ts` 有交互测试。`.github/workflows/ci.yml` 在 Python 3.12/3.13 执行锁定安装、Ruff、compileall、离线 pytest，在 Node 22 执行前端 `type-check`、`build` 和 `test`。这些检查的**当前执行结果**应引用实际 CI run，不能从配置文件推断为已通过。

**VERIFIED**：[D7 交付报告](../audits/V1_DELIVERY_REPORT.md)记录 r12 B01–B03 × 三组 × 两次，共 18 条真实原始记录；每组完整完成率 0%。三次独立 Vue→API→Agent→SQLite→SSE 真实任务均未完成，B01/B02 因 `token_budget`，B03 因 `no_progress`，均无合格引用报告。历史结论为 **No-Go**。原因归属按运行记录保留；无法据此断言单一代码根因。r12 baseline 六次 Token 用量为 `null`，且调用前 40,000 Token 上限不能同等保证，因此 `budget_parity=mismatched`。

### 分层与触发

| 层级 | 用途与可观察边界 | 触发 / 证据 |
| --- | --- | --- |
| Unit | Reducer 合法/非法转换、结构化输出与一次修复、上下文裁剪、去重、事实来源、不变量、终止与用量 | 每个相关 PR；pytest 输出及失败先行测试记录 |
| Fake integration | AgentLoop 接 Fake Provider/Tool；TaskManager 并发/取消；真实临时 SQLite 事务；六路 HTTP 与 SSE 重连 | 每个相关 PR；隔离数据库、确定性时钟、事件/状态断言 |
| Browser smoke | 可控 loopback 页面上的 Chromium 导航、DOM 观察、点击、提取、过期/无效元素及关闭 | 适配器改动或本地验收时显式 opt-in；浏览器版本和资源关闭证据 |
| Real E2E | Vue 提交固定任务，经真实 API、模型、工具、SQLite 与 SSE 得到报告或真实失败 | 放行前，经费用授权；独立任务 ID、脱敏日志、UI/API/数据库核对 |
| Agent Eval | 固定公开任务、每次尝试的字段覆盖、官方来源核验、成本、时延、失败类别 | 稳定代码指纹后，经费用授权；完整原始记录与人工来源核验 |
| Security | URL/私有地址/重定向、网页指令注入、密钥脱敏、异常输出 | 相应边界变更时；受控本地夹具，不访问内网目标 |

本地隔离数据库、Fake Provider 和受控页面只能证明链路行为，不能替代真实业务完成。外部站点、网络或提供方故障保留为失败样本并分类；不可静默删除或只重跑失败项。

## 2. 可追踪测试矩阵

下表全部为 **PROPOSED** 用例；`TEST-001..008`、`TEST-N01..N06` 是追踪矩阵主 ID，`A/B` 是正常/异常子例。验收 ID 见 [验收基线](06_ACCEPTANCE_AND_RELEASE.md)。`自动` 表示拟自动化，`人工` 表示必须保存人工核验记录。每个 P0 功能至少有正常和异常路径。

| Test ID | Requirement | Component | Preconditions / Input | Expected Result | Level / Automation | Evidence target |
| --- | --- | --- | --- | --- | --- | --- |
| TEST-001-A | FR-001 | API、ResearchService、TaskManager、SQLite | 空队列；合法目标提交并列出 | 202 与持久 `queued` 事件同一任务 ID；至多两个运行，其余排队，列表可读 | integration / 自动 | HTTP 响应、任务行、事件 ID、并发轨迹 |
| TEST-001-B | FR-001 | API、PersistenceService、TaskManager | 空目标、无凭据、第三任务排队时重启；另在 queued 已提交后令 `submit` 抛错 | 422/503 无幽灵任务；重启后旧排队任务按既定终态处理；提交失败须补写唯一失败终态，此项当前未实现 | integration / 自动 | 状态码、事务前后行数、重启日志、提交异常注入 |
| TEST-002-A | FR-002 | Planner、ToolRouter、Evaluator、Reducer、AgentLoop | Fake Provider/Tool 返回逐步新增证据 | 观察改变决策；动作一次执行；评估后状态进展并有 trace | unit + integration / 自动 | 决策、动作计数、事件序列 |
| TEST-002-B | FR-002 | Provider、Planner、BrowserUseAdapter | 无效 JSON/动作、陈旧元素、临时 429 或超时；分别注入 Provider 与 ToolResult 失败 | 有界修复/技术重试；Provider 耗尽进入 `token_budget` 或 `execution_error` 终态且不调用 Evaluator；工具故障的 ToolResult 经 Evaluator 后决定重观察；资源关闭 | unit + browser smoke / 自动 opt-in | Provider/工具/评估调用次数、错误类别、关闭记录 |
| TEST-003-A | FR-003 | ToolResult、Evaluator、ResearchFact | 官方页含明确字段及 URL；重复访问 | 事实保留对应来源、去重后不丢正确事实；报告可按事实 ID 回查 | integration / 自动 | fact 行、来源 URL、报告引用映射 |
| TEST-003-B | FR-003 | Evaluator、Reducer、Persistence | 同一步有一条有效和一条缺证据/错主体候选；另输入重复事实、模型伪造诊断字段、历史无片段 trace | 有效事实准入、证据拒绝候选不入 fact/report；事件顶层摘要由本地校验确定、首原因码准确且不含候选正文；模型伪造字段不进入诊断；重复由 Reducer 去重、不算证据拒绝；历史显示“未记录/未保存原文” | unit + integration / 自动 | step trace 摘要、fact 行、状态前后快照、脱敏检查 |
| TEST-004-A | FR-004 | Reporter、Persistence、API/UI | 有已验证事实和未完成子目标 | Markdown 只陈述有来源结论，列出未知项；终态报告可重载 | integration + E2E / 自动+人工 | 报告、fact ID、页面截图、重启后响应 |
| TEST-004-B | FR-004 | Reporter、API/UI | 无事实或报告生成失败 | 显示真实 partial/failed 与原因；不渲染伪造成功或无来源结论 | integration + frontend / 自动 | 终态、错误视图、报告文本 |
| TEST-005-A | FR-005 | Persistence、SSE、Vue | 创建后连接、断线并带 `Last-Event-ID` 重连 | 持久事件按序补读、再进入直播；历史详情与页面一致 | integration + frontend / 自动 | event ID 序列、SQL 行、UI 时间线 |
| TEST-005-B | FR-005 | SSE、TaskManager | 慢订阅者断开、未知 ID、终态瞬间重连；在游标校验与订阅、订阅与首次补读之间插入事件 | 未知 ID 先返回 422 且无订阅；两个竞态窗口均不漏已提交事件或重复展示；订阅者清理，任务不因断线取消 | integration / 自动 | 队列订阅数、响应码、trace 游标与 event ID 比对 |
| TEST-006-A | FR-006 | TaskManager、AgentLoop、Persistence | queued/running 取消；进程关闭后重启 | 各任务仅一个终态事件；浏览器/HTTP 关闭；重启未完成任务标 `server_restart`，不续跑 | integration / 自动 | 任务/事件行、资源关闭计数 |
| TEST-006-B | FR-006 | 同上 | 取消与自然完成、超时、数据库写入并发 | 终态不可逆且无双 `task_finished`；失败可解释，无遗留运行槽 | integration / 自动 | 并发多次运行、唯一事件、slot 计数 |
| TEST-007-A | FR-007 | DeepSeek attempt 计量、Provider meter、事件、API/UI | initialize/plan/evaluate/report 成功，另有一次结构化修复且各请求均返回 usage | repair 与父阶段互斥；各事件阶段已知 Token 和现有事件增量相等、全任务只计一次；耗时/分类可见 | unit + integration + frontend / 自动 | 请求级 Fake 记录、event_id、账本、UI 显示 |
| TEST-007-B | FR-007 | 同上、Reducer | 首次有 usage、修复无 usage；429 重试无响应；不支持 attempt 记录的 Provider；旧 trace 无新字段；预算边界 | 有记录时未知 attempt 正确计数，完整总量为 `null` 且显示已知下界；无记录 Provider 和旧 trace 省略阶段分布而不编造 calls；错误/预算停止原因不冒充实际费用硬限制 | unit + integration / 自动 | 请求次数、known/unknown 账本、旧事件重放、终态 |
| TEST-008-A | FR-008 | Vue、现有报告 API | 已批准且 P0 稳定后使用模板/导出 | 模板只填表单；导出与实际保存的 Markdown 相同 | frontend / 自动 | UI 交互、下载内容比较 |
| TEST-008-B | FR-008 | Vue | 无报告或 partial 报告 | 禁止空成功导出；partial 标识和未知项保留 | frontend / 自动 | UI 状态、文件内容 |
| TEST-N01-A | NFR-001 | Runtime、Persistence | 隔离 DB/Fake Provider；正常事实在 30 步、900 秒、已报告 40k Token 内完成 | 唯一 completed 终态、报告一致、资源关闭 | unit + integration / 自动 | 任务/事件行、资源计数 |
| TEST-N01-B | NFR-001 | Runtime、Persistence | 分别触发步骤/时间/已报告 Token/无进展上限，另造取消与写入失败竞态 | 有界 partial/failed/cancelled、事务原子、无双终态或泄漏 | unit + integration / 自动 | 各边界前后行、事件序列、关闭计数 |
| TEST-N02-A | NFR-002 | Context、Provider、工具 | 固定长页面与重复 URL，所有请求 usage 可见 | 输入规模和阶段已知 Token 可对账；重复动作有界；预算内完成 | unit + Eval / 自动+人工 | prompt 尺寸、请求/URL 次数、Token |
| TEST-N02-B | NFR-002 | Provider、AgentLoop | 模拟无 usage、重试和临界剩余预算 | 未知调用显式标记、不能证明实际费用硬上限；可上界请求遵守 40k/900s/30 步 | unit + integration / 自动 | 请求明细、终态、缺失标记 |
| TEST-N03-A | NFR-003 | URL 边界、浏览器、日志 | 受控公有页面、无恶意文本与秘密 | 浏览、核源可用；日志/事件不含凭据 | security + browser smoke / 自动 opt-in | 受控访问日志、脱敏扫描 |
| TEST-N03-B | NFR-003 | URL 边界、浏览器、Persistence、日志 | 直接私有/回环、多 DNS 答复或解析结果变化、受控公有→私有重定向与点击/弹窗/子资源；恶意页分别指令读取测试密钥、访问私网、伪造事实 | 直接目标在请求前拒绝；以受控请求日志分别记录重定向、点击等请求是否已发出及事后处置，不把最终 URL 拒绝计作事前阻断；三个 canary 均不得形成越权工具决策、私网请求、密钥输出或无来源报告事实；已配置密钥不进日志/trace/SSE，新增诊断元数据不复制页面正文；未证明的浏览器内部请求仍为可信本机残余风险 | security / 自动+人工 | URL/DNS 夹具、本地服务请求日志、工具决策/trace/SSE/报告扫描、风险签收 |
| TEST-N04-A | NFR-004 | 日志、事件 | 正常完成任务，给定 task_id | event_id 顺序、阶段耗时和报告可重建 | integration / 自动 | 脱敏日志、trace/任务对账 |
| TEST-N04-B | NFR-004 | 日志、事件 | Provider/Tool 故障、缺 usage 和取消各一次 | 错误类别与停止原因可复盘，未知值明确且无敏感正文 | integration / 自动 | 故障注入记录、事件链 |
| TEST-N05-A | NFR-005 | CI、类型/配置 | 有效锁文件及本次受检 PR | Python 3.12/3.13、Ruff/pytest、前端检查实际通过 | CI / 自动 | 当前代码指纹的 CI run URL 与退出码 |
| TEST-N05-B | NFR-005 | CI、类型/配置 | 故意无效配置/锁或契约回归夹具（隔离分支） | 适用门禁失败并阻断；不改历史数据 | CI + integration / 自动 | 失败 job、回归测试输出 |
| TEST-N06-A | NFR-006 | 启停与文档 | 干净本机环境、有效 key、隔离 SQLite | README 可启动并提交/读取任务，正常关闭资源 | local smoke / 人工 | 版本、启动命令、任务 ID、关闭日志 |
| TEST-N06-B | NFR-006 | 启停与文档 | 缺 key、重启时 queued/running、旧 SQLite 副本 | 错误明确，未完成任务标 server_restart，历史可读且无续跑声称 | local smoke + integration / 自动+人工 | 响应/任务/事件行、重启记录 |

## 3. 新版评测协议建议（与历史 r12 分离）

**PROPOSED：**沿用 B01–B03 的固定任务原文与 Expected Fields 作为回归任务集；保留历史 r12 协议、18 条记录和原评分，不在旧批次上改分。新版本协议须先定稿并独立命名（建议 `G2-EVAL-v1`），记录代码指纹、受检 browser-use 指纹、锁文件、模型、浏览器/OS、网络与时间窗口、完整 Prompt 哈希、预算、每次尝试和人工核源者。若新版本改变评分类别、工具可用性或 baseline 配置，必须新建协议版本与完整新批次，禁止跨版本直接报改进百分比。

最低放行采用**单独的 full-system 真实业务验收**：B01–B03 各三次，共九次真实 Vue→API→AgentLoop→SQLite→SSE 回归任务；每题至少 2/3 完整成功，全部九次保留并计入分母。“完整成功”须满足[06 的终态、字段与核源定义](06_ACCEPTANCE_AND_RELEASE.md#2-三层最低放行条件)，不能只凭 scorer 的文本字段或 `completed` 状态单独判定。每个实质结论均需打开所引官方页面核验，来源追溯率与准确性均达 100%；按原 Expected Fields 独立计算字段覆盖率，九次汇总至少 90%。回归成功率、覆盖、来源质量三项须同时满足：若每题只成功 2/3，失败尝试也必须保留足够的可核实字段才能达到 90%，否则仍为 No-Go。另有下述 G01–G03 三次独立泛化门槛，与九次回归分开统计。未完成尝试必须保留失败原因，不能因早停步数少而声称效率提高。测试环境、样本量、审核记录与计数脚本作为放行证据；小样本 P95 只是描述性统计，不能宣称统计显著。

**字段分母锁定**：依照现有 [`benchmark.metrics.score_answer`](../../benchmark/metrics.py) 的字段键，B01 为每个候选 `name/repository/license/install/source` 共 **10**，B02 为 FastAPI 与 Flask 各 `name/route/async/install/source` 共 **10**，B03 为 `version/publication_date/change_1/change_2/official_release_source` 共 **5**。三次各题合计分母 `3×(10+10+5)=75`，故九次覆盖率达 ≥90% 至少需 **68/75** 个有官方来源且人工核实的字段。失败、取消、超时、无报告尝试的缺失字段记 0，不剔除；同一尝试的两个变化必须不同，B01 两个候选必须不同。字段是否在文本中出现先由原 scorer 判定，人工核源发现不支持或互相矛盾时该字段为 0 且该次不得记完整成功；不改历史 scorer 或 r12 结果。B03 的“latest”按每次运行时可核验的官方 Release 列表判定，记录检查时间和所见版本，站点变化如实保留。

**逐结论人工核源**：为十二次每一尝试保存 `run_id/task_id/field_key/报告原文定位/fact_id/官方 URL/打开时间/页面支持片段或定位/自动字段分/人工支持判定/冲突理由/核查者`；对报告中超出 Expected Fields 的每条实质结论也建立 claim 行。核查者直接打开官方仓库、文档或 Release 页，比对主体、版本、发布日期、命令与变更归属；页面不可访问记 `unverified` 而非正确。`source_traceability` 的分母是全部实质结论，`source_accuracy` 的分母是已追溯结论；分母为 0 记 N/A 且不放行。所有失败/冲突和每个案例至少一次完整运行要第二遍复核；有第二人时优先交叉复核，否则由同一人隔时依原始记录重核并标注非独立，分歧保留两份记录并以官方页面证据裁决。

**独立泛化留出集（PROPOSED）**：在 Gate 2 修复前锁定下列原文和预期字段，不用作调 Prompt 或挑选成功样本；与 B01–B03 分表报告，每题仅一次真实 full-system 运行，另需费用授权。G01：“Find the official repositories, licenses, and documented Python installation commands for Selenium and Playwright. Cite the official sources for each item.”（两项目各 name/repository/license/install/source，10 字段）。G02：“Compare Django and Starlette for a small Python HTTP API using their official documentation. For each, give its route declaration, documented async handler support, installation command, and exact official source page.”（两项目各 name/route/async/install/source，10 字段）。G03：“Find the latest public release of microsoft/playwright and report its version, publication date, two distinct release-note changes, and official release page.”（5 字段）。G01–G03 **不复用 B01–B03 的站点白名单或旧 scorer**，先用本段字段和人工核源表记录完整原文、代码指纹、执行时间与官方链接；未提供来源的字段为 0。三次中至少 2 次完整成功且无一条无来源的完成宣称，作为单独的泛化放行条件；若公开页面不提供某预设字段，应记录任务不适配并在新版本协议中重新冻结，不能事后删字段或换题提高结果。样本太小，只能说明这三个留出任务的结果，不能推断总体成功率。

继续保留三组比较视角：baseline、adaptive full、adaptive browser-only。若做对照评测，按现有 [Benchmark 协议](../benchmark/BENCHMARK_PROTOCOL.md)逐次记录全部三组及失败；将完整成功率、字段覆盖、来源准确性、prompt/completion Token、时延、步骤、重复 URL 和失败类别分别报告。baseline 缺失 Token 或不能同等实施调用前预算时标 `budget_parity=mismatched`，仅作描述性比较，不能把机制差异归因于单一 Planner。真实模型运行须先取得费用授权；本 Gate 1 不执行。

## 4. 结果判读与证据格式

每次真实运行保存脱敏 `run_id`、任务 ID、案例、Prompt/代码/协议指纹、环境、开始结束时间、终态及停止原因、事件 ID、报告和来源 URL、逐项字段评分及人工核源结论。`null` 表示未观测，不当作 0。报告平均和 P95 耗时、Token 中位数/范围、重试及重复动作次数，同时列出全部失败类别与样本数。安全扫描需覆盖密钥、Bearer、Cookie、任意页面路径中的敏感参数；保存前脱敏，原始秘密不得进入设计或评测文件。

若新增功能改变报告字段或数据库契约，先更新 [数据/API 契约](04_DATA_AND_API_CONTRACTS.md)和[追踪矩阵](09_TRACEABILITY_MATRIX.md)，再选择最小充分测试集。测试通过只说明其所在层级；最终业务放行以真实任务、来源和完整报告为准。
